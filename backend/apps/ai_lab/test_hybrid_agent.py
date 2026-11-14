from types import SimpleNamespace
from dataclasses import replace
from unittest.mock import MagicMock, patch
import uuid
import json

from django.test import SimpleTestCase, override_settings
from . import hybrid_agent as agent
from .provider import ProviderError
from .retrieval import Passage
from apps.ai_retrieval.chunking import token_count


def reference(number, text="Original reference recommendation with its source-defined qualifications."):
    return Passage("P"+str(number),"10","Reference title","Treatment",text,
        {"screen":"uptodateArticle","params":{"id":"10","sectionId":"H1","searchAnchor":"utd-"+"a"*32,"searchContentHash":"b"*64}},
        "b"*64,heading_path=("Treatment",))


def tool(query="reference treatment", **kw):
    return {"role":"assistant","content":None,"tool_calls":[{"id":"call_1","type":"function",
        "function":{"name":"search_references","arguments":json.dumps({"query":query,**kw})}}]}


def approved(*args, **kwargs):
    payload=args[2]
    source_ids=list(dict.fromkeys(s for c in payload["claims"] for s in c["source_ids"]))
    return {"supported":[c["id"] for c in payload["claims"]],"sufficient":True,
        "coverage":[{"requirement":r,"status":"supported","source_ids":source_ids} for r in payload["requirements"]]}, {"latency_ms":1}


