"""Private exact-question cache. Every hit rechecks source evidence and access."""
from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
import json
from pathlib import Path
import re
import unicodedata

from django.conf import settings
from django.core.cache import caches
from django.utils.crypto import constant_time_compare, salted_hmac

from apps.billing.enforcement import require_feature
from . import lexical, reference_index, selection, telemetry
from .models import ReferenceArticle, ReferenceParagraph
from .provider import check_deadline

CACHE_VERSION = 1
MAX_PAYLOAD_BYTES = 512000


@lru_cache(maxsize=1)
def code_signature():
    directory = Path(__file__).parent
    names = ["services.py", "provider.py", "http_transport.py", "retrieval.py", "lexical.py", "selection.py",
             "reference_index.py", "document.py", "response_cache.py", "outline.py", "hybrid_agent.py", "question_profile.py", "streaming.py", "transport_pool.py"]
    retrieval = directory.parent / "ai_retrieval"
    return sha256(b"".join((directory / name).read_bytes() for name in names) + b"".join(
        (retrieval / name).read_bytes() for name in ["retrieval.py", "evidence.py", "media.py", "embeddings.py", "local_embeddings.py", "chunking.py", "vectors.py", "source_links.py", "source_context.py"])
        +(directory.parent/"uptodate"/"media.py").read_bytes()).hexdigest()


def state(value):
    trace = telemetry.current_trace()
    if trace is not None:
        trace.response_cache = value


@dataclass(frozen=True)
class Lookup:
    key: str
    stamp: object
    generation: object


def prepare(question, alias, sources, history, request):
    if not settings.AI_LAB_RESPONSE_CACHE_ENABLED:
        state("disabled")
        return None
    user = getattr(request, "user", None)
    if not user or not getattr(user, "is_authenticated", False) or getattr(user, "pk", None) is None:
        state("bypass")
        return None
    # Permission failures are never swallowed as cache/backend failures.
    require_feature(request, "uptodate")
    try:
        check_deadline()
        stamp = reference_index.source_stamp()
        generation = reference_index.active_generation(stamp)
        if generation is None:
            state("bypass")
            return None
        effort = settings.AI_LAB_REASONING_EFFORT
        if effort is None:
            effort = settings.AI_LAB_LUNA_REASONING_EFFORT
        inputs = {"v": CACHE_VERSION, "user": str(user.pk), "question": unicodedata.normalize("NFC", question.strip()),
            "history": [unicodedata.normalize("NFC", item.strip()) for item in history], "alias": alias, "sources": sources,
            "model": settings.AI_LAB_MODEL, "base_url": settings.AI_LAB_BASE_URL.strip().rstrip("/"),
            "effort": effort.strip().lower(), "source": stamp.identity, "revision": stamp.revision,
            "generation": str(generation), "code": code_signature(), "lexical": settings.AI_LAB_LEXICAL_ENABLED,
            "preprocessed": settings.AI_LAB_PREPROCESSED_MODE, "selection": selection.enabled(),
            "lexical_version": lexical.LEXICAL_VERSION, "selection_version": selection.SELECTION_VERSION}
        inputs["engine"] = settings.AI_LAB_SEARCH_ENGINE
        if settings.AI_LAB_SEARCH_ENGINE == "hybrid":
            from apps.ai_retrieval.retrieval import HybridRetriever
            from apps.ai_retrieval.embeddings import profile
            hybrid = HybridRetriever(request)
            inputs.update(hybrid_generation=str(hybrid.generation.pk), embedding_profile=profile(),
                semantic_ready=hybrid.generation.embedding_ready,
                top_k=settings.AI_LAB_HYBRID_TOP_K, candidates=settings.AI_LAB_HYBRID_CANDIDATES,
                context_tokens=settings.AI_LAB_HYBRID_CONTEXT_TOKENS,
                search_rounds=settings.AI_LAB_HYBRID_MAX_SEARCH_ROUNDS)
            inputs["regimen_enrichment"] = settings.AI_LAB_HYBRID_REGIMEN_ENRICHMENT
            inputs["evidence_focus"] = settings.AI_LAB_HYBRID_EVIDENCE_FOCUS
            inputs["evidence_max_passages"] = settings.AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES
            inputs["source_context"] = {key:getattr(settings,key) for key in [
                "AI_LAB_SOURCE_CONTEXT_ENABLED","AI_LAB_SOURCE_CONTEXT_START_ARTICLES",
                "AI_LAB_SOURCE_CONTEXT_NEIGHBORS","AI_LAB_SOURCE_CONTEXT_LINKED_ARTICLES",
                "AI_LAB_SOURCE_CONTEXT_MAX_PASSAGES"]}
        digest = salted_hmac("ai-lab-private-answer", json.dumps(inputs, ensure_ascii=False, sort_keys=True), algorithm="sha256").hexdigest()
        state("miss")
        return Lookup(f"answer:v{CACHE_VERSION}:{digest}", stamp, generation)
    except Exception:
        check_deadline()
        state("unavailable")
        return None


