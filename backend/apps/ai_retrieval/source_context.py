"""Complete selected evidence through source order and literal internal links."""
from dataclasses import replace
from functools import reduce
from hashlib import sha256
import operator
import re
from types import SimpleNamespace

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchVector
from django.db.models import Q

from apps.ai_lab import lexical, telemetry
from apps.ai_lab.models import ReferenceArticle, ReferenceParagraph, ReferenceSection
from apps.ai_lab.provider import ProviderError
from . import media, source_links
from .chunking import source_metadata
from .models import ReferenceMedia

ROUTE_LABEL = re.compile(r"^(?:oral|intravenous|intramuscular|subcutaneous|topical|intranasal|rectal|parenteral|"
                         r"immediate.release|extended.release|children|adolescents|adults|infants|neonates|"
                         r"initial|maintenance|maximum|note)\b", re.I)


class SourceContext:
    def __init__(self, retriever, query, question, *, audience, intent, concepts, question_profile=None):
        self.r = retriever
        self.audience, self.intent = audience, intent
        self.context = lexical.search_context(question + " " + query, [query], audience=audience, intent=intent,
                                              question_profile=question_profile)
        self.drug_intents = [name for name in self.context.intents if name in {
            "treatment", "drug_therapy", "dose", "renal_dose", "adverse_effects", "contraindications",
            "interaction", "pregnancy", "monitoring", "mechanism", "indications"}]
        if question_profile and intent in {"treatment","drug_therapy","dose","renal_dose"}:
            conditions = [row["name"] for row in question_profile["conditions"] if row["status"] != "excluded"]
            if conditions:
                concepts = [word for word in lexical.tokens(conditions[0]) if word not in lexical.STOP_WORDS]
        noise = {"medical", "medication", "medications", "pharmacotherapy", "regimen", "regimens",
                 "dosing", "dosage", "dose", "doses", "safety", "selection", "restrictions"}
        self.concepts = [word for word in concepts if word not in noise]
        population = {"men", "women", "patients", "elderly"}
        condition = [word for word in self.concepts if word not in population]
        if len(condition) >= 2:
            self.concepts = condition
        self.links = getattr(retriever, "_source_link_maps", {})
        retriever._source_link_maps = self.links
        self.result, self.original = {}, set()
        self.stats = {"neighbors": 0, "section_links": 0, "article_links": 0, "graphic_links": 0,
                      "denied_links": 0, "unavailable_links": 0, "limited": False}
        self.visited = set()
        self.articles = {}

    def article(self, identifier):
        self.r.check_cancelled()
        if identifier in self.articles:
            return self.articles[identifier]
        if not self.r.permitted(identifier):
            self.stats["denied_links"] += 1
            self.articles[identifier] = None
            return None
        article = ReferenceArticle.objects.filter(generation_id=self.r.generation.source_generation,
                                                  source_id=identifier).first()
        self.articles[identifier] = article
        return article

    def passages(self, rows):
        grouped = {}
        for row in rows:
            if row.retrieval_number is not None:
                actual, _ = source_metadata(row.article.title, row.section.heading_path or [row.section.heading])
                if ((self.audience == "pediatric" and actual == "adult")
                        or (self.audience == "adult" and actual == "pediatric")):
                    continue
                grouped.setdefault(row.article_id, []).append(row)
        chunks = [SimpleNamespace(source_id=items[0].article.source_id,
                  content_hash=items[0].article.content_hash, block_ids=[row.pk for row in items])
                  for items in grouped.values()]
        return self.r.passages(chunks, consume=False)

    def add(self, passage, parent, kind, label=""):
        if passage.id in self.original or passage.id == parent.id:
            return False
        pending, seen = [parent.id], set()
        while pending:
            identifier = pending.pop()
            if identifier == passage.id:
                return False
            if identifier not in seen:
                seen.add(identifier)
                ancestor = self.result.get(identifier)
                if ancestor is not None:
                    pending.extend(row["source_id"] for row in ancestor.relations)
        relation = {"source_id": parent.id, "kind": kind, "label": label[:240]}
        if passage.id in self.result:
            old = self.result[passage.id]
            if relation not in old.relations:
                self.result[passage.id] = replace(old, relations=(*old.relations, relation))
            return False
        if len(self.result) >= max(1, settings.AI_LAB_SOURCE_CONTEXT_MAX_PASSAGES):
            self.stats["limited"] = True
            return False
        self.result[passage.id] = replace(passage, relations=(*passage.relations, relation))
        self.stats[kind] += 1
        return True

    def neighbors(self, seed):
        if seed.ordinal is None or seed.media:
            return
        section = seed.target.get("params", {}).get("sectionId")
        rows = ReferenceParagraph.objects.filter(article__generation_id=self.r.generation.source_generation,
            article__source_id=seed.article_id, section__source_id=section,
            ordinal__gte=max(0, seed.ordinal-1),
            ordinal__lte=seed.ordinal+max(1, settings.AI_LAB_SOURCE_CONTEXT_NEIGHBORS)).select_related("article", "section").order_by("ordinal")
        article = self.article(seed.article_id)
        if article is not None and "drug information" in article.title.lower():
            original = next((row for row in rows if row.ordinal == seed.ordinal), None)
            if original is not None:
                base = ReferenceParagraph.objects.filter(article=article, section_id=original.section_id)
                rows = self.indication_rows(base, [original])
        self.add_group(self.passages(rows), seed, "neighbors")

    def add_group(self, passages, parent, kind, label=""):
        additions = {p.id for p in passages if p.id not in self.result}
        if len(self.result) + len(additions) > max(1, settings.AI_LAB_SOURCE_CONTEXT_MAX_PASSAGES):
            self.stats["limited"] = True
            return
        for passage in passages:
            self.add(passage, parent, kind, label)

    def indication_rows(self, base, matches):
        distance = max(3, settings.AI_LAB_SOURCE_CONTEXT_NEIGHBORS)
        condition = reduce(operator.or_, [Q(section_id=row.section_id,
            ordinal__gte=max(0, row.ordinal-1), ordinal__lte=row.ordinal+distance) for row in matches])
        candidates = {(row.section_id,row.ordinal):row for row in base.filter(condition)
                      .select_related("article", "section")}
        matched = {row.pk for row in matches}
        selected = {}
        for seed in matches:
            preceding = candidates.get((seed.section_id,seed.ordinal-1))
            if preceding is not None and re.search(r"^\s*(?:note|however|caution|avoid|do not)\b", preceding.text, re.I):
                selected[preceding.pk] = preceding
            for ordinal in range(seed.ordinal, seed.ordinal+distance+1):
                row = candidates.get((seed.section_id,ordinal))
                if row is None:
                    break
                if row.pk not in matched and row.text.endswith(":") and not ROUTE_LABEL.search(row.text):
                    break
                if row.retrieval_number is not None:
                    selected[row.pk] = row
        return sorted(selected.values(), key=lambda row:row.ordinal)[:24]

    def section_rows(self, article, identifier):
        sections = list(ReferenceSection.objects.filter(article=article).order_by("ordinal"))
        root = next((row for row in sections if row.source_id == identifier), None)
        if root is None:
            return []
        allowed = {root.pk}
        for row in sections:
            if row.parent_id in allowed:
                allowed.add(row.pk)
        return ReferenceParagraph.objects.filter(article=article, section_id__in=allowed,
            retrieval_number__isnull=False).select_related("article", "section").order_by("ordinal")[:16]

    def linked_article(self, article, parent, link, *, depth=0):
        if article.is_directory:
            if depth >= 1:
                return
            for child in article.related_topics[:3]:
                identifier = str(child.get("id", ""))
                if not source_links.IDENTIFIER.fullmatch(identifier):
                    continue
                target = self.article(identifier)
                if target is not None:
                    self.linked_article(target, parent, link, depth=depth+1)
            return
        drug = "drug information" in article.title.lower()
        if drug and not self.drug_intents:
            return
        identifier = link.get("section_id", "")
        if identifier:
            rows = list(self.section_rows(article, identifier))
        else:
            sections = list(ReferenceSection.objects.filter(article=article).order_by("ordinal"))
            pattern = (lexical.REGIMEN_HEADING if drug and self.intent in {"treatment", "drug_therapy"}
                       else "|".join(lexical.INTENTS[name][1] for name in self.drug_intents) if drug
                       else lexical.INTENTS[self.intent][1])
            selected = [s for s in sections if re.search(pattern, " > ".join(s.heading_path) or s.heading, re.I)]
            def correct_population(section):
                actual, _ = source_metadata(article.title, section.heading_path or [section.heading])
                return not ((self.audience == "pediatric" and actual == "adult")
                            or (self.audience == "adult" and actual == "pediatric"))
            selected = [s for s in selected if correct_population(s)]
            selected.sort(key=lambda s: -lexical.heading_score(s.heading, s.heading_path, self.context))
            base = ReferenceParagraph.objects.filter(article=article, section__in=selected[:8])
            matches = []
            if self.concepts:
                expression = reduce(operator.and_, [SearchQuery(word, config="english") for word in self.concepts])
                matches = list(base.annotate(document=SearchVector("text", config="english"))
                    .filter(document=expression).select_related("article", "section").order_by("ordinal")[:8])
            if drug and self.intent in {"treatment", "drug_therapy"} and not matches:
                # A link proves a mention, not an indication or recommendation.
                # Do not borrow another condition's dose when the indication is absent.
                return
            if matches:
                rows = self.indication_rows(base, matches)
            else:
                rows = list(base.filter(retrieval_number__isnull=False)
                    .select_related("article", "section").order_by("ordinal")[:8])
        self.add_group(self.passages(rows), parent, "article_links", link["label"])

    def follow(self, parent, link, counts):
        kind = link["kind"]
        identifier = link.get("target_id", parent.article_id)
        if kind == "article" and identifier == parent.article_id and link.get("section_id"):
            kind = "section"
        identity = (kind, identifier, link.get("section_id", ""))
        if identity in self.visited:
            return
        self.visited.add(identity)
        if kind == "graphic":
            if counts[kind] >= 2:
                self.stats["limited"] = True
                return
            counts[kind] += 1
            prefix = "graphic-" + identifier + "-"
            rows = ReferenceMedia.objects.filter(generation=self.r.generation, source_id=parent.article_id,
                content_hash=parent.content_hash, media_key__startswith=prefix).order_by("pk")[:2]
            for row in rows:
                raw = source_links.services.get_topic(identifier, include_memberships=False)
                if raw is None or sha256(raw["body_html"].encode()).hexdigest() != row.descriptor.get("graphic_hash"):
                    raise ProviderError("REFERENCE_INDEX_STALE")
                self.add(media.passage(row), parent, "graphic_links", link["label"])
            return
        if kind == "section" or identifier == parent.article_id:
            if counts["section"] >= 4:
                self.stats["limited"] = True
                return
            article = self.article(parent.article_id)
            if article is not None:
                before = len(self.result)
                self.add_group(self.passages(self.section_rows(article, link.get("section_id", ""))),
                               parent, "section_links", link["label"])
                counts["section"] += int(len(self.result) > before)
            return
        if counts["article"] >= settings.AI_LAB_SOURCE_CONTEXT_LINKED_ARTICLES:
            self.stats["limited"] = True
            return
        article = self.article(identifier)
        if article is not None:
            before = len(self.result)
            self.linked_article(article, parent, link)
            counts["article"] += int(len(self.result) > before)
        else:
            self.stats["unavailable_links"] += 1

    def expand(self, seeds):
        self.result = {p.id:p for p in seeds}
        self.original = set(self.result)
        leading = list(dict.fromkeys(p.article_id for p in seeds if not p.media))[:settings.AI_LAB_SOURCE_CONTEXT_START_ARTICLES]
        for seed in seeds:
            if seed.article_id in leading:
                self.neighbors(seed)
        # Resolve local section references first. Their paragraphs can contain
        # the actual drug links (summary -> selection/dosing -> monograph).
        # Only then follow one outward hop; never crawl linked article bodies.
        counts = {"section":0, "article":0, "graphic":0}
        scanned, pending = set(), []
        while True:
            parents = [p for p in self.result.values() if p.article_id in leading
                       and not p.media and p.id not in scanned]
            if not parents:
                break
            local = []
            for parent in parents:
                scanned.add(parent.id)
                article = self.article(parent.article_id)
                if article is None:
                    continue
                if parent.article_id not in self.links:
                    with telemetry.operation("source_links"):
                        self.links[parent.article_id] = source_links.load(article)
                anchor = parent.target.get("params", {}).get("searchAnchor")
                for link in self.links[parent.article_id].get(anchor, []):
                    score = lexical.heading_score(parent.section, parent.heading_path, self.context)
                    same_article = link.get("target_id",parent.article_id) == parent.article_id
                    if link["kind"] == "section" or (same_article and link.get("section_id")):
                        label_score = lexical.heading_score(link["label"],[link["label"]],self.context)
                        if self.intent in {"treatment","drug_therapy","dose","renal_dose"} and re.search(
                                r"dosing|dosage|selection|regimen|medical|medication|pharmacolog",link["label"],re.I):
                            label_score += 8
                        local.append((-label_score,-score,len(local),parent,link))
                    elif not same_article or link["kind"] == "graphic":
                        priority = 1 if link["kind"] == "graphic" else 3
                        pending.append((priority,-score,len(pending),parent,link))
            before = set(self.result)
            for _, _, _, parent, link in sorted(local,key=lambda row:row[:3]):
                self.follow(parent,link,counts)
            if not (set(self.result)-before):
                break
        targets = {row[4].get("target_id") for row in pending if row[4]["kind"] == "article"}
        drug_ids = set(ReferenceArticle.objects.filter(generation_id=self.r.generation.source_generation,
            source_id__in=targets, title__icontains="drug information").values_list("source_id", flat=True))
        if self.intent in {"treatment", "drug_therapy", "dose", "renal_dose"}:
            pending = [(0 if link.get("target_id") in drug_ids else priority, score, order, parent, link)
                       for priority, score, order, parent, link in pending]
        # Cover distinct source sections/families before spending every slot
        # on interchangeable options listed in one paragraph.
        balanced, depths, seen_targets = [], {}, set()
        for priority, score, order, parent, link in sorted(pending,key=lambda row:row[:3]):
            identity = (link["kind"],link.get("target_id"),link.get("section_id", ""))
            if identity in seen_targets:
                continue
            seen_targets.add(identity)
            group = (parent.article_id, parent.target.get("params",{}).get("sectionId"), priority)
            depth = depths.get(group,0)
            depths[group] = depth+1
            balanced.append((priority,depth,score,order,parent,link))
        for _, _, _, _, parent, link in sorted(balanced, key=lambda row:row[:4]):
            self.follow(parent, link, counts)
        return list(self.result.values()), self.stats


def expand(retriever, passages, question, query, *, audience, intent, concepts, question_profile=None):
    if not settings.AI_LAB_SOURCE_CONTEXT_ENABLED or not passages:
        return passages, {"enabled": False}
    reader = SourceContext(retriever, query, question, audience=audience, intent=intent, concepts=concepts,
                           question_profile=question_profile)
    result, audit = reader.expand(passages)
    return result, {"enabled": True, **audit}
