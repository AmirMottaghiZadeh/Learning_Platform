from copy import deepcopy
import json
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings

from . import hybrid_agent as agent, lexical, question_profile as profiles
from .provider import ProviderError
from . import test_hybrid_agent as agent_fixtures
from .test_hybrid_agent import approved, reference, tool
from apps.ai_retrieval.evidence import focus_passages


CASE = ("بیماری دچار حمله قلبی شده و بیهوش است.\n"
        "آیا نیتروگلیسیرین زیرزبانی پیش از رسیدن اورژانس مناسب است؟\n"
        "یا اقدام دیگری لازم است؟")


def profile(**changes):
    value = {"kind": "clinical_scenario", "objectives": ["emergency_care", "contraindications"],
             "focus": "Unconscious patient with reported myocardial infarction: prehospital action and sublingual nitroglycerin safety",
             "conditions": [{"name": "myocardial infarction", "status": "reported"}],
             "medications": ["nitroglycerin"],
             "findings": [{"name": "unconsciousness", "state": "present"},
                          {"name": "normal breathing", "state": "unknown"}],
             "constraints": ["sublingual route"], "care_setting": "prehospital"}
    value.update(changes)
    return profiles.validate(value)


class ProfileValidationTests(SimpleTestCase):
    def test_preserves_stated_negation_and_unknowns_without_turning_them_into_positive_entities(self):
        value = profile(conditions=[{"name": "myocardial infarction", "status": "possible"},
                                    {"name": "pulmonary embolism", "status": "excluded"}],
                        findings=[{"name": "fever", "state": "absent"},
                                  {"name": "blood pressure", "state": "unknown"}])
        self.assertEqual(profiles.entities(value), ["myocardial infarction", "nitroglycerin"])
        self.assertNotIn("fever", profiles.keywords(value))
        self.assertEqual(value["conditions"][0]["status"], "possible")
        self.assertEqual(value["findings"][1]["state"], "unknown")

    def test_eight_generic_keywords_cannot_crowd_out_the_decisive_case_finding(self):
        hints = profiles.keywords(profile(), ["generic"+str(n) for n in range(8)])
        self.assertIn("unconsciousness", hints)
        self.assertIn("sublingual route", hints)
        self.assertEqual(len(hints), 8)

    def test_invalid_metadata_is_rejected_before_retrieval(self):
        examples = [None, [], {}, {**profile(), "kind": []}, {**profile(), "objectives": ["invented"]},
                    {**profile(), "objectives": ["dose", "dose"]}, {**profile(), "sql": "select *"},
                    {**profile(), "findings": [{"name": "fever", "state": "maybe"}]},
                    {**profile(), "medications": ["sk-"+"x"*25]},
                    {**profile(), "constraints": ["a"]*7}, {**profile(), "focus": "x"*201}]
        for value in examples:
            with self.subTest(value=value), self.assertRaisesMessage(ProviderError, "INVALID_SEARCH_TOOL_ARGUMENTS"):
                profiles.validate(value)

    def test_case_is_not_split_at_question_marks_newlines_or_a_semicolon(self):
        value = "شرح حال؛\nعلائم حاضر چیست؟\nعلائم غایب؟\nاقدام بعدی؟\nدر خانه چه کنیم؟"
        self.assertEqual(profiles.question_parts(value), [value.rstrip("؟")])

    def test_incidental_prior_therapy_does_not_impose_drug_regimen_on_diagnosis(self):
        value = profile(objectives=["diagnosis", "differential"])
        requirements = agent._requirements("بیمار پس از درمان دارویی علائم تازه دارد؛ تشخیص چیست؟", "diagnosis", value)
        self.assertIn("case_applicability", requirements)
        self.assertIn("diagnostic_assessment", requirements)
        self.assertNotIn("drug_regimen", requirements)

    def test_pharmacotherapy_still_requires_the_recommended_drugs_full_regimen(self):
        value = profile(kind="disease_question", objectives=["drug_therapy"])
        self.assertEqual(agent._requirements("دارودرمانی چیست؟", "drug_therapy", value),
                         ["requested_aspects", "treatment_selection", "drug_regimen", "important_restrictions"])

    def test_safety_decision_with_secondary_therapy_does_not_impose_an_unrequested_alternative_dose(self):
        value = profile(kind="drug_disease", objectives=["contraindications", "drug_therapy"], regimen_requested=False)
        self.assertNotIn("drug_regimen", profiles.requirements(value))
        self.assertIn("intervention_safety", profiles.requirements(value))
        self.assertIn("treatment_selection", profiles.requirements(value))

    def test_requested_regimen_in_a_diagnostic_case_is_kept_and_dosing_cannot_disable_it(self):
        value = profile(objectives=["diagnosis", "drug_therapy"], regimen_requested=True)
        self.assertIn("drug_regimen", profiles.requirements(value))
        for goals in (["dose"], ["renal_dose"], ["drug_therapy"]):
            self.assertIn("drug_regimen", profiles.requirements(profile(objectives=goals,regimen_requested=False)))

    def test_relationship_question_requires_relationship_support_not_independent_monographs(self):
        for kind in ("drug_disease", "drug_interaction"):
            value = profile(kind=kind, objectives=["contraindications", "interaction"])
            self.assertIn("entity_relationship", profiles.requirements(value))
            self.assertIn("intervention_safety", profiles.requirements(value))
            self.assertNotIn("drug_regimen", profiles.requirements(value))

    def test_verification_separates_supported_actions_from_other_sentences_in_the_same_paragraph(self):
        claims, uncited = agent._claims("دستور اول. دستور متفاوت بدون تأیید در همان ارجاع. [P1]", [reference(1)])
        self.assertEqual([c["text"] for c in claims], ["دستور اول.", "دستور متفاوت بدون تأیید در همان ارجاع."])
        self.assertTrue(all(c["source_ids"] == ["P1"] for c in claims))
        self.assertFalse(uncited)

    def test_explicit_diagnostic_objective_overrides_incidental_therapy_and_renal_words(self):
        value = profile(objectives=["diagnosis"])
        context = lexical.search_context("بیمار کلیوی پس از درمان دارویی چه تشخیصی دارد؟",
            ["acute confusion evaluation"], intent="diagnosis", question_profile=value)
        self.assertEqual(context.intents, ("diagnosis",))
        self.assertFalse(context.broad_treatment)
        self.assertFalse(context.first_line_regimen)

    def test_complementary_aspect_can_be_added_without_replacing_original_goal(self):
        value = profile(objectives=["emergency_care", "contraindications"])
        context = lexical.search_context(CASE, ["nitroglycerin adverse effects"],
            intent="adverse_effects", question_profile=value)
        self.assertEqual(set(context.intents), {"emergency_care", "contraindications", "adverse_effects"})
        self.assertIn("unconsciousness", context.aspects)

    @override_settings(AI_LAB_HYBRID_EVIDENCE_FOCUS=True, AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES=16)
    def test_differential_does_not_discard_the_diagnostic_source_as_background(self):
        from dataclasses import replace
        passage = replace(reference(1, "Original confusion evaluation and differential source qualifications."),
                          section="Diagnostic evaluation", heading_path=("Diagnostic evaluation",))
        selected, audit = focus_passages([passage], "درمان قبلی داشته؛ تشخیص افتراقی چیست", "confusion differential",
            intent="differential", question_profile=profile(objectives=["differential"]))
        self.assertEqual(selected, [passage])
        self.assertEqual(audit["off_scope_passages"], 0)


