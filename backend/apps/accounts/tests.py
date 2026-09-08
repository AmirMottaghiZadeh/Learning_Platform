from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache, caches
from django.test import TestCase, override_settings
from django.urls import reverse

from .services import issue_user_session


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="learner",
            email="learner@example.com",
            password="Old-Secure-Password-2026!",
        )
        cache.clear()
        caches["throttle"].clear()

    def tearDown(self):
        cache.clear()
        caches["throttle"].clear()
        super().tearDown()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        PASSWORD_RESET_FRONTEND_URL="https://frontend.example/reset",
        # Delivery itself is queued; run it in-process so this test can assert
        # on the message contents rather than on the transport.
        CELERY_TASK_ALWAYS_EAGER=True,
    )
    def test_password_reset_request_sends_a_signed_link_without_disclosing_account_existence(self):
        known_response = self.client.post(
            reverse("auth-password-reset"),
            {"email": self.user.email},
            content_type="application/json",
        )
        unknown_response = self.client.post(
            reverse("auth-password-reset"),
            {"email": "unknown@example.com"},
            content_type="application/json",
        )

        self.assertEqual(known_response.status_code, 200)
        self.assertEqual(known_response.json(), unknown_response.json())
        self.assertEqual(len(mail.outbox), 1)
        reset_url = next(
            line
            for line in mail.outbox[0].body.splitlines()
            if line.startswith("https://frontend.example/reset?")
        )
        params = parse_qs(urlsplit(reset_url).query)
        self.assertIn("reset_uid", params)
        self.assertIn("reset_token", params)

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        PASSWORD_RESET_FRONTEND_URL="https://frontend.example/reset",
        # Delivery itself is queued; run it in-process so this test can assert
        # on the message contents rather than on the transport.
        CELERY_TASK_ALWAYS_EAGER=True,
    )
    def test_password_reset_confirmation_changes_password_invalidates_existing_tokens_and_single_uses_link(self):
        existing_session = issue_user_session(self.user).session
        response = self.client.post(
            reverse("auth-password-reset"),
            {"email": self.user.email},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        reset_url = next(
            line
            for line in mail.outbox[0].body.splitlines()
            if line.startswith("https://frontend.example/reset?")
        )
        params = parse_qs(urlsplit(reset_url).query)
        payload = {
            "uid": params["reset_uid"][0],
            "token": params["reset_token"][0],
            "new_password": "New-Secure-Password-2026!",
            "new_password_confirm": "New-Secure-Password-2026!",
        }

        response = self.client.post(
            reverse("auth-password-reset-confirm"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        existing_session.refresh_from_db()
        self.assertIsNotNone(existing_session.revoked_at)
        self.assertEqual(existing_session.revoke_reason, "password_reset")

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("New-Secure-Password-2026!"))
        self.assertEqual(
            self.client.post(
                reverse("auth-login"),
                {"username": self.user.username, "password": "Old-Secure-Password-2026!"},
                content_type="application/json",
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                reverse("auth-login"),
                {"username": self.user.username, "password": "New-Secure-Password-2026!"},
                content_type="application/json",
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.post(
                reverse("auth-password-reset-confirm"),
                payload,
                content_type="application/json",
            ).status_code,
            400,
        )

    def test_invalid_password_reset_link_is_rejected(self):
        response = self.client.post(
            reverse("auth-password-reset-confirm"),
            {
                "uid": "invalid",
                "token": "invalid",
                "new_password": "New-Secure-Password-2026!",
                "new_password_confirm": "New-Secure-Password-2026!",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Old-Secure-Password-2026!"))

    def test_registration_rejects_common_numeric_password(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "name": "New Learner",
                "email": "new-learner@example.com",
                "password": "123456789012",
                "password_confirm": "123456789012",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(
            get_user_model().objects.filter(email__iexact="new-learner@example.com").exists()
        )

    def test_registration_accepts_password_that_passes_django_validators(self):
        response = self.client.post(
            reverse("auth-register"),
            {
                "name": "Secure Learner",
                "email": "secure-learner@example.com",
                "password": "Saffron-River-Atlas-2026!",
                "password_confirm": "Saffron-River-Atlas-2026!",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 201)
        self.assertTrue(
            get_user_model().objects.filter(email__iexact="secure-learner@example.com").exists()
        )

    def test_login_is_rate_limited_by_auth_scope(self):
        payload = {"username": self.user.username, "password": "wrong-password"}
        for _ in range(5):
            self.assertEqual(
                self.client.post(
                    reverse("auth-login"),
                    payload,
                    content_type="application/json",
                ).status_code,
                400,
            )
        response = self.client.post(
            reverse("auth-login"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 429)

    def test_legacy_drf_token_is_not_accepted(self):
        from rest_framework.authtoken.models import Token

        token = Token.objects.create(user=self.user)

        response = self.client.get(
            reverse("auth-me"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        self.assertEqual(response.status_code, 401)
        self.assertTrue(Token.objects.filter(pk=token.pk).exists())


class OnboardingTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="learner", email="learner@example.com", password="x",
            first_name="Sara", last_name="Karimi",
        )
        self.auth = {"HTTP_AUTHORIZATION": f"Bearer {issue_user_session(self.user).access_token}"}

    def test_me_returns_a_profile_block_created_on_first_read(self):
        response = self.client.get(reverse("auth-me"), **self.auth)

        self.assertEqual(response.status_code, 200)
        profile = response.json()["profile"]
        self.assertEqual(profile["display_name"], "Sara Karimi")
        self.assertFalse(profile["is_onboarded"])
        self.assertIsNone(profile["onboarded_at"])

    def test_onboarding_sets_fields_and_marks_onboarded(self):
        response = self.client.post(
            reverse("auth-onboarding"),
            {"study_field": "pharmacy", "study_goal": "residency", "study_level": "advanced"},
            content_type="application/json",
            **self.auth,
        )

        self.assertEqual(response.status_code, 200)
        profile = response.json()["profile"]
        self.assertEqual(profile["study_field"], "pharmacy")
        self.assertEqual(profile["study_goal"], "residency")
        self.assertEqual(profile["study_level"], "advanced")
        self.assertTrue(profile["is_onboarded"])

    def test_onboarding_rejects_unknown_choice(self):
        response = self.client.post(
            reverse("auth-onboarding"),
            {"study_field": "astrology", "study_goal": "residency", "study_level": "advanced"},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 400)

    def test_patch_me_updates_display_name_without_re_onboarding(self):
        self.client.post(
            reverse("auth-onboarding"),
            {"study_field": "medicine", "study_goal": "final", "study_level": "beginner"},
            content_type="application/json",
            **self.auth,
        )
        response = self.client.patch(
            reverse("auth-me"),
            {"display_name": "Dr. Karimi"},
            content_type="application/json",
            **self.auth,
        )
        self.assertEqual(response.status_code, 200)
        profile = response.json()["profile"]
        self.assertEqual(profile["display_name"], "Dr. Karimi")
        self.assertEqual(profile["study_field"], "medicine")
        self.assertTrue(profile["is_onboarded"])

    def test_onboarding_requires_authentication(self):
        response = self.client.post(
            reverse("auth-onboarding"),
            {"study_field": "nursing", "study_goal": "clinical", "study_level": "beginner"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 401)
