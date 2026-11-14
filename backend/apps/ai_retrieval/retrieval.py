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
from apps.ai_lab import lexical, reference_index
from apps.ai_lab.models import ReferenceArticle, ReferenceParagraph
from apps.ai_lab.provider import ProviderError
from apps.ai_lab.retrieval import Passage
from apps.uptodate.search_catalog import SearchCatalog, normalize
from . import embeddings, evidence, indexing, vectors
from .models import RetrievalHead, SearchAlias, SearchChunk
from .chunking import token_count


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
    return [w for w in lexical.tokens(query) if w not in lexical.STOP_WORDS and w not in hints and w not in generic][:24]


def query_context(query, **kwargs):
    context = lexical.search_context(query, [query], **kwargs)
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

    def catalog_ids(self, query, audience, intent="general", lookup_kind="topic"):
        words = normalize(query).split()[:12]
        phrases = [" ".join(words[start:start + size]) for size in range(1, len(words)+1)
                   for start in range(len(words)-size+1)]
        matches = list(SearchAlias.objects.filter(generation=self.generation, alias__in=phrases).select_related("concept"))
        if not matches:
            return []
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
        catalog = SearchCatalog([], {match.concept.source_id: match.concept.topic_lists})
        return catalog.hits(match.concept.source_id, query + suffix)

    def lexical_ids(self, query, audience, intent="general", lookup_kind="topic"):
        if connections[indexing.alias()].vendor != "postgresql":
            raise ProviderError("HYBRID_REQUIRES_POSTGRESQL")
        count = settings.AI_LAB_HYBRID_CANDIDATES
        base = SearchChunk.objects.filter(generation=self.generation)
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
        sources = self.catalog_ids(query, audience, intent, lookup_kind)
        curated = []
        if sources:
            tagged = base.filter(source_id__in=sources)
            pattern = lexical.INTENTS.get(intent, lexical.INTENTS["general"])[1].replace(r"\b", r"\y")
            if intent in {"treatment", "drug_therapy"}:
                pattern += "|dosing|dosage|administration|regimen|pharmacologic|summary.*recommendations"
            headings = list(tagged.annotate(path_text=Cast("heading_path", TextField())).filter(
                Q(heading__iregex=pattern) | Q(path_text__iregex=pattern)).values(
                    "pk", "source_id", "heading", "heading_path", "ordinal")[:2000])
            context = query_context(query, audience=audience, intent=intent)
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
            return vectors.search(self.generation, value, settings.AI_LAB_HYBRID_CANDIDATES,
                                  audience=audience), metadata
        finally:
            connections.close_all()

    def search(self, query, *, lookup_kind="topic", audience="general", intent="general", keywords=(), question=None):
        self.validate()
        if not isinstance(query, str) or not 2 <= len(query.strip()) <= 240:
            raise ProviderError("INVALID_SEARCH_TOOL_ARGUMENTS")
        query = query.strip()
        cache = caches["ai_lab"]
        cache_key = "hybrid-ranking:v4:" + salted_hmac("hybrid-ranking", json.dumps([
            str(getattr(getattr(self.request, "user", None), "pk", "diagnostic")), str(self.generation.pk),
            self.generation.embedding_profile, self.generation.embedding_ready, query, lookup_kind, audience, intent,
            list(keywords), settings.AI_LAB_HYBRID_CANDIDATES], sort_keys=True)).hexdigest()
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
        elif self.generation.embedding_ready:
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="reference-vector") as pool:
                future = pool.submit(copy_context().run, self.semantic_ids, query, audience)
                lexical_ids, curated = self.lexical_ids(query, audience, intent, lookup_kind)
                try:
                    semantic, embedding_metadata = future.result()
                except ProviderError as exc:
                    degraded = exc.code  # Keyword evidence still requires all source/quality checks.
        else:
            lexical_ids, curated = self.lexical_ids(query, audience, intent, lookup_kind)
            degraded = "HYBRID_EMBEDDINGS_NOT_READY"
        if cached is None and degraded is None:
            try:
                cache.set(cache_key, {"rankings": [[str(item) for item in ranking] for ranking in [lexical_ids, semantic, curated]],
                    "degraded": degraded}, settings.AI_LAB_RETRIEVAL_CACHE_TTL_SECONDS)
            except Exception:
                pass
        scores = reciprocal_rank_fusion([lexical_ids, semantic, curated])
        context = query_context(query, lookup_kind=lookup_kind,
                                         audience=audience, intent=intent, keywords=keywords)
        candidates = list(SearchChunk.objects.filter(pk__in=list(scores), generation=self.generation))
        if lookup_kind == "drug" and intent in {"dose", "renal_dose"}:
            for neighbor, seed_id in self.dose_neighbors(candidates, audience):
                if neighbor.pk not in scores:
                    scores[neighbor.pk] = scores[seed_id] * .99
                    candidates.append(neighbor)
        concepts = concept_terms(query, intent)
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
            if audience == "patient" and row.source_kind == "patient":
                priority += .04
            priority += min(20, lexical.heading_score(row.heading, row.heading_path, context)) * .001
            if intent in {"dose", "renal_dose"}:
                priority += min(7,lexical.regimen_score(row.text,row.heading))*.001
            return -(scores[row.pk] + priority), str(row.pk)
        candidates.sort(key=rank)
        diverse, overflow, section_counts = [], [], {}
        for row in candidates:
            section = (row.source_id, tuple(row.heading_path) or (row.heading,))
            section_counts[section] = section_counts.get(section, 0) + 1
            (diverse if section_counts[section] <= 2 else overflow).append(row)
        candidates = diverse + overflow
        chosen, total_tokens = [], 0
        for row in candidates:
            if len(chosen) >= settings.AI_LAB_HYBRID_TOP_K:
                break
            if total_tokens + row.token_count > settings.AI_LAB_HYBRID_CONTEXT_TOKENS:
                continue
            try:
                require_feature(self.request, "uptodate", item=row.source_id, consume=False)
            except PlatformAPIError:
                continue
            chosen.append(row); total_tokens += row.token_count
        supplemented = 0
        if (settings.AI_LAB_HYBRID_REGIMEN_ENRICHMENT and lookup_kind == "topic"
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
        passages, focus = evidence.focus_passages(passages, question or query, query,
            lookup_kind=lookup_kind, audience=audience, intent=intent, keywords=keywords)
        from . import media
        media_count=0
        if media.requested(question or query):
            selected=media.search(self.generation,query,article_ids={p.article_id for p in passages},audience=audience,kinds=media.requested_kinds(question or query))
            allowed=[]
            for passage in selected:
                try:require_feature(self.request,"uptodate",item=passage.article_id,consume=False)
                except PlatformAPIError:continue
                allowed.append(passage)
            media_count=len(allowed)
            passages=[*allowed,*passages]
        self.consume_passages(passages)
        self.validate()
        return passages, {"engine":"hybrid" if semantic else "lexical", "lexical_candidates":len(lexical_ids),
            "semantic_candidates":len(semantic), "tagging_candidates":len(curated), "selected_chunks":len(chosen),
            "selected_passages":len(passages), "context_tokens":focus["selected_text_tokens"]+sum(
                token_count(p.text) for p in passages if p.media),
            "chunk_context_tokens":total_tokens,"evidence_focus":focus,
            "regimen_supplement_chunks":supplemented,"selected_media":media_count,
            "generation":str(self.generation.pk), "degraded":degraded, "embedding":embedding_metadata}

    def regimen_supplements(self, chunks, query, audience, intent):
        names = drug_name_catalog(self.generation.source_generation)
        mentioned, seen = [], set()
        for chunk in chunks:
            if chunk.source_kind == "drug":
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

    def passages(self, chunks, *, consume=True):
        wanted = {identifier: chunk for chunk in chunks for identifier in chunk.block_ids}
        rows = {row.pk: row for row in ReferenceParagraph.objects.filter(pk__in=list(wanted),
            article__generation_id=self.generation.source_generation).select_related("article", "section")}
        if len(rows) != len(wanted):
            raise ProviderError("REFERENCE_INDEX_STALE")
        labels={}
        for label in ReferenceParagraph.objects.filter(section_id__in={r.section_id for r in rows.values()},text__endswith=":") \
                .annotate(size=Length("text")).filter(size__lte=180).order_by("section_id","ordinal"):
            labels.setdefault(label.section_id,[]).append(label)
        result, seen = [], set()
        for chunk in chunks:
            for identifier in chunk.block_ids:
                if identifier in seen:
                    continue
                row = rows[identifier]
                article = row.article
                if article.source_id != chunk.source_id or article.content_hash != chunk.content_hash or row.retrieval_number is None:
                    raise ProviderError("REFERENCE_INDEX_STALE")
                result.append(Passage("P"+str(row.pk),article.source_id,article.title,row.section.heading,row.text,
                    {"screen":"uptodateArticle","params":{"id":article.source_id,"title":article.title,
                     "sectionId":row.section.source_id,"searchAnchor":row.source_anchor,"searchContentHash":article.content_hash}},
                    article.content_hash,heading_path=tuple(row.section.heading_path),context=tuple({
                        "quote":label.text,"source_anchor":label.source_anchor,"ordinal":label.ordinal}
                        for label in [label for label in labels.get(row.section_id,[]) if label.ordinal<row.ordinal][-4:]),
                    ordinal=row.ordinal))
                seen.add(identifier)
        if consume:
            self.consume_passages(result)
        return result
