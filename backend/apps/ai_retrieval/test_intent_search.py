from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase
from apps.ai_lab.test_hybrid_agent import reference
from . import embeddings, intent_search


class IntentSearchTests(SimpleTestCase):
    def test_sparse_original_ordinals_keep_the_opening_and_separate_runs(self):
        passages = [replace(reference(n), ordinal=n) for n in [15, 16, 17, 19, 20]]
        result = intent_search.read_ranges([["R1", "R5"]], passages)
        self.assertEqual([p.ordinal for p in result], [15, 16, 17, 19, 20])
        self.assertEqual([p.passage_run for p in result],
                         ["P15-P17"] * 3 + ["P19-P20"] * 2)

    def test_a_range_cannot_cross_an_article_or_invent_a_source(self):
        passages = [replace(reference(1), ordinal=1), replace(reference(2), article_id="other", ordinal=2)]
        selected = intent_search.read_ranges([["R1", "R2"], ["R0", "R1"], ["R1", "R1"]], passages)
        self.assertEqual([p.id for p in selected], ["P1"])

    def test_unoffered_article_or_section_is_rejected(self):
        self.assertEqual(intent_search.checked_ids(["S2", "S1", "S1"], {"S1"}, 2), ["S1"])
        self.assertEqual(intent_search.checked_ids(["S2"], {"S1"}, 2), [])

    def test_profile_check_reports_fields_without_exposing_endpoint(self):
        generation = SimpleNamespace(embedding_ready=True, embedding_profile={"base_url": "old", "id": "1"})
        with patch.object(embeddings, "profile", return_value={"base_url": "new", "id": "2"}):
            result = embeddings.profile_status(generation)
        self.assertEqual(result["code"], "EMBEDDING_PROFILE_CHANGED")
        self.assertEqual(result["changed_fields"], ["base_url", "id"])
        self.assertNotIn("old", str(result))
        self.assertNotIn("new", str(result))

    def test_supplement_must_use_an_original_planned_aspect(self):
        profile = {"kind": "disease_question", "objectives": ["drug_therapy"], "regimen_requested": True, "focus": "subject selection and regimen", "passage_queries": ["usual management", "applicable regimen"]}
        request = MagicMock()
        section = SimpleNamespace(pk="section-uuid", source_id="H1", heading="Evidence", heading_path=["Evidence"],
                                  article=SimpleNamespace(source_id="10"))
        source = replace(reference(1), ordinal=7)
        for aspect, gap in [(2, "applicable regimen"), (99, ""), (None, "")]:
            with self.subTest(aspect=aspect), patch.object(intent_search, "candidate_articles", return_value=(
                    {"10": SimpleNamespace(title="Reference")}, {"code": None}, 0)), patch.object(
                    intent_search, "section_options", return_value=({"S1": section}, [["S1", "10", "Evidence"]])), patch.object(
                    intent_search, "paragraph_options", return_value=[source]), patch.object(
                    intent_search, "decide", side_effect=[{"ids": ["10"]}, {"ids": ["S1"]},
                    {"ranges": [["R1","R1"]], "missing_aspect": aspect, "missing_query": "invented subgroup"}]):
                rows, _, missing = intent_search.collect(request, "query", "question", profile, {}, [])
                self.assertEqual([row.id for row in rows], ["P1"])
                self.assertEqual(missing, gap)
