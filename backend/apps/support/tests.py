import base64
import uuid
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from rest_framework.test import APIClient

from apps.accounts.services import issue_user_session, revoke_user_session
from .models import Conversation, Message, NotificationDelivery, PushSubscription
from .notifications import send_delivery, validate_web_subscription
from .services import mark_read, send_message


class SupportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="support-learner", password="password")
        self.other = get_user_model().objects.create_user(username="other-learner", password="password")
        self.staff = get_user_model().objects.create_superuser(username="support-admin", password="password")
        self.issued = issue_user_session(self.user)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user, token=self.issued.session)
        self.thread = Conversation.objects.create(user=self.user)
        self.base = f"/api/v1/support/conversations/{self.thread.pk}"

    def test_conversation_is_private(self):
        self.client.force_authenticate(user=self.other, token=issue_user_session(self.other).session)
        self.assertEqual(self.client.get(self.base + "/messages/").status_code, 404)
        self.assertEqual(self.client.post(self.base + "/messages/", {"text": "private", "client_id": str(uuid.uuid4())}).status_code, 404)
        self.assertEqual(self.client.post(self.base + "/read/", {"through": 1}).status_code, 404)

    def test_retried_send_is_one_message_and_preserves_first_text(self):
        token = str(uuid.uuid4())
        self.assertEqual(self.client.post(self.base + "/messages/", {"text": "question", "client_id": token}).status_code, 201)
        self.assertEqual(self.client.post(self.base + "/messages/", {"text": "question", "client_id": token}).status_code, 200)
        self.assertEqual(Message.objects.filter(conversation=self.thread).count(), 1)

    def test_user_cannot_spoof_a_staff_reply(self):
        response = self.client.post(self.base + "/messages/", {"text": "hello", "client_id": str(uuid.uuid4()), "from_staff": True})
        self.assertEqual(response.status_code, 201)
        self.assertFalse(Message.objects.get().from_staff)

    def test_read_acknowledgement_does_not_read_a_newer_reply(self):
        first, _ = send_message(self.thread, self.staff, "reply one", uuid.uuid4(), staff=True)
        second, _ = send_message(self.thread, self.staff, "reply two", uuid.uuid4(), staff=True)
        mark_read(self.thread, first.pk)
        summary = self.client.get("/api/v1/support/summary/").json()
        self.assertEqual(summary["unread"], 1)
        self.thread.refresh_from_db()
        self.assertLess(self.thread.user_read_id, second.pk)

    def test_default_conversation_is_reused(self):
        first = self.client.post("/api/v1/support/conversations/", {}, format="json")
        second = self.client.post("/api/v1/support/conversations/", {}, format="json")
        self.assertEqual(first.json()["id"], second.json()["id"])

    def test_admin_requires_support_permission(self):
        browser = Client()
        browser.force_login(self.other)
        response = browser.get("/manage/app/support/")
        self.assertNotEqual(response.status_code, 200)
        browser.force_login(self.staff)
        self.assertEqual(browser.get("/manage/app/support/").status_code, 200)
        self.assertEqual(browser.get(f"/manage/app/support/{self.thread.pk}/").status_code, 200)

    def test_push_subscription_is_disabled_on_same_device_account_switch(self):
        device = "device-install-123456789"
        old = PushSubscription.objects.create(user=self.other, device_id=device, platform="android", expo_token="ExpoPushToken[old]")
        response = self.client.post("/api/v1/support/subscription/", {"device_id": device, "platform": "android", "expo_token": "ExpoPushToken[current]", "enabled": True}, format="json")
        self.assertEqual(response.status_code, 200)
        old.refresh_from_db()
        self.assertFalse(old.enabled)

    def test_saved_staff_reply_has_idempotent_notification_outbox(self):
        PushSubscription.objects.create(user=self.user, session=self.issued.session, device_id="install-123456789", platform="android", expo_token="ExpoPushToken[valid]")
        token = uuid.uuid4()
        first, _ = send_message(self.thread, self.staff, "reply", token, staff=True)
        second, _ = send_message(self.thread, self.staff, "reply", token, staff=True)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(NotificationDelivery.objects.count(), 1)

    def test_revoked_session_does_not_receive_a_queued_notification(self):
        subscription = PushSubscription.objects.create(user=self.user, session=self.issued.session, device_id="install-123456789", platform="android", expo_token="ExpoPushToken[valid]")
        message, _ = send_message(self.thread, self.staff, "reply", uuid.uuid4(), staff=True)
        delivery = NotificationDelivery.objects.get(message=message, subscription=subscription)
        revoke_user_session(self.issued.session)
        with patch("apps.support.notifications.urlopen") as outbound:
            self.assertTrue(send_delivery(delivery.pk))
            outbound.assert_not_called()
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "skipped")

    def test_subscription_rejects_arbitrary_network_targets(self):
        for endpoint in ["http://127.0.0.1/private", "https://169.254.169.254/", "https://fcm.googleapis.com.evil.example/send"]:
            with self.assertRaises(ValueError):
                validate_web_subscription({"endpoint": endpoint, "keys": {}})

    def test_empty_and_oversized_messages_are_rejected(self):
        for text in ["   ", "a" * 4001]:
            self.assertEqual(self.client.post(self.base + "/messages/", {"text": text, "client_id": str(uuid.uuid4())}).status_code, 400)
