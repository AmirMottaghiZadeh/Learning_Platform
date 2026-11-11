"""Check stored source blocks and legacy-reader parity without model requests."""
import statistics
import time

from django.core.management.base import BaseCommand, CommandError
from django.test import override_settings

from apps.ai_lab import document, evaluation, reference_index, retrieval
from apps.ai_lab.models import ReferenceArticle, ReferenceGeneration
from apps.ai_lab.provider import ProviderError
from apps.uptodate import services as utd


def verify_article(identifier, generation, repeat):
    article = utd.get_topic(identifier)
    if article is None:
        raise ProviderError("SOURCE_ARTICLE_MISSING")
    expected = document.prepare_document(identifier, article)
    stored = ReferenceArticle.objects.get(generation=generation, source_id=identifier)
    metadata_fields = ["source_id", "title", "source_version", "content_hash", "is_directory", "related_topics",
                       "raw_block_count", "eligible_block_count", "eligible_section_count", "filter_limited"]
    metadata_ok = all(getattr(stored, name) == expected[name] for name in metadata_fields)
    sections = []
    for section in stored.sections.select_related("parent").order_by("ordinal"):
        item = {name: getattr(section, name) for name in ["ordinal", "source_id", "heading", "heading_path", "hierarchy_known", "retrieval_order"]}
        if section.parent and section.parent.article_id != stored.pk:
            raise ProviderError("INDEX_HIERARCHY_MISMATCH")
        item["parent_ordinal"] = section.parent.ordinal if section.parent else None
        sections.append(item)
    blocks = []
    for block in stored.paragraphs.select_related("section").order_by("ordinal"):
        if block.section.article_id != stored.pk:
            raise ProviderError("INDEX_HIERARCHY_MISMATCH")
        item = {name: getattr(block, name) for name in ["ordinal", "retrieval_number", "source_anchor", "kind", "text",
                                                     "table_headers", "table_context_status", "exclusion_reason"]}
        item["section_ordinal"] = block.section.ordinal
        blocks.append(item)
    storage_ok = metadata_ok and sections == expected["sections"] and blocks == expected["blocks"]
    legacy_times, prepared_times, parity = [], [], True
    for _ in range(repeat):
        with override_settings(AI_LAB_PREPROCESSED_MODE="off"):
            before = time.perf_counter()
            legacy_audit = {}
            legacy = retrieval.read_sections([identifier], None, legacy_audit)
            legacy_times.append(round((time.perf_counter() - before) * 1000, 3))
        with override_settings(AI_LAB_PREPROCESSED_MODE="require"):
            before = time.perf_counter()
            prepared_audit = {}
            prepared = retrieval.read_sections([identifier], None, prepared_audit)
            prepared_times.append(round((time.perf_counter() - before) * 1000, 3))
        parity &= legacy == prepared and prepared_audit.get("preprocessed_articles") == 1
        parity &= all(legacy_audit.get(name) == prepared_audit.get(name) for name in [
            "limited", "related_topics", "selected_articles", "candidate_sections", "candidate_passages"])
    return {"article_id": identifier, "storage_matches_source": storage_ok, "reader_matches_legacy": bool(parity),
            "sections": len(sections), "blocks": len(blocks), "hierarchy_known_sections": sum(s["hierarchy_known"] for s in sections),
            "legacy_read_ms": legacy_times, "prepared_read_ms": prepared_times,
            "legacy_median_ms": statistics.median(legacy_times), "prepared_median_ms": statistics.median(prepared_times)}


class Command(BaseCommand):
    help = "Verify prepared blocks, hierarchy and exact original-reader output; no model/API key required."

    def add_arguments(self, parser):
        parser.add_argument("--article", action="append", dest="article_ids")
        parser.add_argument("--dataset", default=str(evaluation.DEFAULT_DATASET))
        parser.add_argument("--repeat", type=int, default=3)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            if not 1 <= options["repeat"] <= 5:
                raise CommandError("INVALID_REPEAT_COUNT")
            stamp = reference_index.source_stamp()
            active = reference_index.active_generation(stamp)
            if not active:
                raise CommandError("REFERENCE_INDEX_NOT_READY")
            generation = ReferenceGeneration.objects.get(pk=active)
            if options["article_ids"]:
                identifiers = list(dict.fromkeys(options["article_ids"]))
            else:
                dataset = evaluation.load_dataset(options["dataset"])
                identifiers = sorted({source["article_id"] for case in dataset["cases"] for source in case.get("expected", [])})
            report = {"schema": 1, "generation": str(active), "source_backend": stamp.backend,
                      "snapshot_version": stamp.version, "indexed_articles": generation.built_articles,
                      "indexed_sections": generation.section_count, "indexed_blocks": generation.block_count,
                      "format_version": generation.format_version, "extraction_version": generation.extraction_version,
                      "provider_requests": 0, "repeat": options["repeat"], "articles": []}
            for identifier in identifiers:
                try:
                    row = verify_article(identifier, generation, options["repeat"])
                except Exception as exc:
                    code = exc.code if isinstance(exc, ProviderError) else "INDEX_ARTICLE_VERIFICATION_FAILED"
                    row = {"article_id": identifier, "storage_matches_source": False, "reader_matches_legacy": False, "error_code": code}
                report["articles"].append(row)
            failed = sum(not row["storage_matches_source"] or not row["reader_matches_legacy"] for row in report["articles"])
            same_source = reference_index.source_stamp() == stamp
            report.update(checked_articles=len(identifiers), failed_articles=failed, source_unchanged=same_source,
                          compatible_generation=not failed and same_source)
            evaluation.write_private_json(options["output"], report)
            self.stdout.write(f"Verified={len(identifiers)}; failed={failed}; source_unchanged={same_source}; provider requests=0.")
            if failed or not same_source:
                raise CommandError("REFERENCE_INDEX_VERIFICATION_FAILED")
        except CommandError:
            raise
        except Exception:
            raise CommandError("REFERENCE_INDEX_VERIFICATION_FAILED") from None
