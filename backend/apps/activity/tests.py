import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.test import Client
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.services import issue_user_session
from .models import ActivityEvent
from .services import APP_SECTIONS, click_map, report


class ActivityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="activity-learner")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user, token=issue_user_session(self.user).session)

    def test_duplicate_batches_are_idempotent(self):
        body = {"events": [{"id": str(uuid.uuid4()), "section": "lessons", "action": "view"}]}
        self.assertEqual(self.client.post("/api/v1/activity/events/", body, format="json").status_code, 202)
        self.client.post("/api/v1/activity/events/", body, format="json")
        self.assertEqual(ActivityEvent.objects.count(), 1)

    def test_ai_lab_events_do_not_block_other_queued_activity(self):
        events = [{"id": str(uuid.uuid4()), "section": section, "action": "view"}
                  for section in ["dashboard", "aiLab", "lessons", "aiLab"]]
        response = self.client.post("/api/v1/activity/events/", {"events": events}, format="json")
        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data["accepted"], 4)
        self.assertEqual(ActivityEvent.objects.filter(section="aiLab").count(), 2)
        self.assertIn("aiLab", {row["key"] for row in report(source="app")["sections"]})

    def test_unknown_sections_and_invalid_click_coordinates_are_rejected(self):
        for event in [{"section": "private-user-search", "action": "view"}, {"section": "lessons", "action": "click", "x": 101, "y": 20}, {"section": "lessons", "action": "click"}]:
            self.assertEqual(self.client.post("/api/v1/activity/events/", {"events": [{"id": str(uuid.uuid4()), **event}]}, format="json").status_code, 400)

    def test_report_keeps_zero_usage_sections_and_filters_source(self):
        ActivityEvent.objects.create(user=self.user, source="app", section="lessons", action="view")
        ActivityEvent.objects.create(source="site", section="home", action="view")
        data = report(source="app")
        self.assertEqual(data["total"], 1)
        self.assertEqual(len(data["sections"]), len(APP_SECTIONS))
        self.assertEqual(data["most"][0]["key"], "lessons")
        self.assertEqual(data["least"][0]["views"], 0)

    def test_click_map_separates_article_canvas_and_screen_size(self):
        ActivityEvent.objects.create(source="app", section="uptodateArticle", action="click", x=100, y=100, area="article", viewport="mobile")
        ActivityEvent.objects.create(source="app", section="uptodateArticle", action="click", x=0, y=0, area="screen", viewport="mobile")
        grid = click_map(source="app", section="uptodateArticle", area="article")
        self.assertEqual(grid[-1][-1], 1)
        self.assertEqual(sum(map(sum, grid)), 1)

    def test_management_report_requires_admin(self):
        self.client.force_authenticate(user=None)
        self.assertNotEqual(self.client.get("/manage/app/usage/").status_code, 200)

    def test_temporal_heatmap_uses_tehran_weekday_and_hour(self):
        now = timezone.now().astimezone(ZoneInfo("Asia/Tehran"))
        ActivityEvent.objects.create(source="app", section="lessons", action="view", occurred_at=now)
        data = report(source="app")
        self.assertEqual(data["matrix"][(now.weekday() + 2) % 7][now.hour], 1)

    def test_site_click_endpoint_requires_csrf_and_records_only_known_sections(self):
        browser = Client(enforce_csrf_checks=True, HTTP_HOST="site.localhost")
        response = browser.get("/")
        self.assertEqual(response.status_code, 200)
        event = {"id": str(uuid.uuid4()), "section": "home", "action": "click", "x": 45, "y": 22, "viewport": "desktop"}
        self.assertEqual(browser.post("/events/activity/", {"events": [event]}, content_type="application/json").status_code, 403)
        token = browser.cookies["csrftoken"].value
        response = browser.post("/events/activity/", {"events": [event]}, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 202)
        record = ActivityEvent.objects.get(pk=event["id"])
        self.assertEqual((record.source, record.x, record.y, record.viewport), ("site", 45, 22, "desktop"))
        heartbeat = {"id": str(uuid.uuid4()), "section": "home", "action": "engagement", "duration_seconds": 12}
        response = browser.post("/events/activity/", {"events": [heartbeat]}, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(response.status_code, 202)
        self.assertEqual(next(row for row in report(source="site")["sections"] if row["key"] == "home")["seconds"], 12)

    def test_admin_can_render_usage_and_device_reports(self):
        admin = get_user_model().objects.create_superuser(username="heatmap-admin", password="test-password")
        browser = Client()
        browser.force_login(admin)
        self.assertEqual(browser.get("/manage/app/usage/").status_code, 200)
        stale = issue_user_session(self.user).session
        stale.django_session_key = "browser-cookie-no-longer-present"
        stale.save(update_fields=["django_session_key"])
        response = browser.get("/manage/app/devices/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(stale.pk, [session.pk for session in response.context["sessions"]])
        sessions = self.client.get("/api/v1/auth/sessions/").json()
        self.assertFalse(next(session for session in sessions if session["id"] == str(stale.pk))["is_active"])
