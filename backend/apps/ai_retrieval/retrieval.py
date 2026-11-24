"""Direct evidence lookup: indexed source tagging, lexical rank and vector rank."""
from concurrent.futures import ThreadPoolExecutor
from contextvars import copy_context
from dataclasses import replace
from functools import reduce
from functools import lru_cache
import json
import operator
import uuid
import re
from types import SimpleNamespace

from django.conf import settings
from django.contrib.postgres.search import SearchQuery, SearchRank
from django.core.cache import caches
from django.db import connections, close_old_connections
from django.db.models import F
from django.db.models import TextField
from django.db.models.functions import Cast, Length
from django.db.models import Q
from django.utils.crypto import salted_hmac

from apps.billing.enforcement import require_feature
from apps.core.exceptions import PlatformAPIError
from apps.ai_lab import lexical, question_profile as profiles, reference_index, telemetry
from apps.ai_lab.models import ReferenceArticle, ReferenceParagraph
from apps.ai_lab.provider import ProviderError
from apps.ai_lab.retrieval import Passage, source_medication, treatment_topic_titles
from apps.uptodate import services as uptodate
from apps.uptodate.search_catalog import SearchCatalog, normalize
from . import embeddings, evidence, indexing, vectors
from .models import RetrievalHead, SearchAlias, SearchChunk
from .chunking import token_count
from .query_terms import query_text
from .scope import SourceScope
from .treatment_sources import PROBE_ARTICLES, treatment_coverage


def reciprocal_rank_fusion(rankings):
    scores = {}
    for ranking in rankings:
        for position, identifier in enumerate(dict.fromkeys(ranking), 1):
            scores[identifier] = scores.get(identifier, 0) + 1 / (60 + position)
    return scores


def concept_terms(query, intent):
    hints = set(lexical.tokens(lexical.HINTS.get(intent, "")))
    generic = {"major", "important", "significant", "common", "first", "second", "third", "line",
               "recommended", "recommendation", "recommendations", "initial", "regimen", "regimens",
               "medication", "medications", "pediatric", "paediatric", "pharmacologic", "pharmacological"}
    if intent == "adverse_effects":
        generic.update({"serious", "severe", "key", "main", "principal"})
    return [w for w in dict.fromkeys(lexical.tokens(query)) if w not in lexical.STOP_WORDS and w not in hints and w not in generic][:24]


def query_context(query, *, question="", **kwargs):
    context = lexical.search_context(question or query, [query], **kwargs)
    qualifiers = set(lexical.tokens(query)) & {"important", "major", "serious", "significant"}
    if "adverse_effects" in context.intents and qualifiers:
        context = replace(context, aspects=tuple(dict.fromkeys([*context.aspects, *sorted(qualifiers)])))
    return context


@lru_cache(maxsize=2)
def drug_name_catalog(source_generation):
    """Small title metadata only, never a scan of article bodies at question time."""
    names = {}
    for identifier, title in ReferenceArticle.objects.filter(generation_id=source_generation,
            is_directory=False, title__icontains="drug information").values_list("source_id", "title"):
        root = tuple(normalize(title.split(":",1)[0].split("(",1)[0]).split())
        if root and len(root) <= 6:
            names.setdefault(root, []).append((identifier,title))
    return names


