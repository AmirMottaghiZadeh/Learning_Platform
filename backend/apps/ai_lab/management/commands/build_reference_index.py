"""Build prepared UpToDate sources without calling any language model."""
from concurrent.futures import ProcessPoolExecutor
import multiprocessing
import re
import time
import uuid

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.ai_lab.document import prepare_blob_outcome
from apps.ai_lab.models import ReferenceArticle, ReferenceGeneration, ReferenceSource
from apps.ai_lab import reference_index
from apps.ai_lab.provider import ProviderError


class Command(BaseCommand):
    help = "Build/resume versioned reference sections and paragraphs, then atomically activate a complete index."

    def add_arguments(self, parser):
        parser.add_argument("--article", action="append", dest="article_ids")
        parser.add_argument("--limit", type=int)
        parser.add_argument("--workers", type=int, default=1)
        parser.add_argument("--batch-size", type=int, default=20)
        parser.add_argument("--resume", type=uuid.UUID)
        parser.add_argument("--no-activate", action="store_true")
        parser.add_argument("--force", action="store_true", help="Build a new generation even when a compatible one is ready.")
        parser.add_argument("--status", action="store_true")

    def handle(self, *args, **options):
        generation = None
        pool = None
        lock_key = None
        try:
            if not 1 <= options["workers"] <= 8 or not 1 <= options["batch_size"] <= 100:
                raise CommandError("INVALID_BUILD_SIZE")
            stamp = reference_index.source_stamp()
            active = reference_index.active_generation(stamp)
            if options["status"]:
                if active:
                    current = ReferenceGeneration.objects.get(pk=active)
                    self.stdout.write(f"Ready generation={active}; articles={current.built_articles}; sections={current.section_count}; blocks={current.block_count}.")
                else:
                    self.stdout.write("No compatible active generation.")
                return
            catalog = reference_index.source_article_ids()
            if not catalog:
                raise CommandError("EMPTY_SOURCE_CATALOG")
            identifiers = catalog
            if options["article_ids"]:
                identifiers = sorted(set(options["article_ids"]))
                if set(identifiers) - set(catalog):
                    raise CommandError("UNKNOWN_SOURCE_ARTICLE")
            if options["limit"] is not None:
                if options["limit"] < 1:
                    raise CommandError("INVALID_BUILD_LIMIT")
                identifiers = identifiers[:options["limit"]]
            if any(not re.fullmatch(r"[A-Za-z0-9_.:-]{1,32}", identifier) for identifier in identifiers):
                raise CommandError("INVALID_SOURCE_ARTICLE_ID")
            full = identifiers == catalog
            if options["resume"]:
                saved = ReferenceGeneration.objects.get(pk=options["resume"])
                if (options["article_ids"] or options["limit"] is not None) and identifiers != saved.article_ids:
                    raise CommandError("INDEX_RESUME_MISMATCH")
                identifiers, full = saved.article_ids, saved.scope == "full"
            if not full and not options["no_activate"]:
                raise CommandError("PARTIAL_INDEX_REQUIRES_NO_ACTIVATE")
            if active and full and not options["force"] and not options["resume"]:
                self.stdout.write(f"Compatible generation already active: {active}.")
                return
            lock_key = reference_index.acquire_build_lock(stamp.identity)
            generation = reference_index.begin_generation(stamp, identifiers, full=full, resume=options["resume"])
            self.stdout.write(f"Generation={generation.pk}; expected={generation.expected_articles}; scope={generation.scope}.")
            self.stdout.flush()
            done = set(ReferenceArticle.objects.filter(generation=generation).values_list("source_id", flat=True))
            remaining = [identifier for identifier in identifiers if identifier not in done]
            if options["workers"] > 1:
                pool = ProcessPoolExecutor(max_workers=options["workers"], mp_context=multiprocessing.get_context("spawn"))
            started = time.monotonic()
            for offset in range(0, len(remaining), options["batch_size"]):
                selected = remaining[offset:offset + options["batch_size"]]
                blobs = reference_index.source_blobs(selected, stamp.version)
                missing = set(selected) - {row[0] for row in blobs}
                errors = [{"article_id": identifier, "code": "SOURCE_ARTICLE_MISSING"} for identifier in sorted(missing)]
                outcomes = pool.map(prepare_blob_outcome, blobs) if pool else map(prepare_blob_outcome, blobs)
                documents = []
                for outcome in outcomes:
                    if "error" in outcome:
                        errors.append(outcome["error"])
                    else:
                        documents.append(outcome["document"])
                if documents:
                    reference_index.persist_documents(generation, documents)
                if errors:
                    generation.errors = (generation.errors + errors)[:50]
                    generation.save(update_fields=["errors"])
                self.stdout.write(f"Built={generation.built_articles}/{generation.expected_articles}; elapsed_s={time.monotonic()-started:.1f}; errors_recorded={len(generation.errors)}.")
                self.stdout.flush()
            reference_index.finish_generation(generation, stamp, activate=not options["no_activate"])
            self.stdout.write(self.style.SUCCESS(f"Ready generation={generation.pk}; articles={generation.built_articles}; sections={generation.section_count}; blocks={generation.block_count}; active={not options['no_activate']}."))
        except Exception as exc:
            if generation is not None:
                ReferenceGeneration.objects.filter(pk=generation.pk).update(status="failed", finished_at=timezone.now())
            if isinstance(exc, CommandError):
                raise
            code = exc.code if isinstance(exc, ProviderError) else "REFERENCE_INDEX_BUILD_FAILED"
            raise CommandError(code) from None
        finally:
            if pool:
                pool.shutdown(wait=True, cancel_futures=True)
            reference_index.release_build_lock(lock_key)
