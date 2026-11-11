from io import StringIO
import json
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import MagicMock, patch
import zlib

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connection, ProgrammingError
from django.test import TestCase, override_settings
from django.test.utils import CaptureQueriesContext

from apps.core.exceptions import PlatformAPIError
from apps.uptodate import services as utd
from apps.uptodate.tests import _make_snapshot
from . import document, reference_index, retrieval
from .models import ReferenceArticle, ReferenceGeneration, ReferenceParagraph, ReferenceSection, ReferenceSource
from .provider import ProviderError
from .management.commands.verify_reference_index import verify_article


TEXT = "An original source paragraph with enough detail and qualifications to be indexed exactly."


def html(heading="Treatment", text=TEXT):
    return f'<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">{heading}</span></p><p>{text}</p></div>'


@override_settings(AI_LAB_PREPROCESSED_MODE="prefer")
class ReferenceIndexTests(TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.directory = Path(tmp.name)
        _make_snapshot(tmp.name)
        with sqlite3.connect(self.directory / "fts.db") as db:
            db.execute("DELETE FROM fts WHERE contentId IN ('3852','3853')")
        self.settings = override_settings(UPTODATE_DB_DIR=tmp.name, UPTODATE_MYSQL_URL="")
        self.settings.enable()
        self.addCleanup(self.settings.disable)
        self.addCleanup(utd.close_all)
        self.write_article("3851", html())

    def write_article(self, identifier, body, *, outline="", title="Reference article"):
        data = {"title": title, "bodyHtml": body, "outlineHtml": outline}
        with sqlite3.connect(self.directory / "content.db") as db:
            db.execute("DELETE FROM content WHERE id=?", (identifier,))
            db.execute("INSERT INTO content VALUES (?,?,?)", (identifier, zlib.compress(json.dumps(data).encode()), "v1"))
        utd.close_all()

    def add_title(self, identifier):
        with sqlite3.connect(self.directory / "fts.db") as db:
            db.execute("INSERT INTO fts (title, displayTitle, type, contentId, content) VALUES (?,?,?,?,?)",
                       ("Extra reference", "Extra reference", 1, identifier, ""))
        utd.close_all()

    def build(self, **options):
        output = StringIO()
        call_command("build_reference_index", workers=1, batch_size=2, stdout=output, **options)
        return ReferenceGeneration.objects.latest("started_at")

    def test_complete_generation_is_published_and_served_without_source_html_or_extraction(self):
        generation = self.build()
        self.assertEqual(generation.status, "ready")
        self.assertEqual(ReferenceSource.objects.get().active_generation_id, generation.pk)
        audit = {}
        with override_settings(AI_LAB_PREPROCESSED_MODE="require"), \
                patch.object(utd, "get_topic", side_effect=AssertionError("No source HTML at runtime")), \
                patch.object(retrieval, "extract_article", side_effect=AssertionError("No parsing at runtime")), \
                CaptureQueriesContext(connection) as queries:
            sections = retrieval.read_sections(["3851"], None, audit)
        self.assertEqual(sections[0]["passages"][0].text, TEXT)
        self.assertEqual(audit["preprocessed_articles"], 1)
        self.assertLessEqual(len(queries), 5)
        self.assertTrue(all(query["sql"].lstrip().upper().startswith("SELECT") for query in queries))

    def test_prepared_output_exactly_matches_legacy_sections_previews_ids_and_targets(self):
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            expected = retrieval.read_sections(["3851"], None, {})
        self.build()
        actual = retrieval.read_sections(["3851"], None, {})
        self.assertEqual(actual, expected)

    def test_nested_outline_keeps_structural_parent_even_without_parent_paragraphs(self):
        body = '<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Treatment</span></p>' \
               '<p class="headingAnchor" id="H2"><span class="h2">Children</span></p><p>' + TEXT + '</p></div>'
        outline = '<ul><li><a id="outline-link-H1">Treatment</a><ul><li><a id="outline-link-H2">Children</a></li></ul></li></ul>'
        self.write_article("3851", body, outline=outline)
        self.build()
        child = ReferenceSection.objects.get(source_id="H2")
        self.assertEqual(child.heading_path, ["Treatment", "Children"])
        self.assertEqual(child.parent.source_id, "H1")
        self.assertIsNone(child.parent.retrieval_order)
        self.assertTrue(child.hierarchy_known)

    def test_all_source_blocks_and_exclusion_reasons_are_saved_without_changing_visible_menu(self):
        body = '<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Treatment</span></p>' \
               '<p>Short.</p><p>' + TEXT + '</p><p>' + ('x' * 6001) + '</p></div>'
        self.write_article("3851", body)
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            legacy = retrieval.read_sections(["3851"], None, {})
        self.build()
        self.assertEqual(set(ReferenceParagraph.objects.values_list("exclusion_reason", flat=True)), {"", "too_short", "too_long"})
        self.assertEqual(ReferenceParagraph.objects.count(), 3)
        self.assertEqual(retrieval.read_sections(["3851"], None, {}), legacy)

    def test_retrieval_order_follows_first_eligible_block_not_structural_order(self):
        body = '<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">First</span></p><p>Short</p>' \
               '<p class="headingAnchor" id="H2"><span class="h1">Second</span></p><p>' + TEXT + '</p>' \
               '<p class="headingAnchor" id="H1"><span class="h1">First</span></p><p>' + TEXT + '</p></div>'
        self.write_article("3851", body)
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            legacy = retrieval.read_sections(["3851"], None, {})
        self.build()
        self.assertEqual(retrieval.read_sections(["3851"], None, {}), legacy)
        self.assertEqual([section["heading"] for section in legacy], ["Second", "First"])

    def test_more_than_sixty_sections_are_preserved_but_current_menu_remains_compatible(self):
        body = '<div id="topicText">' + ''.join(f'<p class="headingAnchor" id="H{n}"><span class="h1">Section {n}</span></p><p>{TEXT}</p>' for n in range(65)) + '</div>'
        self.write_article("3851", body)
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            legacy = retrieval.read_sections(["3851"], None, {})
        self.build()
        self.assertEqual(ReferenceSection.objects.count(), 65)
        self.assertEqual(ReferenceParagraph.objects.count(), 65)
        audit = {}
        self.assertEqual(retrieval.read_sections(["3851"], None, audit), legacy)
        self.assertEqual(len(legacy), 60)
        self.assertTrue(audit["limited"])

    def test_navigation_directory_and_full_monograph_with_same_placeholder_are_distinct(self):
        body = '<div id="formulinkBodyPlaceholder"></div><ul><li><a class="drug" data-topicid="8786" onclick="untrusted()">Drug name</a></li></ul>'
        self.write_article("3851", body)
        self.build()
        article = ReferenceArticle.objects.get()
        self.assertTrue(article.is_directory)
        self.assertFalse(article.paragraphs.filter(retrieval_number__isnull=False).exists())
        audit = {}
        self.assertEqual(retrieval.read_sections(["3851"], None, audit), [])
        self.assertEqual(audit["related_topics"], [{"id": "8786", "title": "Drug name"}])
        self.assertNotIn("limited", audit)
        self.write_article("3851", body + '<div id="F100"><h2>Adverse Reactions</h2><p>' + TEXT + '</p></div>')
        self.build()
        self.assertFalse(ReferenceArticle.objects.latest("generation__started_at").is_directory)

    def test_permission_is_checked_before_index_or_source_access(self):
        with patch.object(retrieval, "require_feature", side_effect=PlatformAPIError("Denied", status_code=402)), \
                patch.object(reference_index, "read_sections") as read:
            with self.assertRaises(PlatformAPIError):
                retrieval.read_sections(["3851"], None, {})
        read.assert_not_called()

    def test_source_change_invalidates_prepared_data_and_prefer_falls_back_to_current_source(self):
        self.build()
        self.write_article("3851", html(text=TEXT + ' A new qualification.'))
        with override_settings(AI_LAB_PREPROCESSED_MODE="require"), self.assertRaisesMessage(ProviderError, "REFERENCE_INDEX_NOT_READY"):
            retrieval.read_sections(["3851"], None, {})
        audit = {}
        sections = retrieval.read_sections(["3851"], None, audit)
        self.assertIn('A new qualification.', sections[0]["passages"][0].text)
        self.assertEqual(audit["preprocessing_fallbacks"], 1)

    def test_failed_refresh_never_replaces_the_previous_active_generation(self):
        original = self.build()
        self.add_title("3852")
        with self.assertRaisesMessage(CommandError, "INDEX_BUILD_INCOMPLETE"):
            self.build()
        self.assertEqual(ReferenceSource.objects.get().active_generation_id, original.pk)
        self.assertEqual(ReferenceGeneration.objects.latest("started_at").status, "failed")

    def test_resume_skips_committed_articles_and_completes_the_manifest(self):
        self.add_title("3852")
        self.write_article("3852", html(text=TEXT + ' Another source.'))
        stamp = reference_index.source_stamp()
        ids = reference_index.source_article_ids()
        generation = reference_index.begin_generation(stamp, ids)
        blob = reference_index.source_blobs(["3851"], stamp.version)[0]
        reference_index.persist_documents(generation, [document.prepare_blob(blob)])
        completed = self.build(resume=generation.pk)
        self.assertEqual(completed.pk, generation.pk)
        self.assertEqual(completed.built_articles, 2)
        self.assertEqual(completed.articles.count(), 2)
        self.assertEqual(ReferenceParagraph.objects.count(), 2)
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            legacy = retrieval.read_sections(ids, None, {})
        self.assertEqual(retrieval.read_sections(ids, None, {}), legacy)

    def test_partial_build_cannot_be_activated_and_is_not_served(self):
        self.add_title("3852")
        self.write_article("3852", html())
        with self.assertRaisesMessage(CommandError, "PARTIAL_INDEX_REQUIRES_NO_ACTIVATE"):
            self.build(limit=1)
        partial = self.build(limit=1, no_activate=True)
        self.assertEqual(partial.scope, "partial")
        self.assertIsNone(ReferenceSource.objects.get().active_generation_id)
        self.assertIsNone(reference_index.active_generation(reference_index.source_stamp()))

    def test_missing_database_schema_falls_back_only_when_configured(self):
        with patch.object(reference_index, "active_generation", side_effect=ProgrammingError("private database details")):
            self.assertTrue(retrieval.read_sections(["3851"], None, {}))
            with override_settings(AI_LAB_PREPROCESSED_MODE="require"), self.assertRaisesMessage(ProviderError, "REFERENCE_INDEX_UNAVAILABLE"):
                retrieval.read_sections(["3851"], None, {})

    def test_changed_extractor_version_or_format_is_never_served(self):
        generation = self.build()
        ReferenceGeneration.objects.filter(pk=generation.pk).update(format_version=999)
        with override_settings(AI_LAB_PREPROCESSED_MODE="require"), self.assertRaisesMessage(ProviderError, "REFERENCE_INDEX_NOT_READY"):
            retrieval.read_sections(["3851"], None, {})

    def test_unchanged_full_build_is_reused_without_reprocessing(self):
        original = self.build()
        with patch("apps.ai_lab.management.commands.build_reference_index.prepare_blob_outcome", side_effect=AssertionError("No redundant extraction")):
            self.build()
        self.assertEqual(ReferenceGeneration.objects.count(), 1)
        self.assertEqual(ReferenceSource.objects.get().active_generation_id, original.pk)

    def test_non_numeric_source_ids_are_preserved_and_indexed(self):
        self.add_title("grades1.html")
        self.write_article("grades1.html", html())
        self.build()
        audit = {}
        sections = retrieval.read_sections(["grades1.html"], None, audit)
        self.assertEqual(sections[0]["passages"][0].target["params"]["id"], "grades1.html")
        self.assertEqual(audit["preprocessed_articles"], 1)

    def test_full_verifier_checks_storage_as_well_as_visible_legacy_output(self):
        generation = self.build()
        valid = verify_article("3851", generation, 1)
        self.assertTrue(valid["storage_matches_source"])
        self.assertTrue(valid["reader_matches_legacy"])
        ReferenceParagraph.objects.update(text="Changed source paragraph that is not the original text.")
        changed = verify_article("3851", generation, 1)
        self.assertFalse(changed["storage_matches_source"])
        self.assertFalse(changed["reader_matches_legacy"])

    def test_mysql_reused_versions_still_detect_changed_compressed_content(self):
        self.build()
        original = reference_index.source_stamp()
        mysql_stamp = reference_index.SourceStamp(original.identity, original.revision, original.version, "mysql")
        remote = MagicMock()
        remote.cursor.return_value.__enter__.return_value.fetchone.return_value = {"blob_hash": "changed"}
        with patch.object(reference_index, "source_stamp", return_value=mysql_stamp), patch.object(reference_index, "mysql_source_connection", return_value=remote):
            with override_settings(AI_LAB_PREPROCESSED_MODE="require"), self.assertRaisesMessage(ProviderError, "REFERENCE_INDEX_STALE"):
                retrieval.read_sections(["3851"], None, {})
            remote.cursor.return_value.__enter__.return_value.fetchone.return_value = {"blob_hash": ReferenceArticle.objects.get().blob_hash}
            audit = {}
            self.assertTrue(retrieval.read_sections(["3851"], None, audit))
            self.assertEqual(audit["preprocessed_articles"], 1)
        remote.cursor.return_value.__enter__.return_value.execute.assert_called_with(
            "SELECT SHA2(gzip, 256) AS blob_hash FROM content WHERE id = %s", ("3851",))

    def test_mysql_source_identity_excludes_connection_credentials(self):
        remote = MagicMock()
        remote.cursor.return_value.__enter__.return_value.fetchone.return_value = {"value": "snapshot-one"}
        with patch.object(reference_index, "mysql_source_connection", return_value=remote):
            with override_settings(UPTODATE_MYSQL_URL="mysql://first:private-one@source.example:3306/references"):
                first = reference_index.source_stamp()
            with override_settings(UPTODATE_MYSQL_URL="mysql://second:private-two@source.example:3306/references"):
                second = reference_index.source_stamp()
        self.assertEqual(first, second)
        self.assertNotIn("private", first.identity)

    def test_mysql_checks_use_autocommit_and_a_connection_per_thread(self):
        from concurrent.futures import ThreadPoolExecutor
        from threading import Barrier, local

        barrier = Barrier(2)
        connections = [MagicMock(), MagicMock()]
        def read(_):
            first = reference_index.mysql_source_connection()
            barrier.wait(timeout=5)
            self.assertIs(first, reference_index.mysql_source_connection())
            return first
        with override_settings(UPTODATE_MYSQL_URL="mysql://user:private@source.example/references"), \
                patch.object(reference_index, "_source_local", local()), \
                patch.object(reference_index.pymysql, "connect", side_effect=connections) as connect:
            with ThreadPoolExecutor(max_workers=2) as executor:
                results = list(executor.map(read, range(2)))
        self.assertIsNot(results[0], results[1])
        self.assertEqual(connect.call_count, 2)
        self.assertTrue(all(call.kwargs["autocommit"] for call in connect.call_args_list))
        self.assertTrue(all(call.kwargs["read_timeout"] == 10 for call in connect.call_args_list))

    def test_conflicting_builder_does_not_change_active_generation(self):
        original = self.build()
        with patch.object(reference_index, "acquire_build_lock", side_effect=ProviderError("REFERENCE_INDEX_BUILD_BUSY")), \
                self.assertRaisesMessage(CommandError, "REFERENCE_INDEX_BUILD_BUSY"):
            self.build(force=True)
        self.assertEqual(ReferenceSource.objects.get().active_generation_id, original.pk)
        self.assertEqual(ReferenceGeneration.objects.count(), 1)
