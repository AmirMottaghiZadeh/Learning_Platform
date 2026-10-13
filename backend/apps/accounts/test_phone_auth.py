"""Sign-up by mobile number with an SMS code, choosing a password, signing
in with number + password, and resetting a forgotten password by SMS."""

import json
from datetime import timedelta
from unittest import mock

from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import sms
from .models import LearnerProfile, OneTimeCode, UserSession
from .phone import InvalidPhone, normalize_phone

PHONE = "09121234567"
PASSWORD = "Saffron-River-Atlas-2026!"


@override_settings(SMS_BACKEND="console", OTP_CODE_LENGTH=5, OTP_MAX_ATTEMPTS=5, OTP_RESEND_SECONDS=60)
class PhoneAuthTestCase(TestCase):
    def setUp(self):
        caches["throttle"].clear()
        sms.outbox.clear()

    def post(self, name, body, token=None):
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"} if token else {}
        return self.client.post(reverse(name), body, content_type="application/json", **headers)

    def request_code(self, purpose="signup", phone=PHONE):
        return self.post("auth-otp-request", {"phone": phone, "purpose": purpose})

    def last_code(self):
        return sms.outbox[-1].code

    def verify(self, code=None, purpose="signup", phone=PHONE):
        return self.post("auth-otp-verify", {"phone": phone, "purpose": purpose, "code": code or self.last_code()})

    def age_codes(self, seconds):
        OneTimeCode.objects.update(created_at=timezone.now() - timedelta(seconds=seconds))

    def sign_up(self):
        self.request_code()
        res = self.verify()
        token = res.data["access_token"]
        self.post("auth-password-set", {"new_password": PASSWORD, "new_password_confirm": PASSWORD}, token)
        return token


class NormalizePhoneTests(TestCase):
    def test_usual_spellings(self):
        for raw in ["09121234567", "9121234567", "+989121234567", "00989121234567", "989121234567",
                    "۰۹۱۲۱۲۳۴۵۶۷", "0912 123 4567", "0912-123-4567"]:
            self.assertEqual(normalize_phone(raw), PHONE, raw)

    def test_rejects_non_mobile_numbers(self):
        for raw in ["", "02112345678", "0912123456", "091212345678", "abc", "+1 555 1234"]:
            with self.assertRaises(InvalidPhone):
                normalize_phone(raw)


class SignUpTests(PhoneAuthTestCase):
    def test_full_sign_up_then_password_then_login(self):
        res = self.request_code()
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["code_length"], 5)
        self.assertEqual(len(sms.outbox), 1)
        self.assertEqual(sms.outbox[0].phone, PHONE)

        res = self.verify()
        self.assertEqual(res.status_code, 201)
        self.assertFalse(res.data["user"]["has_password"])
        self.assertEqual(res.data["user"]["phone"], PHONE)
        user = get_user_model().objects.get(learner_profile__phone=PHONE)
        self.assertFalse(user.has_usable_password())
        self.assertIsNotNone(user.learner_profile.phone_verified_at)

        # a first password needs no current one; the name comes with it
        token = res.data["access_token"]
        res = self.post(
            "auth-password-set",
            {"new_password": PASSWORD, "new_password_confirm": PASSWORD, "name": "Sara  Ahmadi"},
            token,
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["has_password"])
        self.assertEqual(res.data["profile"]["display_name"], "Sara Ahmadi")
        self.assertEqual((res.data["first_name"], res.data["last_name"]), ("Sara", "Ahmadi"))

        # from now on: number + password, any spelling of the number, no SMS
        for spelling in [PHONE, "+989121234567", "۰۹۱۲۱۲۳۴۵۶۷"]:
            res = self.post("auth-login", {"username": spelling, "password": PASSWORD})
            self.assertEqual(res.status_code, 200, spelling)
        self.assertEqual(len(sms.outbox), 1)

    def test_a_registered_number_is_sent_to_login(self):
        self.sign_up()
        res = self.request_code()
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.data["code"], "PHONE_REGISTERED")

    def test_an_unfinished_sign_up_can_get_a_new_code(self):
        self.request_code()
        self.verify()  # account made, password never chosen
        self.age_codes(120)
        self.assertEqual(self.request_code().status_code, 200)
        res = self.verify()
        self.assertEqual(res.status_code, 200)  # same account, not a new one
        self.assertEqual(get_user_model().objects.filter(learner_profile__phone=PHONE).count(), 1)

    def test_codes_are_stored_hashed(self):
        self.request_code()
        row = OneTimeCode.objects.get()
        self.assertNotIn(self.last_code(), row.code_hash)
        self.assertEqual(len(row.code_hash), 64)

    def test_email_sign_up_is_closed(self):
        res = self.post("auth-register", {
            "name": "X", "email": "x@example.com", "password": PASSWORD, "password_confirm": PASSWORD,
        })
        self.assertEqual(res.status_code, 403)
        self.assertEqual(res.data["code"], "EMAIL_REGISTRATION_CLOSED")


