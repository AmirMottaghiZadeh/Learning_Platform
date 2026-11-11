from copy import deepcopy
from io import StringIO
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings

from . import access, evaluation, http_evaluation, release, review, test_reference_index as fixtures


class ReleaseTests(TestCase):
    setUp_source = fixtures.ReferenceIndexTests.setUp
    write_article = fixtures.ReferenceIndexTests.write_article

    def setUp(self):
        self.setUp_source()
        self.config = {"model": "unit-model", "code_digest": "a" * 64}
        self.cases = [{"id": f"case-{i}", "expect": "answerable", "question": f"پرسش {i}", "expected": [
            {"article_id": "3851", "headings": ["Treatment"]}]} for i in [1, 2]]
        self.cases.append({"id": "abstain", "expect": "abstain", "question": "یک شعر بنویس", "expected": []})
        self.dataset = {"schema": 1, "cases": self.cases}
        self.evidence = evaluation.SourceEvidence()
        self.rows = [self.row(case) for case in self.cases]
        self.reviews = {"schema": 1, "reviews": [{"case_id": row["case_id"], "response_digest": row["response_digest"],
            "reviewer": "Fixture reviewer", "correct_and_sufficient": True} for row in self.rows]}
        self.profile = {"unit": True, "model": "unit-model", "code_digest": "a" * 64}
        self.profile_patch = patch.object(release, "runtime_profile", return_value=self.profile)
        self.profile_patch.start()
        self.addCleanup(self.profile_patch.stop)
        frontend = patch.object(release, "frontend_digest", return_value="b" * 64)
        frontend.start(); self.addCleanup(frontend.stop)
        release._approved.cache_clear()
        self.addCleanup(release._approved.cache_clear)
        self.suite = {"configuration": self.config, "runs": self.rows}
        traffic = []
        for case in self.cases[:2]:
            for scenario in ["cold", "hit"]:
                row = self.row(case)
                row.update(scenario=scenario, client_elapsed_ms=1200, browser_elapsed_ms=1300, rendered_answer_complete=True)
                row["metrics"].update(response_cache="hit" if scenario == "hit" else "miss", provider_requests=0 if scenario == "hit" else 3)
                traffic.append(row)
        self.load = {"configuration": self.config, "runs": traffic, "runtime_profile_digest": evaluation.digest(self.profile),
                     "concurrency": 2, "observed_workers": 2, "shared_cache": True}
        self.browser = deepcopy(self.load)
        self.browser["served_bundle_digest"] = "b" * 64

    def row(self, case):
        bindings = self.evidence.bind(case)
        result = {"parts": []}
        if case["expect"] == "answerable":
            article, extracted = self.evidence.article("3851")
            block = extracted.blocks[0]
            citation = {"source_id": "P1", "source": "uptodate", "title": article["title"], "section": block.section_title,
                "quote": block.text, "summary_fa": "توضیح فارسی منبع", "content_hash": extracted.content_hash,
                "target": {"screen": "uptodateArticle", "params": {"id": "3851", "sectionId": block.section_id,
                    "searchAnchor": block.paragraph_id, "searchContentHash": extracted.content_hash}}}
            result["parts"] = [{"question_fa": case["question"], "status": "answered", "overview_fa": "توضیح فارسی منبع", "items": [citation]}]
        return {"case_id": case["id"], "question": case["question"], "expect": case["expect"], "status": "complete",
            "expected_sources": bindings, "result": result, "response_digest_schema": 2,
            "response_digest": evaluation.clinical_digest(case, bindings, self.config, result),
            "metrics": {"server_elapsed_ms": 1000, "provider_requests": 3},
            "assessment": evaluation.assess(case, result, bindings, self.evidence)}

    def gate(self, **kwargs):
        return release.evaluate_gate(kwargs.get("suite", self.suite), kwargs.get("load", self.load),
            kwargs.get("browser", self.browser), kwargs.get("reviews", self.reviews),
            dataset=self.dataset, evidence=self.evidence, min_api=2, min_browser=2)

    def test_complete_reviewed_bound_fixture_passes_and_pending_never_passes(self):
        self.assertEqual(self.gate()["decision"], "pass")
        pending = self.gate(reviews={"schema": 1, "reviews": []})
        self.assertIn("INDEPENDENT_REVIEW_REQUIRED", pending["blockers"])
        self.assertFalse(pending["release_slo_verified"])

    def test_changed_summary_cannot_keep_the_same_review_digest(self):
        suite = deepcopy(self.suite)
        suite["runs"][0]["result"]["parts"][0]["items"][0]["summary_fa"] = "توضیح تغییر کرده"
        with self.assertRaisesMessage(evaluation.EvaluationError, "RELEASE_RESPONSE_CHANGED"):
            self.gate(suite=suite)

    def test_cache_metadata_changes_do_not_require_reapproving_identical_clinical_content(self):
        row = deepcopy(self.rows[0])
        row["result"]["parts"][0]["retrieval"] = {"cache_hit": True, "reviewed_passages": 0}
        self.assertEqual(row["response_digest"], evaluation.clinical_digest(self.cases[0], row["expected_sources"], self.config, row["result"]))

    def test_missing_case_or_cold_measurement_cannot_be_hidden_by_fast_cache_samples(self):
        suite = {**self.suite, "runs": self.rows[:2]}
        self.assertIn("FULL_SUITE_REQUIRED", self.gate(suite=suite)["blockers"])
        load = deepcopy(self.load)
        load["runs"] = [row for row in load["runs"] if row["scenario"] == "hit"]
        self.assertIn("API_COLD_TARGET_NOT_MET", self.gate(load=load)["blockers"])
        load = deepcopy(self.load)
        load["runs"][0]["metrics"]["response_cache"] = "hit"
        self.assertIn("API_COLD_TARGET_NOT_MET", self.gate(load=load)["blockers"])

    def test_fast_rejection_single_worker_and_unpainted_ui_cannot_pass(self):
        load = deepcopy(self.load)
        load.update(observed_workers=1, shared_cache=False)
        load["runs"][0].update(client_elapsed_ms=1, status="failed")
        self.assertIn("SHARED_MULTIWORKER_LOAD_REQUIRED", self.gate(load=load)["blockers"])
        browser = deepcopy(self.browser)
        browser["runs"][0]["rendered_answer_complete"] = False
        self.assertIn("BROWSER_COLD_TARGET_NOT_MET", self.gate(browser=browser)["blockers"])

    def test_twenty_seconds_is_not_under_twenty_and_runtime_changes_block_release(self):
        load = deepcopy(self.load)
        load["runs"][0]["client_elapsed_ms"] = 20000
        self.assertIn("API_COLD_TARGET_NOT_MET", self.gate(load=load)["blockers"])
        load["runtime_profile_digest"] = "different"
        self.assertIn("API_RUNTIME_CHANGED", self.gate(load=load)["blockers"])
        browser = deepcopy(self.browser)
        browser["served_bundle_digest"] = "old-build"
        self.assertIn("BROWSER_BUILD_CHANGED", self.gate(browser=browser)["blockers"])

    def test_signed_expiring_approval_and_monotonic_cohorts_preserve_pilot_access(self):
        report = self.gate()
        path = self.directory / "approval.json"
        record = release.approval(report, hours=1)
        evaluation.write_private_json(path, record)
        with override_settings(AI_LAB_RELEASE_APPROVAL_FILE=str(path), AI_LAB_ROLLOUT_PERCENT=100):
            self.assertTrue(release.approved())
            self.assertTrue(release.cohort(SimpleNamespace(pk=7)))
        record["payload"]["expires_at"] += 1000
        path.write_text(json.dumps(record)); release._approved.cache_clear()
        with override_settings(AI_LAB_RELEASE_APPROVAL_FILE=str(path)):
            self.assertFalse(release.approved())
        with patch.object(release, "approved", return_value=True):
            cohorts = []
            for percent in [5, 25, 100]:
                with override_settings(AI_LAB_ROLLOUT_PERCENT=percent):
                    cohorts.append({n for n in range(100) if release.cohort(SimpleNamespace(pk=n))})
            self.assertTrue(cohorts[0] <= cohorts[1] <= cohorts[2])
        user = get_user_model().objects.create_user(username="phase-five-pilot")
        with override_settings(AI_LAB_ROLLOUT_PERCENT=100, AI_LAB_RELEASE_APPROVAL_FILE="", AI_LAB_USER_IDS={str(user.pk)}):
            self.assertTrue(access.allowed(user))
        with override_settings(AI_LAB_ROLLOUT_PERCENT=100, AI_LAB_RELEASE_APPROVAL_FILE="", AI_LAB_USER_IDS=set()):
            self.assertFalse(access.allowed(user))

    def test_blocked_gate_cannot_issue_approval(self):
        with self.assertRaisesMessage(evaluation.EvaluationError, "RELEASE_GATE_NOT_PASSED"):
            release.approval(self.gate(reviews={"schema": 1, "reviews": []}))

    def test_compound_missing_part_is_not_a_complete_answer(self):
        case = deepcopy(self.cases[0])
        case["expected"].append({**case["expected"][0], "part_index": 1})
        assessment = evaluation.assess(case, self.rows[0]["result"], self.evidence.bind(case), self.evidence)
        self.assertFalse(assessment["machine_complete"])

    def test_review_import_clears_removed_old_approval_and_requires_alternative_reason(self):
        rows = deepcopy(self.rows)
        evaluation.apply_reviews(rows, self.reviews)
        self.assertTrue(rows[0]["assessment"]["correct_and_sufficient"])
        evaluation.apply_reviews(rows, {"schema": 1, "reviews": []})
        self.assertIsNone(rows[0]["assessment"]["correct_and_sufficient"])
        invalid = deepcopy(self.reviews)
        invalid["reviews"][0]["accept_alternative_sources"] = True
        with self.assertRaisesMessage(evaluation.EvaluationError, "INVALID_SOURCE_REVIEW"):
            evaluation.apply_reviews(rows, invalid)

    def test_review_html_escapes_untrusted_text_and_never_preapproves(self):
        row = deepcopy(self.rows[0]); row["question"] = '<script>alert("question")</script>'
        row["result"]["parts"][0]["overview_fa"] = "توضیح اصلی که باید بازبینی شود"
        html = review.worksheet([{"runs": [row, row]}])
        self.assertIn('&lt;script&gt;', html)
        self.assertNotIn('<script>alert', html)
        self.assertEqual(html.count('data-case="case-1"'), 1)
        self.assertIn('value="" checked', html)
        self.assertIn("connect-src 'none'", html)
        self.assertIn("توضیح اصلی که باید بازبینی شود", html)
        abstain = review.worksheet([{"runs": [self.rows[-1]]}])
        self.assertIn('data-match="true"', abstain)

    def test_http_client_keeps_real_202_admission_status_and_reports_rejection(self):
        opener = MagicMock()
        response = opener.open.return_value.__enter__.return_value
        response.status = 202; response.read.return_value = b'{"job_id":"test"}'
        client = http_evaluation.Client("http://127.0.0.1:8000/api/v1", "private-token")
        with patch.object(http_evaluation, "build_opener", return_value=opener):
            status, body = client.json('/ai-lab/ask/', {})
        self.assertEqual(status, 202)
        self.assertEqual(body["job_id"], "test")
        with self.assertRaises(evaluation.EvaluationError):
            http_evaluation.Client("http://remote.example/api/v1", "private-token")
