from datetime import timedelta
from urllib.parse import parse_qs, urlsplit

from django.contrib.auth import get_user_model
from django.core import mail
from django.core.cache import cache
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token


class AuthenticationSecurityTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="learner",
            email="learner@example.com",
            password="old-secure-password",
        )
        cache.clear()

    def tearDown(self):
        cache.clear()
        super().tearDown()

    @override_settings(
        EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        PASSWORD_RESET_FRONTEND_URL="https://frontend.example/reset",
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
    )
    def test_password_reset_confirmation_changes_password_invalidates_existing_tokens_and_single_uses_link(self):
        existing_token = Token.objects.create(user=self.user)
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
            "new_password": "new-secure-password",
            "new_password_confirm": "new-secure-password",
        }

        response = self.client.post(
            reverse("auth-password-reset-confirm"),
            payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Token.objects.filter(pk=existing_token.pk).exists())

        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("new-secure-password"))
        self.assertEqual(
            self.client.post(
                reverse("auth-login"),
                {"username": self.user.username, "password": "old-secure-password"},
                content_type="application/json",
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                reverse("auth-login"),
                {"username": self.user.username, "password": "new-secure-password"},
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
                "new_password": "new-secure-password",
                "new_password_confirm": "new-secure-password",
            },
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 400)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("old-secure-password"))

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

    @override_settings(AUTH_TOKEN_TTL_HOURS=1)
    def test_expired_token_is_rejected_and_removed(self):
        token = Token.objects.create(user=self.user)
        Token.objects.filter(pk=token.pk).update(created=timezone.now() - timedelta(hours=2))

        response = self.client.get(
            reverse("auth-me"),
            HTTP_AUTHORIZATION=f"Token {token.key}",
        )

        self.assertEqual(response.status_code, 401)
        self.assertFalse(Token.objects.filter(pk=token.pk).exists())
