from datetime import timedelta

from django.core import mail
from .base import SiteTestCase as TestCase
from django.utils import timezone

from apps.website.models import (
    Announcement, Category, Comment, ContactMessage, DailyStat, DownloadLink, Media, Page, Post, Redirect, SiteSettings, Subscriber,
)

HOST = {"HTTP_HOST": "site.localhost"}


def make_post(title="مطلب نمونه", **kw):
    kw.setdefault("status", Post.PUBLISHED)
    kw.setdefault("published_at", timezone.now() - timedelta(hours=1))
    kw.setdefault("body_html", "<h2>بخش یک</h2><p>متن مطلب برای آزمایش.</p><h3>زیر بخش</h3><p>ادامه.</p>")
    slug = kw.pop("slug", None) or f"p-{Post.objects.count() + 1}"
    return Post.objects.create(title=title, slug=slug, **kw)


class HostRoutingTests(TestCase):
    def test_site_host_serves_site(self):
        res = self.client.get("/", **HOST)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "فارمنتا")

    def test_api_host_keeps_api(self):
        res = self.client.get("/api/v1/health/", HTTP_HOST="testserver")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(self.client.get("/blog/", HTTP_HOST="testserver").status_code, 404)

    def test_www_redirects_to_bare_domain(self):
        res = self.client.get("/blog/?page=2", HTTP_HOST="www.pharmenta.ir")
        self.assertEqual(res.status_code, 301)
        self.assertTrue(res["Location"].endswith("://pharmenta.ir/blog/?page=2"))

    def test_maintenance_mode_blocks_visitors_but_not_staff(self):
        row = SiteSettings.get()
        row.maintenance_mode = True
        row.save()
        self.assertEqual(self.client.get("/", **HOST).status_code, 503)
        self.assertEqual(self.client.get("/panel/login/", **HOST).status_code, 200)

    def test_redirect_rule_on_404(self):
        Redirect.objects.create(from_path="/old/", to_url="/blog/")
        res = self.client.get("/old/", **HOST)
        self.assertEqual(res.status_code, 301)
        self.assertEqual(res["Location"], "/blog/")


class PostVisibilityTests(TestCase):
    def test_only_live_posts_listed(self):
        live = make_post("زنده", slug="live")
        make_post("پیش‌نویس", slug="draft", status=Post.DRAFT, published_at=None)
        make_post("آینده", slug="future", status=Post.SCHEDULED, published_at=timezone.now() + timedelta(days=1))
        due = make_post("زمان‌بندی رسیده", slug="due", status=Post.SCHEDULED, published_at=timezone.now() - timedelta(minutes=5))
        res = self.client.get("/blog/", **HOST)
        titles = [p.title for p in res.context["page"].object_list]
        self.assertIn(live.title, titles)
        self.assertIn(due.title, titles)
        self.assertNotIn("پیش‌نویس", titles)
        self.assertNotIn("آینده", titles)

    def test_draft_post_is_404_for_visitors(self):
        make_post(slug="draft", status=Post.DRAFT, published_at=None)
        self.assertEqual(self.client.get("/blog/draft/", **HOST).status_code, 404)

    def test_post_page_has_toc_and_counts_view(self):
        post = make_post(slug="live")
        res = self.client.get("/blog/live/", **HOST)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'id="بخش-یک"')
        post.refresh_from_db()
        self.assertEqual(post.views, 1)
        self.assertEqual(DailyStat.objects.get(kind="post").count, 1)

    def test_bots_are_not_counted(self):
        post = make_post(slug="live")
        self.client.get("/blog/live/", HTTP_USER_AGENT="Googlebot/2.1", **HOST)
        post.refresh_from_db()
        self.assertEqual(post.views, 0)

    def test_search(self):
        make_post("آموزش لایتنر", slug="a")
        make_post("چیز دیگر", slug="b")
        res = self.client.get("/blog/?q=لایتنر", **HOST)
        self.assertEqual([p.slug for p in res.context["page"].object_list], ["a"])

    def test_noindex_post_meta(self):
        make_post(slug="x", noindex=True)
        self.assertContains(self.client.get("/blog/x/", **HOST), 'name="robots" content="noindex')

    def test_category_page(self):
        cat = Category.objects.create(name="آموزش", slug="learn")
        make_post(slug="in", category=cat)
        make_post(slug="out")
        res = self.client.get("/blog/category/learn/", **HOST)
        self.assertEqual([p.slug for p in res.context["page"].object_list], ["in"])


