"""Real authenticated admission, worker, polling and cache-hit load."""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.ai_lab import evaluation, http_evaluation, release, response_cache


class Command(BaseCommand):
    help = "Send bounded authenticated cold/hit traffic to an explicitly selected API. Cold calls consume API credit."

    def add_arguments(self, parser):
        parser.add_argument("--accounts-file", required=True)
        parser.add_argument("--api-base", required=True, help="Versioned API root, e.g. http://127.0.0.1:8765/api/v1")
        parser.add_argument("--output", required=True)
        parser.add_argument("--limit", type=int, default=20)
        parser.add_argument("--concurrency", type=int, default=2)
        parser.add_argument("--poll", type=float, default=1)
        parser.add_argument("--max-requests", type=int, default=120)
        parser.add_argument("--case", action="append", dest="case_ids")

    def handle(self, *args, **options):
        try:
            from pathlib import Path
            if Path(options["output"]).exists():
                raise evaluation.EvaluationError("OUTPUT_ALREADY_EXISTS")
            if not 1 <= options["limit"] <= 100 or not 1 <= options["max_requests"] <= 1000:
                raise evaluation.EvaluationError("INVALID_RUN_BUDGET")
            accounts = http_evaluation.load_accounts(options["accounts_file"])
            status, remote = http_evaluation.Client(options["api_base"], accounts[0]["access_token"]).json("/ai-lab/status/?diagnostics=1")
            if status != 200 or remote.get("runtime", {}).get("profile_digest") != evaluation.digest(release.runtime_profile()):
                raise evaluation.EvaluationError("HTTP_RUNTIME_MISMATCH")
            dataset = evaluation.load_dataset()
            by_id = {case["id"]: case for case in dataset["cases"]}
            if options["case_ids"]:
                if set(options["case_ids"]) - by_id.keys():
                    raise evaluation.EvaluationError("UNKNOWN_CASE_ID")
                selected = [by_id[name] for name in dict.fromkeys(options["case_ids"])]
            else:
                # Authored plans cover varied drug/topic intents without supplying
                # any expected heading or answer to the application.
                import json
                from apps.ai_lab.management.commands.evaluate_lexical_retrieval import DEFAULT_PLANS
                selected = [by_id[row["case_id"]] for row in json.loads(DEFAULT_PLANS.read_text())["plans"]]
            selected = selected[:options["limit"]]
            config = {"model": settings.AI_LAB_MODEL, "base_url": settings.AI_LAB_BASE_URL,
                "reasoning_effort": settings.AI_LAB_REASONING_EFFORT, "code_digest": response_cache.code_signature(),
                "source_version": release.runtime_profile()["source_revision"],
                "max_provider_requests": settings.AI_LAB_MAX_PROVIDER_REQUESTS}
            measured = http_evaluation.run_load(selected, accounts, options["api_base"], config, evaluation.SourceEvidence(),
                concurrency=options["concurrency"], poll=options["poll"], max_requests=options["max_requests"])
            runtime = measured.pop("runtime")
            fingerprints = {row.get("profile_digest") for row in runtime}
            measured.update(schema=1, kind="reference_http_load", configuration=config, concurrency=options["concurrency"],
                polling_seconds=options["poll"], runtime_profile_digest=next(iter(fingerprints)) if len(fingerprints) == 1 else None,
                observed_workers=len({row.get("instance") for row in runtime if row.get("instance")}),
                shared_cache=bool(runtime) and all("redis" in row.get("job_cache_backend", "").lower()
                    and "redis" in row.get("answer_cache_backend", "").lower() for row in runtime), release_slo_verified=False)
            evaluation.write_private_json(options["output"], measured, secrets=[row["access_token"] for row in accounts])
            self.stdout.write(f"HTTP measurements saved; samples={len(measured['runs'])}; workers={measured['observed_workers']}")
        except evaluation.EvaluationError as error:
            raise CommandError(str(error)) from None
        except Exception:
            raise CommandError("HTTP_BENCHMARK_FAILED") from None
