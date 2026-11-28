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
from django.db.models.functions import Length

from apps.ai_lab import lexical, telemetry
from apps.ai_lab.models import ReferenceArticle, ReferenceParagraph, ReferenceSection
from apps.ai_lab.provider import ProviderError
from apps.ai_lab.section_tree import balanced_paragraphs, expand_sections, therapy_root
from apps.uptodate.search_catalog import normalize
from . import evidence, media, source_links
from .chunking import source_metadata
from .models import ReferenceMedia

ROUTE_LABEL = re.compile(r"^(?:oral|intravenous|intramuscular|subcutaneous|topical|intranasal|rectal|parenteral|"
                         r"immediate.release|extended.release|children|adolescents|adults|infants|neonates|"
                         r"initial|maintenance|maximum|note)\b", re.I)
# A monograph's dose line ("Oral: 400 to 600 mg once") is shorter than the
# indexer's 40-character floor, so it carries no retrieval_number. It is still
# the most specific evidence the source holds for an indication, and it is only
# read when a source link leads into that monograph -- never by free-text search.
DOSE_TEXT = re.compile(r"\b\d+(?:\.\d+)?\s*(?:mg|mcg|microgram|g|gram|units?|mL|mEq|%)\b", re.I)
DOSING_HEADING = re.compile(r"dosing|dosage", re.I)
# A catalog root inside a longer clinical phrase is not a drug mention:
# "calcitonin gene-related peptide" is not calcitonin, "dopamine antagonists"
# is not dopamine. Skip a match the next word turns into a class or a pathway.
CLASS_FOLLOW = {"antagonist", "antagonists", "agonist", "agonists", "receptor", "receptors",
                "gene", "genes", "pathway", "pathways", "blocker", "blockers"}


