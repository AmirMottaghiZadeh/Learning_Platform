import sqlite3
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.db import IntegrityError
from django.test import TestCase

from apps.drugs.models import (
    CLINICAL_FIELD_KEYS,
    AtcCode,
    Ingredient,
    IngredientProfileSection,
)


def _make_source_db(directory, profiles, atc_rows=()):
    """Write a minimal copy of the pipeline schema and return its path."""
    path = Path(directory) / "pipeline.db"
    path.unlink(missing_ok=True)
    conn = sqlite3.connect(path)

    profile_cols = ["ingredient_rxcui", "ingredient_name", "n_products",
                    "n_source_records", "pharm_class_epc", "atc_codes"]
    for field in CLINICAL_FIELD_KEYS:
        profile_cols += [
            field,
            f"{field}_n_contributing_products",
            f"{field}_summary_fa",
            f"{field}_summary_en",
        ]
    conn.execute(
        f"CREATE TABLE ingredient_clinical_profiles ({', '.join(c + ' TEXT' for c in profile_cols)})"
    )
    conn.execute(
        "CREATE TABLE ingredient_atc_codes "
        "(ingredient_rxcui TEXT, atc_codes_json TEXT, epc_codes_json TEXT)"
    )

    for profile in profiles:
        row = {col: profile.get(col) for col in profile_cols}
        placeholders = ", ".join(["?"] * len(profile_cols))
        conn.execute(
            f"INSERT INTO ingredient_clinical_profiles VALUES ({placeholders})",
            [row[col] for col in profile_cols],
        )
    for atc in atc_rows:
        conn.execute(
            "INSERT INTO ingredient_atc_codes VALUES (?, ?, ?)",
            [atc["ingredient_rxcui"], atc["atc_codes_json"], atc["epc_codes_json"]],
        )
    conn.commit()
    conn.close()
    return str(path)


class ModelTests(TestCase):
    def test_build_slug_is_name_plus_rxcui(self):
        self.assertEqual(Ingredient.build_slug("Losartan Potassium", "52175"),
                         "losartan-potassium-52175")

    def test_section_content_and_summary_flags(self):
        ingredient = Ingredient.objects.create(
            rxcui="1", name="aspirin", slug="aspirin-1"
        )
        section = IngredientProfileSection.objects.create(
            ingredient=ingredient, field="warnings", raw_text="  ", summary_fa=""
        )
        self.assertFalse(section.has_content)
        self.assertFalse(section.has_summary)

        section.raw_text = "Do not exceed the stated dose."
        section.summary_fa = "بیش از مقدار توصیه‌شده مصرف نکنید."
        section.save()
        self.assertTrue(section.has_content)
        self.assertTrue(section.has_summary)

    def test_one_section_per_field_per_ingredient(self):
        ingredient = Ingredient.objects.create(rxcui="2", name="ibuprofen", slug="ibuprofen-2")
        IngredientProfileSection.objects.create(ingredient=ingredient, field="pregnancy")
        with self.assertRaises(IntegrityError):
            IngredientProfileSection.objects.create(ingredient=ingredient, field="pregnancy")


class ImportOpenfdaTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.profiles = [
            {
                "ingredient_rxcui": "52175",
                "ingredient_name": "losartan",
                "n_products": 7,
                "n_source_records": 206,
                "pharm_class_epc": '["Angiotensin 2 Receptor Blocker"]',
                "atc_codes": '[{"atc_code": "C09CA", "atc_name": "ARBs, plain"}]',
                "indications_and_usage": "Lowers blood pressure.",
                "indications_and_usage_n_contributing_products": 5,
                "indications_and_usage_summary_fa": "فشار خون بالا.",
                "indications_and_usage_summary_en": "Hypertension.",
                "boxed_warning": "Discontinue when pregnancy is detected.",
                "boxed_warning_summary_fa": "در بارداری قطع شود.",
            },
            {
                # No inline atc/pharm -> must fall back to ingredient_atc_codes.
                "ingredient_rxcui": "5487",
                "ingredient_name": "hydrochlorothiazide",
                "n_products": 48,
                "n_source_records": 233,
                "contraindications": "Anuria.",
                "contraindications_summary_fa": "آنوری.",
            },
        ]
        self.atc_rows = [{
            "ingredient_rxcui": "5487",
            "atc_codes_json": '[{"atc_code": "C03AA", "atc_name": "Thiazides, plain"}]',
            "epc_codes_json": '["Thiazide Diuretic"]',
        }]

    def _source(self):
        return _make_source_db(self._tmp.name, self.profiles, self.atc_rows)

    def test_import_creates_ingredients_sections_and_atc(self):
        call_command("import_openfda", source=self._source())

        self.assertEqual(Ingredient.objects.count(), 2)
        # Twelve sections per ingredient, one per clinical field.
        self.assertEqual(IngredientProfileSection.objects.count(), 24)

        losartan = Ingredient.objects.get(rxcui="52175")
        self.assertEqual(losartan.slug, "losartan-52175")
        self.assertEqual(losartan.n_products, 7)
        self.assertEqual(losartan.pharm_classes, ["Angiotensin 2 Receptor Blocker"])
        self.assertEqual(list(losartan.atc_codes.values_list("code", flat=True)), ["C09CA"])

        ind = losartan.sections.get(field="indications_and_usage")
        self.assertEqual(ind.summary_fa, "فشار خون بالا.")
        self.assertEqual(ind.n_contributing_products, 5)
        self.assertTrue(ind.has_content)

        empty = losartan.sections.get(field="abuse")
        self.assertFalse(empty.has_content)

    def test_atc_and_pharm_class_fall_back_to_side_table(self):
        call_command("import_openfda", source=self._source())

        hctz = Ingredient.objects.get(rxcui="5487")
        self.assertEqual(hctz.pharm_classes, ["Thiazide Diuretic"])
        self.assertEqual(list(hctz.atc_codes.values_list("code", flat=True)), ["C03AA"])
        self.assertEqual(AtcCode.objects.get(code="C03AA").name, "Thiazides, plain")

    def test_reimport_is_idempotent(self):
        source = self._source()
        call_command("import_openfda", source=source)
        call_command("import_openfda", source=source)

        self.assertEqual(Ingredient.objects.count(), 2)
        self.assertEqual(IngredientProfileSection.objects.count(), 24)
        self.assertEqual(AtcCode.objects.count(), 2)

    def test_only_summaries_updates_summaries_without_touching_raw_text(self):
        call_command("import_openfda", source=self._source())

        self.profiles[0]["indications_and_usage"] = "REWRITTEN raw text"
        self.profiles[0]["indications_and_usage_summary_fa"] = "خلاصهٔ به‌روزشده."
        call_command("import_openfda", source=self._source(), only_summaries=True)

        ind = Ingredient.objects.get(rxcui="52175").sections.get(field="indications_and_usage")
        self.assertEqual(ind.summary_fa, "خلاصهٔ به‌روزشده.")
        self.assertEqual(ind.raw_text, "Lowers blood pressure.")

    def test_dry_run_writes_nothing(self):
        call_command("import_openfda", source=self._source(), dry_run=True)
        self.assertEqual(Ingredient.objects.count(), 0)
        self.assertEqual(IngredientProfileSection.objects.count(), 0)
        self.assertEqual(AtcCode.objects.count(), 0)
