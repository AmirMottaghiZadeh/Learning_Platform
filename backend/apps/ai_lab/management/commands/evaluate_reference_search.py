"""Phase-zero measurements. Validation and summarization never call a model."""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from urllib.parse import urlsplit

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.ai_lab import document, evaluation, http_transport, lexical, provider, reference_index, response_cache, retrieval, selection, services
from apps.uptodate import services as utd


class Command(BaseCommand):
    help = "Validate reference-search cases, run a bounded paid baseline, or summarize reviewed results."

    def add_arguments(self, parser):
        parser.add_argument("--mode", choices=["validate", "run", "summarize"], default="validate")
        parser.add_argument("--dataset", default=str(evaluation.DEFAULT_DATASET))
        parser.add_argument("--output", required=True, help="New private JSON file; existing files are never overwritten.")
        parser.add_argument("--input", help="Existing baseline JSON for summarize.")
        parser.add_argument("--reviews", help="Manual reviews bound to case IDs and response digests.")
        parser.add_argument("--case", action="append", dest="case_ids", help="Repeat to select case IDs.")
        parser.add_argument("--limit", type=int, default=3, help="Maximum selected cases for a live run (default 3).")
        parser.add_argument("--repeat", type=int, default=1)
        parser.add_argument("--cache-state", choices=["warm", "cold"], default="warm")
        parser.add_argument("--max-requests", type=int, default=12, help="Total upstream request budget across the run.")
        parser.add_argument("--max-seconds", type=int, default=180, help="Total upstream time budget across the run.")

    def handle(self, *args, **options):
        try:
            self.execute_evaluation(options)
        except CommandError:
            raise
        except Exception as exc:
            # Never print provider error bodies, settings, input JSON or repr(exc).
            code = str(exc) if isinstance(exc, evaluation.EvaluationError) else "EVALUATION_COMMAND_FAILED"
            raise CommandError(code) from None

    def execute_evaluation(self, options):
        output = Path(options["output"])
        if output.exists() or output.is_symlink():
            raise CommandError("OUTPUT_ALREADY_EXISTS")
        if options["mode"] == "summarize":
            if not options["input"]:
                raise CommandError("INPUT_REQUIRED")
            report = evaluation.load_baseline(options["input"])
            if options["reviews"]:
                evaluation.apply_reviews(report["runs"], json.loads(Path(options["reviews"]).read_text()))
            report["summary"] = evaluation.summarize(report["runs"], expected_suite_size=report.get("suite_size"))
            evaluation.write_private_json(output, report)
            self.stdout.write(f"Reviewed baseline saved; cases={len(report['runs'])}; no provider calls.")
            return

        dataset = evaluation.load_dataset(options["dataset"])
        cases = dataset["cases"]
        if options["case_ids"]:
            selected_ids = set(options["case_ids"])
            if selected_ids - {case["id"] for case in cases}:
                raise CommandError("UNKNOWN_CASE_ID")
            by_id = {case["id"]: case for case in cases}
            cases = [by_id[identifier] for identifier in dict.fromkeys(options["case_ids"])]
        if options["mode"] == "run":
            if not 1 <= options["limit"] <= 500 or not 1 <= options["repeat"] <= 10:
                raise CommandError("INVALID_RUN_SIZE")
            if not 1 <= options["max_requests"] <= 2000 or not 1 <= options["max_seconds"] <= 7200:
                raise CommandError("INVALID_RUN_BUDGET")
            cases = cases[:options["limit"]]

        evidence = evaluation.SourceEvidence()
        bindings = []
        for case in cases:
            try:
                sources = evidence.bind(case)
                bindings.append({"case_id": case["id"], "status": "source_checked", "sources": sources,
                                 "clinical_review": "pending"})
            except evaluation.EvaluationError as exc:
                bindings.append({"case_id": case["id"], "status": "invalid", "error_code": str(exc)})
        report = {"schema": 1, "created_at": datetime.now(timezone.utc).isoformat(),
                  "dataset_version": dataset.get("version"), "dataset_digest": evaluation.digest(dataset),
                  "suite_size": len(dataset["cases"]), "bindings": bindings,
                  "clinical_gold_status": "source_checked_not_clinically_approved"}
        invalid = sum(binding["status"] == "invalid" for binding in bindings)
        if options["mode"] == "validate":
            report.update(kind="reference_search_source_validation", invalid_cases=invalid, provider_requests=0)
            evaluation.write_private_json(output, report)
            self.stdout.write(f"Source validation saved; cases={len(cases)}; invalid={invalid}; provider calls=0.")
            if invalid:
                raise CommandError("SOURCE_VALIDATION_FAILED")
            return
        if invalid:
            raise CommandError("SOURCE_VALIDATION_FAILED")

        secrets = tuple(provider.credentials().values())
        if not any(secrets):
            raise CommandError("KEY_NOT_CONFIGURED")
        parsed = urlsplit(settings.AI_LAB_BASE_URL)
        # No userinfo, query or fragment can enter configuration snapshots.
        safe_base = f"{parsed.scheme}://{parsed.hostname or ''}{parsed.path}"
        effort = settings.AI_LAB_REASONING_EFFORT
        if effort is None:
            effort = settings.AI_LAB_LUNA_REASONING_EFFORT
        configuration = {"model": settings.AI_LAB_MODEL, "base_url": safe_base,
                         "reasoning_effort": effort, "cache_state": options["cache_state"],
                         "source_backend": "mysql" if utd._using_mysql() else "sqlite",
                         "snapshot_version": utd.snapshot_version(), "pipeline": "uptodate-first-answer",
                         "preprocessing_mode": settings.AI_LAB_PREPROCESSED_MODE,
                         "lexical_enabled": settings.AI_LAB_LEXICAL_ENABLED,
                         "lexical_version": lexical.LEXICAL_VERSION,
                         "section_selection": "local" if selection.enabled() else "model",
                         "selection_version": selection.SELECTION_VERSION if selection.enabled() else None,
                         "total_timeout_seconds": settings.AI_LAB_TOTAL_TIMEOUT_SECONDS,
                         "max_provider_requests": settings.AI_LAB_MAX_PROVIDER_REQUESTS,
                         "http_pool_enabled": settings.AI_LAB_HTTP_POOL_ENABLED,
                         "lexical_limits": {"sections": lexical.MAX_RANKED_SECTIONS, "passages": lexical.MAX_RANKED_PASSAGES,
                                            "characters": lexical.MAX_PASSAGE_CHARACTERS},
                         "prepared_format_version": document.FORMAT_VERSION,
                         "prompt_digest": evaluation.digest([services.PLAN_PROMPT,
                             *([] if selection.enabled() else [services.SECTIONS_PROMPT, services.FIRST_LINE_SECTION_RULES]),
                             services.ANSWER_PROMPT, services.VERIFY_PROMPT, services.FIRST_LINE_ANSWER_RULES, services.FIRST_LINE_VERIFY_RULES]),
                         "pipeline_code_digest": evaluation.digest({Path(module.__file__).name: Path(module.__file__).read_text()
                                                                     for module in [services, provider, http_transport, response_cache, retrieval, document, reference_index, lexical, selection, evaluation, evaluation.telemetry]})}
        report.update(kind="reference_search_baseline", configuration=configuration,
                      budget={"max_requests": options["max_requests"], "max_seconds": options["max_seconds"]},
                      transport="direct_service", response_cache="bypassed_without_account", runs=[], warmup_ms=None)
        utd.close_all()
        if options["cache_state"] == "warm":
            started = time.perf_counter()
            utd.search_page("nocturnal enuresis", limit=30, offset=0, section="")
            report["warmup_ms"] = round((time.perf_counter() - started) * 1000, 3)
        journal = output.with_suffix(output.suffix + ".progress.jsonl")
        journal.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(journal, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
        with os.fdopen(descriptor, "w") as progress, provider.evaluation_budget(options["max_requests"], options["max_seconds"]) as budget:
            evaluation.append_private_journal(progress, {**report, "kind": "reference_search_baseline_journal"}, secrets=secrets)
            for repetition in range(options["repeat"]):
                for case, binding in zip(cases, bindings):
                    if options["cache_state"] == "cold":
                        # Clear only this isolated process's source caches.
                        utd.close_all()
                    row = evaluation.run_case(case, binding["sources"], evidence, configuration, budget=budget)
                    row["repetition"] = repetition + 1
                    report["runs"].append(row)
                    evaluation.append_private_journal(progress, row, secrets=secrets)
                    self.stdout.write(f"Case {case['id']}: {row['status']}; requests={row['metrics']['provider_requests']}")
                    if budget["exhausted"]:
                        break
                if budget["exhausted"]:
                    break
            report["budget"].update(used=budget["used"], exhausted=budget["exhausted"])
        if options["reviews"]:
            evaluation.apply_reviews(report["runs"], json.loads(Path(options["reviews"]).read_text()))
        report["summary"] = evaluation.summarize(report["runs"], expected_suite_size=report["suite_size"])
        evaluation.write_private_json(output, report, secrets=secrets)
        self.stdout.write(f"Private baseline saved; runs={len(report['runs'])}; upstream requests={budget['used']}.")