@override_settings(AI_LAB_HYBRID_MAX_SEARCH_ROUNDS=3,AI_LAB_HYBRID_CONTEXT_TOKENS=6000)
class HybridAgentTests(SimpleTestCase):
    def retriever(self, batches):
        r=MagicMock();r.generation=SimpleNamespace(pk=uuid.uuid4())
        r.search.side_effect=[(batch,{"engine":"lexical"}) for batch in batches]
        return r

    def test_direct_sources_arrive_before_answer_and_only_one_final_verification(self):
        r=self.retriever([[reference(i) for i in range(1,21)]])
        messages=[tool(intent="treatment"),{"role":"assistant","content":"پاسخ فارسی مستند با توضیح کافی. [P1]"}]
        order=[]
        def stream(*args,**kwargs):
            order.append("model")
            return messages.pop(0),{"latency_ms":1}
        def publish(event):order.append(event["citations"][0]["verification"])
        with patch.object(agent,"stream_chat",side_effect=stream) as upstream,patch.object(agent,"chat",side_effect=approved) as verifier:
            result=agent.answer_hybrid("درمان چیست؟",[],None,retriever=r,publish=publish)
        self.assertEqual(upstream.call_count,2)
        self.assertEqual(verifier.call_count,1)
        self.assertEqual(order[:3],["model","retrieved","model"])
        self.assertEqual(result["parts"][0]["status"],"answered")
        self.assertNotIn("[P1]",result["parts"][0]["overview_fa"])

    def test_complementary_search_preserves_question_population_and_intent(self):
        r=self.retriever([[reference(1)],[reference(2)]])
        messages=[tool("child condition treatment",intent="drug_therapy",audience="pediatric"),
                  tool("medicine administration",lookup_kind="drug",audience="general",intent="dose"),
                  {"role":"assistant","content":"توصیه و شیوهٔ مصرف همان دارو. [P1] [P2]"}]
        with patch.object(agent,"stream_chat",side_effect=[(v,{"latency_ms":1}) for v in messages]),patch.object(agent,"chat",side_effect=approved):
            result=agent.answer_hybrid("دارودرمانی در کودکان؟",[],None,retriever=r)
        self.assertEqual(r.search.call_args_list[1].kwargs["audience"],"pediatric")
        self.assertEqual(result["parts"][0]["intent"],"drug_therapy")
        self.assertEqual(len(result["parts"][0]["items"]),2)

    def test_unknown_citation_fails_before_spending_on_verification(self):
        r=self.retriever([[reference(1)]])
        with patch.object(agent,"stream_chat",side_effect=[(tool(),{}),({"content":"پاسخ جعلی. [P999]"},{})]),patch.object(agent,"chat") as verify:
            with self.assertRaisesMessage(ProviderError,"UNKNOWN_SOURCE_ID"):
                agent.answer_hybrid("سؤال مرجع؟",[],None,retriever=r)
            verify.assert_not_called()

    def test_missing_regimen_is_partial_and_never_a_complete_cached_answer(self):
        r=self.retriever([[reference(1)]])
        def incomplete(*args, **kwargs):
            value,meta=approved(*args)
            value["sufficient"]=False
            value["coverage"][2]={"requirement":"drug_regimen","status":"missing","source_ids":[]}
            return value,meta
        with patch.object(agent,"stream_chat",side_effect=[(tool(intent="treatment"),{}),({"content":"توصیهٔ درمانی مستند. [P1]"},{})]),patch.object(agent,"chat",side_effect=incomplete):
            result=agent.answer_hybrid("خط اول درمان چیست؟",[],None,retriever=r)
        self.assertEqual(result["parts"][0]["status"],"partial")
        self.assertEqual(len(result["parts"][0]["items"]),1)

    def test_no_new_evidence_forces_final_answer_without_time_cutoff(self):
        r=self.retriever([[]])
        with patch.object(agent,"stream_chat",side_effect=[(tool(),{}),({"content":"متن کافی پیدا نشد."},{})]) as upstream,patch.object(agent,"chat") as verify:
            result=agent.answer_hybrid("سؤال؟",[],None,retriever=r)
        self.assertEqual(upstream.call_args_list[-1].kwargs["tool_choice"],"none")
        verify.assert_not_called()
        self.assertEqual(result["parts"][0]["status"],"not_found")

    def test_unknown_tools_and_invalid_arguments_never_reach_the_database(self):
        for message in [tool(query="sk-"+"x"*25),tool(keywords=["sk-"+"x"*25]),tool(audience=["adult"]),tool(intent="invented"),
                        {"tool_calls":[{"function":{"name":"run_sql","arguments":"{}"}}]}]:
            r=self.retriever([])
            with self.subTest(message=message),patch.object(agent,"stream_chat",return_value=(message,{})):
                with self.assertRaises(ProviderError):agent.answer_hybrid("سؤال؟",[],None,retriever=r)
            r.search.assert_not_called()

    def test_long_storage_ids_become_short_handles_without_changing_original_citation_target(self):
        original=reference(1427839)
        r=self.retriever([[original]])
        with patch.object(agent,"stream_chat",side_effect=[(tool(),{}),({"content":"پاسخ معتبر فارسی. [P1]"},{})]),patch.object(agent,"chat",side_effect=approved):
            result=agent.answer_hybrid("سؤال مرجع؟",[],None,retriever=r)
        item=result["parts"][0]["items"][0]
        self.assertEqual(item["source_id"],"P1")
        self.assertEqual(item["target"],original.target)
        self.assertEqual(item["quote"],original.text)
        self.assertEqual(original.id,"P1427839")

    def test_english_only_answer_is_rejected_before_paid_verification(self):
        r=self.retriever([[reference(1)]])
        with patch.object(agent,"stream_chat",side_effect=[(tool(),{}),({"content":"An English-only answer. [P1]"},{})]),patch.object(agent,"chat") as verify:
            with self.assertRaisesMessage(ProviderError,"INVALID_MODEL_OUTPUT"):
                agent.answer_hybrid("سؤال مرجع؟",[],None,retriever=r)
        verify.assert_not_called()

    def test_complementary_search_discards_unused_text_from_all_model_history(self):
        first=reference(1,"Retained source recommendation with its original qualifications.")
        unused=reference(2,"UNUSED_SOURCE_TEXT_MUST_NOT_BE_RESENT")
        dose=reference(3,"Additional original source dosing regimen.")
        r=self.retriever([[first,unused],[dose]])
        messages=[tool("Condition treatment",intent="treatment"),
                  tool("Fixturemed dose",intent="dose",retain_source_ids=["P1"]),
                  {"role":"assistant","content":"توصیه و دوز مستند. [P1] [P3]"}]
        snapshots=[]
        def stream(history,**kwargs):
            snapshots.append(json.loads(json.dumps(history)))
            return messages.pop(0),{}
        with patch.object(agent,"stream_chat",side_effect=stream),patch.object(agent,"chat",side_effect=approved) as verifier:
            result=agent.answer_hybrid("دارودرمانی چیست؟",[],None,retriever=r)
        self.assertNotIn("UNUSED_SOURCE_TEXT_MUST_NOT_BE_RESENT",json.dumps(snapshots[-1]))
        self.assertIn(first.text,json.dumps(snapshots[-1]))
        self.assertIn(dose.text,json.dumps(snapshots[-1]))
        self.assertNotIn("retain_source_ids",r.search.call_args_list[1].kwargs)
        self.assertEqual(r.search.call_args_list[0].kwargs["question"],"دارودرمانی چیست")
        self.assertEqual({p["source_id"] for p in result["parts"][0]["items"]},{"P1","P3"})
        self.assertEqual(verifier.call_count,1)

    def test_unknown_retained_source_fails_before_another_search(self):
        r=self.retriever([[reference(1)]])
        with patch.object(agent,"stream_chat",side_effect=[(tool(),{}),(tool("other",retain_source_ids=["P999"]),{})]),patch.object(agent,"chat") as verify:
            with self.assertRaisesMessage(ProviderError,"UNKNOWN_SOURCE_ID"):
                agent.answer_hybrid("سؤال؟",[],None,retriever=r)
        self.assertEqual(r.search.call_count,1)
        verify.assert_not_called()

    def test_retired_source_cannot_be_cited_in_the_final_answer(self):
        r=self.retriever([[reference(1)],[reference(2)]])
        messages=[tool(),tool("replacement",retain_source_ids=[]),{"content":"پاسخ با ارجاع حذف‌شده. [P1]"}]
        with patch.object(agent,"stream_chat",side_effect=[(v,{}) for v in messages]),patch.object(agent,"chat") as verify:
            with self.assertRaisesMessage(ProviderError,"UNKNOWN_SOURCE_ID"):
                agent.answer_hybrid("سؤال؟",[],None,retriever=r)
        verify.assert_not_called()

    def test_token_ceiling_cannot_admit_a_dose_without_its_attached_restriction(self):
        dose=replace(reference(10,"Original oral 10 mg daily."),ordinal=1)
        guard=replace(reference(20,"However, do not use this regimen in the excluded population."),ordinal=2)
        capacity=token_count(json.dumps(agent._evidence_payload([replace(dose,id="P1")]),ensure_ascii=False))+1
        evidence,bindings={},{}
        with override_settings(AI_LAB_HYBRID_CONTEXT_TOKENS=capacity):
            agent._admit_evidence(evidence,bindings,[dose,guard])
        self.assertNotIn(dose.id,bindings)
        self.assertFalse(any(p.text==dose.text for p in evidence.values()))

    def test_verification_includes_attached_uncited_restriction_but_no_unused_background(self):
        dose=replace(reference(1,"Original oral 10 mg daily."),ordinal=1)
        guard=replace(reference(2,"However, avoid this dose in the excluded population."),ordinal=2)
        unused=replace(reference(3,"Unrelated background information."),ordinal=3)
        claims=[{"id":"A1","text":"دوز مستند.","source_ids":["P1"]}]
        with patch.object(agent,"chat",side_effect=approved) as verifier:
            agent._verify("سؤال",claims,[dose,guard,unused],["requested_aspects"],[])
        self.assertEqual({row["id"] for row in verifier.call_args.args[2]["sources"]},{"P1","P2"})
