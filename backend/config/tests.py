import os
import subprocess
import sys

from django.conf import settings
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


class ProductionSearchSettingsTests(SimpleTestCase):
    def test_production_module_rejects_local_search_pilot_even_with_local_environment_label(self):
        script = (
            "from django.core.exceptions import ImproperlyConfigured\n"
            "try:\n import config.settings.production\n"
            "except ImproperlyConfigured as error:\n print(str(error))\n raise SystemExit(2)\n"
        )
        result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, timeout=20,
            env={**os.environ, "ENVIRONMENT": "local", "AI_LAB_LOCAL_LEXICAL_PILOT": "True"})
        self.assertEqual(result.returncode, 2)
        self.assertIn("Lexical pilot mode cannot run with production settings.", result.stdout)


class CorsPreflightTests(SimpleTestCase):
    endpoints = (
        "/api/v1/auth/login/",
        "/api/v1/auth/onboarding/",
    )

    def test_idempotent_mutations_allow_browser_preflight(self):
        # Test exactly the origins the deployment allows, so this can't drift
        # from CORS_ALLOWED_ORIGINS again.
        origins = list(settings.CORS_ALLOWED_ORIGINS)
        if not origins:
            self.skipTest("CORS_ALLOWED_ORIGINS is empty in this environment.")

        client = Client()

        for endpoint in self.endpoints:
            for origin in origins:
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
