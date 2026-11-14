from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
import zlib

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from apps.uptodate import services as utd
from apps.uptodate.tests import _make_snapshot
from . import evaluation, provider, services, telemetry


class EvaluationTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        _make_snapshot(self.tmp.name)
        body = '<div id="topicText"><p id="H1" class="headingAnchor"><span class="h1">Treatment</span></p><p>Original paragraph with a treatment recommendation and its necessary population qualifications.</p></div>'
        with sqlite3.connect(self.directory / "content.db") as connection:
            connection.execute("UPDATE content SET gzip=? WHERE id='3851'", (zlib.compress(json.dumps({
                "title": "Hypertension in adults", "bodyHtml": body,
            }).encode()),))
        self.settings = override_settings(UPTODATE_DB_DIR=self.tmp.name, UPTODATE_MYSQL_URL="")
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.addCleanup(utd.close_all)
        self.case = {"id": "test-one", "category": "treatment", "expect": "answerable", "question": "درمان چیست؟",
                     "expected": [{"article_id": "3851", "heading": "Treatment"}]}
        self.dataset = {"schema": 1, "version": "test-v1", "cases": [self.case]}
        self.dataset_path = self.directory / "cases.json"
        self.dataset_path.write_text(json.dumps(self.dataset))
        self.evidence = evaluation.SourceEvidence()
        self.bindings = self.evidence.bind(self.case)
        _, extracted = self.evidence.article("3851")
        block = extracted.blocks[0]
        self.citation = {"source_id": "P1", "source": "uptodate", "quote": block.text, "summary_fa": "توضیح فارسی مطابق بند منبع",
                         "content_hash": extracted.content_hash,
                         "target": {"screen": "uptodateArticle", "params": {"id": "3851", "sectionId": block.section_id,
                         "searchAnchor": block.paragraph_id, "searchContentHash": extracted.content_hash}}}
        self.result = {"parts": [{"status": "answered", "items": [self.citation]}]}

    def row(self, *, status="complete", result=None, elapsed=1000):
        result = self.result if result is None else result
        return {"case_id": self.case["id"], "category": "treatment", "expect": "answerable", "status": status,
                "response_digest": "a" * 64,
                "assessment": evaluation.assess(self.case, result, self.bindings, self.evidence),
                "metrics": {"server_elapsed_ms": elapsed}}

    def test_default_suite_has_100_unique_cases_and_no_vectors(self):
        dataset = evaluation.load_dataset()
        self.assertEqual(len(dataset["cases"]), 100)
        self.assertFalse(dataset["vectors"])
        self.assertEqual(sum(case["expect"] == "abstain" for case in dataset["cases"]), 5)
        self.assertEqual(sum(case["category"] == "compound" for case in dataset["cases"]), 5)

    def test_invalid_case_manifest_fails_before_execution(self):
        for mutate in [lambda data: data["cases"].append(data["cases"][0]),
                       lambda data: data["cases"][0].update(question="sk-" + "x" * 24),
                       lambda data: data["cases"][0].update(expected=[]),
                       lambda data: data["cases"][0].update(expect="unknown")]:
            data = deepcopy(self.dataset)
            mutate(data)
            self.dataset_path.write_text(json.dumps(data))
            with self.assertRaises(evaluation.EvaluationError):
                evaluation.load_dataset(self.dataset_path)

    def test_source_bindings_use_actual_hash_and_original_paragraph_ids_without_copying_text(self):
        binding = self.bindings[0]
        self.assertEqual(binding["content_hash"], self.citation["content_hash"])
        self.assertIn(self.citation["target"]["params"]["searchAnchor"], binding["paragraph_ids"])
        self.assertNotIn(self.citation["quote"], json.dumps(binding))
        with self.assertRaisesMessage(evaluation.EvaluationError, "EXPECTED_SECTION_MISSING"):
            self.evidence.bind({**self.case, "expected": [{"article_id": "3851", "heading": "Invented"}]})

    def test_original_quote_hash_section_and_anchor_must_all_match(self):
        self.assertTrue(self.evidence.citation_valid(self.citation))
        for key, value in [("quote", "Invented paragraph"), ("content_hash", "wrong")]:
            changed = deepcopy(self.citation)
            changed[key] = value
            self.assertFalse(self.evidence.citation_valid(changed))
        for key in ["sectionId", "searchAnchor", "searchContentHash"]:
            changed = deepcopy(self.citation)
            changed["target"]["params"][key] = "wrong"
            self.assertFalse(self.evidence.citation_valid(changed))

    def test_reference_match_is_not_clinical_approval(self):
        row = self.row()
        self.assertTrue(row["assessment"]["citation_integrity"])
        self.assertTrue(row["assessment"]["expected_sources_matched"])
        summary = evaluation.summarize([row])
        self.assertEqual(summary["machine_complete"], 1)
        self.assertEqual(summary["quality_verified_under_target"], 0)
        self.assertEqual(summary["pending_clinical_reviews"], 1)
        self.assertFalse(summary["provisional_service_target_met"])
        self.assertFalse(summary["release_slo_verified"])

    def test_compound_sources_must_match_their_own_part(self):
        bindings = [{**self.bindings[0], "part_index": 1}]
        assessed = evaluation.assess(self.case, self.result, bindings, self.evidence)
        self.assertFalse(assessed["expected_sources_matched"])

    def test_reviews_are_bound_to_response_digest_and_do_not_allow_stale_approval(self):
        row = self.row()
        review = {"case_id": row["case_id"], "response_digest": "b" * 64,
                  "reviewer": "reviewer", "correct_and_sufficient": True}
        evaluation.apply_reviews([row], {"schema": 1, "reviews": [review]})
        self.assertIsNone(row["assessment"]["correct_and_sufficient"])
        review["response_digest"] = row["response_digest"]
        evaluation.apply_reviews([row], {"schema": 1, "reviews": [review]})
        summary = evaluation.summarize([row], expected_suite_size=100)
        self.assertEqual(summary["quality_verified_under_target"], 1)
        self.assertTrue(summary["provisional_service_target_met"])
        self.assertFalse(summary["full_suite_measured"])
        self.assertFalse(summary["release_slo_verified"])

    def test_fast_errors_partials_bad_references_and_budget_cutoffs_never_pass(self):
        rows = [self.row(status="failed"), self.row(result={"parts": [{"status": "partial", "items": [self.citation]}]}),
                self.row(), self.row()]
        rows[2]["assessment"]["citation_integrity"] = False
        rows[3]["evaluation_budget_exhausted"] = True
        for row in rows:
            row["assessment"]["correct_and_sufficient"] = True
        summary = evaluation.summarize(rows)
        self.assertEqual(summary["answerable_cases"], 4)
        self.assertEqual(summary["quality_verified_success_rate"], 0)
        self.assertFalse(summary["provisional_service_target_met"])

    def test_percentiles_are_nearest_rank_and_empty_is_unknown(self):
        self.assertIsNone(evaluation.percentile([], .95))
        self.assertEqual(evaluation.percentile(list(range(1, 101)), .95), 95)
        self.assertEqual(evaluation.percentile([3, 1], .95), 3)

    def test_private_reports_refuse_overwrite_symlink_and_credentials(self):
        target = self.directory / "report.json"
        evaluation.write_private_json(target, {"safe": True})
        self.assertEqual(target.stat().st_mode & 0o777, 0o600)
        with self.assertRaises(FileExistsError):
            evaluation.write_private_json(target, {})
        link = self.directory / "link.json"
        link.symlink_to(target)
        with self.assertRaises(FileExistsError):
            evaluation.write_private_json(link, {})
        with self.assertRaisesMessage(evaluation.EvaluationError, "CREDENTIAL_IN_REPORT"):
            evaluation.write_private_json(self.directory / "unsafe.json", {"echo": "private-credential"}, secrets=["private-credential"])

    @patch.object(provider, "build_opener", side_effect=AssertionError("Validation must be free"))
    def test_validate_command_binds_sources_without_credentials_or_model_calls(self, opener):
        target = self.directory / "validation.json"
        call_command("evaluate_reference_search", mode="validate", dataset=str(self.dataset_path), output=str(target), stdout=StringIO())
        data = json.loads(target.read_text())
        self.assertEqual(data["provider_requests"], 0)
        self.assertEqual(data["invalid_cases"], 0)
        self.assertEqual(data["bindings"][0]["sources"], self.bindings)
        opener.assert_not_called()

    def test_run_command_keeps_environment_and_produces_comparable_private_report(self):
        target = self.directory / "baseline.json"
        def answer(*args, trace, **kwargs):
            trace.mark("first_titles_ms")
            trace.mark("first_citation_ms")
            trace.finish("complete", answer_complete=True)
            return self.result
        with patch.object(services, "answer", side_effect=answer), patch.object(provider, "credentials", return_value={"luna": "test-credential"}):
            call_command("evaluate_reference_search", mode="run", dataset=str(self.dataset_path),
                         output=str(target), stdout=StringIO())
        report = json.loads(target.read_text())
        self.assertEqual(report["summary"]["machine_complete"], 1)
        self.assertEqual(report["summary"]["quality_verified_under_target"], 0)
        self.assertEqual(report["budget"]["used"], 0)
        self.assertNotIn("test-credential", target.read_text())
        self.assertEqual(report["transport"], "direct_service")

    def test_invalid_heading_writes_validation_failure_report_but_prevents_live_run(self):
        self.dataset["cases"][0]["expected"][0]["heading"] = "Absent heading"
        self.dataset_path.write_text(json.dumps(self.dataset))
        target = self.directory / "invalid.json"
        with self.assertRaisesMessage(CommandError, "SOURCE_VALIDATION_FAILED"):
            call_command("evaluate_reference_search", mode="validate", dataset=str(self.dataset_path), output=str(target), stdout=StringIO())
        self.assertEqual(json.loads(target.read_text())["invalid_cases"], 1)
        with patch.object(provider, "build_opener") as opener, self.assertRaisesMessage(CommandError, "SOURCE_VALIDATION_FAILED"):
            call_command("evaluate_reference_search", mode="run", dataset=str(self.dataset_path), output=str(self.directory / "run.json"), stdout=StringIO())
        opener.assert_not_called()

    def test_run_case_records_partial_failure_instead_of_silent_loss(self):
        with patch.object(services, "answer", side_effect=provider.ProviderError("PROVIDER_UNAVAILABLE")):
            row = evaluation.run_case(self.case, self.bindings, self.evidence, {})
        self.assertEqual(row["status"], "failed")
        self.assertEqual(row["metrics"]["outcome"], "failed")
        self.assertIsNone(row["metrics"]["final_answer_ms"])

    def test_journal_recovers_completed_cases_after_an_incomplete_final_line(self):
        target = self.directory / "progress.jsonl"
        header = {"schema": 1, "kind": "reference_search_baseline_journal", "suite_size": 100}
        with target.open("w") as handle:
            evaluation.append_private_journal(handle, header)
            evaluation.append_private_journal(handle, self.row())
            handle.write('{"case_id":')
        report = evaluation.load_baseline(target)
        self.assertTrue(report["recovered_from_journal"])
        self.assertEqual(len(report["runs"]), 1)
        target.write_text(json.dumps(header) + "\n")
        self.assertEqual(evaluation.load_baseline(target)["runs"], [])

    @patch.object(provider, "build_opener", side_effect=AssertionError("Summarization must be free"))
    def test_summarize_never_calls_model_and_keeps_pending_reviews_out_of_success(self, opener):
        source = self.directory / "baseline.json"
        evaluation.write_private_json(source, {"kind": "reference_search_baseline", "suite_size": 100, "runs": [self.row()]})
        target = self.directory / "summary.json"
        call_command("evaluate_reference_search", mode="summarize", input=str(source), output=str(target), stdout=StringIO())
        report = json.loads(target.read_text())
        self.assertEqual(report["summary"]["machine_complete_under_target"], 1)
        self.assertEqual(report["summary"]["quality_verified_under_target"], 0)
        opener.assert_not_called()
