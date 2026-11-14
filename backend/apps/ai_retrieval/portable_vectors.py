"""Offline, bounded vector transfer between independently built source indexes.

Only immutable input hashes and vectors cross environments. Destination chunks
keep their own paragraph IDs, source pins and citation anchors. No API calls.
"""
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path

from django.db import connections, transaction
from django.db.models import Q

from apps.ai_lab.provider import ProviderError
from . import embeddings, indexing, vectors
from .models import RetrievalHead, SearchChunk

FORMAT = "pharmenta-vectors-v1"
MAX_LINE = 131072


def _source(generation):
    stamp = indexing.reference_index.source_stamp()
    if (generation.status != "ready" or not generation.catalog_ready or not generation.chunk_count
            or generation.source_identity != stamp.identity or generation.source_revision != stamp.revision
            or generation.source_generation != indexing.reference_index.active_generation(stamp)):
        raise ProviderError("REFERENCE_INDEX_STALE")
    if generation.pending_embedding_inputs:
        raise ProviderError("EMBEDDING_PREVIOUS_REQUEST_UNCERTAIN")


def _chunks(generation, batch_size):
    after = None
    while True:
        rows = SearchChunk.objects.filter(generation=generation)
        if after is not None:
            source, ordinal = after
            rows = rows.filter(Q(source_id__gt=source) | Q(source_id=source, ordinal__gt=ordinal))
        batch = list(rows.only("id", "source_id", "ordinal", "content_hash", "input_hash")
                     .order_by("source_id", "ordinal")[:batch_size])
        if not batch:
            return
        yield batch
        after = batch[-1].source_id, batch[-1].ordinal


def _encoded(value):
    return (json.dumps(value, separators=(",", ":"), ensure_ascii=True, allow_nan=False)+"\n").encode()


def _read(stream):
    line = stream.readline(MAX_LINE+1)
    if not line or len(line) > MAX_LINE or not line.endswith(b"\n"):
        raise ProviderError("VECTOR_ARCHIVE_INVALID")
    try:
        return line, json.loads(line)
    except (ValueError, UnicodeError):
        raise ProviderError("VECTOR_ARCHIVE_INVALID") from None


