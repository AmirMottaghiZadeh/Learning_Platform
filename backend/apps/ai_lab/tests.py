import json
import os
from pathlib import Path
import sqlite3
import tempfile
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from apps.core.exceptions import PlatformAPIError
from apps.uptodate import services as utd
from apps.uptodate.tests import _make_snapshot, _add_concept_snapshot
from . import jobs, provider, retrieval, services, views, warmup, workflow

QUOTE = "This is an original reference passage describing the population and intervention with its qualifications."


def passage(n=1):
    return retrieval.Passage(f"P{n}", "10", "Reference title", "Treatment", QUOTE,
        {"screen": "uptodateArticle", "params": {"id": "10", "searchAnchor": "utd-" + "a" * 32,
         "searchContentHash": "b" * 64}}, "b" * 64)


@override_settings(AI_LAB_MODEL="gpt-6-luna", AI_LAB_API_KEY="", AI_LAB_REASONING_EFFORT=None,
                   AI_LAB_LUNA_API_KEY="test-placeholder",
                   AI_LAB_CREDENTIALS_FILE="", AI_LAB_BASE_URL="https://api.gapgpt.app/v1", AI_LAB_LUNA_REASONING_EFFORT="low")
class ProviderTests(SimpleTestCase):
    def response(self, value):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value = json.dumps(value).encode()
        return opener

    def test_provider_error_never_exposes_body_or_authorization(self):
        error = HTTPError("https://api.gapgpt.app", 500, "sensitive upstream error", {}, None)
        with patch.object(provider, "build_opener") as factory:
            factory.return_value.open.side_effect = error
            with self.assertRaises(provider.ProviderError) as raised:
                provider.call("luna", {})
        self.assertEqual(str(raised.exception), "PROVIDER_HTTP_ERROR")
        self.assertEqual(raised.exception.status, 500)

    def test_refuses_http_and_redirects(self):
        with override_settings(AI_LAB_BASE_URL="http://localhost/v1"), patch.object(provider, "build_opener") as opener:
            with self.assertRaisesMessage(provider.ProviderError, "INVALID_PROVIDER_URL"):
                provider.call("luna", {})
            opener.assert_not_called()
        self.assertIsNone(provider.NoRedirect().redirect_request(None))

    @override_settings(AI_LAB_MODEL="provider/model-name", AI_LAB_API_KEY="other-provider-credential",
                       AI_LAB_REASONING_EFFORT="")
    def test_custom_provider_base_url_controls_the_actual_chat_request(self):
        for base in ("https://provider.example/custom/v1", " https://provider.example/custom/v1/ "):
            response = self.response({"model": "provider/model-name", "choices": [
                {"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}]})
            with self.subTest(base=base), override_settings(AI_LAB_BASE_URL=base), patch.object(provider, "build_opener", return_value=response):
                result, meta = provider.chat("luna", "Return JSON", {})
            sent = response.open.call_args.args[0]
            self.assertEqual(sent.full_url, "https://provider.example/custom/v1/chat/completions")
            self.assertEqual(sent.get_header("Authorization"), "Bearer other-provider-credential")
            self.assertEqual(json.loads(sent.data)["model"], "provider/model-name")
            self.assertNotIn("reasoning_effort", json.loads(sent.data))
            self.assertEqual(result, {"ok": True})
            self.assertEqual(meta["model"], "provider/model-name")

    def test_invalid_provider_urls_are_rejected_before_sending_credentials(self):
        for base in ("", "https:///v1", "https://provider.example:invalid/v1",
                     "https://provider.example:0/v1", "https://provider.example:65536/v1",
                     "https://user:password@provider.example/v1", "https://provider.example/v1?key=value",
                     "https://provider.example/v1#fragment", "https://provider.example/\nv1"):
            with self.subTest(base=base), override_settings(AI_LAB_BASE_URL=base), patch.object(provider, "build_opener") as opener:
                with self.assertRaisesMessage(provider.ProviderError, "INVALID_PROVIDER_URL"):
                    provider.call("luna", {})
                opener.assert_not_called()

    def test_rejects_credential_echo_and_wrong_model(self):
        for value, code in [({"output": "test-placeholder"}, "UNSAFE_PROVIDER_RESPONSE"),
                            ({"model": "other-model"}, "MODEL_MISMATCH")]:
            with patch.object(provider, "build_opener", return_value=self.response(value)):
                with self.assertRaisesMessage(provider.ProviderError, code):
                    provider.call("luna", {})

    def test_metadata_records_reported_model_and_only_numeric_usage(self):
        value = {"model": "gpt-6-luna", "usage": {"prompt_tokens": 12, "other": "private"}}
        with patch.object(provider, "build_opener", return_value=self.response(value)):
            _, meta = provider.call("luna", {})
        self.assertEqual(meta["reported_model"], "gpt-6-luna")
        self.assertEqual(meta["usage"], {"prompt_tokens": 12})

    def test_external_credentials_require_private_permissions(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials"
            path.write_text("pharmenta_luna:\nsk-" + "c" * 24)
            with override_settings(AI_LAB_LUNA_API_KEY="", AI_LAB_CREDENTIALS_FILE=str(path)):
                os.chmod(path, 0o644)
                with self.assertRaisesMessage(provider.ProviderError, "CREDENTIAL_FILE_PERMISSIONS"):
                    provider.credentials()
                os.chmod(path, 0o600)
                self.assertEqual(set(provider.credentials()), {"luna"})
                self.assertTrue(all(provider.credentials().values()))
                with override_settings(AI_LAB_LUNA_API_KEY="environment-credential"):
                    self.assertEqual(provider.credentials()["luna"], "environment-credential")

    def test_luna_uses_its_own_credential_and_never_falls_back_to_another_label(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials"
            path.write_text("pharmenta_deepseek:\nsk-" + "b" * 24)
            path.chmod(0o600)
            with override_settings(AI_LAB_LUNA_API_KEY="", AI_LAB_CREDENTIALS_FILE=str(path)), patch.object(provider, "build_opener") as opener:
                with self.assertRaisesMessage(provider.ProviderError, "KEY_NOT_CONFIGURED"):
                    provider.call("luna", {})
                opener.assert_not_called()

    def test_luna_only_file_configures_only_luna_and_reads_replaced_key(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "credentials"
            first, second = "sk-" + "c" * 24, "sk-" + "d" * 24
            path.write_text("pharmenta_luna:\n" + first)
            path.chmod(0o600)
            with override_settings(AI_LAB_LUNA_API_KEY="",
                                   AI_LAB_CREDENTIALS_FILE=str(path)):
                self.assertEqual(provider.credentials(), {"luna": first})
                path.write_text("pharmenta_luna:\n" + second)
                self.assertEqual(provider.credentials(), {"luna": second})

    def test_luna_sends_compatible_parameters_with_low_reasoning_and_no_model_substitution(self):
        response = self.response({"model": "gpt-6-luna", "choices": [
            {"message": {"content": '{"queries":["nocturnal enuresis"]}'}, "finish_reason": "stop"}]})
        with patch.object(provider, "build_opener", return_value=response):
            result, meta = provider.chat("luna", "Return JSON", {"question": "سؤال"}, 700)
        self.assertEqual(result["queries"], ["nocturnal enuresis"])
        self.assertEqual(meta["model"], "gpt-6-luna")
        request = response.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.gapgpt.app/v1/chat/completions")
        sent = json.loads(request.data)
        self.assertEqual(sent["model"], "gpt-6-luna")
        self.assertEqual(sent["reasoning_effort"], "low")
        self.assertEqual(sent["max_completion_tokens"], 700)
        self.assertNotIn("max_tokens", sent)
        self.assertNotIn("temperature", sent)

    def test_luna_rejects_an_upstream_response_from_a_different_model(self):
        with patch.object(provider, "build_opener", return_value=self.response({"model": "other-model"})):
            with self.assertRaisesMessage(provider.ProviderError, "MODEL_MISMATCH"):
                provider.call("luna", {})

    def test_global_deadline_prevents_another_provider_call(self):
        token = provider.deadline.set(0)
        try:
            with patch.object(provider, "build_opener") as opener:
                with self.assertRaisesMessage(provider.ProviderError, "EXPERIMENT_TIMEOUT"):
                    provider.call("luna", {})
                opener.assert_not_called()
        finally:
            provider.deadline.reset(token)

    def test_truncated_output_retries_with_more_output_capacity(self):
        short = self.response({"model": "gpt-6-luna", "choices": [
            {"message": {"content": ""}, "finish_reason": "length"}]})
        complete = self.response({"model": "gpt-6-luna", "choices": [
            {"message": {"content": '{"supported": ["P1"]}'}, "finish_reason": "stop"}]})
        with patch.object(provider, "build_opener", side_effect=[short, complete]):
            result, _ = provider.chat("luna", "Return JSON", {}, 650)
        self.assertEqual(result, {"supported": ["P1"]})
        first = json.loads(short.open.call_args.args[0].data)
        second = json.loads(complete.open.call_args.args[0].data)
        self.assertGreater(second["max_completion_tokens"], first["max_completion_tokens"])
        self.assertEqual(first["reasoning_effort"], "low")
        self.assertEqual(second["reasoning_effort"], "low")

    def test_removed_models_never_reach_the_provider(self):
        with patch.object(provider, "build_opener") as opener:
            for model in ("gemma", "deepseek"):
                with self.assertRaisesMessage(provider.ProviderError, "MODEL_NOT_SUPPORTED"):
                    provider.call(model, {})
                with self.assertRaisesMessage(provider.ProviderError, "MODEL_NOT_SUPPORTED"):
                    provider.chat(model, "Return JSON", {})
        opener.assert_not_called()

    def test_provider_request_model_is_pinned_to_luna(self):
        response = self.response({"model": "gpt-6-luna"})
        with patch.object(provider, "build_opener", return_value=response):
            provider.call("luna", {"model": "other-model"})
        self.assertEqual(json.loads(response.open.call_args.args[0].data)["model"], "gpt-6-luna")

    def test_reasoning_effort_comes_from_server_settings_and_invalid_values_make_no_request(self):
        response = self.response({"model": "gpt-6-luna", "choices": [
            {"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}]})
        with override_settings(AI_LAB_LUNA_REASONING_EFFORT="high"), patch.object(provider, "build_opener", return_value=response):
            provider.chat("luna", "Return JSON", {}, 700)
        self.assertEqual(json.loads(response.open.call_args.args[0].data)["reasoning_effort"], "high")
        with override_settings(AI_LAB_LUNA_REASONING_EFFORT="invalid"), patch.object(provider, "build_opener") as opener:
            with self.assertRaisesMessage(provider.ProviderError, "INVALID_REASONING_EFFORT"):
                provider.chat("luna", "Return JSON", {})
            opener.assert_not_called()

    @override_settings(AI_LAB_MODEL="configured-model", AI_LAB_API_KEY="generic-credential",
                       AI_LAB_REASONING_EFFORT=" HIGH ")
    def test_server_configuration_controls_request_credentials_reasoning_and_metadata(self):
        response = self.response({"model": "configured-model-2026-11-10", "choices": [
            {"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}]})
        with patch.object(provider, "build_opener", return_value=response):
            result, meta = provider.chat("luna", "Return JSON", {}, 700)
        sent = response.open.call_args.args[0]
        self.assertEqual(result, {"ok": True})
        self.assertEqual(json.loads(sent.data)["model"], "configured-model")
        self.assertEqual(json.loads(sent.data)["reasoning_effort"], "high")
        self.assertEqual(sent.get_header("Authorization"), "Bearer generic-credential")
        self.assertEqual(meta["model"], "configured-model")
        self.assertEqual(meta["reported_model"], "configured-model-2026-11-10")

    @override_settings(AI_LAB_MODEL="configured-model")
    def test_custom_model_is_pinned_and_luna_is_no_longer_an_accepted_response(self):
        response = self.response({"model": "configured-model"})
        with patch.object(provider, "build_opener", return_value=response):
            provider.call("luna", {"model": "gpt-6-luna"})
        self.assertEqual(json.loads(response.open.call_args.args[0].data)["model"], "configured-model")
        for reported in ("gpt-6-luna", "configured-model-other", "other/configured-model"):
            with self.subTest(reported=reported), patch.object(provider, "build_opener", return_value=self.response({"model": reported})):
                with self.assertRaisesMessage(provider.ProviderError, "MODEL_MISMATCH"):
                    provider.chat("luna", "Return JSON", {})

    def test_invalid_server_model_never_reaches_provider(self):
        for model in ("", "bad model", "bad\nmodel", "x" * 121):
            with self.subTest(model=model), override_settings(AI_LAB_MODEL=model), patch.object(provider, "build_opener") as opener:
                with self.assertRaisesMessage(provider.ProviderError, "INVALID_MODEL_CONFIGURATION"):
                    provider.call("luna", {})
                opener.assert_not_called()

    @override_settings(AI_LAB_REASONING_EFFORT="")
    def test_empty_reasoning_setting_omits_parameter_instead_of_using_legacy_value(self):
        response = self.response({"model": "gpt-6-luna", "choices": [
            {"message": {"content": '{"ok":true}'}, "finish_reason": "stop"}]})
        with patch.object(provider, "build_opener", return_value=response):
            provider.chat("luna", "Return JSON", {})
        self.assertNotIn("reasoning_effort", json.loads(response.open.call_args.args[0].data))


class GroundingTests(SimpleTestCase):
    def setUp(self):
        network = patch.object(provider, "build_opener", side_effect=AssertionError("Unexpected live provider call"))
        network.start()
        self.addCleanup(network.stop)

    def section(self, article_id="10", count=1):
        paragraphs = [retrieval.Passage(f"P{n}", article_id, f"Article {article_id}", "Treatment", QUOTE,
            {"screen": "uptodateArticle", "params": {"id": article_id}}, "b" * 64) for n in range(1, count + 1)]
        return {"id": "T1", "article_id": article_id, "title": f"Article {article_id}", "heading": "Treatment",
                "preview": QUOTE, "passages": paragraphs}

    def item(self, identifier="P1"):
        return {"source_id": identifier, "summary_fa": "توضیح فارسی مطابق متن اصلی منبع"}

    def decision(self, supported=("P1",), sufficient=True, answer=("P1",)):
        return {"supported": list(supported), "sufficient": sufficient, "answer_source_ids": list(answer)}

    @override_settings(AI_LAB_MODEL="configured-model", AI_LAB_API_KEY="test-placeholder",
                       AI_LAB_REASONING_EFFORT="low", AI_LAB_CREDENTIALS_FILE="")
    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles")
    def test_all_search_stages_use_the_server_configured_model(self, search, read):
        search.return_value = [{"id": "10", "title": "Reference title"}]
        read.return_value = [self.section()]
        outputs = [{"queries": ["treatment"]}, {"section_ids": ["T1"]},
                   {"items": [self.item()]}, self.decision()]
        responses = []
        for output in outputs:
            response = MagicMock()
            response.__enter__.return_value.read.return_value = json.dumps({
                "model": "configured-model", "choices": [{"message": {"content": json.dumps(output)},
                                                            "finish_reason": "stop"}],
            }).encode()
            responses.append(response)
        with patch.object(provider, "build_opener") as factory:
            factory.return_value.open.side_effect = responses
            result = services.answer("درمان بیماری چیست؟", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"][0]["status"], "answered")
        calls = factory.return_value.open.call_args_list
        self.assertEqual(len(calls), 4)
        self.assertEqual([json.loads(call.args[0].data)["model"] for call in calls], ["configured-model"] * 4)
        self.assertTrue(result["stages"])
        self.assertTrue(all(stage["model"] == "configured-model" for stage in result["stages"]))

    def test_unknown_id_modified_quote_or_non_persian_summary_is_removed(self):
        good = self.item()
        self.assertEqual(services._validated_items([good], [passage()])[0]["quote"], QUOTE)
        for invalid in [{"source_id": "unknown"}, {"source_id": []}, {"quote": "invented"}, {"summary_fa": "English only"}]:
            self.assertEqual(services._validated_items([{**good, **invalid}], [passage()]), [])

    @patch.object(services, "chat")
    def test_retired_models_and_other_sources_never_make_provider_calls(self, chat):
        for model, sources in [("jev", ["uptodate"]), ("glm", ["uptodate"]), ("gemma", ["uptodate"]), ("deepseek", ["uptodate"]), ("luna", ["medscape"])]:
            with self.assertRaises(provider.ProviderError):
                services.answer("سؤال", model, sources, [], None)
        chat.assert_not_called()

    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles")
    @patch.object(services, "chat")
    def test_sufficient_first_article_stops_later_articles_queries_and_paragraph_batches(self, chat, search, read):
        search.return_value = [{"id": "10", "title": "First tagged article"}, {"id": "20", "title": "Second article"}]
        read.return_value = [self.section(count=13)]
        for model in provider.MODEL_ALIASES:
            with self.subTest(model=model):
                chat.reset_mock(); search.reset_mock(); read.reset_mock()
                chat.side_effect = [({"queries": ["enuresis", "alternate"]}, {}), ({"section_ids": ["T1"]}, {}),
                    ({"items": [self.item(), self.item("P2")]}, {}), (self.decision(supported=("P1", "P2")), {})]
                observed = []
                result = services.answer("دارودرمانی شب ادراری در کودکان چیست", model, ["uptodate"], [], None,
                    observe=lambda event: observed.append((chat.call_count, event)))
                part = result["parts"][0]
                self.assertEqual(part["status"], "answered")
                self.assertEqual(part["clarification_fa"], "")
                self.assertEqual(len(part["items"]), 1)  # Only evidence needed for the sufficient answer.
                self.assertTrue(part["overview_fa"])
                self.assertTrue(part["retrieval"]["early_stopped"])
                self.assertEqual(part["retrieval"]["reviewed_articles"], 1)
                self.assertEqual(part["retrieval"]["reviewed_passages"], 6)
                self.assertEqual(len(chat.call_args_list), 4)
                self.assertTrue(all(call.args[0] == model for call in chat.call_args_list))
                self.assertEqual(search.call_args.args[0], ["enuresis"])
                search.assert_called_once()
                read.assert_called_once()
                self.assertEqual(read.call_args.args[0], ["10"])
                titles = next((count, event) for count, event in observed if event["type"] == "titles")
                sections = next((count, event) for count, event in observed if event["type"] == "sections")
                self.assertEqual(titles[0], 1)  # Available before the section-selection model call.
                self.assertEqual([row["id"] for row in titles[1]["articles"]], ["10", "20"])
                self.assertEqual(sections[0], 2)  # Available before Persian answer generation.
                self.assertEqual(sections[1]["sections"], [{"id": "T1", "heading": "Treatment"}])
                self.assertEqual(observed[-1][1]["outcome"], "answered")
                self.assertTrue(all("citations" not in event for _, event in observed))

    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles")
    @patch.object(services, "chat")
    def test_verified_but_incomplete_first_article_advances_without_mixing_articles(self, chat, search, read):
        search.return_value = [{"id": "10", "title": "First"}, {"id": "20", "title": "Second"}]
        read.side_effect = [[self.section("10")], [self.section("20")]]
        chat.side_effect = [({"queries": ["topic"]}, {}), ({"section_ids": ["T1"]}, {}),
            ({"items": [self.item()]}, {}), (self.decision(sufficient=False, answer=()), {}),
            ({"section_ids": ["T1"]}, {}), ({"items": [self.item()]}, {}), (self.decision(), {})]
        result = services.answer("مقایسه دو درمان", "luna", ["uptodate"], [], None)
        part = result["parts"][0]
        self.assertEqual(part["retrieval"]["reviewed_articles"], 2)
        self.assertEqual(part["retrieval"]["answer_article_id"], "20")
        self.assertEqual({item["target"]["params"]["id"] for item in part["items"]}, {"20"})
        self.assertEqual(chat.call_args_list[6].args[2]["previously_verified"], [])
        self.assertEqual([call.args[0] for call in read.call_args_list], [["10"], ["20"]])

    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}, {"id": "20", "title": "Second"}])
    @patch.object(services, "chat")
    def test_next_batch_in_same_article_can_complete_answer_before_next_article(self, chat, search, read):
        read.return_value = [self.section(count=13)]
        chat.side_effect = [({"queries": ["topic"]}, {}), ({"section_ids": ["T1"]}, {}),
            ({"items": [self.item()]}, {}), (self.decision(sufficient=False, answer=()), {}),
            ({"items": [self.item("P7")]}, {}), (self.decision(supported=("P7",), answer=("P1", "P7")), {})]
        updates = []
        result = services.answer("مقایسه دو درمان", "luna", ["uptodate"], [], None,
            publish=lambda event: updates.append((chat.call_count, event)))
        part = result["parts"][0]
        self.assertEqual(part["retrieval"]["reviewed_passages"], 12)
        self.assertEqual({item["source_id"] for item in part["items"]}, {"P1", "P7"})
        self.assertEqual(len(chat.call_args_list[5].args[2]["previously_verified"]), 1)
        self.assertEqual([count for count, _ in updates], [4, 6])
        self.assertEqual([item["source_id"] for item in updates[0][1]["citations"]], ["P1"])
        self.assertEqual(updates[0][1]["part_index"], 0)
        self.assertEqual(updates[0][1]["article_id"], "10")
        read.assert_called_once()

    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "Unrelated"}, {"id": "20", "title": "Relevant"}])
    @patch.object(services, "chat")
    def test_article_with_no_relevant_sections_is_skipped_in_normal_search_order(self, chat, search, read):
        read.side_effect = [[self.section("10")], [self.section("20")]]
        chat.side_effect = [({"queries": ["topic"]}, {}), ({"section_ids": []}, {}),
            ({"section_ids": ["T1"]}, {}), ({"items": [self.item()]}, {}), (self.decision(), {})]
        result = services.answer("درمان بیماری", "luna", ["uptodate"], [], None)
        self.assertEqual(result["parts"][0]["retrieval"]["answer_article_id"], "20")
        self.assertEqual(len(chat.call_args_list), 5)

    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    @patch.object(services, "chat")
    def test_only_partial_evidence_is_not_reported_as_sufficient(self, chat, search, read):
        read.return_value = [self.section()]
        chat.side_effect = [({"queries": ["topic"]}, {}), ({"section_ids": ["T1"]}, {}),
            ({"items": [self.item()]}, {}), (self.decision(sufficient=False, answer=()), {})]
        part = services.answer("مقایسه دو درمان", "luna", ["uptodate"], [], None)["parts"][0]
        self.assertEqual(part["status"], "partial")
        self.assertFalse(part["retrieval"]["early_stopped"])
        self.assertEqual(part["retrieval"]["stop_reason"], "no_sufficient_answer")

    @patch.object(services, "read_sections", return_value=[])
    @patch.object(services, "search_articles")
    @patch.object(services, "chat", return_value=({"queries": ["topic"]}, {}))
    def test_article_scan_is_bounded(self, chat, search, read):
        search.return_value = [{"id": str(n), "title": f"Article {n}"} for n in range(20)]
        part = services.answer("درمان بیماری", "luna", ["uptodate"], [], None)["parts"][0]
        self.assertEqual(read.call_count, 8)
        self.assertEqual(part["retrieval"]["stop_reason"], "article_limit")

    @patch.object(services, "read_sections", return_value=[])
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "Reference"}])
    @patch.object(services, "chat", return_value=({"queries": ["topic"]}, {}))
    def test_independent_questions_each_have_their_own_search(self, chat, search, read):
        result = services.answer("سؤال اول؟ سؤال دوم؟", "luna", ["uptodate"], [], None)
        self.assertEqual(len(result["parts"]), 2)
        self.assertEqual(search.call_count, 2)

    @patch.object(services, "search_articles")
    @patch.object(services, "chat")
    def test_zero_result_queries_are_shortened_using_same_model_and_search_service(self, chat, search):
        search.side_effect = [[], []]
        chat.side_effect = [({"queries": ["pharmacotherapy for nocturnal enuresis"]}, {}), ({"queries": ["enuresis"]}, {})]
        result = services.answer("دارودرمانی شب ادراری", "luna", ["uptodate"], [], None)
        self.assertEqual(search.call_args_list[0].args[0], ["pharmacotherapy for nocturnal enuresis"])
        self.assertEqual(search.call_args_list[1].args[0], ["enuresis"])
        self.assertEqual(result["parts"][0]["queries"], ["pharmacotherapy for nocturnal enuresis", "enuresis"])

    @patch.object(services, "chat")
    def test_unverified_or_invented_evidence_cannot_trigger_early_stop(self, chat):
        chat.side_effect = [({"items": [self.item()]}, {}),
                            ({"supported": [], "sufficient": True, "answer_source_ids": ["P1"]}, {})]
        with self.assertRaisesMessage(provider.ProviderError, "UNKNOWN_SOURCE_ID"):
            services._explain_batch("luna", "درمان", [passage()], [], lambda _: None)

    @patch.object(services, "chat")
    def test_unsupported_explanation_is_not_rendered(self, chat):
        chat.side_effect = [({"items": [self.item()]}, {}), (self.decision(supported=(), sufficient=False, answer=()), {})]
        self.assertEqual(services._explain_batch("luna", "درمان", [passage()], [], lambda _: None), ([], []))

    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles", return_value=[{"id": "10", "title": "First"}])
    @patch.object(services, "chat")
    def test_rejected_explanations_are_never_published(self, chat, search, read):
        read.return_value = [self.section()]
        chat.side_effect = [({"queries": ["topic"]}, {}), ({"section_ids": ["T1"]}, {}),
            ({"items": [self.item()]}, {}), (self.decision(supported=(), sufficient=False, answer=()), {})]
        publish = MagicMock()
        part = services.answer("درمان بیماری", "luna", ["uptodate"], [], None, publish=publish)["parts"][0]
        self.assertEqual(part["status"], "not_found")
        publish.assert_not_called()

    @patch.object(services, "read_sections")
    @patch.object(services, "search_articles")
    @patch.object(services, "chat")
    def test_drug_directory_is_followed_before_patient_or_general_topics_without_extra_model_call(self, chat, search, read):
        search.return_value = [{"id": "112290", "title": "Aripiprazole formulations: Drug information"},
                               {"id": "14688", "title": "Unipolar depression in adults: Treatment"}]
        def source(ids, request, audit):
            if ids == ["112290"]:
                audit["related_topics"] = [{"id": "8786", "title": "Aripiprazole (Abilify)"}]
                return []
            self.assertEqual(ids, ["8786"])
            return [self.section("8786")]
        read.side_effect = source
        chat.side_effect = [({"queries": ["aripiprazole"], "lookup_kind": "drug", "audience": "general"}, {}),
            ({"section_ids": ["T1"]}, {}), ({"items": [self.item()]}, {}), (self.decision(), {})]
        observed = []
        part = services.answer("عارضه مهم داروی آریپیپرازول", "luna", ["uptodate"], [], None, observe=observed.append)["parts"][0]
        self.assertEqual(part["status"], "answered")
        self.assertEqual(part["items"][0]["target"]["params"]["id"], "8786")
        self.assertEqual([call.args[0] for call in read.call_args_list], [["112290"], ["8786"]])
        self.assertEqual(chat.call_count, 4)
        self.assertEqual(part["retrieval"]["related_topic_paths"], [{"from": "112290", "to": ["8786"]}])
        self.assertTrue(any(event["type"] == "related_topics" for event in observed))


class WorkflowTests(SimpleTestCase):
    def test_related_drug_topic_is_inserted_after_its_directory(self):
        base = {"part_index": 0, "question_fa": "پرسش"}
        state = workflow.apply_event([], {**base, "type": "titles", "query": "drug", "articles": [
            {"id": "112290", "title": "Drug directory"}, {"id": "14688", "title": "Related adult topic"}]})
        event = {**base, "type": "related_topics", "article_id": "112290", "articles": [{"id": "8786", "title": "Drug monograph"}]}
        state = workflow.apply_event(state, event)
        state = workflow.apply_event(state, event)
        self.assertEqual([item["id"] for item in state[0]["titles"]], ["112290", "8786", "14688"])
        self.assertEqual(state[0]["titles"][1]["related_to"], "112290")

    def test_metadata_is_ordered_deduplicated_bounded_and_contains_no_paragraph_or_reasoning(self):
        base = {"part_index": 0, "question_fa": "پرسش"}
        state = workflow.apply_event([], {**base, "type": "titles", "query": "concept", "articles": [
            {"id": "10", "title": "First", "text": "private text"}, {"id": "20", "title": "Second"}]})
        state = workflow.apply_event(state, {**base, "type": "titles", "query": "concept", "articles": [
            {"id": "10", "title": "Duplicate"}]})
        self.assertEqual(state[0]["titles"], [{"id": "10", "title": "First"}, {"id": "20", "title": "Second"}])
        state = workflow.apply_event(state, {**base, "type": "article", "article_id": "10", "title": "First"})
        state = workflow.apply_event(state, {**base, "type": "sections", "article_id": "10", "paragraph_count": 13,
            "sections": [{"id": "T2", "heading": "Drug therapy", "text": "private text"}, {"id": "T1", "heading": "Recommendations"}],
            "reasoning_content": "private reasoning"})
        self.assertEqual([row["id"] for row in state[0]["articles"][0]["sections"]], ["T2", "T1"])
        self.assertNotIn("private", json.dumps(state))
        state = workflow.apply_event(state, {**base, "type": "titles", "query": "alias",
            "articles": [{"id": str(i), "title": "Reference"} for i in range(200)]})
        self.assertEqual(len(state[0]["titles"]), 120)


class WarmupTests(SimpleTestCase):
    @override_settings(AI_LAB_ENABLED=True, AI_LAB_PREWARM_ENABLED=False)
    @patch.object(warmup.utd, "search_page")
    def test_disabled_warmup_does_no_reference_io(self, search):
        self.assertFalse(warmup.warm_search())
        search.assert_not_called()

    @override_settings(AI_LAB_ENABLED=True, AI_LAB_PREWARM_ENABLED=True)
    @patch.object(warmup.utd, "is_available", return_value=True)
    @patch.object(warmup.utd, "search_page")
    @patch.object(provider, "build_opener", side_effect=AssertionError("Warmup must never call a paid model"))
    def test_warmup_uses_only_canonical_search_and_sanitizes_failures(self, opener, search, available):
        self.assertTrue(warmup.warm_search())
        search.assert_called_once_with("nocturnal enuresis", limit=30, offset=0, section="")
        search.side_effect = RuntimeError("private connection details")
        with self.assertLogs(warmup.logger, level="WARNING") as logs:
            self.assertFalse(warmup.warm_search())
        self.assertNotIn("private connection details", " ".join(logs.output))
        opener.assert_not_called()


class CanonicalSearchTests(SimpleTestCase):
    def test_drug_priority_is_stable_and_pediatric_questions_keep_pediatric_information_first(self):
        articles = [{"id": "general", "title": "Depression in adults"},
            {"id": "patient", "title": "Aripiprazole: Patient drug information"},
            {"id": "pediatric", "title": "Aripiprazole: Pediatric drug information"},
            {"id": "drug", "title": "Aripiprazole: Drug information"}]
        self.assertEqual([row["id"] for row in retrieval.prioritize_topics(articles, "drug")], ["drug", "patient", "general", "pediatric"])
        self.assertEqual(retrieval.prioritize_topics(articles, "drug", "pediatric")[0]["id"], "pediatric")
        self.assertIs(retrieval.prioritize_topics(articles, "topic"), articles)

    @patch.object(retrieval, "require_feature")
    @patch.object(retrieval.utd, "get_topic")
    def test_formulation_directory_uses_only_source_drug_links_and_never_executes_onclick(self, topic, access):
        topic.return_value = {"title": "Aripiprazole formulations: Drug information", "body_html": '''
          <div id="formulinkBodyPlaceholder"></div><ul>
          <li><a class="drug drug_general" data-topicid="8786" onclick="untrusted()">Aripiprazole (Abilify)</a></li>
          <li><a class="drug" data-topicid="8786">Duplicate</a></li>
          <li><a class="drug" data-topicid="112290">Self</a></li>
          <li><a class="drug" data-topicid="https://invalid.test">External</a></li>
          <li><a href="https://invalid.test">Other link</a></li></ul>'''}
        audit = {}
        self.assertEqual(retrieval.read_sections(["112290"], None, audit), [])
        self.assertEqual(audit["related_topics"], [{"id": "8786", "title": "Aripiprazole (Abilify)"}])
        access.assert_called_once_with(None, "uptodate", item="112290", consume=True)
        topic.assert_called_once_with("112290")

    @patch.object(retrieval, "require_feature")
    @patch.object(retrieval.utd, "get_topic")
    def test_full_drug_monograph_with_same_placeholder_is_read_instead_of_following_all_its_links(self, topic, access):
        topic.return_value = {"title": "Aripiprazole: Drug information", "body_html": '''
            <div id="formulinkBodyPlaceholder"></div>
            <ul><li><a class="drug" data-topicid="10978">Other drug information</a></li></ul>
            <div id="F100"><h2>Adverse Reactions</h2><p>''' + QUOTE + '''</p></div>'''}
        audit = {}
        sections = retrieval.read_sections(["8786"], None, audit)
        self.assertTrue(sections)
        self.assertNotIn("related_topics", audit)
        self.assertTrue(any(p.text == QUOTE for section in sections for p in section["passages"]))

    @patch.object(retrieval, "require_feature")
    @patch.object(retrieval.utd, "is_available", return_value=True)
    @patch.object(retrieval.utd, "search_page")
    def test_normal_search_query_rank_and_tag_only_results_are_preserved(self, search, available, access):
        search.return_value = {"total": 2, "terms": ["alias"], "corrected": "", "results": [
            {"id": "tag-only", "title": "Title without query words", "sections": ["Pediatrics"]},
            {"id": "direct", "title": "Alias treatment", "sections": ["Medicine"]}]}
        audit = {}
        result = retrieval.search_articles(["alias treatment"], None, audit)
        search.assert_called_once_with("alias treatment", limit=30, offset=0, section="")
        self.assertEqual([row["id"] for row in result], ["tag-only", "direct"])
        self.assertEqual(audit["search_engine"], "uptodate.search_page")

    @patch.object(retrieval, "require_feature", side_effect=PlatformAPIError("Denied", status_code=402))
    @patch.object(retrieval.utd, "search_page")
    def test_denied_source_is_not_read(self, search, access):
        with self.assertRaises(PlatformAPIError):
            retrieval.search_articles(["enuresis"], None, {})
        search.assert_not_called()

    def test_paragraph_budget_covers_every_selected_section_before_extra_paragraphs(self):
        sections = [{"id": "T1", "passages": [passage(n) for n in range(1, 60)]},
                    {"id": "T2", "passages": [passage(99)]}]
        audit = {}
        result = retrieval.selected_passages(sections, ["T1", "T2"], audit)
        self.assertEqual(result[1].id, "P99")
        self.assertEqual(len(result), 48)
        self.assertTrue(audit["limited"])


class TaggedSourceIntegrationTests(TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(utd.close_all)
        _make_snapshot(tmp.name)
        _add_concept_snapshot(tmp.name)
        with sqlite3.connect(Path(tmp.name) / "search.db") as db:
            db.execute("INSERT INTO query VALUES (?,?,?)", (99, "reference alias", 100))
            db.execute("INSERT INTO query_topic VALUES (?,?,?,?,?)", (99, "140619", "140619", "", ""))
        self.settings = override_settings(UPTODATE_DB_DIR=tmp.name, UPTODATE_MYSQL_URL="")
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        utd.close_all()
        self.user = get_user_model().objects.create_superuser("tagged-lab-admin")

    def test_tag_only_result_matches_normal_app_and_direct_paragraph_endpoint(self):
        normal = utd.search_page("reference alias", limit=30)
        audit = {}
        result = retrieval.search_articles(["reference alias"], SimpleNamespace(user=self.user), audit)
        self.assertEqual([row["id"] for row in result], [row["id"] for row in normal["results"]])
        self.assertEqual(result[0]["id"], "140619")
        self.assertNotIn("alias", result[0]["title"].lower())
        sections = retrieval.read_sections([result[0]["id"]], SimpleNamespace(user=self.user), audit)
        p = sections[0]["passages"][0]
        params = p.target["params"]
        client = APIClient()
        client.force_authenticate(self.user)
        response = client.get(f"/api/v1/uptodate/topics/{params['id']}/", {
            "search_content_hash": params["searchContentHash"], "search_anchor": params["searchAnchor"]})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["search_anchor_status"], "matched")
        self.assertIn(params["searchAnchor"], response.data["body_html"])


@override_settings(AI_LAB_ENABLED=True, AI_LAB_USER_IDS=set(), AI_LAB_MODEL="gpt-6-luna")
class ApiTests(TestCase):
    def setUp(self):
        caches["throttle"].clear()
        self.client = APIClient()
        self.admin = get_user_model().objects.create_user("lab-admin", is_staff=True, is_superuser=True)
        self.learner = get_user_model().objects.create_user("lab-user")
        self.client.force_authenticate(self.admin)
        self.payload = {"question": "پرسش از منابع", "model": "luna", "sources": ["uptodate"]}

    def test_flag_authentication_and_allowlist(self):
        self.client.force_authenticate(None)
        self.assertIn(self.client.get("/api/v1/ai-lab/status/").status_code, [401, 403])
        self.client.force_authenticate(self.admin)
        with override_settings(AI_LAB_ENABLED=False):
            self.assertFalse(self.client.get("/api/v1/ai-lab/status/").data["enabled"])
            self.assertEqual(self.client.post("/api/v1/ai-lab/ask/", self.payload).status_code, 403)
        self.client.force_authenticate(self.learner)
        self.assertFalse(self.client.get("/api/v1/ai-lab/status/").data["enabled"])
        with override_settings(AI_LAB_USER_IDS={str(self.learner.pk)}):
            self.assertTrue(self.client.get("/api/v1/ai-lab/status/").data["enabled"])

    @patch.object(views._executor, "submit")
    def test_luna_is_advertised_and_admitted_as_a_real_job_model(self, submit):
        self.assertEqual(self.client.get("/api/v1/ai-lab/status/").data["models"], {"luna": "gpt-6-luna"})
        response = self.client.post("/api/v1/ai-lab/ask/", {**self.payload, "model": "luna"}, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(submit.call_args.args[3]["model"], "luna")
        active = self.client.get("/api/v1/ai-lab/active/").data["active_job"]
        self.assertEqual(active["model"], "luna")

    @override_settings(AI_LAB_MODEL="configured-model")
    @patch.object(views._executor, "submit")
    def test_configured_upstream_model_does_not_require_a_new_frontend_alias(self, submit):
        self.assertEqual(self.client.get("/api/v1/ai-lab/status/").data["models"], {"luna": "configured-model"})
        response = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(submit.call_args.args[3]["model"], "luna")
        self.assertEqual(self.client.get("/api/v1/ai-lab/active/").data["active_job"]["model"], "luna")

    @patch.object(views._executor, "submit")
    def test_job_is_private_no_store_and_single_active_request(self, submit):
        response = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertIn("no-store", response["Cache-Control"])
        submit.assert_called_once()
        job_id = response.data["job_id"]
        self.assertEqual(self.client.get(f"/api/v1/ai-lab/results/{job_id}/").data["status"], "running")
        self.assertEqual(self.client.post("/api/v1/ai-lab/ask/", self.payload).status_code, 429)
        self.client.force_authenticate(self.learner)
        with override_settings(AI_LAB_USER_IDS={str(self.learner.pk)}):
            self.assertEqual(self.client.get(f"/api/v1/ai-lab/results/{job_id}/").status_code, 404)

    @patch.object(views._executor, "submit")
    def test_api_key_text_and_arbitrary_sources_or_models_are_rejected(self, submit):
        for values in [{"question": "sk-" + "x" * 25}, {"history": ["sk-" + "x" * 25]},
                       {"model": "other-model"}, {"model": "jev"}, {"model": "glm"}, {"model": "gemma"}, {"model": "deepseek"},
                       {"sources": ["internet"]}, {"sources": ["medscape"]}]:
            self.assertEqual(self.client.post("/api/v1/ai-lab/ask/", {**self.payload, **values}, format="json").status_code, 400)
        submit.assert_not_called()

    @patch.object(views, "answer")
    @patch.object(views, "close_old_connections")
    def test_background_failure_releases_locks_and_has_sanitized_public_error(self, close_connections, answer):
        answer.side_effect = provider.ProviderError("PROVIDER_HTTP_ERROR", 500)
        job = str(uuid4())
        cache = caches["throttle"]
        cache.set("ai-lab:slot:0", job)
        cache.set(f"ai-lab:user:{self.admin.pk}", job)
        cache.set(f"ai-lab:job:{job}", {"user_id": self.admin.pk, "status": "running", "stage": "starting",
            "created_at": time.time(), "heartbeat_at": time.time(), **self.payload})
        views._run(job, self.admin, {**self.payload, "history": []}, "ai-lab:slot:0")
        result = cache.get(f"ai-lab:job:{job}")
        self.assertEqual(result["error"], {"code": "PROVIDER_HTTP_ERROR", "provider_status": 500, "model": "gpt-6-luna"})
        self.assertIsNone(cache.get("ai-lab:slot:0"))
        self.assertIsNone(cache.get(f"ai-lab:user:{self.admin.pk}"))

    @patch.object(views._executor, "submit")
    def test_reload_can_recover_own_running_question_without_another_submission(self, submit):
        response = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
        active = self.client.get("/api/v1/ai-lab/active/")
        self.assertIn("no-store", active["Cache-Control"])
        self.assertEqual(active.data["active_job"]["job_id"], response.data["job_id"])
        self.assertEqual(active.data["active_job"]["question"], self.payload["question"])
        self.assertNotIn("heartbeat_at", active.data["active_job"])
        repeated = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
        self.assertEqual(repeated.data["details"]["job_id"], response.data["job_id"])
        submit.assert_called_once()
        self.client.force_authenticate(self.learner)
        with override_settings(AI_LAB_USER_IDS={str(self.learner.pk)}):
            self.assertIsNone(self.client.get("/api/v1/ai-lab/active/").data["active_job"])

    @patch.object(views._executor, "submit")
    @patch.object(views, "close_old_connections")
    def test_verified_findings_are_visible_while_running_recoverable_and_not_duplicated(self, close_connections, submit):
        job_id = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json").data["job_id"]
        citation = {"source_id": "P1", "quote": QUOTE, "summary_fa": "توضیح فارسی مطابق متن منبع",
                    "target": {"screen": "uptodateArticle", "params": {"id": "10"}}}
        event = {"part_index": 0, "question_fa": "سؤال", "article_id": "10", "citations": [citation]}
        final = {"parts": [], "model": "luna"}

        def produce(question, model, sources, history, request, progress, publish, observe):
            base = {"part_index": 0, "question_fa": "سؤال"}
            progress("retrieving")
            observe({**base, "type": "titles", "query": "concept", "articles": [{"id": "10", "title": "First article"}]})
            titles_only = self.client.get(f"/api/v1/ai-lab/results/{job_id}/").data
            self.assertEqual(titles_only["workflow"][0]["titles"], [{"id": "10", "title": "First article"}])
            self.assertEqual(titles_only["findings"], [])
            self.assertNotIn("result", titles_only)
            observe({**base, "type": "article", "article_id": "10", "title": "First article"})
            progress("selecting_sections")
            observe({**base, "type": "sections", "article_id": "10", "paragraph_count": 13,
                     "sections": [{"id": "T1", "heading": "Treatment"}]})
            progress("verifying")
            publish(event)
            running = self.client.get(f"/api/v1/ai-lab/results/{job_id}/").data
            self.assertEqual(running["status"], "running")
            self.assertNotIn("result", running)
            self.assertEqual(running["findings"][0]["citation"]["quote"], QUOTE)
            self.assertGreaterEqual(running["first_result_ms"], 0)
            self.assertNotIn("user_id", running)
            revision = running["revision"]
            unchanged = self.client.get(f"/api/v1/ai-lab/results/{job_id}/?after_revision={revision}").data
            self.assertNotIn("findings", unchanged)
            self.assertNotIn("workflow", unchanged)
            restored = self.client.get("/api/v1/ai-lab/active/").data["active_job"]
            self.assertEqual(restored["findings"], running["findings"])
            self.assertEqual(restored["workflow"], running["workflow"])
            self.assertIn("selecting_sections", running["stages_seen"])
            publish(event)  # A reconnect/repeated callback cannot append the same result twice.
            progress("answering")
            publish({**event, "article_id": "20"})  # P1 in a different article is a distinct finding.
            resumed = self.client.get(f"/api/v1/ai-lab/results/{job_id}/?after_revision={revision}").data
            self.assertEqual([item["id"] for item in resumed["findings"]], ["0:10:P1", "0:20:P1"])
            self.assertEqual([item["sequence"] for item in resumed["findings"]], [1, 2])
            return final

        with patch.object(views, "answer", side_effect=produce):
            views._run(job_id, self.admin, {**self.payload, "history": []}, "ai-lab:slot:0")
        completed = self.client.get(f"/api/v1/ai-lab/results/{job_id}/").data
        self.assertEqual(completed["status"], "complete")
        self.assertEqual(completed["result"], final)
        self.assertEqual(len(completed["findings"]), 2)
        final_again = self.client.get(f"/api/v1/ai-lab/results/{job_id}/?after_revision={completed['revision']}").data
        self.assertIn("result", final_again)
        self.client.force_authenticate(self.learner)
        with override_settings(AI_LAB_USER_IDS={str(self.learner.pk)}):
            denied = self.client.get(f"/api/v1/ai-lab/results/{job_id}/")
        self.assertEqual(denied.status_code, 404)
        self.assertNotIn("findings", denied.data)
        self.assertNotIn("workflow", denied.data)

    @patch.object(views._executor, "submit")
    def test_removed_model_jobs_are_expired_and_cannot_block_a_luna_request(self, submit):
        for model in ("gemma", "deepseek"):
            cache = caches["throttle"]
            cache.clear()
            job_id = str(uuid4())
            cache.set(f"ai-lab:job:{job_id}", {"user_id": self.admin.pk, **self.payload, "model": model,
                "status": "running", "stage": "starting", "created_at": time.time(), "heartbeat_at": time.time()})
            cache.set(f"ai-lab:user:{self.admin.pk}", job_id)
            cache.set("ai-lab:slot:0", job_id)
            self.assertIsNone(self.client.get("/api/v1/ai-lab/active/").data["active_job"])
            self.assertEqual(cache.get(f"ai-lab:job:{job_id}")["error"]["code"], "EXPERIMENT_EXPIRED")
            with patch.object(views, "answer") as answer, patch.object(views, "close_old_connections"):
                views._run(job_id, self.admin, {**self.payload, "model": model, "history": []}, "ai-lab:slot:0")
                answer.assert_not_called()
            self.assertEqual(self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json").status_code, 202)

    @patch.object(views._executor, "submit")
    @patch.object(views, "close_old_connections")
    def test_failure_or_expiration_preserves_findings_and_never_resurrects_job(self, close_connections, submit):
        for expired in (False, True):
            caches["throttle"].clear()
            job_id = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json").data["job_id"]
            event = {"part_index": 0, "question_fa": "سؤال", "article_id": "10", "citations": [{"source_id": "P1"}]}
            def produce(question, model, sources, history, request, progress, publish, observe):
                publish(event)
                if expired:
                    key = f"ai-lab:job:{job_id}"
                    record = caches["throttle"].get(key)
                    record["heartbeat_at"] = time.time() - 46
                    caches["throttle"].set(key, record)
                    publish(event)
                    self.fail("Expired publisher continued")
                raise provider.ProviderError("PROVIDER_UNAVAILABLE")
            with patch.object(views, "answer", side_effect=produce):
                views._run(job_id, self.admin, {**self.payload, "history": []}, "ai-lab:slot:0")
            record = self.client.get(f"/api/v1/ai-lab/results/{job_id}/").data
            self.assertEqual(record["status"], "failed")
            self.assertEqual(len(record["findings"]), 1)
            self.assertEqual(record["error"]["code"], "EXPERIMENT_EXPIRED" if expired else "PROVIDER_UNAVAILABLE")

    @patch.object(views._executor, "submit")
    @patch.object(views, "close_old_connections")
    def test_progressive_findings_are_bounded_without_losing_final_result(self, close_connections, submit):
        job_id = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json").data["job_id"]
        def produce(question, model, sources, history, request, progress, publish, observe):
            publish({"part_index": 0, "question_fa": "سؤال", "article_id": "10",
                     "citations": [{"source_id": f"P{n}"} for n in range(jobs.MAX_FINDINGS + 3)]})
            return {"kept": "final answer"}
        with patch.object(views, "answer", side_effect=produce):
            views._run(job_id, self.admin, {**self.payload, "history": []}, "ai-lab:slot:0")
        record = self.client.get(f"/api/v1/ai-lab/results/{job_id}/").data
        self.assertEqual(record["status"], "complete")
        self.assertTrue(record["findings_limited"])
        self.assertEqual(len(record["findings"]), jobs.MAX_FINDINGS)
        self.assertEqual(record["result"], {"kept": "final answer"})

    @patch.object(views._executor, "submit")
    def test_dead_worker_lock_is_released_and_old_job_cannot_reappear(self, submit):
        response = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
        old_id = response.data["job_id"]
        cache = caches["throttle"]
        key = f"ai-lab:job:{old_id}"
        record = cache.get(key)
        record["heartbeat_at"] = time.time() - 46
        cache.set(key, record)
        response = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertNotEqual(response.data["job_id"], old_id)
        self.assertEqual(cache.get(key)["error"]["code"], "EXPERIMENT_EXPIRED")
        self.assertEqual(submit.call_count, 2)
        with patch.object(views, "close_old_connections"), patch.object(views, "answer") as answer:
            views._run(old_id, self.admin, {**self.payload, "history": []}, "ai-lab:slot:0")
            answer.assert_not_called()
        self.assertEqual(cache.get(f"ai-lab:user:{self.admin.pk}"), response.data["job_id"])

    @patch.object(views._executor, "submit")
    def test_missing_or_completed_job_cannot_leave_a_busy_lock(self, submit):
        cache = caches["throttle"]
        for record in [None, {"user_id": self.admin.pk, "status": "complete", "result": {}}]:
            cache.clear()
            job_id = str(uuid4())
            cache.set(f"ai-lab:user:{self.admin.pk}", job_id)
            cache.set("ai-lab:slot:0", job_id)
            if record:
                cache.set(f"ai-lab:job:{job_id}", record)
            response = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
            self.assertEqual(response.status_code, 202)

    @patch.object(views._executor, "submit")
    def test_live_heartbeat_does_not_extend_total_job_deadline(self, submit):
        response = self.client.post("/api/v1/ai-lab/ask/", self.payload, format="json")
        key = f"ai-lab:job:{response.data['job_id']}"
        cache = caches["throttle"]
        record = cache.get(key)
        record["created_at"] = time.time() - 601
        cache.set(key, record)
        result = self.client.get(f"/api/v1/ai-lab/results/{response.data['job_id']}/")
        self.assertEqual(result.data["status"], "failed")
        self.assertEqual(result.data["error"]["code"], "EXPERIMENT_EXPIRED")
