from django.test import Client

from apps.website.api import note_lines
from apps.website.models import AppRelease, version_code
from apps.website.panel.forms import ReleaseForm

from .base import SiteTestCase


def release(version, *, minimum="", notify=True, published=True, channel=AppRelease.STABLE, platform=AppRelease.ANDROID):
    return AppRelease.objects.create(
        platform=platform, version=version, channel=channel, is_published=published, notify_in_app=notify,
        min_supported_version=minimum, notes_html="<ul><li>جعبهٔ لایتنر</li><li>رفع <b>اشکال</b></li></ul>",
    )


class VersionCodeTests(SiteTestCase):
    def test_matches_app_config(self):
        # frontend/app.config.js: major*10000 + minor*100 + patch
        self.assertEqual(version_code("0.1.0"), 100)
        self.assertEqual(version_code("1.4.2"), 10402)
        self.assertEqual(version_code("12.99.99"), 129999)

    def test_rejects_anything_but_semver_with_small_parts(self):
        for bad in ["1.4", "1.4.2.1", "1.100.0", "1.0.100", "v1.0.0", "1.a.0", "۱.۲.۰", ""]:
            with self.assertRaises(ValueError, msg=bad):
                version_code(bad)

    def test_notes_become_one_line_per_item(self):
        self.assertEqual(note_lines("<p>یک</p><ul><li>دو</li><li>سه <b>چهار</b></li></ul>نکته<br>آخر"),
                         ["یک", "دو", "سه چهار", "نکته", "آخر"])
        self.assertEqual(note_lines(""), [])


class ReleaseCheckTests(SiteTestCase):
    def check(self, code, platform="android"):
        response = Client().get("/api/v1/app/release/", {"platform": platform, "version_code": code})
        self.assertEqual(response.status_code, 200, response.content)
        return response.json()

    def test_no_notified_release_means_no_update(self):
        self.assertEqual(self.check(100), {"update": "none", "latest": None})
        # seed_website's sample release, and any row entered before the
        # in-app notice existed, never reach the app
        release("1.2.0", notify=False)
        self.assertEqual(self.check(100), {"update": "none", "latest": None})

    def test_older_install_gets_an_optional_update_to_the_newest(self):
        release("0.1.0")
        release("0.2.0")
        body = self.check(100)
        self.assertEqual(body["update"], "optional")
        self.assertEqual(body["latest"]["version"], "0.2.0")
        self.assertEqual(body["latest"]["version_code"], 200)
        self.assertEqual(body["latest"]["notes"], ["جعبهٔ لایتنر", "رفع اشکال"])
        self.assertEqual(body["latest"]["download_url"], "https://pharmenta.ir/download/")
        self.assertEqual(self.check(200)["update"], "none")
        self.assertEqual(self.check(300)["update"], "none")

    def test_beta_unpublished_other_platform_and_malformed_releases_are_ignored(self):
        release("0.2.0")
        release("0.3.0", published=False)
        release("0.4.0", channel=AppRelease.BETA)
        release("0.5.0", platform=AppRelease.IOS)
        release("1.0", minimum="0.9.0")
        body = self.check(200)
        self.assertEqual(body["update"], "none")
        self.assertEqual(body["latest"]["version"], "0.2.0")

    def test_below_the_minimum_is_required(self):
        release("0.2.0", minimum="0.1.5")
        self.assertEqual(self.check(104)["update"], "required")
        self.assertEqual(self.check(105)["update"], "optional")

    def test_the_strictest_minimum_holds_after_a_later_release_without_one(self):
        release("0.2.0", minimum="0.2.0")
        release("0.3.0")
        self.assertEqual(self.check(100)["update"], "required")
        self.assertEqual(self.check(200)["update"], "optional")

    def test_needs_no_sign_in_but_valid_parameters(self):
        self.assertEqual(Client().get("/api/v1/app/release/", {"platform": "android"}).status_code, 400)
        self.assertEqual(Client().get("/api/v1/app/release/", {"platform": "web", "version_code": 1}).status_code, 400)


class ReleaseFormTests(SiteTestCase):
    def form(self, **overrides):
        data = {"platform": AppRelease.ANDROID, "version": "1.2.0", "channel": AppRelease.STABLE, "is_published": "on",
                "notify_in_app": "on", "notes_html": "<p>x</p>"}
        data.update(overrides)
        return ReleaseForm(data={k: v for k, v in data.items() if v is not None})

    def test_a_notified_release_needs_semver_versions(self):
        self.assertTrue(self.form().is_valid(), self.form().errors)
        self.assertIn("version", self.form(version="1.2").errors)
        self.assertIn("min_supported_version", self.form(min_supported_version="1.x").errors)
        self.assertIn("min_supported_version", self.form(min_supported_version="1.3.0").errors)
        self.assertTrue(self.form(min_supported_version="1.1.0").is_valid())

    def test_only_a_published_stable_app_release_can_be_notified(self):
        self.assertIn("notify_in_app", self.form(platform=AppRelease.WEB).errors)
        self.assertIn("notify_in_app", self.form(channel=AppRelease.BETA).errors)
        self.assertIn("notify_in_app", self.form(is_published=None).errors)

    def test_an_unnotified_release_keeps_free_form_versions(self):
        self.assertTrue(self.form(version="1.2 beta", notify_in_app=None).is_valid())
