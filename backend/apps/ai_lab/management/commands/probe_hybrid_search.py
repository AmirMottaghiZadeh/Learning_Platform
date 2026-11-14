"""A bounded paid diagnostic; pilot generations are never exposed to the app."""
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4
import re

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.ai_lab import evaluation, hybrid_agent, provider, telemetry, response_cache
from apps.ai_retrieval.models import RetrievalGeneration
from apps.ai_retrieval.retrieval import HybridRetriever
from apps.ai_lab.streaming import endpoint


class Command(BaseCommand):
    help = "Run one bounded hybrid question and save a private clinical-review report. Not an SLO certification."

    def add_arguments(self, parser):
        parser.add_argument("--generation", required=True)
        parser.add_argument("--question", required=True)
        parser.add_argument("--output", required=True)
        parser.add_argument("--max-requests", type=int, default=6)
        parser.add_argument("--max-seconds", type=int, default=120)
        parser.add_argument("--include-draft", action="store_true", help="Save unverified draft and retrieved evidence ONLY in the private diagnostic report.")

    def handle(self, *args, **options):
        try:
            output = Path(options["output"])
            if output.exists() or output.is_symlink():
                raise CommandError("OUTPUT_ALREADY_EXISTS")
            if (not 1 <= options["max_requests"] <= 12 or not 1 <= options["max_seconds"] <= 300
                    or not 3 <= len(options["question"]) <= 1500):
                raise CommandError("INVALID_PROBE_BUDGET")
            if re.search(r"sk-[A-Za-z0-9_-]{16,}", options["question"]):
                raise CommandError("CREDENTIAL_TEXT_REJECTED")
            generation = RetrievalGeneration.objects.get(pk=options["generation"])
            request = SimpleNamespace(user=SimpleNamespace(pk=f"diagnostic-{uuid4()}", is_staff=True, is_authenticated=True))
            retriever = HybridRetriever(request, generation=generation)
            configuration = {"engine":"hybrid","hybrid_generation":str(generation.pk),
                "model":settings.AI_LAB_MODEL,"base_url":endpoint().removesuffix("/chat/completions"),
                "reasoning_effort":settings.AI_LAB_REASONING_EFFORT if settings.AI_LAB_REASONING_EFFORT is not None else settings.AI_LAB_LUNA_REASONING_EFFORT,
                "embedding_profile":generation.embedding_profile,"semantic_ready":generation.embedding_ready,
                "local_lexical_pilot":settings.AI_LAB_LOCAL_LEXICAL_PILOT,
                "top_k":settings.AI_LAB_HYBRID_TOP_K,"candidates":settings.AI_LAB_HYBRID_CANDIDATES,
                "context_tokens":settings.AI_LAB_HYBRID_CONTEXT_TOKENS,
                "max_search_rounds":settings.AI_LAB_HYBRID_MAX_SEARCH_ROUNDS,
                "regimen_enrichment":settings.AI_LAB_HYBRID_REGIMEN_ENRICHMENT,
                "evidence_focus":settings.AI_LAB_HYBRID_EVIDENCE_FOCUS,
                "evidence_max_passages":settings.AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES,
                "answer_drafts":settings.AI_LAB_STREAM_ANSWER_DRAFTS,"executor":settings.AI_LAB_EXECUTOR,
                "code_digest":response_cache.code_signature()}
            trace = telemetry.Trace()
            result, error, complete = None, None, False
            drafts, evidence = {}, {}
            def observe_event(event):
                key=str(event.get("part_index",0))
                if event["type"]=="answer_delta":drafts[key]=drafts.get(key,"")+event["text"]
                elif event["type"]=="answer_reset":drafts[key]=""
            def source_event(event):
                for citation in event["citations"]:
                    evidence[f"{event['part_index']}:{citation['source_id']}"]=citation
            with provider.evaluation_budget(options["max_requests"], options["max_seconds"]) as budget, trace.activate():
                try:
                    result = hybrid_agent.answer_hybrid(options["question"], [], request, retriever=retriever,
                        on_event=observe_event if options["include_draft"] else lambda _:None,
                        publish=source_event if options["include_draft"] else lambda _:None)
                    complete = bool(result["parts"]) and all(p["status"] == "answered" and p["items"] for p in result["parts"])
                    trace.finish("complete", answer_complete=complete)
                except provider.ProviderError as exc:
                    error = exc.code
                    trace.finish("failed")
            report = {"kind": "hybrid_pilot_probe", "generation": str(generation.pk), "scope": generation.scope,
                "configuration":configuration,
                "question": options["question"], "result": result, "error_code": error, "metrics": trace.snapshot(),
                "model": settings.AI_LAB_MODEL, "budget": {"max_requests": options["max_requests"], "used": budget["used"],
                    "max_seconds": options["max_seconds"], "exhausted": budget["exhausted"]},
                "clinical_review": "pending", "release_slo_verified": False}
            if options["include_draft"]:
                report.update(unverified_drafts=drafts,retrieved_evidence=evidence)
            evaluation.write_private_json(output, report, secrets=tuple(provider.credentials().values()))
            self.stdout.write(f"Probe finished; outcome={trace.outcome}; machine_answer_complete={complete}; elapsed_ms={trace.snapshot()['worker_elapsed_ms']}; requests={budget['used']}; clinical_review=pending.")
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"HYBRID_PROBE_FAILED code={getattr(exc, 'code', 'INTERNAL_ERROR')} type={type(exc).__name__}") from None
