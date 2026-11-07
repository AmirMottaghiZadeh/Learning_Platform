from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import UserSession

from . import config
from .models import AdminAction, BillingSettings, GuestAccount, Plan, PlanPrice

User = get_user_model()


class GuestAccessTests(TestCase):
    def setUp(self):
        config.clear_cache()
        self.api = APIClient()

    def tearDown(self):
        config.clear_cache()

    def switch(self, on):
        row = BillingSettings.objects.first() or BillingSettings()
        row.guest_access_enabled = on
        row.save()

    def test_off_by_default(self):
        self.assertEqual(self.api.get("/api/v1/guest/status/").json(), {"enabled": False})
        res = self.api.post("/api/v1/guest/session/")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "GUEST_ACCESS_DISABLED")
        self.assertFalse(GuestAccount.objects.exists())

    def test_guest_gets_an_onboarded_account_that_opens_the_app(self):
        self.switch(True)
        self.assertTrue(self.api.get("/api/v1/guest/status/").json()["enabled"])
        res = self.api.post("/api/v1/guest/session/")
        self.assertEqual(res.status_code, 201)
        body = res.json()
        self.assertTrue(body["user"]["is_guest"])
        self.assertFalse(body["user"]["has_password"])
        self.assertTrue(body["user"]["profile"]["is_onboarded"])

        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {body['access_token']}")
        self.assertEqual(self.api.get("/api/v1/me/dashboard/").status_code, 200)
        # Each visitor gets an account of their own.
        self.assertEqual(APIClient().post("/api/v1/guest/session/").json()["user"]["is_guest"], True)
        self.assertEqual(GuestAccount.objects.count(), 2)

    def test_guests_cannot_buy(self):
        self.switch(True)
        token = self.api.post("/api/v1/guest/session/").json()["access_token"]
        plan = Plan.objects.create(slug="p", name_fa="p")
        price = PlanPrice.objects.create(plan=plan, duration_days=30, price_toman=1000)
        self.api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        res = self.api.post("/api/v1/billing/checkout/", {"price_id": price.pk}, format="json")
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.json()["code"], "GUEST_CANNOT_BUY")

    def test_real_users_are_not_guests(self):
        user = User.objects.create_user(username="real", password="x")
        self.api.force_authenticate(user)
        self.assertFalse(self.api.get("/api/v1/auth/me/").json()["is_guest"])


class GuestConsoleTests(TestCase):
    def setUp(self):
        config.clear_cache()
        self.admin = User.objects.create_superuser(username="root", email="r@example.com", password="pw-123456")
        self.client.force_login(self.admin)

    def tearDown(self):
        config.clear_cache()

    def test_switch_needs_the_password_and_switching_off_ends_guest_sessions(self):
        res = self.client.post(reverse("console:access"), {"guest_access": "on", "password": "wrong"}, follow=True)
        self.assertContains(res, "رمز حساب درست نیست")
        self.assertFalse(config.current().guest_access)

        res = self.client.post(reverse("console:access"), {"guest_access": "on", "password": "pw-123456"}, follow=True)
        self.assertTrue(config.current().guest_access)
        self.assertContains(res, "ورود بدون نام کاربری و رمز روشن است")  # the banner

        api = APIClient()
        token = api.post("/api/v1/guest/session/").json()["access_token"]
        self.assertContains(self.client.get(reverse("console:access")), "نشست‌های مهمانِ باز")
        # Guests stay out of the users list.
        self.assertNotContains(self.client.get(reverse("console:users")), "guest-")

        self.client.post(reverse("console:access"), {"guest_access": "off", "password": "pw-123456"})
        self.assertFalse(config.current().guest_access)
        self.assertFalse(UserSession.objects.filter(user__guest_account__isnull=False, revoked_at__isnull=True).exists())
        api.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        self.assertEqual(api.get("/api/v1/auth/me/").status_code, 401)
        self.assertEqual(AdminAction.objects.filter(action="guest_access").count(), 2)

        self.client.post(reverse("console:access"), {"op": "delete_guests"})
        self.assertFalse(GuestAccount.objects.exists())
        self.assertFalse(User.objects.filter(username__startswith="guest-").exists())

    def test_guests_are_not_deleted_while_access_is_on(self):
        BillingSettings.objects.create(guest_access_enabled=True)
        APIClient().post("/api/v1/guest/session/")
        self.client.post(reverse("console:access"), {"op": "delete_guests"})
        self.assertEqual(GuestAccount.objects.count(), 1)
        with self.assertRaises(CommandError):
            call_command("delete_guest_accounts")