def complete(result):
    if not isinstance(result, dict) or result.get("warnings"):
        return False
    parts = result.get("parts")
    return (isinstance(parts, list) and 1 <= len(parts) <= 3 and all(isinstance(part, dict)
        and part.get("status") == "answered" and isinstance(part.get("items"), list)
        and 1 <= len(part["items"]) <= 18 for part in parts))


def signature(key, result):
    raw = json.dumps(result, ensure_ascii=False, sort_keys=True)
    if len(raw.encode()) > MAX_PAYLOAD_BYTES:
        raise ValueError("Cache payload too large")
    return salted_hmac("ai-lab-answer-value", key + raw, algorithm="sha256").hexdigest()


def validate(result, lookup):
    if not complete(result):
        return None
    citations = [item for part in result["parts"] for item in part["items"]]
    for part in result["parts"]:
        if (not isinstance(part.get("question_fa"), str) or not isinstance(part.get("queries"), list)
                or not part["queries"] or any(not isinstance(query, str) for query in part["queries"])):
            return None
    identifiers, anchors = set(), set()
    for item in citations:
        if not isinstance(item, dict) or item.get("source") != "uptodate":
            return None
        target, summary = item.get("target", {}), item.get("summary_fa")
        if (not isinstance(target, dict) or target.get("screen") != "uptodateArticle"
                or not isinstance(target.get("params"), dict) or not isinstance(summary, str)
                or not 8 <= len(summary) <= 4000 or not re.search(r"[\u0600-\u06ff]", summary)):
            return None
        params = target["params"]
        identifier, anchor = params.get("id"), params.get("searchAnchor")
        if not isinstance(identifier, str) or not 1 <= len(identifier) <= 32 or not isinstance(anchor, str) or not 1 <= len(anchor) <= 80:
            return None
        identifiers.add(identifier)
        anchors.add(anchor)
        context=item.get("context",[])
        if not isinstance(context,list) or len(context)>4:
            return None
        for label in context:
            if (not isinstance(label,dict) or not isinstance(label.get("source_anchor"),str)
                    or not 1<=len(label["source_anchor"])<=80 or not isinstance(label.get("quote"),str)
                    or not 1<=len(label["quote"])<=180 or type(label.get("ordinal")) is not int):
                return None
            anchors.add(label["source_anchor"])
    if any(len({item.get("source_id") for item in part["items"]}) != len(part["items"]) for part in result["parts"]):
        return None
    articles = {article.source_id: article for article in ReferenceArticle.objects.filter(
        generation_id=lookup.generation, source_id__in=identifiers)}
    if len(articles) != len(identifiers):
        return None
    if lookup.stamp.backend == "mysql":
        marks = ",".join(["%s"] * len(identifiers))
        with reference_index.mysql_source_connection().cursor() as cursor:
            cursor.execute(f"SELECT id, SHA2(gzip, 256) AS blob_hash FROM content WHERE id IN ({marks})", list(identifiers))
            hashes = {str(row["id"]): row["blob_hash"] for row in cursor.fetchall()}
        if any(hashes.get(identifier) != article.blob_hash for identifier, article in articles.items()):
            return None
    blocks = {(str(block.article_id), block.source_anchor): block for block in ReferenceParagraph.objects.filter(
        article_id__in=[article.pk for article in articles.values()], source_anchor__in=anchors).select_related("section")}
    for item in citations:
        params = item["target"]["params"]
        article = articles[params["id"]]
        block = blocks.get((str(article.pk), params["searchAnchor"]))
        if (block is None or block.retrieval_number is None or item.get("quote") != block.text or item.get("content_hash") != article.content_hash
                or params.get("searchContentHash") != article.content_hash or params.get("sectionId") != block.section.source_id
                or item.get("title") != article.title or item.get("section") != block.section.heading):
            return None
        if "section_path" in item and item["section_path"] != block.section.heading_path:
            return None
        previous=-1
        for label in item.get("context",[]):
            original=blocks.get((str(article.pk),label["source_anchor"]))
            if (original is None or original.section_id!=block.section_id or original.text!=label["quote"]
                    or original.ordinal!=label["ordinal"] or not previous<original.ordinal<block.ordinal):
                return None
            previous=original.ordinal
    if reference_index.source_stamp() != lookup.stamp or reference_index.active_generation(lookup.stamp) != lookup.generation:
        return None
    check_deadline()
    return sorted(identifiers)


