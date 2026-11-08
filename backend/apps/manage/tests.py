from datetime import timedelta

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import Client, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import LearnerProfile, Role, RoleAssignment, SecurityAuditEvent, UserSession
from apps.accounts.services import issue_user_session
from apps.billing.models import AdminAction, Entitlement, Order, Plan
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

    def test_superuser_login_replaces_oldest_session_when_two_devices_are_active(self):
        user = make("root", superuser=True)
        first = issue_user_session(user)
        second = issue_user_session(user)
        response = self.client.post(reverse("manage:login"), {
            "identifier": user.username, "password": "pw-12345-x",
        }, REMOTE_ADDR="198.51.100.8")
        self.assertRedirects(response, reverse("manage:home"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("manage:home"), REMOTE_ADDR="198.51.100.8").status_code, 200)
        first.session.refresh_from_db()
        second.session.refresh_from_db()
        self.assertEqual(first.session.revoke_reason, "session_limit_replaced")
        self.assertTrue(second.session.is_active)
        current = UserSession.objects.get(pk=self.client.session["tracked_session_id"])
        self.assertEqual((current.surface, current.ip_address), ("manage", "198.51.100.8"))
        self.assertEqual(UserSession.objects.filter(user=user, revoked_at=None).count(), 2)

    def test_replaced_cookie_does_not_block_posting_valid_login_credentials(self):
        user = make("root", superuser=True)
        self.client.force_login(user)
        record = UserSession.objects.get(user=user)
        UserSession.objects.filter(pk=record.pk).update(revoked_at=timezone.now())
        response = self.sign_in(user.username)
        self.assertRedirects(response, reverse("manage:home"), fetch_redirect_response=False)
        self.assertEqual(self.client.get(reverse("manage:home")).status_code, 200)

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
        self.assertEqual(rail, ["home", "sales", "app", "site"])
        self.assertContains(res, reverse("support_admin:inbox"))
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


