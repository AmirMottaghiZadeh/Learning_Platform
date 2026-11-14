from concurrent.futures import ThreadPoolExecutor
import json
from threading import Barrier
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.test import SimpleTestCase, override_settings

from . import provider, telemetry


@override_settings(AI_LAB_MODEL="gpt-6-luna", AI_LAB_API_KEY="private-credential", AI_LAB_REASONING_EFFORT="low",
                   AI_LAB_CREDENTIALS_FILE="", AI_LAB_BASE_URL="https://provider.example/v1")
class TelemetryTests(SimpleTestCase):
    def response(self, *, finish="stop", content='{"ok":true}', usage=None):
        opener = MagicMock()
        data = {"model": "gpt-6-luna", "choices": [{"finish_reason": finish, "message": {"content": content}}]}
        if usage is not None:
            data["usage"] = usage
        opener.open.return_value.__enter__.return_value.read.return_value = json.dumps(data).encode()
        return opener

    def test_retries_record_both_attempts_and_their_reported_tokens(self):
        first = self.response(finish="length", content="", usage={"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120})
        second = self.response(usage={"prompt_tokens": 110, "completion_tokens": 10, "total_tokens": 120})
        trace = telemetry.Trace()
        with trace.activate(), patch.object(provider, "build_opener", side_effect=[first, second]):
            result, _ = telemetry.model_call("planning", provider.chat, "luna", "Return JSON", {}, 100)
        trace.finish("complete", answer_complete=True)
        metrics = trace.snapshot()
        self.assertEqual(result, {"ok": True})
        self.assertEqual(metrics["model_attempts"], 2)
        self.assertEqual(metrics["provider_requests"], 2)
        self.assertEqual(metrics["attempts"][0]["error_code"], "MODEL_OUTPUT_TRUNCATED")
        self.assertEqual(metrics["attempts"][1]["stage"], "planning")
        self.assertEqual(metrics["known_usage"], {"prompt_tokens": 210, "completion_tokens": 30, "total_tokens": 240})
        self.assertEqual(metrics["unknown_usage_requests"], 0)
        self.assertNotIn("private-credential", json.dumps(metrics))

    def test_provider_failure_remains_measured_with_unknown_usage(self):
        trace = telemetry.Trace()
        opener = MagicMock()
        opener.open.side_effect = HTTPError("https://provider.example", 503, "private upstream body", {}, None)
        with trace.activate(), patch.object(provider, "build_opener", return_value=opener):
            with self.assertRaises(provider.ProviderError):
                telemetry.model_call("answering", provider.chat, "luna", "Return JSON", {})
        trace.finish("failed")
        metrics = trace.snapshot()
        self.assertEqual(metrics["provider_requests"], 1)
        self.assertEqual(metrics["unknown_usage_requests"], 1)
        self.assertIsNone(metrics["final_answer_ms"])
        self.assertEqual(metrics["operations"]["answering"]["failed"], 1)
        self.assertNotIn("private upstream body", json.dumps(metrics))

    def test_missing_usage_and_boolean_fields_are_not_reported_as_complete_token_counts(self):
        trace = telemetry.Trace()
        response = self.response(usage={"prompt_tokens": True, "completion_tokens": 2})
        with trace.activate(), patch.object(provider, "build_opener", return_value=response):
            provider.chat("luna", "Return JSON", {})
        metrics = trace.snapshot()
        self.assertEqual(metrics["known_usage"]["completion_tokens"], 2)
        self.assertEqual(metrics["unknown_usage_requests"], 1)

    def test_known_usage_survives_malformed_choice(self):
        response = self.response(usage={"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7})
        data = {"model": "gpt-6-luna", "usage": {"prompt_tokens": 5, "completion_tokens": 2, "total_tokens": 7}, "choices": []}
        response.open.return_value.__enter__.return_value.read.return_value = json.dumps(data).encode()
        trace = telemetry.Trace()
        with trace.activate(), patch.object(provider, "build_opener", return_value=response):
            with self.assertRaisesMessage(provider.ProviderError, "INVALID_PROVIDER_RESPONSE"):
                provider.chat("luna", "Return JSON", {})
        self.assertEqual(trace.snapshot()["known_usage"]["total_tokens"], 7)

    def test_validation_failure_is_an_attempt_but_not_a_network_request(self):
        trace = telemetry.Trace()
        with trace.activate(), override_settings(AI_LAB_REASONING_EFFORT="bad"), patch.object(provider, "build_opener") as opener:
            with self.assertRaises(provider.ProviderError):
                provider.chat("luna", "Return JSON", {})
        self.assertEqual(trace.snapshot()["model_attempts"], 1)
        self.assertEqual(trace.snapshot()["provider_requests"], 0)
        opener.assert_not_called()

    def test_explicit_evaluation_budget_never_sends_request_after_limit_and_restores_context(self):
        response = self.response()
        with provider.evaluation_budget(1, 30) as budget, patch.object(provider, "build_opener", return_value=response):
            provider.chat("luna", "Return JSON", {})
            with self.assertRaisesMessage(provider.ProviderError, "EVALUATION_BUDGET_EXCEEDED"):
                provider.chat("luna", "Return JSON", {})
        self.assertEqual(budget["used"], 1)
        self.assertTrue(budget["exhausted"])
        self.assertEqual(response.open.call_count, 1)
        with patch.object(provider, "build_opener", return_value=response):
            provider.chat("luna", "Return JSON", {})
        self.assertEqual(response.open.call_count, 2)

    def test_queue_and_distinct_milestones_do_not_confuse_partial_with_final(self):
        with patch.object(telemetry.time, "perf_counter", return_value=10):
            trace = telemetry.Trace(queue_wait_ms=50)
        with patch.object(telemetry.time, "perf_counter", return_value=11):
            trace.mark("first_titles_ms")
        with patch.object(telemetry.time, "perf_counter", return_value=12):
            trace.mark("first_citation_ms")
            trace.finish("complete", answer_complete=False)
        metrics = trace.snapshot()
        self.assertEqual(metrics["first_titles_ms"], 1050)
        self.assertEqual(metrics["first_citation_ms"], 2050)
        self.assertEqual(metrics["server_elapsed_ms"], 2050)
        self.assertIsNone(metrics["first_sections_ms"])
        self.assertIsNone(metrics["final_answer_ms"])

    def test_parallel_traces_are_isolated_and_nested_context_is_restored(self):
        barrier = Barrier(2)
        def worker(stage):
            trace = telemetry.Trace()
            with trace.activate(), telemetry.operation(stage):
                barrier.wait(timeout=5)
                self.assertIs(telemetry.current_trace(), trace)
                nested = telemetry.Trace()
                with nested.activate():
                    self.assertIs(telemetry.current_trace(), nested)
                self.assertIs(telemetry.current_trace(), trace)
            return trace.snapshot()
        with ThreadPoolExecutor(max_workers=2) as pool:
            left, right = list(pool.map(worker, ["planning", "answering"]))
        self.assertEqual(set(left["operations"]), {"planning"})
        self.assertEqual(set(right["operations"]), {"answering"})
        self.assertIsNone(telemetry.current_trace())

    def test_attempt_storage_is_bounded_without_losing_totals(self):
        trace = telemetry.Trace()
        with trace.activate():
            for _ in range(260):
                with telemetry.model_attempt():
                    telemetry.provider_request_sent()
                    telemetry.provider_usage({"usage": {"total_tokens": 1}})
        metrics = trace.snapshot()
        self.assertEqual(len(metrics["attempts"]), 256)
        self.assertEqual(metrics["model_attempts"], 260)
        self.assertEqual(metrics["known_usage"]["total_tokens"], 260)
        self.assertTrue(metrics["attempts_limited"])
