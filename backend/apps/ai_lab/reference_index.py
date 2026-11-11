"""Versioned prepared sources. Runtime reads never populate or alter the index."""
from dataclasses import dataclass
from hashlib import sha256
import json
from pathlib import Path
import threading

import dj_database_url
import pymysql
from django.conf import settings
from django.db import DatabaseError, connection, transaction
from django.utils import timezone
from django.views.decorators.debug import sensitive_variables

from apps.uptodate import services as utd
from apps.uptodate.search_extraction import EXTRACTION_VERSION
from .document import FORMAT_VERSION
from .models import ReferenceArticle, ReferenceGeneration, ReferenceParagraph, ReferenceSection, ReferenceSource
from .provider import ProviderError

_source_local = threading.local()


@sensitive_variables()
def mysql_source_connection():
    """Independent, autocommit source reads: no shared cursor or pinned snapshot."""
    configuration = settings.UPTODATE_MYSQL_URL
    source_connection = getattr(_source_local, "connection", None)
    if source_connection is not None and getattr(_source_local, "configuration", None) == configuration:
        try:
            source_connection.ping(reconnect=True)
            return source_connection
        except (pymysql.MySQLError, OSError):
            pass
    if source_connection is not None and source_connection.open:
        source_connection.close()
    source_connection = pymysql.connect(**utd.mysql_config(), autocommit=True, read_timeout=10, write_timeout=10)
    _source_local.connection, _source_local.configuration = source_connection, configuration
    return source_connection


def _hash(value):
    return sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def acquire_build_lock(identity):
    if connection.vendor != "postgresql":
        return None
    key = int(_hash(["ai_lab_reference_build", identity])[:15], 16)
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [key])
        if not cursor.fetchone()[0]:
            raise ProviderError("REFERENCE_INDEX_BUILD_BUSY")
    return key


def release_build_lock(key):
    if key is not None:
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT pg_advisory_unlock(%s)", [key])
        except DatabaseError:
            pass


@dataclass(frozen=True)
class SourceStamp:
    identity: str
    revision: str
    version: str
    backend: str


@sensitive_variables()
def source_stamp():
    """Read source revision independently of the normal search's process cache."""
    if utd._using_mysql():
        parsed = dj_database_url.parse(settings.UPTODATE_MYSQL_URL)
        identity = _hash(["mysql", parsed["HOST"], parsed["PORT"] or 3306, parsed["NAME"]])
        with mysql_source_connection().cursor() as cursor:
            cursor.execute("SELECT value FROM meta WHERE `key` = 'version'")
            row = cursor.fetchone()
        if not row or row["value"] is None:
            raise ProviderError("SOURCE_REVISION_UNAVAILABLE")
        version = str(row["value"])
        return SourceStamp(identity, _hash([version]), version, "mysql")
    directory = Path(settings.UPTODATE_DB_DIR).resolve()
    stamps = {}
    for name in ["content.db", "fts.db", "info.json"]:
        try:
            info = (directory / name).stat()
        except FileNotFoundError:
            if name != "info.json":
                raise
            # The canonical reader accepts snapshots without optional metadata.
            # Its absence is part of the revision, so adding/removing metadata
            # invalidates a generation without inventing a source version.
            stamps[name] = None
            continue
        stamps[name] = [info.st_size, info.st_mtime_ns, info.st_ino]
    metadata = json.loads((directory / "info.json").read_text()) if stamps["info.json"] is not None else {}
    if not isinstance(metadata, dict):
        raise ProviderError("SOURCE_REVISION_UNAVAILABLE")
    version = str(metadata.get("version", ""))
    return SourceStamp(_hash(["sqlite", str(directory)]), _hash([version, stamps]), version, "sqlite")


def source_article_ids():
    if utd._using_mysql():
        with mysql_source_connection().cursor() as cursor:
            cursor.execute("SELECT DISTINCT contentId FROM fts WHERE type = %s ORDER BY contentId", (utd.TOPIC_TYPE,))
            return [str(row["contentId"]) for row in cursor.fetchall()]
    rows = utd._sqlite_conn("fts").execute(
        "SELECT DISTINCT contentId FROM fts WHERE type = ? ORDER BY contentId", (utd.TOPIC_TYPE,))
    return [str(row[0]) for row in rows]


