from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import Role, RoleAssignment, SecurityAuditEvent
from apps.drugs.models import Ingredient, IngredientProfileSection

from . import services
from .checks import numbers_missing_from_source, run_checks, word_diff
from .models import DrugReview, ReviewEvent, SectionEdit, SectionEditRequest
from .services import WorkflowError

FIELD = "dosage_and_administration"
FA = "۵۰ میلی‌گرم یک بار در روز."
EN = "50 mg once daily."
REASON = "Filled the missing dosing summary from the label."


@override_settings(ROOT_URLCONF="apps.data_quality_center.tests_urls")
class ConsoleTestCase(TestCase):
    def setUp(self):
        caches["throttle"].clear()
        User = get_user_model()
        self.staff = User.objects.create_user("editor", "e@e.com", "pass-123456", is_staff=True)
        self.other = User.objects.create_user("editor2", "e2@e.com", "pass-123456", is_staff=True)
        self.superuser = User.objects.create_user(
            "boss", "b@e.com", "pass-123456", is_staff=True, is_superuser=True
        )
        self.client = Client()
        self.client.force_login(self.staff)

        self.ingredient = Ingredient.objects.create(name="losartan", rxcui="52175", slug="losartan-52175")
        self.section = IngredientProfileSection.objects.create(
            ingredient=self.ingredient, field=FIELD,
            raw_text="50 mg once daily; maximum 100 mg.", summary_fa="", summary_en="",
        )

    def url(self, name, field=FIELD):
        return reverse(f"data_quality_center:{name}", args=[self.ingredient.slug, field])

    def save_draft(self, client=None, **overrides):
        payload = {"summary_fa": FA, "summary_en": EN, "reason": REASON, **overrides}
        return (client or self.client).post(self.url("save_draft"), payload)

    def submit(self, client=None, **overrides):
        payload = {"summary_fa": FA, "summary_en": EN, "reason": REASON, **overrides}
        return (client or self.client).post(self.url("submit"), payload, follow=True)

    def as_user(self, user):
        # Review actions belong to the same browser; creating a fresh client
        # each time would simulate a third device under the session limit.
        if not hasattr(self, "user_clients"):
            self.user_clients = {}
        if user.pk not in self.user_clients:
            client = Client()
            client.force_login(user)
            self.user_clients[user.pk] = client
        return self.user_clients[user.pk]

    def review(self, req, action, note="", user=None):
        return self.as_user(user or self.superuser).post(
            reverse("data_quality_center:review_action", args=[req.pk]),
            {"action": action, "note": note},
            follow=True,
        )