class PlatformRoleAccessTests(SiteTestCase):
    """Grant through the actual console, then sign in without Django flags."""

    def setUp(self):
        super().setUp()
        caches["throttle"].clear()
        self.addCleanup(caches["throttle"].clear)
        self.root = make("role-owner", superuser=True)
        self.client.force_login(self.root)

    def grant(self, user, key, op="assign"):
        response = self.client.post(reverse("console:user_role", args=[user.pk]), {"role": key, "op": op})
        self.assertEqual(response.status_code, 302)

    def sign_in(self, user):
        client = Client()
        response = client.post(reverse("manage:login"), {"identifier": user.username, "password": "pw-12345-x"})
        self.assertRedirects(response, reverse("manage:home"), fetch_redirect_response=False)
        return client

    def test_each_administrative_role_opens_all_its_visible_services(self):
        expected = {
            Role.CONTENT_EDITOR: {"site", "data"},
            Role.MEDICAL_REVIEWER: {"data"},
            Role.DATA_QUALITY_REVIEWER: {"data"},
            Role.DATA_QUALITY_APPROVER: {"data"},
            Role.SUPPORT_AGENT: {"app", "site"},
            Role.BILLING_ADMIN: {"users", "sales"},
            Role.PLATFORM_ADMIN: {"users", "sales", "app", "site", "data", "system"},
        }
        for key, required_modules in expected.items():
            with self.subTest(role=key):
                user = make(key)
                self.grant(user, key)
                user.refresh_from_db()
                self.assertFalse(user.is_staff)
                self.assertFalse(user.is_superuser)
                client = self.sign_in(user)
                home = client.get(reverse("manage:home"))
                self.assertEqual(home.status_code, 200)
                modules = home.context["mg"]["modules"]
                self.assertTrue(required_modules.issubset({m["key"] for m in modules}))
                for module in modules:
                    for page in module["pages"]:
                        self.assertFalse(page["external"], (key, page["url"]))
                        response = client.get(page["url"])
                        self.assertEqual(response.status_code, 200, (key, page["url"]))

    def test_learning_roles_do_not_grant_management_access(self):
        for key in (Role.LEARNER, Role.VERIFIED_PROFESSIONAL):
            user = make(key)
            self.grant(user, key)
            response = Client().post(reverse("manage:login"), {"identifier": user.username, "password": "pw-12345-x"})
            self.assertContains(response, "به مدیریت دسترسی ندارد")

    def test_custom_role_uses_its_quality_permission_without_a_known_role_key(self):
        from django.contrib.auth.models import Permission

        role = Role.objects.create(key="quality_observer", name="Quality observer", is_system=False)
        role.permissions.add(Permission.objects.get(content_type__app_label="accounts", codename="view_data_quality_center"))
        user = make("observer")
        self.grant(user, role.key)
        client = self.sign_in(user)
        home = client.get(reverse("manage:home"))
        pages = {page["key"] for module in home.context["mg"]["modules"] for page in module["pages"]}
        self.assertIn("queue", pages)
        self.assertNotIn("review", pages)
        self.assertNotIn("users", pages)
        self.assertEqual(client.get(reverse("data_quality_center:queue")).status_code, 200)
        self.grant(user, role.key, op="revoke")
        self.assertEqual(client.get(reverse("manage:home")).status_code, 302)

    def test_revoking_a_role_blocks_existing_sessions_and_can_be_reassigned(self):
        for key, endpoint in (
            (Role.DATA_QUALITY_REVIEWER, "data_quality_center:queue"),
            (Role.CONTENT_EDITOR, "panel:posts"),
            (Role.SUPPORT_AGENT, "support_admin:inbox"),
            (Role.BILLING_ADMIN, "console:plans"),
            (Role.PLATFORM_ADMIN, "manage:devices"),
        ):
            with self.subTest(role=key):
                user = make(key)
                self.grant(user, key)
                client = self.sign_in(user)
                self.assertEqual(client.get(reverse(endpoint)).status_code, 200)
                self.grant(user, key, op="revoke")
                self.assertNotEqual(client.get(reverse(endpoint)).status_code, 200)
                self.assertEqual(client.get(reverse("manage:home")).status_code, 302)
                self.grant(user, key)
                self.assertEqual(client.get(reverse(endpoint)).status_code, 200)

    def test_expired_roles_neither_sign_in_nor_appear_active(self):
        user = make("expired-reviewer")
        self.grant(user, Role.DATA_QUALITY_REVIEWER)
        now = timezone.now()
        RoleAssignment.objects.filter(user=user).update(created_at=now - timedelta(days=2), expires_at=now - timedelta(days=1))
        response = Client().post(reverse("manage:login"), {"identifier": user.username, "password": "pw-12345-x"})
        self.assertContains(response, "به مدیریت دسترسی ندارد")
        response = self.client.get(reverse("console:user", args=[user.pk]))
        self.assertEqual(response.context["roles_active"], [])

    def test_billing_admin_cannot_delegate_roles_or_change_platform_settings(self):
        user = make("billing")
        target = make("customer")
        self.grant(user, Role.BILLING_ADMIN)
        client = self.sign_in(user)
        response = client.get(reverse("console:user", args=[target.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'id="roles"')
        self.assertNotContains(response, 'id="delete"')
        drawer = client.get(reverse("console:users"), {"u": target.pk})
        self.assertEqual(drawer.status_code, 200)
        self.assertNotContains(drawer, reverse("console:user_block", args=[target.pk]))
        plan = Plan.objects.create(slug="billing-role-plan", name_fa="پلن آزمایشی نقش", is_free=False)
        response = client.post(reverse("console:user_grant", args=[target.pk]), {"plan": plan.pk, "days": "30"})
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Entitlement.objects.filter(user=target, plan=plan, granted_by=user).exists())
        for endpoint in ("user_role", "user_block", "user_logout_all", "user_delete"):
            response = client.post(reverse(f"console:{endpoint}", args=[target.pk]), {"role": Role.PLATFORM_ADMIN})
            self.assertEqual(response.status_code, 403, endpoint)
        for endpoint in ("console:access", "console:rate_limits", "manage:devices", "manage:usage", "app_admin:announcements", "panel:settings"):
            self.assertNotEqual(client.get(reverse(endpoint)).status_code, 200, endpoint)
        self.assertFalse(RoleAssignment.objects.filter(user=target).exists())

    def test_site_and_platform_role_permissions_are_combined(self):
        from apps.support.services import can_support
        from apps.website.permissions import can

        user = make("combined", role=StaffRole.SUPPORT)
        self.grant(user, Role.CONTENT_EDITOR)
        self.assertTrue(can(user, "post.publish"))
        self.assertTrue(can_support(user))
        self.grant(user, Role.CONTENT_EDITOR, op="revoke")
        self.assertFalse(can(user, "post.publish"))
        self.assertTrue(can_support(user))
