"""Round trips through the reference-data files: export what's in the
database, empty it, import the files back, and get the same data -- with
image blocks pointing at whatever ids the images got the second time."""

import tempfile
from datetime import date
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from apps.calculators.models import Calculator, CalculatorCategory, CalculatorTag
from apps.medscape.models import Article, ArticleImage


def run(*args):
    out = StringIO()
    call_command(*args, stdout=out)
    return out.getvalue()


class ReferenceDbTests(TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

        main = CalculatorCategory.objects.create(external_id=1, name="Cardiology", name_fa="قلب", is_main_category=True)
        sub = CalculatorCategory.objects.create(external_id=2, name="Heart failure", name_fa="نارسایی", parent=main)
        tag = CalculatorTag.objects.create(external_id=7, name="score", name_fa="امتیاز")
        calc = Calculator.objects.create(
            uid="CALC-1", calculator_id="1", slug="chads-1", name="CHADS2", name_fa="چادز",
            questions=[{"position": 0, "title": "Age", "title_fa": "سن", "choices": []}],
            results=[{"position": 0, "formula": "(function(){return $0;})();"}],
            formula_strings_fa={"Low": "کم"}, references=["Gage 2001"],
        )
        calc.categories.set([main, sub])
        calc.tags.set([tag])

        self.image = ArticleImage.objects.create(content_hash="a" * 64, content_type="image/png", data=b"\x89PNG-one")
        self.disease = Article.objects.create(
            kind=Article.DISEASE, source_id="123", slug="itp-123", title="ITP",
            categories=[{"category": "medicine", "specialty": "Hematology"}],
            sections=[{
                "heading": "Overview",
                "blocks": [
                    {"type": "paragraph", "text": "Platelets are low."},
                    {"type": "image", "id": self.image.pk, "alt": "smear", "caption": "Blood smear"},
                ],
                "children": [{"heading": "Background", "blocks": [], "children": []}],
            }],
        )
        Article.objects.create(
            kind=Article.GUIDELINE, source_id="copd", slug="g-copd", title="COPD", sections=[],
            latest_update=date(2026, 7, 1),
        )

    def tearDown(self):
        self.tmp.cleanup()

    def export(self, *only):
        args = ["export_reference_db", "--out", str(self.dir)]
        for dataset in only:
            args += ["--only", dataset]
        return run(*args)

    def test_export_writes_three_files(self):
        self.export()
        for name in ("calculators", "guidelines", "diseases"):
            self.assertTrue((self.dir / f"{name}.db").is_file(), name)
        self.assertFalse(list(self.dir.glob("*.partial")))

    def test_calculators_round_trip(self):
        self.export("calculators")
        Calculator.objects.all().delete()
        CalculatorCategory.objects.all().delete()
        CalculatorTag.objects.all().delete()

        report = run("import_calculators_db", "--source", str(self.dir / "calculators.db"))
        self.assertIn("calculator: 1 added", report)
        calc = Calculator.objects.get(uid="CALC-1")
        self.assertEqual(calc.name_fa, "چادز")
        self.assertEqual(calc.formula_strings_fa, {"Low": "کم"})
        self.assertEqual(calc.references, ["Gage 2001"])
        self.assertEqual(sorted(calc.categories.values_list("external_id", flat=True)), [1, 2])
        self.assertEqual(list(calc.tags.values_list("external_id", flat=True)), [7])
        self.assertEqual(CalculatorCategory.objects.get(external_id=2).parent.external_id, 1)

    def test_articles_round_trip_remaps_image_ids(self):
        self.export("diseases", "guidelines")
        Article.objects.all().delete()
        ArticleImage.objects.all().delete()
        # an unrelated image takes the next id, so the reimported one gets another
        ArticleImage.objects.create(content_hash="b" * 64, content_type="image/png", data=b"other")

        run("import_diseases_db", "--source", str(self.dir / "diseases.db"))
        run("import_guidelines_db", "--source", str(self.dir / "guidelines.db"))

        image = ArticleImage.objects.get(content_hash="a" * 64)
        self.assertEqual(bytes(image.data), b"\x89PNG-one")
        disease = Article.objects.get(kind=Article.DISEASE, source_id="123")
        block = disease.sections[0]["blocks"][1]
        self.assertEqual(block, {"type": "image", "id": image.pk, "alt": "smear", "caption": "Blood smear"})
        self.assertEqual(disease.sections[0]["children"][0]["heading"], "Background")
        self.assertEqual(disease.categories, [{"category": "medicine", "specialty": "Hematology"}])
        self.assertEqual(Article.objects.get(kind=Article.GUIDELINE).latest_update, date(2026, 7, 1))

    def test_reimport_updates_in_place(self):
        self.export("diseases")
        Article.objects.filter(pk=self.disease.pk).update(title="Changed locally")
        report = run("import_diseases_db", "--source", str(self.dir / "diseases.db"))
        self.assertIn("article: 0 added, 1 updated", report)
        self.assertIn("image: 0 added, 1 already present", report)
        self.assertEqual(Article.objects.get(pk=self.disease.pk).title, "ITP")
        self.assertEqual(Article.objects.filter(kind=Article.DISEASE).count(), 1)

    def test_prune_removes_only_rows_missing_from_the_file(self):
        self.export("diseases")
        Article.objects.create(kind=Article.DISEASE, source_id="999", slug="extra-999", title="Extra")
        run("import_diseases_db", "--source", str(self.dir / "diseases.db"), "--prune")
        self.assertFalse(Article.objects.filter(source_id="999").exists())
        self.assertTrue(Article.objects.filter(kind=Article.GUIDELINE).exists())  # other kind untouched

    def test_dry_run_writes_nothing(self):
        self.export("diseases")
        Article.objects.all().delete()
        report = run("import_diseases_db", "--source", str(self.dir / "diseases.db"), "--dry-run")
        self.assertIn("rolled back", report)
        self.assertFalse(Article.objects.exists())

    def test_a_file_for_another_dataset_is_refused(self):
        self.export("guidelines")
        with self.assertRaises(CommandError):
            run("import_diseases_db", "--source", str(self.dir / "guidelines.db"))

    def test_a_missing_file_is_refused(self):
        with self.assertRaises(CommandError):
            run("import_calculators_db", "--source", str(self.dir / "nope.db"))
