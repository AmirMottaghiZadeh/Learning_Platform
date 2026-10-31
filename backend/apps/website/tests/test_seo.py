import json
import re
from datetime import timedelta

from django.core.management import call_command
from django.test import override_settings
from django.utils import timezone

from apps.drugs.models import AtcCode, Ingredient, IngredientProfileSection
from apps.website.models import MenuItem, Page, Post
from apps.website.views_drugs import summary_html

from .base import SiteTestCase as TestCase

HOST = {"HTTP_HOST": "site.localhost"}
LD = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.S)


def structured(res):
    """Every schema.org node on a page, from all of its JSON-LD blocks."""
    nodes = []
    for block in LD.findall(res.content.decode()):
        data = json.loads(block)
        nodes += data.get("@graph", [data])
    return nodes


def make_drug(name, name_fa, code, sections):
    atc, _ = AtcCode.objects.get_or_create(code=code, defaults={"name": code, "name_fa": f"گروه {code}"})
    drug = Ingredient.objects.create(rxcui=str(Ingredient.objects.count() + 100), name=name, name_fa=name_fa, slug=f"{name}-1")
    drug.atc_codes.add(atc)
    for field, text in sections.items():
        IngredientProfileSection.objects.create(ingredient=drug, field=field, summary_fa=text)
    return drug


MECHANISM = "مکانیسم اثر: مهار سنتز دیوارهٔ سلولی باکتری با اتصال به پروتئین‌های متصل‌شونده به پنی‌سیلین."
USES = "- عفونت‌های گوش، حلق و بینی\n- عفونت‌های ادراری"
SIDE = "- شایع: اسهال، راش، تهوع\n- مهم/جدی: واکنش‌های آنافیلاکتیک"


@override_settings(SITE_DRUG_ATC_PREFIXES=["J01"])
class DrugPageTests(TestCase):
    def setUp(self):
        super().setUp()
        self.amox = make_drug("amoxicillin", "آموکسی‌سیلین", "J01CA", {
            "clinical_pharmacology": MECHANISM,
            "indications_and_usage": USES,
            "adverse_reactions": SIDE,
            "boxed_warning": "- متن ورودی حاوی هشدار جعبه‌ای بالینی نیست",
            "dosage_and_administration": "۵۰۰ میلی‌گرم هر ۸ ساعت",
            "drug_interactions": "پروبنسید سطح خونی را بالا می‌برد.",
        })
        self.losartan = make_drug("losartan", "لوزارتان", "C09CA", {
            "clinical_pharmacology": MECHANISM, "indications_and_usage": USES, "adverse_reactions": SIDE,
        })
        self.thin = make_drug("thinamycin", "تین‌مایسین", "J01XX", {"indications_and_usage": USES})

    def test_drug_page_shows_public_sections_and_points_to_the_app(self):
        res = self.client.get("/drugs/amoxicillin-1/", **HOST)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "<h1>آموکسی‌سیلین")
        self.assertContains(res, "موارد مصرف")
        self.assertContains(res, "واکنش‌های آنافیلاکتیک")
        # The rest of the lesson is named, not shown.
        self.assertContains(res, "دوز")
        self.assertNotContains(res, "۵۰۰ میلی‌گرم")
        self.assertNotContains(res, "پروبنسید")
        # A generator placeholder is not a boxed warning.
        self.assertNotContains(res, "متن ورودی")
        self.assertNotContains(res, 'id="boxed"')

    def test_only_open_categories_and_substantial_pages(self):
        self.assertEqual(self.client.get("/drugs/losartan-1/", **HOST).status_code, 404)
        self.assertEqual(self.client.get("/drugs/thinamycin-1/", **HOST).status_code, 404)
        index = self.client.get("/drugs/", **HOST)
        self.assertContains(index, "/drugs/amoxicillin-1/")
        self.assertNotContains(index, "losartan")
        self.assertNotContains(index, "thinamycin")

    @override_settings(SITE_DRUG_ATC_PREFIXES=[])
    def test_off_when_no_category_is_open(self):
        self.assertEqual(self.client.get("/drugs/", **HOST).status_code, 404)
        self.assertEqual(self.client.get("/drugs/amoxicillin-1/", **HOST).status_code, 404)

    def test_structured_data(self):
        nodes = structured(self.client.get("/drugs/amoxicillin-1/", **HOST))
        types = {n["@type"] for n in nodes}
        self.assertTrue({"Organization", "WebSite", "BreadcrumbList", "MedicalWebPage"} <= types)
        page = next(n for n in nodes if n["@type"] == "MedicalWebPage")
        self.assertEqual(page["about"]["name"], "Amoxicillin")
        self.assertEqual(page["about"]["code"][0]["codeValue"], "J01CA")
        # No Product-like type anywhere: Google would demand offers/ratings.
        self.assertNotIn('"Drug"', json.dumps(nodes))

    def test_sitemap_lists_drug_pages(self):
        body = self.client.get("/sitemap.xml", **HOST).content.decode()
        self.assertIn("/drugs/</loc>", body)
        self.assertIn("/drugs/amoxicillin-1/", body)
        self.assertNotIn("losartan", body)

    def test_homepage_links_to_drug_pages(self):
        self.assertContains(self.client.get("/", **HOST), "/drugs/amoxicillin-1/")

    def test_summary_html_escapes_and_structures(self):
        html = summary_html("مکانیسم اثر: <script>x</script>\n- یک\n- دو")
        self.assertIn("<b>مکانیسم اثر:</b>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<ul><li>یک</li><li>دو</li></ul>", html)