class AccessTests(ConsoleTestCase):
    # Signing in is the admin's (apps.manage); the desk's own sign-in page
    # sends there.
    def test_anonymous_is_sent_to_the_admin_login(self):
        res = Client().get(reverse("data_quality_center:queue"))
        self.assertEqual(res.status_code, 302)
        self.assertTrue(res["Location"].startswith(reverse("manage:login")))
        res = Client().get(reverse("data_quality_center:login"))
        self.assertTrue(res["Location"].startswith(reverse("manage:login")))

    def test_staff_signs_in_and_it_is_audited(self):
        res = Client().post(reverse("manage:login"), {"identifier": "editor", "password": "pass-123456",
                                                      "next": reverse("data_quality_center:queue")})
        self.assertRedirects(res, reverse("data_quality_center:queue"), fetch_redirect_response=False)
        self.assertTrue(
            SecurityAuditEvent.objects.filter(user=self.staff, event_type=SecurityAuditEvent.LOGIN_SUCCEEDED).exists()
        )

    def test_non_staff_cannot_sign_in(self):
        get_user_model().objects.create_user("learner", "l@e.com", "pass-123456")
        res = Client().post(reverse("manage:login"), {"identifier": "learner", "password": "pass-123456"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "دسترسی ندارد")

    def test_repeated_failures_lock_the_login(self):
        self.addCleanup(caches["throttle"].clear)
        client = Client()
        for _ in range(8):
            client.post(reverse("manage:login"), {"identifier": "editor", "password": "wrong"})
        res = client.post(reverse("manage:login"), {"identifier": "editor", "password": "pass-123456"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "تلاش‌های ناموفق زیاد بود")

    def test_lockout_ignores_a_forged_forwarded_address(self):
        self.addCleanup(caches["throttle"].clear)
        client = Client()
        for i in range(8):
            client.post(
                reverse("manage:login"), {"identifier": "editor", "password": "wrong"},
                HTTP_X_FORWARDED_FOR=f"10.0.0.{i}, 203.0.113.9",
            )
        res = client.post(
            reverse("manage:login"), {"identifier": "editor", "password": "pass-123456"},
            HTTP_X_FORWARDED_FOR="10.9.9.9, 203.0.113.9",
        )
        self.assertContains(res, "تلاش‌های ناموفق زیاد بود")

    def test_operator_cannot_open_the_review_desk(self):
        res = self.client.get(reverse("data_quality_center:review"))
        self.assertRedirects(res, reverse("data_quality_center:queue"), fetch_redirect_response=False)

    def test_pages_render(self):
        self.submit()
        for name in ["queue", "mine", "history"]:
            self.assertEqual(self.client.get(reverse(f"data_quality_center:{name}")).status_code, 200, name)
        self.assertEqual(self.client.get(reverse("data_quality_center:history"), {"tab": "edits"}).status_code, 200)
        page = self.client.get(reverse("data_quality_center:workspace", args=[self.ingredient.slug]))
        self.assertContains(page, "50 mg once daily; maximum 100 mg.")
        desk = self.as_user(self.superuser).get(reverse("data_quality_center:review"))
        self.assertContains(desk, "losartan")

    def test_missing_filter_finds_the_empty_summary(self):
        res = self.client.get(reverse("data_quality_center:queue"), {"show": "missing"})
        self.assertContains(res, "losartan")


class DraftAndSubmitTests(ConsoleTestCase):
    def test_autosave_keeps_one_draft_and_leaves_the_section_alone(self):
        first = self.save_draft()
        self.assertEqual(first.status_code, 200)
        self.assertTrue(first.json()["ok"])
        self.save_draft(summary_en="50 mg once a day.")

        req = SectionEditRequest.objects.get()
        self.assertEqual(req.status, SectionEditRequest.STATUS_DRAFT)
        self.assertEqual(req.after_en, "50 mg once a day.")
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_en, "")
        self.assertFalse(ReviewEvent.objects.exists())  # drafts have no history yet

    def test_line_breaks_are_stored_as_plain_newlines(self):
        self.save_draft(summary_fa="خط اول\r\nخط دوم\r\n", reason="  two   spaces  ")
        req = SectionEditRequest.objects.get()
        self.assertEqual(req.after_fa, "خط اول\nخط دوم")
        self.assertEqual(req.reason, "two spaces")

    def test_autosave_answers_with_checks_and_diff(self):
        data = self.save_draft(summary_en="75 mg once daily.").json()
        warnings = [c["label"] for c in data["checks"] if c["level"] == "warn"]
        self.assertTrue(any("75" in label for label in warnings))
        self.assertIn("<ins>", data["diff"]["en"])

    def test_submit_makes_a_pending_request_and_an_event(self):
        res = self.submit()
        self.assertEqual(res.status_code, 200)
        req = SectionEditRequest.objects.get()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)
        self.assertIsNotNone(req.submitted_at)
        self.assertEqual(req.before_fa, "")
        self.assertTrue(req.checks)
        event = ReviewEvent.objects.get()
        self.assertEqual((event.action, event.actor), (ReviewEvent.SUBMITTED, self.staff))
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "")

    def test_short_reason_keeps_it_a_draft(self):
        self.submit(reason="no")
        self.assertEqual(SectionEditRequest.objects.get().status, SectionEditRequest.STATUS_DRAFT)

    def test_unchanged_text_cannot_be_submitted(self):
        self.submit(summary_fa="", summary_en="")
        self.assertEqual(SectionEditRequest.objects.get().status, SectionEditRequest.STATUS_DRAFT)

    def test_another_operator_cannot_touch_a_held_section(self):
        self.submit()
        res = self.save_draft(client=self.as_user(self.other))
        self.assertEqual(res.status_code, 409)
        self.assertEqual(SectionEditRequest.objects.count(), 1)

    def test_withdraw_returns_it_to_draft(self):
        self.submit()
        self.client.post(self.url("withdraw"))
        req = SectionEditRequest.objects.get()
        self.assertEqual(req.status, SectionEditRequest.STATUS_DRAFT)
        self.assertEqual(req.events.first().action, ReviewEvent.WITHDRAWN)
        # and it can be edited and sent again
        self.submit(summary_en="50 mg once a day.")
        self.assertEqual(SectionEditRequest.objects.get().status, SectionEditRequest.STATUS_PENDING)

    def test_discarding_a_never_submitted_draft_deletes_it(self):
        self.save_draft()
        self.client.post(self.url("discard"))
        self.assertFalse(SectionEditRequest.objects.exists())