def source_blobs(identifiers, version):
    if utd._using_mysql():
        marks = ",".join(["%s"] * len(identifiers))
        with mysql_source_connection().cursor() as cursor:
            cursor.execute(f"SELECT id, gzip, version FROM content WHERE id IN ({marks})", identifiers)
            rows = cursor.fetchall()
    else:
        marks = ",".join(["?"] * len(identifiers))
        rows = utd._sqlite_conn("content").execute(
            f"SELECT id, gzip, version FROM content WHERE id IN ({marks})", identifiers).fetchall()
    return [(str(row["id"]), bytes(row["gzip"]), str(row["version"] or version)) for row in rows]


def begin_generation(stamp, identifiers, *, full=True, resume=None):
    source, _ = ReferenceSource.objects.get_or_create(pk=stamp.identity, defaults={"backend": stamp.backend})
    if resume:
        generation = ReferenceGeneration.objects.get(pk=resume, source=source)
        if (generation.status not in {"building", "failed"} or generation.source_revision != stamp.revision
                or generation.extraction_version != EXTRACTION_VERSION or generation.format_version != FORMAT_VERSION
                or generation.article_ids != identifiers):
            raise ProviderError("INDEX_RESUME_MISMATCH")
        generation.status, generation.errors, generation.finished_at = "building", [], None
        generation.save(update_fields=["status", "errors", "finished_at"])
        return generation
    return ReferenceGeneration.objects.create(source=source, source_revision=stamp.revision,
        snapshot_version=stamp.version, extraction_version=EXTRACTION_VERSION, format_version=FORMAT_VERSION,
        article_ids=identifiers, expected_articles=len(identifiers), scope="full" if full else "partial")


@transaction.atomic
def persist_documents(generation, documents):
    articles, sections, paragraphs = [], [], []
    for document in documents:
        article = ReferenceArticle(generation=generation, **{name: document[name] for name in [
            "source_id", "title", "source_version", "content_hash", "blob_hash", "is_directory", "related_topics",
            "raw_block_count", "eligible_block_count", "eligible_section_count", "filter_limited"]})
        articles.append(article)
        section_map = {}
        for item in document["sections"]:
            section = ReferenceSection(article=article, **{name: item[name] for name in [
                "ordinal", "retrieval_order", "source_id", "heading", "heading_path", "hierarchy_known"]})
            section_map[item["ordinal"]] = section
            sections.append(section)
        for item in document["sections"]:
            if item["parent_ordinal"] is not None:
                section_map[item["ordinal"]].parent = section_map[item["parent_ordinal"]]
        for item in document["blocks"]:
            paragraphs.append(ReferenceParagraph(article=article, section=section_map[item["section_ordinal"]],
                **{name: item[name] for name in ["ordinal", "retrieval_number", "source_anchor", "kind", "text",
                                               "table_headers", "table_context_status", "exclusion_reason"]}))
    ReferenceArticle.objects.bulk_create(articles, batch_size=100)
    ReferenceSection.objects.bulk_create(sections, batch_size=500)
    ReferenceParagraph.objects.bulk_create(paragraphs, batch_size=1000)
    generation.built_articles += len(articles)
    generation.block_count += len(paragraphs)
    generation.section_count += len(sections)
    generation.save(update_fields=["built_articles", "block_count", "section_count"])


@transaction.atomic
def finish_generation(generation, stamp, *, activate=True):
    source = ReferenceSource.objects.select_for_update().get(pk=stamp.identity)
    generation.refresh_from_db()
    if generation.errors or generation.built_articles != generation.expected_articles:
        raise ProviderError("INDEX_BUILD_INCOMPLETE")
    if generation.articles.count() != generation.expected_articles:
        raise ProviderError("INDEX_BUILD_INCOMPLETE")
    if source_stamp() != stamp:
        raise ProviderError("SOURCE_CHANGED_DURING_INDEX_BUILD")
    if activate and generation.scope != "full":
        raise ProviderError("PARTIAL_INDEX_CANNOT_ACTIVATE")
    generation.status, generation.finished_at = "ready", timezone.now()
    generation.save(update_fields=["status", "finished_at"])
    if activate:
        source.active_generation = generation
        source.save(update_fields=["active_generation"])


