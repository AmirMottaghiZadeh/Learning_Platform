import json
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.calculators.models import Calculator


def _write_source(directory, records):
    path = Path(directory) / "calculators.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return str(path)


def _calculator_record(**overrides):
    record = {
        "calculator_id": "1",
        "name": "Test Score",
        "description": "A test calculator.",
        "about": "<p>About it.</p>",
        "author": "Dr Test",
        "categories": [{"id": 1, "name": "Cardiology"}],
        "tags": [{"id": 1, "name": "risk"}],
        "questions": [
            {
                "position": 0,
                "title": "Age?",
                "type": "numeric_input",
                "more_information": None,
                "initial_value": None,
                "choices": [],
                "units": [{"title": "Years", "min_value": "0", "max_value": "120",
                           "min_value_msg": None, "max_value_msg": None,
                           "unit_factor": "1", "initial_value": None}],
            },
        ],
        "results": [
            {
                "position": 0,
                "title": "Score",
                "formula": "(function() { return $0; })();",
                "condition_formula": None,
                "answer": "$result0",
                "type": "default",
            },
        ],
        "references": [{"names": "Someone et al.", "sources": "A journal.", "papers": "<a>link</a>"}],
    }
    record.update(overrides)
    return record


class ImportMedscapeCalculatorsTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_import_creates_a_calculator_with_cleaned_fields(self):
        source = _write_source(self._tmp.name, [_calculator_record()])
        call_command("import_medscape_calculators", source=source)

        self.assertEqual(Calculator.objects.count(), 1)
        calc = Calculator.objects.get(calculator_id="1")
        self.assertEqual(calc.slug, "test-score-1")
        self.assertEqual(calc.categories, ["Cardiology"])
        self.assertEqual(calc.tags, ["risk"])
        self.assertEqual(len(calc.questions), 1)
        self.assertEqual(calc.questions[0]["type"], "numeric_input")
        self.assertEqual(len(calc.results), 1)
        self.assertIn("return $0", calc.results[0]["formula"])

    def test_reimport_is_idempotent(self):
        source = _write_source(self._tmp.name, [_calculator_record()])
        call_command("import_medscape_calculators", source=source)
        call_command("import_medscape_calculators", source=source)

        self.assertEqual(Calculator.objects.count(), 1)

    def test_rerun_updates_changed_fields(self):
        source = _write_source(self._tmp.name, [_calculator_record()])
        call_command("import_medscape_calculators", source=source)

        source = _write_source(self._tmp.name, [_calculator_record(description="Updated.")])
        call_command("import_medscape_calculators", source=source)

        self.assertEqual(Calculator.objects.get(calculator_id="1").description, "Updated.")

    def test_record_missing_name_or_id_is_skipped(self):
        source = _write_source(self._tmp.name, [
            _calculator_record(calculator_id=""),
            _calculator_record(calculator_id="2", name=""),
        ])
        call_command("import_medscape_calculators", source=source)

        self.assertEqual(Calculator.objects.count(), 0)

    def test_dry_run_writes_nothing(self):
        source = _write_source(self._tmp.name, [_calculator_record()])
        call_command("import_medscape_calculators", source=source, dry_run=True)

        self.assertEqual(Calculator.objects.count(), 0)

    def test_questions_and_results_are_sorted_by_position(self):
        record = _calculator_record()
        record["questions"] = [
            {**record["questions"][0], "position": 1, "title": "Second"},
            {**record["questions"][0], "position": 0, "title": "First"},
        ]
        source = _write_source(self._tmp.name, [record])
        call_command("import_medscape_calculators", source=source)

        calc = Calculator.objects.get(calculator_id="1")
        self.assertEqual([q["title"] for q in calc.questions], ["First", "Second"])


class CalculatorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(
            username="reader", email="reader@example.com", password="x"
        ))
        Calculator.objects.create(
            calculator_id="1", slug="test-score-1", name="Test Score",
            description="A test calculator.", categories=["Cardiology"],
            questions=[{"position": 0, "title": "Age?", "type": "numeric_input"}],
            results=[{"position": 0, "title": "Score", "formula": "(function(){return $0;})();"}],
        )
        Calculator.objects.create(
            calculator_id="2", slug="other-tool-2", name="Other Tool",
            description="Unrelated.", categories=["Nephrology"],
        )

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get("/api/v1/calculators/").status_code, 401)

    def test_list_and_search(self):
        res = self.client.get("/api/v1/calculators/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["count"], 2)

        res = self.client.get("/api/v1/calculators/", {"search": "test score"})
        self.assertEqual(res.data["count"], 1)
        self.assertEqual(res.data["results"][0]["slug"], "test-score-1")

        res = self.client.get("/api/v1/calculators/", {"search": "Cardiology"})
        self.assertEqual(res.data["count"], 1)

    def test_detail_includes_questions_and_results(self):
        res = self.client.get("/api/v1/calculators/test-score-1/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["name"], "Test Score")
        self.assertEqual(len(res.data["questions"]), 1)
        self.assertEqual(len(res.data["results"]), 1)

    def test_list_excludes_questions_and_results(self):
        res = self.client.get("/api/v1/calculators/")
        self.assertNotIn("questions", res.data["results"][0])
