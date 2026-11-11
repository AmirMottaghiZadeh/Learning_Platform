from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from http.client import HTTPConnection, HTTPException, RemoteDisconnected
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import json
import ssl
import time
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError
from urllib.request import Request

from django.core.cache import caches
from django.test import SimpleTestCase, TestCase, override_settings

from apps.core.exceptions import PlatformAPIError
from . import http_transport, jobs, provider, reference_index, response_cache, services, telemetry, test_reference_index as fixtures
from .models import ReferenceArticle, ReferenceParagraph

TEST_CACHES = {name: {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": f"phase4-{name}"}
               for name in ["default", "throttle", "ai_lab"]}


@override_settings(CACHES=TEST_CACHES, AI_LAB_RESPONSE_CACHE_ENABLED=True, AI_LAB_RESPONSE_CACHE_TTL_SECONDS=300,
                   AI_LAB_LOCAL_SELECTION_ENABLED=True, AI_LAB_LEXICAL_ENABLED=True)
class ResponseCacheTests(TestCase):
    setUp_source = fixtures.ReferenceIndexTests.setUp
    write_article = fixtures.ReferenceIndexTests.write_article
    build = fixtures.ReferenceIndexTests.build

    def setUp(self):
        self.setUp_source()
        caches["ai_lab"].clear()
        self.addCleanup(caches["ai_lab"].clear)
        self.build()
        self.request = self.account("one")

    def account(self, pk):
        return SimpleNamespace(user=SimpleNamespace(pk=pk, is_authenticated=True, is_staff=True))

    def model(self, alias, prompt, data, limit):
        if prompt == services.PLAN_PROMPT:
            return {"queries": ["reference"], "intent": "treatment"}, {}
        if prompt == services.ANSWER_PROMPT:
            return {"items": [{"source_id": data["paragraphs"][0]["id"], "summary_fa": "توضیح فارسی مطابق متن اصلی منبع"}]}, {}
        self.assertEqual(prompt, services.VERIFY_PROMPT)
        identifier = data["items"][0]["id"]
        return {"supported": [identifier], "sufficient": True, "answer_source_ids": [identifier]}, {}

    def answer(self, **kwargs):
        with patch.object(services, "chat", side_effect=self.model) as chat, \
                patch.object(services, "search_articles", return_value=[{"id": "3851", "title": "Reference article"}]):
            result = services.answer("درمان مرجع چیست؟", "luna", ["uptodate"], [], self.request, **kwargs)
        return result, chat.call_count

    def lookup(self, **kwargs):
        return response_cache.prepare(kwargs.get("question", "درمان مرجع چیست؟"), "luna", ["uptodate"],
                                      kwargs.get("history", []), kwargs.get("request", self.request))

    def test_repeat_is_a_zero_request_hit_with_fresh_metrics_and_workflow(self):
        cold, count = self.answer()
        self.assertEqual(count, 3)
        self.assertEqual(cold["metrics"]["response_cache"], "miss")
        observed, published = [], []
        warm, count = self.answer(observe=observed.append, publish=published.append)
        self.assertEqual(count, 0)
        self.assertEqual(warm["parts"][0]["items"], cold["parts"][0]["items"])
        self.assertEqual(warm["metrics"]["response_cache"], "hit")
        self.assertEqual(warm["metrics"]["known_usage"]["total_tokens"], 0)
        self.assertEqual(warm["metrics"]["provider_requests"], 0)
        self.assertEqual(warm["stages"], [])
        self.assertEqual(warm["parts"][0]["retrieval"]["reviewed_passages"], 0)
        self.assertEqual([event["type"] for event in observed], ["question", "titles", "article", "sections", "article_done"])
        self.assertTrue(published)
        self.assertTrue(warm["metrics"]["machine_answer_complete"])

    def test_cache_key_is_private_and_isolates_accounts_history_and_question_boundaries(self):
        first = self.lookup()
        self.assertNotIn("درمان", first.key)
        self.assertNotIn("one", first.key)
        self.assertNotEqual(first.key, self.lookup(request=self.account("two")).key)
        self.assertNotEqual(first.key, self.lookup(history=["قبلی"]).key)
        self.assertNotEqual(self.lookup(question="اول\nدوم").key, self.lookup(question="اول دوم").key)
        self.assertNotEqual(self.lookup(history=["اول", "دوم"]).key, self.lookup(history=["دوم", "اول"]).key)
        self.answer()
        self.assertIsNone(response_cache.load(self.lookup(request=self.account("two")), self.account("two")))

    def test_changed_model_provider_reasoning_and_selection_mode_invalidate_keys(self):
        first = self.lookup().key
        for setting in [{"AI_LAB_MODEL": "different"}, {"AI_LAB_BASE_URL": "https://other.example/v1"},
                        {"AI_LAB_REASONING_EFFORT": "high"}, {"AI_LAB_LOCAL_SELECTION_ENABLED": False}]:
            with override_settings(**setting):
                self.assertNotEqual(first, self.lookup().key)

    def test_signed_summary_cannot_be_changed_while_retaining_a_valid_quote(self):
        self.answer()
        lookup = self.lookup()
        record = caches["ai_lab"].get(lookup.key)
        record["result"]["parts"][0]["items"][0]["summary_fa"] = "یک توضیح فارسی تغییر کرده و تأیید نشده"
        caches["ai_lab"].set(lookup.key, record)
        _, calls = self.answer()
        self.assertEqual(calls, 3)

    def test_source_change_and_active_generation_replacement_reject_old_cached_results(self):
        self.answer()
        old = self.lookup()
        self.build(force=True)
        self.assertNotEqual(old.key, self.lookup().key)
        self.assertIsNone(response_cache.load(old, self.request))
        self.answer()
        old = self.lookup()
        self.write_article("3851", fixtures.html(text=fixtures.TEXT + " A source update."))
        self.assertIsNone(response_cache.load(old, self.request))
        self.assertIsNone(self.lookup())

    def test_corrupt_stored_evidence_rejects_hit_even_when_original_hash_is_unchanged(self):
        self.answer()
        lookup = self.lookup()
        ReferenceParagraph.objects.update(text=fixtures.TEXT + " Changed stored evidence.")
        self.assertIsNone(response_cache.load(lookup, self.request))

    def test_revoked_base_or_article_access_never_publishes_cached_text(self):
        self.answer()
        publish = MagicMock()
        def permission(request, feature, *, item=None, consume=False):
            if item:
                raise PlatformAPIError("Denied", status_code=402)
        with patch.object(response_cache, "require_feature", side_effect=permission), \
                patch.object(services, "chat", side_effect=AssertionError("No paid fallback on denied access")):
            with self.assertRaises(PlatformAPIError):
                services.answer("درمان مرجع چیست؟", "luna", ["uptodate"], [], self.request, publish=publish)
        publish.assert_not_called()
        with patch.object(response_cache, "require_feature", side_effect=PlatformAPIError("Denied", status_code=402)):
            with self.assertRaises(PlatformAPIError):
                self.lookup()

    def test_cached_hit_checks_each_article_allowance_with_consume(self):
        self.answer()
        with patch.object(response_cache, "require_feature") as permission:
            _, calls = self.answer()
        self.assertEqual(calls, 0)
        self.assertTrue(any(call.kwargs == {"item": "3851", "consume": True} for call in permission.call_args_list))

    def test_mysql_blob_hash_change_without_revision_change_invalidates_hit(self):
        self.answer()
        lookup = self.lookup()
        stamp = reference_index.SourceStamp(lookup.stamp.identity, lookup.stamp.revision, lookup.stamp.version, "mysql")
        mysql_lookup = response_cache.Lookup(lookup.key, stamp, lookup.generation)
        connection = MagicMock()
        connection.cursor.return_value.__enter__.return_value.fetchall.return_value = [{"id": "3851", "blob_hash": "changed"}]
        with patch.object(reference_index, "mysql_source_connection", return_value=connection):
            self.assertIsNone(response_cache.load(mysql_lookup, self.request))

    def test_cache_outage_is_nonfatal_and_does_not_expose_backend_error(self):
        backend = MagicMock()
        backend.get.side_effect = RuntimeError("private connection string")
        backend.set.side_effect = RuntimeError("private connection string")
        with patch.object(response_cache, "caches", {"ai_lab": backend}):
            result, calls = self.answer()
        self.assertEqual(calls, 3)
        self.assertEqual(result["parts"][0]["status"], "answered")
        self.assertNotIn("private connection string", json.dumps(result))

    def test_partial_and_empty_results_are_never_cached(self):
        self.assertFalse(response_cache.complete({"parts": []}))
        self.assertFalse(response_cache.complete({"parts": [{"status": "partial", "items": [{}]}]}))
        self.assertFalse(response_cache.complete({"parts": [{"status": "answered", "items": []}]}))
        result, _ = self.answer()
        lookup = self.lookup()
        caches["ai_lab"].delete(lookup.key)
        partial = deepcopy(result)
        partial["parts"][0]["status"] = "partial"
        response_cache.store(lookup, partial)
        self.assertIsNone(caches["ai_lab"].get(lookup.key))

    def test_disabled_cache_does_not_read_or_write_answers(self):
        with override_settings(AI_LAB_RESPONSE_CACHE_ENABLED=False):
            first, count = self.answer()
            second, second_count = self.answer()
        self.assertEqual((count, second_count), (3, 3))
        self.assertEqual(first["metrics"]["response_cache"], "disabled")

    def test_benchmark_uses_ephemeral_account_and_writes_private_cold_hit_report(self):
        from io import StringIO
        from django.core.management import call_command
        output = self.directory / "cache-diagnostic.json"
        dataset = {"schema": 1, "cases": [{"id": "fixture", "question": "درمان مرجع چیست؟", "expect": "answerable",
            "expected": [{"article_id": "3851", "headings": ["Treatment"]}]}]}
        with patch.object(services, "chat", side_effect=self.model), \
                patch.object(services, "search_articles", return_value=[{"id": "3851", "title": "Reference article"}]), \
                patch("apps.ai_lab.evaluation.load_dataset", return_value=dataset), \
                patch.object(provider, "credentials", return_value={"luna": "test-placeholder"}), \
                patch.object(provider, "build_opener") as network:
            call_command("benchmark_reference_cache", output=str(output), case_ids=["fixture"], stdout=StringIO())
        report = json.loads(output.read_text())
        self.assertEqual(report["cases"][0]["cold"]["metrics"]["response_cache"], "miss")
        self.assertEqual(report["cases"][0]["warm"]["metrics"]["response_cache"], "hit")
        self.assertEqual(report["cases"][0]["warm"]["metrics"]["provider_requests"], 0)
        self.assertEqual(output.stat().st_mode & 0o777, 0o600)
        network.assert_not_called()


@override_settings(AI_LAB_HTTP_KEEPALIVE_SECONDS=30)
class HTTPPoolTests(SimpleTestCase):
    def setUp(self):
        http_transport.close()
        self.addCleanup(http_transport.close)

    def response(self, chunks=(b"{}", b""), status=200, close=False):
        response = MagicMock(status=status, will_close=close)
        response.read1.side_effect = chunks
        response.isclosed.return_value = False
        response.length = None
        return response

    def test_successful_server_closed_response_is_fully_read_without_reusing_dead_socket(self):
        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers.get("Content-Length", "0")))
                self.send_response(200)
                self.send_header("Content-Length", "2")
                self.send_header("Connection", "close")
                self.end_headers()
                self.wfile.write(b"{}")
        server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        server.daemon_threads = True
        Thread(target=server.serve_forever, kwargs={"poll_interval": .02}, daemon=True).start()
        pool = http_transport.HTTPSOpener()
        def connection(host, port, *, timeout, context):
            return HTTPConnection(host, port, timeout=timeout)
        try:
            with patch.object(http_transport.http.client, "HTTPSConnection", side_effect=connection):
                with pool.open(self.request(f"https://127.0.0.1:{server.server_port}/"), timeout=1) as response:
                    self.assertEqual(response.read(100), b"{}")
            self.assertIsNone(pool.connection)
        finally:
            pool.close()
            server.shutdown()
            server.server_close()

    def request(self, base="https://provider.example/v1/chat/completions", key="test-one"):
        return Request(base, data=b"{}", headers={"Authorization": key}, method="POST")

    @patch.object(http_transport.http.client, "HTTPSConnection")
    def test_connection_is_reused_with_new_headers_and_verified_tls(self, factory):
        connection = factory.return_value
        connection.getresponse.side_effect = [self.response(), self.response()]
        pool = http_transport.opener()
        for key in ["test-one", "test-two"]:
            with pool.open(self.request(key=key), timeout=2) as response:
                self.assertEqual(response.read(100), b"{}")
        self.assertEqual(factory.call_count, 1)
        self.assertEqual(connection.request.call_args_list[1].kwargs["headers"]["Authorization"], "test-two")
        context = factory.call_args.kwargs["context"]
        self.assertTrue(context.check_hostname)
        self.assertEqual(context.verify_mode, ssl.CERT_REQUIRED)

    @patch.object(http_transport.http.client, "HTTPSConnection")
    def test_provider_change_idle_expiry_and_unread_body_discard_connection(self, factory):
        factory.return_value.getresponse.side_effect = [self.response() for _ in range(4)]
        pool = http_transport.opener()
        for base in ["https://one.example/v1", "https://two.example/v1"]:
            with pool.open(self.request(base), timeout=2) as response:
                response.read(100)
        self.assertEqual(factory.call_count, 2)
        pool.last_used = time.monotonic() - 31
        with pool.open(self.request("https://two.example/v1"), timeout=2):
            pass
        self.assertIsNone(pool.connection)
        self.assertEqual(factory.call_count, 3)

    @patch.object(http_transport.http.client, "HTTPSConnection")
    def test_redirect_and_stale_post_are_never_replayed(self, factory):
        pool = http_transport.opener()
        response = self.response(status=302)
        factory.return_value.getresponse.return_value = response
        with self.assertRaises(HTTPError):
            pool.open(self.request(), timeout=2)
        response.read1.assert_not_called()
        self.assertEqual(factory.return_value.request.call_count, 1)
        factory.return_value.getresponse.side_effect = RemoteDisconnected()
        with self.assertRaises(RemoteDisconnected):
            pool.open(self.request(), timeout=2)
        self.assertEqual(factory.return_value.request.call_count, 2)
        self.assertIsNone(pool.connection)

    def test_thread_and_process_boundaries_do_not_share_a_live_client(self):
        main = http_transport.opener()
        with ThreadPoolExecutor(max_workers=1) as executor:
            other = executor.submit(http_transport.opener).result()
        self.assertIsNot(main, other)
        with patch.object(http_transport.os, "getpid", return_value=-1):
            self.assertIsNot(main, http_transport.opener())

    @override_settings(AI_LAB_HTTP_POOL_ENABLED=True)
    def test_explicit_proxy_configuration_preserves_legacy_routing(self):
        with patch.object(provider, "getproxies", return_value={"https": "http://private-proxy"}), \
                patch.object(provider, "_urllib_opener") as legacy, patch.object(http_transport, "opener") as pooled:
            provider.build_opener(provider.NoRedirect)
        legacy.assert_called_once()
        pooled.assert_not_called()

    def test_trickling_headers_and_body_are_bounded_by_absolute_deadline(self):
        for drip_headers in [True, False]:
            class Handler(BaseHTTPRequestHandler):
                def log_message(self, *args):
                    pass

                def do_POST(self):
                    self.rfile.read(int(self.headers.get("Content-Length", "0")))
                    header = b"HTTP/1.1 200 OK\r\nContent-Length: 30\r\nConnection: close\r\n\r\n"
                    try:
                        data = header + b"x" * 30 if drip_headers else b"x" * 30
                        if not drip_headers:
                            self.wfile.write(header)
                            self.wfile.flush()
                        for value in data:
                            self.wfile.write(bytes([value]))
                            self.wfile.flush()
                            time.sleep(.02)
                    except OSError:
                        pass
            server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
            server.daemon_threads = True
            thread = Thread(target=server.serve_forever, kwargs={"poll_interval": .02}, daemon=True)
            thread.start()
            def connection(host, port, *, timeout, context):
                return HTTPConnection(host, port, timeout=timeout)
            pool = http_transport.HTTPSOpener()
            started = time.monotonic()
            try:
                with patch.object(http_transport.http.client, "HTTPSConnection", side_effect=connection):
                    with self.assertRaises((HTTPException, OSError, TimeoutError)):
                        with pool.open(self.request(f"https://127.0.0.1:{server.server_port}/"), timeout=.16) as response:
                            response.read(100)
                self.assertLess(time.monotonic() - started, .8)
            finally:
                pool.close()
                server.shutdown()
                server.server_close()


