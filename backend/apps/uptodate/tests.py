import base64
import json
import sqlite3
import tempfile
import zlib
from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock, patch

import pymysql
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings
from rest_framework.test import APIClient

from . import services
from .mysql_schema import ensure_title_search_index


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
            ("Hypertension section fragment", "Hypertension section fragment", 2, "9999",
             "hypertension fragment"),
            ("Cardiovascular risk", "Hypertension overview", 1, "3852",
             "hypertension blood pressure adults treatment"),
            ("Diabetes mellitus", "Diabetes mellitus", 1, "3853",
             "An overview of diagnosis and management."),
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

    images = sqlite3.connect(d / "images.db")
    images.execute("CREATE TABLE images (id TEXT PRIMARY KEY, binary BLOB, type TEXT)")
    images.execute(
        "INSERT INTO images VALUES (?,?,?)", ("73781", b"\x89PNG\r\n\x1a\nfake", "png")
    )
    images.commit()
    images.close()


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
        # UPTODATE_MYSQL_URL may be set in the developer's own .env (for
        # exercising the MySQL mirror locally); tests must not depend on
        # that ambient, network-reaching setting.
        return override_settings(UPTODATE_DB_DIR=self._tmp.name, UPTODATE_MYSQL_URL="")

    def test_search_returns_topic_articles_with_section(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "hypertension"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data), 1)  # the type-2 fragment is excluded
        self.assertEqual(res.data[0]["id"], "3851")
        self.assertEqual(res.data[0]["section"], "Cardiovascular Medicine")
        self.assertIn("hypertension", res.data[0]["snippet"])

    def test_search_without_query_is_empty(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_search_does_not_match_article_body(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "blood pressure"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_search_requires_every_word_in_title(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "hypertension treatment"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data, [])

    def test_title_prefix_search_is_case_insensitive(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "HYPERT adu"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([row["id"] for row in res.data], ["3851"])

    def test_title_match_does_not_require_a_body_match(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "diabetes"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([row["id"] for row in res.data], ["3853"])
        self.assertIn("overview of diagnosis", res.data[0]["snippet"])

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
        with override_settings(UPTODATE_DB_DIR="/nonexistent/path", UPTODATE_MYSQL_URL=""):
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "x"})
        self.assertEqual(res.status_code, 503)
        self.assertEqual(res.data["code"], "FEATURE_NOT_AVAILABLE")

    def test_requires_authentication(self):
        with self._with_snapshot():
            res = APIClient().get("/api/v1/uptodate/topics/", {"search": "x"})
        self.assertEqual(res.status_code, 401)

    def test_image_returns_base64_with_content_type(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/images/73781/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["content_type"], "image/png")
        self.assertEqual(base64.b64decode(res.data["data_base64"]), b"\x89PNG\r\n\x1a\nfake")

    def test_missing_image_is_404(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/images/000000/")
        self.assertEqual(res.status_code, 404)


class SnippetTests(TestCase):
    HEAD = (
        "Hypertension in adults  Authors:Jane Doe, MD Section Editor:John Roe, MD"
        "Literature review current through:\xa0Jun 2026.\xa0|\xa0This topic last updated:"
        "\xa0Feb 11, 2026.INTRODUCTION\xa0—\xa0Hypertension is common.●Most adults need "
        "two drugs to reach their blood pressure target. (See 'Treatment' below.)The rest follows."
    )

    def test_skips_header_and_run_in_heading(self):
        snippet = services._snippet(self.HEAD, ["hypertension"], "Hypertension in adults")
        self.assertTrue(snippet.startswith("Hypertension is common."))
        self.assertNotIn("Authors", snippet)
        self.assertNotIn("INTRODUCTION", snippet)
        self.assertNotIn("●", snippet)

    def test_centres_on_the_query_hit(self):
        snippet = services._snippet(self.HEAD, ["blood", "pressure"], "Hypertension in adults")
        self.assertIn("blood pressure target", snippet)
        self.assertIn("below.) The rest", snippet)

    def test_reads_the_last_updated_date(self):
        self.assertEqual(services._updated_from_text(self.HEAD.replace("\xa0", " ")), "Feb 11, 2026")
        html = '<span class="emphasis">This topic last updated:</span>&nbsp;Feb 11, 2026.</div>'
        self.assertEqual(services._updated_from_html(html), "Feb 11, 2026")


class MysqlTitleSearchTests(SimpleTestCase):
    @override_settings(UPTODATE_MYSQL_URL="mysql://test:test@localhost/uptodate")
    def test_search_uses_title_index_and_preserves_result_previews(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.return_value = [{
            "title": "Hypertension in adults", "contentId": "3851", "head": SnippetTests.HEAD,
        }]
        with (
            patch.object(services, "_mysql_conn", return_value=connection),
            patch.object(services, "snapshot_version", return_value="202607"),
            patch.object(services, "_section_for", return_value="Cardiovascular Medicine"),
        ):
            results = services.search_topics("HYPERT adu", limit=3)

        sql, params = cursor.execute.call_args.args
        self.assertEqual(sql.count("MATCH(title)"), 2)  # Filtering and ranking.
        self.assertNotIn("MATCH(title, content)", sql)
        self.assertEqual(params, (services.SNIPPET_SOURCE_CHARS, "+HYPERT* +adu*", "+HYPERT* +adu*", 1, 3))
        self.assertEqual(results, [{
            "id": "3851", "title": "Hypertension in adults", "section": "Cardiovascular Medicine",
            "version": "202607", "snippet": services._snippet(SnippetTests.HEAD, ["HYPERT", "adu"], "Hypertension in adults"),
            "updated": "Feb 11, 2026",
        }])

    @override_settings(UPTODATE_MYSQL_URL="mysql://test:test@localhost/uptodate")
    def test_punctuation_only_search_never_connects_to_mysql(self):
        with patch.object(services, "_mysql_conn") as connect:
            self.assertEqual(services.search_topics('"() +-*'), [])
        connect.assert_not_called()


class MysqlTitleIndexTests(SimpleTestCase):
    def setUp(self):
        self.connection = MagicMock()
        self.cursor = self.connection.cursor.return_value.__enter__.return_value

    def test_existing_combined_index_is_not_a_title_only_index(self):
        self.cursor.fetchall.return_value = [
            {"Key_name": "ft_fts_search", "Column_name": "title"},
            {"Key_name": "ft_fts_search", "Column_name": "content"},
        ]
        self.assertTrue(ensure_title_search_index(self.connection))
        self.cursor.execute.assert_any_call("ALTER TABLE fts ADD FULLTEXT INDEX ft_fts_title (title)")

    def test_existing_title_index_is_reused_regardless_of_its_name(self):
        self.cursor.fetchall.return_value = [{"Key_name": "custom_title_index", "Column_name": "title"}]
        self.assertFalse(ensure_title_search_index(self.connection))
        self.assertEqual(self.cursor.execute.call_count, 1)

    def test_concurrent_index_creation_is_idempotent(self):
        self.cursor.fetchall.side_effect = [[], [{"Key_name": "ft_fts_title", "Column_name": "title"}]]
        self.cursor.execute.side_effect = [None, pymysql.err.OperationalError(1061, "Duplicate key name"), None]
        self.assertFalse(ensure_title_search_index(self.connection))

    def test_permission_errors_are_not_silenced(self):
        self.cursor.fetchall.return_value = []
        self.cursor.execute.side_effect = [None, pymysql.err.OperationalError(1142, "ALTER denied")]
        with self.assertRaises(pymysql.err.OperationalError):
            ensure_title_search_index(self.connection)

    def test_duplicate_name_without_required_index_is_not_silenced(self):
        self.cursor.fetchall.return_value = [{"Key_name": "ft_fts_title", "Column_name": "content"}]
        self.cursor.execute.side_effect = [None, pymysql.err.OperationalError(1061, "Duplicate key name"), None]
        with self.assertRaises(pymysql.err.OperationalError):
            ensure_title_search_index(self.connection)

    @override_settings(UPTODATE_MYSQL_URL="")
    def test_deploy_command_does_not_connect_for_sqlite(self):
        with patch("apps.uptodate.management.commands.ensure_uptodate_search_index.pymysql.connect") as connect:
            call_command("ensure_uptodate_search_index", stdout=StringIO())
        connect.assert_not_called()

    @override_settings(UPTODATE_MYSQL_URL="mysql://test:test@localhost/uptodate")
    def test_deploy_command_upgrades_an_existing_mirror_without_local_files(self):
        self.cursor.fetchall.return_value = []
        with patch(
            "apps.uptodate.management.commands.ensure_uptodate_search_index.pymysql.connect",
            return_value=self.connection,
        ):
            call_command("ensure_uptodate_search_index", stdout=StringIO())
        self.cursor.execute.assert_any_call("ALTER TABLE fts ADD FULLTEXT INDEX ft_fts_title (title)")
        self.connection.close.assert_called_once()

    def test_snapshot_import_upgrades_existing_schema_before_copying(self):
        from .management.commands.migrate_uptodate_to_mysql import Command

        self.cursor.fetchall.return_value = []
        Command()._ensure_schema(self.connection)
        self.cursor.execute.assert_any_call("ALTER TABLE fts ADD FULLTEXT INDEX ft_fts_title (title)")
        self.connection.commit.assert_called_once()
