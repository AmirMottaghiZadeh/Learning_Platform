"""Fixed authored queries measure retrieval, without supplying gold IDs to it."""
import json
from pathlib import Path
from types import SimpleNamespace
import time
from uuid import uuid4

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.ai_lab import evaluation, provider, response_cache
from apps.ai_lab.management.commands.evaluate_lexical_retrieval import DEFAULT_PLANS
from apps.ai_retrieval.models import RetrievalGeneration
from apps.ai_retrieval.retrieval import HybridRetriever


class Command(BaseCommand):
    help = "Measure full-index retrieval with authored queries; lexical by default, paid vectors only with explicit opt-in."

    def add_arguments(self, parser):
        parser.add_argument("--generation", required=True)
        parser.add_argument("--plans", default=str(DEFAULT_PLANS))
        parser.add_argument("--output", required=True)
        parser.add_argument("--semantic", action="store_true")
        parser.add_argument("--max-requests", type=int, default=20)
        parser.add_argument("--max-seconds", type=int, default=180)

    def handle(self, *args, **options):
        try:
            output = Path(options["output"])
            if output.exists() or output.is_symlink():
                raise CommandError("OUTPUT_ALREADY_EXISTS")
            plans = json.loads(Path(options["plans"]).read_text())["plans"]
            if not isinstance(plans, list) or not 1 <= len(plans) <= 100:
                raise CommandError("INVALID_PLANS")
            if not 1 <= options["max_requests"] <= 100 or not 1 <= options["max_seconds"] <= 600:
                raise CommandError("INVALID_RUN_BUDGET")
            generation = RetrievalGeneration.objects.get(pk=options["generation"])
            if not options["semantic"]:
                generation.embedding_ready = False  # Process-local diagnostic, never persisted.
            elif not generation.embedding_ready:
                raise CommandError("HYBRID_EMBEDDINGS_NOT_READY")
            dataset = evaluation.load_dataset()
            cases = {case["id"]: case for case in dataset["cases"]}
            evidence, rows = evaluation.SourceEvidence(), []
            request = SimpleNamespace(user=SimpleNamespace(pk=f"diagnostic-{uuid4()}", is_staff=True, is_authenticated=True))
            retriever = HybridRetriever(request, generation=generation)
            with provider.evaluation_budget(options["max_requests"], options["max_seconds"]) as budget:
                for plan in plans:
                    case = cases[plan["case_id"]]
                    bindings = evidence.bind(case)
                    started = time.perf_counter()
                    passages, audit = retriever.search(plan["queries"][0], question=case["question"], **{key: plan[key] for key in
                        ["lookup_kind", "audience", "intent", "keywords"] if key in plan})
                    elapsed = (time.perf_counter() - started) * 1000
                    matched = []
                    for binding in bindings:
                        found = {heading for p in passages if p.article_id == binding["article_id"]
                                 for heading in [p.section, *p.heading_path]}
                        matched.append({"article_id": binding["article_id"],
                            "article_found": any(p.article_id == binding["article_id"] for p in passages),
                            "any_heading": any(h in found for h in binding["headings"]),
                            "all_headings": all(h in found for h in binding["headings"])})
                    anchors_valid = True
                    for p in passages:
                        _, doc = evidence.article(p.article_id)
                        block = next((b for b in doc.blocks if b.paragraph_id == p.target["params"]["searchAnchor"]), None)
                        anchors_valid &= block is not None and block.text == p.text and doc.content_hash == p.content_hash
                    rows.append({"case_id": case["id"], "retrieval_ms": round(elapsed, 3), "expected": matched,
                                 "anchors_valid": anchors_valid, "audit": audit,
                                 "retrieved": [{"article_id": p.article_id, "title": p.title,
                                    "heading": p.section, "heading_path": list(p.heading_path),
                                    "anchor": p.target["params"]["searchAnchor"]} for p in passages]})
                    self.stdout.write(f"Checked {case['id']}; retrieval_ms={elapsed:.1f}; anchors={anchors_valid}")
                    if budget["exhausted"]:
                        break
            report = {"kind": "fixed_plan_hybrid_retrieval", "generation": str(generation.pk), "scope": generation.scope,
                "configuration": {"code_digest": response_cache.code_signature(),
                    "embedding_profile": generation.embedding_profile,
                    "top_k": settings.AI_LAB_HYBRID_TOP_K, "candidates": settings.AI_LAB_HYBRID_CANDIDATES,
                    "context_tokens": settings.AI_LAB_HYBRID_CONTEXT_TOKENS,
                    "regimen_enrichment": settings.AI_LAB_HYBRID_REGIMEN_ENRICHMENT,
                    "evidence_focus": settings.AI_LAB_HYBRID_EVIDENCE_FOCUS,
                    "evidence_max_passages": settings.AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES,
                    "dataset_digest": evaluation.digest(dataset), "plans_digest": evaluation.digest(plans)},
                "semantic_enabled": options["semantic"], "provider_requests": budget["used"], "cases": rows,
                "clinical_quality_assessed": False, "release_slo_verified": False,
                "summary": {"cases": len(rows), "all_anchors_valid": all(r["anchors_valid"] for r in rows),
                    "any_expected_heading_cases": sum(any(e["any_heading"] for e in r["expected"]) for r in rows),
                    "all_expected_heading_cases": sum(all(e["all_headings"] for e in r["expected"]) for r in rows),
                    "retrieval_p50_ms": evaluation.percentile([r["retrieval_ms"] for r in rows], .5),
                    "retrieval_p95_ms": evaluation.percentile([r["retrieval_ms"] for r in rows], .95)}}
            evaluation.write_private_json(output, report, secrets=tuple(provider.credentials().values()))
            self.stdout.write(json.dumps(report["summary"]))
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"HYBRID_RETRIEVAL_EVALUATION_FAILED code={getattr(exc, 'code', 'INTERNAL_ERROR')} type={type(exc).__name__}") from None
