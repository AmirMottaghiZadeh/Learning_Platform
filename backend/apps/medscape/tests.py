import json
import tempfile
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from rest_framework.test import APIClient

from apps.medscape.models import Article


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
                "content": "Some text.\n\nwebmd.ads2.defineAd({id:'ads-pos-1',pos: 1});\n\nMore text.",
                "children": [{"heading": "Background", "content": "Nested text.", "children": []}],
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
                "content": "Guideline text.",
                "subsections": [{"heading": "Detail", "content": "More detail."}],
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
        self.addCleanup(self._diseases.cleanup)
        self.addCleanup(self._guidelines.cleanup)

    def _import(self, **kwargs):
        call_command(
            "import_medscape_articles",
            diseases_dir=self._diseases.name,
            guidelines_dir=self._guidelines.name,
            **kwargs,
        )

    def test_import_creates_a_disease_article_with_cleaned_content(self):
        _write_diseases_tree(self._diseases.name, {"medicine": {"cardiology.json": [_disease_record()]}})
        self._import()

        self.assertEqual(Article.objects.filter(kind="disease").count(), 1)
        article = Article.objects.get(kind="disease", source_id="1")
        self.assertEqual(article.slug, "test-condition-1")
        self.assertEqual(article.categories, [{"category": "medicine", "specialty": "Cardiology"}])
        self.assertNotIn("webmd.ads2", article.sections[0]["content"])
        self.assertIn("Some text.", article.sections[0]["content"])
        self.assertEqual(article.sections[0]["children"][0]["heading"], "Background")

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

    def test_import_creates_a_guideline_with_filename_derived_specialty(self):
        _write_guidelines(self._guidelines.name, "guidelines_content.json", [_guideline_record()])
        self._import()

        self.assertEqual(Article.objects.filter(kind="guideline").count(), 1)
        article = Article.objects.get(kind="guideline")
        self.assertEqual(article.title, "A Test Guideline: Full Title")
        self.assertEqual(article.slug, "g-a-test-guideline-2024a1000abc")
        self.assertEqual(article.categories, [{"category": "guideline", "specialty": "Guidelines"}])
        self.assertEqual(article.sections[0]["children"][0]["heading"], "Detail")

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
            sections=[{"heading": "Overview", "content": "Text.", "children": []}],
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
