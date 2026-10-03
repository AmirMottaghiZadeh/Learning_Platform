import hashlib
import json
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.medscape.models import Article, ArticleImage

# A well-known minimal valid 1x1 transparent PNG.
_PNG_BYTES = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
    0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x04, 0x00, 0x00, 0x00, 0xB5, 0x1C, 0x0C, 0x02, 0x00, 0x00, 0x00,
    0x0B, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x64, 0x60, 0x00, 0x00,
    0x00, 0x06, 0x00, 0x02, 0x30, 0x81, 0xD0, 0x2F, 0x00, 0x00, 0x00, 0x00,
    0x49, 0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
])
_PNG_HASH = hashlib.sha256(_PNG_BYTES).hexdigest()


def _disease_record(**overrides):
    record = {
        "article_id": "1",
        "url": "https://emedicine.medscape.com/article/1-print",
        "category": "medicine",
        "specialty": "cardiology",
        "title": "Test Condition",
        "meta": "Updated: Jan 1, 2024\nAuthor: Dr Test",
        "sections": [
            {
                "heading": "Overview",
                "blocks": [
                    {"type": "paragraph", "text": "Some text."},
                    {"type": "paragraph", "text": "webmd.ads2.defineAd({id:'ads-pos-1',pos: 1}); More text."},
                ],
                "children": [{
                    "heading": "Background",
                    "blocks": [
                        {"type": "paragraph", "text": "Nested text."},
                        {"type": "list", "ordered": False, "items": ["First", "Second"]},
                        {"type": "table", "headers": ["A", "B"], "rows": [["1", "2"]]},
                        {"type": "image", "file": f"{_PNG_HASH}.png", "url": "https://example.com/x.png",
                         "alt": "Diagram", "caption": "Figure 1."},
                    ],
                    "children": [],
                }],
            },
        ],
    }
    record.update(overrides)
    return record


def _guideline_record(**overrides):
    record = {
        "url": "https://reference.medscape.com/cc1/p10/a-test-guideline-2024a1000abc",
        "link_text": "A Test Guideline",
        "page_title": "A Test Guideline",
        "article_title": "A Test Guideline: Full Title",
        "sections": [
            {
                "order": 1,
                "heading": "Overview",
                "blocks": [{"type": "paragraph", "text": "Guideline text."}],
                "subsections": [{"heading": "Detail", "blocks": [{"type": "paragraph", "text": "More detail."}]}],
            },
        ],
    }
    record.update(overrides)
    return record


def _write_diseases_tree(root, by_category):
    """by_category: {"medicine": {"cardiology.json": [record, ...]}, ...}"""
    for category, files in by_category.items():
        cat_dir = Path(root) / category
        cat_dir.mkdir(parents=True, exist_ok=True)
        for filename, records in files.items():
            (cat_dir / filename).write_text(json.dumps(records), encoding="utf-8")


def _write_guidelines(root, filename, records):
    Path(root, filename).write_text(json.dumps(records), encoding="utf-8")


