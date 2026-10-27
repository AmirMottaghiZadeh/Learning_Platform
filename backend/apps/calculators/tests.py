import sqlite3
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
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

    def test_tags_are_in_the_detail_but_not_the_list(self):
        calc = Calculator.objects.get(slug="test-score-1")
        calc.tags.add(CalculatorTag.objects.create(external_id=7, name="risk", name_fa="خطر"))

        self.assertNotIn("tags", self.client.get("/api/v1/calculators/").data[0])
        detail = self.client.get("/api/v1/calculators/test-score-1/").data
        self.assertEqual([(t["name"], t["name_fa"]) for t in detail["tags"]], [("risk", "خطر")])

    def test_list_reads_only_its_own_columns_with_a_fixed_number_of_queries(self):
        # The list defers the big JSON/text columns; touching one per row
        # would silently add a query per calculator.
        cardiology = CalculatorCategory.objects.get(name="Cardiology")
        for i in range(10):
            extra = Calculator.objects.create(
                uid=f"CALC-X{i}", calculator_id=f"x{i}", slug=f"extra-{i}", name=f"Extra {i}",
                questions=[{"position": 0}], results=[{"position": 0}],
            )
            extra.categories.add(cardiology)
        with CaptureQueriesContext(connection) as ctx:
            res = self.client.get("/api/v1/calculators/")
        self.assertEqual(len(res.data), 12)
        self.assertEqual(len(ctx.captured_queries), 2)  # calculators + their categories
        calculator_select = ctx.captured_queries[0]["sql"]
        for heavy in ("questions", "results", "about", "formula_strings_fa"):
            self.assertNotIn(f'"calculators_calculator"."{heavy}"', calculator_select)

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


class FormulaErrataTests(TestCase):
    """The corrections to the source's mistaken formulas (apps/calculators/errata.py)."""

    GENEVA = "676"
    GARFIELD = "685"

    def test_geneva_score_adds_the_surgery_question_not_a_missing_one(self):
        from apps.calculators.errata import fix_results

        rows = [{"position": 0, "formula": "results += $7;\n\tresults += $8;"}]
        fixed = fix_results(self.GENEVA, rows)
        self.assertEqual(fixed[0]["formula"], "results += $7;\n\tresults += $2;")
        self.assertEqual(rows[0]["formula"], "results += $7;\n\tresults += $8;")  # input untouched

    def test_fixes_apply_once(self):
        from apps.calculators.errata import FORMULA_ERRATA, fix_results

        for calculator_id, per_row in FORMULA_ERRATA.items():
            rows = [{"position": p, "formula": "x $result1 $result2 $result3 results += $8; results += $1 +$2 +$3 + $4 + $5 + $6 + $7 + $8 + $9 + $10;"} for p in per_row]
            once = fix_results(calculator_id, rows)
            self.assertEqual(fix_results(calculator_id, once), once, calculator_id)

    def test_one_based_results_are_renumbered_once(self):
        from apps.calculators.errata import fix_results

        rows = [
            {"position": 0, "answer": "$result1", "formula": "return $2;"},
            {"position": 1, "answer": "$result2", "formula": "return $result1 + 1;"},
            {"position": 2, "answer": "$result3", "formula": "return $result1 + $result2;", "condition_formula": "$result2 > 0"},
        ]
        fixed = fix_results(self.GARFIELD, rows)
        self.assertEqual([r["answer"] for r in fixed], ["$result0", "$result1", "$result2"])
        self.assertEqual(fixed[1]["formula"], "return $result0 + 1;")
        self.assertEqual(fixed[2]["formula"], "return $result0 + $result1;")
        self.assertEqual(fixed[2]["condition_formula"], "$result1 > 0")
        self.assertEqual(fix_results(self.GARFIELD, fixed), fixed)  # a second run changes nothing
        self.assertEqual(rows[1]["formula"], "return $result1 + 1;")  # input untouched

    def test_zero_based_calculators_are_not_renumbered(self):
        from apps.calculators.errata import fix_results

        rows = [{"position": 0, "answer": "$result0", "formula": "return 1;"}, {"position": 1, "answer": "$result1", "formula": "return $result0;"}]
        self.assertEqual(fix_results("6", rows), rows)

    def test_renal_cell_survival_row_compares_the_stage_the_stage_row_returns(self):
        from apps.calculators.errata import fix_results

        rows = [{"position": 2, "formula": 'if (stage == "Stage III") {', "condition_formula": '($result1 == "Stage I") || ($result1 == "Stage IV")'}]
        fixed = fix_results("573", rows)[0]
        self.assertEqual(fixed["formula"], 'if (stage == "III") {')
        self.assertEqual(fixed["condition_formula"], '($result1 == "I") || ($result1 == "IV")')

    def test_every_listed_replacement_applies(self):
        from apps.calculators.errata import fix_results

        rows = [{"position": 0, "formula": "var age = $2; var ondialysis = $10; results = bmivalue + gfrvalue + agevalue + $3 + $4 + $5 + $6 + $7 + $8 + $9;"}]
        fixed = fix_results("325", rows)[0]["formula"]
        self.assertEqual(fixed, "var age = $3; var ondialysis = $2; results = bmivalue + gfrvalue + agevalue + $4 + $5 + $6 + $7 + $8 + $9 + $10;")
        self.assertEqual(fix_results("325", [{"position": 0, "formula": fixed}])[0]["formula"], fixed)

    def test_a_title_formula_with_no_result_of_its_own_becomes_the_result(self):
        from apps.calculators.errata import fix_results

        rows = [{"position": 0, "formula": "", "title_formula": "(function() { return 'x'; })();", "answer": "", "answer_fa": None}]
        fixed = fix_results("136", rows)[0]
        self.assertEqual((fixed["formula"], fixed["answer"], fixed["answer_fa"]), ("(function() { return 'x'; })();", "$result0", "$result0"))
        self.assertEqual(fix_results("136", [fixed]), [fixed])

    def test_persian_for_the_new_result_text_is_added(self):
        from apps.calculators.errata import STRINGS_FA, fix_strings_fa

        strings = {"Fully eligible": "کاملاً واجد شرایط"}
        fixed = fix_strings_fa("362", strings)
        self.assertEqual(fixed, {**strings, **STRINGS_FA["362"]})
        self.assertEqual(strings, {"Fully eligible": "کاملاً واجد شرایط"})  # input untouched
        self.assertIs(fix_strings_fa("1", strings), strings)

    def test_other_calculators_are_left_alone(self):
        from apps.calculators.errata import fix_results

        rows = [{"position": 0, "formula": "results += $8;"}]
        self.assertIs(fix_results("1", rows), rows)


