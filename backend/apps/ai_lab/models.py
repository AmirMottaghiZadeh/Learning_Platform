"""Rebuildable reference data, separate from licensed source snapshots."""
import uuid

from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVector
from django.db import models


class ReferenceSource(models.Model):
    id = models.CharField(primary_key=True, max_length=64)
    backend = models.CharField(max_length=8)
    active_generation = models.ForeignKey("ReferenceGeneration", null=True, blank=True,
                                          on_delete=models.SET_NULL, related_name="+")


class ReferenceGeneration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(ReferenceSource, on_delete=models.CASCADE, related_name="generations")
    source_revision = models.CharField(max_length=64)
    snapshot_version = models.CharField(max_length=120)
    extraction_version = models.CharField(max_length=64)
    format_version = models.PositiveIntegerField()
    status = models.CharField(max_length=12, default="building")
    scope = models.CharField(max_length=8, default="full")
    article_ids = models.JSONField(default=list)
    expected_articles = models.PositiveIntegerField()
    built_articles = models.PositiveIntegerField(default=0)
    block_count = models.PositiveBigIntegerField(default=0)
    section_count = models.PositiveBigIntegerField(default=0)
    errors = models.JSONField(default=list)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)


class ReferenceArticle(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    generation = models.ForeignKey(ReferenceGeneration, on_delete=models.CASCADE, related_name="articles")
    source_id = models.CharField(max_length=32)
    title = models.TextField()
    source_version = models.CharField(max_length=120)
    content_hash = models.CharField(max_length=64)
    blob_hash = models.CharField(max_length=64)
    is_directory = models.BooleanField(default=False)
    related_topics = models.JSONField(default=list)
    raw_block_count = models.PositiveIntegerField()
    eligible_block_count = models.PositiveIntegerField()
    eligible_section_count = models.PositiveIntegerField()
    filter_limited = models.BooleanField(default=False)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["generation", "source_id"], name="ref_article_source_unique")]


class ReferenceSection(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    article = models.ForeignKey(ReferenceArticle, on_delete=models.CASCADE, related_name="sections")
    ordinal = models.PositiveIntegerField()
    retrieval_order = models.PositiveIntegerField(null=True, blank=True)
    source_id = models.CharField(max_length=160, blank=True)
    heading = models.TextField(blank=True)
    heading_path = models.JSONField(default=list)
    hierarchy_known = models.BooleanField(default=False)
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children")

    class Meta:
        constraints = [models.UniqueConstraint(fields=["article", "ordinal"], name="ref_section_order_unique")]


class ReferenceParagraph(models.Model):
    article = models.ForeignKey(ReferenceArticle, on_delete=models.CASCADE, related_name="paragraphs")
    section = models.ForeignKey(ReferenceSection, on_delete=models.CASCADE, related_name="paragraphs")
    ordinal = models.PositiveIntegerField()
    retrieval_number = models.PositiveIntegerField(null=True, blank=True)
    source_anchor = models.CharField(max_length=80)
    kind = models.CharField(max_length=12)
    text = models.TextField()
    table_headers = models.JSONField(default=list)
    table_context_status = models.CharField(max_length=24, blank=True)
    exclusion_reason = models.CharField(max_length=24, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["article", "source_anchor"], name="ref_paragraph_anchor_unique")]
        indexes = [models.Index(fields=["article", "ordinal"], name="ref_paragraph_order_idx")]
        indexes += [GinIndex(SearchVector("text", config="english"),
                            condition=models.Q(retrieval_number__isnull=False), name="ref_paragraph_fts_idx")]
