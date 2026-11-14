from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch

from django.core.management import call_command
from django.test import TestCase, override_settings
from apps.core.exceptions import PlatformAPIError
from apps.ai_lab import test_reference_index as fixtures
from apps.ai_lab.models import ReferenceParagraph
from apps.ai_lab.provider import ProviderError
from apps.uptodate import services as utd
from . import indexing
from .models import RetrievalGeneration, SearchAlias, SearchConcept, SearchChunk
from .retrieval import HybridRetriever


class HybridRetrievalTests(TestCase):
    databases = "__all__"
    setUp_source = fixtures.ReferenceIndexTests.setUp
    write_article = fixtures.ReferenceIndexTests.write_article
    add_title = fixtures.ReferenceIndexTests.add_title
    build_reference = fixtures.ReferenceIndexTests.build

    def setUp(self):
        self.setUp_source()
        self.write_article("3851", fixtures.html("Dosing: Pediatric", "Nocturnal enuresis: original pediatric source qualifications and regimen."), title="Pediatric reference")
        self.add_title("3852")
        self.write_article("3852", fixtures.html("Dosing: Adult", "Nocturnal enuresis: original adult source qualifications and regimen."), title="Adult reference")
        self.build_reference()
        call_command("build_hybrid_index", stdout=StringIO())
        self.generation = RetrievalGeneration.objects.latest("created_at")
        self.request = SimpleNamespace(user=SimpleNamespace(pk="diagnostic", is_authenticated=True, is_staff=True))

    def retriever(self):
        return HybridRetriever(self.request, generation=self.generation)

    def test_canonical_text_anchor_hash_and_population_survive_direct_lookup(self):
        passages, audit = self.retriever().search("nocturnal enuresis", audience="pediatric", intent="dose")
        self.assertTrue(passages)
        self.assertEqual({p.article_id for p in passages}, {"3851"})
        self.assertEqual(audit["degraded"], "HYBRID_EMBEDDINGS_NOT_READY")
        for passage in passages:
            row = ReferenceParagraph.objects.get(pk=int(passage.id[1:]))
            self.assertEqual(passage.text, row.text)
            self.assertEqual(passage.target["params"]["searchAnchor"], row.source_anchor)
            self.assertEqual(passage.target["params"]["searchContentHash"], passage.content_hash)
            self.assertEqual(passage.ordinal,row.ordinal)

    def test_article_quota_is_consumed_only_for_focused_evidence(self):
        def focus(rows,*args,**kwargs):
            selected=[row for row in rows if row.article_id=="3851"]
            return selected,{"selected_text_tokens":1}
        with patch("apps.ai_retrieval.retrieval.evidence.focus_passages",side_effect=focus),\
                patch("apps.ai_retrieval.retrieval.require_feature") as permission:
            passages,_=self.retriever().search("nocturnal enuresis")
        self.assertTrue(passages)
        consumed=[call.kwargs["item"] for call in permission.call_args_list if call.kwargs.get("consume")]
        self.assertEqual(consumed,["3851"])

    def test_tag_only_synonym_reaches_article_without_loading_the_snapshot_catalog_at_runtime(self):
        concept = SearchConcept.objects.create(generation=self.generation, source_id="alias", topic_lists=["3851", "", "", "", ""])
        SearchAlias.objects.create(generation=self.generation, concept=concept, alias="unusual synonym", weight=10)
        with patch.object(utd, "_search_catalog", side_effect=AssertionError("No cold catalog at request time")):
            passages, audit = self.retriever().search("unusual synonym", audience="pediatric", intent="dose")
        self.assertTrue(passages)
        self.assertEqual(passages[0].article_id, "3851")
        self.assertGreater(audit["tagging_candidates"], 0)

    def test_revoked_article_access_never_exposes_a_passage(self):
        def permission(request, feature, **kwargs):
            if kwargs.get("item"):
                raise PlatformAPIError("Denied", status_code=402)
        with patch("apps.ai_retrieval.retrieval.require_feature", side_effect=permission):
            passages, audit = self.retriever().search("nocturnal enuresis")
        self.assertEqual(passages, [])

    def test_changed_source_is_rejected_before_issuing_any_embedding(self):
        retriever = self.retriever()
        self.write_article("3851", fixtures.html(text=fixtures.TEXT + " Changed source."))
        with patch("apps.ai_retrieval.embeddings.embed") as paid:
            with self.assertRaisesMessage(ProviderError, "REFERENCE_INDEX_STALE"):
                retriever.search("nocturnal enuresis")
        paid.assert_not_called()

    def test_one_long_tagged_section_cannot_crowd_out_another_articles_relevant_evidence(self):
        text="Original source qualification and detail. " * 75
        body='<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Adverse Reactions (Significant)</span></p>'
        body+=''.join(f'<p>{n}: {text}</p>' for n in range(40))+'</div>'
        self.write_article("3852",body,title="First reference")
        self.write_article("3851",fixtures.html("Adverse Reactions",fixtures.TEXT),title="Second reference")
        self.build_reference(force=True)
        call_command("build_hybrid_index",stdout=StringIO())
        self.generation=RetrievalGeneration.objects.latest("created_at")
        concept=SearchConcept.objects.create(generation=self.generation,source_id="alias",topic_lists=["3852,3851","","",""])
        SearchAlias.objects.create(generation=self.generation,concept=concept,alias="unusual synonym",weight=10)
        passages,audit=self.retriever().search("unusual synonym",intent="adverse_effects")
        self.assertIn("3851",{p.article_id for p in passages})

    def test_long_generic_intent_tag_cannot_override_the_named_drug_tag(self):
        for alias, identifier in [("ibuprofen","3851"),("adverse effects","3852")]:
            concept=SearchConcept.objects.create(generation=self.generation,source_id=alias,topic_lists=[identifier,"","",""])
            SearchAlias.objects.create(generation=self.generation,concept=concept,alias=alias,weight=10)
        passages,_=self.retriever().search("ibuprofen adverse effects",lookup_kind="drug",intent="adverse_effects")
        self.assertEqual({p.article_id for p in passages},{"3851"})

    def test_case_tags_include_both_drug_and_disease_even_if_the_short_query_names_only_one(self):
        from apps.ai_lab.test_question_profile import profile
        for alias, identifier in [("nitroglycerin","3851"),("myocardial infarction","3852")]:
            concept=SearchConcept.objects.create(generation=self.generation,source_id=alias,topic_lists=[identifier,"","",""])
            SearchAlias.objects.create(generation=self.generation,concept=concept,alias=alias,weight=10)
        retriever=self.retriever()
        identifiers=retriever.catalog_ids("nitroglycerin precautions","general","contraindications","topic",profile())
        self.assertEqual(identifiers,["3852","3851"])
        # Without a typed relationship, preserve the canonical single-tag route.
        self.assertEqual(retriever.catalog_ids("nitroglycerin precautions","general","contraindications"),["3851"])

    def test_excluded_condition_is_not_used_as_a_positive_case_tag(self):
        from apps.ai_lab.test_question_profile import profile
        concept=SearchConcept.objects.create(generation=self.generation,source_id="excluded",topic_lists=["3852","","",""])
        SearchAlias.objects.create(generation=self.generation,concept=concept,alias="pulmonary embolism",weight=10)
        value=profile(conditions=[{"name":"pulmonary embolism","status":"excluded"}])
        self.assertEqual(self.retriever().catalog_ids("nitroglycerin precautions","general",question_profile=value),[])

    def test_default_drug_lookup_uses_the_canonical_monograph_and_explicit_children_keep_theirs(self):
        for identifier,title in [("3851","Fixturemed: Drug information"),("3852","Fixturemed: Pediatric drug information")]:
            self.write_article(identifier,fixtures.html("Adverse Reactions",
                "Fixturemed has original adverse reactions and important source qualifications for this population."),title=title)
        self.build_reference(force=True)
        call_command("build_hybrid_index",stdout=StringIO())
        self.generation=RetrievalGeneration.objects.latest("created_at")
        ordinary,_=self.retriever().search("Fixturemed adverse effects",lookup_kind="drug",intent="adverse_effects")
        pediatric,_=self.retriever().search("Fixturemed adverse effects",lookup_kind="drug",intent="adverse_effects",audience="pediatric")
        self.assertTrue(ordinary)
        self.assertTrue(pediatric)
        self.assertEqual({p.article_id for p in ordinary},{"3851"})
        self.assertEqual(pediatric[0].article_id,"3852")

    def test_regimen_enrichment_only_reads_a_source_named_medicine_for_the_same_population(self):
        self.write_article("3851",fixtures.html("Summary and Recommendations",
            "For pediatric ConditionY management we suggest Fixturemed with these original source qualifications."),title="Condition reference")
        body='<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Dosing: Adult</span></p>'
        body+='<p>ConditionY in adults: oral 999 mg daily, with the original source qualifications.</p>'
        body+='<p class="headingAnchor" id="H2"><span class="h1">Dosing: Pediatric</span></p>'
        body+='<p>ConditionY in children: oral 10 mg daily, with the original source qualifications.</p></div>'
        self.write_article("3852",body,title="Fixturemed: Drug information")
        self.add_title("3853")
        self.write_article("3853",fixtures.html("Dosing: Pediatric",
            "ConditionY in children: oral 777 mg daily, with the original source qualifications."),title="Differentmed: Drug information")
        self.build_reference(force=True)
        call_command("build_hybrid_index",stdout=StringIO())
        self.generation=RetrievalGeneration.objects.latest("created_at")
        core=list(SearchChunk.objects.filter(generation=self.generation,source_id="3851"))
        supplementary=self.retriever().regimen_supplements(core,"ConditionY treatment","pediatric","treatment")
        self.assertTrue(supplementary)
        self.assertEqual({row.source_id for row in supplementary},{"3852"})
        self.assertTrue(all(row.audience=="pediatric" for row in supplementary))
        self.assertTrue(any("10 mg" in row.text for row in supplementary))
        self.assertFalse(any("999" in row.text or "777" in row.text for row in supplementary))
        core[0].text="No medicine is named in this original source paragraph."
        self.assertEqual(self.retriever().regimen_supplements(core,"ConditionY treatment","pediatric","treatment"),[])

    def test_short_indication_and_route_labels_lead_to_the_adjacent_dose_and_remain_verifiable(self):
        from apps.ai_lab import response_cache, hybrid_agent, evaluation
        self.write_article("3851",fixtures.html("Summary and Recommendations",
            "For pediatric ConditionY management we suggest Fixturemed with these original source qualifications."),title="Condition reference")
        body='<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Dosing: Pediatric</span></p>'
        body+='<p>ConditionY:</p><p>Note: the formulation restrictions for ConditionY in children must be observed.</p>'
        body+='<p>Oral:</p><p>Children: initial 10 mg once daily, with the original source qualifiers.</p></div>'
        self.write_article("3852",body,title="Fixturemed: Drug information")
        self.build_reference(force=True)
        call_command("build_hybrid_index",stdout=StringIO())
        self.generation=RetrievalGeneration.objects.latest("created_at")
        retriever=self.retriever()
        core=list(SearchChunk.objects.filter(generation=self.generation,source_id="3851"))
        supplements=retriever.regimen_supplements(core,"ConditionY treatment","pediatric","treatment")
        dose_chunks=[row for row in supplements if "10 mg" in row.text]
        self.assertTrue(dose_chunks)
        passage=next(p for p in retriever.passages(dose_chunks) if "10 mg" in p.text)
        self.assertNotIn("ConditionY",passage.text)
        self.assertEqual([label["quote"] for label in passage.context],["ConditionY:","Oral:"])
        item=hybrid_agent._citation(passage)
        result={"parts":[{"question_fa":"پرسش دوز", "queries":["ConditionY"], "status":"answered","items":[item]}]}
        lookup=response_cache.Lookup("fixture",retriever.stamp,self.generation.source_generation)
        self.assertEqual(response_cache.validate(result,lookup),["3852"])
        source_evidence = evaluation.SourceEvidence()
        self.assertTrue(source_evidence.citation_valid(item))
        item["context"][0]["quote"]="Different condition:"
        self.assertIsNone(response_cache.validate(result,lookup))
        self.assertFalse(source_evidence.citation_valid(item))

    def test_model_generation_clone_preserves_source_context_and_copies_no_vectors_or_reservations(self):
        original=list(SearchChunk.objects.filter(generation=self.generation).order_by('source_id','ordinal'))
        from .models import ReferenceMedia,IndexedArticle
        ReferenceMedia.objects.create(generation=self.generation,source_id=original[0].source_id,
            content_hash=original[0].content_hash,media_key="um-"+"d"*32,kind="table",
            article_title=original[0].title,title="Source table",search_text="Source table",evidence_text="Original cells")
        IndexedArticle.objects.filter(generation=self.generation,source_id=original[0].source_id).update(media_built=True)
        self.generation.embedding_tokens_reserved=999
        self.generation.pending_embedding_inputs=['previous-request']
        self.generation.save(update_fields=['embedding_tokens_reserved','pending_embedding_inputs'])
        clone=indexing.clone_generation(self.generation)
        copied=list(SearchChunk.objects.filter(generation=clone).order_by('source_id','ordinal'))
        self.assertEqual(len(copied),len(original))
        for first,second in zip(original,copied):
            self.assertNotEqual(first.pk,second.pk)
            self.assertEqual((first.text,first.block_ids,first.input_hash,first.heading_path),
                             (second.text,second.block_ids,second.input_hash,second.heading_path))
        self.assertEqual(clone.embedding_profile,{})
        self.assertFalse(clone.embedding_ready)
        self.assertEqual(clone.embedding_tokens_reserved,0)
        self.assertEqual(clone.pending_embedding_inputs,[])
        self.assertEqual(ReferenceMedia.objects.get(generation=clone).evidence_text,"Original cells")
        self.assertTrue(IndexedArticle.objects.get(generation=clone,source_id=original[0].source_id).media_built)
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.embedding_tokens_reserved,999)