class CodeRuleTests(PhoneAuthTestCase):
    def test_resend_waits_for_the_gap(self):
        self.request_code()
        res = self.request_code()
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.data["code"], "OTP_TOO_SOON")
        self.assertGreater(res.data["details"]["retry_after"], 0)
        self.age_codes(61)
        self.assertEqual(self.request_code().status_code, 200)

    @override_settings(OTP_MAX_PER_PHONE_PER_DAY=2)
    def test_daily_cap(self):
        self.request_code()
        self.age_codes(61)
        self.request_code()
        self.age_codes(61)
        res = self.request_code()
        self.assertEqual(res.status_code, 429)
        self.assertEqual(res.data["code"], "OTP_DAILY_LIMIT")

    def test_wrong_codes_lock_the_code(self):
        self.request_code()
        right = self.last_code()
        wrong = "00000" if right != "00000" else "11111"
        for left in [4, 3, 2, 1, 0]:
            res = self.verify(wrong)
            self.assertEqual(res.data["code"], "OTP_INVALID")
            self.assertEqual(res.data["details"]["attempts_left"], left)
        res = self.verify(right)  # even the right one is dead now
        self.assertEqual(res.data["code"], "OTP_LOCKED")
        self.assertFalse(get_user_model().objects.filter(learner_profile__phone=PHONE).exists())

    def test_expired_code(self):
        self.request_code()
        OneTimeCode.objects.update(expires_at=timezone.now() - timedelta(seconds=1))
        self.assertEqual(self.verify().data["code"], "OTP_EXPIRED")

    def test_a_code_works_once(self):
        self.request_code()
        code = self.last_code()
        self.assertEqual(self.verify(code).status_code, 201)
        self.assertEqual(self.verify(code).data["code"], "OTP_EXPIRED")

    def test_only_the_newest_code_works(self):
        self.request_code()
        old = self.last_code()
        self.age_codes(61)
        self.request_code()
        new = self.last_code()
        if old != new:
            self.assertEqual(self.verify(old).data["code"], "OTP_INVALID")
        self.assertIn(self.verify(new).status_code, (200, 201))

    def test_codes_are_per_purpose(self):
        self.sign_up()
        self.request_code("reset")
        self.assertEqual(self.verify(purpose="signup").status_code, 400)

    def test_send_failure_frees_the_number(self):
        with mock.patch("apps.accounts.otp.send_code", side_effect=sms.SmsSendError("down")):
            res = self.request_code()
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data["code"], "SMS_SEND_FAILED")
        self.assertFalse(OneTimeCode.objects.exists())
        self.assertEqual(self.request_code().status_code, 200)  # no wait imposed

    def test_invalid_number(self):
        res = self.post("auth-otp-request", {"phone": "02112345678", "purpose": "signup"})
        self.assertEqual(res.status_code, 400)
        self.assertEqual(sms.outbox, [])


