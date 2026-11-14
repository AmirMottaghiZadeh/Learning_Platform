from hashlib import sha256
from io import StringIO
from types import SimpleNamespace
from unittest.mock import patch
import json

from django.core.cache import caches
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase, override_settings

from apps.ai_lab import hybrid_agent, test_reference_index as fixtures
from apps.ai_lab.models import ReferenceArticle, ReferenceParagraph
from apps.ai_lab.provider import ProviderError
from apps.ai_lab.retrieval import Passage
from apps.uptodate.search_extraction import extract_article
from . import source_links, source_context, media
from .evidence import retain_with_context
from .models import RetrievalGeneration
from .retrieval import HybridRetriever


class SourceLinkParserTests(SimpleTestCase):
    def parse(self, body):
        extracted = extract_article("10", body)
        parser = source_links.ParagraphLinks()
        parser.feed(extracted.html)
        return extracted, parser.links

    def test_literal_article_section_and_graphic_links_belong_to_their_original_block(self):
        body='''<div id="topicText"><p class="headingAnchor" id="H1"><span class="h1">Selection</span> — Original text
        <a class="drug" data-topicid="20" onclick="doOperation({contentId:'20'})">Fixturemed</a>.</p>
        <p>Observe restrictions. <a onclick="doOperation({sectionName:'H2'})">Special considerations</a>
        <a onclick="doOperation({contentIds:['30']})">table 5</a></p>
        <p><a href="https://outside.example/drug">External</a><a onclick="doOperation({abstractNumbers:[1]})">1</a></p></div>'''
        extracted, links = self.parse(body)
        self.assertEqual(links[extracted.blocks[0].paragraph_id][0],
                         {"kind":"article","target_id":"20","section_id":"","drug":True,"label":"Fixturemed"})
        self.assertEqual([row["kind"] for row in links[extracted.blocks[1].paragraph_id]],["section","graphic"])
        self.assertNotIn(extracted.blocks[2].paragraph_id,links)

    def test_script_and_external_targets_never_become_followable_links(self):
        _, links=self.parse('<div id="topicText"><p>Original source <a data-topicid="https://private.example/">bad</a>'
            '<a href="javascript:fetch(1)">external</a></p><script>doOperation({contentId:"999"})</script></div>')
        self.assertEqual(links,{})

    def test_metadata_is_cached_only_for_signed_exact_source_hash(self):
        body='<div id="topicText"><p>Original <a data-topicid="20">Fixturemed</a> recommendation.</p></div>'
        extracted=extract_article("10",body)
        article=SimpleNamespace(source_id="10",content_hash=extracted.content_hash)
        raw={"body_html":body}
        with patch.object(source_links.services,"get_topic",return_value=raw) as read:
            first=source_links.load(article)
            self.assertEqual(source_links.load(article),first)
            read.assert_called_once()
        key=f"source-links:{source_links.VERSION}:{source_links.EXTRACTION_VERSION}:10:{article.content_hash}"
        cached=caches["ai_lab"].get(key)
        cached["links"]={"forged":[{"kind":"article","target_id":"999","label":"bad"}]}
        caches["ai_lab"].set(key,cached,60)
        with patch.object(source_links.services,"get_topic",return_value=raw) as read:
            self.assertEqual(source_links.load(article),first)
            read.assert_called_once()
        with patch.object(source_links.services,"get_topic",return_value={"body_html":body+"changed"}):
            with self.assertRaisesMessage(ProviderError,"REFERENCE_INDEX_STALE"):
                source_links.load(SimpleNamespace(source_id="10",content_hash="f"*64))