@override_settings(AI_LAB_TOTAL_TIMEOUT_SECONDS=18, AI_LAB_MAX_PROVIDER_REQUESTS=2)
class RuntimeBudgetTests(SimpleTestCase):
    @override_settings(CACHES=TEST_CACHES)
    def test_fresh_heartbeat_does_not_keep_a_job_alive_beyond_worker_budget(self):
        cache = caches["throttle"]
        now = time.time()
        cache.set("ai-lab:job:runtime-expired", {"user_id": "runtime-user", "status": "running", "model": "luna",
            "sources": ["uptodate"], "created_at": now - 25, "heartbeat_at": now})
        cache.set("ai-lab:user:runtime-user", "runtime-expired")
        record = jobs.read("runtime-expired", "runtime-user")
        self.assertEqual(record["status"], "failed")
        self.assertIsNone(cache.get("ai-lab:user:runtime-user"))

    @override_settings(AI_LAB_API_KEY="test-key", AI_LAB_MODEL="test-model", AI_LAB_CREDENTIALS_FILE="",
                       AI_LAB_MIN_CALL_BUDGET_SECONDS=.05)
    def test_invalid_json_retry_does_not_get_a_fresh_time_budget(self):
        clock = [10.0]
        opener = MagicMock()
        def body(limit):
            clock[0] = 10.18
            return json.dumps({"model": "test-model", "choices": [
                {"message": {"content": "invalid JSON"}, "finish_reason": "stop"}]}).encode()
        opener.open.return_value.__enter__.return_value.read.side_effect = body
        token = provider.deadline.set(10.2)
        try:
            with patch.object(provider.time, "monotonic", side_effect=lambda: clock[0]), \
                    patch.object(provider, "build_opener", return_value=opener):
                with self.assertRaisesMessage(provider.ProviderError, "EXPERIMENT_TIMEOUT"):
                    provider.chat("luna", "JSON only", {})
            self.assertEqual(opener.open.call_count, 1)
        finally:
            provider.deadline.reset(token)

    def test_expired_queue_budget_prevents_planning_and_restores_parent_context(self):
        trace = telemetry.Trace(queue_wait_ms=19000)
        with patch.object(services, "chat") as chat:
            with self.assertRaisesMessage(provider.ProviderError, "EXPERIMENT_TIMEOUT"):
                services.answer("درمان مرجع", "luna", ["uptodate"], [], None, trace=trace)
        chat.assert_not_called()
        self.assertEqual(trace.snapshot()["provider_requests"], 0)
        self.assertIsNone(provider.deadline.get())

    def test_existing_outer_deadline_is_not_extended(self):
        token = provider.deadline.set(0)
        try:
            with patch.object(services, "chat") as chat:
                with self.assertRaisesMessage(provider.ProviderError, "EXPERIMENT_TIMEOUT"):
                    services.answer("درمان مرجع", "luna", ["uptodate"], [], None)
            chat.assert_not_called()
            self.assertEqual(provider.deadline.get(), 0)
        finally:
            provider.deadline.reset(token)

    @override_settings(AI_LAB_API_KEY="test-key", AI_LAB_MODEL="test-model", AI_LAB_CREDENTIALS_FILE="")
    def test_request_cap_counts_real_attempts_and_blocks_next_post(self):
        opener = MagicMock()
        opener.open.return_value.__enter__.return_value.read.return_value = b'{}'
        with provider.request_budget(), patch.object(provider, "build_opener", return_value=opener):
            provider.call("luna", {})
            provider.call("luna", {})
            with self.assertRaisesMessage(provider.ProviderError, "SEARCH_REQUEST_LIMIT"):
                provider.call("luna", {})
        self.assertEqual(opener.open.call_count, 2)

    def test_small_remaining_budget_does_not_start_another_model_request(self):
        token = provider.deadline.set(time.monotonic() + .1)
        try:
            with override_settings(AI_LAB_API_KEY="test-key", AI_LAB_CREDENTIALS_FILE=""), patch.object(provider, "build_opener") as opener:
                with self.assertRaisesMessage(provider.ProviderError, "EXPERIMENT_TIMEOUT"):
                    provider.call("luna", {})
            opener.assert_not_called()
        finally:
            provider.deadline.reset(token)