def active_generation(stamp):
    row = ReferenceSource.objects.filter(pk=stamp.identity).values(
        "active_generation_id", "active_generation__status", "active_generation__source_revision",
        "active_generation__format_version", "active_generation__extraction_version", "active_generation__scope").first()
    if (not row or row["active_generation__status"] != "ready"
            or row["active_generation__source_revision"] != stamp.revision
            or row["active_generation__format_version"] != FORMAT_VERSION
            or row["active_generation__scope"] != "full"
            or row["active_generation__extraction_version"] != EXTRACTION_VERSION):
        return None
    return row["active_generation_id"]


def read_sections(identifier, section_offset, passage_offset, audit, *, context=None):
    """Return (sections, eligible_count), or None for a permitted legacy fallback."""
    mode = settings.AI_LAB_PREPROCESSED_MODE
    if mode == "off":
        return None
    if mode not in {"prefer", "require"}:
        raise ProviderError("INVALID_INDEX_MODE")
    try:
        return _read_sections(identifier, section_offset, passage_offset, audit, mode, context=context)
    except (DatabaseError, pymysql.MySQLError, OSError, ValueError):
        if mode == "require":
            raise ProviderError("REFERENCE_INDEX_UNAVAILABLE") from None
        audit["preprocessing_fallbacks"] = audit.get("preprocessing_fallbacks", 0) + 1
        return None
    except ProviderError as exc:
        if mode != "prefer" or exc.code != "SOURCE_REVISION_UNAVAILABLE":
            raise
        audit["preprocessing_fallbacks"] = audit.get("preprocessing_fallbacks", 0) + 1
        return None


def _read_sections(identifier, section_offset, passage_offset, audit, mode, *, context=None):
    from .retrieval import MAX_SECTIONS_PER_ARTICLE, Passage

    stamp = source_stamp()
    generation_id = active_generation(stamp)
    article = ReferenceArticle.objects.filter(generation_id=generation_id, source_id=identifier).first() if generation_id else None
    if article is not None and stamp.backend == "mysql":
        # Row versions in older mirrors can be reused. Verify the compressed
        # source on its server, without transferring or parsing article HTML.
        with mysql_source_connection().cursor() as cursor:
            cursor.execute("SELECT SHA2(gzip, 256) AS blob_hash FROM content WHERE id = %s", (identifier,))
            row = cursor.fetchone()
        if not row or row["blob_hash"] != article.blob_hash:
            if mode == "require":
                raise ProviderError("REFERENCE_INDEX_STALE")
            article = None
    if article is None:
        if mode == "require":
            raise ProviderError("REFERENCE_INDEX_NOT_READY")
        audit["preprocessing_fallbacks"] = audit.get("preprocessing_fallbacks", 0) + 1
        return None
    audit["preprocessed_articles"] = audit.get("preprocessed_articles", 0) + 1
    audit["preprocessing_generation"] = str(generation_id)
    if article.is_directory:
        audit["related_topics"] = article.related_topics
        return [], 0
    if context is not None:
        from .lexical import prepared_sections
        from .telemetry import operation
        with operation("lexical_retrieval"):
            return prepared_sections(article, context, section_offset, passage_offset, audit)
    groups = list(article.sections.filter(retrieval_order__isnull=False).order_by("retrieval_order")[:MAX_SECTIONS_PER_ARTICLE])
    grouped = {group.pk: [] for group in groups}
    for block in article.paragraphs.filter(section_id__in=grouped, retrieval_number__isnull=False).order_by("ordinal").values(
            "section_id", "retrieval_number", "text", "source_anchor"):
        grouped[block["section_id"]].append(block)
    result = []
    for group in groups:
        passages = [Passage(id=f"P{passage_offset + block['retrieval_number']}", article_id=identifier,
            title=article.title, section=group.heading, text=block["text"], content_hash=article.content_hash,
            target={"screen": "uptodateArticle", "params": {"id": identifier, "title": article.title,
                "sectionId": group.source_id, "searchAnchor": block["source_anchor"],
                "searchContentHash": article.content_hash}}) for block in grouped[group.pk]]
        result.append({"id": f"T{section_offset + len(result) + 1}", "article_id": identifier,
                       "title": article.title, "heading": group.heading,
                       "preview": " ".join(p.text for p in passages[:2])[:280], "passages": passages})
    if article.filter_limited or article.eligible_section_count > MAX_SECTIONS_PER_ARTICLE:
        audit["limited"] = True
    return result, article.eligible_block_count
