import json
import math
from pathlib import Path
import shutil
import time
from collections import OrderedDict
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.ai_lab.provider import ProviderError
from apps.ai_lab.transport_pool import pooled
from apps.ai_retrieval import embeddings, indexing, vectors
from apps.ai_retrieval.models import RetrievalGeneration


class Command(BaseCommand):
    help = "Embed chunks with a per-run input limit and cumulative reserved-token ceiling; reuse existing vectors."

    def add_arguments(self, parser):
        parser.add_argument("generation")
        parser.add_argument("--max-inputs", type=int, required=True)
        parser.add_argument("--max-tokens", type=int, required=True)
        parser.add_argument("--batch-size", type=int, default=16)
        parser.add_argument("--retry-uncertain", action="store_true")
        parser.add_argument("--activate", action="store_true")
        parser.add_argument("--min-free-disk-gb", type=float, default=0,
            help="Stop before another paid batch/index build when the checked filesystem falls below this many GiB.")
        parser.add_argument("--disk-check-path", default=".",
            help="Existing path on the PostgreSQL storage filesystem; only meaningful when it shares this host/mount.")
        parser.add_argument("--stop-file",default="",
            help="Pause after the current committed batch when this file exists; do not interrupt a paid request.")

    @pooled
    def handle(self, *args, **options):
        stage = "preflight"
        lock = None
        try:
            if (options["max_inputs"] < 1 or options["max_tokens"] < 1 or not 1 <= options["batch_size"] <= 128
                    or not math.isfinite(options["min_free_disk_gb"]) or options["min_free_disk_gb"] < 0):
                raise ProviderError("INVALID_EMBEDDING_BUDGET")
            disk_path = Path(options["disk_check_path"]).resolve()
            def disk_guard():
                if options["min_free_disk_gb"] and shutil.disk_usage(disk_path).free < options["min_free_disk_gb"] * 2**30:
                    raise ProviderError("EMBEDDING_DISK_RESERVE_REACHED")
            disk_guard()
            generation = RetrievalGeneration.objects.get(pk=options["generation"])
            if generation.status != "ready" or not generation.chunk_count:
                raise ProviderError("HYBRID_INDEX_NOT_READY")
            if options["activate"] and generation.scope != "full":
                raise ProviderError("PARTIAL_INDEX_CANNOT_ACTIVATE")
            lock = indexing.reference_index.acquire_build_lock("hybrid-embed:" + str(generation.pk))
            stamp = indexing.reference_index.source_stamp()
            def validate_source():
                if (generation.source_identity != stamp.identity or generation.source_revision != stamp.revision
                        or generation.source_generation != indexing.reference_index.active_generation(stamp)
                        or indexing.reference_index.source_stamp() != stamp):
                    raise ProviderError("REFERENCE_INDEX_STALE")
            validate_source()
            profile = vectors._configuration(generation)
            vectors.ensure_schema()
            local = profile.get("backend") == "onnx"
            if generation.pending_embedding_inputs and not local and not options["retry_uncertain"]:
                raise ProviderError("EMBEDDING_PREVIOUS_REQUEST_UNCERTAIN")
            generation.embedding_profile = profile
            generation.pending_embedding_inputs = []
            generation.save(update_fields=["embedding_profile", "pending_embedding_inputs"])
            paid_inputs, reused_inputs, after_id = 0, 0, None
            started = time.monotonic()
            stored_vectors = vectors.count(generation, profile["id"])
            self.stdout.write(json.dumps({"stage":"embedding", "generation":str(generation.pk),
                "model":profile["model"], "dimensions":profile["dimensions"],
                "stored_vectors":stored_vectors, "expected_vectors":generation.chunk_count,
                "max_inputs":options["max_inputs"], "max_tokens":options["max_tokens"]}))
            while True:
                if options["stop_file"] and Path(options["stop_file"]).exists():
                    self.stdout.write(json.dumps({"paused":True,"generation":str(generation.pk),
                        "stored_vectors":stored_vectors,"expected_vectors":generation.chunk_count,
                        "cumulative_tokens_reserved":generation.embedding_tokens_reserved}))
                    return
                disk_guard()
                validate_source()
                vectors._configuration(generation)
                rows = vectors.missing(generation, profile["id"], options["batch_size"], after_id=after_id)
                # Respect the adapter's total-input ceiling even for batches
                # containing unusually long source paragraphs.
                batch_tokens = 0
                for position,row in enumerate(rows):
                    if batch_tokens + row.token_count > 180000:
                        rows = rows[:position]
                        break
                    batch_tokens += row.token_count
                if not rows:
                    break
                cached = vectors.reuse(profile["id"], [row.input_hash for row in rows])
                cached_rows = [row for row in rows if row.input_hash in cached]
                if cached_rows:
                    vectors.store(generation, profile, cached_rows, [cached[row.input_hash] for row in cached_rows])
                    reused_inputs += len(cached_rows)
                    stored_vectors += len(cached_rows)
                remaining = [row for row in rows if row.input_hash not in cached]
                if not remaining:
                    after_id = rows[-1].pk
                    continue
                unique = list(OrderedDict((row.input_hash, row) for row in remaining).values())
                reserved = sum(row.token_count for row in unique)
                if (paid_inputs + len(unique) > options["max_inputs"]
                        or generation.embedding_tokens_reserved + reserved > options["max_tokens"]):
                    self.stdout.write(json.dumps({"budget_reached":True, "generation":str(generation.pk),
                        "paid_inputs":paid_inputs, "reused_inputs":reused_inputs,
                        "cumulative_tokens_reserved":generation.embedding_tokens_reserved,
                        "vectors":vectors.count(generation,profile["id"]), "expected":generation.chunk_count}))
                    return
                # Commit the reservation BEFORE the paid POST. If the worker
                # dies or loses the response, resuming requires an explicit
                # uncertain retry and previous token reservations still count.
                generation.embedding_tokens_reserved += reserved
                generation.embedding_requests_used += 1
                generation.pending_embedding_inputs = [row.input_hash for row in unique]
                generation.save(update_fields=["embedding_tokens_reserved", "embedding_requests_used", "pending_embedding_inputs"])
                stage = "embedding"
                values, metadata = embeddings.embed([row.embedding_input for row in unique])
                by_hash = dict(zip((row.input_hash for row in unique), values))
                with transaction.atomic(using=indexing.alias()):
                    vectors.store(generation, profile, remaining, [by_hash[row.input_hash] for row in remaining])
                    generation.pending_embedding_inputs = []
                    generation.save(update_fields=["pending_embedding_inputs"])
                paid_inputs += len(unique)
                stored_vectors += len(remaining)
                after_id = rows[-1].pk
                self.stdout.write(json.dumps({"paid_inputs":paid_inputs, "reused_inputs":reused_inputs,
                    "cumulative_tokens_reserved":generation.embedding_tokens_reserved,
                    "generation":str(generation.pk), "stored_vectors":stored_vectors,
                    "expected_vectors":generation.chunk_count,
                    "elapsed_seconds":round(time.monotonic()-started,1), **metadata,
                    "computed_inputs":paid_inputs,"paid_inputs":0 if local else paid_inputs}))
            stage = "index"
            disk_guard()
            validate_source()
            if vectors.count(generation, profile["id"]) != generation.chunk_count:
                raise ProviderError("HYBRID_EMBEDDINGS_INCOMPLETE")
            self.stdout.write(json.dumps({"stage":"hnsw", "generation":str(generation.pk),
                "stored_vectors":generation.chunk_count, "elapsed_seconds":round(time.monotonic()-started,1)}))
            vectors.create_index(generation, profile)
            generation.embedding_ready = True
            generation.save(update_fields=["embedding_ready"])
            if options["activate"]:
                indexing.activate_generation(generation)
            self.stdout.write(json.dumps({"ready":True,"generation":str(generation.pk),"chunks":generation.chunk_count,
                "paid_inputs":0 if local else paid_inputs,"computed_inputs":paid_inputs,
                "reused_inputs":reused_inputs,"cumulative_tokens_reserved":generation.embedding_tokens_reserved}))
        except Exception as exc:
            status = getattr(exc, "status", 0)
            status_text = f" provider_status={status}" if type(status) is int and 100 <= status <= 599 else ""
            raise CommandError(f"HYBRID_EMBED_FAILED stage={stage} code={getattr(exc,'code','INTERNAL_ERROR')} type={type(exc).__name__}{status_text}") from None
        finally:
            indexing.reference_index.release_build_lock(lock)
