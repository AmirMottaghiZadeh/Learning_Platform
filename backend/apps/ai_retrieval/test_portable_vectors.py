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

    def test_skip_verify_scans_once_and_resumes_without_decoding_existing_vector_values(self):
        exported=self.archive();target=self.target()
        saved=list(target.chunks.filter(ordinal__in=[0,2]).order_by("ordinal"))
        vectors.store(target,self.profile,saved,[[1,0,0],[0,0,1]])
        events=[]
        with patch.object(portable,"_scan",wraps=portable._scan) as scan:
            with patch.object(portable,"_decode",wraps=portable._decode) as decode:
                with patch.object(vectors,"store",wraps=vectors.store) as store:
                    result=portable.import_vectors(target,self.path,batch_size=1,skip_verify=True,progress=events.append)
        self.assertEqual(scan.call_count,1)
        # Header, missing middle vector, footer; saved values are not decoded.
        self.assertEqual(decode.call_count,3)
        self.assertEqual(store.call_count,1)
        self.assertEqual((result["imported"],result["reused"]),(1,2))
        self.assertEqual(result["payload_sha256"],exported["payload_sha256"])
        self.assertEqual(events[-1]["imported"],1)
        self.assertEqual(events[-1]["reused"],2)
        self.assertEqual({event["stage"] for event in events},{"import"})
        self.assertFalse(result["index_ready"])
        self.paid.assert_not_called()

    def test_skip_verify_interrupted_batches_resume_and_build_index_without_reinserting(self):
        self.archive();target=self.target()
        actual=vectors.store
        def interrupted(generation,profile,rows,values):
            if rows[0].ordinal==1:
                raise RuntimeError("interrupted")
            return actual(generation,profile,rows,values)
        with patch.object(vectors,"store",side_effect=interrupted):
            with self.assertRaisesMessage(RuntimeError,"interrupted"):
                portable.import_vectors(target,self.path,batch_size=1,skip_verify=True)
        self.assertEqual(vectors.count(target,self.profile["id"]),1)
        result=portable.import_vectors(target,self.path,batch_size=2,skip_verify=True,build_index=True)
        self.assertEqual((result["imported"],result["reused"]),(2,1))
        target.refresh_from_db()
        self.assertTrue(target.embedding_ready)
        self.assertFalse(RetrievalHead.objects.exists())
        self.paid.assert_not_called()

    def test_skip_verify_still_rejects_invalid_footer_and_never_marks_index_ready(self):
        self.archive();target=self.target()
        lines=gzip.decompress(self.path.read_bytes()).splitlines()
        lines[-1]=json.dumps({"end":3,"sha256":"f"*64}).encode()
        self.path.write_bytes(gzip.compress(b"\n".join(lines)+b"\n"))
        with patch.object(vectors,"create_index") as create:
            with self.assertRaisesMessage(ProviderError,"VECTOR_ARCHIVE_CHECKSUM_MISMATCH"):
                portable.import_vectors(target,self.path,skip_verify=True,build_index=True)
        create.assert_not_called()
        target.refresh_from_db()
        self.assertFalse(target.embedding_ready)
        # One-pass mode commits batches before the footer, leaving them resumable.
        self.assertEqual(vectors.count(target,self.profile["id"]),3)

    def test_skip_verify_still_validates_new_vectors_and_header(self):
        self.archive();target=self.target()
        original=gzip.decompress(self.path.read_bytes()).splitlines()
        lines=list(original)
        header=json.loads(lines[0]);header["chunks"]=4
        lines[0]=json.dumps(header).encode()
        self.path.write_bytes(gzip.compress(b"\n".join(lines)+b"\n"))
        with self.assertRaisesMessage(ProviderError,"VECTOR_ARCHIVE_PROFILE_OR_CORPUS_MISMATCH"):
            portable.import_vectors(target,self.path,skip_verify=True)
        self.assertEqual(vectors.count(target,self.profile["id"]),0)
        lines=list(original)
        record=json.loads(lines[1]);record[4]=[0,0,0]
        lines[1]=json.dumps(record).encode()
        self.path.write_bytes(gzip.compress(b"\n".join(lines)+b"\n"))
        with self.assertRaises(ProviderError):
            portable.import_vectors(target,self.path,skip_verify=True)
        self.assertEqual(vectors.count(target,self.profile["id"]),0)

    def test_skip_verify_rejects_mismatched_reused_input_prefix_and_saved_metadata(self):
        self.archive();target=self.target()
        first=target.chunks.get(ordinal=0)
        vectors.store(target,self.profile,[first],[[1,0,0]])
        SearchChunk.objects.filter(pk=first.pk).update(content_hash="f"*64)
        with self.assertRaisesMessage(ProviderError,"VECTOR_ARCHIVE_INPUT_MISMATCH"):
            portable.import_vectors(target,self.path,skip_verify=True)
        SearchChunk.objects.filter(pk=first.pk).update(content_hash=first.content_hash,input_hash="e"*64)
        with self.assertRaisesMessage(ProviderError,"VECTOR_IMPORT_EXISTING_MISMATCH"):
            portable.import_vectors(target,self.path,skip_verify=True)

    def test_skip_verify_command_and_exclusive_flags(self):
        self.archive();target=self.target()
        output=StringIO()
        call_command("import_hybrid_vectors",str(target.pk),input=str(self.path),skip_verify=True,stdout=output)
        self.assertNotIn('"stage": "verify"',output.getvalue())
        self.assertIn('"imported": 3',output.getvalue())
        self.assertIn('"provider_requests": 0',output.getvalue())
        with self.assertRaises(CommandError):
            call_command("import_hybrid_vectors",str(target.pk),input=str(self.path),
                skip_verify=True,verify_only=True,stdout=StringIO())
        with self.assertRaises(ValueError):
            portable.import_vectors(target,self.path,skip_verify=True,verify_only=True)

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
