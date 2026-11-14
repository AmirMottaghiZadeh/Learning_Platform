import json
import uuid
from unittest.mock import patch
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.test import TestCase,override_settings
from django.urls import reverse
from apps.drugs.models import Ingredient,IngredientProfileSection
from . import ai_assist,services
from .models import AISettings,AIPromptPreset,AIEditRun,SectionEditRequest

CACHES={key:{"BACKEND":"django.core.cache.backends.locmem.LocMemCache","LOCATION":"dqc-ai-tests-"+key} for key in ["default","throttle","ai_lab"]}


@override_settings(CACHES=CACHES)
class AIEditTests(TestCase):
    def setUp(self):
        caches["throttle"].clear()
        self.user=get_user_model().objects.create_user("ai-editor",is_staff=True)
        self.admin=get_user_model().objects.create_user("ai-boss",is_superuser=True,is_staff=True)
        self.ingredient=Ingredient.objects.create(name="Fixture drug",rxcui="test-ai-dqc",slug="test-ai-dqc")
        self.section=IngredientProfileSection.objects.create(ingredient=self.ingredient,field="dosage_and_administration",raw_text="50 mg daily; maximum 100 mg.",summary_fa="۵۰ میلی‌گرم روزانه",summary_en="50 mg daily")
        self.config=AISettings.objects.create(pk=1,enabled=True,model="fixture-model",encrypted_api_key=ai_assist.encrypt_key("test-private-api-value"))
        self.result={"summary_fa":"خلاصهٔ پیشنهادی","summary_en":"Suggested summary","notes":"پیشنهاد برای بازبینی"}

    def body(self,**changes):
        return {"request_id":str(uuid.uuid4()),"instruction":"ویرایش جمله‌بندی","target":"both","summary_fa":self.section.summary_fa,"summary_en":self.section.summary_en,**changes}

    def suggest(self,body=None):
        with patch.object(ai_assist,"provider",return_value=(self.result,{"prompt_tokens":10})) as provider:
            run=ai_assist.suggest(self.user,self.section,body or self.body())
        return run,provider

    def test_key_is_encrypted_and_dedicated_settings_are_admin_only(self):
        self.assertNotIn("test-private-api-value",self.config.encrypted_api_key)
        self.assertEqual(ai_assist.decrypt_key(self.config.encrypted_api_key),"test-private-api-value")
        self.client.force_login(self.user)
        self.assertEqual(self.client.get(reverse("data_quality_center:ai_settings")).status_code,302)
        self.client.force_login(self.admin)
        response=self.client.get(reverse("data_quality_center:ai_settings"))
        self.assertEqual(response.status_code,200)
        self.assertNotContains(response,"test-private-api-value")
        self.assertNotContains(response,self.config.encrypted_api_key)
        self.assertContains(response,"تطبیق با متن خام OpenFDA")

    def test_suggestion_never_modifies_published_fields_or_creates_a_review_request(self):
        run,provider=self.suggest()
        self.assertEqual(run.status,"complete")
        self.assertEqual(run.summary_fa,self.result["summary_fa"])
        self.section.refresh_from_db();self.assertEqual(self.section.summary_en,"50 mg daily")
        self.assertFalse(SectionEditRequest.objects.exists())
        self.assertEqual(provider.call_args.args[1]["raw_openfda"],self.section.raw_text)

    def test_translation_forces_destination_and_preserves_source_even_if_model_changes_it(self):
        preset=AIPromptPreset.objects.get(action="fa_to_en")
        run,_=self.suggest(self.body(preset_id=preset.pk,target="both",instruction=""))
        self.assertEqual(run.target,"en");self.assertEqual(run.summary_fa,self.section.summary_fa)
        self.assertEqual(run.summary_en,self.result["summary_en"])
        run,_=self.suggest(self.body(preset_id=AIPromptPreset.objects.get(action="en_to_fa").pk,instruction=""))
        self.assertEqual(run.summary_en,self.section.summary_en)

    def test_single_target_keeps_other_column_unchanged(self):
        run,_=self.suggest(self.body(target="fa"))
        self.assertEqual(run.summary_en,self.section.summary_en)

    def test_retry_same_id_reuses_result_and_other_input_is_rejected(self):
        body=self.body();run,_=self.suggest(body)
        with patch.object(ai_assist,"provider") as provider:
            self.assertEqual(ai_assist.suggest(self.user,self.section,body).pk,run.pk)
            with self.assertRaises(ai_assist.AIError):ai_assist.suggest(self.user,self.section,{**body,"summary_en":"Changed"})
        provider.assert_not_called()

    def test_read_only_user_and_held_section_cannot_call_the_provider(self):
        ordinary=get_user_model().objects.create_user("reader")
        with patch.object(ai_assist,"provider") as provider:
            with self.assertRaises(ai_assist.AIError):ai_assist.suggest(ordinary,self.section,self.body())
            draft=services.save_draft(self.section,self.admin,summary_fa="draft",summary_en="draft",reason="Reviewable change")
            draft.status=SectionEditRequest.STATUS_PENDING;draft.save(update_fields=["status"])
            with self.assertRaises(ai_assist.AIError):ai_assist.suggest(self.user,self.section,self.body())
        provider.assert_not_called()

    def test_empty_translation_source_and_oversized_raw_text_are_not_silently_cut(self):
        body=self.body(preset_id=AIPromptPreset.objects.get(action="fa_to_en").pk,summary_fa="")
        with self.assertRaises(ai_assist.AIError):self.suggest(body)
        self.section.raw_text="x"*90001
        with self.assertRaises(ai_assist.AIError):self.suggest()

    def test_invalid_output_records_safe_error_and_releases_lock(self):
        with patch.object(ai_assist,"provider",return_value=({"summary_fa":123},{})):
            with self.assertRaises(ai_assist.AIError):ai_assist.suggest(self.user,self.section,self.body())
        self.assertEqual(AIEditRun.objects.get().error_code,"DQC_AI_OUTPUT")
        run,_=self.suggest();self.assertEqual(run.status,"complete")

    def test_endpoint_needs_csrf_and_returns_no_provider_key(self):
        self.client.force_login(self.user)
        url=reverse("data_quality_center:ai_suggest",args=[self.ingredient.slug,self.section.field])
        with patch.object(ai_assist,"provider",return_value=(self.result,{})):
            response=self.client.post(url,json.dumps(self.body()),content_type="application/json")
        self.assertEqual(response.status_code,200);self.assertNotContains(response,"test-private-api-value")
        self.assertIn("no-store",response["Cache-Control"])
        from django.test import Client
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.user)
        self.assertEqual(csrf.post(url,json.dumps(self.body()),content_type="application/json").status_code,403)

    def test_invalid_preset_input_has_a_safe_validation_error(self):
        with self.assertRaises(ai_assist.AIError):self.suggest(self.body(preset_id=["bad"]))

    def test_admin_can_save_encrypted_key_and_custom_prompt_without_echoing_key(self):
        self.client.force_login(self.admin)
        rows=list(AIPromptPreset.objects.all())
        body={"config-enabled":"on","config-base_url":"https://provider.example/v1","config-model":"new-model",
            "config-reasoning_effort":"low","config-timeout_seconds":"60","config-max_output_tokens":"4000",
            "config-api_key":"another-private-test-value","prompts-TOTAL_FORMS":str(len(rows)+1),
            "prompts-INITIAL_FORMS":str(len(rows)),"prompts-MIN_NUM_FORMS":"0","prompts-MAX_NUM_FORMS":"30"}
        for i,row in enumerate(rows):
            for key in ["id","name","action","instruction","order"]:body[f"prompts-{i}-{key}"]=str(getattr(row,key))
            body[f"prompts-{i}-active"]="on"
        i=len(rows)
        body.update({f"prompts-{i}-name":"دستور اختصاصی آزمون",f"prompts-{i}-action":"custom",
            f"prompts-{i}-instruction":"حفظ تمام اعداد و اصلاح نگارش",f"prompts-{i}-active":"on",f"prompts-{i}-order":"10"})
        response=self.client.post(reverse("data_quality_center:ai_settings"),body)
        self.assertEqual(response.status_code,302)
        self.config.refresh_from_db()
        self.assertNotIn("another-private-test-value",self.config.encrypted_api_key)
        self.assertEqual(ai_assist.decrypt_key(self.config.encrypted_api_key),"another-private-test-value")
        self.assertTrue(AIPromptPreset.objects.filter(name="دستور اختصاصی آزمون").exists())
        self.assertNotContains(self.client.get(reverse("data_quality_center:ai_settings")),"another-private-test-value")
