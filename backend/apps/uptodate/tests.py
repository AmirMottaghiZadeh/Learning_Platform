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
from .search_catalog import SearchCatalog
from .text import plain_title
from .mysql_schema import ensure_title_search_index
from .search_extraction import extract_article
from apps.core.exceptions import PlatformAPIError


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
        self.assertEqual(res.data[0]["snippet"], "")  # titles only: no body excerpt
        self.assertEqual(res.data[0]["terms"], ["hypertension"])
        self.assertEqual(res.data[0]["corrected"], "")

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

    def test_paged_search_counts_every_match_and_its_sections(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "hypertension", "paged": 1, "limit": 1})
            filtered = self.client.get(
                "/api/v1/uptodate/topics/", {"search": "hypertension", "paged": 1, "section": "Neurology"}
            )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["total"], 1)
        self.assertEqual(res.data["sections"], [{"name": "Cardiovascular Medicine", "count": 1}])
        self.assertEqual([row["id"] for row in res.data["results"]], ["3851"])
        self.assertEqual(filtered.data["total"], 0)
        self.assertEqual(filtered.data["all"], 1)
        self.assertEqual(filtered.data["results"], [])
        self.assertEqual(filtered.data["sections"], res.data["sections"])

    def test_title_match_does_not_require_a_body_match(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "diabetes"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([row["id"] for row in res.data], ["3853"])

    def test_misspelt_word_is_corrected_to_the_closest_title_word(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "hypertention adlts"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([row["id"] for row in res.data], ["3851"])
        self.assertEqual(res.data[0]["corrected"], "hypertension adults")
        self.assertEqual(res.data[0]["terms"], ["hypertension", "adults"])

    def test_word_being_typed_is_corrected_to_a_word_start(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "hipert"})
        self.assertEqual([row["id"] for row in res.data], ["3851"])
        self.assertEqual(res.data[0]["terms"], ["hypert"])

    def test_result_carries_the_date_from_the_topic_header(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/", {"search": "hypertension"})
        self.assertEqual(res.data[0]["updated"], "")  # the fixture's text has no header

    def test_detail_returns_decompressed_article(self):
        with self._with_snapshot():
            res = self.client.get("/api/v1/uptodate/topics/3851/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["title"], "Hypertension in adults")
        self.assertIn("<p>Body.</p>", res.data["body_html"])
        self.assertEqual(res.data["contributors"], ["Jane Doe, MD"])

    @override_settings(OFFLINE_PACKAGE_SECRET="search-supplement-tests")
    def test_old_package_gets_an_encrypted_search_only_supplement(self):
        from apps.offline.pack import derive_key, open_sealed

        _add_concept_snapshot(self._tmp.name)
        build = "uptodate-202607-20261101-abcdef"
        with self._with_snapshot(), patch("apps.offline.services.is_entitled", return_value=True):
            response = self.client.get("/api/v1/uptodate/search-metadata/", {"build": build, "version": "202607"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/octet-stream")
        data = json.loads(zlib.decompress(open_sealed(derive_key(build), response.content)))
        self.assertEqual(data["schema"], 1)
        self.assertEqual(data["memberships"]["140619"], ["Family Medicine", "Gastroenterology"])
        self.assertIn(["h pylori", "1", 100], data["search"]["queries"])
        self.assertNotIn(b"Helicobacter", response.content)
        self.assertNotIn("body_html", data)

    def test_search_supplement_requires_authentication_paid_access_and_matching_version(self):
        url = "/api/v1/uptodate/search-metadata/"
        params = {"build": "uptodate-202607-20261101-abcdef", "version": "202607"}
        self.assertEqual(APIClient().get(url, params).status_code, 401)
        with self._with_snapshot():
            with patch("apps.offline.services.is_entitled", return_value=False):
                self.assertEqual(self.client.get(url, params).status_code, 402)
            with patch("apps.offline.services.is_entitled", return_value=True):
                self.assertEqual(self.client.get(url, {**params, "version": "older"}).status_code, 409)
                self.assertEqual(self.client.get(url, {**params, "build": "uptodate-202606-20261101-abcdef"}).status_code, 409)
                self.assertEqual(self.client.get(url, {**params, "build": "../bad"}).status_code, 400)

    def test_paged_concept_response_serializes_suggestions_and_all_memberships(self):
        _add_concept_snapshot(self._tmp.name)
        with self._with_snapshot():
            response = self.client.get("/api/v1/uptodate/topics/", {"search": "h pylori", "paged": 1, "section": "Gastroenterology"})
        self.assertEqual(response.data["results"][0]["id"], "140619")
        self.assertEqual(response.data["results"][0]["sections"], ["Family Medicine", "Gastroenterology"])
        self.assertEqual(response.data["suggestions"][0]["query"], "h pylori treatment")
        self.assertEqual(response.data["suggestions"][0]["kind"], "treatment")
        self.assertEqual(response.data["suggestions"][0]["count"], 3)
        self.assertIsInstance(response.data["suggestions"][0]["count"], int)

    def test_search_anchor_requires_exact_revision_and_existing_block(self):
        result = extract_article("3851", "<html><body><p>Body.</p></body></html>")
        anchor = result.blocks[0].paragraph_id
        with self._with_snapshot():
            url = "/api/v1/uptodate/topics/3851/"
            matched = self.client.get(url, {"search_content_hash": result.content_hash, "search_anchor": anchor})
            missing = self.client.get(url, {"search_content_hash": result.content_hash, "search_anchor": "utd-" + "0" * 32})
            stale = self.client.get(url, {"search_content_hash": "0" * 64, "search_anchor": anchor})
            invalid = self.client.get(url, {"search_anchor": anchor})
        self.assertEqual(matched.status_code, 200)
        self.assertEqual(matched.data["search_anchor_status"], "matched")
        self.assertIn(anchor, matched.data["body_html"])
        self.assertEqual(missing.data["search_anchor_status"], "missing")
        self.assertNotIn("data-pharmenta-search-anchor", missing.data["body_html"])
        self.assertEqual(stale.data["search_anchor_status"], "stale")
        self.assertNotIn("data-pharmenta-search-anchor", stale.data["body_html"])
        self.assertEqual(invalid.status_code, 400)

    def test_search_anchor_respects_existing_access_control(self):
        result = extract_article("3851", "<html><body><p>Body.</p></body></html>")
        params = {"search_content_hash": result.content_hash, "search_anchor": result.blocks[0].paragraph_id}
        with self._with_snapshot(), patch("apps.uptodate.views.require_feature", side_effect=PlatformAPIError(
            "Access denied", code="PREMIUM_REQUIRED", status_code=402
        )) as check:
            response = self.client.get("/api/v1/uptodate/topics/3851/", params)
        self.assertEqual(response.status_code, 402)
        self.assertNotIn("body_html", response.data)
        self.assertEqual(check.call_args.kwargs, {"item": "3851", "consume": True})

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


class HeaderTextTests(SimpleTestCase):
    HEAD = (
        "Hypertension in adults  Authors:Jane Doe, MD Section Editor:John Roe, MD"
        "Literature review current through:\xa0Jun 2026.\xa0|\xa0This topic last updated:"
        "\xa0Feb 11, 2026.INTRODUCTION\xa0—\xa0Hypertension is common.●Most adults need "
        "two drugs to reach their blood pressure target. (See 'Treatment' below.)The rest follows."
    )

    def test_skips_header_and_run_in_heading(self):
        text = services.snippet_source(self.HEAD, "Hypertension in adults")
        self.assertTrue(text.startswith("Hypertension is common."))
        self.assertNotIn("Authors", text)
        self.assertNotIn("INTRODUCTION", text)
        self.assertNotIn("●", text)
        self.assertIn("below.) The rest", text)

    def test_reads_the_last_updated_date(self):
        self.assertEqual(services._updated_from_text(self.HEAD.replace("\xa0", " ")), "Feb 11, 2026")
        html = '<span class="emphasis">This topic last updated:</span>&nbsp;Feb 11, 2026.</div>'
        self.assertEqual(services._updated_from_html(html), "Feb 11, 2026")


def _add_concept_snapshot(directory):
    """Real source shapes: aliases, ranked associations and multiple TOC paths."""
    directory = Path(directory)
    titles = {
        "140619": "Treatment of <i>Helicobacter pylori</i> infection in adults",
        "18": "Approach to the diagnosis of Helicobacter pylori infection in adults",
        "2012": "Patient education: H. pylori infection",
        "5890": "Infantile hypertrophic pyloric stenosis",
        "14409": "Helicobacter pylori: Diagnosis and management in children",
    }
    with sqlite3.connect(directory / "fts.db") as db:
        db.executemany("INSERT INTO fts(title,displayTitle,type,contentId,content) VALUES(?,?,?,?,?)",
                       [(title, title, 1, cid, "This topic last updated: Feb 11, 2026.") for cid, title in titles.items()])
    with sqlite3.connect(directory / "content.db") as db:
        for cid, title in titles.items():
            doc = {"title": title, "bodyHtml": '<p id="H1">Body &lt;em&gt;versus&lt;/em&gt; placebo. Age &lt;7 and dose &gt;5.</p>'}
            db.execute("INSERT INTO content VALUES(?,?,?)", (cid, zlib.compress(json.dumps(doc).encode()), "202607"))
    with sqlite3.connect(directory / "toc.db") as db:
        db.executemany("INSERT INTO toc VALUES(?,?,?,?,?)", [
            (20, "Family Medicine", 0, "", None), (21, "Gastroenterology", 0, "", None),
            (22, titles["140619"], 20, "", "140619"), (23, titles["140619"], 21, "", "140619"),
            (24, titles["140619"], 21, "", "140619"),  # duplicate path must not double-count
            (25, titles["18"], 21, "", "18"), (26, titles["14409"], 21, "", "14409"),
        ])
    with sqlite3.connect(directory / "search.db") as db:
        db.executescript('''CREATE TABLE query(id INTEGER, word TEXT, weight INTEGER);
            CREATE TABLE query_topic(id INTEGER PRIMARY KEY, x_topic_hits TEXT, a_topic_hits TEXT, p_topic_hits TEXT, i_topic_hits TEXT);''')
        db.executemany("INSERT INTO query VALUES(?,?,?)", [
            (1, "h pylori", 100), (1, "helicobacter pylori", 90),
            (1, "pylori (helicobacter pylori)", 80),
            (2, "h pylori treatment", 150), (2, "treatment of h pylori", 100),
            (3, "h pylori testing", 80), (3, "h pylori diagnosis", 60),
        ])
        db.executemany("INSERT INTO query_topic VALUES(?,?,?,?,?)", [
            (1, "140619,18,14409,2012,missing", "140619,18", "14409,18", "2012"),
            (2, "140619,14409,2012", "140619", "14409", "2012"),
            (3, "18,14409", "18", "14409", "2012"),
        ])


class SnapshotSearchRegressionTests(SimpleTestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(services.close_all)
        _make_snapshot(tmp.name)
        _add_concept_snapshot(tmp.name)
        self.settings = override_settings(UPTODATE_DB_DIR=tmp.name, UPTODATE_MYSQL_URL="")
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        services.close_all()

    def test_abbreviation_and_full_name_use_the_same_curated_order(self):
        for query in ("h pylori", "H. pylori", "helicobacter pylori", "pylori"):
            page = services.search_page(query)
            self.assertEqual(page["results"][0]["id"], "140619")
            self.assertNotIn("5890", [r["id"] for r in page["results"]])
            self.assertNotIn("missing", [r["id"] for r in page["results"]])
            self.assertEqual(page["corrected"], "")

    def test_every_specialty_keeps_treatment_and_counts_it_once(self):
        page = services.search_page("h pylori", section="Gastroenterology")
        self.assertEqual(page["results"][0]["id"], "140619")
        self.assertEqual(page["results"][0]["section"], "Gastroenterology")
        self.assertEqual(page["results"][0]["sections"], ["Family Medicine", "Gastroenterology"])
        self.assertEqual(next(s["count"] for s in page["sections"] if s["name"] == "Gastroenterology"), 3)

    def test_suggestions_are_distinct_concepts_and_are_actionable(self):
        suggestions = services.search_page("h pylori")["suggestions"]
        self.assertEqual([s["query"] for s in suggestions], ["h pylori treatment", "h pylori testing"])
        self.assertEqual(services.search_page(suggestions[0]["query"])["results"][0]["id"], "140619")
        self.assertEqual([(s["kind"], s["count"]) for s in suggestions], [("treatment", 3), ("diagnosis", 2)])

    def test_partial_suggestions_keep_priority_deduplicate_hits_and_classify_test_of_cure(self):
        from .search_catalog import SearchCatalog
        catalog = SearchCatalog(
            [["h pylori test of cure", "cure", 20], ["h pylori treatment", "tx", 100],
             ["h pylori diagnosis", "dx", 50], ["h pylori treatment adult", "tx", 30]],
            {"cure": ["18,18,missing", "", "", ""], "tx": ["140619,18", "140619", "", ""],
             "dx": ["18,missing", "", "", ""]},
        )
        suggestions = catalog.suggest("h py", {"18", "140619"})
        self.assertEqual([(s["kind"], s["count"]) for s in suggestions], [("treatment", 2), ("diagnosis", 1), ("followup", 1)])
        self.assertEqual(suggestions[0]["query"], "h pylori treatment")
        self.assertEqual(catalog.suggest("h", {"18", "140619"}), [])

    def test_unknown_qualifier_is_not_dropped_and_pediatric_audience_is_used(self):
        self.assertEqual(services.search_page("h pylori zzzzzz")["total"], 0)
        page = services.search_page("h pylori children")
        self.assertEqual([r["id"] for r in page["results"]], ["14409"])

    def test_normalizes_titles_but_preserves_original_body_and_anchor_revision(self):
        article = services.get_topic("140619")
        self.assertEqual(article["title"], "Treatment of Helicobacter pylori infection in adults")
        self.assertIn("&lt;em&gt;versus&lt;/em&gt;", article["body_html"])
        self.assertEqual(article["sections"], ["Family Medicine", "Gastroenterology"])
        for value in ("Age <7 and dose >5", "Age &lt;7 and dose &gt;5", "Age &amp;lt;7 and dose &amp;gt;5"):
            self.assertEqual(plain_title(value), "Age <7 and dose >5")
        self.assertEqual(plain_title("&amp;lt;i&amp;gt;H. pylori&amp;lt;/i&amp;gt;&nbsp;≥5"), "H. pylori ≥5")

    def test_catalog_is_reused_until_the_snapshot_is_closed(self):
        catalog = services._search_catalog(services.snapshot_version())
        self.assertIs(catalog, services._search_catalog(services.snapshot_version()))

    @override_settings(UPTODATE_MYSQL_URL="mysql://test:test@localhost/uptodate")
    def test_mysql_reads_the_same_source_tables(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect = [
            [{"id": 1, "word": "H. pylori", "weight": 100}],
            [{"id": 1, "x_topic_hits": "140619,18", "a_topic_hits": "140619", "p_topic_hits": "", "i_topic_hits": ""}],
        ]
        with patch.object(services, "_mysql_conn", return_value=connection):
            catalog = services._search_catalog("mysql-test")
        self.assertEqual(catalog.resolve("h pylori")[0], "1")
        self.assertEqual(catalog.hits("1", "h pylori"), ["140619", "18"])



class MysqlTitleSearchTests(SimpleTestCase):
    def tearDown(self):
        services._title_index.cache_clear()
        services._term.cache_clear()

    @override_settings(UPTODATE_MYSQL_URL="mysql://test:test@localhost/uptodate")
    def test_titles_are_read_once_and_only_result_headers_after(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchall.side_effect = [
            [
                {"rowid": 1, "contentId": "3851", "title": "Hypertension in adults"},
                {"rowid": 3, "contentId": "3853", "title": "Diabetes mellitus"},
            ],
            [{"rowid": 1, "head": HeaderTextTests.HEAD}],
            [],  # the second search needs no header: the date is kept
        ]
        with (
            patch.object(services, "_mysql_conn", return_value=connection),
            patch.object(services, "snapshot_version", return_value="202607"),
            patch.object(services, "_section_memberships_for", side_effect=lambda ids: {i: ["Cardiovascular Medicine"] for i in ids}),
            patch.object(services, "_search_catalog", return_value=SearchCatalog([], {})),
        ):
            results = services.search_topics("HYPERT adu", limit=3)
            again = services.search_topics("hypertension", limit=3)

        statements = [call.args[0] for call in cursor.execute.call_args_list]
        self.assertEqual(len(statements), 2)
        self.assertIn("SELECT rowid, contentId, title FROM fts WHERE type = %s", statements[0])
        self.assertIn("LEFT(content, %s) AS head FROM fts WHERE rowid IN (%s)", statements[1])
        self.assertFalse(any("MATCH" in sql for sql in statements))
        self.assertEqual(results, [{
            "id": "3851", "title": "Hypertension in adults", "section": "Cardiovascular Medicine", "sections": ["Cardiovascular Medicine"],
            "version": "202607", "snippet": "", "updated": "Feb 11, 2026",
            "terms": ["hypert", "adu"], "corrected": "",
        }])
        self.assertEqual(again[0]["updated"], "Feb 11, 2026")

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


class TitleSearchTests(SimpleTestCase):
    """The title search over a made-up set of titles."""

    def page(self, query, titles, limit=10, offset=0, section=""):
        index = services.build_title_index((i + 1, str(100 + i), t) for i, t in enumerate(titles))
        index.updated.update({i + 1: "" for i in range(len(titles))})
        services._term.cache_clear()
        self.addCleanup(services._term.cache_clear)
        with (
            patch.object(services, "_title_index", return_value=index),
            patch.object(services, "snapshot_version", return_value="test"),
            patch.object(services, "_search_catalog", return_value=SearchCatalog([], {})),
            patch.object(services, "_section_memberships_for", side_effect=lambda ids: {i: [self.sections[i]] if self.sections.get(i) else [] for i in ids}),
        ):
            return services.search_page(query, limit=limit, offset=offset, section=section)

    sections: dict = {}

    def search(self, query, titles, limit=10, offset=0, section=""):
        return self.page(query, titles, limit, offset, section)["results"]

    def titles(self, query, titles):
        return [r["title"] for r in self.search(query, titles)]

    def test_words_match_starts_of_title_words_in_any_order(self):
        titles = ["Asthma in adults", "Adult asthma treatment", "Pneumonia in adults"]
        self.assertEqual(sorted(self.titles("adu asth", titles)), ["Adult asthma treatment", "Asthma in adults"])

    def test_one_typo_in_a_short_word_and_more_in_a_long_one(self):
        titles = ["Asthma in adults", "Anaphylaxis: Emergency treatment", "Phenytoin poisoning"]
        self.assertEqual(self.titles("asthama", titles), ["Asthma in adults"])
        self.assertEqual(self.titles("anafilaxis", titles), ["Anaphylaxis: Emergency treatment"])
        self.assertEqual(self.titles("fenytoin", titles), ["Phenytoin poisoning"])

    def test_swapped_letters_count_as_one_typo(self):
        self.assertEqual(self.titles("ashtma", ["Asthma in adults"]), ["Asthma in adults"])

    def test_the_correction_is_reported(self):
        results = self.search("pnemonia adults", ["Pneumonia in adults"])
        self.assertEqual(results[0]["corrected"], "pneumonia adults")
        self.assertEqual(results[0]["terms"], ["pneumonia", "adults"])

    def test_a_tie_goes_to_the_word_more_titles_share(self):
        titles = ["Leukemia in children", "Acute leukemia", "Lukemia virus (made up)"]
        # "lukemi" is one typo from both; "leukemia" is in more titles
        self.assertEqual(self.search("lukemi", titles)[0]["terms"], ["lukemi"])  # a real start: kept
        self.assertEqual(self.search("lukemya", titles[:2])[0]["corrected"], "leukemia")

    def test_too_short_or_too_far_words_are_not_corrected(self):
        titles = ["Asthma in adults"]
        self.assertEqual(self.search("xq", titles), [])
        self.assertEqual(self.search("zzzzzz", titles), [])

    def test_a_plural_also_finds_the_singular(self):
        titles = ["Infection prevention", "Infections of the skin", "Infectious mononucleosis"]
        found = self.titles("infections", titles)
        self.assertEqual(sorted(found), ["Infection prevention", "Infections of the skin"])
        # a word whose singular is no title word stays as typed
        self.assertEqual(self.titles("diabetes", ["Diabetes mellitus", "Diabetic foot"]), ["Diabetes mellitus"])

    def test_tags_in_a_title_are_not_words(self):
        titles = ["Infections due to <i>Serratia</i> species"]
        self.assertEqual(self.titles("serratia", titles), ["Infections due to Serratia species"])
        index = services.build_title_index([(1, "1", titles[0])])
        self.assertEqual(index.words[0], ["infections", "due", "to", "serratia", "species"])

    def test_ranking(self):
        titles = [
            "Asthma in pregnancy and lactation",
            "Asthmatic bronchitis",
            "Patient education: Asthma in adults (The Basics)",
            "Asthma",
            "Asthma in adults",
            "Overview of asthma in adults",
            "Genetics of asthma",
        ]
        self.assertEqual(self.titles("asthma", titles), [
            "Asthma",  # the title is the query
            "Overview of asthma in adults",  # the overview
            "Asthma in adults",  # no other word that narrows it
            "Genetics of asthma",  # one
            "Asthma in pregnancy and lactation",  # two
            "Patient education: Asthma in adults (The Basics)",  # for patients
            "Asthmatic bronchitis",  # only the start of a word
        ])

    def test_every_title_with_the_word_is_found_wherever_it_sits(self):
        titles = [f"Hypertension topic {n}" for n in range(40)] + ["Overview of hypertension in adults"]
        page = self.page("hypertension", titles, limit=25)
        self.assertEqual(page["total"], 41)
        self.assertEqual(page["results"][0]["title"], "Overview of hypertension in adults")
        rest = self.page("hypertension", titles, limit=25, offset=25)["results"]
        found = {r["title"] for r in page["results"]} | {r["title"] for r in rest}
        self.assertEqual(found, set(titles))

    def test_a_longer_word_is_also_found_inside_title_words(self):
        titles = ["Hyperkalemia in adults", "Hypokalemia in children", "Kale (made up)", "Malaria"]
        found = self.titles("kalemia", titles)
        self.assertEqual(sorted(found), ["Hyperkalemia in adults", "Hypokalemia in children"])
        # at a word's start ranks first
        self.assertEqual(self.titles("kale", titles)[0], "Kale (made up)")
        # three letters only ever match a word's start
        self.assertEqual(self.titles("lem", titles), [])
        # found inside a word is no misspelling: nothing is corrected
        self.assertEqual(self.page("kalemia", titles)["corrected"], "")

    def test_sections_are_counted_over_every_match_and_one_can_be_picked(self):
        titles = ["Asthma in adults", "Asthma in children", "Asthma and pregnancy"]
        self.sections = {"100": "Pulmonary", "101": "Pediatrics", "102": "Pulmonary"}
        self.addCleanup(setattr, self, "sections", {})
        page = self.page("asthma", titles, limit=1)
        self.assertEqual(page["total"], 3)
        self.assertEqual(page["sections"], [{"name": "Pulmonary", "count": 2}, {"name": "Pediatrics", "count": 1}])
        picked = self.page("asthma", titles, section="Pediatrics")
        self.assertEqual(picked["total"], 1)
        self.assertEqual(picked["all"], 3)
        self.assertEqual([r["title"] for r in picked["results"]], ["Asthma in children"])
        self.assertEqual(picked["sections"], page["sections"])

    def test_limit(self):
        titles = [f"Asthma {n}" for n in range(30)]
        self.assertEqual(len(self.search("asthma", titles, limit=5)), 5)


class SectionLookupTests(SimpleTestCase):
    def test_sections_of_many_topics_take_one_query_per_tree_level(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.addCleanup(services.close_all)
        toc = sqlite3.connect(Path(tmp.name) / "toc.db")
        toc.execute("CREATE TABLE toc (id INTEGER, title TEXT, parentId INTEGER, section TEXT, contentId TEXT)")
        toc.executemany("INSERT INTO toc VALUES (?,?,?,?,?)", [
            (1, "Cardiovascular Medicine", 0, "", None),
            (2, "Neurology", None, "", None),
            (10, "Hypertension", 1, "", None),
            (100, "Topic A", 10, "", "1"),
            (101, "Topic B", 2, "", "2"),
            (102, "Topic C", 1, "", "3"),
            (103, "Orphan", 999, "", "4"),
        ])
        toc.commit()
        toc.close()
        with override_settings(UPTODATE_DB_DIR=tmp.name, UPTODATE_MYSQL_URL=""):
            services.close_all()
            with patch.object(services, "_SECTION_BATCH", 2):
                found = services._sections_for(["1", "2", "3", "4", "5"])
            self.assertEqual(found, {
                "1": "Cardiovascular Medicine", "2": "Neurology", "3": "Cardiovascular Medicine", "4": "", "5": "",
            })
            # kept: asked again, nothing is read
            with patch.object(services, "_toc_rows", side_effect=AssertionError("read again")):
                self.assertEqual(services._section_for("2"), "Neurology")


class TypoDistanceTests(SimpleTestCase):
    def test_whole_word(self):
        self.assertEqual(services._typo_distance("pnemonia", "pneumonia", 2, False), (1, 9))
        self.assertEqual(services._typo_distance("ashtma", "asthma", 1, False), (1, 6))
        self.assertIsNone(services._typo_distance("asthma", "pneumonia", 2, False))

    def test_start_of_a_word(self):
        # "pnemo" is one edit from "pneumo", the start of "pneumonia"
        self.assertEqual(services._typo_distance("pnemo", "pneumonia", 2, True), (1, 6))
        self.assertEqual(services._typo_distance("pneum", "pneumonia", 2, True), (0, 5))
