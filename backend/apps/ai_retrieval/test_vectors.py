from io import StringIO
from unittest import SkipTest
from unittest.mock import patch
from types import SimpleNamespace
import uuid
from pathlib import Path
from tempfile import TemporaryDirectory

from django.conf import settings
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import TransactionTestCase, override_settings

from . import embeddings, indexing, vectors
from .models import RetrievalGeneration, SearchChunk


@override_settings(AI_LAB_EMBEDDING_MODEL="text-embedding-3-small", AI_LAB_EMBEDDING_DIMENSIONS=3,
                   AI_LAB_EMBEDDING_BASE_URL="https://embedding.example/v1")
class NativeVectorTests(TransactionTestCase):
    databases = "__all__"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connection = connections[indexing.alias()]
        if connection.vendor != "postgresql":
            raise SkipTest("Native pgvector requires PostgreSQL")
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_available_extensions WHERE name='vector'")
            if cursor.fetchone()[0] != 1:
                raise SkipTest("Optional vector extension is unavailable in this test environment")

    def setUp(self):
        self.profile = embeddings.profile()
        self.generation = RetrievalGeneration.objects.create(source_identity="a"*64, source_revision="b"*64,
            source_generation=uuid.uuid4(), chunker_version="fixture", expected_articles=1, built_articles=1,
            status="ready", scope="pilot", chunk_count=3, embedding_profile=self.profile)
        vectors.ensure_schema()
        self.rows = [SearchChunk.objects.create(generation=self.generation, source_id="10", content_hash="c"*64,
            ordinal=i, title="Reference", heading="Treatment", text="Original paragraph with clinical qualifications.",
            block_ids=[i+1], input_hash=str(i)*64, token_count=10, audience="adult" if i == 0 else "pediatric") for i in range(3)]
        stamp = SimpleNamespace(identity=self.generation.source_identity, revision=self.generation.source_revision)
        source = patch.object(indexing.reference_index, "source_stamp", return_value=stamp)
        source.start(); self.addCleanup(source.stop)
        active = patch.object(indexing.reference_index, "active_generation", return_value=self.generation.source_generation)
        active.start(); self.addCleanup(active.stop)

    def tearDown(self):
        # This optional native table is command-owned. Remove its FKs before
        # Django flushes the model-owned test tables; never touch a live DB.
        with connections[indexing.alias()].cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {vectors.TABLE}")
        super().tearDown()

    def test_actual_vector_storage_hnsw_reuse_and_population_filter(self):
        values = [[1,0,0], [.9,.1,0], [0,1,0]]
        vectors.store(self.generation, self.profile, self.rows, values)
        vectors.store(self.generation, self.profile, self.rows, values)
        self.assertEqual(vectors.count(self.generation, self.profile["id"]), 3)
        self.assertEqual(vectors.missing(self.generation, self.profile["id"], 20), [])
        vectors.create_index(self.generation, self.profile)
        self.generation.embedding_ready = True
        self.generation.save(update_fields=["embedding_ready"])
        result = vectors.search(self.generation, [1,0,0], 2, audience="pediatric")
        self.assertEqual(result, [self.rows[1].pk, self.rows[2].pk])
        self.assertEqual(len(vectors.reuse(self.profile["id"], [r.input_hash for r in self.rows])), 3)

    def test_budget_reservation_precedes_paid_call_and_uncertain_calls_are_not_replayed(self):
        def unavailable(texts):
            self.generation.refresh_from_db()
            self.assertEqual(self.generation.embedding_tokens_reserved, 20)
            self.assertEqual(len(self.generation.pending_embedding_inputs), 2)
            raise RuntimeError("private body must not be printed")
        with patch.object(embeddings, "embed", side_effect=unavailable) as paid:
            with self.assertRaises(CommandError) as caught:
                call_command("embed_hybrid_index", str(self.generation.pk), max_inputs=3, max_tokens=100, batch_size=2, stdout=StringIO())
            self.assertNotIn("private body", str(caught.exception))
            with self.assertRaisesMessage(CommandError, "EMBEDDING_PREVIOUS_REQUEST_UNCERTAIN"):
                call_command("embed_hybrid_index", str(self.generation.pk), max_inputs=3, max_tokens=100, stdout=StringIO())
        paid.assert_called_once()

    def test_resuming_complete_vectors_never_rebills_and_a_budget_stop_never_marks_ready(self):
        with patch.object(embeddings, "embed") as paid:
            call_command("embed_hybrid_index", str(self.generation.pk), max_inputs=1, max_tokens=5, stdout=StringIO())
            self.generation.refresh_from_db()
            self.assertFalse(self.generation.embedding_ready)
            paid.assert_not_called()
            vectors.store(self.generation, self.profile, self.rows, [[1,0,0], [0,1,0], [0,0,1]])
            call_command("embed_hybrid_index", str(self.generation.pk), max_inputs=1, max_tokens=5, stdout=StringIO())
            paid.assert_not_called()
        self.generation.refresh_from_db()
        self.assertTrue(self.generation.embedding_ready)

    def test_keyset_batch_progress_and_restart_do_not_skip_a_missing_lower_uuid(self):
        ordered = sorted(self.rows, key=lambda row: row.pk)
        vectors.store(self.generation, self.profile, [ordered[1]], [[1, 0, 0]])
        self.assertEqual(vectors.missing(self.generation, self.profile["id"], 1), [ordered[0]])
        self.assertEqual(vectors.missing(self.generation, self.profile["id"], 2,
            after_id=ordered[0].pk), [ordered[2]])
        # A new process starts without the cursor and still sees an unfilled
        # lower UUID, even if a previous process had advanced farther.
        self.assertEqual(vectors.missing(self.generation, self.profile["id"], 3), [ordered[0], ordered[2]])

    def test_low_disk_stops_before_paid_work_without_leaving_an_uncertain_reservation(self):
        with patch("apps.ai_retrieval.management.commands.embed_hybrid_index.shutil.disk_usage",
                return_value=SimpleNamespace(free=1024)), patch.object(embeddings, "embed") as paid:
            with self.assertRaisesMessage(CommandError, "EMBEDDING_DISK_RESERVE_REACHED"):
                call_command("embed_hybrid_index", str(self.generation.pk), max_inputs=3, max_tokens=100,
                    min_free_disk_gb=2, stdout=StringIO())
        self.generation.refresh_from_db()
        paid.assert_not_called()
        self.assertEqual(self.generation.embedding_tokens_reserved, 0)
        self.assertEqual(self.generation.pending_embedding_inputs, [])

    def test_source_change_stops_before_next_paid_batch(self):
        def change_source(texts):
            self.generation.refresh_from_db()
            self.generation.source_revision = "changed"
            # Only the process-local generation must retain its old pin.
            indexing.reference_index.source_stamp.return_value = SimpleNamespace(identity="a"*64, revision="changed")
            return [[1, 0, 0] for text in texts], {}
        with patch.object(embeddings, "embed", side_effect=change_source) as paid:
            with self.assertRaisesMessage(CommandError, "REFERENCE_INDEX_STALE"):
                call_command("embed_hybrid_index", str(self.generation.pk), max_inputs=3, max_tokens=100,
                    batch_size=1, stdout=StringIO())
        paid.assert_called_once()
        self.generation.refresh_from_db()
        self.assertFalse(self.generation.embedding_ready)
        self.assertEqual(self.generation.pending_embedding_inputs, [])

    def test_128_input_batch_completes_with_validated_vectors_and_one_request(self):
        with patch.object(embeddings,'embed',return_value=([[1,0,0] for _ in self.rows],{})) as embed:
            call_command('embed_hybrid_index',str(self.generation.pk),max_inputs=3,max_tokens=100,
                         batch_size=128,stdout=StringIO())
        embed.assert_called_once()
        self.generation.refresh_from_db()
        self.assertTrue(self.generation.embedding_ready)
        self.assertEqual(vectors.count(self.generation,self.profile['id']),3)

    def test_foreground_pause_waits_for_committed_batch_and_leaves_no_uncertain_inputs(self):
        with TemporaryDirectory() as directory:
            stop=Path(directory)/'stop'
            def finish_current(texts):
                stop.touch()
                return [[1,0,0] for _ in texts],{}
            with patch.object(embeddings,'embed',side_effect=finish_current) as embed:
                output=StringIO()
                call_command('embed_hybrid_index',str(self.generation.pk),max_inputs=3,max_tokens=100,
                    batch_size=1,stop_file=str(stop),stdout=output)
            embed.assert_called_once()
            self.generation.refresh_from_db()
            self.assertEqual(vectors.count(self.generation,self.profile['id']),1)
            self.assertEqual(self.generation.pending_embedding_inputs,[])
            self.assertFalse(self.generation.embedding_ready)
            self.assertIn('"paused": true',output.getvalue())
