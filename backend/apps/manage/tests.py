from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import LearnerProfile, SecurityAuditEvent
from apps.billing.models import AdminAction, Order, Plan
from apps.drugs.models import Ingredient
from apps.website.models import ActivityLog, Comment, ContactMessage, Media, Post, StaffRole
from apps.website.tests.base import SiteTestCase

User = get_user_model()
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64


def make(username, *, superuser=False, staff=False, role=None):
    user = User.objects.create_user(username=username, password="pw-12345-x", is_superuser=superuser,
                                    is_staff=staff or superuser)
    if role:
        StaffRole.objects.create(user=user, role=role)
    return user


class SignInTests(SiteTestCase):
    def setUp(self):
        super().setUp()
        self.addCleanup(caches["throttle"].clear)

    def sign_in(self, identifier, password="pw-12345-x", **extra):
        return self.client.post(reverse("manage:login"), {"identifier": identifier, "password": password, **extra})

    def test_every_kind_of_admin_signs_in_and_it_is_audited(self):
        for name, kw in (("root", {"superuser": True}), ("desk", {"staff": True}), ("ed", {"role": StaffRole.EDITOR})):
            user = make(name, **kw)
            client = Client()
            res = client.post(reverse("manage:login"), {"identifier": name, "password": "pw-12345-x"})
            self.assertRedirects(res, reverse("manage:home"), fetch_redirect_response=False)
            self.assertEqual(client.get(reverse("manage:home")).status_code, 200, name)
            self.assertTrue(SecurityAuditEvent.objects.filter(user=user, event_type=SecurityAuditEvent.LOGIN_SUCCEEDED).exists())

    def test_a_phone_number_signs_in_too(self):
        user = make("ed", role=StaffRole.EDITOR)
        LearnerProfile.objects.create(user=user, phone="09121234567")
        self.assertEqual(self.sign_in("09121234567").status_code, 302)

    def test_a_learner_is_refused(self):
        make("plain")
        res = self.sign_in("plain")
        self.assertContains(res, "به مدیریت دسترسی ندارد")
        self.assertEqual(self.client.get(reverse("manage:home")).status_code, 302)

    def test_next_must_stay_on_this_host(self):
        make("root", superuser=True)
        self.assertEqual(self.sign_in("root", next="https://evil.example/")["Location"], reverse("manage:home"))
        self.assertEqual(self.sign_in("root", next="/manage/activity/")["Location"], "/manage/activity/")

    def test_failures_lock_by_the_unforgeable_address(self):
        make("root", superuser=True)
        for i in range(8):
            self.client.post(reverse("manage:login"), {"identifier": "root", "password": "bad"},
                             HTTP_X_FORWARDED_FOR=f"10.0.0.{i}, 203.0.113.9")
        res = self.client.post(reverse("manage:login"), {"identifier": "root", "password": "pw-12345-x"},
                               HTTP_X_FORWARDED_FOR="10.9.9.9, 203.0.113.9")
        self.assertContains(res, "تلاش‌های ناموفق زیاد بود")

    def test_sign_out_needs_post(self):
        self.client.force_login(make("root", superuser=True))
        self.assertEqual(self.client.get(reverse("manage:logout")).status_code, 405)
        self.assertRedirects(self.client.post(reverse("manage:logout")), reverse("manage:login"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("manage:home")).status_code, 302)

    def test_the_tools_old_sign_in_pages_send_here(self):
        for name in ("console:login", "panel:login", "data_quality_center:login"):
            res = self.client.get(reverse(name), {"next": "/manage/sales/plans/"})
            self.assertEqual(res["Location"], f"{reverse('manage:login')}?next=/manage/sales/plans/", name)


