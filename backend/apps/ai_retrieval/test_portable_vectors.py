import gzip
from io import StringIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import SkipTest
from unittest.mock import patch
import uuid

from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import connections
from django.test import TransactionTestCase, override_settings

from apps.ai_lab.provider import ProviderError
from . import embeddings, indexing, portable_vectors as portable, vectors
from .models import RetrievalGeneration, RetrievalHead, SearchChunk


@override_settings(AI_LAB_EMBEDDING_MODEL="text-embedding-3-small",AI_LAB_EMBEDDING_DIMENSIONS=3,
                   AI_LAB_EMBEDDING_BASE_URL="https://embedding.example/v1")
class PortableVectorTests(TransactionTestCase):
    databases = "__all__"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        connection=connections[indexing.alias()]
        if connection.vendor!="postgresql":
            raise SkipTest("Portable vectors need PostgreSQL/pgvector")
        with connection.cursor() as cursor:
            cursor.execute("SELECT count(*) FROM pg_available_extensions WHERE name='vector'")
            if cursor.fetchone()[0]!=1:
                raise SkipTest("Optional pgvector unavailable")

    def setUp(self):
        self.directory=TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.path=Path(self.directory.name)/"vectors.jsonl.gz"
        self.profile=embeddings.profile()
        self.source=RetrievalGeneration.objects.create(source_identity="a"*64,source_revision="b"*64,
            source_generation=uuid.uuid4(),chunker_version="fixture",scope="full",status="ready",
            expected_articles=1,built_articles=1,catalog_ready=True,chunk_count=3,
            embedding_profile=self.profile,embedding_ready=True)
        self.rows=[]
        for n in range(3):
            self.rows.append(SearchChunk.objects.create(generation=self.source,source_id="10",ordinal=n,
                content_hash="c"*64,input_hash=str(n)*64,block_ids=[n+1],title="PRIVATE ORIGINAL TEXT",
                text="PRIVATE ORIGINAL PARAGRAPH",token_count=10))
        vectors.ensure_schema()
        vectors.store(self.source,self.profile,self.rows,[[1,0,0],[0,1,0],[0,0,1]])
        stamp=patch.object(indexing.reference_index,"source_stamp",return_value=SimpleNamespace(
            identity=self.source.source_identity,revision=self.source.source_revision))
        self.stamp=stamp.start();self.addCleanup(stamp.stop)
        active=patch.object(indexing.reference_index,"active_generation",return_value=self.source.source_generation)
        self.active=active.start();self.addCleanup(active.stop)
        paid=patch.object(embeddings,"embed",side_effect=AssertionError("Paid API must never be called"))
        self.paid=paid.start();self.addCleanup(paid.stop)

    def tearDown(self):
        with connections[indexing.alias()].cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {vectors.TABLE}")
        super().tearDown()

    def target(self):
        source=self.source
        target=RetrievalGeneration.objects.create(source_identity="d"*64,source_revision="e"*64,
            source_generation=uuid.uuid4(),chunker_version=source.chunker_version,scope="full",status="ready",
            expected_articles=1,built_articles=1,catalog_ready=True,chunk_count=3)
        for row in self.rows:
            SearchChunk.objects.create(generation=target,source_id=row.source_id,ordinal=row.ordinal,
                content_hash=row.content_hash,input_hash=row.input_hash,title=row.title,text=row.text,
                block_ids=[1000+row.ordinal],token_count=10)
        self.stamp.return_value=SimpleNamespace(identity=target.source_identity,revision=target.source_revision)
        self.active.return_value=target.source_generation
        return target

    def archive(self):
        return portable.export_vectors(self.source,self.path,batch_size=2)

    def test_transfer_remaps_to_destination_chunk_ids_preserves_local_paragraphs_and_never_activates(self):
        exported=self.archive()
        self.assertEqual(self.path.stat().st_mode&0o777,0o600)
        with gzip.open(self.path,"rt") as stream:
            payload=stream.read()
        self.assertNotIn("PRIVATE ORIGINAL",payload)
        self.assertNotIn("block_ids",payload)
        self.assertNotIn(str(self.rows[0].pk),payload)
        target=self.target()
        checked=portable.import_vectors(target,self.path,verify_only=True)
        self.assertEqual(vectors.count(target,self.profile["id"]),0)
        result=portable.import_vectors(target,self.path,batch_size=1,build_index=True)
        self.assertEqual(result["payload_sha256"],exported["payload_sha256"])
        self.assertEqual(checked["verified"],3)
        self.assertEqual(result["imported"],3)
        target.refresh_from_db()
        self.assertTrue(target.embedding_ready)
        self.assertEqual(list(target.chunks.order_by("ordinal").values_list("block_ids",flat=True)),[[1000],[1001],[1002]])
        self.assertFalse(RetrievalHead.objects.exists())
        self.assertEqual(vectors.search(target,[1,0,0],1),[target.chunks.get(ordinal=0).pk])
        self.paid.assert_not_called()

    def test_input_mismatch_and_wrong_footer_stop_before_any_vector_write(self):
        self.archive();target=self.target()
        original=self.path.read_bytes()
        SearchChunk.objects.filter(generation=target,ordinal=2).update(input_hash="f"*64)
        with self.assertRaisesMessage(ProviderError,"VECTOR_ARCHIVE_INPUT_MISMATCH"):
            portable.import_vectors(target,self.path)
        self.assertEqual(vectors.count(target,self.profile["id"]),0)
        SearchChunk.objects.filter(generation=target,ordinal=2).update(input_hash="2"*64)
        lines=gzip.decompress(original).splitlines()
        lines[-1]=json.dumps({"end":3,"sha256":"f"*64}).encode()
        self.path.write_bytes(gzip.compress(b"\n".join(lines)+b"\n"))
        with self.assertRaisesMessage(ProviderError,"VECTOR_ARCHIVE_CHECKSUM_MISMATCH"):
            portable.import_vectors(target,self.path)
        self.assertEqual(vectors.count(target,self.profile["id"]),0)

    def test_resume_committed_batches_reuses_matching_vectors_without_rebilling(self):
        self.archive();target=self.target()
        actual=vectors.store
        def interrupted(generation,profile,rows,values):
            if rows and rows[0].ordinal==1:
                raise RuntimeError("interrupted")
            return actual(generation,profile,rows,values)
        with patch.object(vectors,"store",side_effect=interrupted):
            with self.assertRaisesMessage(RuntimeError,"interrupted"):
                portable.import_vectors(target,self.path,batch_size=1)
        target.refresh_from_db()
        self.assertFalse(target.embedding_ready)
        self.assertEqual(vectors.count(target,self.profile["id"]),1)
        result=portable.import_vectors(target,self.path,batch_size=2)
        self.assertEqual((result["imported"],result["reused"]),(2,1))
        self.assertEqual(result["provider_requests"],0)
        self.paid.assert_not_called()

    def test_active_target_and_wrong_profile_are_rejected(self):
        self.archive();target=self.target()
        RetrievalHead.objects.create(source_identity=target.source_identity,active=target)
        with self.assertRaisesMessage(ProviderError,"VECTOR_IMPORT_TARGET_IS_ACTIVE"):
            portable.import_vectors(target,self.path)
        RetrievalHead.objects.all().delete()
        with override_settings(AI_LAB_EMBEDDING_DIMENSIONS=4):
            with self.assertRaisesMessage(ProviderError,"VECTOR_ARCHIVE_PROFILE_OR_CORPUS_MISMATCH"):
                portable.import_vectors(target,self.path)

    def test_existing_conflicting_vector_is_not_silently_reused(self):
        self.archive();target=self.target()
        row=target.chunks.get(ordinal=0)
        vectors.store(target,self.profile,[row],[[0,1,0]])
        with self.assertRaisesMessage(ProviderError,"VECTOR_IMPORT_EXISTING_MISMATCH"):
            portable.import_vectors(target,self.path)
        target.refresh_from_db()
        self.assertFalse(target.embedding_ready)

    def test_commands_export_and_verify_without_credentials_or_raw_exception_output(self):
        call_command("export_hybrid_vectors",str(self.source.pk),output=str(self.path),stdout=StringIO())
        target=self.target()
        output=StringIO()
        call_command("import_hybrid_vectors",str(target.pk),input=str(self.path),verify_only=True,stdout=output)
        self.assertIn('"provider_requests": 0',output.getvalue())
        with self.assertRaises(CommandError) as caught:
            call_command("import_hybrid_vectors",str(target.pk),input="/missing/private/path",stdout=StringIO())
        self.assertNotIn("/missing/private/path",str(caught.exception))
