import json
from unittest.mock import patch
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import TestCase, SimpleTestCase, override_settings
from rest_framework.test import APIClient

from . import events, jobs, runner, job_store, views
from .models import SearchRun
from .provider import ProviderError

TEST_CACHES = {name: {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": f"durable-{name}"}
               for name in ["default", "throttle", "ai_lab"]}


@override_settings(CACHES=TEST_CACHES, AI_LAB_ENABLED=True, AI_LAB_SEARCH_ENGINE="hybrid",
                   AI_LAB_EVENT_REDIS_URL="", AI_LAB_EXECUTOR="thread", ENVIRONMENT="local",
                   AI_LAB_FEEDBACK_ENABLED=False, AI_LAB_STREAM_ANSWER_DRAFTS=False)
class DurableSearchTests(TestCase):
    def setUp(self):
        caches["throttle"].clear()
        self.user = get_user_model().objects.create_user("stream-owner", is_staff=True, is_superuser=True)
        self.other = get_user_model().objects.create_user("stream-other", is_staff=True, is_superuser=True)
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        self.payload = {"question": "پرسش خصوصی از منابع", "model": "luna", "sources": ["uptodate"], "request_id": "client-one"}
        self.enqueue = patch.object(views._executor, "submit").start()
        self.addCleanup(patch.stopall)

    def submit(self, **changes):
        return self.client.post("/api/v1/ai-lab/ask/", {**self.payload, **changes}, format="json")

    def test_idempotent_post_enqueues_once_and_rejects_changed_payload(self):
        first = self.submit()
        self.assertEqual(first.status_code, 202)
        self.assertEqual(self.submit().data, first.data)
        self.assertEqual(self.enqueue.call_count, 1)
        self.assertEqual(self.submit(question="پرسش دیگری از منابع").status_code, 409)
        self.assertEqual(SearchRun.objects.count(), 1)
        run = SearchRun.objects.get()
        self.assertNotIn(self.payload["question"], run.encrypted_payload)
        self.assertEqual(job_store.decode(run.encrypted_payload)["question"], self.payload["question"])

    def test_broker_messages_only_contain_job_ids(self):
        with override_settings(AI_LAB_EXECUTOR="celery", CELERY_TASK_ALWAYS_EAGER=False), patch("apps.ai_lab.tasks.run_search.apply_async") as queued:
            response = self.submit()
        self.assertEqual(response.status_code, 202)
        queued.assert_called_once_with(args=[response.data["job_id"]], queue="ai_search")
        self.enqueue.assert_not_called()

    def test_local_eager_setting_for_other_features_never_runs_ai_in_the_web_request(self):
        with override_settings(AI_LAB_EXECUTOR="celery",CELERY_TASK_ALWAYS_EAGER=True,CELERY_BROKER_URL="redis://localhost/4"),patch("config.celery.app.send_task") as queued:
            response=self.submit()
        self.assertEqual(response.status_code,202)
        queued.assert_called_once_with("ai_lab.run_search",args=[response.data["job_id"]],queue="ai_search")
        self.enqueue.assert_not_called()

    def test_event_failure_prevents_paid_work_and_does_not_leave_a_live_job(self):
        with patch.object(events, "last_sequence", side_effect=ProviderError("SEARCH_EVENT_STORE_UNAVAILABLE")):
            self.assertEqual(self.submit().status_code, 503)
        self.assertEqual(SearchRun.objects.count(), 0)
        self.enqueue.assert_not_called()

    def test_queue_redelivery_does_not_start_the_provider_again(self):
        identifier = self.submit().data["job_id"]
        with patch.object(runner, "close_old_connections"), patch.object(views, "_run") as run:
            runner.execute(identifier)
            runner.execute(identifier)
        run.assert_called_once()
        self.assertTrue(run.call_args.kwargs["durable"])
        self.assertEqual(SearchRun.objects.get().status, "running")

    def test_missing_cache_recovers_same_owned_job_from_durable_state(self):
        identifier = self.submit().data["job_id"]
        caches["throttle"].clear()
        self.assertEqual(self.client.get("/api/v1/ai-lab/active/").data["active_job"]["job_id"], identifier)
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(f"/api/v1/ai-lab/results/{identifier}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/v1/ai-lab/results/{identifier}/stream/").status_code, 404)
        self.assertEqual(self.client.post(f"/api/v1/ai-lab/results/{identifier}/cancel/").status_code, 404)

    def test_queued_cancellation_releases_capacity_and_never_calls_a_model(self):
        identifier = self.submit().data["job_id"]
        self.assertEqual(self.client.post(f"/api/v1/ai-lab/results/{identifier}/cancel/").status_code, 200)
        with patch.object(runner, "close_old_connections"), patch.object(views, "_run") as run:
            runner.execute(identifier)
        run.assert_not_called()
        self.assertIsNone(jobs.active(self.user.pk))
        result = self.client.get(f"/api/v1/ai-lab/results/{identifier}/").data
        self.assertEqual(result["error"]["code"], "SEARCH_CANCELLED")

    def test_replayed_stream_has_ordered_sources_then_complete_and_no_private_payload(self):
        identifier = self.submit().data["job_id"]
        events.append(identifier, {"type": "sources", "findings": [{"id": "0:10:P1"}]})
        events.append(identifier, {"type": "complete", "job": {"status": "complete", "result": {"parts": []}}})
        response = self.client.get(f"/api/v1/ai-lab/results/{identifier}/stream/?after_sequence=0", HTTP_ACCEPT="application/x-ndjson")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["X-Accel-Buffering"], "no")
        content = b"".join(response.streaming_content).decode()
        rows = [json.loads(line) for line in content.splitlines()]
        self.assertEqual([row["sequence"] for row in rows], [1, 2, 3])
        self.assertEqual([row["type"] for row in rows], ["snapshot", "sources", "complete"])
        self.assertNotIn("encrypted_payload", content)
        self.assertNotIn(self.payload["question"], content)
        self.assertEqual(self.enqueue.call_count, 1)

    def test_result_survives_cache_loss_and_retrieved_sources_are_upgraded(self):
        identifier = self.submit().data["job_id"]
        citation = {"source_id": "P1", "verification": "retrieved", "summary_fa": ""}
        def produce(*args, **kwargs):
            publish = args[6]
            event = {"part_index": 0, "question_fa": "سؤال", "article_id": "10", "citations": [citation]}
            publish(event)
            publish({**event, "citations": [{**citation, "verification": "verified", "summary_fa": "متن تأییدشده"}]})
            kwargs["on_event"]({"type": "answer_delta", "part_index": 0, "text": "پیش‌نویس"})
            return {"parts": [], "model": "luna"}
        with patch.object(views, "answer", side_effect=produce), patch.object(views, "close_old_connections"), patch.object(runner, "close_old_connections"):
            runner.execute(identifier)
        run = SearchRun.objects.get()
        self.assertEqual(run.status, "complete")
        result = jobs.read(identifier, self.user.pk)
        self.assertEqual(len(result["findings"]), 1)
        self.assertEqual(result["findings"][0]["citation"]["verification"], "verified")
        self.assertNotIn("answer_drafts", result)
        caches["throttle"].clear()
        restored = jobs.read(identifier, self.user.pk)
        self.assertEqual(restored["status"], "complete")
        self.assertEqual(restored["findings"], result["findings"])

    def test_sql_final_state_wins_over_stale_running_cache_after_redis_recovery(self):
        identifier = self.submit().data["job_id"]
        SearchRun.objects.filter(pk=identifier).update(status="complete",
            encrypted_result=job_store.encode({"status":"complete","result":{"parts":[]}}))
        response = self.client.get(f"/api/v1/ai-lab/results/{identifier}/")
        self.assertEqual(response.data["status"], "complete")
        self.assertNotIn("error", response.data)

    @override_settings(AI_LAB_FEEDBACK_ENABLED=True)
    def test_feedback_database_is_not_on_the_answer_delivery_path(self):
        identifier = self.submit().data["job_id"]
        with patch.object(views, "answer", return_value={"parts":[]}), patch.object(views,"close_old_connections"), \
                patch.object(runner,"close_old_connections"), patch("apps.ai_feedback.services.save_answer") as store:
            runner.execute(identifier)
        store.assert_not_called()
        self.assertTrue(jobs.read(identifier,self.user.pk)["feedback_available"])

    @override_settings(AI_LAB_MAX_CONCURRENT_JOBS=2)
    def test_redis_loss_does_not_allow_more_jobs_than_the_persisted_capacity(self):
        self.assertEqual(self.submit().status_code,202)
        caches["throttle"].clear()
        self.client.force_authenticate(self.other)
        self.assertEqual(self.submit(request_id="other-request").status_code,202)
        third=get_user_model().objects.create_user("stream-third",is_staff=True,is_superuser=True)
        self.client.force_authenticate(third)
        response=self.submit(request_id="third-request")
        self.assertEqual(response.status_code,429)
        self.assertEqual(SearchRun.objects.filter(status__in=["queued","running"]).count(),2)
        self.assertEqual(self.enqueue.call_count,2)

    @override_settings(AI_LAB_LOCAL_LEXICAL_PILOT=True)
    def test_local_lexical_pilot_stays_admin_only_even_with_an_allowlisted_learner(self):
        learner=get_user_model().objects.create_user("pilot-learner")
        self.assertTrue(self.client.get("/api/v1/ai-lab/status/").data["enabled"])
        self.client.force_authenticate(learner)
        with override_settings(AI_LAB_USER_IDS={str(learner.pk)}):
            self.assertFalse(self.client.get("/api/v1/ai-lab/status/").data["enabled"])