def export_vectors(generation, output, *, batch_size=256, progress=lambda _:None):
    _source(generation)
    profile = vectors._configuration(generation)
    if (not generation.embedding_ready or not vectors.available()
            or vectors.count(generation, profile["id"]) != generation.chunk_count):
        raise ProviderError("HYBRID_EMBEDDINGS_INCOMPLETE")
    output = Path(output)
    # Exclusive creation prevents overwriting another backup or following a
    # symlink. A failed/incomplete export is removed, never presented as ready.
    fd = os.open(output, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    lock = None
    try:
        lock = indexing.reference_index.acquire_build_lock("hybrid-embed:"+str(generation.pk))
        header = {"format": FORMAT, "profile": profile, "chunker_version": generation.chunker_version,
                  "scope": generation.scope, "chunks": generation.chunk_count}
        digest, count = sha256(), 0
        with os.fdopen(fd, "wb") as target:
            fd = None
            with gzip.GzipFile(filename="", fileobj=target, mode="wb", compresslevel=1, mtime=0) as stream:
                raw = _encoded(header)
                stream.write(raw); digest.update(raw)
                for batch in _chunks(generation, batch_size):
                    _source(generation)
                    ids = [row.pk for row in batch]
                    with connections[indexing.alias()].cursor() as cursor:
                        cursor.execute(f"SELECT chunk_id,input_hash,embedding::text,vector_dims(embedding) "
                            f"FROM {vectors.TABLE} WHERE generation_id=%s AND profile_id=%s "
                            "AND chunk_id=ANY(%s)", [generation.pk, profile["id"], ids])
                        stored = {row[0]:row[1:] for row in cursor.fetchall()}
                    for row in batch:
                        vector = stored.get(row.pk)
                        if not vector or vector[0] != row.input_hash or vector[2] != profile["dimensions"]:
                            raise ProviderError("HYBRID_EMBEDDINGS_INCOMPLETE")
                        # Native pgvector text is already a bounded JSON number
                        # array. Avoid materializing millions of Python floats.
                        prefix = _encoded([row.source_id,row.ordinal,row.content_hash,row.input_hash])[:-2]
                        raw = prefix+b","+vector[1].encode()+b"]\n"
                        if len(raw)>MAX_LINE:
                            raise ProviderError("VECTOR_ARCHIVE_INVALID")
                        stream.write(raw); digest.update(raw); count += 1
                    progress({"stage":"export","written":count,"expected":generation.chunk_count})
                _source(generation)
                if count != generation.chunk_count:
                    raise ProviderError("HYBRID_INDEX_INCOMPLETE")
                checksum = digest.hexdigest()
                stream.write(_encoded({"end":count,"sha256":checksum}))
            target.flush(); os.fsync(target.fileno())
        return {"exported":count,"payload_sha256":checksum,"bytes":output.stat().st_size}
    except BaseException:
        if fd is not None:
            os.close(fd)
        output.unlink(missing_ok=True)
        raise
    finally:
        indexing.reference_index.release_build_lock(lock)


def _scan(generation, path, profile, batch_size, consume, progress):
    count, digest = 0, sha256()
    with gzip.open(path, "rb") as stream:
        raw, header = _read(stream)
        if (not isinstance(header, dict) or header.get("format") != FORMAT
                or header.get("profile") != profile or header.get("chunks") != generation.chunk_count
                or header.get("chunker_version") != generation.chunker_version
                or header.get("scope") != generation.scope):
            raise ProviderError("VECTOR_ARCHIVE_PROFILE_OR_CORPUS_MISMATCH")
        digest.update(raw)
        for batch in _chunks(generation, batch_size):
            _source(generation)
            values = []
            for row in batch:
                raw, record = _read(stream)
                if (not isinstance(record, list) or len(record)!=5
                        or record[:4] != [row.source_id,row.ordinal,row.content_hash,row.input_hash]):
                    raise ProviderError("VECTOR_ARCHIVE_INPUT_MISMATCH")
                values.append(embeddings.validate_vector(record[4],profile["dimensions"]))
                digest.update(raw); count += 1
            consume(batch, values)
            progress({"stage":"verify" if consume is _discard else "import","checked":count,
                      "expected":generation.chunk_count})
        _, footer = _read(stream)
        if (count != generation.chunk_count or not isinstance(footer, dict)
                or footer != {"end":count,"sha256":digest.hexdigest()} or stream.read(1)):
            raise ProviderError("VECTOR_ARCHIVE_CHECKSUM_MISMATCH")
    _source(generation)
    return digest.hexdigest()


def _discard(rows, values):
    pass


def import_vectors(generation, path, *, batch_size=256, verify_only=False, build_index=False, progress=lambda _:None):
    _source(generation)
    profile = vectors._configuration(generation)
    if not verify_only and RetrievalHead.objects.filter(active=generation).exists():
        raise ProviderError("VECTOR_IMPORT_TARGET_IS_ACTIVE")
    lock = indexing.reference_index.acquire_build_lock("hybrid-embed:"+str(generation.pk))
    try:
        if not verify_only and RetrievalHead.objects.filter(active=generation).exists():
            raise ProviderError("VECTOR_IMPORT_TARGET_IS_ACTIVE")
        # Validate the entire archive BEFORE storing a single vector. The
        # second pass checks it again, including a mutation/truncation in flight.
        digest = _scan(generation,path,profile,batch_size,_discard,progress)
        if verify_only:
            return {"verified":generation.chunk_count,"payload_sha256":digest,"provider_requests":0}
        vectors.ensure_schema()
        generation.embedding_ready = False
        generation.embedding_profile = profile
        generation.save(update_fields=["embedding_ready","embedding_profile"])
        imported, reused = 0, 0
        def store(rows, values):
            nonlocal imported, reused
            ids = [row.pk for row in rows]
            with connections[indexing.alias()].cursor() as cursor:
                cursor.execute(f"SELECT chunk_id,input_hash,vector_dims(embedding),embedding::text FROM {vectors.TABLE} "
                    "WHERE generation_id=%s AND profile_id=%s AND chunk_id=ANY(%s)",
                    [generation.pk,profile["id"],ids])
                existing = {row[0]:row[1:] for row in cursor.fetchall()}
            fresh, fresh_values = [], []
            for row,value in zip(rows,values):
                if row.pk in existing:
                    previous = existing[row.pk]
                    if (previous[:2] != (row.input_hash,profile["dimensions"])
                            or any(abs(a-b)>1e-6 for a,b in zip(json.loads(previous[2]),value))):
                        raise ProviderError("VECTOR_IMPORT_EXISTING_MISMATCH")
                    reused += 1
                else:
                    fresh.append(row); fresh_values.append(value)
            with transaction.atomic(using=indexing.alias()):
                vectors.store(generation,profile,fresh,fresh_values)
            imported += len(fresh)
        second = _scan(generation,path,profile,batch_size,store,progress)
        if second != digest or vectors.count(generation,profile["id"]) != generation.chunk_count:
            raise ProviderError("VECTOR_ARCHIVE_CHECKSUM_MISMATCH")
        if build_index:
            progress({"stage":"hnsw","vectors":generation.chunk_count})
            vectors.create_index(generation,profile)
            _source(generation)
            generation.embedding_ready = True
            generation.save(update_fields=["embedding_ready"])
        return {"imported":imported,"reused":reused,"index_ready":generation.embedding_ready,
                "payload_sha256":digest,"provider_requests":0,"active":False}
    finally:
        indexing.reference_index.release_build_lock(lock)
