"""Resumable derived index. Construction never runs during a user question."""
from decimal import Decimal, InvalidOperation
import uuid

from django.conf import settings
from django.contrib.postgres.search import SearchVector
from django.db import connections, transaction
from django.db.models import Count, Max, Sum, TextField
from django.db.models.functions import Cast
from django.utils import timezone

from apps.ai_lab import reference_index
from apps.ai_lab.models import ReferenceArticle, ReferenceParagraph
from apps.ai_lab.provider import ProviderError
from apps.uptodate import services as utd
from .chunking import CHUNKER_VERSION, article_chunks
from .models import IndexedArticle, RetrievalGeneration, RetrievalHead, SearchAlias, SearchChunk, SearchConcept


def alias():
    return settings.AI_RETRIEVAL_DATABASE_ALIAS


def catalog(generation):
    if generation.catalog_ready:
        return
    source = utd._search_catalog(generation.source_version)
    directories = {a.source_id: [item["id"] for item in a.related_topics]
                   for a in ReferenceArticle.objects.filter(generation_id=generation.source_generation,
                       is_directory=True).only("source_id", "related_topics")}
    def topics(lists):
        return [",".join(dict.fromkeys(expanded for identifier in value.split(",") if identifier.strip()
                     for expanded in directories.get(identifier.strip(), [identifier.strip()]))) for value in lists]
    concepts = {key: SearchConcept(id=uuid.uuid5(generation.pk, "concept:" + key),
                generation=generation, source_id=key, topic_lists=topics(value))
                for key, value in source.topics.items()}
    rows = [SearchAlias(generation=generation, concept=concepts[key], alias=name, weight=weight)
            for name, (key, weight) in source.aliases.items() if key in concepts]
    with transaction.atomic(using=alias()):
        SearchAlias.objects.filter(generation=generation).delete()
        SearchConcept.objects.filter(generation=generation).delete()
        SearchConcept.objects.bulk_create(list(concepts.values()), batch_size=1000)
        SearchAlias.objects.bulk_create(rows, batch_size=1000)
        generation.catalog_ready = True
        generation.save(update_fields=["catalog_ready"])


def build(*, limit=None, identifiers=(), resume=None, progress=lambda _: None):
    stamp = reference_index.source_stamp()
    source_generation = reference_index.active_generation(stamp)
    if not source_generation:
        raise ProviderError("REFERENCE_INDEX_NOT_READY")
    lock = reference_index.acquire_build_lock("hybrid:" + stamp.identity)
    try:
        articles = ReferenceArticle.objects.filter(generation_id=source_generation, is_directory=False).order_by("source_id")
        if identifiers:
            articles = articles.filter(source_id__in=identifiers)
        if limit:
            articles = articles[:limit]
        ids = list(articles.values_list("source_id", flat=True))
        if not ids:
            raise ProviderError("NO_REFERENCE_ARTICLES")
        full = not limit and not identifiers
        if resume:
            generation = RetrievalGeneration.objects.get(pk=resume)
            if (generation.source_revision != stamp.revision or generation.source_generation != source_generation
                    or generation.chunker_version != CHUNKER_VERSION or generation.article_ids != ids
                    or generation.status not in {"building", "failed"}):
                raise ProviderError("HYBRID_RESUME_MISMATCH")
            generation.status, generation.errors = "building", []
            generation.save(update_fields=["status", "errors"])
        else:
            generation = RetrievalGeneration.objects.create(source_identity=stamp.identity,
                source_revision=stamp.revision, source_generation=source_generation,
                source_version=stamp.version, chunker_version=CHUNKER_VERSION,
                expected_articles=len(ids), article_ids=ids, scope="full" if full else "pilot")
        progress({"generation": str(generation.pk), "articles": len(ids), "scope": generation.scope})
        try:
            catalog(generation)
            done = set(IndexedArticle.objects.filter(generation=generation).values_list("source_id", flat=True))
            for article in articles.iterator(chunk_size=20):
                if article.source_id in done:
                    continue
                paragraphs = ReferenceParagraph.objects.filter(article=article).select_related("section").order_by("ordinal")
                rows = [SearchChunk(**data) for data in article_chunks(article, paragraphs.iterator(chunk_size=200), generation.pk)]
                with transaction.atomic(using=alias()):
                    SearchChunk.objects.bulk_create(rows, batch_size=200)
                    if connections[alias()].vendor == "postgresql":
                        SearchChunk.objects.filter(generation=generation, source_id=article.source_id).update(search_document=(
                            SearchVector("title", config="english", weight="A")
                            + SearchVector(Cast("heading_path", TextField()), config="english", weight="B")
                            + SearchVector("text", config="english", weight="C")))
                    IndexedArticle.objects.create(generation=generation, source_id=article.source_id,
                        content_hash=article.content_hash, chunk_count=len(rows))
                    generation.built_articles += 1
                    generation.chunk_count += len(rows)
                    generation.embedding_tokens += sum(row.token_count for row in rows)
                    generation.save(update_fields=["built_articles", "chunk_count", "embedding_tokens"])
                if generation.built_articles % 20 == 0:
                    progress({"built": generation.built_articles, "total": len(ids), "chunks": generation.chunk_count})
            if reference_index.source_stamp() != stamp or reference_index.active_generation(stamp) != source_generation:
                raise ProviderError("REFERENCE_INDEX_STALE")
            if generation.built_articles != len(ids) or IndexedArticle.objects.filter(generation=generation).count() != len(ids):
                raise ProviderError("HYBRID_INDEX_INCOMPLETE")
            generation.status, generation.finished_at = "ready", timezone.now()
            generation.save(update_fields=["status", "finished_at"])
            return generation
        except Exception as exc:
            generation.status = "failed"
            generation.errors = [{"code": getattr(exc, "code", "BUILD_FAILED"), "type": type(exc).__name__}]
            generation.save(update_fields=["status", "errors"])
            raise
    finally:
        reference_index.release_build_lock(lock)