def load(lookup, request):
    if lookup is None:
        return None
    try:
        record = caches["ai_lab"].get(lookup.key)
        if record is None:
            return None
        if not isinstance(record, dict) or record.get("schema") != CACHE_VERSION:
            state("stale")
            return None
        if not constant_time_compare(record.get("signature", ""), signature(lookup.key, record.get("result"))):
            state("stale")
            caches["ai_lab"].delete(lookup.key)
            return None
        result = deepcopy(record.get("result"))
        with telemetry.operation("cache_validation"):
            identifiers = validate(result, lookup)
        if not identifiers:
            state("stale")
            caches["ai_lab"].delete(lookup.key)
            return None
    except Exception:
        check_deadline()
        state("unavailable")
        return None
    # Apply current entitlements/quota before any cached titles or text escape.
    for identifier in identifiers:
        require_feature(request, "uptodate", item=identifier, consume=True)
    check_deadline()
    state("hit")
    result.update(stages=[])
    for part in result["parts"]:
        identifiers = list(dict.fromkeys(item["target"]["params"]["id"] for item in part["items"]))
        part["retrieval"] = {"cache_hit": True, "search_engine": "verified_response_cache", "reviewed_articles": 0,
            "reviewed_passages": 0, "selected_articles": len(identifiers),
            "early_stopped": True, "stop_reason": "validated_cache_hit", "limited": False}
    return result


def store(lookup, result):
    if lookup is None or not complete(result):
        return
    remaining = check_deadline()
    if remaining is not None and remaining < 1:
        return
    try:
        if not validate(result, lookup):
            return
        stored = {name: deepcopy(value) for name, value in result.items() if name not in {"metrics", "elapsed_ms", "stages"}}
        raw = json.dumps(stored, ensure_ascii=False)
        if len(raw.encode()) > MAX_PAYLOAD_BYTES or re.search(r"sk-[A-Za-z0-9_-]{16,}", raw):
            return
        caches["ai_lab"].set(lookup.key, {"schema": CACHE_VERSION, "result": stored,
            "signature": signature(lookup.key, stored)}, settings.AI_LAB_RESPONSE_CACHE_TTL_SECONDS)
    except Exception:
        check_deadline()


def replay(result, progress, publish, observe):
    progress("retrieving")
    for number, part in enumerate(result["parts"]):
        check_deadline()
        def event(value):
            observe({"part_index": number, "question_fa": part["question_fa"], **value})
        items = part["items"]
        articles = list({item["target"]["params"]["id"]: {"id": item["target"]["params"]["id"], "title": item["title"]} for item in items}.values())
        event({"type": "question"})
        event({"type": "titles", "query": part["queries"][0], "articles": articles})
        for article in articles:
            article_id = article["id"]
            current = [item for item in items if item["target"]["params"]["id"] == article_id]
            event({"type": "article", "article_id": article_id, "title": article["title"]})
            headings = list(dict.fromkeys(item["section"] for item in current))
            event({"type": "sections", "article_id": article_id, "sections": [
                {"id": f"T{index + 1}", "heading": heading} for index, heading in enumerate(headings)], "paragraph_count": len(current)})
            publish({"part_index": number, "question_fa": part["question_fa"], "article_id": article_id, "citations": current})
            event({"type": "article_done", "article_id": article_id, "outcome": "answered"})
