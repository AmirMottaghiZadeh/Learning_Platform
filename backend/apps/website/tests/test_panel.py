from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone

from apps.accounts.models import LearnerProfile
from apps.website.models import (
    ActivityLog, Announcement, Category, Comment, ContactMessage, Media, Page, Post, PostRevision, SiteSettings, StaffRole, Subscriber,
)

from .base import SiteTestCase

# The panel lives in the admin (apps.manage), on the API's host; the public
# site answers on its own.
HOST = {}
SITE = {"HTTP_HOST": "site.localhost"}
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 64
User = get_user_model()


def url(name, *args):
    return reverse(f"panel:{name}", args=args)


def sign_in(client, data):
    """The admin's one sign-in, which the panel's own sign-in page sends to."""
    return client.post(reverse("manage:login"), data)


def make_user(username, role=None, superuser=False):
    user = User.objects.create_user(username=username, password="pw-12345-x", is_superuser=superuser, is_staff=superuser)
    if role:
        StaffRole.objects.create(user=user, role=role)
    return user


class PanelCase(SiteTestCase):
    def login(self, user):
        self.client.force_login(user)

    def get(self, name, *args, **kw):
        return self.client.get(url(name, *args), **HOST, **kw)

    def post(self, name, data=None, *args, **kw):
        return self.client.post(url(name, *args), data or {}, **HOST, **kw)


class AuthTests(PanelCase):
    def test_anonymous_redirected_to_login(self):
        res = self.get("dashboard")
        self.assertEqual(res.status_code, 302)
        self.assertIn("/manage/login/", res["Location"])
        self.assertIn("/manage/login/", self.get("login")["Location"])

    def test_login_works_for_staff_with_phone(self):
        user = make_user("u1", StaffRole.EDITOR)
        LearnerProfile.objects.create(user=user, phone="09121234567")
        res = sign_in(self.client, {"identifier": "09121234567", "password": "pw-12345-x"})
        self.assertEqual(res.status_code, 302)
        self.assertEqual(self.get("dashboard").status_code, 200)

    def test_login_refused_without_a_role(self):
        make_user("plain")
        res = sign_in(self.client, {"identifier": "plain", "password": "pw-12345-x"})
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "دسترسی ندارد")
        self.assertEqual(self.get("dashboard").status_code, 302)

    def test_wrong_password_and_lockout(self):
        from django.core.cache import caches

        self.addCleanup(caches["throttle"].clear)
        make_user("u1", StaffRole.ADMIN)
        for _ in range(8):
            sign_in(self.client, {"identifier": "u1", "password": "bad"})
        res = sign_in(self.client, {"identifier": "u1", "password": "pw-12345-x"})
        self.assertContains(res, "تلاش‌های ناموفق زیاد")

    def test_next_redirect_stays_on_site(self):
        make_user("u1", StaffRole.ADMIN)
        res = sign_in(self.client, {"identifier": "u1", "password": "pw-12345-x", "next": "https://evil.com/"})
        self.assertEqual(res["Location"], reverse("manage:home"))

    def test_logout_needs_post(self):
        self.login(make_user("u1", StaffRole.ADMIN))
        self.assertEqual(self.get("logout").status_code, 405)
        self.assertEqual(self.post("logout").status_code, 302)


ALL_PAGES = [
    ("dashboard", ()), ("posts", ()), ("post_new", ()), ("media", ()), ("comments", ()), ("contact", ()), ("subscribers", ()),
    ("plans", ()), ("orders", ()), ("subscriptions", ()), ("stats", ()), ("seo", ()), ("settings", ()), ("staff", ()), ("activity", ()),
    ("categories", ()), ("categories_new", ()), ("tags", ()), ("pages", ()), ("pages_new", ()), ("announcements", ()), ("announcements_new", ()),
    ("releases", ()), ("releases_new", ()), ("links", ()), ("links_new", ()), ("menus", ()), ("menus_new", ()), ("blocks", ()), ("blocks_new", ()),
    ("redirects", ()), ("redirects_new", ()),
]