class HybridRetriever:
    def __init__(self, request, *, generation=None, check_cancelled=lambda:None):
        self.request, self.consumed = request, set()
        self.scope = SourceScope()
        self._treatment_scope = None
        self.search_count = 0
        self._article_cache = {}
        self._section_cache = {}
        self._label_cache = {}
        self.check_cancelled = check_cancelled
        require_feature(request, "uptodate")
        self.stamp = reference_index.source_stamp()
        source = reference_index.active_generation(self.stamp)
        if generation is None:
            head = RetrievalHead.objects.filter(pk=self.stamp.identity).select_related("active").first()
            generation = head.active if head else None
            if generation and generation.scope != "full":
                raise ProviderError("HYBRID_INDEX_NOT_READY")
        if (generation is None or generation.status != "ready" or not generation.catalog_ready
                or generation.source_revision != self.stamp.revision or generation.source_generation != source):
            raise ProviderError("HYBRID_INDEX_NOT_READY")
        self.generation = generation

    def validate(self):
        if (reference_index.source_stamp() != self.stamp
                or reference_index.active_generation(self.stamp) != self.generation.source_generation):
            raise ProviderError("REFERENCE_INDEX_STALE")

    def permitted(self, identifier):
        try:
            require_feature(self.request, "uptodate", item=identifier, consume=False)
            return True
        except PlatformAPIError:
            return False

    def register_related(self, parent, target, *, kind="source_link"):
        if self._treatment_scope is not None:
            target = str(target)
            article = self._article_cache.get(target)
            if article is None:
                article = ReferenceArticle.objects.filter(generation_id=self.generation.source_generation,
                                                          source_id=target).first()
                if article is not None:
                    self._article_cache[target] = article
            if article is not None and not lexical.treatment_title_allowed(article.title, self._treatment_scope):
                return False
        if not settings.AI_LAB_TAG_SCOPED_SEARCH or not self.scope.established:
            return True
        return self.scope.follow(parent, target, limit=max(1, settings.AI_LAB_SOURCE_CONTEXT_LINKED_ARTICLES), kind=kind)

    def _choose_roots(self, identifiers, query, audience, lookup_kind, intent, profile, *, require_treatment_condition=False):
        rows = list(ReferenceArticle.objects.filter(generation_id=self.generation.source_generation,
            source_id__in=list(dict.fromkeys(identifiers))[:200], is_directory=False).only(
                "source_id", "title", "content_hash", "related_topics", "is_directory", "generation_id"))
        order = {identifier: n for n, identifier in enumerate(identifiers)}
        concepts = set(concept_terms(query, intent))
        entities = [set(lexical.tokens(entity)) - lexical.STOP_WORDS - {"history", "severe", "previous", "prior"}
                    for entity in profiles.entities(profile or {})]
        entities = [words for words in entities if words]
        if require_treatment_condition and self._treatment_scope and profile:
            conditions = [set(lexical.tokens(row["name"])) - lexical.STOP_WORDS
                          for row in profile["conditions"] if row["status"] != "excluded"]
            conditions = [words for words in conditions if words]
            if conditions:
                rows = [row for row in rows if any(words <= set(lexical.tokens(row.title)) for words in conditions)]
        context = query_context(query, lookup_kind=lookup_kind, audience=audience,
                                intent=intent, question_profile=profile)
        def source_match(article):
            words = set(lexical.tokens(article.title))
            drug = "drug information" in article.title.lower()
            pediatric = bool(words & {"pediatric", "paediatric", "children"})
            exact_drug = set(lexical.tokens(article.title.split(":", 1)[0].split("(", 1)[0])) == concepts
            # A word such as "sequence", "monitoring" or "prevention" must
            # not outweigh the actual condition/drug in a tagged title.
            overlap = [len(words & entity)/len(entity) for entity in entities]
            return (lookup_kind == "drug" and not drug, lookup_kind == "drug" and not exact_drug,
                audience == "pediatric" and not pediatric, audience in {"adult", "general"} and pediatric,
                -max(overlap, default=0), -sum(overlap))

        def rank(article):
            return (*source_match(article),
                lexical.treatment_title_priority(article.title, self._treatment_scope),
                -lexical.heading_score(article.title, [article.title], context), order.get(article.source_id, 999))
        rows.sort(key=rank)
        rows = [article for article in rows if lexical.treatment_title_allowed(article.title, self._treatment_scope)]
        if self._treatment_scope and self._treatment_scope.stage in {"general", "initial"}:
            admitted = [article for article in rows[:PROBE_ARTICLES] if self.permitted(article.source_id)]
            coverage = treatment_coverage(self.generation.source_generation,
                                          [article.source_id for article in admitted], self._treatment_scope, audience)
            best_match = min((source_match(article) for article in admitted if coverage.get(article.source_id, 0) >= 0), default=None)
            primary = [article for article in admitted if coverage.get(article.source_id) == 2 and source_match(article) == best_match]
            if primary:
                rows = primary
            else:
                rows = [article for article in rows if coverage.get(article.source_id, 0) >= 0]
        chosen = []
        for article in rows:
            if self.permitted(article.source_id):
                chosen.append(article.source_id)
                self._article_cache[article.source_id] = article
            if len(chosen) >= max(1, settings.AI_LAB_SOURCE_CONTEXT_START_ARTICLES):
                break
        return chosen

    def _bind_scope(self, query, audience, intent, lookup_kind, profile):
        if self.scope.established:
            return
        identifiers = self.catalog_ids(query, audience, intent, lookup_kind, profile)
        if self._treatment_scope and settings.AI_LAB_INITIAL_SEARCH_FALLBACK:
            identifiers = self.treatment_title_ids(identifiers, query, profile)
        roots = self._choose_roots(identifiers, query, audience, lookup_kind, intent, profile)
        fallback = not roots and settings.AI_LAB_INITIAL_SEARCH_FALLBACK
        if fallback:
            # Cheap title metadata first. Never OR/rank the complete paragraph corpus.
            terms = concept_terms(query, intent)
            terms = sorted(set(terms), key=lambda word: -len(word))[:4]
            title_filter = reduce(operator.or_, [Q(title__icontains=word) for word in terms], Q(pk__in=[]))
            identifiers = list(ReferenceArticle.objects.filter(title_filter,
                generation_id=self.generation.source_generation, is_directory=False)
                .values_list("source_id", flat=True)[:120])
            roots = self._choose_roots(identifiers, query, audience, lookup_kind, intent, profile, require_treatment_condition=True)
            if not roots:
                expression = SearchQuery(query, config="english", search_type="websearch")
                base = SearchChunk.objects.filter(generation=self.generation, search_document=expression)
                if audience in {"adult", "pediatric"}:
                    base = base.exclude(audience="pediatric" if audience == "adult" else "adult")
                identifiers = list(base.annotate(score=SearchRank(F("search_document"), expression))
                    .order_by("-score", "pk").values_list("source_id", flat=True)[:40])
                if not identifiers and self.generation.embedding_ready:
                    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="reference-initial") as pool:
                        ids, _ = pool.submit(copy_context().run, self.semantic_ids, query, audience).result()
                    rows = dict(SearchChunk.objects.filter(pk__in=ids).values_list("pk", "source_id"))
                    identifiers = [rows[i] for i in ids if i in rows]
                roots = self._choose_roots(identifiers, query, audience, lookup_kind, intent, profile, require_treatment_condition=True)
        self.scope.bind(roots, fallback=fallback)

    def treatment_title_ids(self, identifiers, query, profile):
        conditions = [row["name"] for row in (profile or {}).get("conditions", []) if row["status"] != "excluded"]
        titles = treatment_topic_titles(self.generation.source_generation, [*conditions, query])
        return list(dict.fromkeys([*identifiers[:120], *(row["id"] for row in titles
            if lexical.treatment_title_allowed(row["title"], self._treatment_scope))]))

    def catalog_ids(self, query, audience, intent="general", lookup_kind="topic", question_profile=None):
        words = normalize(query).split()[:12]
        phrases = [" ".join(words[start:start + size]) for size in range(1, len(words)+1)
                   for start in range(len(words)-size+1)]
        entity_phrases = []
        if question_profile:
            for entity in profiles.entities(question_profile)[:4]:
                parts = normalize(entity).split()[:8]
                entity_phrases.append([" ".join(parts[start:start+size]) for size in range(1,len(parts)+1)
                                       for start in range(len(parts)-size+1)])
            phrases += [phrase for group in entity_phrases for phrase in group]
        cache_key = "source-tag-metadata:v1:" + salted_hmac("source-tag-metadata", json.dumps([
            str(self.generation.pk), sorted(set(phrases))], ensure_ascii=False)).hexdigest()
        try: saved = caches["ai_lab"].get(cache_key)
        except Exception: saved = None
        if (isinstance(saved,list) and len(saved)<=300 and all(isinstance(row,dict)
                and set(row)=={"alias","weight","source_id","topic_lists"}
                and isinstance(row["alias"],str) and type(row["weight"]) is int
                and isinstance(row["source_id"],str) and isinstance(row["topic_lists"],list)
                and all(isinstance(value,str) for value in row["topic_lists"]) for row in saved)):
            matches = [SimpleNamespace(alias=row["alias"],weight=row["weight"],
                concept=SimpleNamespace(source_id=row["source_id"],topic_lists=row["topic_lists"])) for row in saved]
        else:
            matches = list(SearchAlias.objects.filter(generation=self.generation, alias__in=phrases).select_related("concept"))
            # Only immutable catalog metadata is shared, never a patient's
            # question, facts, permissions, passages or generated answer.
            saved = [{"alias":row.alias,"weight":row.weight,"source_id":row.concept.source_id,
                      "topic_lists":row.concept.topic_lists} for row in matches]
            try: caches["ai_lab"].set(cache_key,saved,86400)
            except Exception: pass
        if not matches:
            return []
        all_matches = matches
        concepts = set(concept_terms(query, intent))
        clinical = [row for row in matches if set(normalize(row.alias).split()) & concepts]
        if clinical:
            matches = clinical
        def score(row):
            start = next((n for n in range(len(words)) if " ".join(words[n:n+len(row.alias.split())]) == row.alias), len(words))
            return ((start, -len(row.alias.split()), -row.weight, row.alias) if lookup_kind == "drug"
                    else (-len(row.alias.split()), start, -row.weight, row.alias))
        match = min(matches, key=score)
        suffix = {"pediatric":" children", "adult":" adult", "patient":" patient education"}.get(audience, "")
        chosen = []
        if question_profile:
            for group in entity_phrases:
                candidates = [row for row in all_matches if row.alias in group]
                if candidates:
                    chosen.append(min(candidates,key=lambda row:(-len(row.alias.split()),-row.weight,row.alias)))
        chosen.append(match)
        selected = list({row.concept.source_id:row for row in chosen}.values())[:4]
        catalogs = [SearchCatalog([], {row.concept.source_id:row.concept.topic_lists}).hits(
            row.concept.source_id,query+suffix) for row in selected]
        # Preserve the original single-tag order. Cases/relationships may need
        # both a condition and drug tag; interleave them without extra API calls.
        return list(dict.fromkeys(identifier for n in range(max(map(len,catalogs),default=0))
                                   for group in catalogs for identifier in group[n:n+1]))

    def lexical_ids(self, query, audience, intent="general", lookup_kind="topic", question_profile=None, *, question=""):
        if connections[indexing.alias()].vendor != "postgresql":
            raise ProviderError("HYBRID_REQUIRES_POSTGRESQL")
        count = settings.AI_LAB_HYBRID_CANDIDATES
        base = SearchChunk.objects.filter(generation=self.generation)
        scoped = settings.AI_LAB_TAG_SCOPED_SEARCH and self.scope.established
        if scoped:
            base = base.filter(source_id__in=self.scope.ids)
        excluded = "adult" if audience == "pediatric" else "pediatric" if audience == "adult" else None
        if excluded:
            base = base.exclude(audience=excluded)
        terms = concept_terms(query, intent)
        if not terms:
            return [], []
        broad = reduce(operator.and_, [SearchQuery(word, config="english") for word in terms])
        strict = SearchQuery(query, config="english", search_type="websearch")
        def ranked(rows, expression):
            return list(rows.filter(search_document=expression).annotate(score=SearchRank(
                F("search_document"), expression, cover_density=True, normalization=32)).order_by("-score", "pk").values_list("pk", flat=True)[:count])
        exact = ranked(base, strict)
        relaxed = ranked(base, broad) if len(exact) < count else []
        if len(set(exact + relaxed)) < min(settings.AI_LAB_HYBRID_TOP_K, count) and len(terms) > 1:
            # OR is a final sparse-result fallback over clinical concept terms,
            # never over ubiquitous words such as "adverse effects" or "dose".
            fallback_query = reduce(operator.or_, [SearchQuery(word, config="english") for word in terms])
            relaxed = list(dict.fromkeys([*relaxed, *ranked(base, fallback_query)]))[:count]
        sources = list(self.scope.ids) if scoped else self.catalog_ids(query, audience, intent, lookup_kind, question_profile)
        if not scoped and self._treatment_scope:
            if settings.AI_LAB_INITIAL_SEARCH_FALLBACK:
                sources = self.treatment_title_ids(sources, query, question_profile)
            sources = self._choose_roots(sources, query, audience, lookup_kind, intent, question_profile)
        curated = []
        if sources:
            tagged = base.filter(source_id__in=sources)
            context = query_context(query, question=question, audience=audience, intent=intent, question_profile=question_profile)
            objectives = question_profile["objectives"] if question_profile else [intent]
            pattern = "|".join(lexical.INTENTS[name][1] for name in dict.fromkeys([intent,*objectives])).replace(r"\b", r"\y")
            if intent in {"treatment", "drug_therapy"}:
                pattern += "|dosing|dosage|administration|regimen|pharmacologic|summary.*recommendations"
            heading_rows = tagged.annotate(path_text=Cast("heading_path", TextField())).values(
                "pk", "source_id", "heading", "heading_path", "ordinal")
            headings = list(heading_rows.filter(Q(heading__iregex=pattern) | Q(path_text__iregex=pattern))[:2000])
            if context.initial_only:
                initial = lexical.INITIAL_THERAPY.replace(r"\b", r"\y")
                matches = heading_rows.filter(Q(heading__iregex=initial) | Q(path_text__iregex=initial)
                                              | Q(text__iregex=initial)).order_by("source_id", "ordinal")[:2000]
                headings = list({row["pk"]: row for row in [*headings, *matches]}.values())
            positions = {identifier: n for n, identifier in enumerate(sources)}
            headings.sort(key=lambda row: (-lexical.heading_score(row["heading"], row["heading_path"], context),
                                          positions.get(row["source_id"], 999), row["ordinal"]))
            balanced, remainder, sections, articles = [], [], {}, {}
            for row in headings:
                section = (row["source_id"], tuple(row["heading_path"]) or (row["heading"],))
                if sections.get(section, 0) >= 3 or articles.get(row["source_id"], 0) >= 12:
                    remainder.append(row)
                    continue
                balanced.append(row)
                sections[section] = sections.get(section, 0) + 1
                articles[row["source_id"]] = articles.get(row["source_id"], 0) + 1
            # Tag-only synonyms must still reach their linked article even
            # when the alias itself never appears in the source paragraphs.
            fallback = [row["pk"] for row in (balanced + remainder)[:count]] or list(tagged.order_by("ordinal").values_list("pk", flat=True)[:count])
            curated = list(dict.fromkeys([*fallback, *ranked(tagged, broad)]))[:count]
        return list(dict.fromkeys([*exact, *relaxed]))[:count], curated

    def semantic_ids(self, query, audience):
        close_old_connections()
        try:
            configuration = embeddings.profile()
            if self.generation.embedding_profile != configuration:
                raise ProviderError("EMBEDDING_PROFILE_CHANGED")
            digest = salted_hmac("hybrid-query-embedding", json.dumps([
                str(self.request.user.pk), configuration["id"], query], ensure_ascii=False)).hexdigest()
            cache, key = caches["ai_lab"], "embedding-query:" + digest
            try:
                value = cache.get(key)
            except Exception:
                value = None
            metadata = {"cache_hit": value is not None, "requests":0}
            if value is None:
                rows, details = embeddings.embed_query(query, check_cancelled=self.check_cancelled)
                value = rows[0]
                metadata.update(details, requests=details.get("provider_requests",1))
                try:
                    cache.set(key, value, 3600)
                except Exception:
                    pass
            value = embeddings.validate_vector(value, configuration["dimensions"])
            scope = {"source_ids": self.scope.ids} if settings.AI_LAB_TAG_SCOPED_SEARCH and self.scope.established else {}
            return vectors.search(self.generation, value, settings.AI_LAB_HYBRID_CANDIDATES,
                                  audience=audience, **scope), metadata
        finally:
            connections.close_all()

    def search(self, query, *, lookup_kind="topic", audience="general", intent="general", keywords=(), question=None, question_profile=None):
        from . import media

        self.validate()
        if question_profile is not None:
            question_profile = profiles.validate(question_profile)
            question_profile = profiles.for_question(question_profile, question or query)
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 240:
            raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
        query = query.strip()
        if self.search_count == 0:
            self._treatment_scope = lexical.treatment_topic_scope(question or f"{query} {audience}", lookup_kind, intent,
                                                                 audience=audience)
        if settings.AI_LAB_TAG_SCOPED_SEARCH:
            query = query_text(query)
            self._bind_scope(media.catalog_query(query) if media.requested(question or query) else query,
                             audience, intent, lookup_kind, question_profile)
        followup = self.search_count > 0
        self.search_count += 1
        if settings.AI_LAB_TAG_SCOPED_SEARCH and not self.scope.ids:
            return [], {"engine":"scoped", "scope":self.scope.audit(), "selected_passages":0,
                "selected_chunks":0,"context_tokens":0,"embedding":{"requests":0},"degraded":None}
        cache = caches["ai_lab"]
        context = query_context(query, question=question, lookup_kind=lookup_kind,
            audience=audience, intent=intent, keywords=keywords, question_profile=question_profile)
        cache_key = "hybrid-ranking:v8:" + salted_hmac("hybrid-ranking", json.dumps([
            str(getattr(getattr(self.request, "user", None), "pk", "diagnostic")), str(self.generation.pk),
            self.generation.embedding_profile, self.generation.embedding_ready, query, lookup_kind, audience, intent,
            list(keywords), question_profile, settings.AI_LAB_HYBRID_CANDIDATES,
            self.scope.audit() if settings.AI_LAB_TAG_SCOPED_SEARCH else None, followup,
            context.first_line_regimen, context.initial_only,
            (self._treatment_scope.stage, self._treatment_scope.populations, self._treatment_scope.modalities)
            if self._treatment_scope else None],
            sort_keys=True)).hexdigest()
        try:
            cached = cache.get(cache_key)
        except Exception:
            cached = None
        if isinstance(cached, dict) and isinstance(cached.get("rankings"), list) and len(cached["rankings"]) == 3:
            try:
                if any(not isinstance(ranking, list) or len(ranking) > 200 for ranking in cached["rankings"]):
                    raise ValueError
                cached_rankings = [[uuid.UUID(item) for item in ranking] for ranking in cached["rankings"]]
            except (ValueError, TypeError, AttributeError):
                cached = None
        else:
            cached = None
        semantic, embedding_metadata, degraded = [], {}, None
        if cached is not None:
            lexical_ids, semantic, curated = cached_rankings
            degraded = cached.get("degraded")
            embedding_metadata = {"requests": 0, "retrieval_cache_hit": True}
        elif self.generation.embedding_ready and not (settings.AI_LAB_TAG_SCOPED_SEARCH and followup):
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="reference-vector") as pool:
                future = pool.submit(copy_context().run, self.semantic_ids, query, audience)
                lexical_ids, curated = self.lexical_ids(query, audience, intent, lookup_kind, question_profile, question=question)
                try:
                    semantic, embedding_metadata = future.result()
                except ProviderError as exc:
                    degraded = exc.code  # Keyword evidence still requires all source/quality checks.
        else:
            lexical_ids, curated = self.lexical_ids(query, audience, intent, lookup_kind, question_profile, question=question)
            degraded = None if self.generation.embedding_ready else "HYBRID_EMBEDDINGS_NOT_READY"
        if cached is None and degraded is None:
            try:
                cache.set(cache_key, {"rankings": [[str(item) for item in ranking] for ranking in [lexical_ids, semantic, curated]],
                    "degraded": degraded}, settings.AI_LAB_RETRIEVAL_CACHE_TTL_SECONDS)
            except Exception:
                pass
        scores = reciprocal_rank_fusion([lexical_ids, semantic, curated])
        candidates = [row for row in SearchChunk.objects.filter(pk__in=list(scores), generation=self.generation)
                      if lexical.treatment_title_allowed(row.title, self._treatment_scope)]
        if lookup_kind == "drug" and intent in {"dose", "renal_dose"}:
            for neighbor, seed_id in self.dose_neighbors(candidates, audience):
                if neighbor.pk not in scores:
                    scores[neighbor.pk] = scores[seed_id] * .99
                    candidates.append(neighbor)
        concepts = concept_terms(query, intent)
        entity_terms = [set(lexical.tokens(entity))-lexical.STOP_WORDS for entity in profiles.entities(question_profile or {})]
        def rank(row):
            priority = .04 if lookup_kind == "drug" and row.source_kind == "drug" else 0
            title_tokens = set(lexical.tokens(row.title))
            if concepts:
                priority += .025 * sum(word in title_tokens for word in concepts) / len(concepts)
            if lookup_kind == "drug":
                root = row.title.split(":", 1)[0].split("(", 1)[0].strip().lower()
                if set(lexical.tokens(root)) == set(concepts):
                    priority += .015
                if audience == "general" and {"pediatric", "paediatric"} & title_tokens:
                    priority -= .008
            if audience == "adult" and "adults" in title_tokens or audience == "pediatric" and "children" in title_tokens:
                priority += .005
            if lookup_kind == "drug" and audience in {"adult","pediatric"} and row.audience == audience:
                priority += .015
            if audience == "patient" and row.source_kind == "patient":
                priority += .04
            priority += min(20, lexical.heading_score(row.heading, row.heading_path, context)) * .001
            if len(entity_terms)>1:
                text = set(lexical.tokens(row.title+" "+row.heading+" "+row.text))
                priority += .003 * sum(bool(words) and words<=text for words in entity_terms)
            if intent in {"dose", "renal_dose"}:
                priority += min(7,lexical.regimen_score(row.text,row.heading))*.001
            line = lexical.initial_match(row.heading_path or (row.heading,), row.text) if context.initial_only else 0
            return -line, lexical.treatment_title_priority(row.title, self._treatment_scope), -(scores[row.pk] + priority), str(row.pk)
        candidates.sort(key=rank)
        diverse, overflow, section_counts = [], [], {}
        for row in candidates:
            section = (row.source_id, tuple(row.heading_path) or (row.heading,))
            section_counts[section] = section_counts.get(section, 0) + 1
            (diverse if section_counts[section] <= 2 else overflow).append(row)
        candidates = diverse + overflow
        chosen, total_tokens = [], 0
        canonical_drug = lookup_kind == "drug" and audience == "general" and any(
            row.source_kind == "drug" and row.audience != "pediatric" for row in candidates)
        for row in candidates:
            if len(chosen) >= settings.AI_LAB_HYBRID_TOP_K:
                break
            if total_tokens + row.token_count > settings.AI_LAB_HYBRID_CONTEXT_TOKENS:
                continue
            if context.initial_only and lexical.after_initial_therapy(row.heading_path or (row.heading,)):
                continue
            # A default monograph lookup follows the canonical Drug information
            # edition. Do not mix pediatric-only assertions into a general
            # answer when its ordinary monograph is available. Explicit child
            # questions still use their own audience and sources.
            if canonical_drug and row.source_kind == "drug" and row.audience == "pediatric":
                continue
            try:
                require_feature(self.request, "uptodate", item=row.source_id, consume=False)
            except PlatformAPIError:
                continue
            chosen.append(row); total_tokens += row.token_count
        supplemented = 0
        if (settings.AI_LAB_HYBRID_REGIMEN_ENRICHMENT and lookup_kind == "topic"
                and not lexical.first_line_without_regimen(question or query)
                and intent in {"treatment", "drug_therapy"}):
            capacity = min(2, max(0, settings.AI_LAB_HYBRID_TOP_K-1))
            core = chosen[:max(1,settings.AI_LAB_HYBRID_TOP_K-capacity)]
            supplements = self.regimen_supplements(core, query, audience, intent)[:capacity] if capacity else []
            if supplements:
                # Keep the evidence/token budget fixed. These are monographs
                # named by the retrieved source, not recommendations guessed
                # by a drug dictionary or an extra model call.
                trial_tokens = sum(row.token_count for row in core)
                for row in supplements:
                    if trial_tokens + row.token_count > settings.AI_LAB_HYBRID_CONTEXT_TOKENS:
                        continue
                    core.append(row); trial_tokens += row.token_count; supplemented += 1
                if supplemented:
                    chosen = core
                    total_tokens = trial_tokens
        passages = self.passages(chosen, consume=False)
        from . import source_context
        original_evidence = set()
        with telemetry.operation("source_context"):
            if settings.AI_LAB_SOURCE_CONTEXT_ENABLED:
                passages, _ = evidence.focus_passages(passages, question or query, query,
                    lookup_kind=lookup_kind, audience=audience, intent=intent, keywords=keywords, question_profile=question_profile)
                original_evidence = {p.id for p in passages}
            passages, source_audit = source_context.expand(self, passages, question or query, query,
                audience=audience, intent=intent, concepts=concept_terms(query, intent), question_profile=question_profile)
        expanded = passages
        passages, focus = evidence.focus_passages(expanded, question or query, query,
            lookup_kind=lookup_kind, audience=audience, intent=intent, keywords=keywords, question_profile=question_profile)
        if original_evidence:
            passages = evidence.retain_with_context(expanded, original_evidence | {p.id for p in passages})
            focus.update(selected_passages=len(passages), selected_text_tokens=sum(token_count(p.text) for p in passages))
            if intent in {"treatment", "drug_therapy", "dose", "renal_dose"}:
                core = [p for p in passages if p.id in original_evidence]
                additional = [p for p in passages if p.id not in original_evidence]
                additional.sort(key=lambda p:(not bool(evidence.DOSE_NUMBER.search(p.text)),
                    -lexical.regimen_score(p.text,p.section)))
                passages = core + additional
        media_count=0
        explicit_media = media.requested(question or query)
        text_articles = {p.article_id for p in passages if not p.media}
        if explicit_media or text_articles:
            media_articles = self.scope.ids if explicit_media and settings.AI_LAB_TAG_SCOPED_SEARCH else text_articles
            selected=media.search(self.generation,query,article_ids=media_articles, audience=audience,
                kinds=media.requested_kinds(question or query), scoped=not explicit_media or settings.AI_LAB_TAG_SCOPED_SEARCH,
                implicit=not explicit_media)
            if explicit_media:
                roots = list(dict.fromkeys([*(row.source_id for row in chosen), *sorted(media_articles)]))
                if not settings.AI_LAB_TAG_SCOPED_SEARCH and not roots:
                    lookup = media.catalog_query(query)
                    page = uptodate.search_page(lookup, limit=6, offset=0, section="")
                    roots = [hit["id"] for hit in page["results"]]
                media_ids = roots[:6]
                source_articles = {article.source_id: article for article in ReferenceArticle.objects.filter(
                    generation_id=self.generation.source_generation, source_id__in=media_ids)}
                original = media.outline_media([source_articles[i] for i in media_ids if i in source_articles], [query],
                    question or query, audience, request=self.request, generation_id=self.generation.source_generation,
                    allow_related=lambda parent, target: self.register_related(parent, target, kind="media_source_link"))
                if media.ALGORITHM_INTENT.search(question or query):
                    selected = [passage for passage in selected if media.ALGORITHM_INTENT.search(passage.media[0]["title"])]
                preferred = {media.identity(p.media[0]): p for p in original}
                original_targets = {media.target_identity(p.media[0]) for p in original}
                for passage in selected:
                    if media.target_identity(passage.media[0]) not in original_targets:
                        preferred.setdefault(media.identity(passage.media[0]), passage)
                selected = list(preferred.values())
            allowed=[]
            for passage in selected:
                try:require_feature(self.request,"uptodate",item=passage.article_id,consume=False)
                except PlatformAPIError:continue
                allowed.append(passage)
            if explicit_media:
                allowed, _ = media.select_media(question or query, allowed)
            combined = {p.id: p for p in (allowed if explicit_media else passages)}
            for passage in ([p for p in passages if not p.media] if explicit_media else allowed):
                combined.setdefault(passage.id,passage)
            passages=list(combined.values())
        media_count=sum(bool(p.media) for p in passages)
        self.consume_passages(passages)
        self.validate()
        return passages, {"engine":"hybrid" if semantic else "lexical", "lexical_candidates":len(lexical_ids),
            "semantic_candidates":len(semantic), "tagging_candidates":len(curated), "selected_chunks":len(chosen),
            "selected_passages":len(passages), "context_tokens":sum(token_count(p.text) for p in passages),
            "chunk_context_tokens":total_tokens,"evidence_focus":focus,
            "regimen_supplement_chunks":supplemented,"selected_media":media_count,"source_context":source_audit,
            "generation":str(self.generation.pk), "degraded":degraded, "embedding":embedding_metadata,
            "scope":self.scope.audit() if settings.AI_LAB_TAG_SCOPED_SEARCH else None}

    def regimen_supplements(self, chunks, query, audience, intent):
        names = drug_name_catalog(self.generation.source_generation)
        mentioned, seen = [], set()
        for chunk in chunks:
            if chunk.source_kind == "drug":
                continue
            if re.search(r"\b(?:to avoid|contraindicat\w*)\b", " > ".join(chunk.heading_path) or chunk.heading,re.I):
                continue
            words = normalize(chunk.text).split()[:800]
            for position in range(len(words)):
                for size in range(min(6,len(words)-position),0,-1):
                    name=tuple(words[position:position+size])
                    if name in names and name not in seen:
                        mentioned.append(name);seen.add(name)
        condition = concept_terms(query,intent)
        if not condition:
            return []
        expression = reduce(operator.and_,[SearchQuery(term,config="english") for term in condition])
        selected_ids = {row.pk for row in chunks}
        excluded = "adult" if audience=="pediatric" else "pediatric" if audience=="adult" else ""
        # Bounded source-linked supplementation; the LLM still decides whether
        # the medication is recommended, contraindicated or only an alternative.
        for name in mentioned[:3]:
            sources = [identifier for identifier,_ in names[name]]
            parent = None
            if settings.AI_LAB_TAG_SCOPED_SEARCH and self.scope.established:
                parent = next((row.source_id for row in chunks if " ".join(name) in normalize(row.text)), None)
                if parent is None:
                    continue
            rows=list(SearchChunk.objects.filter(generation=self.generation,source_id__in=sources)
                .exclude(audience=excluded).exclude(pk__in=selected_ids)
                .annotate(path_text=Cast("heading_path",TextField()))
                .filter(Q(heading__iregex=lexical.REGIMEN_HEADING.replace(r"\b",r"\y"))
                        |Q(path_text__iregex=lexical.REGIMEN_HEADING.replace(r"\b",r"\y")))
                .filter(search_document=expression).annotate(score=SearchRank(F("search_document"),expression))
                .order_by("-score","ordinal")[:40])
            for neighbor,seed_id in self.dose_neighbors(rows,audience):
                if neighbor.pk not in {row.pk for row in rows} and neighbor.pk not in selected_ids:
                    neighbor.score = next(row.score for row in rows if row.pk==seed_id)
                    rows.append(neighbor)
            rows.sort(key=lambda row:("patient" in row.title.lower(),
                audience=="pediatric" and "pediatric" not in row.title.lower(),
                -lexical.regimen_score(row.text,row.heading),-row.score,row.ordinal))
            permitted=[]
            for row in rows:
                try:
                    require_feature(self.request,"uptodate",item=row.source_id,consume=False)
                except PlatformAPIError:
                    continue
                # Failed candidate lookups must not reserve every related
                # article slot before literal source links are expanded.
                if parent and not self.register_related(parent,row.source_id,kind="source_mention"):
                    continue
                permitted.append(row)
                if len(permitted)>=2:
                    break
            if permitted:
                return permitted
        return []

    def dose_neighbors(self, rows, audience):
        # A short label such as "Oral:" intentionally creates a chunk break.
        # The indication/note before it must still lead to the adjacent dose.
        seeds={}
        for row in rows:
            path=" > ".join(row.heading_path) or row.heading
            if row.source_kind=="drug" and re.search(r"dosing|dosage|\bdose\b",path,re.I) \
                    and not re.search(r"forms|storage|pricing",path,re.I) \
                    and lexical.regimen_score(row.text,row.heading)<4:
                seeds[(row.source_id,row.ordinal+1)]=row
            if len(seeds)>=12:
                break
        if not seeds:
            return []
        condition=reduce(operator.or_,[Q(source_id=identifier,ordinal=ordinal) for identifier,ordinal in seeds])
        excluded="adult" if audience=="pediatric" else "pediatric" if audience=="adult" else ""
        result=[]
        for row in SearchChunk.objects.filter(condition,generation=self.generation).exclude(audience=excluded):
            seed=seeds[(row.source_id,row.ordinal)]
            if row.heading_path==seed.heading_path and lexical.regimen_score(row.text,row.heading)>=4:
                result.append((row,seed.pk))
        return result

    def consume_passages(self, passages):
        needed = {passage.article_id for passage in passages} - self.consumed
        if not needed:
            return
        articles = ReferenceArticle.objects.filter(generation_id=self.generation.source_generation, source_id__in=needed)
        for article in articles:
            require_feature(self.request, "uptodate", item=article.source_id, consume=True)
            if self.stamp.backend == "mysql":
                with reference_index.mysql_source_connection().cursor() as cursor:
                    cursor.execute("SELECT SHA2(gzip,256) AS blob_hash FROM content WHERE id=%s", [article.source_id])
                    current = cursor.fetchone()
                if not current or current["blob_hash"] != article.blob_hash:
                    raise ProviderError("REFERENCE_INDEX_STALE")
            self.consumed.add(article.source_id)
        if needed - self.consumed:
            raise ProviderError("REFERENCE_INDEX_STALE")

    def passages(self, chunks, *, consume=True, prefetched=None):
        wanted = {identifier: chunk for chunk in chunks for identifier in chunk.block_ids}
        rows = ({row.pk:row for row in prefetched} if prefetched is not None else
            {row.pk: row for row in ReferenceParagraph.objects.filter(pk__in=list(wanted),
            article__generation_id=self.generation.source_generation).select_related("article", "section")})
        if len(rows) != len(wanted):
            raise ProviderError("REFERENCE_INDEX_STALE")
        missing = {r.section_id for r in rows.values()} - set(self._label_cache)
        for identifier in missing:
            self._label_cache[identifier] = []
        for label in ReferenceParagraph.objects.filter(section_id__in=missing,text__endswith=":") \
                .annotate(size=Length("text")).filter(size__lte=180).order_by("section_id","ordinal"):
            self._label_cache[label.section_id].append(label)
        labels=self._label_cache
        result, seen = [], set()
        drug_names = drug_name_catalog(self.generation.source_generation) if self._treatment_scope else ()
        for chunk in chunks:
            for identifier in chunk.block_ids:
                if identifier in seen:
                    continue
                row = rows[identifier]
                article = row.article
                if article.source_id != chunk.source_id or article.content_hash != chunk.content_hash or row.retrieval_number is None:
                    raise ProviderError("REFERENCE_INDEX_STALE")
                preceding = [label for label in labels.get(row.section_id, []) if label.ordinal < row.ordinal][-4:]
                heading_path = row.section.heading_path or [row.section.heading]
                medication = source_medication(article.title, [*heading_path, *(label.text for label in preceding)],
                                               drug_names)
                result.append(Passage("P"+str(row.pk),article.source_id,article.title,row.section.heading,row.text,
                    {"screen":"uptodateArticle","params":{"id":article.source_id,"title":article.title,
                     "sectionId":row.section.source_id,"searchAnchor":row.source_anchor,"searchContentHash":article.content_hash}},
                    article.content_hash,heading_path=tuple(row.section.heading_path),context=tuple({
                        "quote":label.text,"source_anchor":label.source_anchor,"ordinal":label.ordinal}
                        for label in preceding),
                    ordinal=row.ordinal, medication=medication))
                seen.add(identifier)
        if consume:
            self.consume_passages(result)
        return result