class ResetTests(PhoneAuthTestCase):
    def test_reset_an_unknown_number(self):
        res = self.request_code("reset")
        self.assertEqual(res.status_code, 404)
        self.assertEqual(res.data["code"], "PHONE_NOT_REGISTERED")

    def test_forgotten_password(self):
        old_token = self.sign_up()
        self.age_codes(120)
        self.assertEqual(self.request_code("reset").status_code, 200)
        res = self.verify(purpose="reset")
        self.assertEqual(res.status_code, 200)
        token = res.data["access_token"]

        new = "Cedar-Lantern-Orbit-2027!"
        res = self.post("auth-password-set", {"new_password": new, "new_password_confirm": new}, token)
        self.assertEqual(res.status_code, 200)
        # the other device is signed out, this one stays in
        self.assertEqual(self.client.get(reverse("auth-me"), HTTP_AUTHORIZATION=f"Bearer {old_token}").status_code, 401)
        self.assertEqual(self.client.get(reverse("auth-me"), HTTP_AUTHORIZATION=f"Bearer {token}").status_code, 200)
        self.assertEqual(self.post("auth-login", {"username": PHONE, "password": new}).status_code, 200)
        self.assertEqual(self.post("auth-login", {"username": PHONE, "password": PASSWORD}).status_code, 400)

    def test_changing_a_password_later_needs_the_current_one(self):
        self.sign_up()
        token = self.post("auth-login", {"username": PHONE, "password": PASSWORD}).data["access_token"]
        new = "Cedar-Lantern-Orbit-2027!"
        res = self.post("auth-password-set", {"new_password": new, "new_password_confirm": new}, token)
        self.assertEqual(res.data["code"], "INVALID_CURRENT_PASSWORD")
        res = self.post(
            "auth-password-set",
            {"new_password": new, "new_password_confirm": new, "current_password": PASSWORD},
            token,
        )
        self.assertEqual(res.status_code, 200)

    def test_weak_password_is_refused(self):
        self.request_code()
        token = self.verify().data["access_token"]
        for weak in ["Ab3x!", "987654321"]:  # too short; only digits
            res = self.post("auth-password-set", {"new_password": weak, "new_password_confirm": weak}, token)
            self.assertEqual(res.status_code, 400, weak)
        self.assertFalse(get_user_model().objects.get(learner_profile__phone=PHONE).has_usable_password())

    def test_a_six_character_password_is_enough(self):
        self.request_code()
        token = self.verify().data["access_token"]
        res = self.post("auth-password-set", {"new_password": "Kavir7", "new_password_confirm": "Kavir7"}, token)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.post("auth-login", {"username": PHONE, "password": "Kavir7"}).status_code, 200)


@override_settings(
    SMS_BACKEND="smsir", SMSIR_API_KEY="test-key", SMSIR_OTP_TEMPLATE_ID=123456, SMSIR_OTP_PARAMETER="CODE",
    SMSIR_VERIFY_URL="https://api.sms.ir/v1/send/verify",
)
class SmsIrBackendTests(TestCase):
    def response(self, payload):
        resp = mock.MagicMock()
        resp.read.return_value = json.dumps(payload).encode()
        resp.__enter__.return_value = resp
        return resp

    def test_sends_the_verify_request(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response(
            {"status": 1, "message": "موفق", "data": {"messageId": 987, "cost": 1.0}}
        )) as urlopen:
            message_id = sms.send_code(PHONE, "12345")
        self.assertEqual(message_id, "987")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.sms.ir/v1/send/verify")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("X-api-key"), "test-key")
        self.assertEqual(json.loads(request.data), {
            "mobile": PHONE, "templateId": 123456, "parameters": [{"name": "CODE", "value": "12345"}],
        })

    def test_a_refusal_raises(self):
        with mock.patch("urllib.request.urlopen", return_value=self.response({"status": 0, "message": "خطا"})):
            with self.assertRaises(sms.SmsSendError):
                sms.send_code(PHONE, "12345")

    @override_settings(SMSIR_OTP_TEMPLATE_ID=0)
    def test_missing_template_raises(self):
        with self.assertRaises(sms.SmsSendError):
            sms.send_code(PHONE, "12345")


class ProfileTests(PhoneAuthTestCase):
    def test_me_reports_phone_and_password_state(self):
        token = self.sign_up()
        me = self.client.get(reverse("auth-me"), HTTP_AUTHORIZATION=f"Bearer {token}").data
        self.assertEqual(me["phone"], PHONE)
        self.assertTrue(me["has_password"])
        self.assertEqual(UserSession.objects.filter(revoked_at__isnull=True).count(), 1)
        self.assertEqual(LearnerProfile.objects.get().phone, PHONE)
