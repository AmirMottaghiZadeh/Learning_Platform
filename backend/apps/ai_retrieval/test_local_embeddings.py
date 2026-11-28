import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock,patch

from django.test import SimpleTestCase,override_settings
from apps.ai_lab import telemetry
from apps.ai_lab.provider import ProviderError
from . import embeddings,local_embeddings


@override_settings(AI_LAB_EMBEDDING_BACKEND="onnx",AI_LAB_EMBEDDING_MODEL="onnx-community/embeddinggemma-300m-ONNX",
    AI_LAB_EMBEDDING_DIMENSIONS=768,AI_LAB_EMBEDDING_REVISION="1",AI_LAB_EMBEDDING_REMOTE_ENABLED=False)
class LocalEmbeddingTests(SimpleTestCase):
    def setUp(self):
        self.directory=TemporaryDirectory();self.addCleanup(self.directory.cleanup)
        self.root=Path(self.directory.name)
        for name in local_embeddings.ARTIFACTS:
            path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes((name+" fixture").encode())
        self.config=override_settings(AI_LAB_LOCAL_EMBEDDING_DIR=str(self.root))
        self.config.enable();self.addCleanup(self.config.disable)

    def test_local_profile_is_bound_to_artifacts_and_is_portable_between_directories(self):
        first=embeddings.profile()
        self.assertEqual(first["backend"],"onnx")
        self.assertNotIn(str(self.root),json.dumps(first))
        (self.root/'tokenizer.json').write_text('different tokenizer fixture')
        self.assertNotEqual(first["id"],embeddings.profile()["id"])

    def test_local_queries_and_documents_use_different_model_prefixes(self):
        self.assertEqual(local_embeddings.format_input('question','query'),'task: search result | query: question')
        self.assertEqual(local_embeddings.format_input('Article\nHeading\nOriginal text','document'),
                         'title: Article | text: Heading\nOriginal text')

    def test_offline_dispatch_never_reads_keys_or_makes_provider_requests(self):
        encoder=Mock();encoder.encode.return_value=([[1.0]+[0.0]*767],{'native_input_tokens':5,'windows':1})
        trace=telemetry.Trace()
        with patch.object(local_embeddings,'_encoder',return_value=encoder),\
             patch.object(embeddings,'credentials',side_effect=AssertionError('No credential access')),\
             patch.object(embeddings.httpx,'Client',side_effect=AssertionError('No HTTP allowed')),trace.activate():
            values,meta=embeddings.embed_query('سؤال آزمایشی')
        self.assertEqual(len(values[0]),768)
        self.assertEqual(encoder.encode.call_args.args[1],'query')
        self.assertEqual(meta['provider_requests'],0)
        self.assertEqual(trace.request_count,0)
        self.assertEqual(meta['paid_input_tokens'],0)

    def test_missing_files_do_not_fall_back_to_a_remote_service(self):
        (self.root/local_embeddings.ARTIFACTS[0]).unlink()
        with patch.object(embeddings.httpx,'Client') as http:
            with self.assertRaisesMessage(ProviderError,'LOCAL_EMBEDDING_MODEL_FILES_REQUIRED'):
                embeddings.embed_query('Question')
        http.assert_not_called()

    def test_remote_embedding_is_explicitly_disabled_even_if_a_key_exists(self):
        with override_settings(AI_LAB_EMBEDDING_BACKEND='openai',AI_LAB_EMBEDDING_API_KEY='test-private-key'),\
             patch.object(embeddings.httpx,'Client') as http:
            with self.assertRaisesMessage(ProviderError,'REMOTE_EMBEDDING_DISABLED'):
                embeddings.embed(['Original text'])
        http.assert_not_called()
