from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client, RequestFactory, TestCase, TransactionTestCase, override_settings, skipUnlessDBFeature
from django.utils import timezone
from rest_framework.test import APIClient

from .devices import client_ip, device_details
from .models import UserSession
from .services import issue_user_session, revoke_user_session


@override_settings(AUTH_MAX_ACTIVE_SESSIONS=2)
class DeviceSessionTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="device-user", password="test-password")
        self.factory = RequestFactory()
        caches["throttle"].clear()
        self.addCleanup(caches["throttle"].clear)

    def request(self, identity, ip="203.0.113.1"):
        return self.factory.post("/api/v1/auth/login/", HTTP_X_DEVICE_ID=identity * 32, HTTP_X_CLIENT_PLATFORM="android", HTTP_X_DEVICE_OS_VERSION="14", HTTP_USER_AGENT="Pharmenta/1.0", REMOTE_ADDR=ip)

    def test_third_device_replaces_oldest_session(self):
        first = issue_user_session(self.user, request=self.request("a"))
        second = issue_user_session(self.user, request=self.request("b"))
        third = issue_user_session(self.user, request=self.request("c"))
        self.assertEqual(UserSession.objects.filter(user=self.user, revoked_at=None).count(), 2)
        first.session.refresh_from_db(); second.session.refresh_from_db()
        self.assertFalse(first.session.is_active)
        self.assertEqual(first.session.revoke_reason, "session_limit_replaced")
        self.assertTrue(second.session.is_active and third.session.is_active)
        self.assertFalse(first.session.refresh_tokens.filter(revoked_at=None).exists())

    def test_http_login_from_new_ip_succeeds_when_two_slots_are_full(self):
        first = issue_user_session(self.user, request=self.request("a"))
        issue_user_session(self.user, request=self.request("b"))
        client = APIClient()
        response = client.post("/api/v1/auth/login/", {
            "username": self.user.username, "password": "test-password",
        }, format="json", HTTP_X_DEVICE_ID="c" * 32, REMOTE_ADDR="198.51.100.7")
        self.assertEqual(response.status_code, 200)
        new_session = UserSession.objects.get(pk=response.data["session_id"])
        self.assertEqual(new_session.ip_address, "198.51.100.7")
        client.credentials(HTTP_AUTHORIZATION="Bearer " + first.access_token)
        self.assertEqual(client.get("/api/v1/auth/me/").status_code, 401)
        client.credentials(HTTP_AUTHORIZATION="Bearer " + response.data["access_token"])
        self.assertEqual(client.get("/api/v1/auth/me/").status_code, 200)

    def test_session_with_least_recent_use_is_replaced(self):
        first = issue_user_session(self.user, request=self.request("a"))
        second = issue_user_session(self.user, request=self.request("b"))
        UserSession.objects.filter(pk=first.session.pk).update(last_used_at=timezone.now())
        third = issue_user_session(self.user, request=self.request("c"))
        first.session.refresh_from_db()
        second.session.refresh_from_db()
        self.assertTrue(first.session.is_active and third.session.is_active)
        self.assertFalse(second.session.is_active)

    def test_reauthentication_same_install_does_not_use_an_extra_slot(self):
        first = issue_user_session(self.user, request=self.request("a"))
        issue_user_session(self.user, request=self.request("b"))
        replacement = issue_user_session(self.user, request=self.request("a"))
        first.session.refresh_from_db()
        self.assertFalse(first.session.is_active)
        self.assertTrue(replacement.session.is_active)
        self.assertEqual(UserSession.objects.filter(user=self.user, revoked_at=None).count(), 2)

    def test_revoking_one_device_opens_a_slot(self):
        first = issue_user_session(self.user, request=self.request("a"))
        issue_user_session(self.user, request=self.request("b"))
        revoke_user_session(first.session)
        self.assertTrue(issue_user_session(self.user, request=self.request("c")).session.is_active)

    def test_authentication_retains_ip_history_and_native_os(self):
        issued = issue_user_session(self.user, request=self.request("a"))
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer " + issued.access_token)
        response = client.get("/api/v1/auth/me/", REMOTE_ADDR="203.0.113.2", HTTP_X_CLIENT_PLATFORM="android", HTTP_X_DEVICE_OS_VERSION="14")
        self.assertEqual(response.status_code, 200)
        issued.session.refresh_from_db()
        self.assertEqual(issued.session.os_name, "Android")
        self.assertTrue(issued.session.is_active)
        self.assertEqual(UserSession.objects.filter(user=self.user, revoked_at=None).count(), 1)
        self.assertEqual(set(issued.session.addresses.values_list("ip_address", flat=True)), {"203.0.113.1", "203.0.113.2"})

    def test_browser_and_app_share_the_limit(self):
        issued = issue_user_session(self.user, request=self.request("a"))
        browser = Client()
        self.assertTrue(browser.login(username=self.user.username, password="test-password"))
        browser.get("/api/v1/docs/")
        self.assertEqual(UserSession.objects.filter(user=self.user, revoked_at=None).count(), 2)
        replacement = issue_user_session(self.user, request=self.request("b"))
        issued.session.refresh_from_db()
        self.assertFalse(issued.session.is_active)
        self.assertTrue(replacement.session.is_active)
        self.assertEqual(browser.get("/api/v1/docs/").status_code, 200)

    def test_replacing_browser_session_deletes_its_cookie(self):
        browser = Client()
        browser.force_login(self.user)
        record = UserSession.objects.get(user=self.user)
        issue_user_session(self.user, request=self.request("a"))
        issue_user_session(self.user, request=self.request("b"))
        record.refresh_from_db()
        self.assertFalse(record.is_active)
        self.assertNotIn("_auth_user_id", browser.session)

    def test_revoked_browser_cookie_no_longer_authenticates(self):
        browser = Client()
        browser.force_login(self.user)
        record = UserSession.objects.get(user=self.user)
        revoke_user_session(record)
        self.assertNotIn("_auth_user_id", browser.session)

    @override_settings(CLIENT_IP_TRUSTED_PROXIES="127.0.0.1/32")
    def test_forwarded_ip_is_accepted_only_from_a_trusted_peer(self):
        request = self.factory.get("/", REMOTE_ADDR="203.0.113.5", HTTP_X_FORWARDED_FOR="198.51.100.8")
        self.assertEqual(client_ip(request), "203.0.113.5")
        request.META["REMOTE_ADDR"] = "127.0.0.1"
        self.assertEqual(client_ip(request), "198.51.100.8")
        request.META["HTTP_X_FORWARDED_FOR"] = "spoofed, 198.51.100.9"
        self.assertEqual(client_ip(request), "198.51.100.9")

    def test_browser_os_is_detected_from_user_agent(self):
        request = self.factory.get("/", HTTP_USER_AGENT="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/130.0.0.0 Safari/537.36")
        data = device_details(request)
        self.assertEqual((data["os_name"], data["browser"], data["device_type"]), ("Windows", "Chrome", "desktop"))

    def test_legacy_environment_value_cannot_raise_limit_above_two(self):
        with override_settings(AUTH_MAX_ACTIVE_SESSIONS=10):
            issue_user_session(self.user, request=self.request("a"))
            issue_user_session(self.user, request=self.request("b"))
            issue_user_session(self.user, request=self.request("c"))
            self.assertEqual(UserSession.objects.filter(user=self.user, revoked_at=None).count(), 2)


@override_settings(AUTH_MAX_ACTIVE_SESSIONS=2)
class ConcurrentDeviceTests(TransactionTestCase):
    @skipUnlessDBFeature("has_select_for_update")
    def test_simultaneous_first_logins_never_create_three_active_devices(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier
        from django.db import close_old_connections

        user = get_user_model().objects.create_user(username="concurrent-device-user")
        barrier = Barrier(3)

        def login(index):
            close_old_connections()
            try:
                local_user = get_user_model().objects.get(pk=user.pk)
                barrier.wait(timeout=10)
                request = RequestFactory().post("/api/v1/auth/login/", HTTP_X_DEVICE_ID=(str(index) * 32))
                issue_user_session(local_user, request=request)
                return True
            finally:
                close_old_connections()

        with ThreadPoolExecutor(max_workers=3) as pool:
            outcomes = list(pool.map(login, range(3)))
        self.assertEqual(outcomes, [True, True, True])
        self.assertEqual(UserSession.objects.filter(user=user, revoked_at=None).count(), 2)
        self.assertEqual(UserSession.objects.filter(user=user, revoke_reason="session_limit_replaced").count(), 1)
