from uuid import uuid4
from unittest.mock import patch
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import connections, OperationalError
from django.test import TestCase, override_settings
from rest_framework.test import APIClient
from . import services
from .models import SearchAnswer, SearchFeedback
from .router import FeedbackRouter


@override_settings(AI_LAB_ENABLED=True, AI_LAB_FEEDBACK_ENABLED=True)
class FeedbackTests(TestCase):
    databases={'default','ai_feedback'}

    def setUp(self):
        self.user=get_user_model().objects.create_superuser('feedback-owner','owner@example.test','fixture')
        self.other=get_user_model().objects.create_superuser('feedback-other','other@example.test','fixture')
        self.client=APIClient();self.client.force_authenticate(self.user)
        self.job=uuid4();self.url=f'/api/v1/ai-lab/results/{self.job}/feedback/'
        self.result={'parts':[{'intent':'drug_therapy','items':[],'status':'partial'}], 'pipeline':'uptodate-outline-v1'}
        self.assertTrue(services.save_answer(self.job,self.user,'پرسش اصلی',self.result))

    def test_real_storage_is_in_separate_database_and_not_default_schema(self):
        self.assertNotEqual(settings.DATABASES['default']['NAME'],settings.DATABASES['ai_feedback']['NAME'])
        self.assertEqual(SearchAnswer.objects.get(pk=self.job)._state.db,'ai_feedback')
        self.assertNotIn(SearchAnswer._meta.db_table,connections['default'].introspection.table_names())
        self.assertIn(SearchAnswer._meta.db_table,connections['ai_feedback'].introspection.table_names())
        self.assertFalse(FeedbackRouter().allow_migrate('default','ai_feedback'))
        self.assertFalse(FeedbackRouter().allow_migrate('ai_feedback','auth'))

    def test_vote_change_is_idempotent_and_question_answer_are_server_owned(self):
        self.assertIsNone(self.client.get(self.url).json()['value'])
        for vote in [1,1,-1]:
            response=self.client.post(self.url,{'value':vote,'question':'forged','result':{}},format='json')
            self.assertEqual(response.status_code,200)
        self.assertEqual(SearchFeedback.objects.count(),1)
        self.assertEqual(self.client.get(self.url).json()['value'],-1)
        saved=SearchAnswer.objects.get(pk=self.job)
        self.assertEqual(saved.question,'پرسش اصلی')
        self.assertEqual(saved.result,self.result)
        self.assertEqual(saved.question_types,['drug_therapy'])

    def test_other_account_cannot_read_or_rate_and_invalid_value_rejected(self):
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get(self.url).status_code,404)
        self.assertEqual(self.client.post(self.url,{'value':1}).status_code,404)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(self.url,{'value':3}).status_code,400)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.post(self.url,{'value':1}).status_code,401)

    def test_store_failure_is_explicit_without_leaking_connection_details(self):
        with patch.object(services.SearchAnswer.objects,'get',side_effect=OperationalError('private-connection-secret')):
            response=self.client.post(self.url,{'value':1})
        self.assertEqual(response.status_code,503)
        self.assertNotIn('private-connection-secret',str(response.data))
        self.assertEqual(SearchFeedback.objects.count(),0)

    def test_finished_response_snapshot_is_immutable_for_feedback(self):
        self.assertFalse(services.save_answer(self.job,self.other,'replacement',{}))
        self.assertFalse(services.save_answer(self.job,self.user,'replacement',{}))
        self.assertEqual(SearchAnswer.objects.get(pk=self.job).question,'پرسش اصلی')

    def test_durable_answer_is_copied_from_owned_server_snapshot_when_feedback_is_requested(self):
        from apps.ai_lab.models import SearchRun
        from apps.ai_lab.job_store import encode
        job = uuid4()
        SearchRun.objects.create(id=job,owner=self.user,client_id="feedback-durable",payload_digest="a"*64,
            status="complete",encrypted_payload=encode({"question":"پرسش معتبرِ ذخیره‌شده"}),
            encrypted_result=encode({"status":"complete","result":self.result}))
        url=f'/api/v1/ai-lab/results/{job}/feedback/'
        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.post(url,{'value':1}).status_code,404)
        self.assertFalse(SearchAnswer.objects.filter(pk=job).exists())
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(url,{'value':1,'question':'forged','result':{}},format='json').status_code,200)
        saved=SearchAnswer.objects.get(pk=job)
        self.assertEqual(saved.question,'پرسش معتبرِ ذخیره‌شده')
        self.assertEqual(saved.result,self.result)
        self.assertEqual(SearchFeedback.objects.get(answer=saved).value,1)