class SiteIdentityTests(TestCase):
    def test_home_declares_site_name_and_logo(self):
        nodes = structured(self.client.get("/", **HOST))
        website = next(n for n in nodes if n["@type"] == "WebSite")
        org = next(n for n in nodes if n["@type"] == "Organization")
        self.assertEqual(website["name"], "فارمنتا")
        self.assertIn("Pharmenta", website["alternateName"])
        self.assertTrue(org["logo"]["url"].endswith("/icon-512.png"))

    def test_head_links_stable_icons(self):
        res = self.client.get("/", **HOST)
        self.assertContains(res, '<link rel="icon" href="/favicon.ico"')
        self.assertContains(res, '<link rel="apple-touch-icon" href="/apple-touch-icon.png">')
        self.assertContains(res, '<meta property="og:image" content="https://pharmenta.ir/og-image.png">')

    def test_icons_are_served_at_the_root(self):
        for path, kind in [("/favicon.ico", "image/x-icon"), ("/apple-touch-icon.png", "image/png"), ("/icon-512.png", "image/png")]:
            res = self.client.get(path, **HOST)
            self.assertEqual(res.status_code, 200, path)
            self.assertEqual(res["Content-Type"], kind)
            self.assertTrue(b"".join(res.streaming_content))

    def test_manifest(self):
        data = json.loads(self.client.get("/site.webmanifest", **HOST).content)
        self.assertEqual(data["name"], "فارمنتا")
        self.assertEqual({i["sizes"] for i in data["icons"]}, {"192x192", "512x512"})

    def test_meta_description_is_one_line(self):
        from apps.website.models import SiteSettings

        site = SiteSettings.get()
        site.description = "خط اول\r\nخط دوم"
        site.save()
        self.assertContains(self.client.get("/", **HOST), '<meta name="description" content="خط اول خط دوم">')

    def test_post_structured_data_names_the_editorial_team(self):
        Post.objects.create(
            title="مطلب", slug="p-1", body_html="<p>متن</p>", status=Post.PUBLISHED,
            published_at=timezone.now() - timedelta(hours=1),
        )
        nodes = structured(self.client.get("/blog/p-1/", **HOST))
        post = next(n for n in nodes if n["@type"] == "BlogPosting")
        self.assertEqual(post["author"], {"@type": "Organization", "name": "تیم علمی فارمنتا", "parentOrganization": {"@id": "https://pharmenta.ir/#organization"}})

    def test_sitemap_leaves_out_noindex_and_foreign_canonical_posts(self):
        when = timezone.now() - timedelta(hours=1)
        Post.objects.create(title="a", slug="kept", status=Post.PUBLISHED, published_at=when)
        Post.objects.create(title="b", slug="hidden", status=Post.PUBLISHED, published_at=when, noindex=True)
        Post.objects.create(title="c", slug="elsewhere", status=Post.PUBLISHED, published_at=when, canonical_url="https://example.com/c/")
        body = self.client.get("/sitemap.xml", **HOST).content.decode()
        self.assertIn("/blog/kept/", body)
        self.assertNotIn("/blog/hidden/", body)
        self.assertNotIn("/blog/elsewhere/", body)