class SourceContext:
    def __init__(self, retriever, query, question, *, audience, intent, concepts, question_profile=None):
        self.r = retriever
        self.audience, self.intent = audience, intent
        self.context = lexical.search_context(question + " " + query, [query], audience=audience, intent=intent,
                                              question_profile=question_profile)
        self.regimen = (intent in {"treatment", "drug_therapy", "dose", "renal_dose"}
                        or bool(question_profile and question_profile.get("regimen_requested")))
        self.drug_intents = [name for name in self.context.intents if name in {
            "treatment", "drug_therapy", "dose", "renal_dose", "adverse_effects", "contraindications",
            "interaction", "pregnancy", "monitoring", "mechanism", "indications"}]
        if self.regimen and "drug_therapy" not in self.drug_intents:
            self.drug_intents.append("drug_therapy")
        if question_profile and self.regimen:
            conditions = [row["name"] for row in question_profile["conditions"] if row["status"] != "excluded"]
            if conditions:
                concepts = [word for word in lexical.tokens(conditions[0]) if word not in lexical.STOP_WORDS]
        noise = {"medical", "medication", "medications", "pharmacotherapy", "regimen", "regimens",
                 "dosing", "dosage", "dose", "doses", "safety", "selection", "restrictions"}
        self.concepts = [word for word in concepts if word not in noise]
        self.medications = set(lexical.tokens(" ".join((question_profile or {}).get("medications", []))))
        population = {"men", "women", "patients", "elderly"}
        condition = [word for word in self.concepts if word not in population]
        if len(condition) >= 2:
            self.concepts = condition
        self.links = getattr(retriever, "_source_link_maps", {})
        retriever._source_link_maps = self.links
        self.result, self.original = {}, set()
        self.stats = {"neighbors": 0, "subsections": 0, "section_links": 0, "article_links": 0, "graphic_links": 0,
                      "dose_sweep": 0, "denied_links": 0, "unavailable_links": 0, "limited": False}
        # Headroom the dose sweep may use past the passage cap, so link-following
        # cannot crowd out the dose rows a therapy answer needs.
        self.reserve = 0
        self.visited = set()
        self.articles = {}

    def sections(self, article):
        cached = self.r._section_cache.get(article.pk)
        if cached is None:
            cached = list(ReferenceSection.objects.filter(article=article).order_by("ordinal"))
            self.r._section_cache[article.pk] = cached
        return cached

    def article(self, identifier):
        self.r.check_cancelled()
        if identifier in self.articles:
            return self.articles[identifier]
        if not self.r.permitted(identifier):
            self.stats["denied_links"] += 1
            self.articles[identifier] = None
            return None
        article = self.r._article_cache.get(identifier)
        if article is None:
            article = ReferenceArticle.objects.filter(generation_id=self.r.generation.source_generation,
                                                      source_id=identifier).first()
            if article is not None:
                self.r._article_cache[identifier] = article
        self.articles[identifier] = article
        return article

    def retrievable(self, row):
        """A numbered paragraph, or a short dose line from a drug monograph.

        The indexer excludes paragraphs under 40 characters, which is exactly
        the length of a monograph's dose line ("Oral: 400 to 600 mg once") and
        of its indication label. Those lines are read only through a source
        link into the monograph, never by free-text search, so they are let
        through here instead of requiring a full index rebuild.
        """
        if row.retrieval_number is not None:
            return True
        if not DOSE_TEXT.search(row.text or ""):
            return False
        if "drug information" not in (row.article.title or "").lower():
            return False
        return bool(DOSING_HEADING.search(" > ".join(row.section.heading_path or [row.section.heading])))

    def passages(self, rows, *, audience=None):
        audience = audience or self.audience
        grouped = {}
        for row in rows:
            if self.retrievable(row):
                actual, _ = source_metadata(row.article.title, row.section.heading_path or [row.section.heading])
                if ((audience == "pediatric" and actual == "adult")
                        or (audience == "adult" and actual == "pediatric")):
                    continue
                grouped.setdefault(row.article_id, []).append(row)
        chunks = [SimpleNamespace(source_id=items[0].article.source_id,
                  content_hash=items[0].article.content_hash, block_ids=[row.pk for row in items])
                  for items in grouped.values()]
        return self.r.passages(chunks, consume=False,
            prefetched=[row for items in grouped.values() for row in items], allow_unretrievable=True)

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
        if len(self.result) >= max(1, settings.AI_LAB_SOURCE_CONTEXT_MAX_PASSAGES) + self.reserve:
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
        if len(self.result) + len(additions) > max(1, settings.AI_LAB_SOURCE_CONTEXT_MAX_PASSAGES) + self.reserve:
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
                if self.retrievable(row):
                    selected[row.pk] = row
        return sorted(selected.values(), key=lambda row:row.ordinal)[:24]

    def source_indication_labels(self, base, parent):
        """Match original indication labels to the linking source's own words.

        A subtype need not be repeated in a monograph (e.g. the source says
        seizure types, while the dosing label says seizures). No medical
        synonym/indication is invented here; the writer still sees both the
        source relationship and the original label and must verify applicability.
        """
        generic = {"drug", "drugs", "dose", "doses", "dosing", "dosage", "therapy", "treatment",
            "initial", "maintenance", "monotherapy", "adjunctive", "oral", "intravenous", "note",
            "adult", "adults", "children", "infants", "patients", "patient", "daily", "guidance",
            "type", "types", "first", "line", "most", "best", "general", "efficacy", "established",
            "evidence", "data", "available", "limited", "clinical", "study", "studies", "results",
            "variable", "optimal", "effective", "effectiveness", "formulation", "preparation"}
        def words(text):
            return {word.rstrip("s") for word in lexical.tokens(text)
                    if word not in lexical.STOP_WORDS and word not in generic and len(word)>3}
        # Reference titles and evidence-quality wording do not identify an
        # indication ("efficacy not established" must not outrank "seizures").
        source_words = words(re.sub(r"\(See\b[^)]*\)","",parent.text,flags=re.I))
        condition_words = words(" ".join(self.concepts))
        labels = list(base.filter(text__endswith=":").annotate(size=Length("text"))
            .filter(size__lte=180).select_related("article","section").order_by("ordinal"))
        scored = [(4*len(words(row.text) & condition_words)+len(words(row.text) & source_words), row) for row in labels]
        best = max((score for score,_ in scored), default=0)
        return [row for score,row in scored if score == best][:2] if best else []

    def section_rows(self, article, identifier):
        sections = self.sections(article)
        # Some snapshots repeat an anchor in an empty outline node and the
        # actual body. Resolve all occurrences in this same article, rather
        # than silently choosing the empty outline and missing its regimen.
        roots = {row.pk for row in sections if row.source_id == identifier}
        return self.branch_rows(article, sections, roots) if roots else []

    def branch_rows(self, article, sections, roots):
        allowed = expand_sections(sections, roots)
        rows = ReferenceParagraph.objects.filter(article=article, section_id__in=allowed)
        if "drug information" in (article.title or "").lower():
            # Keep the short dose lines and indication labels of dosing
            # branches; elsewhere in the article they are only labels.
            dosing = {section.pk for section in sections if DOSING_HEADING.search(section.heading or "")}
            short = set(expand_sections(sections, dosing)) & set(allowed)
            rows = rows.filter(Q(retrieval_number__isnull=False)
                               | Q(section_id__in=short, exclusion_reason="too_short"))
        else:
            rows = rows.filter(retrieval_number__isnull=False)
        return balanced_paragraphs(rows.select_related("article", "section"), 24)

    def therapy_subsections(self, seeds):
        if not self.regimen:
            return
        budget = max(1, settings.AI_LAB_SOURCE_CONTEXT_MAX_PASSAGES // 2)
        visited = set()
        for seed in seeds:
            article = self.article(seed.article_id)
            # Monographs can repeat a dose family across indications. Their
            # separate indication-aware lookup must retain its tighter scope.
            if article is None or "drug information" in article.title.lower():
                continue
            sections = self.sections(article)
            by_id = {section.pk: section for section in sections}
            anchor = seed.target.get("params", {}).get("sectionId")
            matches = [section for section in sections if section.source_id == anchor and section.hierarchy_known]
            for section in matches:
                root = therapy_root(section, by_id)
                if root is None or root.pk in visited:
                    continue
                visited.add(root.pk)
                rows = self.branch_rows(article, sections, {root.pk})
                for passage in self.passages(rows):
                    if self.stats["subsections"] >= budget:
                        self.stats["limited"] = True
                        return
                    self.add(passage, seed, "subsections", root.heading)

    def linked_article(self, article, parent, link, *, depth=0, kind="article_links"):
        audience = self.audience
        if audience == "general":
            inherited, _ = source_metadata(parent.title, parent.heading_path or [parent.section])
            if inherited in {"adult", "pediatric"}:
                audience = inherited
        if article.is_directory:
            if depth >= 1:
                return
            for child in article.related_topics[:3]:
                identifier = str(child.get("id", ""))
                if not source_links.IDENTIFIER.fullmatch(identifier):
                    continue
                if not self.r.register_related(article.source_id, identifier, kind="directory_link"):
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
            sections = self.sections(article)
            pattern = (lexical.REGIMEN_HEADING if drug and self.regimen
                       else "|".join(lexical.INTENTS[name][1] for name in self.drug_intents) if drug
                       else lexical.INTENTS[self.intent][1])
            selected = [s for s in sections if re.search(pattern, " > ".join(s.heading_path) or s.heading, re.I)]
            def correct_population(section):
                actual, _ = source_metadata(article.title, section.heading_path or [section.heading])
                return not ((audience == "pediatric" and actual == "adult")
                            or (audience == "adult" and actual == "pediatric"))
            selected = [s for s in selected if correct_population(s)]
            selected.sort(key=lambda s: -lexical.heading_score(s.heading, s.heading_path, self.context))
            base = ReferenceParagraph.objects.filter(article=article, section__in=selected[:8])
            matches = []
            if self.concepts:
                expression = reduce(operator.and_, [SearchQuery(word, config="english") for word in self.concepts])
                matches = list(base.annotate(document=SearchVector("text", config="english"))
                    .filter(document=expression).select_related("article", "section").order_by("ordinal")[:8])
            if drug and self.regimen and not matches and link.get("drug"):
                matches = self.source_indication_labels(base,parent)
            if drug and self.regimen and not matches:
                # A link proves a mention, not an indication or recommendation.
                # Do not borrow another condition's dose when the indication is absent.
                return
            if matches:
                rows = self.indication_rows(base, matches)
            else:
                rows = balanced_paragraphs(base.filter(retrieval_number__isnull=False)
                    .select_related("article", "section"), 16)
        self.add_group(self.passages(rows,audience=audience), parent, kind, link["label"])

    def follow(self, parent, link, counts):
        kind = link["kind"]
        identifier = link.get("target_id", parent.article_id)
        if kind == "article" and identifier == parent.article_id and link.get("section_id"):
            kind = "section"
        identity = (kind, identifier, link.get("section_id", ""))
        if identity in self.visited:
            return
        if kind == "article" and identifier != parent.article_id \
                and counts["article"] >= settings.AI_LAB_SOURCE_CONTEXT_LINKED_ARTICLES:
            self.stats["limited"] = True
            return
        self.visited.add(identity)
        new_related = (settings.AI_LAB_TAG_SCOPED_SEARCH and identifier not in self.r.scope.ids)
        if kind != "graphic" and identifier != parent.article_id:
            if not self.r.register_related(parent.article_id, identifier):
                self.stats["limited"] = True
                return
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
        article = self.article(identifier)
        before = len(self.result)
        if article is not None:
            self.linked_article(article, parent, link)
            counts["article"] += int(len(self.result) > before)
        else:
            self.stats["unavailable_links"] += 1
        if len(self.result) == before:
            self.visited.discard(identity)
        if new_related and not any(p.article_id == identifier for p in self.result.values()) \
                and not any(row["parent"] == identifier for row in self.r.scope.related.values()):
            self.r.scope.related.pop(identifier,None)

    def sweep_drug_doses(self):
        """Open the monographs of drugs the evidence itself names.

        A topic can name a drug without linking it, or its link can lose the
        budget to a comparator. The monograph is where the dose for the asked
        indication lives, so those drugs are opened directly, after the link
        path, through the same indication-aware path as a followed link.
        Bounded by AI_LAB_SOURCE_CONTEXT_DOSE_DRUGS; no model call is made.
        """
        if not self.regimen:
            return
        from .retrieval import drug_name_catalog
        names = drug_name_catalog(self.r.generation.source_generation)
        present = {p.article_id for p in self.result.values()}
        added = 0
        limit = max(0, settings.AI_LAB_SOURCE_CONTEXT_DOSE_DRUGS)
        self.reserve = limit * 6

        def preferred(entries):
            adult = [row for row in entries if row[1].lower().endswith(": drug information")]
            pediatric = [row for row in entries if "pediatric" in row[1].lower()]
            return (pediatric or adult or entries) if self.audience == "pediatric" else (adult or entries)

        # Count mentions across the whole evidence first: a drug the answer will
        # discuss appears in several selected paragraphs, while an incidental
        # name (an interacting drug in a warning) appears once.
        counts, parents, order = {}, {}, {}
        for passage in list(self.result.values()):
            if passage.media:
                continue
            parent = self.article(passage.article_id)
            if parent is None or "drug information" in parent.title.lower():
                continue
            path = " > ".join(passage.heading_path) or passage.section
            if re.search(r"to avoid|contraindicat", path, re.I):
                continue
            words = normalize(passage.text).split()[:400]
            found = set()
            for position in range(len(words)):
                for size in range(min(6, len(words) - position), 0, -1):
                    name = tuple(words[position:position + size])
                    if name in names and (position + size >= len(words)
                                          or words[position + size] not in CLASS_FOLLOW):
                        found.add(name)
            for name in found:
                counts[name] = counts.get(name, 0) + 1
                order.setdefault(name, len(order))
                parents.setdefault(name, passage)

        per_section = {}
        for name in sorted(counts, key=lambda key: (-counts[key], order[key])):
            if added >= limit:
                break
            section = parents[name].section
            # Three monographs per source section: one section (triptans) would
            # otherwise take the whole budget and leave the NSAID branch bare.
            if per_section.get(section, 0) >= 3:
                continue
            options = [identifier for identifier, _ in preferred(names[name])]
            if not options or options[0] in present:
                continue
            identifier = options[0]
            passage = parents[name]
            monograph = self.article(identifier)
            if monograph is None or not self.r.register_related(passage.article_id, identifier,
                                                                kind="source_mention"):
                continue
            present.add(identifier)
            self.linked_article(monograph, passage, {"kind": "article", "target_id": identifier,
                "section_id": "", "drug": True, "label": " ".join(name)}, kind="dose_sweep")
            added += 1
            per_section[section] = per_section.get(section, 0) + 1
        self.reserve = 0

    def expand(self, seeds):
        self.result = {p.id:p for p in seeds}
        self.original = set(self.result)
        leading = list(dict.fromkeys(p.article_id for p in seeds if not p.media))[:settings.AI_LAB_SOURCE_CONTEXT_START_ARTICLES]
        self.therapy_subsections([seed for seed in seeds if seed.article_id in leading and not seed.media])
        # A drug monograph reached directly (not among the leading articles)
        # still needs the dose rows that sit below its indication label. Without
        # them the answer sees the label only and reports "no dose evidence"
        # while the dose is in the next source paragraph. Bounded by the same
        # linked-article budget so one question cannot pull every monograph.
        neighbor_articles = set(leading)
        extra_articles = max(0, settings.AI_LAB_SOURCE_CONTEXT_LINKED_ARTICLES)
        for seed in seeds:
            if seed.media:
                continue
            if seed.article_id in neighbor_articles:
                self.neighbors(seed)
                continue
            if not self.regimen or extra_articles <= 0:
                continue
            article = self.article(seed.article_id)
            if article is None or "drug information" not in article.title.lower():
                continue
            neighbor_articles.add(seed.article_id)
            extra_articles -= 1
            self.neighbors(seed)
        # Resolve local section references first. Their paragraphs can contain
        # the actual drug links (summary -> selection/dosing -> monograph).
        # Only then follow one outward hop; never crawl linked article bodies.
        counts = {"section":0, "article":0, "graphic":0}
        scanned, related_scanned, pending = set(), set(), []
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
                if parent.article_id not in related_scanned:
                    related_scanned.add(parent.article_id)
                    terms = set(self.concepts) | self.medications
                    for link in self.links[parent.article_id].get(source_links.RELATED, []):
                        shared = terms.intersection(lexical.tokens(link["label"]))
                        if shared:
                            pending.append((4,-len(shared),len(pending),parent,link))
                anchor = parent.target.get("params", {}).get("searchAnchor")
                for link in self.links[parent.article_id].get(anchor, []):
                    if self.regimen and link.get("drug") and re.search(
                            r"\b(?:to avoid|contraindicat\w*)\b", " > ".join(parent.heading_path) or parent.section,re.I):
                        continue
                    score = lexical.heading_score(parent.section, parent.heading_path, self.context)
                    same_article = link.get("target_id",parent.article_id) == parent.article_id
                    if link["kind"] == "section" or (same_article and link.get("section_id")):
                        label_score = lexical.heading_score(link["label"],[link["label"]],self.context)
                        if self.regimen and re.search(
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
        if self.regimen:
            def drug_priority(priority, parent, link):
                if link.get("target_id") not in drug_ids:
                    return priority+2
                label = set(lexical.tokens(link["label"]))
                heading = set(lexical.tokens(parent.section))
                direct = bool(label) and label == heading
                # The source's dedicated medication/recommendation section
                # outranks its incidental mentions or comparator paragraphs.
                recommended = bool(evidence.RECOMMENDATION.search(parent.text))
                if direct and recommended:
                    return 0
                if recommended:
                    return 1
                return 2 if direct else 3
            pending = [(drug_priority(priority,parent,link), score, order, parent, link)
                       for priority, score, order, parent, link in pending]
        # Cover distinct source sections/families before spending every slot
        # on interchangeable options listed in one paragraph.
        balanced, depths, seen_targets = [], {}, {}
        for priority, score, order, parent, link in sorted(pending,key=lambda row:row[:3]):
            identity = (link["kind"],link.get("target_id"),link.get("section_id", ""))
            if seen_targets.get(identity,0) >= 2:
                continue
            seen_targets[identity] = seen_targets.get(identity,0)+1
            group = (parent.article_id, parent.target.get("params",{}).get("sectionId"), priority)
            depth = depths.get(group,0)
            depths[group] = depth+1
            balanced.append((priority,depth,score,order,parent,link))
        for _, _, _, _, parent, link in sorted(balanced, key=lambda row:row[:4]):
            self.follow(parent, link, counts)
        # The linked sections name drugs the seeds never mentioned (a NSAID
        # list inside the treatment topic). Sweep again over the whole set.
        self.sweep_drug_doses()
        return list(self.result.values()), self.stats


def expand(retriever, passages, question, query, *, audience, intent, concepts, question_profile=None):
    if not settings.AI_LAB_SOURCE_CONTEXT_ENABLED or not passages:
        return passages, {"enabled": False}
    reader = SourceContext(retriever, query, question, audience=audience, intent=intent, concepts=concepts,
                           question_profile=question_profile)
    result, audit = reader.expand(passages)
    return result, {"enabled": True, **audit}