class ImportMedscapeArticlesTests(TestCase):
    def setUp(self):
        self._diseases = tempfile.TemporaryDirectory()
        self._guidelines = tempfile.TemporaryDirectory()
        self._disease_images = tempfile.TemporaryDirectory()
        self._guideline_images = tempfile.TemporaryDirectory()
        self.addCleanup(self._diseases.cleanup)
        self.addCleanup(self._guidelines.cleanup)
        self.addCleanup(self._disease_images.cleanup)
        self.addCleanup(self._guideline_images.cleanup)
        Path(self._disease_images.name, f"{_PNG_HASH}.png").write_bytes(_PNG_BYTES)

    def _import(self, **kwargs):
        call_command(
            "import_medscape_articles",
            diseases_dir=self._diseases.name,
            guidelines_dir=self._guidelines.name,
            disease_images_dir=self._disease_images.name,
            guideline_images_dir=self._guideline_images.name,
            **kwargs,
        )

    def test_import_creates_a_disease_article_with_cleaned_blocks(self):
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [_disease_record()]}})
        self._import()

        self.assertEqual(Article.objects.filter(kind="disease").count(), 1)
        article = Article.objects.get(kind="disease", source_id="1")
        self.assertEqual(article.slug, "test-condition-1")
        self.assertEqual(article.categories, [{"category": "medicine", "specialty": "Cardiology"}])

        overview = article.sections[0]
        self.assertEqual(overview["blocks"][0]["text"], "Some text.")
        self.assertEqual(overview["blocks"][1]["text"], "More text.", "ad-loader call should be stripped")
        self.assertEqual(overview["children"][0]["heading"], "Background")

    def test_list_and_table_blocks_survive_import(self):
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [_disease_record()]}})
        self._import()

        bg = Article.objects.get(source_id="1").sections[0]["children"][0]
        types = [b["type"] for b in bg["blocks"]]
        self.assertEqual(types, ["paragraph", "list", "table", "image"])
        self.assertEqual(bg["blocks"][1]["items"], ["First", "Second"])
        self.assertEqual(bg["blocks"][2]["rows"], [["1", "2"]])

    def test_image_block_resolves_to_a_stored_article_image(self):
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [_disease_record()]}})
        self._import()

        self.assertEqual(ArticleImage.objects.count(), 1)
        image = ArticleImage.objects.get()
        self.assertEqual(image.content_hash, _PNG_HASH)
        self.assertEqual(image.data, _PNG_BYTES)

        bg = Article.objects.get(source_id="1").sections[0]["children"][0]
        image_block = bg["blocks"][3]
        self.assertEqual(image_block, {"type": "image", "id": image.pk, "alt": "Diagram", "caption": "Figure 1."})

    def test_same_image_reused_across_articles_is_stored_once(self):
        rec2 = _disease_record(article_id="2", title="Second Condition")
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [_disease_record(), rec2]}})
        self._import()
        self.assertEqual(ArticleImage.objects.count(), 1)

    def test_missing_image_file_drops_the_block_without_failing(self):
        rec = _disease_record()
        rec["sections"][0]["children"][0]["blocks"][3]["file"] = "does-not-exist.png"
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [rec]}})
        self._import()

        bg = Article.objects.get(source_id="1").sections[0]["children"][0]
        types = [b["type"] for b in bg["blocks"]]
        self.assertNotIn("image", types)

    def test_article_cross_listed_across_specialty_files_keeps_every_pair(self):
        rec = _disease_record()
        _write_diseases_tree(self._diseases.name, {
            "medicine": {
                "cardiology.json": [rec],
                "critical_care.json": [_disease_record(specialty="critical_care")],
            },
        })
        self._import()

        self.assertEqual(Article.objects.filter(kind="disease").count(), 1)
        article = Article.objects.get(kind="disease", source_id="1")
        self.assertEqual(
            sorted(article.categories, key=lambda c: c["specialty"]),
            [
                {"category": "medicine", "specialty": "Cardiology"},
                {"category": "medicine", "specialty": "Critical Care"},
            ],
        )

    def test_reimport_is_idempotent(self):
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [_disease_record()]}})
        self._import()
        self._import()

        self.assertEqual(Article.objects.filter(kind="disease").count(), 1)
        self.assertEqual(ArticleImage.objects.count(), 1)

    def test_import_creates_a_guideline_with_filename_derived_specialty(self):
        _write_guidelines(self._guidelines.name, "guidelines_content.json", [_guideline_record()])
        self._import()

        self.assertEqual(Article.objects.filter(kind="guideline").count(), 1)
        article = Article.objects.get(kind="guideline")
        self.assertEqual(article.title, "A Test Guideline: Full Title")
        self.assertEqual(article.slug, "g-a-test-guideline-2024a1000abc")
        self.assertEqual(article.categories, [{"category": "guideline", "specialty": "Guidelines"}])
        self.assertEqual(article.sections[0]["children"][0]["heading"], "Detail")
        self.assertEqual(article.sections[0]["children"][0]["blocks"][0]["text"], "More detail.")

    def test_unrecognized_guideline_filename_is_skipped_not_fatal(self):
        _write_guidelines(self._guidelines.name, "unknown_file.json", [_guideline_record()])
        self._import()
        self.assertEqual(Article.objects.filter(kind="guideline").count(), 0)

    def test_record_missing_required_fields_is_skipped(self):
        _write_diseases_tree(self._diseases.name, {
            "medicine": {"cardiology.json": [_disease_record(article_id=""), _disease_record(title="")]},
        })
        self._import()
        self.assertEqual(Article.objects.filter(kind="disease").count(), 0)

    def test_dry_run_writes_nothing(self):
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [_disease_record()]}})
        self._import(dry_run=True)
        self.assertEqual(Article.objects.count(), 0)
        self.assertEqual(ArticleImage.objects.count(), 0)


class MedscapeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.client.force_authenticate(get_user_model().objects.create_user(
            username="reader", email="reader@example.com", password="x"
        ))
        Article.objects.create(
            kind="disease", source_id="1", slug="test-condition-1", title="Test Condition",
            categories=[
                {"category": "medicine", "specialty": "Cardiology"},
                {"category": "medicine", "specialty": "Critical Care"},
            ],
            sections=[{"heading": "Overview", "blocks": [{"type": "paragraph", "text": "Text."}], "children": []}],
        )
        Article.objects.create(
            kind="disease", source_id="2", slug="other-condition-2", title="Other Condition",
            categories=[{"category": "surgery", "specialty": "Orthopedics"}],
            sections=[],
        )
        Article.objects.create(
            kind="guideline", source_id="g1", slug="g-a-guideline", title="A Guideline",
            categories=[{"category": "guideline", "specialty": "Guidelines"}],
            sections=[],
        )
        self.image = ArticleImage.objects.create(
            content_hash=_PNG_HASH, content_type="image/png", data=_PNG_BYTES,
            source_url="https://example.com/x.png",
        )

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get("/api/v1/medscape/tree/").status_code, 401)

    def test_tree_counts_cross_listed_articles_under_every_specialty(self):
        res = self.client.get("/api/v1/medscape/tree/", {"kind": "disease"})
        self.assertEqual(res.status_code, 200)
        by_category = {row["category"]: row["specialties"] for row in res.data}
        medicine = {s["name"]: s["count"] for s in by_category["medicine"]}
        self.assertEqual(medicine, {"Cardiology": 1, "Critical Care": 1})
        surgery = {s["name"]: s["count"] for s in by_category["surgery"]}
        self.assertEqual(surgery, {"Orthopedics": 1})

    def test_tree_is_scoped_to_kind(self):
        res = self.client.get("/api/v1/medscape/tree/", {"kind": "guideline"})
        self.assertEqual([row["category"] for row in res.data], ["guideline"])

    def test_list_by_category_and_specialty(self):
        res = self.client.get(
            "/api/v1/medscape/articles/", {"kind": "disease", "category": "medicine", "specialty": "Cardiology"}
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual([a["slug"] for a in res.data], ["test-condition-1"])

    def test_list_by_search(self):
        res = self.client.get("/api/v1/medscape/articles/", {"kind": "disease", "search": "other"})
        self.assertEqual([a["slug"] for a in res.data], ["other-condition-2"])

    def test_list_without_search_or_category_pair_returns_empty(self):
        res = self.client.get("/api/v1/medscape/articles/", {"kind": "disease"})
        self.assertEqual(res.data, [])

    def test_detail_includes_sections(self):
        res = self.client.get("/api/v1/medscape/articles/test-condition-1/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["title"], "Test Condition")
        self.assertEqual(len(res.data["sections"]), 1)

    def test_list_excludes_sections(self):
        res = self.client.get(
            "/api/v1/medscape/articles/", {"kind": "disease", "category": "medicine", "specialty": "Cardiology"}
        )
        self.assertNotIn("sections", res.data[0])

    def test_image_detail_returns_base64_data(self):
        res = self.client.get(f"/api/v1/medscape/images/{self.image.pk}/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["content_type"], "image/png")
        import base64
        self.assertEqual(base64.b64decode(res.data["data_base64"]), _PNG_BYTES)

    def test_image_detail_404_for_unknown_id(self):
        res = self.client.get("/api/v1/medscape/images/999999/")
        self.assertEqual(res.status_code, 404)
