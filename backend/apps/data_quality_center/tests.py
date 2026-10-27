from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.accounts.models import SecurityAuditEvent
from apps.drugs.models import Ingredient, IngredientProfileSection

from . import services
from .checks import numbers_missing_from_source, run_checks, word_diff
from .models import ReviewEvent, SectionEdit, SectionEditRequest
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
        client = Client()
        client.force_login(user)
        return client

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