def activate_generation(generation, *, require_embeddings=True):
    stamp = reference_index.source_stamp()
    if (generation.scope != "full" or generation.status != "ready" or not generation.catalog_ready
            or generation.source_identity != stamp.identity or generation.source_revision != stamp.revision
            or generation.source_generation != reference_index.active_generation(stamp)):
        raise ProviderError("HYBRID_INDEX_NOT_READY")
    if require_embeddings and not generation.embedding_ready:
        raise ProviderError("HYBRID_EMBEDDINGS_NOT_READY")
    with transaction.atomic(using=alias()):
        head, _ = RetrievalHead.objects.select_for_update().get_or_create(source_identity=stamp.identity)
        head.active = generation
        head.save(update_fields=["active"])


def clone_generation(source, *, identifiers=(), progress=lambda _:None):
    """Copy immutable prepared text/FTS/catalog into an independent vector generation.

    Existing embeddings, billing reservations and uncertain requests are never
    re-labelled as another model. No source parsing or paid inference occurs.
    """
    stamp = reference_index.source_stamp()
    if (source.status != "ready" or not source.catalog_ready or source.source_identity != stamp.identity
            or source.source_revision != stamp.revision
            or source.source_generation != reference_index.active_generation(stamp)):
        raise ProviderError("REFERENCE_INDEX_STALE")
    if connections[alias()].vendor != "postgresql":
        raise ProviderError("HYBRID_REQUIRES_POSTGRESQL")
    selected = list(IndexedArticle.objects.filter(generation=source,**({"source_id__in":identifiers} if identifiers else {}))
                    .order_by("source_id").values_list("source_id",flat=True))
    if not selected or identifiers and set(selected)!=set(identifiers):
        raise ProviderError("NO_REFERENCE_ARTICLES")
    generation = RetrievalGeneration.objects.create(source_identity=source.source_identity,
        source_revision=source.source_revision,source_generation=source.source_generation,
        source_version=source.source_version,chunker_version=source.chunker_version,
        scope="pilot" if identifiers else source.scope,expected_articles=len(selected),article_ids=selected)
    progress({"generation":str(generation.pk),"cloned_from":str(source.pk),"scope":generation.scope})
    try:
        with transaction.atomic(using=alias()):
            with connections[alias()].cursor() as cursor:
                cursor.execute("INSERT INTO ai_retrieval_searchchunk (id,generation_id,source_id,content_hash,ordinal,title,heading,heading_path,audience,source_kind,text,block_ids,input_hash,token_count,search_document) "
                    "SELECT md5(%s||':chunk:'||id::text)::uuid,%s,source_id,content_hash,ordinal,title,heading,heading_path,audience,source_kind,text,block_ids,input_hash,token_count,search_document "
                    "FROM ai_retrieval_searchchunk WHERE generation_id=%s AND source_id=ANY(%s)",
                    [str(generation.pk),generation.pk,source.pk,selected])
                cursor.execute("INSERT INTO ai_retrieval_indexedarticle (generation_id,source_id,content_hash,chunk_count,media_built) "
                    "SELECT %s,source_id,content_hash,chunk_count,media_built FROM ai_retrieval_indexedarticle WHERE generation_id=%s AND source_id=ANY(%s)",
                    [generation.pk,source.pk,selected])
                cursor.execute("INSERT INTO ai_retrieval_referencemedia (generation_id,source_id,content_hash,media_key,kind,article_title,title,caption,search_text,evidence_text,audience,descriptor) "
                    "SELECT %s,source_id,content_hash,media_key,kind,article_title,title,caption,search_text,evidence_text,audience,descriptor "
                    "FROM ai_retrieval_referencemedia WHERE generation_id=%s AND source_id=ANY(%s)",
                    [generation.pk,source.pk,selected])
                cursor.execute("INSERT INTO ai_retrieval_searchconcept (id,generation_id,source_id,topic_lists) "
                    "SELECT md5(%s||':concept:'||id::text)::uuid,%s,source_id,topic_lists FROM ai_retrieval_searchconcept WHERE generation_id=%s",
                    [str(generation.pk),generation.pk,source.pk])
                cursor.execute("INSERT INTO ai_retrieval_searchalias (generation_id,concept_id,alias,weight) "
                    "SELECT %s,md5(%s||':concept:'||concept_id::text)::uuid,alias,weight FROM ai_retrieval_searchalias WHERE generation_id=%s",
                    [generation.pk,str(generation.pk),source.pk])
            counts=SearchChunk.objects.filter(generation=generation).aggregate(chunks=Count("pk"),tokens=Sum("token_count"))
            generation.built_articles=len(selected)
            generation.chunk_count=counts["chunks"]
            generation.embedding_tokens=counts["tokens"] or 0
            generation.catalog_ready=True
            generation.status="ready"
            generation.finished_at=timezone.now()
            if reference_index.source_stamp()!=stamp or reference_index.active_generation(stamp)!=source.source_generation:
                raise ProviderError("REFERENCE_INDEX_STALE")
            generation.save()
        return generation
    except Exception as exc:
        generation.status="failed"
        generation.errors=[{"code":getattr(exc,"code","CLONE_FAILED"),"type":type(exc).__name__}]
        generation.save(update_fields=["status","errors"])
        raise


def manifest(generation):
    distinct = SearchChunk.objects.filter(generation=generation).values("input_hash").annotate(tokens=Max("token_count"))
    result = distinct.aggregate(unique_inputs=Count("input_hash"), unique_tokens=Sum("tokens"))
    result.update(generation=str(generation.pk), scope=generation.scope, status=generation.status,
                  articles=generation.built_articles, chunks=generation.chunk_count,
                  tokens_with_repeats=generation.embedding_tokens,
                  oversized_inputs=SearchChunk.objects.filter(generation=generation, token_count__gt=8000).count())
    rate = settings.AI_LAB_EMBEDDING_PRICE_PER_MILLION
    if rate:
        try:
            value = Decimal(rate)
            if not value.is_finite() or value < 0:
                raise InvalidOperation
            result["estimated_embedding_cost"] = str(Decimal(result["unique_tokens"] or 0) / 1_000_000 * value)
            result["rate_per_million"] = str(value)
        except InvalidOperation:
            raise ProviderError("INVALID_EMBEDDING_PRICE") from None
    return result
