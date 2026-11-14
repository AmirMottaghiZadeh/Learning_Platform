from django.contrib.auth import get_user_model
from django.core.cache import cache, caches
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from apps.accounts.models import OneTimeCode
from apps.billing.models import AdminAction

from . import ratelimit
from .models import RateLimitSettings

User = get_user_model()


class LimitsTestCase(TestCase):
    def setUp(self):
        cache.clear()
        caches["throttle"].clear()
        ratelimit.clear_cache()
        self.addCleanup(ratelimit.clear_cache)
        self.addCleanup(caches["throttle"].clear)
        self.user = User.objects.create_user(username="limits", email="limits@example.com", password="right-password-1")

    def set(self, **fields):
        row = RateLimitSettings.objects.first() or RateLimitSettings()
        for key, value in fields.items():
            setattr(row, key, value)
        row.save()
        return row

    def login(self):
        return self.client.post(
            reverse("auth-login"), {"username": "limits", "password": "wrong"}, content_type="application/json"
        ).status_code


class ThrottleSettingsTests(LimitsTestCase):
    def test_without_a_row_the_environment_rates_apply(self):
        limits = ratelimit.current()
        self.assertTrue(limits.enabled)
        self.assertEqual(limits.rates["auth_login"], "5/min")
        self.assertEqual(limits.modes["auth_login"], "default")
        self.assertIsNone(limits.rates["user"])  # no limit unless one is set
        self.assertEqual([self.login() for _ in range(6)][-1], 429)

    def test_a_custom_rate_replaces_the_default(self):
        self.set(rates={"auth_login": "2/minute"})
        self.assertEqual([self.login() for _ in range(3)], [400, 400, 429])

    def test_one_scope_can_have_no_limit(self):
        self.set(rates={"auth_login": "off"})
        self.assertNotIn(429, [self.login() for _ in range(8)])

    def test_the_switch_turns_every_limit_off(self):
        self.set(enabled=False, rates={"auth_login": "1/minute"})
        self.assertNotIn(429, [self.login() for _ in range(8)])
        self.set(enabled=True)
        self.assertEqual([self.login() for _ in range(2)], [400, 429])

    def test_a_limit_for_signed_in_users_counts_only_them(self):
        self.set(rates={"user": "2/minute"})
        api = APIClient()
        api.force_authenticate(self.user)
        codes = [api.get("/api/v1/billing/me/").status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])
        # an anonymous request is the "anon" scope's, not counted here
        from .throttling import DistributedUserRateThrottle
        from rest_framework.test import APIRequestFactory
        from django.contrib.auth.models import AnonymousUser
        request = APIRequestFactory().get("/")
        request.user = AnonymousUser()
        self.assertIsNone(DistributedUserRateThrottle().get_cache_key(request, None))

    def test_a_broken_rate_in_the_row_falls_back_to_the_default(self):
        self.set(rates={"auth_login": "lots"})
        self.assertEqual(ratelimit.current().rates["auth_login"], "5/min")


@override_settings(SMS_BACKEND="console", OTP_RESEND_SECONDS=60, OTP_MAX_PER_PHONE_PER_DAY=8)
class OtpSettingsTests(LimitsTestCase):
    PHONE = "09120000000"

    def ask(self):
        return self.client.post(
            reverse("auth-otp-request"), {"phone": self.PHONE, "purpose": "signup"}, content_type="application/json"
        )

    def test_the_resend_gap_can_be_changed(self):
        self.assertEqual(self.ask().status_code, 200)
        self.assertEqual(self.ask().json()["code"], "OTP_TOO_SOON")
        self.set(otp={"resend_seconds": 0})
        res = self.ask()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["resend_in"], 0)

    def test_the_sms_limits_can_be_switched_off(self):
        self.set(otp_enabled=False, rates={"auth_otp_request": "off"})
        codes = [self.ask().status_code for _ in range(10)]
        self.assertEqual(codes, [200] * 10)
        self.assertEqual(OneTimeCode.objects.filter(phone=self.PHONE).count(), 10)


class RateLimitConsoleTests(LimitsTestCase):
    def setUp(self):
        super().setUp()
        self.admin = User.objects.create_superuser("boss", "boss@example.com", "boss-password-1")
        self.client.force_login(self.admin)
        self.url = reverse("console:rate_limits")

    def form(self, **extra):
        data = {"enabled": "on", "otp_enabled": "on", "password": "boss-password-1"}
        for scope in ratelimit.SCOPE_KEYS:
            data[f"mode_{scope}"] = "default"
        data.update(extra)
        return data

    def test_the_page_lists_every_scope_and_sms_limit(self):
        page = self.client.get(self.url)
        self.assertEqual(page.status_code, 200)
        for scope, label, _ in ratelimit.SCOPES:
            self.assertContains(page, f'name="mode_{scope}"')
            self.assertContains(page, label)
        for key, *_ in ratelimit.OTP_FIELDS:
            self.assertContains(page, f'name="otp_{key}"')

    def test_saving_sets_rates_switches_and_sms_limits_and_is_logged(self):
        res = self.client.post(self.url, self.form(**{
            "mode_auth_login": "custom", "count_auth_login": "۱۰", "unit_auth_login": "hour",
            "mode_guest_session": "off", "otp_enabled": "off", "otp_resend_seconds": "30",
        }), follow=True)
        self.assertContains(res, "ذخیره شد")
        row = RateLimitSettings.objects.get()
        self.assertEqual(row.rates, {"auth_login": "10/hour", "guest_session": "off"})
        self.assertTrue(row.enabled)
        self.assertFalse(row.otp_enabled)
        self.assertEqual(row.otp, {"resend_seconds": 30})
        limits = ratelimit.current()
        self.assertEqual(limits.rates["auth_login"], "10/hour")
        self.assertIsNone(limits.rates["guest_session"])
        self.assertEqual(AdminAction.objects.filter(action="rate_limits").count(), 1)

    def test_switching_everything_off(self):
        self.client.post(self.url, self.form(enabled="off"))
        self.assertFalse(ratelimit.current().enabled)
        self.assertIsNone(ratelimit.rate_for("auth_login"))

    def test_wrong_password_or_bad_numbers_change_nothing(self):
        res = self.client.post(self.url, self.form(password="nope", enabled="off"), follow=True)
        self.assertContains(res, "رمز حساب درست نیست")
        res = self.client.post(self.url, self.form(**{"mode_auth_login": "custom", "count_auth_login": "0"}), follow=True)
        self.assertContains(res, "ورود با رمز")
        res = self.client.post(self.url, self.form(otp_window_seconds="5"), follow=True)
        self.assertContains(res, "باید عددی بین")
        self.assertFalse(RateLimitSettings.objects.exists())

    def test_staff_without_platform_admin_role_is_denied(self):
        staff = User.objects.create_user("staff", "staff@example.com", "pw", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(self.url).status_code, 403)
