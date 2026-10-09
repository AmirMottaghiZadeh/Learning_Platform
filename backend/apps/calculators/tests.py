import sqlite3
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.calculators.models import Calculator, CalculatorCategory, CalculatorTag

SCHEMA = """
CREATE TABLE calculator (
    id INTEGER PRIMARY KEY, uid TEXT UNIQUE NOT NULL, calculator_id TEXT NOT NULL, url TEXT,
    name TEXT, name_fa TEXT, description TEXT, description_fa TEXT,
    about TEXT, about_fa TEXT, disclaimer_footer TEXT, disclaimer_footer_fa TEXT,
    translated INTEGER NOT NULL, data TEXT NOT NULL, data_fa TEXT, formula_strings_fa TEXT
);
CREATE TABLE category (id INTEGER PRIMARY KEY, external_id INTEGER UNIQUE, name TEXT, name_fa TEXT,
                       parent_id INTEGER REFERENCES category(id), is_main_category INTEGER);
CREATE TABLE tag (id INTEGER PRIMARY KEY, external_id INTEGER UNIQUE, name TEXT, name_fa TEXT);
CREATE TABLE calculator_category (calculator_id INTEGER, category_id INTEGER,
                                  PRIMARY KEY (calculator_id, category_id));
CREATE TABLE calculator_tag (calculator_id INTEGER, tag_id INTEGER,
                             PRIMARY KEY (calculator_id, tag_id));
CREATE TABLE question (
    id INTEGER PRIMARY KEY, calculator_id INTEGER NOT NULL, external_id INTEGER, position INTEGER,
    type TEXT, title TEXT, title_fa TEXT, more_information TEXT, more_information_fa TEXT,
    section_name TEXT, section_name_fa TEXT, initial_value TEXT, allow_negative_answer INTEGER, linked_items TEXT
);
CREATE TABLE choice (
    id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL, external_id INTEGER, position INTEGER,
    title_primary TEXT, title_primary_fa TEXT, title_secondary TEXT, title_secondary_fa TEXT,
    error_message TEXT, error_message_fa TEXT, warning_message TEXT, warning_message_fa TEXT,
    success_message TEXT, success_message_fa TEXT, answer_factor TEXT, unit_independent INTEGER
);
CREATE TABLE question_unit (
    id INTEGER PRIMARY KEY, question_id INTEGER NOT NULL, external_id INTEGER, position INTEGER,
    type TEXT, title TEXT, title_fa TEXT, unit_factor TEXT, initial_value TEXT, min_value TEXT, max_value TEXT,
    min_value_msg TEXT, min_value_msg_fa TEXT, max_value_msg TEXT, max_value_msg_fa TEXT
);
CREATE TABLE result (
    id INTEGER PRIMARY KEY, calculator_id INTEGER NOT NULL, external_id INTEGER, position INTEGER,
    type TEXT, title TEXT, title_fa TEXT, sub_title TEXT, sub_title_fa TEXT, answer TEXT, answer_fa TEXT,
    formula TEXT, condition_formula TEXT, title_formula TEXT, sub_title_formula TEXT
);
CREATE TABLE error_check (
    id INTEGER PRIMARY KEY, calculator_id INTEGER NOT NULL, external_id INTEGER, position INTEGER,
    type TEXT, title TEXT, title_fa TEXT, answer TEXT, answer_fa TEXT, formula TEXT
);
CREATE TABLE reference (id INTEGER PRIMARY KEY, calculator_id INTEGER NOT NULL, position INTEGER,
                        names TEXT, papers TEXT, sources TEXT);
"""


