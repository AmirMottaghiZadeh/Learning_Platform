"""Waiting queue: capacity pressure queues searches instead of refusing them."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from . import jobs, runner, views
from .models import SearchRun

TEST_CACHES = {name: {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": f"queue-{name}"}
               for name in ["default", "throttle", "ai_lab"]}


@override_settings(CACHES=TEST_CACHES, AI_LAB_ENABLED=True, AI_LAB_SEARCH_ENGINE="hybrid",
                   AI_LAB_EVENT_REDIS_URL="", AI_LAB_EXECUTOR="thread", ENVIRONMENT="local",
                   AI_LAB_FEEDBACK_ENABLED=False, AI_LAB_STREAM_ANSWER_DRAFTS=False,
                   AI_LAB_MAX_CONCURRENT_JOBS=2, AI_LAB_MAX_CONCURRENT_SLOTS=64,
                   AI_LAB_QUEUE_MAX_LENGTH=200, AI_LAB_QUEUE_ETA_SECONDS=20)
class QueueAdmissionTests(TestCase):
    def setUp(self):
        caches["throttle"].clear()
        self.senders = []
        for number in range(6):
            user = get_user_model().objects.create_user(f"queue-user-{number}", is_staff=True, is_superuser=True)
            client = APIClient()
            client.force_authenticate(user)
            self.senders.append(client)
        self.enqueue = patch.object(views._executor, "submit").start()
        self.addCleanup(patch.stopall)

    def submit(self, number, **changes):
        payload = {"question": f"پرسش صف شمارهٔ {number}", "model": "luna",
                   "sources": ["uptodate"], "request_id": f"queue-request-{number}"}
        return self.senders[number].post("/api/v1/ai-lab/ask/", {**payload, **changes}, format="json")

    def release_slot(self, run):
        SearchRun.objects.filter(pk=run.pk).update(status="complete")
        cache = caches["throttle"]
        cache.delete(run.slot)
        cache.delete(f"ai-lab:user:{run.owner_id}")

    def test_capacity_full_queues_with_position_instead_of_rejecting(self):
        self.assertEqual(self.submit(0).status_code, 202)
        self.assertEqual(self.submit(1).status_code, 202)
        third = self.submit(2)
        self.assertEqual(third.status_code, 202)
        self.assertEqual(third.data["queue_position"], 1)
        # One round of both slots must finish before the next batch starts.
        self.assertEqual(third.data["eta_seconds"], 20)
        run = SearchRun.objects.get(pk=third.data["job_id"])
        self.assertEqual((run.status, run.slot), ("queued", ""))
        self.assertEqual(self.enqueue.call_count, 2)

    def test_waiting_searches_are_first_in_first_out(self):
        for number in range(2):
            self.submit(number)
        first = self.submit(2)
        second = self.submit(3)
        self.assertEqual(first.data["queue_position"], 1)
        self.assertEqual(second.data["queue_position"], 2)
        self.assertEqual(second.data["eta_seconds"], 20)
        # A position past the first batch waits an extra round.
        third = self.submit(4)
        self.assertEqual(third.data["queue_position"], 3)
        self.assertEqual(third.data["eta_seconds"], 40)

    def test_reading_a_waiting_job_reports_the_same_position(self):
        self.submit(0)
        self.submit(1)
        identifier = self.submit(2).data["job_id"]
        record = self.senders[2].get(f"/api/v1/ai-lab/results/{identifier}/")
        self.assertEqual(record.status_code, 200)
        self.assertEqual(record.data["stage"], "queued")
        self.assertEqual(record.data["queue_position"], 1)
        self.assertEqual(jobs.read(identifier, SearchRun.objects.get(pk=identifier).owner_id)["queue_position"], 1)

    def test_freed_slot_starts_the_oldest_waiting_search(self):
        self.submit(0)
        self.submit(1)
        waiting = self.submit(2).data["job_id"]
        self.assertEqual(runner.promote(), 0)  # both slots still busy
        self.release_slot(SearchRun.objects.get(slot="ai-lab:slot:0"))
        self.assertEqual(runner.promote(), 1)
        run = SearchRun.objects.get(pk=waiting)
        self.assertTrue(run.slot)
        self.assertEqual(self.enqueue.call_count, 3)

    def test_queue_promotes_in_arrival_order_when_several_slots_free(self):
        for number in range(2):
            self.submit(number)
        waiting = [self.submit(number).data["job_id"] for number in (2, 3, 4)]
        for run in SearchRun.objects.filter(slot__startswith="ai-lab:slot:"):
            self.release_slot(run)
        self.assertEqual(runner.promote(), 2)
        promoted = list(SearchRun.objects.filter(pk__in=waiting, slot__startswith="ai-lab:slot:").order_by("created_at"))
        self.assertEqual([str(run.pk) for run in promoted], waiting[:2])

    @override_settings(AI_LAB_QUEUE_MAX_LENGTH=1)
    def test_a_full_queue_is_reported_instead_of_growing_without_bound(self):
        self.submit(0)
        self.submit(1)
        self.assertEqual(self.submit(2).status_code, 202)  # one waiting seat
        full = self.submit(3)
        self.assertEqual(full.status_code, 429)
        self.assertEqual(full.data["code"], "AI_LAB_QUEUE_FULL")
        self.assertEqual(SearchRun.objects.filter(status="queued", slot="").count(), 1)

    @override_settings(AI_LAB_MAX_CONCURRENT_JOBS=32, AI_LAB_MAX_CONCURRENT_SLOTS=8)
    def test_deployment_ceiling_caps_the_slot_names(self):
        self.assertEqual(runner._capacity(), 8)
        self.assertEqual(len(runner._slot_names()), 8)

    def test_idempotent_resubmit_of_a_waiting_search_keeps_its_place(self):
        self.submit(0)
        self.submit(1)
        first = self.submit(2)
        again = self.submit(2)
        self.assertEqual(again.status_code, 202)
        self.assertEqual(again.data["job_id"], first.data["job_id"])
        self.assertEqual(again.data["queue_position"], first.data["queue_position"])
        self.assertEqual(SearchRun.objects.filter(status="queued", slot="").count(), 1)
