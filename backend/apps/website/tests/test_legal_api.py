from django.test import TestCase

from apps.website.models import Page


class LegalPageApiTests(TestCase):
    def test_the_terms_and_privacy_pages_are_public(self):
        Page.objects.update_or_create(slug="terms", defaults={"title": "قوانین و مقررات", "body_html": "<p>بند ۱</p>"})
        res = self.client.get("/api/v1/app/legal/terms/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual((res.data["title"], res.data["body_html"]), ("قوانین و مقررات", "<p>بند ۱</p>"))

    def test_other_pages_and_drafts_are_not_served(self):
        Page.objects.update_or_create(slug="about", defaults={"title": "دربارهٔ ما"})
        Page.objects.update_or_create(slug="privacy", defaults={"title": "حریم خصوصی", "status": Page.DRAFT})
        self.assertEqual(self.client.get("/api/v1/app/legal/about/").status_code, 404)
        self.assertEqual(self.client.get("/api/v1/app/legal/privacy/").status_code, 404)
