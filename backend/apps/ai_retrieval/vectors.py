"""Optional native pgvector storage. Web requests never install extensions or DDL."""
import json
import re
import uuid
from django.db import connections, transaction
from apps.ai_lab.provider import ProviderError
from . import embeddings, indexing

TABLE = "ai_retrieval_chunk_vector"


def available():
    connection = connections[indexing.alias()]
    if connection.vendor != "postgresql":
        return False
    with connection.cursor() as cursor:
        cursor.execute("SELECT EXISTS(SELECT 1 FROM pg_extension WHERE extname='vector'), to_regclass(%s)", [TABLE])
        extension, table = cursor.fetchone()
    return bool(extension and table)


def ensure_schema():
    connection = connections[indexing.alias()]
    if connection.vendor != "postgresql":
        raise ProviderError("VECTOR_REQUIRES_POSTGRESQL")
    with connection.cursor() as cursor:
        cursor.execute("SELECT installed_version FROM pg_available_extensions WHERE name='vector'")
        row = cursor.fetchone()
        if row is None:
            raise ProviderError("VECTOR_EXTENSION_UNAVAILABLE")
        if not row[0]:
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector")
            except Exception:
                raise ProviderError("VECTOR_EXTENSION_ADMIN_REQUIRED") from None
        cursor.execute(f"""CREATE TABLE IF NOT EXISTS {TABLE} (
            chunk_id uuid NOT NULL REFERENCES ai_retrieval_searchchunk(id) ON DELETE CASCADE,
            generation_id uuid NOT NULL REFERENCES ai_retrieval_retrievalgeneration(id) ON DELETE CASCADE,
            profile_id varchar(64) NOT NULL,
            input_hash varchar(64) NOT NULL,
            embedding vector NOT NULL,
            PRIMARY KEY (chunk_id, profile_id)
        )""")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS hybrid_vector_input_idx ON {TABLE}(profile_id,input_hash)")
        cursor.execute(f"CREATE INDEX IF NOT EXISTS hybrid_vector_gen_idx ON {TABLE}(generation_id,profile_id)")


def _configuration(generation):
    profile = embeddings.profile()
    if generation.embedding_profile and generation.embedding_profile != profile:
        raise ProviderError("EMBEDDING_PROFILE_CHANGED")
    return profile


def count(generation, profile_id):
    if not available():
        return 0
    with connections[indexing.alias()].cursor() as cursor:
        cursor.execute(f"SELECT count(*) FROM {TABLE} WHERE generation_id=%s AND profile_id=%s", [generation.pk, profile_id])
        return cursor.fetchone()[0]


def missing(generation, profile_id, limit, *, after_id=None):
    from .models import SearchChunk
    parameters = [generation.pk, profile_id]
    cursor_filter = ""
    if after_id is not None:
        cursor_filter = " AND c.id>%s"
        parameters.append(uuid.UUID(str(after_id)))
    parameters.append(limit)
    with connections[indexing.alias()].cursor() as cursor:
        cursor.execute(f"SELECT c.id FROM ai_retrieval_searchchunk c WHERE c.generation_id=%s AND NOT EXISTS "
                       f"(SELECT 1 FROM {TABLE} v WHERE v.chunk_id=c.id AND v.profile_id=%s){cursor_filter} ORDER BY c.id LIMIT %s",
                       parameters)
        ids = [row[0] for row in cursor.fetchall()]
    return list(SearchChunk.objects.filter(pk__in=ids).order_by("pk"))


def reuse(profile_id, hashes):
    if not hashes:
        return {}
    placeholders = ",".join(["%s"] * len(hashes))
    with connections[indexing.alias()].cursor() as cursor:
        cursor.execute(f"SELECT DISTINCT ON (input_hash) input_hash,embedding::text FROM {TABLE} "
                       f"WHERE profile_id=%s AND input_hash IN ({placeholders})", [profile_id, *hashes])
        return {key: json.loads(vector) for key, vector in cursor.fetchall()}


def store(generation, profile, rows, values):
    if len(rows) != len(values):
        raise ProviderError("INVALID_EMBEDDING_RESPONSE")
    parameters = [(row.pk, generation.pk, profile["id"], row.input_hash,
                   json.dumps(embeddings.validate_vector(value, profile["dimensions"]))) for row, value in zip(rows, values)]
    with connections[indexing.alias()].cursor() as cursor:
        cursor.executemany(f"INSERT INTO {TABLE}(chunk_id,generation_id,profile_id,input_hash,embedding) "
                           "VALUES (%s,%s,%s,%s,%s::vector) ON CONFLICT (chunk_id,profile_id) DO NOTHING", parameters)


def create_index(generation, profile):
    # UUID/hex/dimension validation makes the internal DDL literals bounded and
    # independent of provider strings, source text or user questions.
    identifier = uuid.UUID(str(generation.pk)).hex
    digest = profile["id"]
    dimensions = profile["dimensions"]
    if not re.fullmatch(r"[0-9a-f]{64}", digest) or type(dimensions) is not int or not 1 <= dimensions <= 2000:
        raise ProviderError("INVALID_EMBEDDING_CONFIGURATION")
    name = "hybrid_hnsw_" + identifier[:20] + "_" + digest[:12]
    connection = connections[indexing.alias()]
    if connection.in_atomic_block:
        raise ProviderError("VECTOR_INDEX_REQUIRES_AUTOCOMMIT")
    with connection.cursor() as cursor:
        cursor.execute("SELECT i.indisvalid FROM pg_index i JOIN pg_class c ON c.oid=i.indexrelid "
                       "JOIN pg_namespace n ON n.oid=c.relnamespace WHERE c.relname=%s AND n.nspname=current_schema()", [name])
        row = cursor.fetchone()
        if row and row[0]:
            return
        if row:
            cursor.execute(f'DROP INDEX CONCURRENTLY "{name}"')
        cursor.execute(f'CREATE INDEX CONCURRENTLY "{name}" ON {TABLE} USING hnsw '
                       f'((embedding::vector({dimensions})) vector_cosine_ops) '
                       f"WHERE generation_id='{generation.pk}'::uuid AND profile_id='{digest}'")


def search(generation, vector, limit, *, audience="general"):
    configuration = _configuration(generation)
    if not generation.embedding_ready or not available():
        raise ProviderError("HYBRID_EMBEDDINGS_NOT_READY")
    value = json.dumps(embeddings.validate_vector(vector, configuration["dimensions"]))
    # Fetch candidates from the active generation's partial HNSW index. Filter
    # explicit populations before the final LIMIT; overfetch guards the join.
    excluded = "adult" if audience == "pediatric" else "pediatric" if audience == "adult" else ""
    with transaction.atomic(using=indexing.alias()):
        with connections[indexing.alias()].cursor() as cursor:
            cursor.execute("SET LOCAL hnsw.ef_search = 120")
            cursor.execute("SELECT extversion FROM pg_extension WHERE extname='vector'")
            version = tuple(int(v) for v in cursor.fetchone()[0].split(".")[:2])
            if version >= (0, 8):
                cursor.execute("SET LOCAL hnsw.iterative_scan = 'strict_order'")
            cursor.execute(f"SELECT v.chunk_id FROM {TABLE} v JOIN ai_retrieval_searchchunk c ON c.id=v.chunk_id "
                           f"WHERE v.generation_id=%s AND v.profile_id=%s AND c.audience<>%s "
                           f"ORDER BY v.embedding::vector({configuration['dimensions']}) <=> %s::vector({configuration['dimensions']}) LIMIT %s",
                           [generation.pk, configuration["id"], excluded, value, limit])
            return [row[0] for row in cursor.fetchall()]