@override_settings(SITE_DRUG_ATC_PREFIXES=["J01"])
class SeedSeoContentTests(TestCase):
    def test_adds_drafts_and_menu_once(self):
        make_drug("amoxicillin", "آموکسی‌سیلین", "J01CA", {
            "clinical_pharmacology": MECHANISM, "indications_and_usage": USES, "adverse_reactions": SIDE,
        })
        call_command("seed_seo_content", stdout=open("/dev/null", "w"))
        posts = Post.objects.all()
        self.assertEqual(posts.count(), 6)
        self.assertTrue(all(p.status == Post.DRAFT for p in posts))
        self.assertEqual(Page.objects.get(slug="editorial-policy").status, Page.DRAFT)
        self.assertTrue(MenuItem.objects.filter(location=MenuItem.HEADER, url="/drugs/").exists())
        body = Post.objects.get(slug="what-is-a-drug-formulary").body_html
        self.assertIn('href="/drugs/amoxicillin-1/"', body)
        self.assertNotIn("[[", body)

        # Edited content survives a second run.
        post = posts.first()
        post.title = "ویرایش‌شده"
        post.save()
        call_command("seed_seo_content", stdout=open("/dev/null", "w"))
        self.assertEqual(Post.objects.count(), 6)
        self.assertEqual(Post.objects.get(pk=post.pk).title, "ویرایش‌شده")
        self.assertEqual(MenuItem.objects.filter(url="/drugs/").count(), 2)


@override_settings(SITE_DRUG_ATC_PREFIXES=["J01"])
class DrugGroupTests(TestCase):
    def setUp(self):
        super().setUp()
        sections = {"clinical_pharmacology": MECHANISM, "indications_and_usage": USES, "adverse_reactions": SIDE}
        self.amox = make_drug("amoxicillin", "آموکسی‌سیلین", "J01CA", sections)
        make_drug("ampicillin", "آمپی‌سیلین", "J01CA", sections)
        make_drug("cefixime", "سفیکسیم", "J01DD", sections)

    def test_subgroup_page_lists_its_drugs_with_their_uses(self):
        res = self.client.get("/drugs/group/j01ca/", **HOST)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, "<h1>داروهای گروه J01CA</h1>")
        self.assertContains(res, "/drugs/amoxicillin-1/")
        self.assertContains(res, "/drugs/ampicillin-1/")
        self.assertNotContains(res, "/drugs/cefixime-1/")
        self.assertContains(res, "عفونت‌های گوش، حلق و بینی، عفونت‌های ادراری")
        self.assertContains(res, '<link rel="canonical" href="https://pharmenta.ir/drugs/group/j01ca/">')
        nodes = structured(res)
        page = next(n for n in nodes if n["@type"] == "CollectionPage")
        self.assertEqual(page["mainEntity"]["numberOfItems"], 2)

    def test_category_page_and_thin_groups(self):
        res = self.client.get("/drugs/group/j01/", **HOST)
        self.assertEqual(res.status_code, 200)
        self.assertContains(res, 'href="/drugs/group/j01ca/"')
        self.assertContains(res, "/drugs/cefixime-1/")
        # One drug is no group page: it would only repeat the drug's own.
        self.assertEqual(self.client.get("/drugs/group/j01dd/", **HOST).status_code, 404)
        self.assertEqual(self.client.get("/drugs/group/c09/", **HOST).status_code, 404)
        res = self.client.get("/drugs/group/J01CA/", **HOST)
        self.assertEqual((res.status_code, res["Location"]), (301, "/drugs/group/j01ca/"))

    def test_drug_page_names_the_drug_in_headings_and_links_its_group(self):
        res = self.client.get("/drugs/amoxicillin-1/", **HOST)
        self.assertContains(res, "<h2>عوارض جانبی آموکسی‌سیلین</h2>")
        self.assertContains(res, "<h2>موارد مصرف آموکسی‌سیلین</h2>")
        self.assertContains(res, "<title>آموکسی‌سیلین (Amoxicillin): موارد مصرف، عوارض جانبی و مکانیسم اثر | فارمنتا</title>")
        self.assertContains(res, 'href="/drugs/group/j01ca/"')
        nodes = structured(res)
        trail = next(n for n in nodes if n["@type"] == "BreadcrumbList")["itemListElement"]
        self.assertEqual([i.get("item") for i in trail], [
            "https://pharmenta.ir/", "https://pharmenta.ir/drugs/", "https://pharmenta.ir/drugs/group/j01/",
            "https://pharmenta.ir/drugs/group/j01ca/", None,
        ])
        about = next(n for n in nodes if n["@type"] == "MedicalWebPage")["about"]
        self.assertEqual(about["alternateName"], ["آموکسی‌سیلین", "آموکسی سیلین", "آموکسیسیلین"])

    def test_sitemap_lists_group_pages(self):
        body = self.client.get("/sitemap.xml", **HOST).content.decode()
        self.assertIn("/drugs/group/j01/</loc>", body)
        self.assertIn("/drugs/group/j01ca/</loc>", body)
        self.assertNotIn("/drugs/group/j01dd/", body)