class CommentTests(TestCase):
    def setUp(self):
        super().setUp()
        self.post = make_post(slug="live")

    def test_comment_waits_for_approval(self):
        res = self.client.post("/blog/live/comment/", {"name": "علی", "body": "عالی بود"}, **HOST)
        self.assertEqual(res.status_code, 302)
        comment = Comment.objects.get()
        self.assertEqual(comment.status, Comment.PENDING)
        self.assertNotContains(self.client.get("/blog/live/", **HOST), "عالی بود")
        comment.status = Comment.APPROVED
        comment.save()
        self.assertContains(self.client.get("/blog/live/", **HOST), "عالی بود")

    def test_honeypot_blocks_bots(self):
        self.client.post("/blog/live/comment/", {"name": "x", "body": "spam spam", "website": "http://x"}, **HOST)
        self.assertEqual(Comment.objects.count(), 0)

    def test_comments_can_be_turned_off(self):
        row = SiteSettings.get()
        row.comments_enabled = False
        row.save()
        self.client.post("/blog/live/comment/", {"name": "علی", "body": "عالی بود"}, **HOST)
        self.assertEqual(Comment.objects.count(), 0)


class FormsTests(TestCase):
    def test_newsletter_subscribe_once(self):
        for _ in range(2):
            self.client.post("/newsletter/", {"email": "A@Example.com"}, **HOST)
        self.assertEqual(Subscriber.objects.get().email, "a@example.com")

    def test_newsletter_rejects_bad_email(self):
        self.client.post("/newsletter/", {"email": "nope"}, **HOST)
        self.assertEqual(Subscriber.objects.count(), 0)

    def test_contact_form_saves_message(self):
        res = self.client.post("/contact/", {"name": "رضا", "email": "r@x.ir", "message": "سلام، یک پرسش دارم"}, **HOST)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(ContactMessage.objects.get().name, "رضا")

    def test_contact_needs_a_way_to_reply(self):
        self.client.post("/contact/", {"name": "رضا", "message": "سلام، یک پرسش دارم"}, **HOST)
        self.assertEqual(ContactMessage.objects.count(), 0)


class DownloadAndMachineTests(TestCase):
    def test_download_click_counts_and_redirects(self):
        link = DownloadLink.objects.create(store="bazaar", url="https://cafebazaar.ir/app/x")
        res = self.client.get(f"/dl/{link.pk}/", **HOST)
        self.assertEqual(res.status_code, 302)
        self.assertEqual(res["Location"], "https://cafebazaar.ir/app/x")
        link.refresh_from_db()
        self.assertEqual(link.clicks, 1)

    def test_sitemap_lists_live_posts_only(self):
        make_post(slug="live")
        make_post(slug="draft", status=Post.DRAFT, published_at=None)
        body = self.client.get("/sitemap.xml", **HOST).content.decode()
        self.assertIn("/blog/live/", body)
        self.assertNotIn("/blog/draft/", body)

    def test_robots_hides_panel(self):
        body = self.client.get("/robots.txt", **HOST).content.decode()
        self.assertIn("Disallow: /panel/", body)
        self.assertIn("Sitemap:", body)

    def test_robots_when_site_noindex(self):
        row = SiteSettings.get()
        row.noindex_site = True
        row.save()
        self.assertIn("Disallow: /\n", self.client.get("/robots.txt", **HOST).content.decode())

    def test_rss(self):
        make_post("مطلب فید", slug="feed")
        self.assertContains(self.client.get("/rss.xml", **HOST), "مطلب فید")

    def test_announcement_hidden_until_published(self):
        Announcement.objects.create(title="آینده", slug="soon", published_at=timezone.now() + timedelta(days=1))
        self.assertEqual(self.client.get("/announcements/soon/", **HOST).status_code, 404)

    def test_media_served_with_cache_headers(self):
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 32
        item = Media.objects.create(filename="a.png", content_type="image/png", size=len(png), sha256="ab" * 32, data=png)
        res = self.client.get(item.url, **HOST)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res["Content-Type"], "image/png")
        self.assertIn("immutable", res["Cache-Control"])
        self.assertEqual(res["X-Content-Type-Options"], "nosniff")

    def test_draft_page_hidden(self):
        Page.objects.create(title="پیش‌نویس", slug="secret", status=Page.DRAFT)
        self.assertEqual(self.client.get("/secret/", **HOST).status_code, 404)
