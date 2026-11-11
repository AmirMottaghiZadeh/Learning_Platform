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
    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    def test_first_line_returns_drug_and_source_regimen_with_separate_original_citations(self, search, read, chat):
        recommendation = passage(1, text="For the synthetic condition in adults, we recommend example drug X as first-line treatment.")
        regimen = passage(99, section="Administration", text="Example drug X: 5 mg orally once daily for seven days in the synthetic adult population only.")
        read.return_value = [{**group(), "passages": [recommendation]},
            {**group(2), "heading": "Administration", "passages": [regimen]}]
        name = {"source_id": "P1", "summary_fa": "برای جمعیت بزرگسال فرضی، داروی نمونهٔ X درمان خط اول منبع است."}
        dose = {"source_id": "P99", "summary_fa": "داروی نمونهٔ X در متن فرضی با مقدار ۵ میلی‌گرم خوراکی، روزی یک بار به مدت هفت روز آمده است."}
        chat.side_effect = [({"queries": ["synthetic condition"]}, {}), ({"items": [name, dose]}, {}),
            ({**decision(supported=("P1", "P99"), answer=("P1", "P99")), "regimen_complete": True}, {})]
        part = services.answer("خط اول درمان بیماری چیست؟", "luna", ["uptodate"], [], None)["parts"][0]
        self.assertEqual(part["status"], "answered")
        self.assertEqual([item["summary_fa"] for item in part["items"]], [name["summary_fa"], dose["summary_fa"]])
        self.assertEqual(part["items"][1]["quote"], regimen.text)
        self.assertEqual(part["items"][1]["target"], regimen.target)
        self.assertEqual(chat.call_count, 3)
        self.assertTrue(part["retrieval"]["early_stopped"])

    @override_settings(AI_LAB_LOCAL_SELECTION_ENABLED=False, AI_LAB_LEXICAL_ENABLED=False)
    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group()])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    def test_first_line_regimen_requirement_survives_retrieval_rollback(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"section_ids": ["T1"]}, {}),
            ({"items": [explanation()]}, {}), ({**decision(), "regimen_complete": False}, {})]
        part = services.answer("خط اول درمان چیست؟", "luna", ["uptodate"], [], None)["parts"][0]
        self.assertEqual(part["status"], "partial")
        self.assertIn("administration/dosing", chat.call_args_list[1].args[1])
        self.assertIn("regimen_complete", chat.call_args_list[3].args[1])

    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group(1, 7)])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}, {"id": "20", "title": "Later"}])
    def test_first_line_does_not_stop_at_drug_name_and_keeps_searching_same_article(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"items": [explanation()]}, {}),
            ({**decision(), "regimen_complete": False}, {}), ({"items": [explanation("P7")]}, {}),
            ({**decision(supported=("P7",), answer=("P1", "P7")), "regimen_complete": True}, {})]
        part = services.answer("خط اول درمان بیماری چیست؟", "luna", ["uptodate"], [], None)["parts"][0]
        self.assertEqual(part["status"], "answered")
        self.assertEqual([item["source_id"] for item in part["items"]], ["P1", "P7"])
        self.assertEqual(part["retrieval"]["reviewed_passages"], 7)
        self.assertEqual(chat.call_count, 5)
        self.assertIn("FIRST-LINE TREATMENT", chat.call_args_list[1].args[1])
        self.assertIn("regimen_complete", chat.call_args_list[2].args[1])
        read.assert_called_once()
        search.assert_called_once()

    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group()])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    def test_first_line_missing_regimen_stays_partial_with_explicit_notice(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"items": [explanation()]}, {}),
                            ({**decision(), "regimen_complete": False}, {})]
        result = services.answer("خط اول درمان چیست؟", "luna", ["uptodate"], [], None)
        part = result["parts"][0]
        self.assertEqual(part["status"], "partial")
        self.assertIn("دوزی حدس زده نشده", part["clarification_fa"])
        self.assertFalse(result["metrics"]["machine_answer_complete"])
        self.assertFalse(part["retrieval"]["early_stopped"])

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

    @override_settings(AI_LAB_MODEL="configured-model", AI_LAB_API_KEY="test-placeholder",
                       AI_LAB_REASONING_EFFORT="low", AI_LAB_CREDENTIALS_FILE="")
    @patch.object(services, "read_sections", return_value=[group(1, 13)])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}, {"id": "20", "title": "Second"}])
    def test_default_path_uses_three_actual_provider_requests_and_streams_sections_after_planning(self, search, read):
        outputs = [{"queries": ["concept"]}, {"items": [explanation()]}, decision()]
        responses = []
        for output in outputs:
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps({"model": "configured-model",
                "choices": [{"message": {"content": json.dumps(output)}, "finish_reason": "stop"}]}).encode()
            responses.append(response)
        observed, published = [], []
        with patch.object(provider, "build_opener") as factory:
            factory.return_value.open.side_effect = responses
            result = services.answer("درمان بیماری", "luna", ["uptodate"], [], None,
                observe=lambda event: observed.append((factory.return_value.open.call_count, event)), publish=published.append)
        self.assertEqual(result["parts"][0]["status"], "answered")
        self.assertEqual([stage["stage"] for stage in result["stages"]], ["planning", "answering", "verification"])
        self.assertEqual(result["metrics"]["provider_requests"], 3)
        self.assertEqual(result["metrics"]["model_attempts"], 3)
        self.assertEqual(result["metrics"]["operations"]["section_selection"]["count"], 1)
        section_event = next(row for row in observed if row[1]["type"] == "sections")
        self.assertEqual(section_event[0], 1)
        self.assertTrue(section_event[1]["sections"])
        self.assertTrue(published)
        self.assertTrue(result["parts"][0]["retrieval"]["early_stopped"])
        read.assert_called_once()
        search.assert_called_once()
        self.assertTrue(result["metrics"]["machine_answer_complete"])
        self.assertNotIn(fixtures.TEXT, json.dumps(result["metrics"]))

    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group(1, 13)])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}, {"id": "20", "title": "Second"}])
    def test_partial_first_batch_continues_same_article_and_keeps_previous_verified_evidence(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"items": [explanation()]}, {}),
            (decision(sufficient=False, answer=()), {}), ({"items": [explanation("P7")]}, {}),
            (decision(supported=("P7",), answer=("P1", "P7")), {})]
        published = []
        result = services.answer("مقایسه دو درمان", "luna", ["uptodate"], [], None, publish=published.append)
        part = result["parts"][0]
        self.assertEqual(part["status"], "answered")
        self.assertEqual(part["retrieval"]["reviewed_passages"], 12)
        self.assertEqual(chat.call_count, 5)
        self.assertEqual(chat.call_args_list[4].args[2]["previously_verified"][0]["id"], "P1")
        self.assertEqual({item["source_id"] for item in part["items"]}, {"P1", "P7"})
        self.assertEqual(len(published), 2)
        read.assert_called_once()

    @patch.object(services, "chat")
    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}, {"id": "20", "title": "Second"}])
    def test_partial_articles_never_mix_evidence_and_restart_current_item_ids(self, search, read, chat):
        read.side_effect = [[group(article_id="10")], [group(article_id="20")]]
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"items": [explanation()]}, {}),
            (decision(sufficient=False, answer=()), {}), ({"items": [explanation()]}, {}), (decision(), {})]
        result = services.answer("مقایسه دو درمان", "luna", ["uptodate"], [], None)
        part = result["parts"][0]
        self.assertEqual(part["retrieval"]["reviewed_articles"], 2)
        self.assertEqual(part["items"][0]["target"]["params"]["id"], "20")
        self.assertEqual(chat.call_args_list[4].args[2]["previously_verified"], [])

    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group()])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    def test_unsupported_population_or_claim_is_never_published(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"], "audience": "pediatric"}, {}), ({"items": [explanation()]}, {}),
                            (decision(supported=(), sufficient=False, answer=()), {})]
        publish = MagicMock()
        result = services.answer("درمان کودکان", "luna", ["uptodate"], [], None, publish=publish)
        self.assertEqual(result["parts"][0]["status"], "not_found")
        self.assertIsNone(result["metrics"]["final_answer_ms"])
        publish.assert_not_called()

    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group()])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    def test_unknown_model_identifiers_cannot_become_citations(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"items": [explanation("P999")]}, {})]
        result = services.answer("درمان بیماری", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"][0]["status"], "not_found")
        self.assertEqual(chat.call_count, 2)
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"items": [explanation()]}, {}),
                            (decision(supported=("P999",), answer=("P999",)), {})]
        with self.assertRaisesMessage(provider.ProviderError, "UNKNOWN_SOURCE_ID"):
            services.answer("درمان بیماری", "luna", ["uptodate"], [], None)

    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "Empty"}])
    def test_empty_article_does_not_call_model_for_section_selection(self, search, read, chat):
        chat.return_value = ({"queries": ["concept"]}, {})
        result = services.answer("درمان بیماری", "luna", ["uptodate"], [], None)
        self.assertEqual(chat.call_count, 1)
        self.assertEqual(result["parts"][0]["status"], "not_found")

    @patch.object(services, "chat", return_value=({"queries": []}, {}))
    @patch.object(services, "search_articles")
    def test_nonmedical_request_abstains_without_reading_source(self, search, chat):
        result = services.answer("یک شعر بنویس", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"], [])
        self.assertEqual(chat.call_count, 1)
        search.assert_not_called()

    @patch.object(services, "chat")
    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles")
    def test_compound_question_uses_three_calls_per_part_and_keeps_sources_separate(self, search, read, chat):
        search.side_effect = [[{"id": "10", "title": "First"}], [{"id": "20", "title": "Second"}]]
        read.side_effect = [[group(article_id="10")], [group(article_id="20")]]
        chat.side_effect = [({"queries": ["first concept"]}, {}), ({"queries": ["second concept"]}, {}),
            ({"items": [explanation()]}, {}), (decision(), {}), ({"items": [explanation()]}, {}), (decision(), {})]
        result = services.answer("سؤال اول؟ سؤال دوم؟", "luna", ["uptodate"], [], None)
        self.assertEqual(len(result["parts"]), 2)
        self.assertTrue(all(part["status"] == "answered" for part in result["parts"]))
        self.assertEqual([part["items"][0]["target"]["params"]["id"] for part in result["parts"]], ["10", "20"])
        self.assertEqual(chat.call_count, 6)
        self.assertEqual(chat.call_args_list[5].args[2]["previously_verified"], [])

    @patch.object(services, "chat")
    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles", return_value=[{"id": "112290", "title": "Aripiprazole formulations: Drug information"}])
    def test_drug_directory_is_followed_without_a_section_model_request(self, search, read, chat):
        def source(identifiers, request, audit, **kwargs):
            if identifiers == ["112290"]:
                audit["related_topics"] = [{"id": "8786", "title": "Aripiprazole"}]
                return []
            self.assertEqual(identifiers, ["8786"])
            return [group(article_id="8786")]
        read.side_effect = source
        chat.side_effect = [({"queries": ["aripiprazole"], "lookup_kind": "drug"}, {}),
                            ({"items": [explanation()]}, {}), (decision(), {})]
        result = services.answer("عوارض آریپیپرازول", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"][0]["status"], "answered")
        self.assertEqual(result["parts"][0]["items"][0]["target"]["params"]["id"], "8786")
        self.assertEqual(chat.call_count, 3)

    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group(1, 13)])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    def test_later_provider_failure_preserves_verified_partial_answer(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"items": [explanation()]}, {}),
                            (decision(sufficient=False, answer=()), {}), provider.ProviderError("PROVIDER_TIMEOUT")]
        result = services.answer("درمان بیماری", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"][0]["status"], "partial")
        self.assertEqual(result["parts"][0]["items"][0]["source_id"], "P1")
        self.assertIsNone(result["metrics"]["final_answer_ms"])
        self.assertFalse(result["metrics"]["machine_answer_complete"])

    @override_settings(AI_LAB_LOCAL_SELECTION_ENABLED=False)
    @patch.object(services, "chat")
    @patch.object(services, "read_sections", return_value=[group()])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    def test_explicit_rollback_keeps_model_section_selection(self, search, read, chat):
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"section_ids": ["T1"]}, {}),
                            ({"items": [explanation()]}, {}), (decision(), {})]
        part = services.answer("درمان بیماری", "luna", ["uptodate"], [], None)["parts"][0]
        self.assertEqual(part["status"], "answered")
        self.assertEqual(part["retrieval"]["article_attempts"][0]["selection_engine"], "model")
        self.assertEqual(chat.call_count, 4)


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
            if prompt == services.ANSWER_PROMPT:
                self.assertEqual(data["paragraphs"][0]["section"], "Adverse Reactions")
                return {"items": [explanation(data["paragraphs"][0]["id"])]}, {}
            self.assertEqual(prompt, services.VERIFY_PROMPT)
            identifier = data["items"][0]["id"]
            return decision(supported=(identifier,), answer=(identifier,)), {}
        with patch.object(services, "chat", side_effect=model) as chat, \
                patch.object(services, "search_articles", return_value=[{"id": "3851", "title": "Aripiprazole: Drug information"}]), \
                patch.object(retrieval.utd, "get_topic", side_effect=AssertionError("No source HTML at runtime")):
            result = services.answer("عوارض آریپیپرازول", "luna", ["uptodate"], [], None)
        self.assertEqual(chat.call_count, 3)
        citation = result["parts"][0]["items"][0]
        self.assertEqual(citation["source_id"], "P66")
        self.assertEqual(citation["target"]["params"]["sectionId"], "H99")
        self.assertTrue(citation["target"]["params"]["searchAnchor"])
        self.assertEqual(citation["target"]["params"]["searchContentHash"], citation["content_hash"])
