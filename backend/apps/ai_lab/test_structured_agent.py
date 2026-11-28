import json
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from django.test import SimpleTestCase, override_settings
from . import structured_agent as scoped, hybrid_agent as agent
from .test_hybrid_agent import reference, tool, approved
from .test_question_profile import profile
from .provider import ProviderError


@override_settings(AI_LAB_TAG_SCOPED_SEARCH=True,AI_LAB_PLAN_CACHE_TTL_SECONDS=0,
    AI_LAB_HYBRID_MAX_SEARCH_ROUNDS=3,AI_LAB_HYBRID_CONTEXT_TOKENS=6000)
class StructuredAgentTests(SimpleTestCase):
    def retriever(self, passages):
        r=MagicMock();r.generation=SimpleNamespace(pk="test-generation")
        r.search.return_value=(passages,{"engine":"scoped"})
        return r

    def plan(self, **kwargs):
        value=profile(kind="drug_question",objectives=["adverse_effects"],regimen_requested=False,
            conditions=[],findings=[],medications=["Fixturemed"],focus="Adverse effects of Fixturemed")
        value.update(kwargs)
        return tool("Fixturemed adverse effects",lookup_kind="drug",question_profile=value)

    def test_compact_plan_writer_and_verifier_have_no_intermediate_model_decision(self):
        r=self.retriever([reference(10,"Original important adverse reactions and source-defined qualifications.")])
        calls=[]
        def stream(messages,**kwargs):
            calls.append((messages,kwargs))
            return (self.plan() if len(calls)==1 else {"content":"عارضهٔ مستند همراه با قیود منبع. [P1]"}),{}
        published=[]
        with patch.object(scoped,"stream_chat",side_effect=stream),patch.object(agent,"chat",side_effect=approved) as verify:
            result=agent.answer_hybrid("عوارض دارو چیست؟",[],None,retriever=r,publish=published.append)
        self.assertEqual(len(calls),2)
        self.assertEqual(verify.call_count,1)
        self.assertEqual(calls[1][1]["tool_choice"],"none")
        self.assertNotIn("tools",calls[1][1])
        self.assertLess(len(calls[0][0][0]["content"]),len(agent.AGENT_PROMPT)/2)
        self.assertEqual(result["parts"][0]["status"],"answered")
        self.assertEqual(published[0]["citations"][0]["verification"],"retrieved")
        self.assertEqual(result["parts"][0]["items"][0]["quote"],r.search.return_value[0][0].text)

    def test_missing_facet_uses_one_local_followup_without_an_extra_model_call(self):
        p=reference(10,"An original source describes the medication's adverse reactions.")
        r=self.retriever([p])
        extra=reference(20,"Monitor source-defined findings at the original monitoring interval.")
        r.search.side_effect=[([p],{}),([extra],{})]
        with patch.object(scoped,"stream_chat",side_effect=[(self.plan(objectives=["adverse_effects","monitoring"]),{}),
                ({"content":"عارضه و پایش مطابق منبع. [P1] [P2]"},{})]) as model, \
                patch.object(agent,"chat",side_effect=approved):
            result=agent.answer_hybrid("عارضه و پایش دارو چیست؟",[],None,retriever=r)
        self.assertEqual(r.search.call_count,2)
        self.assertEqual(model.call_count,2)
        self.assertEqual(result["parts"][0]["retrieval"]["searches"][1]["supplement_for"],["monitoring"])
        self.assertEqual(r.search.call_args_list[0].kwargs["question_profile"],r.search.call_args_list[1].kwargs["question_profile"])

    def test_no_source_does_not_spend_on_writer_or_verification(self):
        r=self.retriever([])
        with patch.object(scoped,"stream_chat",return_value=(self.plan(),{})) as model,patch.object(agent,"chat") as verify:
            result=agent.answer_hybrid("عوارض دارو چیست؟",[],None,retriever=r)
        model.assert_called_once();verify.assert_not_called()
        self.assertEqual(result["parts"][0]["status"],"not_found")

    def test_discovered_algorithm_is_returned_even_without_answer_paragraphs(self):
        source = reference(10, "Decision algorithm")
        source = replace(source, media=({"key": "fixture", "kind": "image", "article_id": source.article_id,
                         "title": "Decision pathway", "caption": "Original source", "is_algorithm": True},))
        retriever = self.retriever([source])
        with patch.object(scoped, "stream_chat", return_value=(self.plan(), {})) as model, patch.object(agent, "chat") as verify:
            part = agent.answer_hybrid("الگوریتم Fixturemed را نشان بده", [], None, retriever=retriever)["parts"][0]
        model.assert_called_once()
        verify.assert_not_called()
        self.assertEqual(part["status"], "answered")
        self.assertEqual(part["items"][0]["media"][0]["key"], "fixture")

    def test_numeric_formulation_fact_does_not_satisfy_a_requested_treatment_regimen(self):
        rows=[reference(10,"We recommend Fixturemed. The available solution contains 10 mg/mL.")]
        value=profile(kind="disease_question",objectives=["drug_therapy","dose"],regimen_requested=True)
        self.assertIn("dose",scoped.missing_facets(rows,value))

    def test_regimen_must_match_both_named_medication_and_indication(self):
        value = profile(kind="drug_question", medications=["Fixturemed"], objectives=["dose"], regimen_requested=True,
                        conditions=[{"name": "ConditionY", "status": "reported"}])
        comparator = reference(10, "For ConditionY, the ComparatorMed initial dose is 10 mg daily.")
        other_indication = reference(20, "For ConditionZ, the Fixturemed initial dose is 20 mg daily.")
        matching = reference(30, "For ConditionY, the Fixturemed initial dose is 30 mg daily.")
        self.assertIn("dose", scoped.missing_facets([comparator, other_indication], value))
        self.assertNotIn("dose", scoped.missing_facets([comparator, other_indication, matching], value))

    def test_writer_cannot_trigger_a_new_search(self):
        r=self.retriever([reference(10,"Original adverse effects with the source-defined constraints.")])
        with patch.object(scoped,"stream_chat",side_effect=[(self.plan(),{}),(tool("unrelated corpus search"),{})]):
            with self.assertRaisesMessage(ProviderError,"UNEXPECTED_SEARCH_TOOL"):
                agent.answer_hybrid("عوارض دارو چیست؟",[],None,retriever=r)
        self.assertEqual(r.search.call_count,1)

    def test_unknown_citations_never_reach_the_verifier(self):
        r=self.retriever([reference(10,"Original adverse reactions with the source qualifications.")])
        with patch.object(scoped,"stream_chat",side_effect=[(self.plan(),{}),({"content":"پاسخ غیرمستند. [P999]"},{})]),patch.object(agent,"chat") as verify:
            with self.assertRaisesMessage(ProviderError,"UNKNOWN_SOURCE_ID"):
                agent.answer_hybrid("عوارض دارو چیست؟",[],None,retriever=r)
        verify.assert_not_called()

    def test_stated_case_facts_and_unknowns_survive_into_one_aggregate_verification(self):
        value=profile()
        r=self.retriever([reference(10,"Emergency initial assessment and source-defined precautions for this condition.")])
        with patch.object(scoped,"stream_chat",side_effect=[
                (tool("unconscious myocardial infarction nitroglycerin",lookup_kind="drug",intent="dose",question_profile=value),{}),
                ({"content":"اقدام مشروط مطابق وضعیت و منبع. [P1]"},{})]),patch.object(agent,"chat",side_effect=approved) as verify:
            result=agent.answer_hybrid("بیمار بیهوش است؛ اقدام مناسب چیست؟",[],None,retriever=r)
        self.assertEqual(r.search.call_args.kwargs["lookup_kind"],"topic")
        self.assertEqual(r.search.call_args.kwargs["intent"],"emergency_care")
        self.assertEqual(verify.call_args.args[2]["question_profile"],value)
        self.assertNotIn("drug_regimen",result["parts"][0]["requirements"])
        self.assertIn("intervention_safety",result["parts"][0]["requirements"])

    def test_missing_source_regimen_remains_partial_without_fabricating_a_dose(self):
        r=self.retriever([reference(10,"We recommend the source-defined drug therapy with the original restrictions.")])
        value=profile(kind="disease_question",objectives=["drug_therapy"],conditions=[],findings=[],medications=[])
        def partial(*args,**kwargs):
            answer,meta=approved(*args)
            answer["sufficient"]=False
            answer["coverage"][2]={"requirement":"drug_regimen","status":"missing","source_ids":[]}
            return answer,meta
        with patch.object(scoped,"stream_chat",side_effect=[(tool(question_profile=value),{}),
                ({"content":"توصیهٔ دارویی مطابق متن موجود. [P1]"},{})]),patch.object(agent,"chat",side_effect=partial):
            result=agent.answer_hybrid("دارودرمانی و دوز چیست؟",[],None,retriever=r)
        self.assertEqual(result["parts"][0]["status"],"partial")
        self.assertIn("drug_regimen",result["parts"][0]["requirements"])

    def test_first_line_selection_keeps_verified_sentence_without_dose_or_valid_coverage(self):
        initial = replace(reference(10, "We recommend initial therapy with Fixturemed for this subgroup."),
                          section="Initial therapy", heading_path=("Initial therapy",))
        other = reference(20, "A different passage describes management after failure.")
        retriever = self.retriever([other, initial])
        proposal = self.plan(kind="disease_question", objectives=["drug_therapy", "dose"], regimen_requested=True)
        raw = "یک ادعای بدون ارجاع.\n\nدرمان اول برای زیرگروه ذکرشده داروی نمونه است [P1]. درمان دیگری هم اضافه کنید [P2]."
        decision = {"supported": ["A1"], "sufficient": True,
                    "coverage": [{"requirement": "requested_aspects", "status": "supported", "source_ids": ["P2"]}]}
        with patch.object(scoped, "stream_chat", side_effect=[(proposal, {}), ({"content": raw}, {})]), \
                patch.object(agent, "chat", return_value=(decision, {})) as verify:
            part = agent.answer_hybrid("آرتریت روماتویید درمان خط اولش چیه", [], None, retriever=retriever)["parts"][0]
        self.assertEqual(part["status"], "partial")
        self.assertNotIn("drug_regimen", part["requirements"])
        self.assertNotIn("dose", retriever.search.call_args.kwargs["question_profile"]["objectives"])
        self.assertEqual([row["source_ids"] for row in verify.call_args.args[2]["claims"]], [["P1"], ["P2"]])
        self.assertEqual(part["items"][0]["quote"], initial.text)
        self.assertEqual(part["answer_blocks"], [{"text_fa": "درمان اول برای زیرگروه ذکرشده داروی نمونه است.", "source_ids": ["P1"]}])

    def test_fully_rejected_draft_is_rewritten_once_and_checked_again(self):
        retriever = self.retriever([reference(10, "Original adverse reactions with an important source qualification.")])
        raw = "یک ادعای غیرمستند در پیش‌نویس. [P1]"
        repair = "عارضه با شرط ذکرشده در منبع گزارش شده است. [P1]"
        with patch.object(scoped, "stream_chat", side_effect=[(self.plan(), {}), ({"content": raw}, {})]), \
                patch.object(agent, "chat", side_effect=[
                    ({"supported": [], "sufficient": False, "coverage": []}, {}), ({"answer": repair}, {}),
                    ({"supported": ["A1"], "sufficient": True, "coverage": [
                        {"requirement": "requested_aspects", "status": "supported", "source_ids": ["P1"]}]}, {}),
                ]) as calls:
            part = agent.answer_hybrid("عوارض دارو چیست؟", [], None, retriever=retriever)["parts"][0]
        self.assertEqual(calls.call_count, 3)
        self.assertEqual(part["status"], "answered")
        self.assertNotIn("ادعای غیرمستند", part["overview_fa"])
        self.assertIn("شرط ذکرشده", part["overview_fa"])