class PagesRenderTests(PanelCase):
    def test_every_page_renders_for_admin(self):
        self.login(make_user("a", StaffRole.ADMIN))
        # content to list
        cat = Category.objects.create(name="آموزش", slug="learn")
        post = Post.objects.create(title="مطلب", slug="m", status=Post.PUBLISHED, published_at=timezone.now(), category=cat, body_html="<p>x</p>")
        PostRevision.objects.create(post=post, title="مطلب", body_html="<p>x</p>")
        Comment.objects.create(post=post, name="ع", body="سلام همه")
        ContactMessage.objects.create(name="ر", message="پیام آزمایشی", email="a@b.ir")
        Subscriber.objects.create(email="s@b.ir")
        Page.objects.create(title="درباره", slug="about")
        Announcement.objects.create(title="خبر", slug="news")
        Media.objects.create(filename="a.png", content_type="image/png", size=len(PNG), sha256="a" * 64, data=PNG, title="تصویر")
        for name, args in ALL_PAGES:
            with self.subTest(page=name):
                self.assertEqual(self.get(name, *args).status_code, 200, name)
        self.assertEqual(self.get("post_edit", post.pk).status_code, 200)
        self.assertEqual(self.get("post_revisions", post.pk).status_code, 200)
        self.assertEqual(self.get("categories_edit", cat.pk).status_code, 200)
        self.assertEqual(self.get("media_edit", Media.objects.get().pk).status_code, 200)
        self.assertEqual(self.get("media_picker").status_code, 200)

    def test_pages_render_for_each_role(self):
        for role in (StaffRole.EDITOR, StaffRole.AUTHOR, StaffRole.SUPPORT):
            self.client.logout()
            self.login(make_user(f"u-{role}", role))
            self.assertEqual(self.get("dashboard").status_code, 200, role)

    def test_empty_dashboard_with_traffic(self):
        from apps.website.models import DailyStat

        self.login(make_user("a", StaffRole.ADMIN))
        for i in range(3):
            DailyStat.bump(DailyStat.VIEW, "/")
        DailyStat.bump(DailyStat.DOWNLOAD, "play")
        res = self.get("dashboard")
        self.assertContains(res, "نمودار بازدید")
        self.assertContains(res, "Google Play")


class PermissionTests(PanelCase):
    def test_support_cannot_open_posts_or_settings(self):
        self.login(make_user("s", StaffRole.SUPPORT))
        self.assertEqual(self.get("posts").status_code, 403)
        self.assertEqual(self.get("settings").status_code, 403)
        self.assertEqual(self.get("comments").status_code, 200)

    def test_editor_cannot_open_settings_or_staff(self):
        self.login(make_user("e", StaffRole.EDITOR))
        self.assertEqual(self.get("settings").status_code, 403)
        self.assertEqual(self.get("staff").status_code, 403)
        self.assertEqual(self.get("activity").status_code, 403)

    def test_nav_hides_what_a_role_cannot_use(self):
        self.login(make_user("s", StaffRole.SUPPORT))
        res = self.get("dashboard")
        self.assertNotContains(res, "تنظیمات")
        self.assertContains(res, "نظرات")


