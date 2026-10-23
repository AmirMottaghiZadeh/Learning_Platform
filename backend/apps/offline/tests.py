import base64
import json
import tempfile
import zlib
from io import StringIO
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.billing import config as billing_config
from apps.billing import services as billing
from apps.billing.models import Entitlement, GuestAccount
from apps.billing.tests import make_plan
from apps.lexicomp import services as lexicomp_services
from apps.lexicomp.tests import _make_snapshot as make_lexicomp_snapshot
from apps.uptodate import services as uptodate_services
from apps.uptodate.tests import _make_snapshot as make_uptodate_snapshot

from . import pack, storage
from .builders import build_lexicomp, build_uptodate

SECRET = "test-offline-secret"
User = get_user_model()


def _quiet(*args, **kwargs):
    pass


def _index(out: Path, manifest: dict):
    key = pack.derive_key(manifest["build"])
    build_dir = out / manifest["dataset"] / manifest["build"]
    return key, build_dir, json.loads(zlib.decompress(pack.read_record(build_dir, key, manifest["index"])))


def _record(build_dir, key, locs, i):
    return pack.read_record(build_dir, key, locs[i * 3:i * 3 + 3])


@override_settings(OFFLINE_PACKAGE_SECRET=SECRET)
class PackFormatTests(TestCase):
    def test_a_sealed_record_opens_only_with_its_builds_key(self):
        key = pack.derive_key("uptodate-1-20261023-abc123")
        record = pack.seal(key, b"hello")
        self.assertEqual(pack.open_sealed(key, record), b"hello")
        self.assertEqual(len(record), pack.NONCE_BYTES + 5 + 16)
        with self.assertRaises(Exception):
            pack.open_sealed(pack.derive_key("uptodate-1-20261023-other0"), record)

    def test_the_key_depends_on_the_secret(self):
        build = "lexicomp-202606-20261023-abc123"
        key = pack.derive_key(build)
        with self.settings(OFFLINE_PACKAGE_SECRET="another"):
            self.assertNotEqual(pack.derive_key(build), key)

    def test_no_secret_is_an_error(self):
        with self.settings(OFFLINE_PACKAGE_SECRET=""):
            with self.assertRaises(pack.PackError):
                pack.derive_key("uptodate-x")

    def test_build_must_belong_to_the_dataset(self):
        self.assertTrue(pack.build_matches_dataset("uptodate-1-20261023-abc123", "uptodate"))
        self.assertFalse(pack.build_matches_dataset("lexicomp-1-20261023-abc123", "uptodate"))
        self.assertFalse(pack.build_matches_dataset("uptodate-../x", "uptodate"))

    def test_records_spill_into_new_parts(self):
        with tempfile.TemporaryDirectory() as out:
            writer = pack.PackWriter(out, "lexicomp", "1", part_bytes=100)
            locs = [writer.add(b"x" * 60) for _ in range(3)]
            manifest = writer.finish({"dataset": "lexicomp"})
            self.assertEqual([loc[0] for loc in locs], [0, 1, 2])
            self.assertEqual(len(manifest["files"]), 4)  # the index lands in a part of its own
            self.assertEqual(manifest["total_size"], sum(f["size"] for f in manifest["files"]))
            latest = json.loads((Path(out) / "lexicomp" / "latest.json").read_text())
            self.assertEqual(latest["build"], manifest["build"])