class ReviewTests(ConsoleTestCase):
    def pending(self):
        self.submit()
        return SectionEditRequest.objects.get()

    def test_superuser_approval_applies_and_writes_the_ledger(self):
        req = self.pending()
        self.review(req, "approve", "Looks right.")

        self.section.refresh_from_db()
        self.assertEqual((self.section.summary_fa, self.section.summary_en), (FA, EN))
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_APPROVED)
        edit = SectionEdit.objects.get()
        self.assertEqual((edit.request, edit.editor, edit.approved_by), (req, self.staff, self.superuser))
        self.assertEqual(req.events.first().action, ReviewEvent.APPROVED)
        with self.assertRaises(ValueError):
            edit.save()

    def test_operator_cannot_approve(self):
        req = self.pending()
        with self.assertRaises(WorkflowError):
            services.approve(req, self.staff)
        self.review(req, "approve", user=self.staff)
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "")

    def test_approval_refuses_a_section_that_changed_since_submission(self):
        req = self.pending()
        IngredientProfileSection.objects.filter(pk=self.section.pk).update(summary_en="Changed elsewhere.")
        self.review(req, "approve")
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_en, "Changed elsewhere.")

    def test_changes_requested_then_resubmitted(self):
        req = self.pending()
        self.review(req, "changes")  # a note is required
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)

        self.review(req, "changes", "Mention the 100 mg maximum.")
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_CHANGES_REQUESTED)
        self.assertEqual(req.review_note, "Mention the 100 mg maximum.")

        self.submit(summary_en="50 mg once daily; at most 100 mg a day.")
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)
        self.assertEqual(
            list(req.events.values_list("action", flat=True)),
            [ReviewEvent.RESUBMITTED, ReviewEvent.CHANGES_REQUESTED, ReviewEvent.SUBMITTED],
        )

    def test_discarding_a_sent_back_request_keeps_its_history(self):
        req = self.pending()
        self.review(req, "changes", "Fix the units.")
        self.client.post(self.url("discard"))
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_DISCARDED)
        self.assertEqual(req.events.first().action, ReviewEvent.DISCARDED)

    def test_rejection_leaves_the_section_unchanged(self):
        req = self.pending()
        self.review(req, "reject", "Not supported by the label.")
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_REJECTED)
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_fa, "")
        self.assertFalse(SectionEdit.objects.exists())

    def test_revert_puts_the_earlier_text_back_through_approval(self):
        req = self.pending()
        self.review(req, "approve")
        edit = SectionEdit.objects.get()

        boss = self.as_user(self.superuser)
        boss.post(reverse("data_quality_center:revert", args=[edit.pk]), {"reason": "Approved by mistake, restoring."})
        revert = SectionEditRequest.objects.get(reverts=edit)
        self.assertEqual(revert.status, SectionEditRequest.STATUS_PENDING)
        self.assertEqual((revert.after_fa, revert.after_en), ("", ""))
        self.assertEqual(revert.events.get().action, ReviewEvent.REVERT_REQUESTED)

        self.review(revert, "approve")
        self.section.refresh_from_db()
        self.assertEqual((self.section.summary_fa, self.section.summary_en), ("", ""))
        self.assertEqual(SectionEdit.objects.count(), 2)

    def test_operator_cannot_revert(self):
        req = self.pending()
        self.review(req, "approve")
        edit = SectionEdit.objects.get()
        self.client.post(reverse("data_quality_center:revert", args=[edit.pk]), {"reason": "Restoring the old text."})
        self.assertFalse(SectionEditRequest.objects.filter(reverts=edit).exists())

    def test_events_are_append_only(self):
        req = self.pending()
        event = req.events.get()
        event.note = "rewritten"
        with self.assertRaises(ValueError):
            event.save()


