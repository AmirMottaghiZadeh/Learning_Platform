from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.drugs.models import Ingredient, IngredientProfileSection

from .models import SectionEdit, SectionEditRequest


@override_settings(ROOT_URLCONF="apps.data_quality_center.tests_urls")
class DataQualityCenterTests(TestCase):
    def setUp(self):
        self.staff = get_user_model().objects.create_user(
            "editor", "e@e.com", "x", is_staff=True
        )
        self.superuser = get_user_model().objects.create_user(
            "boss", "b@e.com", "x", is_staff=True, is_superuser=True
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

    def _submit_edit(self, **overrides):
        payload = {
            "summary_fa": "۵۰ میلی‌گرم یک بار در روز.",
            "summary_en": "50 mg once daily.",
            "reason": "Filled the missing dosing summary from the label.",
        }
        payload.update(overrides)
        return self.client.post(self._edit_url(), payload, follow=True)

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

    def test_edit_creates_a_pending_request_without_touching_the_section(self):
        res = self._submit_edit()
        self.assertEqual(res.status_code, 200)

        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "")  # untouched until approved
        self.assertEqual(self.section.raw_text, "50 mg once daily.")

        req = SectionEditRequest.objects.get()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)
        self.assertEqual(req.field, "dosage_and_administration")
        self.assertEqual(req.before_fa, "")
        self.assertEqual(req.after_fa, "۵۰ میلی‌گرم یک بار در روز.")
        self.assertEqual(req.requested_by, self.staff)
        self.assertEqual(SectionEdit.objects.count(), 0)

    def test_second_submission_while_one_is_pending_is_rejected(self):
        self._submit_edit()
        res = self._submit_edit(summary_fa="یک متن دیگر", summary_en="different text")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(SectionEditRequest.objects.count(), 1)

    def test_short_reason_is_rejected_and_nothing_changes(self):
        res = self.client.post(self._edit_url(), {
            "summary_fa": "چیزی", "summary_en": "x", "reason": "no",
        }, follow=True)
        self.assertEqual(res.status_code, 200)
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "")
        self.assertEqual(SectionEditRequest.objects.count(), 0)

    def test_no_op_edit_writes_no_request(self):
        self.client.post(self._edit_url(), {
            "summary_fa": "", "summary_en": "", "reason": "This should be a no-op edit.",
        })
        self.assertEqual(SectionEditRequest.objects.count(), 0)

    def test_superuser_approval_applies_the_change_and_writes_the_ledger(self):
        self._submit_edit()
        req = SectionEditRequest.objects.get()

        self.client.force_login(self.superuser)
        res = self.client.post(
            reverse("data_quality_center:review_request", args=[req.id]),
            {"action": "approve", "note": "Looks right."},
            follow=True,
        )
        self.assertEqual(res.status_code, 200)

        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "۵۰ میلی‌گرم یک بار در روز.")

        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_APPROVED)
        self.assertEqual(req.reviewed_by, self.superuser)

        log = SectionEdit.objects.get()
        self.assertEqual(log.editor, self.staff)
        self.assertEqual(log.approved_by, self.superuser)
        with self.assertRaises(ValueError):
            log.save()

    def test_superuser_rejection_leaves_the_section_unchanged(self):
        self._submit_edit()
        req = SectionEditRequest.objects.get()

        self.client.force_login(self.superuser)
        self.client.post(
            reverse("data_quality_center:review_request", args=[req.id]),
            {"action": "reject", "note": "Needs a source citation."},
        )

        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "")
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_REJECTED)
        self.assertEqual(SectionEdit.objects.count(), 0)

    def test_plain_staff_cannot_review_a_request(self):
        self._submit_edit()
        req = SectionEditRequest.objects.get()
        res = self.client.post(
            reverse("data_quality_center:review_request", args=[req.id]),
            {"action": "approve", "note": ""},
        )
        self.assertEqual(res.status_code, 403)
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)

    def test_approval_is_refused_if_the_section_drifted_since_submission(self):
        self._submit_edit()
        req = SectionEditRequest.objects.get()

        # Something else changed the section after the request was filed.
        self.section.summary_fa = "یک چیز دیگر"
        self.section.save(update_fields=["summary_fa"])

        self.client.force_login(self.superuser)
        self.client.post(
            reverse("data_quality_center:review_request", args=[req.id]),
            {"action": "approve", "note": ""},
        )
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)  # refused, still open
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "یک چیز دیگر")

    def test_pending_requests_page_lists_the_open_request(self):
        self._submit_edit()
        res = self.client.get(reverse("data_quality_center:pending_requests"))
        self.assertContains(res, "losartan")
        self.assertContains(res, "Filled the missing dosing summary")

    def test_history_page_lists_requests_regardless_of_status(self):
        self._submit_edit()
        req = SectionEditRequest.objects.get()
        self.client.force_login(self.superuser)
        self.client.post(
            reverse("data_quality_center:review_request", args=[req.id]),
            {"action": "approve", "note": ""},
        )
        res = self.client.get(reverse("data_quality_center:edit_history"))
        self.assertContains(res, "losartan")
        self.assertContains(res, "Filled the missing dosing summary")

    def test_non_staff_is_redirected_to_admin_login(self):
        plain = get_user_model().objects.create_user("plain", "p@e.com", "x")
        c = Client()
        c.force_login(plain)
        res = c.get(reverse("data_quality_center:ingredient_list"))
        self.assertEqual(res.status_code, 302)
        self.assertIn("/admin/login/", res["Location"])
