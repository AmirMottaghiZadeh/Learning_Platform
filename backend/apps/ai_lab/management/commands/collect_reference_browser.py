import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.ai_lab import evaluation, release, response_cache


class Command(BaseCommand):
    help = "Bind Chrome UI render measurements to the source and clinical-review digest; no model calls."

    def add_arguments(self, parser):
        parser.add_argument("--input", required=True)
        parser.add_argument("--output", required=True)

    def handle(self, *args, **options):
        try:
            raw = json.loads(Path(options["input"]).read_text())
            if raw.get("schema") != 1 or raw.get("kind") != "reference_browser_measurements":
                raise evaluation.EvaluationError("INVALID_BROWSER_REPORT")
            cases = {case["id"]: case for case in evaluation.load_dataset()["cases"]}
            config = {"model": settings.AI_LAB_MODEL, "base_url": settings.AI_LAB_BASE_URL,
                "reasoning_effort": settings.AI_LAB_REASONING_EFFORT, "code_digest": response_cache.code_signature(),
                "source_version": release.runtime_profile()["source_revision"]}
            evidence, rows = evaluation.SourceEvidence(), []
            for sample in raw["runs"]:
                case, job = cases[sample["case_id"]], sample["job"]
                bindings = evidence.bind(case)
                row = {"case_id": case["id"], "question": case["question"], "expect": case["expect"],
                    "category": case.get("category", "unspecified"), "expected_sources": bindings,
                    "scenario": sample["scenario"], "browser_elapsed_ms": sample["browser_elapsed_ms"],
                    "rendered_answer_complete": sample["rendered_answer_complete"], "status": job["status"], "metrics": job.get("metrics", {})}
                if job.get("result") is not None:
                    row["result"] = job["result"]
                if job.get("error"):
                    row["error_code"] = job["error"]["code"]
                row["assessment"] = evaluation.assess(case, row.get("result", {}), bindings, evidence)
                row["response_digest_schema"] = 2
                row["response_digest"] = evaluation.clinical_digest(case, bindings, config, row.get("result"), row.get("error_code"))
                rows.append(row)
            evaluation.write_private_json(options["output"], {"schema": 1, "kind": "reference_browser_load", "configuration": config,
                "served_bundle_digest": raw.get("served_bundle_digest"),
                "runtime_profile_digest": raw.get("runtime_profile_digest"), "runs": rows, "release_slo_verified": False})
            self.stdout.write(f"Source-bound browser measurements saved; samples={len(rows)}")
        except evaluation.EvaluationError as error:
            raise CommandError(str(error)) from None
        except Exception:
            raise CommandError("BROWSER_COLLECTION_FAILED") from None
