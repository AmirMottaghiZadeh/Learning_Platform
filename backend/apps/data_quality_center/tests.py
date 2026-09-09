from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.drugs.models import Ingredient, IngredientProfileSection

from .models import SectionEdit


@override_settings(ROOT_URLCONF="apps.data_quality_center.tests_urls")
class DataQualityCenterTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            "editor", "e@e.com", "x", is_staff=True
        )
        self.client = Client()
        self.client.force_login(self.staff)

        self.ingredient = Ingredient.objects.create(
            name="losartan", rxcui="52175", slug="losartan-52175"
        )
        self.section = IngredientProfileSection.objects.create(
            ingredient=self.ingredient, field="dosage_and_administration",
            raw_text="50 mg once daily.", summary_fa="", summary_en="",
        )

    def _edit_url(self):
        return reverse(
            "data_quality_center:section_edit",
            args=[self.ingredient.slug, "dosage_and_administration"],
        )

    def test_list_and_detail_render_for_staff(self):
        self.assertEqual(self.client.get(reverse("data_quality_center:ingredient_list")).status_code, 200)
        detail = self.client.get(
            reverse("data_quality_center:ingredient_detail", args=[self.ingredient.slug])
        )
        self.assertEqual(detail.status_code, 200)
        self.assertContains(detail, "50 mg once daily.")

    def test_missing_filter_finds_the_empty_summary(self):
        res = self.client.get(reverse("data_quality_center:ingredient_list"), {"missing": "fa"})
        self.assertContains(res, "losartan")

    def test_edit_saves_summaries_and_writes_an_append_only_log(self):
        res = self.client.post(self._edit_url(), {
            "summary_fa": "۵۰ میلی‌گرم یک بار در روز.",
            "summary_en": "50 mg once daily.",
            "reason": "Filled the missing dosing summary from the label.",
        }, follow=True)
        self.assertEqual(res.status_code, 200)

        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "۵۰ میلی‌گرم یک بار در روز.")
        self.assertEqual(self.section.raw_text, "50 mg once daily.")  # untouched

        log = SectionEdit.objects.get()
        self.assertEqual(log.field, "dosage_and_administration")
        self.assertEqual(log.before_fa, "")
        self.assertEqual(log.after_fa, "۵۰ میلی‌گرم یک بار در روز.")
        self.assertEqual(log.editor, self.staff)
        with self.assertRaises(ValueError):
            log.save()

    def test_short_reason_is_rejected_and_nothing_changes(self):
        res = self.client.post(self._edit_url(), {
            "summary_fa": "چیزی", "summary_en": "x", "reason": "no",
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "")
        self.assertEqual(SectionEdit.objects.count(), 0)

    def test_no_op_edit_writes_no_log(self):
        self.client.post(self._edit_url(), {
            "summary_fa": "", "summary_en": "", "reason": "This should be a no-op edit.",
        })
        self.assertEqual(SectionEdit.objects.count(), 0)

    def test_history_page_lists_edits(self):
        self.client.post(self._edit_url(), {
            "summary_fa": "متن", "summary_en": "text",
            "reason": "Adding an English and Persian summary.",
        })
        res = self.client.get(reverse("data_quality_center:edit_history"))
        self.assertContains(res, "losartan")
        self.assertContains(res, "Adding an English and Persian summary.")

    def test_non_staff_is_redirected_to_admin_login(self):
        plain = get_user_model().objects.create_user("plain", "p@e.com", "x")
        c = Client()
        c.force_login(plain)
        res = c.get(reverse("data_quality_center:ingredient_list"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin/login/", res["Location"])