class CheckTests(TestCase):
    def test_numbers_are_compared_with_the_source(self):
        raw = "Give 2.5 mg twice daily, up to 1,000 mg."
        self.assertEqual(numbers_missing_from_source(raw, "۲٫۵ میلی‌گرم دو بار در روز", "1000 mg max"), [])
        self.assertEqual(numbers_missing_from_source(raw, "5 mg"), ["5"])

    def test_one_language_changed_is_flagged(self):
        results = run_checks("Take 50 mg.", "قبلی", "جدید", "Old text", "Old text")
        self.assertIn("sync", [r["key"] for r in results if r["level"] == "warn"])

    def test_word_diff_marks_added_and_removed_words(self):
        html, added, removed = word_diff("take 50 mg daily", "take 75 mg daily <b>")
        self.assertIn("<del>50</del>", html)
        self.assertIn("<ins>75</ins>", html)
        self.assertIn("&lt;b&gt;", html)
        self.assertEqual((added, removed), (2, 1))


class RoleWorkflowTests(ConsoleTestCase):
    def role_user(self, key):
        user = get_user_model().objects.create_user(key, password="pass-123456")
        RoleAssignment.objects.create(user=user, role=Role.objects.get(key=key))
        return user

    def test_reviewer_can_submit_review_and_request_changes_but_cannot_apply(self):
        reviewer = self.role_user(Role.DATA_QUALITY_REVIEWER)
        client = self.as_user(reviewer)
        self.submit(client=client)
        req = SectionEditRequest.objects.get()
        page = client.get(reverse("data_quality_center:review"))
        self.assertEqual(page.status_code, 200)
        self.assertNotContains(page, 'name="action" value="approve"')
        self.review(req, "approve", user=reviewer)
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_PENDING)
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_en, "")
        self.assertFalse(SectionEdit.objects.exists())
        with self.assertRaises(WorkflowError):
            services.approve(req, reviewer)
        self.review(req, "changes", "Correct the units.", user=reviewer)
        req.refresh_from_db()
        self.assertEqual(req.status, SectionEditRequest.STATUS_CHANGES_REQUESTED)

    def test_approver_can_apply_without_django_staff_or_superuser_flags(self):
        self.submit()
        req = SectionEditRequest.objects.get()
        approver = self.role_user(Role.DATA_QUALITY_APPROVER)
        page = self.as_user(approver).get(reverse("data_quality_center:review"))
        self.assertContains(page, 'name="action" value="approve"')
        self.review(req, "approve", user=approver)
        self.section.refresh_from_db()
        self.assertEqual(self.section.summary_en, EN)
        self.assertEqual(SectionEdit.objects.get().approved_by, approver)

    def test_view_permission_is_read_only_and_does_not_allow_mutations(self):
        from django.contrib.auth.models import Permission

        viewer = get_user_model().objects.create_user("viewer", password="pass-123456")
        viewer.user_permissions.add(Permission.objects.get(content_type__app_label="accounts", codename="view_data_quality_center"))
        client = self.as_user(viewer)
        page = client.get(reverse("data_quality_center:workspace", args=[self.ingredient.slug]))
        self.assertEqual(page.status_code, 200)
        self.assertEqual(page.context["mode"], "readonly")
        self.assertNotContains(page, 'id="submit-btn"')
        response = self.save_draft(client=client)
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SectionEditRequest.objects.exists())
        with self.assertRaises(WorkflowError):
            services.save_draft(self.section, viewer, summary_fa=FA, summary_en=EN, reason=REASON)

    def test_role_revocation_blocks_service_mutations_with_the_same_user_object(self):
        reviewer = self.role_user(Role.DATA_QUALITY_REVIEWER)
        req = services.save_draft(self.section, reviewer, summary_fa=FA, summary_en=EN, reason=REASON)
        RoleAssignment.objects.filter(user=reviewer).update(revoked_at=timezone.now())
        for action in (services.submit, services.discard):
            with self.assertRaises(WorkflowError):
                action(req, reviewer)

    def test_inactive_superuser_cannot_apply_through_workflow(self):
        self.submit()
        req = SectionEditRequest.objects.get()
        self.superuser.is_active = False
        with self.assertRaises(WorkflowError):
            services.approve(req, self.superuser)


