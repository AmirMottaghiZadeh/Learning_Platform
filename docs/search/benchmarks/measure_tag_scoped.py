"""Bounded, private-account comparison with the four existing owner questions.

Run from backend with its venv. Public output contains timings/counts only;
answers and source excerpts are written separately with mode 0600.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys
from threading import Lock
from time import perf_counter
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    parser.add_argument("--private-dir", required=True)
    parser.add_argument("--case", action="append", dest="cases")
    args = parser.parse_args()
    output = Path(args.output)
    if output.exists():
        parser.error("OUTPUT_ALREADY_EXISTS")
    import django
    django.setup()
    from django.conf import settings
    from django.db.backends.utils import CursorWrapper
    from apps.ai_lab import evaluation, hybrid_agent, provider, services, structured_agent, telemetry

    if settings.AI_LAB_SEARCH_ENGINE != "hybrid" or not settings.AI_LAB_TAG_SCOPED_SEARCH:
        parser.error("TAG_SCOPED_ENGINE_REQUIRED")
    baseline = json.loads((ROOT / "docs/search/smart-search-latency-four-user-questions-2026-11-18.json").read_text())
    cases = [r for r in baseline["runs"] if not args.cases or r["id"] in args.cases]
    if not cases or (args.cases and set(args.cases) - {r["id"] for r in cases}):
        parser.error("UNKNOWN_CASE")
    report = {"created_at_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "direct_engine_fresh_private_account_not_browser_queue_or_load_test",
        "clinical_review": "pending_owner_review", "release_slo_verified": False,
        "configuration": {"model": settings.AI_LAB_MODEL, "base_url": settings.AI_LAB_BASE_URL,
            "reasoning_effort": settings.AI_LAB_REASONING_EFFORT, "tag_scoped": True,
            "initial_fallback": settings.AI_LAB_INITIAL_SEARCH_FALLBACK,
            "embedding_model": settings.AI_LAB_EMBEDDING_MODEL,
            "dimensions": settings.AI_LAB_EMBEDDING_DIMENSIONS}, "runs": []}
    secrets = tuple(provider.credentials().values())
    for case in cases:
        request = SimpleNamespace(user=SimpleNamespace(pk=f"diagnostic-{uuid4()}", is_authenticated=True, is_staff=True))
        trace = telemetry.Trace()
        sql, events, calls, reviews = defaultdict(lambda: {"count": 0, "elapsed_ms": 0}), [], [], []
        lock, started = Lock(), perf_counter()
        execute = CursorWrapper.execute
        stream_chat = structured_agent.stream_chat
        chat = hybrid_agent.chat
        def captured(messages, **kwargs):
            item = {"messages": messages}
            calls.append(item)
            value = stream_chat(messages, **kwargs)
            item["response"] = value
            return value
        def captured_review(alias, prompt, data, *a, **kw):
            item = {"prompt": prompt, "data": data}
            reviews.append(item)
            value = chat(alias, prompt, data, *a, **kw)
            item["response"] = value
            return value
        def measured(cursor, *a, **kw):
            t = perf_counter()
            try:
                return execute(cursor, *a, **kw)
            finally:
                with lock:
                    row = sql[cursor.db.alias]
                    row["count"] += 1
                    row["elapsed_ms"] += (perf_counter() - t) * 1000
        def progress(stage):
            events.append({"stage": stage, "at_ms": round((perf_counter()-started)*1000, 3)})
            print(json.dumps({"case": case["id"], **events[-1]}), flush=True)
        result, error = None, None
        with patch.object(CursorWrapper, "execute", measured), patch.object(structured_agent, "stream_chat", captured), \
                patch.object(hybrid_agent, "chat", captured_review), provider.evaluation_budget(8, 180) as budget:
            try:
                result = services.answer(case["question"], "luna", ["uptodate"], [], request,
                    progress=progress, trace=trace)
            except Exception as exc:
                error = {"code": getattr(exc, "code", "INTERNAL_ERROR"), "type": type(exc).__name__}
        elapsed = round((perf_counter()-started)*1000, 3)
        parts = result.get("parts", []) if result else []
        row = {"id": case["id"], "elapsed_ms": elapsed, "baseline_elapsed_ms": case["elapsed_ms"],
            "status": [p["status"] for p in parts], "error": error,
            "source_count": sum(len(p["items"]) for p in parts),
            "coverage": [p["coverage"] for p in parts], "metrics": trace.snapshot(),
            "retrieval": [p["retrieval"] for p in parts], "progress": events,
            "sql": {a: {"count": v["count"], "elapsed_ms": round(v["elapsed_ms"], 3)} for a,v in sql.items()},
            "budget_used": budget["used"]}
        report["runs"].append(row)
        evaluation.write_private_json(Path(args.private_dir) / (case["id"]+".json"),
            {"question": case["question"], "result": result, "measurement": row,
                "private_model_calls": calls, "private_verifications": reviews}, secrets=secrets)
        print(json.dumps({"case": case["id"], "elapsed_ms": elapsed, "status": row["status"],
            "error": error, "provider_requests": trace.request_count}), flush=True)
    evaluation.write_private_json(output, report, secrets=secrets)
    print(json.dumps({"finished": True, "cases": len(cases), "output": str(output)}), flush=True)


if __name__ == "__main__":
    main()