@override_settings(OFFLINE_PACKAGE_SECRET=SECRET, UPTODATE_MYSQL_URL="")
class BuildTests(TestCase):
    def setUp(self):
        self._src = tempfile.TemporaryDirectory()
        self._out = tempfile.TemporaryDirectory()
        self.addCleanup(self._src.cleanup)
        self.addCleanup(self._out.cleanup)
        self.addCleanup(uptodate_services.close_all)
        self.addCleanup(lexicomp_services.close_all)
        self.src, self.out = Path(self._src.name), Path(self._out.name)

    def test_uptodate_records_match_what_the_api_answers(self):
        make_uptodate_snapshot(self.src)
        manifest = build_uptodate(self.src, self.out, pack.DEFAULT_PART_BYTES, log=_quiet)
        key, build_dir, index = _index(self.out, manifest)

        self.assertEqual(index["version"], "202607")
        topics = index["topics"]
        self.assertEqual(topics["ids"], ["3851", "3852", "3853"])  # the type-2 fragment is not searchable
        self.assertEqual(index["sections"][topics["sections"][0]], "Cardiovascular Medicine")
        # token counts per row (title + content), as FTS5's bm25 sees them
        self.assertEqual(topics["lengths"][0], 3 + 5)
        self.assertEqual(index["rows"], 4)
        self.assertEqual(topics["terms"][0], "hypertens in adult")

        i = index["articles"]["ids"].index("3851")
        article = json.loads(zlib.decompress(_record(build_dir, key, index["articles"]["locs"], i)))
        with self.settings(UPTODATE_DB_DIR=str(self.src)):
            self.assertEqual(article, uptodate_services.get_topic("3851"))

        head = zlib.decompress(_record(build_dir, key, topics["heads"], 0)).decode()
        self.assertEqual(head, uptodate_services.snippet_source("hypertension blood pressure adults treatment", "Hypertension in adults"))

        self.assertEqual(index["images"]["ids"], ["73781"])
        self.assertEqual(index["images"]["types"], ["png"])
        self.assertEqual(_record(build_dir, key, index["images"]["locs"], 0), b"\x89PNG\r\n\x1a\nfake")

    def test_nothing_in_the_parts_is_readable(self):
        make_uptodate_snapshot(self.src)
        manifest = build_uptodate(self.src, self.out, pack.DEFAULT_PART_BYTES, log=_quiet)
        raw = b"".join(p.read_bytes() for p in (self.out / "uptodate" / manifest["build"]).glob("part-*.bin"))
        for needle in (b"Hypertension", b"Jane Doe", b"PNG", b"Cardiovascular"):
            self.assertNotIn(needle, raw)

    def test_lexicomp_index_and_monographs(self):
        make_lexicomp_snapshot(self.src)
        manifest = build_lexicomp(self.src, self.out, pack.DEFAULT_PART_BYTES, log=_quiet)
        key, build_dir, index = _index(self.out, manifest)
        self.assertEqual(index["generics"], [[1, "Warfarin"], [2, "Aspirin"], [3, "Ibuprofen"]])
        self.assertEqual(index["brands"], [[1, 2, "Ecotrin (Aspirin)"]])
        self.assertIn([102, 13, 3], index["exceptions"])
        self.assertEqual(index["severity"]["1"], "Major")
        first = index["monographs"][0]
        self.assertEqual(first[:5], [100, 10, 2, 1, 1])
        texts = json.loads(zlib.decompress(pack.read_record(build_dir, key, first[5:8])))
        self.assertEqual(texts["summary"], "Aspirin increases anticoagulant effect.")
        self.assertEqual(texts["management"], "Monitor INR.")

    def test_command_builds_and_reads_back(self):
        make_lexicomp_snapshot(self.src)
        stdout = StringIO()
        call_command("build_offline_package", "lexicomp", "--out", str(self.out), "--source", str(self.src), stdout=stdout)
        self.assertIn("Built lexicomp-v-", stdout.getvalue())  # no info.json in the fixture
        self.assertTrue((self.out / "lexicomp" / "latest.json").is_file())

    def test_command_needs_the_secret(self):
        with self.settings(OFFLINE_PACKAGE_SECRET=""):
            with self.assertRaises(CommandError):
                call_command("build_offline_package", "lexicomp", "--out", str(self.out), "--source", str(self.src))


