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
