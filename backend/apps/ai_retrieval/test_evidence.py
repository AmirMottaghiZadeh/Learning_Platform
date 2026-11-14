from dataclasses import replace

from django.test import SimpleTestCase, override_settings

from apps.ai_lab.retrieval import Passage
from .evidence import focus_passages, retain_with_context


def paragraph(number, text, *, heading="Treatment", ordinal=None, article="10", context=()):
    return Passage("P"+str(number),article,"Condition reference",heading,text,
        {"screen":"uptodateArticle","params":{"id":article,"sectionId":heading,"searchAnchor":"anchor-"+str(number)}},
        "a"*64,heading_path=(heading,),context=context,ordinal=ordinal)


@override_settings(AI_LAB_HYBRID_EVIDENCE_FOCUS=True,AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES=12)
class EvidenceFocusTests(SimpleTestCase):
    def focus(self, rows, **kwargs):
        return focus_passages(rows,"دارودرمانی بیماری چیست؟","Condition pharmacotherapy",intent="drug_therapy",**kwargs)

    def test_prunes_background_duplicates_and_filler_before_model_input(self):
        recommendation=paragraph(1,"For Condition we recommend Fixturemed with the original source qualifications.")
        regimen=paragraph(2,"Condition: oral 10 mg once daily, with source-defined titration.",heading="Dosing")
        restriction=paragraph(3,"Do not use Fixturemed in the source-defined excluded population.",heading="Precautions")
        rows=[recommendation,regimen,restriction,
              paragraph(4,"The definition and historical background of Condition.",heading="Definition"),
              replace(recommendation,id="P5")]
        rows += [paragraph(i,f"Further study number {i}: original details unrelated to the requested aspect.") for i in range(6,35)]
        selected,audit=self.focus(rows)
        self.assertEqual({p.id for p in selected},{"P1","P2","P3"})
        self.assertEqual(audit["duplicate_passages"],1)
        self.assertEqual(audit["off_scope_passages"],1)
        self.assertLess(audit["selected_text_tokens"],audit["input_text_tokens"])
        self.assertEqual(selected[1].text,regimen.text)
        self.assertEqual(selected[1].target,regimen.target)

    def test_exact_text_with_different_indication_context_is_not_deduplicated(self):
        first=paragraph(1,"Oral: 10 mg once daily.",heading="Dosing",context=({"quote":"ConditionA:","source_anchor":"A","ordinal":1},))
        second=replace(first,id="P2",context=({"quote":"ConditionB:","source_anchor":"B","ordinal":2},))
        selected,audit=self.focus([first,second])
        self.assertEqual(len(selected),2)
        self.assertEqual(audit["duplicate_passages"],0)

    def test_adjacent_qualification_is_kept_even_when_soft_target_is_full(self):
        dose=paragraph(1,"Fixturemed: oral 10 mg once daily.",heading="Dosing",ordinal=1)
        guard=paragraph(2,"However, this dose must not be used in the source-defined excluded population.",heading="Dosing",ordinal=2)
        with override_settings(AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES=1):
            selected,_=focus_passages([dose,guard],"دوز Fixturemed چیست؟","Fixturemed dose",intent="dose")
        self.assertEqual({p.id for p in selected},{"P1","P2"})

    def test_source_labels_can_bridge_a_qualification_but_a_missing_paragraph_cannot(self):
        guard=paragraph(1,"Note: observe the original formulation restriction.",heading="Dosing",ordinal=2)
        dose=paragraph(2,"Children: 10 mg once daily.",heading="Dosing",ordinal=4,
            context=({"quote":"Oral:","source_anchor":"route","ordinal":3},))
        self.assertEqual(len(retain_with_context([guard,dose],[dose.id])),2)
        self.assertEqual(retain_with_context([guard,replace(dose,context=())],[dose.id]),[replace(dose,context=())])

    def test_nearby_ids_in_another_section_or_unknown_order_are_not_source_context(self):
        dose=paragraph(1,"Oral 10 mg daily.",heading="Dosing",ordinal=1)
        other=paragraph(2,"However, avoid the unrelated source's intervention.",heading="Other section",ordinal=2)
        unknown=replace(other,id="P3",section="Dosing",heading_path=("Dosing",),ordinal=None)
        self.assertEqual(retain_with_context([dose,other,unknown],[dose.id]),[dose])

    def test_unknown_semantic_or_tag_only_heading_still_reaches_the_model(self):
        row=paragraph(1,"Original source facts stated without the query's synonym.",heading="Unfamiliar heading")
        selected,_=focus_passages([row],"پرسش مرجع","unusual synonym",intent="general")
        self.assertEqual(selected,[row])

    def test_first_line_non_drug_recommendation_is_not_removed_from_general_treatment(self):
        row=paragraph(1,"We recommend the source-defined non-drug treatment first.",heading="Nonpharmacologic treatment")
        selected,_=focus_passages([row],"خط اول درمان چیست؟","Condition first-line treatment",intent="treatment")
        self.assertEqual(selected,[row])

    def test_simple_adverse_effect_question_does_not_send_unrelated_dosing(self):
        adverse=paragraph(1,"Fixturemed adverse effects include the original source-described reaction.",heading="Adverse Reactions")
        dose=paragraph(2,"Fixturemed: oral 10 mg daily.",heading="Dosing")
        selected,_=focus_passages([adverse,dose],"عارضهٔ Fixturemed چیست؟","Fixturemed adverse effects",lookup_kind="drug",intent="adverse_effects")
        self.assertEqual(selected,[adverse])

    def test_flag_can_restore_full_evidence_for_a_controlled_comparison(self):
        rows=[paragraph(i,str(i),heading="Definition") for i in range(1,20)]
        with override_settings(AI_LAB_HYBRID_EVIDENCE_FOCUS=False):
            selected,audit=self.focus(rows)
        self.assertEqual(selected,rows)
        self.assertFalse(audit["enabled"])

    def test_first_line_lookup_omits_explicit_later_line_sections(self):
        first=paragraph(1,"We recommend Fixturemed initially, with the original restrictions.",heading="Initial treatment")
        later=paragraph(2,"We recommend Differentmed 10 mg daily after initial treatment fails.",heading="Second-line treatment")
        selected,_=focus_passages([first,later],"خط اول درمان چیست؟","Condition first-line treatment",intent="treatment")
        self.assertEqual(selected,[first])

    def test_refractory_question_can_still_use_a_later_line_section(self):
        row=paragraph(1,"We recommend the source-defined subsequent regimen.",heading="Treatment-resistant condition")
        selected,_=focus_passages([row],"درمان بیماری مقاوم چیست؟","refractory Condition treatment",intent="treatment")
        self.assertEqual(selected,[row])

    def test_incidental_therapy_word_in_an_adverse_effect_question_does_not_protect_all_doses(self):
        adverse=paragraph(1,"Fixturemed adverse effects include the original source-described reaction.",heading="Adverse Reactions")
        dose=paragraph(2,"Fixturemed: oral 10 mg daily.",heading="Dosing")
        selected,_=focus_passages([adverse,dose],"عارضهٔ دارودرمانی با Fixturemed چیست؟","Fixturemed adverse effects",intent="adverse_effects")
        self.assertEqual(selected,[adverse])
