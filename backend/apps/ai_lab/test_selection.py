from unittest.mock import MagicMock, patch
import json

from django.test import SimpleTestCase, TestCase, override_settings

from . import lexical, provider, retrieval, selection, services, test_reference_index as fixtures


def passage(number, *, article_id="10", text=fixtures.TEXT, section="Treatment"):
    return retrieval.Passage(f"P{number}", article_id, "Reference title", section, text,
        {"screen": "uptodateArticle", "params": {"id": article_id, "sectionId": "H1",
            "searchAnchor": f"original-{number}", "searchContentHash": "b" * 64}}, "b" * 64)


def group(number=1, count=1, *, article_id="10", offset=0):
    return {"id": f"T{number}", "article_id": article_id, "title": "Reference title", "heading": "Treatment",
            "preview": fixtures.TEXT, "passages": [passage(offset + n, article_id=article_id) for n in range(1, count + 1)]}


def explanation(identifier="P1"):
    return {"source_id": identifier, "summary_fa": "توضیح فارسی بر اساس متن اصلی منبع"}


def decision(*, supported=("P1",), sufficient=True, answer=("P1",)):
    return {"supported": list(supported), "sufficient": sufficient, "answer_source_ids": list(answer)}


class EvidenceSelectionTests(SimpleTestCase):
    def test_first_line_reserves_first_batch_for_recommendation_and_late_regimen(self):
        groups = [group(1, 10), *[group(n, 1, offset=n * 100) for n in range(2, 10)]]
        groups[-1]["heading"] = "Administration"
        dose = groups[-1]["passages"][0]
        dose.text = "Synthetic example agent: 5 mg orally once daily; restricted to the original source population."
        context = lexical.search_context("خط اول درمان بیماری چیست؟", ["example condition"])
        _, selected = selection.select_evidence(groups, {}, context=context)
        self.assertEqual([p.id for p in selected[:3]], ["P1", "P2", "P3"])
        self.assertIn(dose, selected[:6])
        self.assertIs(next(p for p in selected if p.id == dose.id), dose)
        self.assertLessEqual(len(selected), lexical.MAX_RANKED_PASSAGES)
        self.assertLessEqual(sum(len(p.text) for p in selected), lexical.MAX_PASSAGE_CHARACTERS)

    def test_important_effects_qualifier_promotes_significant_section_into_first_batch(self):
        general, significant = group(1, 20), group(2, 5, offset=100)
        general["heading"] = "Adverse Reactions"
        significant["heading"] = "Adverse Reactions (Significant): Considerations"
        context = lexical.search_context("عارضه مهم آریپیپرازول", ["aripiprazole"], lookup_kind="drug",
                                         keywords=["important adverse effect"])
        ranked = lexical.rank_memory_sections([general, significant], context, {})
        self.assertEqual(ranked[0]["id"], "T2")
        _, selected = selection.select_evidence(ranked, {})
        self.assertEqual([p.id for p in selected[:3]], ["P101", "P102", "P103"])

    def test_first_batch_covers_leading_evidence_and_alternative_sections(self):
        groups = [group(1, 10), *[group(n, 2, offset=n * 100) for n in range(2, 7)]]
        audit = {}
        identifiers, selected = selection.select_evidence(groups, audit)
        self.assertEqual([p.id for p in selected[:6]], ["P1", "P2", "P3", "P201", "P301", "P401"])
        self.assertEqual(identifiers, [g["id"] for g in groups])
        self.assertEqual(len(selected), 18)
        self.assertEqual(audit["selection_engine"], "local")
        self.assertTrue(audit["limited"])

    def test_fallback_batch_can_reach_last_of_sixteen_ranked_sections(self):
        groups = [group(1, 20), *[group(n, 1, offset=n * 100) for n in range(2, 17)]]
        identifiers, selected = selection.select_evidence(groups, {})
        self.assertIn("T16", identifiers)
        self.assertIn("P1601", [p.id for p in selected])
        self.assertLessEqual(len(selected), lexical.MAX_RANKED_PASSAGES)

    def test_whole_original_objects_targets_and_character_budget_are_preserved(self):
        groups = [group(1, 20)]
        for p in groups[0]["passages"]:
            p.text = "x" * 5000
        audit = {}
        _, selected = selection.select_evidence(groups, audit)
        self.assertEqual(len(selected), 4)
        self.assertIs(selected[0], groups[0]["passages"][0])
        self.assertEqual(selected[0].target["params"]["searchAnchor"], "original-1")
        self.assertTrue(all(len(p.text) == 5000 for p in selected))
        self.assertLessEqual(audit["selected_passage_characters"], lexical.MAX_PASSAGE_CHARACTERS)

    def test_duplicate_ids_empty_sections_and_empty_evidence_are_handled(self):
        groups = [group(1, 0), group(2, 2), group(3, 1)]
        identifiers, selected = selection.select_evidence(groups, {})
        self.assertEqual(identifiers, ["T2"])
        self.assertEqual([p.id for p in selected], ["P1", "P2"])
        self.assertEqual(selection.select_evidence([], {}), ([], []))


