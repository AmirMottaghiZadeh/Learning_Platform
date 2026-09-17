from io import StringIO
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import override_settings
from django.test import Client, SimpleTestCase, TestCase

from apps.core.events import LearningEvent, NullLearningEventPublisher, build_learning_event


class LearningEventTests(SimpleTestCase):
    def test_build_learning_event_creates_platform_envelope(self):
        event = build_learning_event(
            event_type="QuestionAnswered",
            learner_id=10,
            payload={"question_id": 20},
        )

        self.assertEqual(event.event_type, "QuestionAnswered")
        self.assertEqual(event.learner_id, 10)
        self.assertEqual(event.product_id, "pharmexa")
        self.assertEqual(event.payload, {"question_id": 20})
        self.assertTrue(event.correlation_id)

    def test_learning_event_requires_event_type(self):
        with self.assertRaises(ValueError):
            LearningEvent(event_type="", learner_id=1, product_id="pharmexa")

    def test_null_publisher_matches_event_publisher_contract(self):
        event = build_learning_event(event_type="HealthChecked", learner_id=None)

        self.assertIsNone(NullLearningEventPublisher().publish(event))


class HealthCheckTests(TestCase):
    def test_health_check_returns_release_metadata_and_database_status(self):
        response = Client().get("/api/v1/health/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")
        self.assertEqual(response.json()["checks"]["database"], "ok")
        self.assertIn("database_latency_ms", response.json()["checks"])
        self.assertIn("X-Request-ID", response)

    def test_liveness_check_does_not_require_database_probe(self):
        response = Client().get("/api/v1/live/", HTTP_X_REQUEST_ID="test-request-id")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["checks"]["database"], "not_checked")
        self.assertEqual(response["X-Request-ID"], "test-request-id")

    def test_production_settings_restrict_rendering_to_json(self):
        """A browser's Accept header must never be able to reach
        BrowsableAPIRenderer in production: that HTML page needs DRF's own
        static assets, which CompressedManifestStaticFilesStorage doesn't
        reliably have in its hashed manifest, and rendering it 500s with
        "Missing staticfiles manifest entry" -- a real production incident
        this guards against.

        This can't be exercised end-to-end from a test running under local
        settings: DRF resolves a view's `renderer_classes` from
        DEFAULT_RENDERER_CLASSES once, as a class attribute, when the view
        module is first imported -- so overriding the REST_FRAMEWORK setting
        afterwards (override_settings) has no effect on an already-loaded
        view. Asserting against production.py's own source is what's left
        that actually verifies the fix without loading two conflicting
        settings modules (with their own validators) into one process.
        """
        source = Path(settings.BASE_DIR, "config", "settings", "production.py").read_text()
        self.assertIn(
            'REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ["rest_framework.renderers.JSONRenderer"]',
            source,
        )

    def test_backup_command_supports_dry_run(self):
        output = StringIO()

        with override_settings(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": "pharmexa",
                    "USER": "postgres",
                    "PASSWORD": "postgres",
                    "HOST": "127.0.0.1",
                    "PORT": "5432",
                    "CONN_HEALTH_CHECKS": True,
                }
            },
            DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/pharmexa",
        ):
            call_command("backup_database", "--dry-run", stdout=output)

        self.assertIn(".dump", output.getvalue())


class OpenAPISchemaTests(TestCase):
    def test_versioned_schema_includes_platform_api_paths(self):
        response = Client().get("/api/v1/schema/?format=json")

        self.assertEqual(response.status_code, 200)
        paths = response.json()["paths"]
        expected_paths = {
            "/api/v1/health/",
            "/api/v1/live/",
            "/api/v1/ready/",
            "/api/v1/auth/login/",
            "/api/v1/auth/register/",
            "/api/v1/auth/me/",
        }

        self.assertTrue(expected_paths.issubset(paths.keys()))
        self.assertGreater(len(paths), len(expected_paths))