class ListingPaginationTests(TestCase):
    def setUp(self):
        super().setUp()
        from apps.website.models import SiteSettings

        site = SiteSettings.get()
        site.posts_per_page = 1
        site.save()
        when = timezone.now() - timedelta(hours=1)
        for i in range(3):
            Post.objects.create(title=f"مطلب {i}", slug=f"p-{i}", status=Post.PUBLISHED, published_at=when)

    def test_later_pages_are_their_own_indexable_pages(self):
        res = self.client.get("/blog/?page=2", **HOST)
        self.assertContains(res, '<link rel="canonical" href="https://pharmenta.ir/blog/?page=2">')
        self.assertContains(res, '<link rel="prev" href="https://pharmenta.ir/blog/">')
        self.assertContains(res, '<link rel="next" href="https://pharmenta.ir/blog/?page=3">')
        self.assertContains(res, "<title>مقالات - صفحهٔ ۲ | فارمنتا</title>")
        self.assertNotContains(res, 'name="robots"')
        first = self.client.get("/blog/", **HOST)
        self.assertContains(first, '<link rel="canonical" href="https://pharmenta.ir/blog/">')
        self.assertNotContains(first, 'rel="prev"')

    def test_search_results_stay_out_of_the_index(self):
        self.assertContains(self.client.get("/blog/?q=مطلب", **HOST), '<meta name="robots" content="noindex, follow">')

    def test_empty_category_and_thin_tag_are_noindex(self):
        from apps.website.models import Category, Tag

        empty = Category.objects.create(name="خالی", slug="empty")
        self.assertContains(self.client.get(empty.get_absolute_url(), **HOST), 'content="noindex, follow"')
        tag = Tag.objects.create(name="کم", slug="few")
        Post.objects.get(slug="p-0").tags.add(tag)
        self.assertContains(self.client.get("/blog/tag/few/", **HOST), 'content="noindex, follow"')


class SearchEngineTests(TestCase):
    def test_bing_verification_meta(self):
        from apps.website.models import SiteSettings

        site = SiteSettings.get()
        site.bing_verification = "ABC123"
        site.save()
        self.assertContains(self.client.get("/", **HOST), '<meta name="msvalidate.01" content="ABC123">')

    @override_settings(INDEXNOW_KEY="0123456789abcdef")
    def test_indexnow_key_file(self):
        res = self.client.get("/0123456789abcdef.txt", **HOST)
        self.assertEqual((res.status_code, res.content), (200, b"0123456789abcdef"))
        self.assertEqual(self.client.get("/wrongkey1.txt", **HOST).status_code, 404)

    def test_indexnow_key_file_off_without_a_key(self):
        self.assertEqual(self.client.get("/0123456789abcdef.txt", **HOST).status_code, 404)

    @override_settings(INDEXNOW_KEY="0123456789abcdef")
    def test_indexnow_submit_posts_the_urls(self):
        from unittest import mock

        from apps.website import indexnow

        response = mock.MagicMock(status=200)
        response.__enter__.return_value = response
        with mock.patch("urllib.request.urlopen", return_value=response) as urlopen:
            self.assertEqual(indexnow.submit(["/drugs/", "/blog/x/", "/drugs/"]), 2)
        body = json.loads(urlopen.call_args[0][0].data)
        self.assertEqual(body["host"], "pharmenta.ir")
        self.assertEqual(body["keyLocation"], "https://pharmenta.ir/0123456789abcdef.txt")
        self.assertEqual(body["urlList"], ["https://pharmenta.ir/blog/x/", "https://pharmenta.ir/drugs/"])

    @override_settings(INDEXNOW_KEY="0123456789abcdef")
    def test_publishing_a_post_notifies_after_commit(self):
        from unittest import mock

        with mock.patch("apps.website.indexnow.submit") as submit, mock.patch("threading.Thread.start", lambda t: t.run()):
            with self.captureOnCommitCallbacks(execute=True):
                Post.objects.create(title="تازه", slug="fresh", status=Post.PUBLISHED, published_at=timezone.now() - timedelta(minutes=1))
            with self.captureOnCommitCallbacks(execute=True):
                Post.objects.create(title="پیش‌نویس", slug="draft", status=Post.DRAFT)
        submit.assert_called_once_with(["/blog/fresh/", "/blog/"])

    @override_settings(INDEXNOW_KEY="0123456789abcdef")
    def test_indexnow_is_silent_when_the_site_is_noindex(self):
        from unittest import mock

        from apps.website import indexnow
        from apps.website.models import SiteSettings

        site = SiteSettings.get()
        site.noindex_site = True
        site.save()
        with mock.patch("urllib.request.urlopen") as urlopen:
            self.assertEqual(indexnow.submit(["/"]), 0)
        urlopen.assert_not_called()