class NavigationTests(SiteTestCase):
    def rail(self, user):
        self.client.force_login(user)
        res = self.client.get(reverse("manage:home"))
        self.assertEqual(res.status_code, 200)
        return [m["key"] for m in res.context["mg"]["modules"]], res

    def test_each_role_sees_its_modules(self):
        rail, _ = self.rail(make("root", superuser=True))
        self.assertEqual(rail, ["home", "users", "sales", "app", "site", "data", "system"])
        rail, res = self.rail(make("desk", staff=True))
        self.assertEqual(rail, ["home", "data"])
        self.assertNotContains(res, reverse("console:plans"))
        rail, res = self.rail(make("help", role=StaffRole.SUPPORT))
        self.assertEqual(rail, ["home", "sales", "site"])
        self.assertNotContains(res, reverse("console:discounts"))

    def test_the_current_page_and_badges(self):
        self.client.force_login(make("root", superuser=True))
        post = Post.objects.create(title="یک مطلب", slug="one")
        Comment.objects.create(post=post, name="سارا", body="خوب بود")
        res = self.client.get(reverse("panel:comments"))
        mg = res.context["mg"]
        self.assertEqual(mg["module"]["key"], "site")
        self.assertEqual(mg["page"]["key"], "comments")
        self.assertEqual(mg["page"]["badge"], 1)
        self.assertEqual(self.client.get(reverse("console:plan_new")).context["mg"]["page"]["key"], "plans")

    def test_the_command_bar_offers_only_allowed_pages(self):
        self.client.force_login(make("help", role=StaffRole.SUPPORT))
        jump = self.client.get(reverse("manage:home")).context["mg"]["jump"]
        urls = {j["url"] for j in jump}
        self.assertIn(reverse("panel:comments"), urls)
        self.assertNotIn(reverse("panel:settings"), urls)
        self.assertNotIn(reverse("console:users"), urls)


class HomeTests(SiteTestCase):
    def test_triage_for_a_superuser(self):
        self.client.force_login(make("root", superuser=True))
        post = Post.objects.create(title="یک مطلب", slug="one")
        comment = Comment.objects.create(post=post, name="سارا", body="جدول دوزها کمک کرد")
        ContactMessage.objects.create(name="علی", message="آزمون قفل است")
        plan = Plan.objects.create(slug="pro", name_fa="حرفه‌ای")
        Order.objects.create(plan=plan, amount_toman=100, payable_toman=100, status=Order.STATUS_FAILED, gateway="zarinpal")
        res = self.client.get(reverse("manage:home"))
        self.assertContains(res, "جدول دوزها کمک کرد")
        self.assertContains(res, f"?one={comment.pk}")
        self.assertContains(res, "پیام تماس از علی")
        self.assertContains(res, "پرداخت ناموفق امروز")
        self.assertContains(res, "بخش‌ها در یک نگاه")

    def test_publishing_a_comment_from_home(self):
        self.client.force_login(make("root", superuser=True))
        post = Post.objects.create(title="یک مطلب", slug="one")
        comment = Comment.objects.create(post=post, name="سارا", body="خوب")
        home = reverse("manage:home")
        res = self.client.post(f"{reverse('panel:comment_action')}?one={comment.pk}", {"action": "approve"}, HTTP_REFERER=home)
        self.assertRedirects(res, home, fetch_redirect_response=False)
        comment.refresh_from_db()
        self.assertEqual(comment.status, Comment.APPROVED)

    def test_an_author_gets_a_calm_home(self):
        self.client.force_login(make("w", role=StaffRole.AUTHOR))
        res = self.client.get(reverse("manage:home"))
        self.assertContains(res, "کاری منتظر نیست")
        self.assertNotContains(res, "فروش و حساب‌ها")