class WholeDrugAndSourcesTests(ConsoleTestCase):
    def publish(self):
        self.section.summary_fa = FA
        self.section.summary_en = EN
        self.section.save()

    def confirm(self, *, user=None, version=None):
        return self.as_user(user or self.superuser).post(
            reverse("data_quality_center:confirm_drug_review", args=[self.ingredient.slug]),
            {"version": version if version is not None else services.drug_review_version(self.ingredient)},
        )

    def test_filled_summaries_are_unreviewed_until_whole_drug_confirmation(self):
        self.publish()
        self.assertFalse(self.ingredient.is_reviewed)
        response = self.client.get(reverse("data_quality_center:queue"))
        self.assertContains(response, 'data-drug-reviewed="false"')
        self.confirm()
        self.ingredient.refresh_from_db()
        self.assertTrue(self.ingredient.is_reviewed)
        self.assertEqual(self.ingredient.reviewed_by_username, self.superuser.username)
        self.assertEqual(DrugReview.objects.count(), 1)
        self.confirm()
        self.assertEqual(DrugReview.objects.count(), 1)  # double click is harmless
        response = self.client.get(reverse("data_quality_center:queue"), {"show": "reviewed"})
        self.assertContains(response, 'data-drug-reviewed="true"')
        response = self.client.get(reverse("data_quality_center:queue"), {"show": "unreviewed"})
        self.assertEqual(response.context["page"].paginator.count, 0)

    def test_approving_one_section_does_not_mark_the_whole_drug_reviewed(self):
        self.submit()
        self.review(SectionEditRequest.objects.get(), "approve")
        self.ingredient.refresh_from_db()
        self.assertFalse(self.ingredient.is_reviewed)

    def test_operator_cannot_confirm_or_see_the_confirmation_button(self):
        self.publish()
        page = self.client.get(reverse("data_quality_center:workspace", args=[self.ingredient.slug]))
        self.assertNotContains(page, "تأیید بازبینی دارو")
        self.confirm(user=self.staff)
        self.assertFalse(DrugReview.objects.exists())
        with self.assertRaises(WorkflowError):
            services.confirm_drug_review(self.ingredient, self.staff, services.drug_review_version(self.ingredient))

    def test_assigned_approver_can_confirm_without_django_staff_flags(self):
        self.publish()
        approver = get_user_model().objects.create_user("drug-approver", password="pass-123456")
        RoleAssignment.objects.create(user=approver, role=Role.objects.get(key=Role.DATA_QUALITY_APPROVER))
        page = self.as_user(approver).get(reverse("data_quality_center:workspace", args=[self.ingredient.slug]))
        self.assertContains(page, "تأیید بازبینی دارو")
        self.confirm(user=approver)
        self.ingredient.refresh_from_db()
        self.assertTrue(self.ingredient.is_reviewed)
        self.assertEqual(DrugReview.objects.get().reviewer, approver)

    def test_confirmation_refuses_empty_pending_or_stale_content(self):
        self.confirm()
        self.assertFalse(DrugReview.objects.exists())
        self.publish()
        old_version = services.drug_review_version(self.ingredient)
        self.section.other_sources_fa = "اطلاعات تکمیلی آزمایشی"
        self.section.save()
        self.confirm(version=old_version)
        self.assertFalse(DrugReview.objects.exists())
        self.submit(summary_en="Changed text.")
        self.confirm()
        self.assertFalse(DrugReview.objects.exists())

    def test_published_changes_and_deleted_sections_require_a_new_review(self):
        self.publish()
        extra = IngredientProfileSection.objects.create(ingredient=self.ingredient, field="warnings", summary_en="Sample text.")
        self.confirm()
        self.section.other_sources_en = "New supplementary content."
        self.section.save()
        self.ingredient.refresh_from_db()
        self.assertFalse(self.ingredient.is_reviewed)
        self.confirm()
        self.ingredient.refresh_from_db()
        self.assertTrue(self.ingredient.is_reviewed)
        extra.delete()
        self.ingredient.refresh_from_db()
        self.assertFalse(self.ingredient.is_reviewed)

    @override_settings(ROOT_URLCONF="config.urls")
    def test_other_sources_are_hidden_until_approved_and_can_be_removed(self):
        from rest_framework.test import APIClient

        api = APIClient()
        api.force_authenticate(self.staff)
        url = f"/api/v1/lessons/drugs/{self.ingredient.slug}/"
        self.submit(other_sources_fa="اطلاعات تکمیلی آزمایشی", other_sources_en="Supplementary preview content.")
        self.assertEqual(api.get(url).data["lesson_sections"], [])
        req = SectionEditRequest.objects.get()
        page = self.as_user(self.superuser).get(reverse("data_quality_center:review"))
        self.assertContains(page, "اطلاعات تکمیلی آزمایشی")
        self.review(req, "approve")
        drug = api.get(url).data
        self.assertFalse(drug["is_reviewed"])
        self.assertEqual(drug["lesson_sections"][0]["other_sources_fa"], "اطلاعات تکمیلی آزمایشی")
        self.confirm()
        self.assertTrue(api.get(url).data["is_reviewed"])
        self.submit(other_sources_fa="", other_sources_en="")
        req = SectionEditRequest.objects.get(status=SectionEditRequest.STATUS_PENDING)
        self.review(req, "approve")
        drug = api.get(url).data
        self.assertFalse(drug["is_reviewed"])
        self.assertNotIn("other_sources_fa", drug["lesson_sections"][0])
        self.assertNotIn("other_sources_en", drug["lesson_sections"][0])

    def test_other_sources_only_change_can_be_approved_and_reverted(self):
        self.publish()
        self.submit(other_sources_fa="اطلاعات تکمیلی", other_sources_en="Additional source text.")
        req = SectionEditRequest.objects.get()
        self.review(req, "approve")
        edit = SectionEdit.objects.get()
        self.assertEqual(edit.after_other_sources_en, "Additional source text.")
        revert = services.start_revert(edit, self.superuser, "Restoring the previous published content.")
        services.approve(revert, self.superuser)
        self.section.refresh_from_db()
        self.assertEqual(self.section.other_sources_en, "")
        self.assertEqual(self.section.summary_en, EN)

    def test_other_source_drift_blocks_approval_and_old_clients_preserve_additions(self):
        self.publish()
        self.section.other_sources_en = "Published extra text."
        self.section.save()
        self.submit(summary_en="Proposed changed summary.")
        req = SectionEditRequest.objects.get()
        self.assertEqual(req.after_other_sources_en, "Published extra text.")
        self.section.other_sources_en = "Changed independently."
        self.section.save()
        with self.assertRaises(WorkflowError):
            services.approve(req, self.superuser)
        self.assertFalse(SectionEdit.objects.exists())

    def test_reviewer_history_survives_account_deletion_and_is_append_only(self):
        self.publish()
        self.confirm()
        row = DrugReview.objects.get()
        with self.assertRaises(ValueError):
            row.save()
        self.superuser.delete()
        row.refresh_from_db()
        self.assertIsNone(row.reviewer)
        self.assertEqual(row.reviewer_username, "boss")
        self.ingredient.refresh_from_db()
        self.assertTrue(self.ingredient.is_reviewed)