@override_settings(AI_LAB_HYBRID_MAX_SEARCH_ROUNDS=3, AI_LAB_HYBRID_CONTEXT_TOKENS=6000)
class ProfileAgentTests(SimpleTestCase):
    retriever = agent_fixtures.HybridAgentTests.retriever

    def test_full_case_understanding_uses_the_existing_first_call_and_reaches_verification(self):
        r = self.retriever([[reference(1)]])
        value = profile()
        messages = [tool("unconscious myocardial infarction prehospital nitroglycerin safety",
                         lookup_kind="drug", intent="dose", question_profile=value),
                    {"content": "پاسخ مستند و مشروط به وضعیت بیمار. [P1]"}]
        with patch.object(agent, "stream_chat", side_effect=[(m,{}) for m in messages]) as upstream, \
                patch.object(agent, "chat", side_effect=approved) as verify:
            result = agent.answer_hybrid(CASE, [], None, retriever=r)
        self.assertEqual(upstream.call_count, 2)
        self.assertIn("question_profile", upstream.call_args_list[0].kwargs["tools"][0]["function"]["parameters"]["required"])
        self.assertEqual(r.search.call_args.kwargs["question"], CASE.rstrip("؟"))
        self.assertEqual(r.search.call_args.kwargs["lookup_kind"], "topic")
        self.assertEqual(r.search.call_args.kwargs["intent"], "emergency_care")
        self.assertEqual(r.search.call_args.kwargs["question_profile"], value)
        self.assertEqual(verify.call_args.args[2]["question_profile"], value)
        part = result["parts"][0]
        self.assertEqual(part["status"], "answered")
        self.assertIn("immediate_actions", part["requirements"])
        self.assertIn("intervention_safety", part["requirements"])
        self.assertNotIn("drug_regimen", part["requirements"])

    def test_case_facts_are_bound_even_if_the_complementary_call_proposes_another_profile(self):
        r = self.retriever([[reference(1)], [reference(2)]])
        initial = profile()
        changed = profile(kind="drug_question", objectives=["dose"], findings=[], constraints=[], medications=["another drug"])
        messages = [tool(question_profile=initial, audience="adult"),
                    tool("nitroglycerin contraindications", intent="contraindications", question_profile=changed),
                    {"content": "پاسخ با شواهد مرتبط با همان شرایط بیمار. [P1] [P2]"}]
        with patch.object(agent, "stream_chat", side_effect=[(m,{}) for m in messages]), \
                patch.object(agent, "chat", side_effect=approved) as verify:
            result = agent.answer_hybrid(CASE, [], None, retriever=r)
        second = r.search.call_args_list[1].kwargs
        self.assertEqual(second["question_profile"], initial)
        self.assertEqual(second["audience"], "adult")
        self.assertEqual(verify.call_args.args[2]["question_profile"], initial)
        self.assertNotIn("drug_regimen", result["parts"][0]["requirements"])

    def test_an_empty_first_case_query_can_be_repaired_within_the_existing_round_limit(self):
        r = self.retriever([[], [reference(1)]])
        messages = [tool("overly narrow query", question_profile=profile()), tool("broader equivalent syndrome"),
                    {"content": "پاسخ مستند پس از یافتن منبع مرتبط. [P1]"}]
        with patch.object(agent, "stream_chat", side_effect=[(m,{}) for m in messages]) as upstream, \
                patch.object(agent, "chat", side_effect=approved):
            result = agent.answer_hybrid(CASE, [], None, retriever=r)
        self.assertEqual(r.search.call_count, 2)
        self.assertEqual(upstream.call_args_list[1].kwargs["tool_choice"], "auto")
        self.assertEqual(result["parts"][0]["status"], "answered")

    def test_two_empty_case_queries_stop_without_repeated_paid_searches(self):
        r = self.retriever([[], []])
        messages = [tool("first query", question_profile=profile()), tool("broader query"),
                    {"content": "شواهد کافی پیدا نشد."}]
        with patch.object(agent, "stream_chat", side_effect=[(m,{}) for m in messages]) as upstream, patch.object(agent, "chat") as verify:
            result = agent.answer_hybrid(CASE, [], None, retriever=r)
        self.assertEqual(r.search.call_count, 2)
        self.assertEqual(upstream.call_args_list[-1].kwargs["tool_choice"], "none")
        self.assertEqual(result["parts"][0]["status"], "not_found")
        verify.assert_not_called()

    def test_malformed_profile_never_reaches_sources(self):
        r = self.retriever([])
        invalid = deepcopy(profile())
        invalid["findings"][0]["state"] = "invented"
        with patch.object(agent,"stream_chat",return_value=(tool(question_profile=invalid),{})):
            with self.assertRaisesMessage(ProviderError,"INVALID_SEARCH_TOOL_ARGUMENTS"):
                agent.answer_hybrid(CASE, [], None, retriever=r)
        r.search.assert_not_called()
