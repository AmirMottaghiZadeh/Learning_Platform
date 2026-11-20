import base64
import uuid
from io import StringIO
from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.core.management import call_command
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.services import issue_user_session, revoke_user_session
from .models import Conversation, Message, NotificationDelivery, PushSubscription
from .notifications import send_delivery, validate_web_subscription
from .services import mark_read, send_message


@override_settings(SUPPORT_PUSH_NOTIFICATIONS_ENABLED=True)
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


@override_settings(SUPPORT_PUSH_NOTIFICATIONS_ENABLED=False)
class DisabledSupportNotificationsTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="paused-push-user")
        self.staff = get_user_model().objects.create_superuser(username="paused-push-admin", password="password")
        self.session = issue_user_session(self.user).session
        self.client = APIClient()
        self.client.force_authenticate(user=self.user, token=self.session)
        self.thread = Conversation.objects.create(user=self.user)
        self.subscription = PushSubscription.objects.create(user=self.user, session=self.session, device_id="paused-install-123456", platform="android", expo_token="ExpoPushToken[valid]")

    @override_settings(SUPPORT_WEB_PUSH_PUBLIC_KEY="configured-public", SUPPORT_WEB_PUSH_PRIVATE_KEY="/private/configured.pem")
    def test_summary_preserves_unread_count_but_disables_push(self):
        Message.objects.create(conversation=self.thread, sender=self.staff, from_staff=True, text="reply")
        response = self.client.get("/api/v1/support/summary/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"unread": 1, "push_enabled": False, "web_push_public_key": "", "web_push_configured": False})

    def test_registration_is_blocked_but_unsubscribe_still_works(self):
        body = {"device_id": self.subscription.device_id, "platform": "android", "expo_token": self.subscription.expo_token, "enabled": True}
        response = self.client.post("/api/v1/support/subscription/", body, format="json")
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["code"], "SUPPORT_NOTIFICATIONS_DISABLED")
        body["enabled"] = False
        self.assertEqual(self.client.post("/api/v1/support/subscription/", body, format="json").status_code, 200)
        self.subscription.refresh_from_db()
        self.assertFalse(self.subscription.enabled)

    def test_reply_is_saved_without_creating_or_queuing_push(self):
        with patch("apps.support.services._queue_notification") as queue, self.captureOnCommitCallbacks(execute=True):
            message, created = send_message(self.thread, self.staff, "chat still works", uuid.uuid4(), staff=True)
        self.assertTrue(created)
        self.assertEqual(message.text, "chat still works")
        self.assertFalse(NotificationDelivery.objects.exists())
        queue.assert_not_called()

    def test_existing_deliveries_cannot_contact_either_provider(self):
        message = Message.objects.create(conversation=self.thread, sender=self.staff, from_staff=True, text="old reply")
        with patch("apps.support.notifications.urlopen") as expo, patch("pywebpush.webpush") as web:
            for platform in ["android", "web"]:
                with self.subTest(platform=platform):
                    self.subscription.platform = platform
                    self.subscription.save(update_fields=["platform"])
                    delivery = NotificationDelivery.objects.create(message=message, subscription=self.subscription)
                    self.assertTrue(send_delivery(delivery.pk))
                    delivery.refresh_from_db()
                    self.assertEqual((delivery.status, delivery.error, delivery.attempts), ("skipped", "notifications_disabled", 0))
                    delivery.delete()
            expo.assert_not_called()
            web.assert_not_called()

    def test_disabled_retry_command_skips_pending_messages_without_queuing(self):
        message = Message.objects.create(conversation=self.thread, sender=self.staff, from_staff=True, text="old reply")
        delivery = NotificationDelivery.objects.create(message=message, subscription=self.subscription)
        abandoned_message = Message.objects.create(conversation=self.thread, sender=self.staff, from_staff=True, text="abandoned reply")
        abandoned = NotificationDelivery.objects.create(message=abandoned_message, subscription=self.subscription, status="sending")
        NotificationDelivery.objects.filter(pk=abandoned.pk).update(updated_at=timezone.now() - timedelta(minutes=6))
        with patch("apps.support.management.commands.retry_support_notifications.enqueue") as queue:
            output = StringIO()
            call_command("retry_support_notifications", stdout=output)
        queue.assert_not_called()
        self.assertIn("disabled", output.getvalue())
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, "skipped")
        abandoned.refresh_from_db()
        self.assertEqual(abandoned.status, "skipped")

    def test_management_chat_displays_paused_notification_status(self):
        browser = Client()
        browser.force_login(self.staff)
        self.assertContains(browser.get("/manage/app/support/"), "اعلان‌ها: فعلاً غیرفعال")