class QuestionUnitTests(TestCase):
    def test_unit_goes_before_the_question_mark(self):
        from apps.calculators.errata import _with_unit

        self.assertEqual(_with_unit("Age?", "years"), "Age (years)?")
        self.assertEqual(_with_unit("LDH? (Measured at Admission)", "U/L"), "LDH (U/L)? (Measured at Admission)")
        self.assertEqual(_with_unit("Resting pulse rate", "beats/min"), "Resting pulse rate (beats/min)")
        self.assertEqual(_with_unit("سن؟", "سال"), "سن (سال)؟")
        self.assertEqual(_with_unit("Age (years)?", "years"), "Age (years)?")  # already there

    def test_questions_are_fixed_once_and_others_left_alone(self):
        from apps.calculators.errata import fix_questions

        qs = [{"position": 1, "title": "Age?", "title_fa": "سن؟"}, {"position": 2, "title": "Sex?", "title_fa": "جنسیت؟"}]
        fixed = fix_questions("286", qs)
        self.assertEqual((fixed[0]["title"], fixed[0]["title_fa"]), ("Age (years)?", "سن (سال)؟"))
        self.assertEqual(fixed[1], qs[1])
        self.assertEqual(fix_questions("286", fixed), fixed)
        self.assertIs(fix_questions("999999", qs), qs)


class ChoiceErrataTests(TestCase):
    def test_wrong_weights_are_corrected_by_title_and_a_missing_choice_added_once(self):
        from apps.calculators.errata import fix_questions

        intermittency = {
            "position": 2,
            "choices": [
                {"title_primary": "Not at all", "answer_factor": "0"},
                {"title_primary": "Less than 1 in 5 times", "answer_factor": "1"},
                {"title_primary": "About half the time", "answer_factor": "2"},
                {"title_primary": "More than half the time", "answer_factor": "4"},
                {"title_primary": "Almost always", "answer_factor": "5"},
            ],
        }
        fixed = fix_questions("338", [intermittency])
        self.assertEqual(
            [(c["title_primary"], c["answer_factor"]) for c in fixed[0]["choices"]],
            [("Not at all", "0"), ("Less than 1 in 5 times", "1"), ("Less than half the time", "2"),
             ("About half the time", "3"), ("More than half the time", "4"), ("Almost always", "5")],
        )
        self.assertEqual(fix_questions("338", fixed), fixed)
        self.assertEqual(intermittency["choices"][2]["answer_factor"], "2")  # input untouched

    def test_a_weight_already_changed_is_left_alone(self):
        from apps.calculators.errata import fix_questions

        q = {"position": 3, "choices": [{"title_primary": "Nearly every day", "answer_factor": "1"}]}
        self.assertEqual(fix_questions("317", [q]), [q])


class FaUnitsTests(TestCase):
    def test_only_the_persian_text_is_standardized(self):
        from apps.calculators.errata import standardize_fa_units

        fields = {
            "name": "Dose (mg/kg)",
            "about_fa": "<p>۱۰ میلی‌گرم بر کیلوگرم</p>",
            "questions": [{"title": "Weight", "title_fa": "وزن (کیلوگرم)", "units": [{"title": "mg/dl", "title_fa": "میلی‌گرم/دسی‌لیتر"}]}],
            "results": [{"answer": "$result0 mg", "answer_fa": "$result0 میلی‌گرم"}],
            "formula_strings_fa": {"Give 2 g": "۲ گرم تجویز شود"},
        }
        fixed = standardize_fa_units(fields)
        self.assertEqual(fixed["about_fa"], "<p>10 mg/kg</p>")
        self.assertEqual(fixed["questions"][0]["title_fa"], "وزن (kg)")
        self.assertEqual(fixed["questions"][0]["units"][0], {"title": "mg/dl", "title_fa": "mg/dL"})
        self.assertEqual(fixed["results"][0]["answer_fa"], "$result0 mg")
        self.assertEqual(fixed["formula_strings_fa"], {"Give 2 g": "2 g تجویز شود"})
        self.assertEqual(fixed["name"], "Dose (mg/kg)")
        self.assertEqual(standardize_fa_units(fixed), fixed)
