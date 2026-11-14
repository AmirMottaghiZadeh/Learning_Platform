from io import StringIO
import time
from unittest.mock import patch
from django.test import TestCase, override_settings
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.core.cache import caches
from . import services, reference_index, test_reference_index as fixtures, jobs
from .models import ReferenceArticle
from .outline import OutlineReader
from .provider import ProviderError


class OutlinePipelineTests(TestCase):
    setUp = fixtures.ReferenceIndexTests.setUp
    write_article = fixtures.ReferenceIndexTests.write_article
    add_title = fixtures.ReferenceIndexTests.add_title
    build = fixtures.ReferenceIndexTests.build

    def prepare(self):
        self.write_article('3851', fixtures.html(heading='Treatment'))
        self.build()

    def model(self, alias, system, payload, tokens):
        if system == services.PLAN_PROMPT:
            return {'queries': ['concept'], 'intent': 'adverse_effects', 'requirements': ['adverse_effects']}, {}
        if system == services.ARTICLE_PROMPT:
            self.assertEqual(set(payload['articles'][0]), {'id', 'title'})
            return {'article_ids': [a['id'] for a in payload['articles'][:3]]}, {}
        if system == services.TITLE_PROMPT:
            self.assertTrue(all(set(s) == {'id','article_id','title','path'} for s in payload['sections']))
            return {'section_ids': [s['id'] for s in payload['sections'][:3]]}, {}
        if 'paragraphs' in payload:
            return {'items': [{'source_id': p['id'], 'summary_fa': 'توضیح فارسی بر اساس پاراگراف اصلی'} for p in payload['paragraphs']]}, {}
        ids = [p['id'] for p in payload['items']]
        return {'supported': ids, 'sufficient': True, 'answer_source_ids': ids,
                'coverage': [{'requirement': r, 'status':'supported', 'source_ids':ids} for r in payload['requirements']]}, {}

    def test_outline_queries_no_paragraph_table_until_selection_and_reads_only_selected_sections(self):
        self.write_article('3851', fixtures.html()[:-6] + '<p class="headingAnchor" id="other"><span class="h1">Other section</span></p><p>Unselected source text that must not be sent as evidence to the model.</p></div>')
        self.build()
        with CaptureQueriesContext(connection) as queries:
            reader = OutlineReader(None)
            candidates = reader.candidates([{'id':'3851','title':'original'}])
            headings = reader.headings(candidates)
        self.assertFalse(any('ai_lab_referenceparagraph' in q['sql'].lower() for q in queries))
        self.assertTrue(headings)
        passages = reader.passages([headings[0]['id']])
        self.assertEqual(len(passages), 1)
        self.assertEqual(passages[0].text, fixtures.TEXT)
        self.assertTrue(passages[0].target['params']['searchAnchor'])

    def test_coverage_does_not_skip_remaining_paragraphs_in_selected_section(self):
        body=fixtures.html()[:-6]+''.join(f'<p>{fixtures.TEXT} Distinct paragraph {n}.</p>' for n in range(8))+'</div>'
        self.write_article('3851',body);self.build()
        counts=[]
        def model(*args):
            if 'paragraphs' in args[2]:counts.append(len(args[2]['paragraphs']))
            return self.model(*args)
        with patch.object(services,'search_articles',return_value=[{'id':'3851','title':'original'}]),patch.object(services,'chat',side_effect=model):
            part=services.answer('عارضه دارو چیست؟','luna',['uptodate'],[],None)['parts'][0]
        self.assertEqual(sum(counts),9)
        self.assertEqual(part['retrieval']['reviewed_passages'],9)

    def test_old_selection_flags_cannot_reactivate_body_first_selection(self):
        self.prepare()
        with override_settings(AI_LAB_LEXICAL_ENABLED=False,AI_LAB_LOCAL_SELECTION_ENABLED=False),patch.object(services,'search_articles',return_value=[{'id':'3851','title':'original'}]),patch.object(services,'chat',side_effect=self.model):
            part=services.answer('عارضه دارو چیست؟','luna',['uptodate'],[],None)['parts'][0]
        self.assertEqual(part['retrieval']['selection_engine'],'model_titles_only')

    def test_formulation_directories_resolve_using_metadata_not_article_bodies(self):
        self.add_title('3852');self.write_article('3852',fixtures.html());self.build()
        ReferenceArticle.objects.filter(source_id='3851').update(is_directory=True,related_topics=[{'id':'3852','title':'Related drug monograph'}])
        with CaptureQueriesContext(connection) as queries:
            candidates=OutlineReader(None).candidates([{'id':'3851','title':'Drug directory'}])
        self.assertEqual([a['id'] for a in candidates],['3852'])
        self.assertFalse(any('ai_lab_referenceparagraph' in q['sql'].lower() for q in queries))

    @patch.object(services, 'search_articles')
    def test_order_is_plan_article_titles_section_titles_then_answer_and_verification(self, search):
        self.prepare(); search.return_value=[{'id':'3851','title':'original'}]
        calls=[]
        def model(*args):
            calls.append(args)
            return self.model(*args)
        with patch.object(services, 'chat', side_effect=model):
            result=services.answer('عارضه دارو چیست؟','luna',['uptodate'],[],None)
        self.assertEqual(result['parts'][0]['status'],'answered')
        self.assertEqual(len(calls),5)
        self.assertEqual([c[1] for c in calls[:3]], [services.PLAN_PROMPT, services.ARTICLE_PROMPT, services.TITLE_PROMPT])
        self.assertNotIn(fixtures.TEXT, str([c[2] for c in calls[:3]]))
        self.assertEqual(calls[3][2]['paragraphs'][0]['text'],fixtures.TEXT)

    @patch.object(services, 'search_articles')
    def test_global_three_section_limit_and_multiple_article_citations(self, search):
        for identifier in ['3852','3853']:
            self.add_title(identifier);self.write_article(identifier,fixtures.html())
        self.build()
        search.return_value=[{'id':i,'title':'original'} for i in ['3851','3852','3853']]
        with patch.object(services,'chat',side_effect=self.model):
            part=services.answer('عارضه دارو چیست؟','luna',['uptodate'],[],None)['parts'][0]
        self.assertEqual(part['retrieval']['selected_sections'],3)
        self.assertEqual({i['target']['params']['id'] for i in part['items']},{'3851','3852','3853'})
        self.assertEqual(len({i['source_id'] for i in part['items']}),3)

    @patch.object(services, 'search_articles')
    def test_unknown_or_more_than_three_selections_fail_before_reading_body(self, search):
        self.prepare();search.return_value=[{'id':'3851','title':'original'}]
        for ids in [['invented'],['3851']*4]:
            def model(alias,system,payload,tokens):
                return ({'article_ids':ids},{}) if system==services.ARTICLE_PROMPT else self.model(alias,system,payload,tokens)
            with self.subTest(ids=ids),patch.object(services,'chat',side_effect=model),patch.object(OutlineReader,'passages') as body:
                with self.assertRaises(ProviderError):services.answer('عارضه دارو چیست؟','luna',['uptodate'],[],None)
                body.assert_not_called()

    @patch.object(services, 'search_articles')
    def test_elapsed_time_over_old_deadline_does_not_abort_new_pipeline(self,search):
        self.prepare();search.return_value=[{'id':'3851','title':'original'}]
        with patch.object(services,'chat',side_effect=self.model),patch('apps.ai_lab.telemetry.Trace.elapsed',return_value=90000):
            result=services.answer('عارضه دارو چیست؟','luna',['uptodate'],[],None)
        self.assertEqual(result['parts'][0]['status'],'answered')

    def test_live_new_job_is_not_expired_by_old_total_time(self):
        cache=caches['throttle'];key='ai-lab:job:outline-old'
        cache.set(key,{'user_id':7,'status':'running','pipeline':'outline-v1','created_at':time.time()-10000,
            'heartbeat_at':time.time(),'model':'luna','sources':['uptodate']},60)
        self.addCleanup(cache.delete,key)
        self.assertEqual(jobs.read('outline-old',7)['status'],'running')

    def test_missing_requirement_keeps_supported_answer_partial(self):
        self.prepare()
        def model(*args):
            value,meta=self.model(*args)
            if 'coverage' in value:value['coverage'][0]['status']='missing'
            return value,meta
        with patch.object(services,'search_articles',return_value=[{'id':'3851','title':'original'}]),patch.object(services,'chat',side_effect=model):
            part=services.answer('عارضه دارو چیست؟','luna',['uptodate'],[],None)['parts'][0]
        self.assertEqual(part['status'],'partial')
        self.assertTrue(part['items'])
