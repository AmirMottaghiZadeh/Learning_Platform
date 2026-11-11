from unittest.mock import patch

from django.db import connection
from django.test import SimpleTestCase, TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from apps.core.exceptions import PlatformAPIError
from . import lexical, retrieval, services, test_reference_index as fixtures


class LexicalRankingTests(SimpleTestCase):
    def test_first_line_implicitly_requests_regimen_but_other_queries_do_not(self):
        for question in ["خط اول درمان چیست؟", "درمان خط اول بیماری", "داروی خط اول چیست؟",
                         "خط‌اول‌درمان چیست", "درمان اولیه چیست؟", "first-line treatment", "first line therapy"]:
            with self.subTest(question=question):
                context = lexical.search_context(question, ["example condition"])
                self.assertTrue(context.first_line_regimen)
                self.assertIn("treatment", context.intents)
                self.assertIn("dosing", context.terms)
        for question in ["عوارض دارو چیست؟", "خط دوم درمان چیست؟", "درمان بیماری چیست؟"]:
            self.assertFalse(lexical.first_line_treatment(question))

    def test_first_line_ranks_administration_and_dose_evidence_without_changing_the_question(self):
        context = lexical.search_context("خط اول درمان بیماری چیست؟", ["example condition"])
        self.assertGreater(lexical.heading_score("Administration", [], context),
                           lexical.heading_score("Epidemiology", [], context))
        self.assertGreater(lexical.text_score("Example agent: 5 mg orally once daily, with source restrictions.", context),
                           lexical.text_score("Historical background for the example condition.", context))

    def context(self, question="عوارض داروی آریپیپرازول", **kwargs):
        return lexical.search_context(question, ["aripiprazole"], lookup_kind="drug", **kwargs)

    def test_intent_inference_and_terms_are_bounded_not_a_clinical_answer(self):
        context = self.context(keywords=["akathisia " * 100] * 40)
        self.assertIn("adverse_effects", context.intents)
        self.assertIn("aripiprazole", context.terms)
        self.assertLessEqual(len(context.terms), lexical.MAX_TERMS)
        self.assertTrue(all(len(term) <= 40 for term in context.terms))
        self.assertIn("renal_dose", self.context("تنظیم دوز در نارسایی کلیوی").intents)

    def test_topic_treatment_rank_preserves_tag_only_candidates_and_stable_ties(self):
        articles = [{"id": "1", "title": "Psoriasis: Epidemiology"},
                    {"id": "2", "title": "Psoriasis in children: Treatment"},
                    {"id": "3", "title": "Management of psoriasis in adults"},
                    {"id": "4", "title": "A tagged topic without query words"},
                    {"id": "5", "title": "A tagged topic without query words"}]
        context = lexical.search_context("درمان پسوریازیس بزرگسالان", ["psoriasis"], audience="adult")
        ranked = lexical.rank_topics(articles, context)
        self.assertEqual(ranked[0]["id"], "3")
        self.assertEqual({row["id"] for row in ranked}, {row["id"] for row in articles})
        self.assertLess([row["id"] for row in ranked].index("4"), [row["id"] for row in ranked].index("5"))
        self.assertEqual(articles[0]["id"], "1")

    def test_monograph_and_requested_population_priorities_dominate_keyword_overlap(self):
        articles = [{"id": "a", "title": "Aripiprazole treatment adverse reactions in adults"},
                    {"id": "b", "title": "Aripiprazole: Patient drug information"},
                    {"id": "c", "title": "Aripiprazole: Pediatric drug information"},
                    {"id": "d", "title": "Aripiprazole: Drug information"}]
        self.assertEqual(lexical.rank_topics(articles, self.context())[0]["id"], "d")
        self.assertEqual(lexical.rank_topics(articles, self.context(audience="pediatric"))[0]["id"], "c")
        self.assertEqual(lexical.rank_topics(articles, self.context(audience="patient"))[0]["id"], "b")

    def test_broad_treatment_prefers_overview_but_explicit_scope_keeps_specific_article(self):
        articles = [{"id": "specific", "title": "Plaque psoriasis in adults: Treatment with topical therapy"},
                    {"id": "overview", "title": "Plaque psoriasis in adults: Overview of management"}]
        context = lexical.search_context("خط اول درمان پسوریازیس چیست", ["plaque psoriasis"],
                                         audience="adult", keywords=["first-line treatment"])
        self.assertTrue(context.broad_treatment)
        self.assertEqual(lexical.rank_topics(articles, context)[0]["id"], "overview")
        context = lexical.search_context("درمان موضعی پسوریازیس چیست", ["plaque psoriasis"],
                                         audience="adult", keywords=["topical therapy"])
        self.assertFalse(context.broad_treatment)
        self.assertEqual(lexical.rank_topics(articles, context)[0]["id"], "specific")

    def test_parent_heading_promotes_specific_children_without_guessing_answer(self):
        context = self.context()
        self.assertGreater(lexical.heading_score("Akathisia", ["Adverse Reactions", "Akathisia"], context),
                           lexical.heading_score("Pharmacokinetics", ["Pharmacokinetics"], context))

    def test_explicit_aspect_outranks_incidental_treatment_word(self):
        context = lexical.search_context("پس از درمان اچ پیلوری چگونه ریشه کنی تایید می‌شود؟", ["h pylori"],
                                         keywords=["confirmation", "eradication", "test of cure"])
        self.assertGreater(lexical.heading_score("CONFIRMATION OF ERADICATION (TEST OF CURE)", [], context),
                           lexical.heading_score("Treatment", [], context))

    def test_broad_treatment_promotes_explicit_source_recommendation_over_repeated_keywords(self):
        context = lexical.search_context("خط اول درمان پسوریازیس چیست", ["psoriasis"], keywords=["first-line treatment"])
        background = "Background discussion of psoriasis, including the terminology first line. " * 30
        recommendation = "For patients with psoriasis, we suggest initial treatment subject to the original population restrictions."
        self.assertGreater(lexical.text_score(recommendation, context), lexical.text_score(background, context))

    def test_late_relevant_paragraph_becomes_first_without_changing_anchor_or_text(self):
        def passage(number, text):
            return retrieval.Passage(f"P{number}", "1", "Aripiprazole", "Adverse Reactions", text,
                                     {"params": {"searchAnchor": f"original-{number}"}}, "hash")
        first = passage(1, "Unrelated opening background.")
        last = passage(90, "Aripiprazole adverse reactions: original qualifications and restrictions.")
        sections = [{"id": "T1", "heading": "Adverse Reactions", "passages": [first, last]}]
        result = lexical.rank_memory_sections(sections, self.context(), {})
        self.assertIs(result[0]["passages"][0], last)
        self.assertEqual(last.target["params"]["searchAnchor"], "original-90")
        self.assertIs(sections[0]["passages"][0], first)

    def test_budget_keeps_whole_paragraphs_and_covers_selected_sections(self):
        def passage(number):
            return retrieval.Passage(f"P{number}", "1", "Title", "Heading", "x" * 5000, {}, "hash")
        sections = [{"id": "T1", "passages": [passage(n) for n in range(1, 30)]},
                    {"id": "T2", "passages": [passage(99)]}]
        audit = {}
        result = lexical.bounded_passages(sections, ["T1", "T2"], audit)
        self.assertEqual(result[1].id, "P99")
        self.assertLessEqual(sum(len(p.text) for p in result), lexical.MAX_PASSAGE_CHARACTERS)
        self.assertTrue(all(len(p.text) == 5000 for p in result))
        self.assertTrue(audit["limited"])
        self.assertLessEqual(len(result), lexical.MAX_RANKED_PASSAGES)

    @patch.object(services, "chat")
    def test_planner_retains_minimal_catalog_queries_and_separate_aspect(self, chat):
        chat.return_value = ({"queries": ["aripiprazole"], "lookup_kind": "drug", "audience": "general",
                              "intent": "adverse_effects", "keywords": ["adverse reactions"]}, {})
        plan = services.plan_question("عارضه آریپیپرازول چیست", [], [], "luna")[0]
        self.assertEqual(plan["queries"], ["aripiprazole"])
        self.assertEqual(plan["intent"], "adverse_effects")
        self.assertEqual(chat.call_count, 1)

    @patch.object(services, "chat")
    def test_bad_planner_retrieval_hints_are_rejected(self, chat):
        for extra in [{"intent": []}, {"intent": "invented"}, {"keywords": "string"}, {"keywords": [[]]}]:
            chat.return_value = ({"queries": ["aripiprazole"], **extra}, {})
            with self.assertRaisesMessage(services.ProviderError, "INVALID_MODEL_OUTPUT"):
                services.plan_question("عارضه آریپیپرازول چیست", [], [], "luna")

    @override_settings(AI_LAB_LEXICAL_ENABLED=False)
    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles")
    @patch.object(services, "chat")
    def test_feature_flag_restores_legacy_read_and_budget_with_four_model_calls(self, chat, search, read):
        p = retrieval.Passage("P1", "1", "Title", "Treatment", fixtures.TEXT, {}, "hash")
        search.return_value = [{"id": "1", "title": "Title"}]
        read.return_value = [{"id": "T1", "article_id": "1", "title": "Title", "heading": "Treatment",
                              "preview": fixtures.TEXT, "passages": [p]}]
        chat.side_effect = [({"queries": ["concept"]}, {}), ({"section_ids": ["T1"]}, {}),
                            ({"items": [{"source_id": "P1", "summary_fa": "توضیح فارسی مطابق با منبع"}]}, {}),
                            ({"supported": ["P1"], "sufficient": True, "answer_source_ids": ["P1"]}, {})]
        result = services.answer("درمان بیماری", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"][0]["status"], "answered")
        self.assertIsNone(read.call_args.kwargs["context"])
        self.assertEqual(chat.call_count, 4)


@override_settings(AI_LAB_PREPROCESSED_MODE="prefer", AI_LAB_LEXICAL_ENABLED=True)
class LexicalIndexTests(TestCase):
    # Reuse source-fixture helpers, not their test methods.
    setUp = fixtures.ReferenceIndexTests.setUp
    write_article = fixtures.ReferenceIndexTests.write_article
    add_title = fixtures.ReferenceIndexTests.add_title
    build = fixtures.ReferenceIndexTests.build

    def context(self):
        return lexical.search_context("عارضه مهم آریپیپرازول", ["aripiprazole"], lookup_kind="drug")

    def test_first_line_keeps_late_numeric_regimen_with_original_anchor_in_prepared_and_fallback(self):
        # Synthetic evidence, not a clinical dosing recommendation.
        body = '<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Summary and recommendations</span></p>'
        body += '<p>For this synthetic condition, we suggest initial treatment with the example agent, respecting all source restrictions.</p>'
        body += '<p class="headingAnchor" id="H2"><span class="h1">Administration</span></p>'
        body += ''.join(f'<p>Historical background paragraph {number} without medication details or a proposed regimen.</p>' for number in range(12))
        detail = 'Example agent: 5 mg orally once daily for the synthetic adult population only, with source restrictions.'
        body += '<p>' + detail + '</p></div>'
        self.write_article("3851", body)
        self.build()
        context = lexical.search_context("خط اول درمان بیماری چیست؟", ["synthetic condition"])
        indexed = retrieval.read_sections(["3851"], None, {}, context=context)
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            fallback = retrieval.read_sections(["3851"], None, {}, context=context)
        actual = next(p for section in indexed for p in section["passages"] if p.text == detail)
        other = next(p for section in fallback for p in section["passages"] if p.text == detail)
        self.assertEqual(actual, other)
        self.assertEqual(actual.target["params"]["sectionId"], "H2")
        self.assertTrue(actual.target["params"]["searchAnchor"])

    def make_long_article(self):
        body = '<div id="topicText">' + ''.join(
            f'<p class="headingAnchor" id="H{n}"><span class="h1">Background {n}</span></p><p>{fixtures.TEXT}</p>'
            for n in range(65))
        body += '<p class="headingAnchor" id="H99"><span class="h1">Significant Adverse Reactions</span></p>'
        body += ''.join(f'<p>{fixtures.TEXT} Historical information number {n}.</p>' for n in range(20))
        body += '<p>Aripiprazole adverse reactions include the exact original details, restrictions, and qualifications.</p></div>'
        self.write_article("3851", body, title="Aripiprazole: Drug information")
        return body

    def test_index_retrieves_relevant_section_after_sixty_and_late_block_first(self):
        self.make_long_article()
        self.build()
        audit = {}
        with patch.object(retrieval.utd, "get_topic", side_effect=AssertionError("No HTML")), \
                patch.object(retrieval, "extract_article", side_effect=AssertionError("No extraction")), \
                CaptureQueriesContext(connection) as queries:
            sections = retrieval.read_sections(["3851"], None, audit, context=self.context())
        self.assertEqual(sections[0]["heading"], "Significant Adverse Reactions")
        self.assertEqual(sections[0]["id"], "T66")
        best = sections[0]["passages"][0]
        self.assertIn("Aripiprazole adverse reactions", best.text)
        self.assertEqual(best.target["params"]["sectionId"], "H99")
        self.assertTrue(best.target["params"]["searchAnchor"])
        self.assertLessEqual(len(sections), lexical.MAX_RANKED_SECTIONS)
        self.assertLessEqual(len(queries), 6)
        self.assertTrue(all(query["sql"].lstrip().upper().startswith("SELECT") for query in queries))
        if connection.vendor == "postgresql":
            self.assertEqual(audit["lexical_engine"], "postgresql_fts")
            self.assertTrue(any("@@" in query["sql"] for query in queries))

    def test_index_and_fallback_keep_original_passage_targets(self):
        self.make_long_article()
        self.build()
        indexed = retrieval.read_sections(["3851"], None, {}, context=self.context())[0]["passages"][0]
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            fallback = retrieval.read_sections(["3851"], None, {}, context=self.context())[0]["passages"][0]
        self.assertEqual(indexed, fallback)

    def test_english_stemming_matches_variant_without_loading_all_paragraphs(self):
        self.write_article("3851", fixtures.html(text="The prescribed therapies include medications with original population restrictions and qualifications."))
        self.build()
        context = lexical.search_context("درمان", ["therapy"], keywords=["medication"])
        audit = {}
        result = retrieval.read_sections(["3851"], None, audit, context=context)
        self.assertTrue(result)
        self.assertGreater(audit["lexical_hits"], 0)

    def test_excluded_blocks_never_become_fts_evidence(self):
        body = '<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Adverse Reactions</span></p><p>'
        body += "Aripiprazole adverse reactions " * 250
        body += '</p><p class="headingAnchor" id="H2"><span class="h1">Warnings</span></p><p>' + fixtures.TEXT + '</p></div>'
        self.write_article("3851", body)
        self.build()
        sections = retrieval.read_sections(["3851"], None, {}, context=self.context())
        self.assertTrue(all(len(p.text) <= 6000 for section in sections for p in section["passages"]))
        self.assertFalse(any("Aripiprazole" in p.text for section in sections for p in section["passages"]))

    def test_no_lexical_matches_preserves_opening_context(self):
        self.build()
        context = lexical.search_context("سوال", ["unmatchableword"])
        result = retrieval.read_sections(["3851"], None, {}, context=context)
        self.assertEqual(result[0]["passages"][0].text, fixtures.TEXT)

    def test_permissions_precede_lexical_queries(self):
        with patch.object(retrieval, "require_feature", side_effect=PlatformAPIError("Denied", status_code=402)), \
                patch.object(lexical, "prepared_sections") as prepared:
            with self.assertRaises(PlatformAPIError):
                retrieval.read_sections(["3851"], None, {}, context=self.context())
        prepared.assert_not_called()

    def test_stale_index_falls_back_and_require_mode_refuses_old_content(self):
        self.build()
        self.write_article("3851", fixtures.html(text=fixtures.TEXT + " A new source update."))
        audit = {}
        result = retrieval.read_sections(["3851"], None, audit, context=self.context())
        self.assertIn("new source update", result[0]["passages"][0].text)
        self.assertEqual(audit["lexical_engine"], "memory")
        with override_settings(AI_LAB_PREPROCESSED_MODE="require"), self.assertRaises(services.ProviderError):
            retrieval.read_sections(["3851"], None, {}, context=self.context())

    def test_multiple_articles_preserve_unique_section_and_paragraph_ids(self):
        self.make_long_article()
        self.add_title("3852")
        self.write_article("3852", fixtures.html(heading="Adverse Reactions", text=fixtures.TEXT))
        self.build()
        sections = retrieval.read_sections(["3851", "3852"], None, {}, context=self.context())
        identifiers = [section["id"] for section in sections]
        self.assertEqual(len(identifiers), len(set(identifiers)))
        identifiers = [p.id for section in sections for p in section["passages"]]
        self.assertEqual(len(identifiers), len(set(identifiers)))

    @patch.object(services, "chat", side_effect=AssertionError("Offline evaluation must not call a model"))
    def test_fixed_plan_evaluation_writes_private_report_and_verifies_original_anchors(self, chat):
        from django.core.management import call_command
        from io import StringIO
        import json

        self.build()
        dataset = {"schema": 1, "cases": [{"id": "test", "question": "درمان چیست", "expect": "answerable",
            "expected": [{"article_id": "3851", "headings": ["Treatment"]}]}]}
        plans = {"schema": 1, "plans": [{"case_id": "test", "queries": ["reference"], "intent": "treatment"}]}
        dataset_file, plans_file, output = [self.directory / name for name in ["cases.json", "plans.json", "report.json"]]
        dataset_file.write_text(json.dumps(dataset))
        plans_file.write_text(json.dumps(plans))
        with patch.object(retrieval, "search_articles", return_value=[{"id": "3851", "title": "Reference article"}]):
            call_command("evaluate_lexical_retrieval", dataset=str(dataset_file), plans=str(plans_file),
                         output=str(output), repeat=1, stdout=StringIO())
        report = json.loads(output.read_text())
        self.assertEqual(report["provider_requests"], 0)
        self.assertTrue(report["summary"]["all_source_anchors_valid"])
        self.assertEqual(report["summary"]["all_expected_headings_available"], 1)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        self.assertNotIn(fixtures.TEXT, output.read_text())
        chat.assert_not_called()
