import base64
from hashlib import sha256
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.test import SimpleTestCase,TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from apps.ai_retrieval.media_catalog import catalog_media
from .media import extract_media,graphic_ids,resolve_one,safe_fragment,viewer_payload


ARTICLE={"id":"1","title":"Clinical reference","body_html":'<p>Original text</p><table><caption>Original table</caption><tr><th>Header</th><th>Value</th></tr><tr><td rowspan="2">A</td><td>10</td></tr><tr><td>20</td></tr></table><img src="58087" alt="Original figure description">',"outline_html":"","updated":""}


class MediaExtractionTests(SimpleTestCase):
    def test_catalog_and_viewer_use_the_same_keys_and_preserve_complex_table(self):
        catalog=catalog_media(ARTICLE);rich=extract_media(ARTICLE,include_graphics=False)
        self.assertEqual({row["key"] for row in catalog},{row["key"] for row in rich})
        self.assertIn('rowspan="2"',rich[0]["html"])
        self.assertIn("Original figure description",catalog[1]["text"])

    def test_nested_tables_do_not_change_outer_table_or_image_identity(self):
        article={**ARTICLE,"body_html":'<table><tr><td><table><tr><td>Nested</td></tr></table><img src="99"></td></tr></table><img src="88">'}
        self.assertEqual({r["key"] for r in catalog_media(article)},{r["key"] for r in extract_media(article,include_graphics=False)})

    def test_unsafe_markup_and_remote_images_are_removed(self):
        html=safe_fragment('<table onclick="bad()"><tr><td>A<script>bad()</script></td></tr></table><img src="file:///etc/passwd"><iframe src="https://invalid"></iframe>')
        self.assertNotIn("script",html);self.assertNotIn("onclick",html);self.assertNotIn("file:",html);self.assertNotIn("iframe",html)

    def test_related_graphic_ids_are_parsed_without_executing_javascript(self):
        html='<a onclick="doOperation({contentIds:[&quot;123&quot;]})">table 1</a>'
        self.assertEqual(graphic_ids(html),["123"])

    def test_media_key_cannot_read_an_unrelated_graphic(self):
        self.assertIsNone(resolve_one(ARTICLE,"graphic-999-um-"+"a"*32))

    def test_images_inside_tables_are_resolved_from_local_database(self):
        item={"kind":"table","title":"Table with image","html":'<table><tr><td><img src="123" alt="Original image"></td></tr></table>'}
        with patch("apps.uptodate.services.get_image",return_value={"content_type":"image/png","data_base64":"Zml4dHVyZQ=="}) as image:
            data=viewer_payload(item)
        image.assert_called_once_with("123")
        self.assertIn('src="data:image/png;base64,Zml4dHVyZQ=="',data["html"])
        self.assertIn("Original image",data["html"])

    def test_pdf_contains_a_real_document_and_never_fetches_remote_urls(self):
        from .pdf import article_pdf
        article={**ARTICLE,"body_html":'<p>Original source text</p><table><tr><th>Header</th></tr><tr><td>Value</td></tr></table><img src="https://invalid.example/image"><style>@import "file:///etc/passwd";</style>'}
        with patch("urllib.request.urlopen") as remote:
            pdf=article_pdf(article)
        self.assertTrue(pdf.startswith(b"%PDF-"));self.assertGreater(len(pdf),1000);remote.assert_not_called()


class MediaPdfApiTests(TestCase):
    def setUp(self):
        self.user=get_user_model().objects.create_user("media-reader")
        self.api=APIClient();self.api.force_authenticate(self.user)
        self.available=patch("apps.uptodate.views._require_available");self.available.start();self.addCleanup(self.available.stop)
        self.feature=patch("apps.uptodate.views.require_feature");self.feature_mock=self.feature.start();self.addCleanup(self.feature.stop)
        self.source=patch("apps.uptodate.services.get_topic",return_value=ARTICLE);self.source.start();self.addCleanup(self.source.stop)

    def test_pdf_endpoint_requires_auth_and_checks_source_access(self):
        with patch("apps.uptodate.pdf.article_pdf",return_value=b"%PDF-fixture"):
            response=self.api.get(reverse("uptodate-pdf",args=["1"]))
        self.assertEqual(response.status_code,200);self.assertEqual(response["Content-Type"],"application/pdf")
        self.assertIn("attachment",response["Content-Disposition"])
        self.feature_mock.assert_called_once();self.assertTrue(self.feature_mock.call_args.kwargs["consume"])
        self.api.force_authenticate(None);self.assertEqual(self.api.get(reverse("uptodate-pdf",args=["1"])).status_code,401)

    def test_table_endpoint_returns_original_structure_and_rejects_stale_hash(self):
        key=extract_media(ARTICLE,include_graphics=False)[0]["key"]
        url=reverse("uptodate-media",args=["1",key])
        response=self.api.get(url,{"content_hash":sha256(ARTICLE["body_html"].encode()).hexdigest()})
        self.assertEqual(response.status_code,200);self.assertIn('rowspan="2"',response.data["html"])
        self.assertEqual(self.api.get(url,{"content_hash":"0"*64}).status_code,409)
