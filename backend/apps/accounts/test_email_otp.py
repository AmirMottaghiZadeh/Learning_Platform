from datetime import timedelta
import re
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient
from . import email_otp
from .models import EmailLoginIdentity, EmailOneTimeCode
from .otp import OtpError


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",AUTH_EMAIL_OTP_ENABLED=True,
    CACHES={key:{"BACKEND":"django.core.cache.backends.locmem.LocMemCache","LOCATION":"email-tests-"+key} for key in ["default","throttle","ai_lab"]})
class EmailOtpTests(TestCase):
    def setUp(self):
        from django.core.cache import caches
        for name in ["default","throttle","ai_lab"]:caches[name].clear()
        self.api=APIClient()

    def send(self,email="person@example.com"):
        row=email_otp.request_code(email)
        code=re.search(r"\b\d{6}\b",mail.outbox[-1].body).group()
        return row,code

    def test_only_hmac_is_stored_and_email_is_normalized(self):
        row,code=self.send("Person@Example.com")
        self.assertEqual(row.identity_id,"person@example.com")
        self.assertNotIn(code,row.code_hash)
        self.assertEqual(len(row.code_hash),64)

    def test_verified_email_creates_a_single_learner_account(self):
        _,code=self.send()
        user,created=email_otp.verify_code("PERSON@example.com",code)
        self.assertTrue(created);self.assertEqual(user.email,"person@example.com")
        self.assertFalse(user.has_usable_password())
        self.assertTrue(EmailLoginIdentity.objects.get(pk=user.email).verified_at)
        with self.assertRaises(OtpError):email_otp.verify_code(user.email,code)

    def test_existing_email_signs_in_to_the_same_account(self):
        existing=get_user_model().objects.create_user("email-owner",email="Person@example.com",password="test-password")
        _,code=self.send();user,created=email_otp.verify_code("person@example.com",code)
        self.assertFalse(created);self.assertEqual(user.pk,existing.pk)

    def test_wrong_attempts_persist_and_eventually_lock(self):
        row,code=self.send();wrong="000000" if code!="000000" else "111111"
        for _ in range(5):
            with self.assertRaises(OtpError):email_otp.verify_code(row.identity_id,wrong)
        row.refresh_from_db();self.assertEqual(row.attempts,5)
        with self.assertRaisesMessage(OtpError,"تعداد تلاش‌ها"):email_otp.verify_code(row.identity_id,code)

    def test_expired_code_never_authenticates(self):
        row,code=self.send();row.expires_at=timezone.now()-timedelta(seconds=1);row.save()
        with self.assertRaises(OtpError):email_otp.verify_code(row.identity_id,code)
        self.assertFalse(get_user_model().objects.filter(email=row.identity_id).exists())

    def test_resend_cooldown_and_latest_code_only(self):
        row,first=self.send()
        with self.assertRaises(OtpError):self.send()
        EmailOneTimeCode.objects.filter(pk=row.pk).update(created_at=timezone.now()-timedelta(minutes=2))
        _,second=self.send()
        row.refresh_from_db();self.assertIsNotNone(row.consumed_at)
        self.assertTrue(EmailOneTimeCode.objects.filter(consumed_at__isnull=True).count()==1)

    def test_delivery_failure_keeps_no_usable_unsent_code(self):
        with patch("apps.accounts.email_otp.EmailMultiAlternatives.send",side_effect=OSError("private SMTP failure")):
            with self.assertRaises(OtpError):self.send()
        self.assertFalse(EmailOneTimeCode.objects.exists())

    @override_settings(EMAIL_BACKEND="django.core.mail.backends.console.EmailBackend")
    def test_console_backend_cannot_print_a_login_code(self):
        with patch("apps.accounts.email_otp.EmailMultiAlternatives.send") as send:
            with self.assertRaises(OtpError):email_otp.request_code("person@example.com")
        send.assert_not_called()

    def test_disabled_account_cannot_sign_in_with_a_valid_email_code(self):
        get_user_model().objects.create_user("one",email="person@example.com",is_active=False)
        _,code=self.send()
        with self.assertRaises(OtpError):email_otp.verify_code("person@example.com",code)

    @override_settings(AUTH_EMAIL_OTP_ENABLED=False)
    def test_feature_can_be_disabled(self):
        with self.assertRaises(OtpError):email_otp.request_code("person@example.com")

    def test_api_returns_a_private_session_only_after_correct_code(self):
        response=self.api.post(reverse("auth-email-otp-request"),{"email":"person@example.com"},format="json")
        self.assertEqual(response.status_code,200);self.assertNotIn("code",response.data)
        code=re.search(r"\b\d{6}\b",mail.outbox[-1].body).group()
        response=self.api.post(reverse("auth-email-otp-verify"),{"email":"person@example.com","code":code},format="json")
        self.assertEqual(response.status_code,201);self.assertTrue(response.data["access_token"])
        self.assertEqual(response["Cache-Control"],"no-store")
        self.api.credentials(HTTP_AUTHORIZATION="Bearer "+response.data["access_token"])
        self.assertEqual(self.api.get(reverse("auth-me")).status_code,200)
