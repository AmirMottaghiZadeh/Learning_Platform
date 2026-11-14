import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
import uuid

from django.test import SimpleTestCase, TestCase, override_settings
from apps.ai_lab.provider import ProviderError
from . import chunking, embeddings, indexing
from .models import RetrievalGeneration, RetrievalHead


class ChunkingTests(SimpleTestCase):
    def paragraph(self, n, text, *, section=1, eligible=True, path=("Dosing: Pediatric", "Nocturnal enuresis")):
        return SimpleNamespace(pk=n, text=text, section_id=section,
            section=SimpleNamespace(heading=path[-1], heading_path=list(path)),
            retrieval_number=n if eligible else None)

    def chunks(self, paragraphs):
        return list(chunking.article_chunks(SimpleNamespace(source_id="10", title="Desmopressin: Drug information",
            content_hash="a"*64), paragraphs, uuid.UUID(int=1)))

    def test_preserves_original_dose_blocks_and_citation_mapping(self):
        texts = ["Children: use this medicine only for the stated indication.",
                 "Oral: 0.2 mg once daily; titrate only as directed in this source.",
                 "Restrict fluids as specified for the same patient population."]
        rows = self.chunks([self.paragraph(i, text) for i, text in enumerate(texts, 1)])
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["text"], "\n\n".join(texts))
        self.assertEqual(rows[0]["block_ids"], [1, 2, 3])
        self.assertEqual(rows[0]["audience"], "pediatric")

    def test_never_crosses_sections_or_excluded_blocks(self):
        rows = self.chunks([self.paragraph(1, "First context."), self.paragraph(2, "Excluded", eligible=False),
                            self.paragraph(3, "Second context."), self.paragraph(4, "Other section.", section=2)])
        self.assertEqual([row["block_ids"] for row in rows], [[1], [3], [4]])

    def test_long_block_is_not_truncated_and_hash_changes_with_context(self):
        text = "Original dose and qualifier. " * 1000
        row = self.chunks([self.paragraph(1, text)])[0]
        self.assertEqual(row["text"], text)
        self.assertGreater(row["token_count"], chunking.TARGET_TOKENS)
        other = self.chunks([self.paragraph(1, text, path=("Dosing: Adult", "Other indication"))])[0]
        self.assertNotEqual(row["input_hash"], other["input_hash"])

    def test_adult_heading_overrides_pediatric_title(self):
        audience, _ = chunking.source_metadata("Amoxicillin: Pediatric drug information", ["Dosing: Adult", "Sinusitis"])
        self.assertEqual(audience, "adult")
        audience, _ = chunking.source_metadata("Amoxicillin: Drug information", ["Dosing: Pediatric", "Sinusitis"])
        self.assertEqual(audience, "pediatric")


@override_settings(AI_LAB_EMBEDDING_MODEL="text-embedding-3-small", AI_LAB_EMBEDDING_DIMENSIONS=3,
                   AI_LAB_EMBEDDING_BACKEND="openai", AI_LAB_EMBEDDING_REMOTE_ENABLED=True,
                   AI_LAB_EMBEDDING_BASE_URL="https://embedding.example/v1", AI_LAB_EMBEDDING_REVISION="1",
                   AI_LAB_EMBEDDING_API_KEY="test-embedding-secret", AI_LAB_EMBEDDING_USE_CHAT_KEY=False)
class EmbeddingTests(SimpleTestCase):
    def response(self, data, status=200):
        client = MagicMock()
        response = client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value
        response.status_code = status
        response.iter_bytes.return_value = [json.dumps(data).encode()]
        return client

    def test_reorders_validates_normalizes_and_does_not_return_vectors_as_metadata(self):
        client = self.response({"model":"text-embedding-3-small", "data":[
            {"index":1,"embedding":[0, 3, 0]}, {"index":0,"embedding":[2, 0, 0]}], "usage":{"prompt_tokens":3,"private":"hidden"}})
        with patch.object(embeddings.httpx, "Client", client):
            vectors, meta = embeddings.embed(["first", "second"])
        self.assertEqual(vectors, [[1,0,0],[0,1,0]])
        self.assertEqual(meta["usage"], {"prompt_tokens":3})
        self.assertNotIn("test-embedding-secret", json.dumps(meta))

    def test_rejects_invalid_vectors_duplicate_indexes_and_model_substitution(self):
        for data in [
            {"model":"other", "data":[]},
            {"data":[{"index":0,"embedding":[0,0,0]}]},
            {"data":[{"index":0,"embedding":[1,2]}]},
            {"data":[{"index":True,"embedding":[1,2,3]}]},
            {"data":[{"index":0,"embedding":[True,2,3]}]},
            {"data":[{"index":0,"embedding":[float('nan'),2,3]}]},
        ]:
            with self.subTest(data=data), patch.object(embeddings.httpx,"Client", self.response(data)):
                with self.assertRaises(ProviderError): embeddings.embed(["test"])

    def test_non_200_never_reads_error_body_or_replays_request(self):
        client = self.response({"secret":"must not read"}, 429)
        with patch.object(embeddings.httpx,"Client", client):
            with self.assertRaisesMessage(ProviderError,"EMBEDDING_HTTP_ERROR"):embeddings.embed(["test"])
        client.return_value.__enter__.return_value.stream.assert_called_once()
        client.return_value.__enter__.return_value.stream.return_value.__enter__.return_value.iter_bytes.assert_not_called()

    def test_chat_key_reuse_requires_explicit_opt_in_and_same_provider(self):
        with override_settings(AI_LAB_EMBEDDING_API_KEY=""), patch.object(embeddings,"credentials") as credentials:
            with self.assertRaisesMessage(ProviderError,"EMBEDDING_KEY_NOT_CONFIGURED"): embeddings.api_key()
            with override_settings(AI_LAB_EMBEDDING_USE_CHAT_KEY=True, AI_LAB_BASE_URL="https://other.example/v1"):
                with self.assertRaisesMessage(ProviderError,"EMBEDDING_KEY_PROVIDER_MISMATCH"): embeddings.api_key()
            credentials.assert_not_called()

    def test_invalid_url_does_not_send_any_credentials(self):
        for url in ["http://example.com", "https://user:secret@example.com", "https://example.com?key=secret", "https://example.com:bad"]:
            with self.subTest(url=url), override_settings(AI_LAB_EMBEDDING_BASE_URL=url), patch.object(embeddings.httpx,"Client") as client:
                with self.assertRaises(ProviderError): embeddings.embed(["test"])
                client.assert_not_called()


class IndexActivationTests(TestCase):
    databases = "__all__"

    def test_partial_generation_can_never_become_active(self):
        generation = RetrievalGeneration.objects.create(source_identity="a"*64, source_revision="b"*64,
            source_generation=uuid.uuid4(), chunker_version=chunking.CHUNKER_VERSION,
            scope="pilot", status="ready", expected_articles=1, built_articles=1, catalog_ready=True)
        stamp = SimpleNamespace(identity="a"*64, revision="b"*64)
        with patch.object(indexing.reference_index,"source_stamp",return_value=stamp):
            with self.assertRaisesMessage(ProviderError,"HYBRID_INDEX_NOT_READY"):
                indexing.activate_generation(generation,require_embeddings=False)
        self.assertFalse(RetrievalHead.objects.exists())