class SourceContextIntegrationTests(TestCase):
    databases="__all__"
    setUp_source=fixtures.ReferenceIndexTests.setUp
    write_article=fixtures.ReferenceIndexTests.write_article
    add_title=fixtures.ReferenceIndexTests.add_title
    build_reference=fixtures.ReferenceIndexTests.build

    def setUp(self):
        self.setUp_source()
        self.write_article("3851",'''<div id="topicText">
          <p class="headingAnchor" id="H1"><span class="h1">Selection and dosing</span> — We recommend the source-defined first-line drug therapy for ConditionY.</p>
          <p>We prefer <a class="drug" data-topicid="3852">Fixturemed</a> over the source-defined comparator for ConditionY.
          See <a onclick="doOperation({sectionName:'H2'})">Special considerations</a>.</p>
          <p>However, monitor the source-defined safety restrictions when initiating this treatment for ConditionY.</p>
          <p class="headingAnchor" id="H2"><span class="h1">Special considerations</span></p>
          <p>Avoid this regimen in the explicitly excluded source population for ConditionY.</p></div>''',title="ConditionY medical treatment")
        self.add_title("3852")
        self.write_article("3852",'''<div id="topicText">
          <p class="headingAnchor" id="H1"><span class="h1">Dosing: Adult</span></p>
          <p>ConditionY:</p><p>Oral:</p><p>Adults: 10 mg daily; observe the original source qualifiers and restrictions.</p>
          <p>However, avoid this dose in the original source-defined excluded population.</p>
          <p>DifferentCondition:</p><p>Oral:</p><p>DifferentCondition: 999 mg daily, for its separate source-defined indication only.</p>
          <p class="headingAnchor" id="H2"><span class="h1">Dosing: Pediatric</span></p>
          <p>ConditionY in children: 777 mg daily, with its separate original population restrictions.</p></div>''',title="Fixturemed: Drug information")
        self.build_reference()
        call_command("build_hybrid_index",stdout=StringIO())
        self.generation=RetrievalGeneration.objects.latest("created_at")
        self.r=HybridRetriever(SimpleNamespace(user=SimpleNamespace(pk="source-context-test",is_staff=True,is_authenticated=True)),generation=self.generation)

    def seed(self):
        row=ReferenceParagraph.objects.filter(article__generation_id=self.generation.source_generation,
            article__source_id="3851",text__contains="We recommend").first()
        article=row.article
        chunk=SimpleNamespace(source_id=article.source_id,content_hash=article.content_hash,block_ids=[row.pk])
        return self.r.passages([chunk],consume=False)

    def expand(self):
        return source_context.expand(self.r,self.seed(),"دارودرمانی ConditionY چیست؟","ConditionY medical treatment",
            audience="adult",intent="drug_therapy",concepts=["conditiony","medical"])

    def test_neighbor_section_and_exact_monograph_complete_the_evidence_without_search_or_embedding(self):
        with patch("apps.ai_retrieval.embeddings.embed",side_effect=AssertionError("No embedding allowed")),\
                patch.object(self.r,"lexical_ids",side_effect=AssertionError("No global search allowed")):
            passages,audit=self.expand()
        self.assertTrue(any("We prefer" in p.text for p in passages))
        self.assertTrue(any(p.section=="Special considerations" for p in passages))
        doses=[p for p in passages if p.article_id=="3852"]
        self.assertTrue(any("10 mg" in p.text for p in doses))
        self.assertFalse(any("999 mg" in p.text or "777 mg" in p.text for p in doses))
        self.assertTrue(all(p.relations for p in doses))
        self.assertGreater(audit["article_links"],0)
        for passage in passages:
            row=ReferenceParagraph.objects.get(pk=int(passage.id[1:]))
            self.assertEqual(passage.text,row.text)
            self.assertEqual(passage.target["params"]["searchAnchor"],row.source_anchor)

    def test_denied_linked_article_is_not_read_or_exposed(self):
        allowed=self.r.permitted
        with patch.object(self.r,"permitted",side_effect=lambda identifier:identifier!="3852" and allowed(identifier)):
            passages,audit=self.expand()
        self.assertFalse(any(p.article_id=="3852" for p in passages))
        self.assertGreater(audit["denied_links"],0)

    def test_flag_returns_the_unchanged_original_selection(self):
        seeds=self.seed()
        with override_settings(AI_LAB_SOURCE_CONTEXT_ENABLED=False),patch.object(source_links,"load") as read:
            rows,audit=source_context.expand(self.r,seeds,"question","ConditionY",audience="adult",intent="treatment",concepts=["conditiony"])
        self.assertEqual(rows,seeds)
        self.assertFalse(audit["enabled"])
        read.assert_not_called()

    def test_section_reference_can_lead_to_a_drug_link_without_another_global_search(self):
        self.write_article("3851",'''<div id="topicText">
          <p class="headingAnchor" id="H1"><span class="h1">Summary</span></p>
          <p>For ConditionY, see <a onclick="doOperation({sectionName:'H9'})">Selection and dosing</a> for the original treatment details.</p>
          <p class="headingAnchor" id="H2"><span class="h1">Background</span></p>
          <p>Other source background that does not answer the drug-therapy question.</p>
          <p class="headingAnchor" id="H9"><span class="h1">Selection and dosing</span></p>
          <p>For ConditionY we prefer <a data-topicid="3852">Fixturemed</a> rather than the original comparator, with source restrictions.</p></div>''',title="ConditionY treatment")
        self.build_reference(force=True)
        call_command("build_hybrid_index",stdout=StringIO())
        self.generation=RetrievalGeneration.objects.latest("created_at")
        self.r=HybridRetriever(self.r.request,generation=self.generation)
        row=ReferenceParagraph.objects.filter(article__generation_id=self.generation.source_generation,
            article__source_id="3851",text__contains="see Selection and dosing").first()
        seed=self.r.passages([SimpleNamespace(source_id="3851",content_hash=row.article.content_hash,block_ids=[row.pk])],consume=False)
        with override_settings(AI_LAB_SOURCE_CONTEXT_NEIGHBORS=1):
            passages,audit=source_context.expand(self.r,seed,"دارودرمانی ConditionY","ConditionY treatment",
                audience="adult",intent="drug_therapy",concepts=["conditiony"])
        self.assertTrue(any(p.article_id=="3852" and "10 mg" in p.text for p in passages))
        self.assertGreater(audit["section_links"],0)
        self.assertGreater(audit["article_links"],0)

    @override_settings(AI_LAB_SOURCE_CONTEXT_LINKED_ARTICLES=2)
    def test_linked_regimens_cover_different_source_sections_before_more_options_of_one_family(self):
        self.write_article("3851",'''<div id="topicText">
          <p class="headingAnchor" id="H1"><span class="h1">Initial treatment</span> — We recommend the original first-line medication options for ConditionY.</p>
          <p>For ConditionY, the choices include <a data-topicid="3852">Fixturemed</a>,
          <a data-topicid="3853">Optionmed</a> and <a data-topicid="3854">Anothermed</a>.
          See <a onclick="doOperation({sectionName:'H8'})">Combination selection and dosing</a> for the other class.</p>
          <p class="headingAnchor" id="H8"><span class="h1">Combination selection and dosing</span></p>
          <p>For the source-defined ConditionY subgroup we also recommend <a data-topicid="3855">Otherclassmed</a>, with its original restrictions.</p></div>''',title="ConditionY treatment")
        for identifier,name in [("3853","Optionmed"),("3854","Anothermed"),("3855","Otherclassmed")]:
            self.add_title(identifier)
            self.write_article(identifier,fixtures.html("Dosing: Adult",
                "ConditionY: oral 5 mg daily with the source-defined indication, schedule and safety restrictions."),title=name+": Drug information")
        self.build_reference(force=True)
        call_command("build_hybrid_index",stdout=StringIO())
        self.generation=RetrievalGeneration.objects.latest("created_at")
        self.r=HybridRetriever(self.r.request,generation=self.generation)
        row=ReferenceParagraph.objects.filter(article__generation_id=self.generation.source_generation,
            article__source_id="3851",text__contains="We recommend the original").first()
        seed=self.r.passages([SimpleNamespace(source_id="3851",content_hash=row.article.content_hash,block_ids=[row.pk])],consume=False)
        passages,_=source_context.expand(self.r,seed,"دارودرمانی ConditionY","ConditionY treatment",
            audience="adult",intent="drug_therapy",concepts=["conditiony"])
        linked={p.article_id for p in passages if p.article_id!="3851"}
        self.assertIn("3855",linked)
        self.assertEqual(len(linked),2)