def _build_sqlite(directory, calculators=None):
    """A minimal SQLite fixture matching the real import source's schema.
    `calculators` is a list of (calculator_row_overrides, questions, results)
    tuples; one category and one tag are always seeded and linked to every
    calculator so the M2M import path is exercised by default."""
    path = Path(directory) / "calculators.sqlite"
    path.unlink(missing_ok=True)
    conn = sqlite3.connect(str(path))
    conn.executescript(SCHEMA)
    conn.execute(
        "INSERT INTO category (id, external_id, name, name_fa, parent_id, is_main_category) "
        "VALUES (1, 100, 'Cardiology', 'قلب', NULL, 1)"
    )
    conn.execute(
        "INSERT INTO tag (id, external_id, name, name_fa) VALUES (1, 200, 'risk', 'ریسک')"
    )

    for i, (calc_overrides, questions, results) in enumerate(calculators or [], start=1):
        row = {
            "id": i, "uid": f"CALC-{i}", "calculator_id": str(i), "url": "",
            "name": "Test Score", "name_fa": "امتیاز تست",
            "description": "A test calculator.", "description_fa": "یک ماشین‌حساب تست.",
            "about": "<p>About it.</p>", "about_fa": "<p>درباره‌اش.</p>",
            "disclaimer_footer": "", "disclaimer_footer_fa": "",
            "translated": 1, "data": "{}", "data_fa": None, "formula_strings_fa": None,
        }
        row.update(calc_overrides)
        conn.execute(
            "INSERT INTO calculator (id, uid, calculator_id, url, name, name_fa, description, "
            "description_fa, about, about_fa, disclaimer_footer, disclaimer_footer_fa, translated, "
            "data, data_fa, formula_strings_fa) VALUES (:id,:uid,:calculator_id,:url,:name,:name_fa,"
            ":description,:description_fa,:about,:about_fa,:disclaimer_footer,:disclaimer_footer_fa,"
            ":translated,:data,:data_fa,:formula_strings_fa)",
            row,
        )
        conn.execute("INSERT INTO calculator_category (calculator_id, category_id) VALUES (?, 1)", (i,))
        conn.execute("INSERT INTO calculator_tag (calculator_id, tag_id) VALUES (?, 1)", (i,))

        for q in questions or []:
            conn.execute(
                "INSERT INTO question (id, calculator_id, position, type, title, title_fa, "
                "more_information, more_information_fa, section_name, section_name_fa, initial_value) "
                "VALUES (:id,:calculator_id,:position,:type,:title,:title_fa,NULL,NULL,NULL,NULL,NULL)",
                {"id": q["id"], "calculator_id": i, **q},
            )
            unit = q.get("unit")
            if unit:
                conn.execute(
                    "INSERT INTO question_unit (question_id, position, title, title_fa, min_value, "
                    "max_value, unit_factor) VALUES (?, 0, ?, ?, ?, ?, '1')",
                    (q["id"], unit["title"], unit["title_fa"], unit["min_value"], unit["max_value"]),
                )

        for r in results or []:
            conn.execute(
                "INSERT INTO result (calculator_id, position, title, title_fa, formula, "
                "condition_formula, answer, answer_fa, type) "
                "VALUES (:calculator_id,:position,:title,:title_fa,:formula,NULL,:answer,:answer_fa,'default')",
                {"calculator_id": i, **r},
            )
        conn.execute(
            "INSERT INTO reference (calculator_id, position, names, sources, papers) "
            "VALUES (?, 0, 'Someone et al.', 'A journal.', '<a>link</a>')",
            (i,),
        )

    conn.commit()
    conn.close()
    return str(path)


def _one_calculator(**overrides):
    questions = [{
        "id": 1, "position": 0, "title": "Age?", "title_fa": "سن؟", "type": "numeric_input",
        "unit": {"title": "Years", "title_fa": "سال", "min_value": "0", "max_value": "120"},
    }]
    results = [{
        "position": 0, "title": "Score", "title_fa": "امتیاز",
        "formula": "(function() { return $0; })();", "answer": "$result0", "answer_fa": "$result0",
    }]
    return (overrides, questions, results)


class ImportCalculatorsTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)

    def test_import_creates_a_bilingual_calculator(self):
        source = _build_sqlite(self._tmp.name, [_one_calculator()])
        call_command("import_calculators", source=source)

        self.assertEqual(Calculator.objects.count(), 1)
        calc = Calculator.objects.get(uid="CALC-1")
        self.assertEqual(calc.slug, "test-score-1")
        self.assertEqual(calc.name_fa, "امتیاز تست")
        self.assertEqual([c.name for c in calc.categories.all()], ["Cardiology"])
        self.assertEqual([c.name_fa for c in calc.categories.all()], ["قلب"])
        self.assertEqual([t.name for t in calc.tags.all()], ["risk"])
        self.assertEqual(len(calc.questions), 1)
        self.assertEqual(calc.questions[0]["title_fa"], "سن؟")
        self.assertEqual(calc.questions[0]["units"][0]["title_fa"], "سال")
        self.assertEqual(len(calc.results), 1)
        self.assertIn("return $0", calc.results[0]["formula"])

    def test_formula_string_translations_are_imported(self):
        source = _build_sqlite(self._tmp.name, [_one_calculator(
            formula_strings_fa='{"Positive": "مثبت", "Empty": "  ", "Negative": "منفی"}',
        )])
        call_command("import_calculators", source=source)

        self.assertEqual(
            Calculator.objects.get(uid="CALC-1").formula_strings_fa,
            {"Positive": "مثبت", "Negative": "منفی"},
        )

    def test_missing_or_malformed_formula_string_translations_import_as_empty(self):
        source = _build_sqlite(self._tmp.name, [
            _one_calculator(),
            ({"uid": "CALC-2", "calculator_id": "2", "formula_strings_fa": "not json"}, [], []),
        ])
        call_command("import_calculators", source=source)

        self.assertEqual(Calculator.objects.get(uid="CALC-1").formula_strings_fa, {})
        self.assertEqual(Calculator.objects.get(uid="CALC-2").formula_strings_fa, {})

    def test_reimport_is_idempotent(self):
        source = _build_sqlite(self._tmp.name, [_one_calculator()])
        call_command("import_calculators", source=source)
        call_command("import_calculators", source=source)

        self.assertEqual(Calculator.objects.count(), 1)
        self.assertEqual(CalculatorCategory.objects.count(), 1)
        self.assertEqual(CalculatorTag.objects.count(), 1)

    def test_rerun_updates_changed_fields(self):
        source = _build_sqlite(self._tmp.name, [_one_calculator()])
        call_command("import_calculators", source=source)

        source = _build_sqlite(self._tmp.name, [_one_calculator(description="Updated.")])
        call_command("import_calculators", source=source)

        self.assertEqual(Calculator.objects.get(uid="CALC-1").description, "Updated.")

    def test_record_missing_name_is_skipped(self):
        source = _build_sqlite(self._tmp.name, [_one_calculator(name="")])
        call_command("import_calculators", source=source)

        self.assertEqual(Calculator.objects.count(), 0)

    def test_dry_run_writes_nothing(self):
        source = _build_sqlite(self._tmp.name, [_one_calculator()])
        call_command("import_calculators", source=source, dry_run=True)

        self.assertEqual(Calculator.objects.count(), 0)
        self.assertEqual(CalculatorCategory.objects.count(), 0)

    def test_questions_and_results_are_sorted_by_position(self):
        overrides, _, results = _one_calculator()
        questions = [
            {"id": 1, "position": 1, "title": "Second", "title_fa": "دوم", "type": "numeric_input"},
            {"id": 2, "position": 0, "title": "First", "title_fa": "اول", "type": "numeric_input"},
        ]
        source = _build_sqlite(self._tmp.name, [(overrides, questions, results)])
        call_command("import_calculators", source=source)

        calc = Calculator.objects.get(uid="CALC-1")
        self.assertEqual([q["title"] for q in calc.questions], ["First", "Second"])

    def test_category_parent_links_are_wired_up(self):
        source = _build_sqlite(self._tmp.name, [_one_calculator()])
        conn = sqlite3.connect(source)
        conn.execute(
            "INSERT INTO category (id, external_id, name, name_fa, parent_id, is_main_category) "
            "VALUES (2, 101, 'Arrhythmia', 'آریتمی', 1, 0)"
        )
        conn.execute("INSERT INTO calculator_category (calculator_id, category_id) VALUES (1, 2)")
        conn.commit()
        conn.close()

        call_command("import_calculators", source=source)

        sub = CalculatorCategory.objects.get(external_id=101)
        self.assertEqual(sub.name, "Arrhythmia")
        self.assertEqual(sub.parent.name, "Cardiology")


class CalculatorApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(
            username="reader", email="reader@example.com", password="x"
        ))
        cardiology = CalculatorCategory.objects.create(external_id=1, name="Cardiology", name_fa="قلب", is_main_category=True)
        nephrology = CalculatorCategory.objects.create(external_id=2, name="Nephrology", name_fa="کلیه", is_main_category=True)

        c1 = Calculator.objects.create(
            uid="CALC-1", calculator_id="1", slug="test-score-1",
            name="Test Score", name_fa="امتیاز تست",
            description="A test calculator.", description_fa="یک ماشین‌حساب تست.",
            questions=[{"position": 0, "title": "Age?", "title_fa": "سن؟", "type": "numeric_input"}],
            results=[{"position": 0, "title": "Score", "title_fa": "امتیاز", "formula": "(function(){return $0;})();"}],
        )
        c1.categories.add(cardiology)
        c2 = Calculator.objects.create(
            uid="CALC-2", calculator_id="2", slug="other-tool-2",
            name="Other Tool", name_fa="ابزار دیگر", description="Unrelated.",
        )
        c2.categories.add(nephrology)

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get("/api/v1/calculators/").status_code, 401)

    def test_list_returns_the_full_unpaginated_set(self):
        res = self.client.get("/api/v1/calculators/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 2)
        self.assertEqual({c["slug"] for c in res.data}, {"test-score-1", "other-tool-2"})

    def test_list_includes_bilingual_category_objects(self):
        res = self.client.get("/api/v1/calculators/")
        row = next(c for c in res.data if c["slug"] == "test-score-1")
        self.assertEqual(row["name_fa"], "امتیاز تست")
        self.assertEqual(
            [(cat["name"], cat["name_fa"]) for cat in row["categories"]],
            [("Cardiology", "قلب")],
        )

    def test_detail_includes_questions_and_results(self):
        res = self.client.get("/api/v1/calculators/test-score-1/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["name"], "Test Score")
        self.assertEqual(len(res.data["questions"]), 1)
        self.assertEqual(res.data["questions"][0]["title_fa"], "سن؟")
        self.assertEqual(len(res.data["results"]), 1)
        self.assertEqual(res.data["formula_strings_fa"], {})

    def test_list_excludes_questions_and_results(self):
        res = self.client.get("/api/v1/calculators/")
        self.assertNotIn("questions", res.data[0])

    def test_category_list_returns_the_full_tree_independent_of_calculators(self):
        CalculatorCategory.objects.create(
            external_id=3, name="Arrhythmia", name_fa="آریتمی",
            parent=CalculatorCategory.objects.get(name="Cardiology"),
        )
        res = self.client.get("/api/v1/calculators/categories/")
        self.assertEqual(res.status_code, 200)
        names = {row["name"] for row in res.data}
        self.assertEqual(names, {"Cardiology", "Nephrology", "Arrhythmia"})
        arrhythmia = next(row for row in res.data if row["name"] == "Arrhythmia")
        cardiology = next(row for row in res.data if row["name"] == "Cardiology")
        self.assertEqual(arrhythmia["parent_id"], cardiology["id"])