class ActivityTests(SiteTestCase):
    def test_both_logs_merge_newest_first(self):
        root = make("root", superuser=True)
        ActivityLog.objects.create(user_label="ed", action="post_publish", object_type="Post", object_repr="مطلب الف")
        AdminAction.objects.create(actor=root, action="discount_create", summary="ساخت کد تخفیف TERM20")
        self.client.force_login(root)
        res = self.client.get(reverse("manage:activity"))
        self.assertContains(res, "مطلب الف")
        self.assertContains(res, "ساخت کد تخفیف TERM20")
        res = self.client.get(reverse("manage:activity"), {"source": "site"})
        self.assertNotContains(res, "TERM20")

    def test_a_site_admin_sees_only_the_site_log(self):
        AdminAction.objects.create(action="discount_create", summary="ساخت کد تخفیف TERM20")
        ActivityLog.objects.create(user_label="ed", action="post_publish", object_repr="مطلب الف")
        self.client.force_login(make("boss", role=StaffRole.ADMIN))
        res = self.client.get(reverse("manage:activity"))
        self.assertContains(res, "مطلب الف")
        self.assertNotContains(res, "TERM20")

    def test_others_may_not_open_it(self):
        self.client.force_login(make("desk", staff=True))
        self.assertEqual(self.client.get(reverse("manage:activity")).status_code, 403)


class SearchTests(SiteTestCase):
    def find(self, user, q):
        self.client.force_login(user)
        return self.client.get(reverse("manage:search"), {"q": q}).json()["results"]

    def test_a_superuser_finds_people_plans_and_drugs(self):
        learner = User.objects.create_user("learner")
        LearnerProfile.objects.create(user=learner, phone="09125550000")
        Plan.objects.create(slug="pro", name_fa="حرفه‌ای")
        Ingredient.objects.create(rxcui="1", name="warfarin", slug="warfarin-1")
        root = make("root", superuser=True)
        self.assertIn(reverse("console:user", args=[learner.pk]), [r["url"] for r in self.find(root, "۰۹۱۲۵۵۵")])
        self.assertEqual([r["type"] for r in self.find(root, "حرفه")], ["پلن"])
        self.assertIn("دارو", [r["type"] for r in self.find(root, "warf")])

    def test_support_finds_no_people_or_drugs(self):
        User.objects.create_user("learner09")
        Ingredient.objects.create(rxcui="1", name="learnerol", slug="learnerol-1")
        self.assertEqual(self.find(make("help", role=StaffRole.SUPPORT), "learner"), [])


@override_settings(MANAGE_PUBLIC_URL="https://api.example/manage")
class OldAddressTests(SiteTestCase):
    def test_ops_moves_under_manage(self):
        res = self.client.get("/ops/users/", {"q": "1"})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res["Location"], "/manage/sales/users/?q=1")
        self.assertEqual(self.client.get("/ops/data-quality/review/")["Location"], "/manage/data/review/")

    def test_the_sites_panel_and_ops_send_to_the_admin(self):
        site = {"HTTP_HOST": "site.localhost"}
        self.assertEqual(self.client.get("/panel/posts/", **site)["Location"], "https://api.example/manage/site/posts/")
        self.assertEqual(self.client.get("/ops/", **site)["Location"], "https://api.example/manage/sales/")


class MediaOnTheAdminHostTests(SiteTestCase):
    def test_the_panel_pictures_load_here(self):
        item = Media.objects.create(filename="a.png", content_type="image/png", size=len(PNG), sha256="a" * 64, data=PNG)
        res = self.client.get(item.url)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "image/png")


class ShellTests(SiteTestCase):
    def test_every_tool_page_wears_the_shell(self):
        self.client.force_login(make("root", superuser=True))
        for name in ("manage:home", "console:plans", "console:discounts", "panel:posts", "panel:dashboard", "data_quality_center:queue"):
            res = self.client.get(reverse(name))
            self.assertEqual(res.status_code, 200, name)
            self.assertContains(res, 'class="mg-rail"', msg_prefix=name)
            self.assertContains(res, 'id="mg-pal"', msg_prefix=name)

    def test_site_links_point_at_the_site(self):
        self.client.force_login(make("root", superuser=True))
        Post.objects.create(title="منتشرشده", slug="live", status=Post.PUBLISHED, published_at=timezone.now() - timedelta(days=1))
        res = self.client.get(reverse("panel:posts"))
        self.assertContains(res, f'{settings.SITE_PUBLIC_URL.rstrip("/")}/blog/live/')