class PostTests(PanelCase):
    def setUp(self):
        super().setUp()
        self.editor = make_user("e", StaffRole.EDITOR)
        self.login(self.editor)

    def payload(self, **kw):
        data = {"title": "راهنمای تازه", "slug": "", "excerpt": "خلاصه", "body_html": "<h2>بخش</h2><p>متن <script>alert(1)</script>سالم</p>",
                "category": "", "status": Post.DRAFT, "allow_comments": "on", "tags_text": "ATC، لایتنر", "intent": "save"}
        data.update(kw)
        return data

    def test_create_cleans_html_and_makes_slug_tags_revision(self):
        res = self.post("post_new", self.payload())
        post = Post.objects.get()
        self.assertEqual(res.status_code, 302)
        self.assertNotIn("script", post.body_html)
        self.assertTrue(post.slug)
        self.assertEqual(sorted(post.tags.values_list("name", flat=True)), ["ATC", "لایتنر"])
        self.assertEqual(post.author, self.editor)
        self.assertEqual(post.revisions.count(), 1)

    def test_publish_intent_makes_it_public(self):
        self.post("post_new", self.payload(intent="publish"))
        post = Post.objects.get()
        self.assertEqual(post.status, Post.PUBLISHED)
        self.assertEqual(self.client.get(post.get_absolute_url(), **SITE).status_code, 200)

    def test_scheduling_needs_a_future_date(self):
        res = self.post("post_new", self.payload(status=Post.SCHEDULED, published_at="1300/01/01 10:00"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(Post.objects.count(), 0)

    def test_jalali_schedule_is_saved(self):
        from apps.billing import jalali

        future = timezone.localdate() + timedelta(days=5)
        jy, jm, jd = jalali.to_jalali(future)
        res = self.post("post_new", self.payload(status=Post.SCHEDULED, published_at=f"{jy}/{jm:02d}/{jd:02d} 09:30"))
        self.assertEqual(res.status_code, 302)
        post = Post.objects.get()
        self.assertEqual(post.status, Post.SCHEDULED)
        self.assertGreater(post.published_at, timezone.now())
        from django.test import Client

        self.assertEqual(Client().get(post.get_absolute_url(), **SITE).status_code, 404)
        # the admin is on another domain, so its preview link carries a signed token
        from apps.website import services

        path = post.get_absolute_url()
        self.assertEqual(Client().get(f"{path}?preview={services.preview_token(post)}", **SITE).status_code, 200)
        self.assertEqual(Client().get(f"{path}?preview=forged", **SITE).status_code, 404)
        self.assertTrue(services.post_link(post).startswith(services.absolute(path) + "?preview="))

    def test_editing_changes_creates_new_revision_only_when_text_changes(self):
        self.post("post_new", self.payload())
        post = Post.objects.get()
        self.post("post_edit", self.payload(slug=post.slug), post.pk)
        self.assertEqual(post.revisions.count(), 1)
        self.post("post_edit", self.payload(slug=post.slug, body_html="<p>چیز دیگر</p>"), post.pk)
        self.assertEqual(post.revisions.count(), 2)

    def test_restore_revision(self):
        self.post("post_new", self.payload(body_html="<p>اول</p>"))
        post = Post.objects.get()
        self.post("post_edit", self.payload(slug=post.slug, body_html="<p>دوم</p>"), post.pk)
        first = post.revisions.order_by("created_at").first()
        self.post("revision_restore", {}, post.pk, first.pk)
        post.refresh_from_db()
        self.assertIn("اول", post.body_html)

    def test_slug_unique(self):
        self.post("post_new", self.payload(title="عنوان یکسان"))
        self.post("post_new", self.payload(title="عنوان یکسان"))
        self.assertEqual(Post.objects.count(), 2)
        self.assertEqual(Post.objects.values("slug").distinct().count(), 2)

    def test_bulk_publish_and_delete(self):
        a = Post.objects.create(title="a", slug="a")
        b = Post.objects.create(title="b", slug="b")
        self.post("posts", {"bulk": "publish", "ids": [a.pk, b.pk]})
        self.assertEqual(Post.objects.filter(status=Post.PUBLISHED).count(), 2)
        self.post("posts", {"bulk": "delete", "ids": [a.pk]})
        self.assertEqual(Post.objects.count(), 1)

    def test_duplicate(self):
        post = Post.objects.create(title="اصل", slug="orig", body_html="<p>x</p>", status=Post.PUBLISHED, published_at=timezone.now())
        self.post("post_duplicate", {}, post.pk)
        copy = Post.objects.exclude(pk=post.pk).get()
        self.assertEqual(copy.status, Post.DRAFT)
        self.assertIn("کپی", copy.title)


class AuthorTests(PanelCase):
    def setUp(self):
        super().setUp()
        self.author = make_user("w", StaffRole.AUTHOR)
        self.login(self.author)

    def test_author_cannot_publish(self):
        # "published" is not among an author's choices, so a forged request is refused ...
        self.post("post_new", {"title": "نوشته", "body_html": "<p>x</p>", "status": Post.PUBLISHED, "intent": "publish", "allow_comments": "on"})
        self.assertEqual(Post.objects.count(), 0)
        # ... and the publish button on an allowed status does not publish either.
        self.post("post_new", {"title": "نوشته", "body_html": "<p>x</p>", "status": Post.DRAFT, "intent": "publish", "allow_comments": "on"})
        post = Post.objects.get()
        self.assertEqual(post.status, Post.DRAFT)
        self.assertEqual(post.author, self.author)

    def test_author_submits_for_review(self):
        self.post("post_new", {"title": "نوشته", "body_html": "<p>x</p>", "status": Post.DRAFT, "intent": "review", "allow_comments": "on"})
        self.assertEqual(Post.objects.get().status, Post.REVIEW)

    def test_author_sees_only_own_posts(self):
        other = make_user("o", StaffRole.EDITOR)
        mine = Post.objects.create(title="من", slug="mine", author=self.author)
        theirs = Post.objects.create(title="او", slug="theirs", author=other)
        res = self.get("posts")
        titles = [p.title for p in res.context["page"].object_list]
        self.assertEqual(titles, ["من"])
        self.assertEqual(self.get("post_edit", theirs.pk).status_code, 404)
        self.assertEqual(self.get("post_edit", mine.pk).status_code, 200)

    def test_author_cannot_edit_published_post(self):
        post = Post.objects.create(title="من", slug="mine", author=self.author, status=Post.PUBLISHED, published_at=timezone.now())
        self.assertEqual(self.get("post_edit", post.pk).status_code, 403)

    def test_author_cannot_bulk_publish(self):
        post = Post.objects.create(title="من", slug="mine", author=self.author)
        self.post("posts", {"bulk": "publish", "ids": [post.pk]})
        post.refresh_from_db()
        self.assertEqual(post.status, Post.DRAFT)


class MediaTests(PanelCase):
    def setUp(self):
        super().setUp()
        self.login(make_user("e", StaffRole.EDITOR))

    def test_upload_image(self):
        res = self.post("media_upload", {"files": SimpleUploadedFile("عکس من.png", PNG, content_type="image/png")})
        self.assertEqual(res.status_code, 302)
        item = Media.objects.get()
        self.assertEqual(item.content_type, "image/png")
        self.assertEqual(self.client.get(item.url, **HOST).status_code, 200)

    def test_upload_json_for_picker(self):
        res = self.post("media_upload", {"files": SimpleUploadedFile("a.png", PNG)}, HTTP_X_REQUESTED_WITH="XMLHttpRequest")
        self.assertEqual(res.json()["items"][0]["image"], True)

    def test_rejects_disguised_files(self):
        self.post("media_upload", {"files": SimpleUploadedFile("evil.png", b"<script>alert(1)</script>", content_type="image/png")})
        self.assertEqual(Media.objects.count(), 0)
        self.post("media_upload", {"files": SimpleUploadedFile("evil.svg", b"<svg onload=alert(1)>", content_type="image/svg+xml")})
        self.assertEqual(Media.objects.count(), 0)

    def test_rejects_big_files(self):
        big = b"\x89PNG\r\n\x1a\n" + b"0" * (5 * 1024 * 1024 + 1)
        self.post("media_upload", {"files": SimpleUploadedFile("big.png", big)})
        self.assertEqual(Media.objects.count(), 0)

    def test_edit_alt_and_delete(self):
        item = Media.from_upload(SimpleUploadedFile("a.png", PNG))
        self.post("media_edit", {"title": "عنوان", "alt": "توضیح"}, item.pk)
        item.refresh_from_db()
        self.assertEqual(item.alt, "توضیح")
        self.post("media_delete", {}, item.pk)
        self.assertEqual(Media.objects.count(), 0)

    def test_deleting_cover_keeps_post(self):
        item = Media.from_upload(SimpleUploadedFile("a.png", PNG))
        post = Post.objects.create(title="p", slug="p", cover=item)
        self.post("media_delete", {}, item.pk)
        post.refresh_from_db()
        self.assertIsNone(post.cover)


class InboxTests(PanelCase):
    def setUp(self):
        super().setUp()
        self.login(make_user("s", StaffRole.SUPPORT))
        self.post_obj = Post.objects.create(title="p", slug="p", status=Post.PUBLISHED, published_at=timezone.now())

    def test_approve_and_reply(self):
        c = Comment.objects.create(post=self.post_obj, name="ع", body="سلام")
        self.post("comment_action", {"action": "approve", "ids": [c.pk]})
        c.refresh_from_db()
        self.assertEqual(c.status, Comment.APPROVED)
        self.post("comment_action", {"action": "reply", "ids": [c.pk], "reply": "ممنون از شما"})
        reply = Comment.objects.get(is_staff_reply=True)
        self.assertEqual(reply.parent, c)
        self.assertEqual(reply.status, Comment.APPROVED)

    def test_single_row_action_uses_one_param(self):
        a = Comment.objects.create(post=self.post_obj, name="a", body="aaa")
        b = Comment.objects.create(post=self.post_obj, name="b", body="bbb")
        self.client.post(url("comment_action") + f"?one={a.pk}", {"action": "trash", "ids": [a.pk, b.pk]}, **HOST)
        a.refresh_from_db(); b.refresh_from_db()
        self.assertEqual((a.status, b.status), (Comment.TRASH, Comment.PENDING))

    def test_contact_status_and_delete(self):
        m = ContactMessage.objects.create(name="ر", message="پیام")
        self.post("contact_action", {"action": "answered"}, m.pk)
        m.refresh_from_db()
        self.assertEqual(m.status, ContactMessage.ANSWERED)
        self.post("contact_action", {"action": "delete"}, m.pk)
        self.assertEqual(ContactMessage.objects.count(), 0)

    def test_subscribers_csv(self):
        Subscriber.objects.create(email="x@y.ir")
        res = self.get("subscribers_export")
        self.assertEqual(res["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn("x@y.ir", res.content.decode("utf-8-sig"))


class AdminTests(PanelCase):
    def setUp(self):
        super().setUp()
        self.admin = make_user("a", StaffRole.ADMIN)
        self.login(self.admin)

    def test_settings_save(self):
        res = self.client.post(url("settings") + "?tab=general", {"site_name": "نام تازه", "tagline": "شعار", "description": "d", "footer_note": "", "copyright_text": "x"}, **HOST)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(SiteSettings.get().site_name, "نام تازه")
        self.assertContains(self.client.get("/", **SITE), "نام تازه")

    def test_analytics_field_only_for_superuser(self):
        res = self.client.get(url("settings") + "?tab=seo", **HOST)
        self.assertNotContains(res, "analytics_head")
        self.client.logout()
        self.login(make_user("root", superuser=True))
        res = self.client.get(url("settings") + "?tab=seo", **HOST)
        self.assertContains(res, "analytics_head")

    def test_add_staff_by_phone(self):
        user = User.objects.create_user(username="09120000000")
        LearnerProfile.objects.create(user=user, phone="09120000000")
        self.post("staff", {"action": "add", "identifier": "0912 000 0000", "role": StaffRole.AUTHOR})
        self.assertEqual(user.site_role.role, StaffRole.AUTHOR)

    def test_add_staff_unknown_user(self):
        res = self.post("staff", {"action": "add", "identifier": "nobody", "role": StaffRole.AUTHOR})
        self.assertContains(res, "پیدا نشد")

    def test_cannot_change_own_role(self):
        self.post("staff_update", {"role": StaffRole.AUTHOR}, self.admin.site_role.pk)
        self.admin.site_role.refresh_from_db()
        self.assertEqual(self.admin.site_role.role, StaffRole.ADMIN)

    def test_activity_log_records_changes(self):
        self.post("categories_new", {"name": "دستهٔ تازه", "slug": "", "order": 5})
        self.assertTrue(ActivityLog.objects.filter(action="create", object_type="Category").exists())

    def test_generic_crud_roundtrip(self):
        self.post("categories_new", {"name": "یک", "slug": "", "order": 1})
        cat = Category.objects.get()
        self.assertEqual(cat.slug, "یک")
        self.post("categories_edit", {"name": "دو", "slug": "two", "order": 2}, cat.pk)
        cat.refresh_from_db()
        self.assertEqual((cat.name, cat.slug), ("دو", "two"))
        self.post("categories_delete", {}, cat.pk)
        self.assertEqual(Category.objects.count(), 0)

    def test_page_body_is_sanitized(self):
        self.post("pages_new", {"title": "قوانین", "slug": "", "kind": "default", "status": "published", "body_html": '<p onclick="x()">متن</p><script>1</script>'})
        page = Page.objects.get()
        self.assertEqual(page.body_html, "<p>متن</p>")

    def test_announcement_jalali_date(self):
        self.post("announcements_new", {"title": "خبر", "slug": "", "level": "info", "body_html": "<p>x</p>", "is_published": "on", "published_at": "1405/07/20 10:00"})
        a = Announcement.objects.get()
        self.assertEqual(a.published_at.astimezone().year, 2026)

    def test_global_search(self):
        Post.objects.create(title="آموزش لایتنر", slug="l")
        res = self.client.get(url("search") + "?q=لایتنر", **HOST)
        self.assertEqual(res.json()["results"][0]["label"], "آموزش لایتنر")

    def test_seo_page_lists_problems(self):
        Post.objects.create(title="بدون توضیح", slug="x", status=Post.PUBLISHED, published_at=timezone.now())
        res = self.get("seo")
        self.assertContains(res, "بدون توضیح")
        self.assertContains(res, "بدون تصویر شاخص")


class CommercePagesTests(PanelCase):
    def test_orders_and_plans_pages_with_data(self):
        from apps.billing.models import Order, Plan, PlanPrice

        user = make_user("buyer")
        LearnerProfile.objects.create(user=user, phone="09123334444")
        plan = Plan.objects.create(slug="pro", name_fa="حرفه‌ای", kind="plan", status="active")
        price = PlanPrice.objects.create(plan=plan, duration_days=30, price_toman=199000)
        Order.objects.create(user=user, plan=plan, price=price, duration_days=30, amount_toman=199000, payable_toman=199000, status=Order.STATUS_PAID, paid_at=timezone.now())
        self.login(make_user("a", StaffRole.ADMIN))
        res = self.get("orders")
        self.assertContains(res, "09123334444")
        self.assertContains(res, "حرفه‌ای")
        self.assertContains(self.get("plans"), "حرفه‌ای")
        self.assertContains(self.get("dashboard"), "درآمد")