@override_settings(AI_LAB_EVENT_REDIS_URL="", ENVIRONMENT="local")
class EventJournalTests(SimpleTestCase):
    def test_search_and_indexing_queues_have_independent_broker_routes(self):
        from config.celery import app
        for name in ["ai_search","ai_indexing"]:
            queue=app.amqp.queues[name]
            self.assertEqual(queue.exchange.name,name)
            self.assertEqual(queue.routing_key,name)

    def test_events_replay_after_sequence_and_never_include_credential_strings(self):
        identifier = uuid4()
        self.assertEqual(events.append(identifier, {"type": "heartbeat"}), 1)
        self.assertEqual(events.append(identifier, {"type": "heartbeat"}), 2)
        self.assertEqual([r["sequence"] for r in events.read(identifier, 1, block_ms=0)], [2])
        with self.assertRaisesMessage(ProviderError, "UNSAFE_SEARCH_EVENT"):
            events.append(identifier, {"secret": "sk-" + "x" * 30})
        self.assertEqual(events.last_sequence(identifier), 2)

    @override_settings(ENVIRONMENT="production", RUNNING_TESTS=False)
    def test_production_never_silently_uses_an_in_process_journal(self):
        with self.assertRaisesMessage(ProviderError, "SEARCH_EVENT_STORE_REQUIRED"):
            events.append(uuid4(), {"type": "heartbeat"})
