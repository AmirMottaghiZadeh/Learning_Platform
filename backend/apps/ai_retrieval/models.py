"""Rebuildable chunk/catalog data; no cross-database foreign keys to source tables."""
import uuid
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField, SearchVector
from django.db import models


class RetrievalGeneration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source_identity = models.CharField(max_length=64)
    source_revision = models.CharField(max_length=64)
    source_generation = models.UUIDField()
    source_version = models.CharField(max_length=120, blank=True)
    chunker_version = models.CharField(max_length=64)
    scope = models.CharField(max_length=8, default="full")
    status = models.CharField(max_length=16, default="building")
    expected_articles = models.PositiveIntegerField()
    article_ids = models.JSONField(default=list)
    built_articles = models.PositiveIntegerField(default=0)
    chunk_count = models.PositiveBigIntegerField(default=0)
    embedding_tokens = models.PositiveBigIntegerField(default=0)
    catalog_ready = models.BooleanField(default=False)
    embedding_profile = models.JSONField(default=dict)
    embedding_ready = models.BooleanField(default=False)
    embedding_tokens_reserved = models.PositiveBigIntegerField(default=0)
    embedding_requests_used = models.PositiveIntegerField(default=0)
    pending_embedding_inputs = models.JSONField(default=list)
    errors = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)


class RetrievalHead(models.Model):
    source_identity = models.CharField(primary_key=True, max_length=64)
    active = models.ForeignKey(RetrievalGeneration, null=True, blank=True, on_delete=models.SET_NULL)


class IndexedArticle(models.Model):
    generation = models.ForeignKey(RetrievalGeneration, on_delete=models.CASCADE)
    source_id = models.CharField(max_length=32)
    content_hash = models.CharField(max_length=64)
    chunk_count = models.PositiveIntegerField()
    media_built = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["generation", "source_id"], name="hybrid_article_once")]


class SearchChunk(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    generation = models.ForeignKey(RetrievalGeneration, on_delete=models.CASCADE, related_name="chunks")
    source_id = models.CharField(max_length=32)
    content_hash = models.CharField(max_length=64)
    ordinal = models.PositiveIntegerField()
    title = models.TextField()
    heading = models.TextField(blank=True)
    heading_path = models.JSONField(default=list)
    audience = models.CharField(max_length=12, default="general")
    source_kind = models.CharField(max_length=12, default="topic")
    text = models.TextField()
    block_ids = models.JSONField(default=list)
    input_hash = models.CharField(max_length=64, db_index=True)
    token_count = models.PositiveIntegerField()
    search_document = SearchVectorField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["generation", "source_id", "ordinal"], name="hybrid_chunk_order_unique")]
        indexes = [models.Index(fields=["generation", "source_id"], name="hybrid_chunk_article_idx"),
                   GinIndex(fields=["search_document"], name="hybrid_chunk_fts_idx")]

    @property
    def embedding_input(self):
        return f"{self.title}\n{' > '.join(self.heading_path) or self.heading}\n{self.text}"


class SearchConcept(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    generation = models.ForeignKey(RetrievalGeneration, on_delete=models.CASCADE)
    source_id = models.CharField(max_length=64)
    topic_lists = models.JSONField(default=list)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["generation", "source_id"], name="hybrid_concept_unique")]


class SearchAlias(models.Model):
    generation = models.ForeignKey(RetrievalGeneration, on_delete=models.CASCADE)
    concept = models.ForeignKey(SearchConcept, on_delete=models.CASCADE)
    alias = models.CharField(max_length=1000)
    weight = models.IntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["generation", "alias"], name="hybrid_alias_unique")]


class ReferenceMedia(models.Model):
    generation = models.ForeignKey(RetrievalGeneration,on_delete=models.CASCADE,related_name="media")
    source_id = models.CharField(max_length=32)
    content_hash = models.CharField(max_length=64)
    media_key = models.CharField(max_length=100)
    kind = models.CharField(max_length=8)
    article_title = models.TextField()
    title = models.TextField()
    caption = models.TextField(blank=True)
    search_text = models.TextField()
    evidence_text = models.TextField()
    audience = models.CharField(max_length=12,default="general")
    descriptor = models.JSONField(default=dict)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["generation","source_id","media_key"],name="hybrid_media_once")]
        indexes = [models.Index(fields=["generation","source_id"],name="hybrid_media_article_idx"),
            GinIndex(SearchVector("search_text",config="english"),name="hybrid_media_fts_idx")]
