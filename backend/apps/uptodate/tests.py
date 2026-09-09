import json
import sqlite3
import tempfile
import zlib
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from . import services


def _make_snapshot(directory: str):
    d = Path(directory)
    (d / "info.json").write_text(json.dumps({"version": 202607}))

    fts = sqlite3.connect(d / "fts.db")
    fts.execute(
        "CREATE VIRTUAL TABLE fts USING fts5("
        "title, displayTitle UNINDEXED, type UNINDEXED, contentId UNINDEXED, "
        "content, tokenize=porter)"
    )
    fts.executemany(
        "INSERT INTO fts (title, displayTitle, type, contentId, content) VALUES (?,?,?,?,?)",
        [
            ("Hypertension in adults", "Hypertension in adults", 1, "3851",
             "hypertension blood pressure adults treatment"),
            ("A section fragment", "A section fragment", 2, "9999",
             "hypertension fragment"),
        ],
    )
    fts.commit()
    fts.close()

    content = sqlite3.connect(d / "content.db")
    content.execute("CREATE TABLE content (id TEXT, gzip BLOB, version TEXT)")
    body = json.dumps({
        "type": 1,
        "title": "Hypertension in adults",
        "bodyHtml": "<html><body><p>Body.</p></body></html>",
        "outlineHtml": "<html><body>Outline</body></html>",
        "contributors": [
            {"typeName": "Author", "contributors": [{"name": "Jane Doe, MD"}]},
        ],
    }).encode()
    content.execute(
        "INSERT INTO content VALUES (?,?,?)", ("3851", zlib.compress(body), "27.0")
    )
    content.commit()
    content.close()

    toc = sqlite3.connect(d / "toc.db")
    toc.execute("CREATE TABLE toc (id INTEGER, title TEXT, parentId INTEGER, section TEXT, contentId TEXT)")
    toc.executemany(
        "INSERT INTO toc VALUES (?,?,?,?,?)",
        [
            (8, "Cardiovascular Medicine", 0, "Contents", None),
            (728, "Hypertension", 8, "Hypertension", None),
            (9761, "Hypertension in adults", 728, "Drug therapy", "3851"),
        ],
    )
    toc.commit()
    toc.close()


class UptodateTests(TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.addCleanup(services.close_all)
        _make_snapshot(self._tmp.name)
        self.client = APIClient()
        self.client.force_authenticate(
            get_user_model().objects.create_user("u", "u@e.com", "x")
        )

    def _with_snapshot(self):
        return override_settings(UPTODATE_DB_DIR=self._tmp.name)

    def test_search_returns_topic_articles_with_section(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "hypertension"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)  # the type-2 fragment is excluded
        self.assertEqual(res.data[0]["id"], "3851")
        self.assertEqual(res.data[0]["section"], "Cardiovascular Medicine")

    def test_search_without_query_is_empty(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_detail_returns_decompressed_article(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/3851/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["title"], "Hypertension in adults")
        self.assertIn("<p>Body.</p>", res.data["body_html"])
        self.assertEqual(res.data["contributors"], ["Jane Doe, MD"])

    def test_missing_topic_is_404(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/404404/")
        self.assertEqual(res.status_code, 404)

    def test_unavailable_snapshot_answers_503(self):
        services.close_all()
        with override_settings(UPTODATE_DB_DIR="/nonexistent/path"):
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "x"})
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data["code"], "FEATURE_NOT_AVAILABLE")

    def test_requires_authentication(self):
        with self._with_snapshot():
            res = APIClient().get("/api/v1/uptodate/topics/", {"search": "x"})
        self.assertEqual(res.status_code, 401)
