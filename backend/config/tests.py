from django.core.exceptions import ImproperlyConfigured
from django.test import Client, SimpleTestCase

from config.security import validate_production_secret_key


class ProductionSecretKeyTests(SimpleTestCase):
    def test_rejects_short_or_placeholder_secrets(self):
        weak_values = [
            "",
            "x",
            "12345678",
            "short-secret",
            "docker-local-secret-change-before-production",
        ]

        for value in weak_values:
            with self.subTest(value=value):
                with self.assertRaises(ImproperlyConfigured):
                    validate_production_secret_key(value)

    def test_accepts_long_diverse_secret(self):
        secret = "Prod-2026!Saffron_River+Atlas#Quartz$Nimbus%Orbit&Harbor"

        self.assertEqual(validate_production_secret_key(secret), secret)


class CorsPreflightTests(SimpleTestCase):
    endpoints = (
        "/api/v1/quiz/start/",
        "/api/v1/flashcards/seed/",
    )
    origins = (
        "http://localhost:8081",
        "http://127.0.0.1:8081",
    )

    def test_idempotent_mutations_allow_browser_preflight(self):
        client = Client()

        for endpoint in self.endpoints:
            for origin in self.origins:
                with self.subTest(endpoint=endpoint, origin=origin):
                    response = client.options(
                        endpoint,
                        HTTP_ORIGIN=origin,
                        HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
                        HTTP_ACCESS_CONTROL_REQUEST_HEADERS=(
                            "authorization,content-type,idempotency-key"
                        ),
                    )

                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(
                        response["Access-Control-Allow-Origin"],
                        origin,
                    )
                    allowed_headers = {
                        header.strip().lower()
                        for header in response[
                            "Access-Control-Allow-Headers"
                        ].split(",")
                    }
                    self.assertIn("authorization", allowed_headers)
                    self.assertIn("content-type", allowed_headers)
                    self.assertIn("idempotency-key", allowed_headers)
