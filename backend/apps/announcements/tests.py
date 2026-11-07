from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from apps.billing.models import AdminAction, Entitlement, Plan

from .models import AnnouncementReceipt, AppAnnouncement

User = get_user_model()


def make(title="نسخهٔ تازه", **kw):
    kw.setdefault("body", "متن")
    kw.setdefault("is_published", True)
    return AppAnnouncement.objects.create(title=title, **kw)


class FeedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("learner", password="x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def feed(self, **params):
        res = self.client.get(reverse("announcements"), params)
        self.assertEqual(res.status_code, 200)
        return res.json()

    def titles(self, **params):
        return [a["title"] for a in self.feed(**params)]

    def test_only_published_ones_in_their_window(self):
        now = timezone.now()
        make("حالا")
        make("پیش‌نویس", is_published=False)
        make("بعداً", starts_at=now + timedelta(hours=2))
        make("گذشته", ends_at=now - timedelta(minutes=1))
        make("تا فردا", ends_at=now + timedelta(days=1))
        self.assertEqual(sorted(self.titles()), ["تا فردا", "حالا"])

    def test_pinned_first_then_newest(self):
        now = timezone.now()
        make("قدیمی", starts_at=now - timedelta(days=2))
        make("تازه", starts_at=now - timedelta(hours=1))
        make("سنجاق", starts_at=now - timedelta(days=5), is_pinned=True)
        self.assertEqual(self.titles(), ["سنجاق", "تازه", "قدیمی"])

    def test_audiences(self):
        make("همه")
        make("رایگان", audience=AppAnnouncement.AUDIENCE_FREE)
        make("مشترک", audience=AppAnnouncement.AUDIENCE_SUBSCRIBERS)
        make("نسخهٔ قدیمی", audience=AppAnnouncement.AUDIENCE_OLD_APP, below_version="0.2.0")
        self.assertEqual(sorted(self.titles()), ["رایگان", "همه"])
        self.assertIn("نسخهٔ قدیمی", self.titles(version_code=100))  # 0.1.0
        self.assertNotIn("نسخهٔ قدیمی", self.titles(version_code=200))  # 0.2.0
        plan = Plan.objects.create(slug="pro", name_fa="حرفه‌ای")
        Entitlement.objects.create(user=self.user, plan=plan, source=Entitlement.SOURCE_ADMIN, ends_at=timezone.now() + timedelta(days=30))
        self.assertEqual(sorted(self.titles()), ["مشترک", "همه"])

    def test_the_button_and_what_the_app_needs(self):
        make("وب", cta_label="دریافت", link_kind="url", link_url="https://pharmenta.ir/download/")
        make("اپ", cta_label="باز کردن", link_kind="app", link_screen="lesson", link_param="B01", dismissible=False)
        make("بی‌دکمه")
        rows = {a["title"]: a for a in self.feed()}
        self.assertEqual(rows["وب"]["button"], {"label": "دریافت", "kind": "url", "url": "https://pharmenta.ir/download/", "screen": "", "param": ""})
        self.assertEqual(rows["اپ"]["button"]["screen"], "lesson")
        self.assertFalse(rows["اپ"]["dismissible"])
        self.assertIsNone(rows["بی‌دکمه"]["button"])
        self.assertFalse(rows["وب"]["seen"])

    def test_seen_click_and_dismiss(self):
        item = make()
        url = reverse("announcement-event", args=[item.pk])
        self.assertEqual(self.client.post(url, {"event": "seen"}, format="json").status_code, 204)
        self.assertTrue(self.feed()[0]["seen"])
        self.client.post(url, {"event": "click"}, format="json")
        self.client.post(url, {"event": "dismiss"}, format="json")
        self.assertEqual(self.feed(), [])
        receipt = AnnouncementReceipt.objects.get()
        self.assertTrue(receipt.seen_at and receipt.clicked_at and receipt.dismissed_at)
        self.assertEqual(self.client.post(url, {"event": "nope"}, format="json").status_code, 400)

    def test_a_notice_that_cannot_be_closed_stays(self):
        item = make(dismissible=False)
        self.client.post(reverse("announcement-event", args=[item.pk]), {"event": "dismiss"}, format="json")
        self.assertEqual(len(self.feed()), 1)

    def test_a_draft_shows_only_on_the_testers_phone(self):
        make("آزمایشی", is_published=False, test_user=self.user)
        rows = self.feed()
        self.assertEqual([r["title"] for r in rows], ["آزمایشی"])
        self.assertTrue(rows[0]["is_test"])
        other = APIClient()
        other.force_authenticate(User.objects.create_user("other", password="x"))
        self.assertEqual(other.get(reverse("announcements")).json(), [])

    def test_needs_sign_in(self):
        self.assertEqual(APIClient().get(reverse("announcements")).status_code, 401)

    def test_install_only_reaches_uninstalled_web_clients_including_drafts(self):
        make("نصب", link_kind="pwa", audience="web_new")
        make("آزمایش نصب", link_kind="pwa", is_published=False, test_user=self.user)
        make("خبر عادی")
        self.assertEqual(self.titles(), ["خبر عادی"])
        for state in ("native", "standalone", "unknown"):
            self.assertEqual(self.titles(pwa_state=state), ["خبر عادی"])
        self.assertCountEqual(self.titles(pwa_state="browser"), ["نصب", "آزمایش نصب", "خبر عادی"])
        install = next(r for r in self.feed(pwa_state="browser") if r["title"] == "نصب")
        self.assertEqual(install["button"]["kind"], "pwa")
        self.assertEqual(install["button"]["label"], "نصب")

    def test_install_dismissal_is_per_account_and_survives_editing_and_login(self):
        item = make(link_kind="pwa", dismissible=False)
        url = reverse("announcement-event", args=[item.pk])
        self.assertEqual(self.client.post(url, {"event": "click"}).status_code, 204)
        self.assertEqual(len(self.feed(pwa_state="browser")), 1)  # cancelling install must not hide it
        self.assertEqual(self.client.post(url, {"event": "dismiss"}).status_code, 204)
        item.body = "متن ویرایش‌شده"
        item.save()
        fresh_client = APIClient()
        fresh_client.force_authenticate(self.user)
        self.assertEqual(fresh_client.get(reverse("announcements"), {"pwa_state": "browser"}).json(), [])
        other = User.objects.create_user("another", password="x")
        fresh_client.force_authenticate(other)
        self.assertEqual(len(fresh_client.get(reverse("announcements"), {"pwa_state": "browser"}).json()), 1)
        self.assertTrue(AnnouncementReceipt.objects.get(user=self.user, announcement=item).dismissed_at)


class AdminTests(TestCase):
    def setUp(self):
        self.root = User.objects.create_superuser("root", "r@e.com", "pw-123456")
        self.client.force_login(self.root)

    def payload(self, **kw):
        data = {"title": "نسخهٔ تازه آماده است", "body": "برای دریافت بزن.", "kind": "update", "link_kind": "", "audience": "all",
                "starts_at": "", "ends_at": "", "dismissible": "on"}
        data.update(kw)
        return data

    def test_write_publish_and_end(self):
        res = self.client.post(reverse("app_admin:announcement_new"), self.payload(
            action="publish", link_kind="url", cta_label="دریافت", link_url="https://pharmenta.ir/download/",
        ))
        item = AppAnnouncement.objects.get()
        self.assertRedirects(res, reverse("app_admin:announcement", args=[item.pk]), fetch_redirect_response=False)
        self.assertEqual((item.state, item.created_by, item.link_kind), ("active", self.root, "url"))
        self.assertTrue(AdminAction.objects.filter(action="announcement_publish").exists())
        page = self.client.get(reverse("app_admin:announcement", args=[item.pk]))
        self.assertContains(page, "نسخهٔ تازه آماده است")
        self.assertContains(page, "تمام کن")
        self.client.post(reverse("app_admin:announcement_action", args=[item.pk]), {"action": "end"})
        item.refresh_from_db()
        self.assertEqual(item.state, "ended")

    def test_checks_the_button_audience_and_dates(self):
        res = self.client.post(reverse("app_admin:announcement_new"), self.payload(
            action="save", link_kind="url", cta_label="", link_url="ftp://x",
            audience="old_app", below_version="new", starts_at="۱۴۰۵/۰۸/۱۰ ۱۰:۰۰", ends_at="۱۴۰۵/۰۸/۰۱ ۱۰:۰۰",
        ))
        self.assertEqual(res.status_code, 200)
        for text in ("دکمه متن لازم دارد", "https://", "0.2.0", "پایان باید بعد از شروع باشد"):
            self.assertContains(res, text)
        res = self.client.post(reverse("app_admin:announcement_new"), self.payload(action="save", link_kind="app", cta_label="باز کن", link_screen="lesson", link_param=""))
        self.assertContains(res, "کد ATC گروه را بنویسید")
        self.assertFalse(AppAnnouncement.objects.exists())

    def test_test_on_my_phone_keeps_it_a_draft(self):
        self.client.post(reverse("app_admin:announcement_new"), self.payload(action="test"))
        item = AppAnnouncement.objects.get()
        self.assertEqual((item.is_published, item.test_user), (False, self.root))

    def test_delete_and_figures(self):
        item = make()
        learner = User.objects.create_user("learner", password="x")
        AnnouncementReceipt.objects.create(announcement=item, user=learner, seen_at=timezone.now(), clicked_at=timezone.now())
        page = self.client.get(reverse("app_admin:announcements"))
        self.assertContains(page, "۱ دیدند · ۱ زدند")
        self.client.post(reverse("app_admin:announcement_action", args=[item.pk]), {"action": "delete"})
        self.assertFalse(AppAnnouncement.objects.exists())

    def test_only_superusers(self):
        staff = User.objects.create_user("staff", password="x", is_staff=True)
        self.client.force_login(staff)
        self.assertEqual(self.client.get(reverse("app_admin:announcements")).status_code, 302)

    def test_install_action_sets_audience_and_permanent_dismissal_without_custom_url(self):
        self.client.post(reverse("app_admin:announcement_new"), self.payload(
            action="publish", link_kind="pwa", cta_label="", audience="all", dismissible="",
            link_url="https://example.com", link_screen="quiz", link_param="anything",
        ))
        item = AppAnnouncement.objects.get()
        self.assertEqual((item.link_kind, item.cta_label, item.audience, item.dismissible), ("pwa", "نصب", "web_new", True))
        self.assertEqual((item.link_url, item.link_screen, item.link_param), ("", "", ""))
        page = self.client.get(reverse("app_admin:announcement", args=[item.pk]))
        self.assertContains(page, "نصب وب‌اپ (PWA)")
        self.assertContains(page, "دیگر نشان نده")