class LinkedEvidenceTests(SimpleTestCase):
    def paragraph(self,number,text,relations=()):
        return Passage("P"+str(number),"10","Source","Treatment",text,
            {"screen":"uptodateArticle","params":{"id":"10","sectionId":"H1","searchAnchor":"anchor"}},"a"*64,
            heading_path=("Treatment",),relations=relations)

    def test_dose_keeps_its_source_parent_and_parent_is_cited_in_verification_and_cache(self):
        parent=self.paragraph(100,"We do not recommend Fixturemed for the source-defined population.")
        dose=self.paragraph(200,"Oral 10 mg daily for the indicated population.",({"source_id":"P100","kind":"article_links","label":"Fixturemed"},))
        self.assertEqual(retain_with_context([parent,dose],[dose.id]),[parent,dose])
        evidence,bindings={},{}
        hybrid_agent._admit_evidence(evidence,bindings,[parent,dose])
        child=next(p for p in evidence.values() if p.text==dose.text)
        self.assertEqual(child.relations[0]["source_id"],bindings[parent.id])
        claims,_=hybrid_agent._claims(f"توضیح مستند. [{child.id}]",list(evidence.values()))
        self.assertIn(bindings[parent.id],claims[0]["source_ids"])

    def test_missing_parent_cannot_leave_a_linked_dose_in_the_model_input(self):
        dose=self.paragraph(200,"Oral 10 mg daily.",({"source_id":"P100","kind":"article_links","label":"Fixturemed"},))
        self.assertEqual(retain_with_context([dose],[dose.id]),[])
        evidence,bindings={},{}
        hybrid_agent._admit_evidence(evidence,bindings,[dose])
        self.assertFalse(evidence)

    def test_additional_group_is_skipped_as_a_whole_when_its_context_budget_is_full(self):
        parent=self.paragraph(100,"Original treatment recommendation and its restrictions.")
        dose=self.paragraph(200,"Oral 10 mg daily.")
        guard=self.paragraph(300,"However, avoid this dose in the source-excluded population.")
        reader=source_context.SourceContext(SimpleNamespace(),"Condition treatment","درمان",audience="adult",intent="treatment",concepts=["condition"])
        reader.result={parent.id:parent};reader.original={parent.id}
        with override_settings(AI_LAB_SOURCE_CONTEXT_MAX_PASSAGES=2):
            reader.add_group([dose,guard],parent,"article_links","Fixturemed")
        self.assertEqual(list(reader.result),[parent.id])
        self.assertTrue(reader.stats["limited"])


class LinkedMediaValidationTests(SimpleTestCase):
    def test_original_table_text_hash_and_metadata_are_validated(self):
        article={"body_html":"original article"}
        content_hash=sha256(article["body_html"].encode()).hexdigest()
        record={"key":"um-"+"a"*32,"kind":"table","title":"Original table","caption":"Original caption","text":"Original cells"}
        citation={"source":"uptodate","content_hash":content_hash,
            "quote":"Original table\nOriginal caption\nOriginal cells",
            "target":{"screen":"uptodateArticle","params":{"id":"10","mediaKey":record["key"],"mediaContentHash":content_hash}},
            "media":[{"key":record["key"],"kind":"table","article_id":"10","content_hash":content_hash,"content_complete":True}]}
        with patch.object(source_links.services,"get_topic",return_value=article),patch("apps.ai_retrieval.media_catalog.catalog_media",return_value=[record]):
            self.assertTrue(media.citation_valid(citation))
            self.assertFalse(media.citation_valid({**citation,"quote":"Altered clinical values"}))
            changed=json.loads(json.dumps(citation));changed["media"][0]["content_complete"]=False
            self.assertFalse(media.citation_valid(changed))