@override_settings(AI_LAB_LOCAL_SELECTION_ENABLED=True, AI_LAB_LEXICAL_ENABLED=True)
class LocalSelectionGroundingTests(SimpleTestCase):
    def setUp(self):
        self.network = patch.object(provider, "build_opener", side_effect=AssertionError("Unexpected network call"))
        self.network.start()
        self.addCleanup(self.network.stop)





    @patch.object(services, "chat")
    def test_first_line_requires_explicit_verified_regimen_coverage(self, chat):
        for flag in [None, "true", 1]:
            with self.subTest(flag=flag):
                chat.side_effect = [({"items": [explanation()]}, {}), ({**decision(), "regimen_complete": flag}, {})]
                with self.assertRaisesMessage(provider.ProviderError, "INVALID_MODEL_OUTPUT"):
                    services._explain_batch("luna", "خط اول درمان چیست؟", [passage(1)], [], lambda _: None)

    @patch.object(services, "chat")
    def test_nonpharmacologic_first_line_can_finish_without_inventing_a_drug(self, chat):
        chat.side_effect = [({"items": [explanation()]}, {}), ({**decision(), "regimen_complete": True}, {})]
        supported, chosen = services._explain_batch("luna", "خط اول درمان چیست؟", [passage(1)], [], lambda _: None)
        self.assertEqual(chosen, ["P1"])
        self.assertEqual(len(supported), 1)
        self.assertIn("nonpharmacologic", chat.call_args_list[0].args[1])







    @patch.object(services, "chat", return_value=({"queries": []}, {}))
    @patch.object(services, "search_articles")
    def test_nonmedical_request_abstains_without_reading_source(self, search, chat):
        result = services.answer("یک شعر بنویس", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"], [])
        self.assertEqual(chat.call_count, 1)
        search.assert_not_called()






@override_settings(AI_LAB_LOCAL_SELECTION_ENABLED=True, AI_LAB_LEXICAL_ENABLED=True)
class PreparedSelectionTests(TestCase):
    setUp = fixtures.ReferenceIndexTests.setUp
    write_article = fixtures.ReferenceIndexTests.write_article
    add_title = fixtures.ReferenceIndexTests.add_title
    build = fixtures.ReferenceIndexTests.build

    def test_full_prepared_path_uses_three_calls_and_cites_original_source_after_sixty_sections(self):
        body = '<div id="topicText">' + ''.join(
            f'<p class="headingAnchor" id="H{n}"><span class="h1">Background {n}</span></p><p>{fixtures.TEXT}</p>'
            for n in range(65))
        body += '<p class="headingAnchor" id="H99"><span class="h1">Adverse Reactions</span></p>'
        body += '<p>Aripiprazole adverse reactions are described here with the exact original restrictions and qualifications.</p></div>'
        self.write_article("3851", body, title="Aripiprazole: Drug information")
        self.build()
        def model(alias, prompt, data, limit):
            if prompt == services.PLAN_PROMPT:
                return {"queries": ["aripiprazole"], "lookup_kind": "drug", "intent": "adverse_effects"}, {}
            if prompt == services.ARTICLE_PROMPT:
                return {"article_ids":[a["id"] for a in data["articles"][:3]]}, {}
            if prompt == services.TITLE_PROMPT:
                return {"section_ids":[s["id"] for s in data["sections"] if s["title"] == "Adverse Reactions"]}, {}
            if prompt == services.ANSWER_PROMPT:
                self.assertEqual(data["paragraphs"][0]["section"], "Adverse Reactions")
                return {"items": [explanation(data["paragraphs"][0]["id"])]}, {}
            identifier = data["items"][0]["id"]
            return decision(supported=(identifier,), answer=(identifier,)), {}
        with patch.object(services, "chat", side_effect=model) as chat, \
                patch.object(services, "search_articles", return_value=[{"id": "3851", "title": "Aripiprazole: Drug information"}]), \
                patch.object(retrieval.utd, "get_topic", side_effect=AssertionError("No source HTML at runtime")):
            result = services.answer("عوارض آریپیپرازول", "luna", ["uptodate"], [], None)
        self.assertEqual(chat.call_count, 5)
        citation = result["parts"][0]["items"][0]
        self.assertTrue(citation["source_id"].startswith("P"))
        self.assertEqual(citation["target"]["params"]["sectionId"], "H99")
        self.assertTrue(citation["target"]["params"]["searchAnchor"])
        self.assertEqual(citation["target"]["params"]["searchContentHash"], citation["content_hash"])
