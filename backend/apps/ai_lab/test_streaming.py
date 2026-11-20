import json
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase, override_settings
from . import provider, streaming, telemetry


@override_settings(AI_LAB_API_KEY="test-private-key",AI_LAB_MODEL="gpt-6-luna",AI_LAB_REASONING_EFFORT="low",
                   AI_LAB_BASE_URL="https://provider.example/v1", AI_LAB_RESPONSE_MODEL_ALIASES=())
class StreamingProviderTests(SimpleTestCase):
    def mock_client(self, deltas, *, finish="stop", done=True, model="gpt-6-luna", status=200, prefix=(), suffix=()):
        lines=[]
        for value in prefix:
            lines += ["data: " + json.dumps(value), ""]
        for delta in deltas:
            lines += ["data: "+json.dumps({"model":model,"choices":[{"index":0,"delta":delta,"finish_reason":None}]}), ""]
        lines += ["data: "+json.dumps({"model":model,"choices":[{"index":0,"delta":{},"finish_reason":finish}]}), ""]
        lines += ["data: "+json.dumps({"choices":[],"usage":{"prompt_tokens":10,"completion_tokens":20,"total_tokens":30}}), ""]
        for value in suffix:
            lines += ["data: " + json.dumps(value), ""]
        if done:lines += ["data: [DONE]", ""]
        client=MagicMock()
        response=client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value
        response.status_code=status
        response.iter_lines.return_value=iter(lines)
        return client

    def test_empty_initial_model_metadata_does_not_abort_a_valid_tool_stream(self):
        tool = {"index": 0, "id": "call_1", "type": "function",
                "function": {"name": "search_references", "arguments": '{"query":"enuresis"}'}}
        for model in [None, "", "   "]:
            with self.subTest(model=model):
                client = self.mock_client([{"tool_calls": [tool]}], finish="tool_calls",
                    prefix=[{"model": model, "choices": [], "usage": None}])
                output, trace = [], telemetry.Trace()
                with patch.object(streaming.httpx, "Client", client), trace.activate():
                    message, meta = streaming.stream_chat([], on_delta=output.append)
                self.assertEqual(json.loads(message["tool_calls"][0]["function"]["arguments"]), {"query": "enuresis"})
                self.assertEqual(meta["reported_model"], "gpt-6-luna")
                self.assertEqual(output, [])
                self.assertEqual(trace.request_count, 1)

    def test_empty_trailing_model_metadata_preserves_identity_text_and_usage(self):
        client = self.mock_client([{"content": "پاسخ مستند"}], suffix=[{
            "model": None, "choices": [], "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}}])
        output = []
        with patch.object(streaming.httpx, "Client", client):
            message, meta = streaming.stream_chat([], on_delta=output.append)
        self.assertEqual("".join(output), message["content"])
        self.assertEqual(meta["reported_model"], "gpt-6-luna")
        self.assertEqual(meta["usage"]["total_tokens"], 30)

    def test_nonempty_or_malformed_model_metadata_is_still_validated_before_any_output(self):
        for model, code in [("other-model", "MODEL_MISMATCH"), (0, "INVALID_PROVIDER_RESPONSE"),
                            (False, "INVALID_PROVIDER_RESPONSE"), ({}, "INVALID_PROVIDER_RESPONSE")]:
            with self.subTest(model=model):
                client = self.mock_client([{"content": "private answer" * 30}], prefix=[{"model": model, "choices": []}])
                output = []
                with patch.object(streaming.httpx, "Client", client), self.assertRaisesMessage(provider.ProviderError, code):
                    streaming.stream_chat([], on_delta=output.append)
                self.assertEqual(output, [])

    def test_empty_model_on_actual_generation_choices_is_not_treated_as_metadata(self):
        for model in [None, "", " "]:
            with self.subTest(model=model):
                client = self.mock_client([{"content": "private answer" * 30}], model=model)
                output = []
                with patch.object(streaming.httpx, "Client", client), self.assertRaisesMessage(provider.ProviderError, "INVALID_PROVIDER_RESPONSE"):
                    streaming.stream_chat([], on_delta=output.append)
                self.assertEqual(output, [])

    def test_metadata_does_not_make_a_truncated_stream_complete_or_allow_a_key_echo(self):
        for prefix, done, code in [
            ([{"model": None, "choices": [], "usage": None}], False, "PROVIDER_STREAM_INCOMPLETE"),
            ([{"model": None, "choices": [], "private_echo": "test-private-key"}], True, "UNSAFE_PROVIDER_RESPONSE"),
        ]:
            with self.subTest(code=code):
                client = self.mock_client([{"content": "پاسخ"}], prefix=prefix, done=done)
                with patch.object(streaming.httpx, "Client", client), self.assertRaisesMessage(provider.ProviderError, code):
                    streaming.stream_chat([])
                client.return_value.__enter__.return_value.stream.assert_called_once()

    def test_metadata_and_done_without_a_generation_finish_are_not_an_answer(self):
        client = self.mock_client([])
        response = client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value
        response.iter_lines.return_value = iter([
            'data: {"model": null, "choices": [], "usage": null}', "", "data: [DONE]", "",
        ])
        output = []
        with patch.object(streaming.httpx, "Client", client), self.assertRaisesMessage(provider.ProviderError, "PROVIDER_STREAM_INCOMPLETE"):
            streaming.stream_chat([], on_delta=output.append)
        self.assertEqual(output, [])

    def test_streams_only_content_and_records_one_paid_attempt(self):
        client=self.mock_client([{"reasoning_content":"never expose reasoning"},{"content":"پاسخ مستند فارسی. "*20},{"content":"پایان پاسخ"}])
        output=[];trace=telemetry.Trace()
        with patch.object(streaming.httpx,"Client",client),trace.activate():
            message,meta=streaming.stream_chat([{"role":"user","content":"question"}],on_delta=output.append)
        self.assertEqual("".join(output),message["content"])
        self.assertGreater(len(output),1)
        self.assertNotIn("never expose reasoning","".join(output))
        self.assertEqual(trace.request_count,1)
        self.assertEqual(meta["usage"]["total_tokens"],30)

    def test_reassembles_tool_arguments_without_emitting_them_as_answer(self):
        client=self.mock_client([
            {"tool_calls":[{"index":0,"id":"call_1","type":"function","function":{"name":"search_references","arguments":'{"query":"nocturnal '}}]},
            {"tool_calls":[{"index":0,"function":{"arguments":'enuresis"}'}}]}],finish="tool_calls")
        output=[]
        with patch.object(streaming.httpx,"Client",client):
            message,_=streaming.stream_chat([],on_delta=output.append)
        self.assertEqual(json.loads(message["tool_calls"][0]["function"]["arguments"]),{"query":"nocturnal enuresis"})
        self.assertEqual(output,[])

    def test_split_credential_echo_is_blocked_before_a_callback(self):
        for parts in [["test-pri","vate-key"],["sk-"+"a"*7,"a"*15]]:
            output=[]
            with patch.object(streaming.httpx,"Client",self.mock_client([{"content":p} for p in parts])):
                with self.assertRaisesMessage(provider.ProviderError,"UNSAFE_PROVIDER_RESPONSE"):
                    streaming.stream_chat([],on_delta=output.append)
            self.assertEqual(output,[])

    def test_wrong_model_incomplete_stream_and_truncation_are_never_replayed(self):
        for options,code in [({"model":"other"},"MODEL_MISMATCH"),({"done":False},"PROVIDER_STREAM_INCOMPLETE"),({"finish":"length"},"MODEL_OUTPUT_TRUNCATED")]:
            client=self.mock_client([{"content":"پاسخ"}],**options)
            with patch.object(streaming.httpx,"Client",client):
                with self.assertRaisesMessage(provider.ProviderError,code):streaming.stream_chat([])
            client.return_value.__enter__.return_value.stream.assert_called_once()

    @override_settings(AI_LAB_MODEL="GPT-6-Luna", AI_LAB_RESPONSE_MODEL_ALIASES=("openai/gpt-6-luna",))
    def test_gateway_alias_supports_streamed_tools_without_changing_the_request_model(self):
        tool = {"index": 0, "id": "call_1", "type": "function",
                "function": {"name": "search_references", "arguments": '{"query":"enuresis"}'}}
        client = self.mock_client([{"tool_calls": [tool]}], finish="tool_calls", model="openai/gpt-6-luna")
        with patch.object(streaming.httpx, "Client", client):
            message, meta = streaming.stream_chat([])
        self.assertEqual(message["tool_calls"][0]["function"]["name"], "search_references")
        self.assertEqual(meta["reported_model"], "openai/gpt-6-luna")
        sent = client.return_value.__enter__.return_value.stream.call_args.kwargs["json"]
        self.assertEqual(sent["model"], "GPT-6-Luna")
        self.assertEqual(sent["reasoning_effort"], "low")

    def test_unconfigured_gateway_alias_is_rejected_before_emitting_text(self):
        output = []
        client = self.mock_client([{"content": "private answer" * 30}], model="openai/gpt-6-luna")
        with patch.object(streaming.httpx, "Client", client):
            with self.assertRaisesMessage(provider.ProviderError, "MODEL_MISMATCH"):
                streaming.stream_chat([], on_delta=output.append)
        self.assertEqual(output, [])

    @override_settings(AI_LAB_RESPONSE_MODEL_ALIASES=("openai/gpt-6-luna",))
    def test_explicit_alias_does_not_allow_an_unrelated_streamed_model(self):
        client = self.mock_client([{"content": "answer"}], model="openai/other-model")
        with patch.object(streaming.httpx, "Client", client):
            with self.assertRaisesMessage(provider.ProviderError, "MODEL_MISMATCH"):
                streaming.stream_chat([])

    @override_settings(AI_LAB_RESPONSE_MODEL_ALIASES=("*",))
    def test_invalid_alias_never_opens_a_stream(self):
        with patch.object(streaming.httpx, "Client") as client:
            with self.assertRaisesMessage(provider.ProviderError, "INVALID_RESPONSE_MODEL_CONFIGURATION"):
                streaming.stream_chat([])
        client.assert_not_called()

    def test_non_200_never_reads_error_body(self):
        client=self.mock_client([],status=401)
        with patch.object(streaming.httpx,"Client",client):
            with self.assertRaisesMessage(provider.ProviderError,"PROVIDER_HTTP_ERROR"):streaming.stream_chat([])
        client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value.iter_lines.assert_not_called()

    def test_streaming_honors_the_same_evaluation_request_budget(self):
        with provider.evaluation_budget(1,10),patch.object(streaming.httpx,"Client",self.mock_client([{"content":"پاسخ"}])):
            streaming.stream_chat([])
            with self.assertRaisesMessage(provider.ProviderError,"EVALUATION_BUDGET_EXCEEDED"):streaming.stream_chat([])

    def test_cancellation_closes_upstream_and_stops_without_a_replay(self):
        client=self.mock_client([{"content":"پاسخ"}])
        with patch.object(streaming.httpx,"Client",client):
            with self.assertRaisesMessage(provider.ProviderError,"SEARCH_CANCELLED"):
                streaming.stream_chat([],check_cancelled=MagicMock(side_effect=provider.ProviderError("SEARCH_CANCELLED")))
        client.return_value.__enter__.return_value.stream.assert_not_called()