@override_settings(OFFLINE_PACKAGE_SECRET=SECRET, OFFLINE_S3_BUCKET="", BILLING_ENFORCEMENT_ENABLED=True)
class ApiTests(TestCase):
    def setUp(self):
        self._src = tempfile.TemporaryDirectory()
        self._out = tempfile.TemporaryDirectory()
        self.addCleanup(self._src.cleanup)
        self.addCleanup(self._out.cleanup)
        self.addCleanup(lexicomp_services.close_all)
        self.addCleanup(storage.clear_cache)
        self.addCleanup(billing_config.clear_cache)
        billing_config.clear_cache()
        storage.clear_cache()
        make_lexicomp_snapshot(self._src.name)
        self.manifest = build_lexicomp(self._src.name, self._out.name, pack.DEFAULT_PART_BYTES, log=_quiet)
        self.user = User.objects.create_user("u", "u@e.com", "x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _packages_dir(self):
        return self.settings(OFFLINE_PACKAGES_DIR=self._out.name)

    def _pay(self):
        plan = make_plan("pro", [("lexicomp", None, "")])
        billing.grant(self.user, plan, days=30, source=Entitlement.SOURCE_ADMIN)

    def test_nothing_published_lists_no_package(self):
        with self.settings(OFFLINE_PACKAGES_DIR=""):
            res = self.client.get("/api/v1/offline/packages/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual({r["dataset"] for r in res.data}, {"uptodate", "lexicomp"})
        self.assertTrue(all(r["package"] is None for r in res.data))

    def test_list_shows_the_published_build_and_entitlement(self):
        with self._packages_dir():
            res = self.client.get("/api/v1/offline/packages/")
        rows = {r["dataset"]: r for r in res.data}
        self.assertEqual(rows["lexicomp"]["package"]["build"], self.manifest["build"])
        self.assertIsNone(rows["uptodate"]["package"])
        self.assertFalse(rows["lexicomp"]["entitled"])
        self.assertEqual(rows["lexicomp"]["license_days"], 30)

    def test_free_learner_cannot_download_or_license(self):
        with self._packages_dir():
            urls = self.client.post("/api/v1/offline/packages/lexicomp/urls/", {}, format="json")
            lic = self.client.post(
                "/api/v1/offline/packages/lexicomp/license/", {"build": self.manifest["build"]}, format="json"
            )
        self.assertEqual(urls.status_code, 402)
        self.assertEqual(urls.data["code"], "PREMIUM_REQUIRED")
        self.assertEqual(lic.status_code, 402)

    def test_paid_learner_downloads_every_part_with_ranges(self):
        self._pay()
        with self._packages_dir():
            res = self.client.post("/api/v1/offline/packages/lexicomp/urls/", {}, format="json")
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.data["build"], self.manifest["build"])
            part = res.data["files"][0]
            anon = APIClient()
            whole = b"".join(anon.get(part["url"]).streaming_content)
            tail = anon.get(part["url"], HTTP_RANGE="bytes=10-")
        self.assertEqual(len(whole), part["size"])
        self.assertEqual(tail.status_code, 206)
        self.assertEqual(b"".join(tail.streaming_content), whole[10:])
        self.assertEqual(tail["Content-Range"], f"bytes 10-{part['size'] - 1}/{part['size']}")

    def test_a_tampered_file_token_is_refused(self):
        self._pay()
        with self._packages_dir():
            res = self.client.post("/api/v1/offline/packages/lexicomp/urls/", {}, format="json")
            url = res.data["files"][0]["url"]
            self.assertEqual(APIClient().get(url[:-3] + "xx/").status_code, 404)

    def test_a_replaced_build_is_not_served(self):
        self._pay()
        with self._packages_dir():
            res = self.client.post(
                "/api/v1/offline/packages/lexicomp/urls/", {"build": "lexicomp-old-20200101-000000"}, format="json"
            )
        self.assertEqual(res.status_code, 409)
        self.assertEqual(res.data["details"]["build"], self.manifest["build"])

    def test_native_license_carries_the_raw_key(self):
        self._pay()
        res = self.client.post(
            "/api/v1/offline/packages/lexicomp/license/", {"build": self.manifest["build"]}, format="json"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(base64.b64decode(res.data["key"]), pack.derive_key(self.manifest["build"]))
        self.assertNotIn("wrapped_key", res.data)
        self.assertGreater(res.data["valid_until"], res.data["server_time"])

    def test_web_license_wraps_the_key_to_the_browsers_public_key(self):
        self._pay()
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        spki = private.public_key().public_bytes(Encoding.DER, PublicFormat.SubjectPublicKeyInfo)
        res = self.client.post(
            "/api/v1/offline/packages/lexicomp/license/",
            {"build": self.manifest["build"], "public_key": base64.b64encode(spki).decode()},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertNotIn("key", res.data)
        oaep = padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None)
        key = private.decrypt(base64.b64decode(res.data["wrapped_key"]), oaep)
        self.assertEqual(key, pack.derive_key(self.manifest["build"]))

    def test_a_bad_public_key_is_a_validation_error(self):
        self._pay()
        res = self.client.post(
            "/api/v1/offline/packages/lexicomp/license/",
            {"build": self.manifest["build"], "public_key": "bm90LWEta2V5"},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_license_for_another_datasets_build_is_refused(self):
        self._pay()
        res = self.client.post(
            "/api/v1/offline/packages/lexicomp/license/", {"build": "uptodate-1-20261023-abc123"}, format="json"
        )
        self.assertEqual(res.status_code, 404)

    def test_an_expired_plan_stops_the_license(self):
        self._pay()
        Entitlement.objects.filter(user=self.user).update(revoked_at="2026-01-01T00:00:00Z")
        res = self.client.post(
            "/api/v1/offline/packages/lexicomp/license/", {"build": self.manifest["build"]}, format="json"
        )
        self.assertEqual(res.status_code, 402)

    def test_guest_is_never_entitled(self):
        GuestAccount.objects.create(user=self.user)
        with self.settings(BILLING_ENFORCEMENT_ENABLED=False):
            billing_config.clear_cache()
            res = self.client.post(
                "/api/v1/offline/packages/lexicomp/license/", {"build": self.manifest["build"]}, format="json"
            )
        self.assertEqual(res.status_code, 402)

    def test_with_enforcement_off_a_paid_plan_is_still_needed(self):
        with self.settings(BILLING_ENFORCEMENT_ENABLED=False):
            billing_config.clear_cache()
            res = self.client.post(
                "/api/v1/offline/packages/lexicomp/license/", {"build": self.manifest["build"]}, format="json"
            )
        self.assertEqual(res.status_code, 402)

    def test_staff_may_without_a_plan(self):
        self.user.is_staff = True
        self.user.save()
        res = self.client.post(
            "/api/v1/offline/packages/lexicomp/license/", {"build": self.manifest["build"]}, format="json"
        )
        self.assertEqual(res.status_code, 200)

    def test_the_free_plan_does_not_count_as_paid(self):
        from apps.billing.models import Plan

        free = Plan.objects.get(is_free=True)
        billing.grant(self.user, free, days=30, source=Entitlement.SOURCE_ADMIN)
        res = self.client.post(
            "/api/v1/offline/packages/lexicomp/license/", {"build": self.manifest["build"]}, format="json"
        )
        self.assertEqual(res.status_code, 402)

    def test_unknown_dataset_is_404(self):
        res = self.client.post("/api/v1/offline/packages/medscape/urls/", {}, format="json")
        self.assertEqual(res.status_code, 404)
