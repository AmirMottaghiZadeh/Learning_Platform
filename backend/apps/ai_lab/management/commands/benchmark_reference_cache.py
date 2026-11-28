"""Bounded cold/hit diagnostics in a private, ephemeral account namespace."""
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from django.conf import settings
from django.core.cache import caches
from django.core.management.base import BaseCommand, CommandError

from apps.ai_lab import evaluation, http_transport, provider, response_cache
from apps.uptodate import services as utd

DEFAULT_CASES = ["drug-aripiprazole-adverse", "topic-enuresis-treatment", "topic-psoriasis-first-line"]


class Command(BaseCommand):
    help = "Measure paid cold answers and validated zero-request cache hits; isolated diagnostic account only."

    def add_arguments(self, parser):
        parser.add_argument("--output", required=True)
        parser.add_argument("--case", action="append", dest="case_ids")
        parser.add_argument("--limit", type=int, default=3)
        parser.add_argument("--max-requests", type=int, default=12)
        parser.add_argument("--max-seconds", type=int, default=120)

    def handle(self, *args, **options):
        keys = []
        try:
            output = Path(options["output"])
            if output.exists() or output.is_symlink():
                raise CommandError("OUTPUT_ALREADY_EXISTS")
            if not settings.AI_LAB_RESPONSE_CACHE_ENABLED:
                raise CommandError("RESPONSE_CACHE_DISABLED")
            if (not 1 <= options["limit"] <= 20 or not 1 <= options["max_requests"] <= 100
                    or not 1 <= options["max_seconds"] <= 600):
                raise CommandError("INVALID_RUN_BUDGET")
            secrets = tuple(provider.credentials().values())
            if not any(secrets):
                raise CommandError("KEY_NOT_CONFIGURED")
            dataset = evaluation.load_dataset()
            by_id = {case["id"]: case for case in dataset["cases"]}
            identifiers = list(dict.fromkeys(options["case_ids"] or DEFAULT_CASES))[:options["limit"]]
            if set(identifiers) - by_id.keys():
                raise CommandError("UNKNOWN_CASE_ID")
            # No database user/account is created and no real learner's quota
            # or answer-cache namespace is used by this administrator command.
            request = SimpleNamespace(user=SimpleNamespace(pk=f"diagnostic-{uuid4()}", is_authenticated=True, is_staff=True))
            evidence = evaluation.SourceEvidence()
            configuration = {"model": settings.AI_LAB_MODEL, "reasoning_effort": settings.AI_LAB_REASONING_EFFORT,
                "http_pool_enabled": settings.AI_LAB_HTTP_POOL_ENABLED, "total_timeout_seconds": None,
                "max_provider_requests": settings.AI_LAB_OUTLINE_MAX_PROVIDER_REQUESTS, "code_digest": response_cache.code_signature(),
                "cache_ttl_seconds": settings.AI_LAB_RESPONSE_CACHE_TTL_SECONDS, "source_version": utd.snapshot_version()}
            rows = []
            utd.search_page("nocturnal enuresis", limit=30, offset=0, section="")
            with provider.evaluation_budget(options["max_requests"], options["max_seconds"]) as budget:
                for identifier in identifiers:
                    case = by_id[identifier]
                    binding = evidence.bind(case)
                    lookup = response_cache.prepare(case["question"], "luna", ["uptodate"], case.get("history", []), request)
                    if lookup is None:
                        raise CommandError("COMPATIBLE_REFERENCE_INDEX_REQUIRED")
                    keys.append(lookup.key)
                    cold = evaluation.run_case(case, binding, evidence, configuration, request=request, budget=budget)
                    warm = {"status": "skipped", "reason": "no_complete_cached_answer"}
                    if cold["status"] == "complete" and caches["ai_lab"].get(lookup.key) is not None:
                        warm = evaluation.run_case(case, binding, evidence, configuration, request=request, budget=budget)
                    rows.append({"case_id": identifier, "cold": cold, "warm": warm})
                    self.stdout.write(f"Checked {identifier}: cold={cold['status']}; warm={warm['status']}")
                    if budget["exhausted"]:
                        break
            report = {"schema": 1, "kind": "reference_cache_diagnostic", "created_at": datetime.now(timezone.utc).isoformat(),
                "scope": "direct_service_ephemeral_account_not_browser_or_load_slo", "configuration": configuration,
                "dataset_digest": evaluation.digest(dataset), "cases": rows,
                "provider_requests": budget["used"], "budget_exhausted": budget["exhausted"], "release_slo_verified": False}
            evaluation.write_private_json(output, report, secrets=secrets)
            self.stdout.write(f"Report saved; cases={len(rows)}; provider requests={budget['used']}")
        except CommandError:
            raise
        except Exception:
            raise CommandError("CACHE_BENCHMARK_FAILED") from None
        finally:
            for key in keys:
                try:
                    caches["ai_lab"].delete(key)
                except Exception:
                    pass
            http_transport.close()
