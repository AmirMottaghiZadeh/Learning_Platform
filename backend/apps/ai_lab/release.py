"""Response-bound quality/performance gates and signed, expiring cohort approval."""
from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
import math
import re
from pathlib import Path
import time
from urllib.parse import urlsplit

from django.conf import settings
from django.utils.crypto import constant_time_compare, salted_hmac

from . import evaluation, reference_index, response_cache

GATE_VERSION = 1
HYBRID_CONFIGURATION_KEYS = (
    "engine", "hybrid_generation", "embedding_profile", "semantic_ready", "local_lexical_pilot",
    "top_k", "candidates", "context_tokens", "max_search_rounds", "regimen_enrichment", "answer_drafts", "executor",
    "evidence_focus", "evidence_max_passages",
)


def frontend_digest():
    configured = settings.AI_LAB_FRONTEND_BUNDLE_SHA256
    if configured:
        return configured if re.fullmatch(r"[a-f0-9]{64}", configured) else None
    files = list((Path(__file__).resolve().parents[3] / "frontend/dist/_expo/static/js/web").glob("index-*.js"))
    return sha256(files[0].read_bytes()).hexdigest() if len(files) == 1 else None


def runtime_profile():
    stamp = reference_index.source_stamp()
    base = settings.AI_LAB_BASE_URL.strip().rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise evaluation.EvaluationError("INVALID_PROVIDER_URL")
    effort = settings.AI_LAB_REASONING_EFFORT
    if effort is None:
        effort = settings.AI_LAB_LUNA_REASONING_EFFORT
    profile = {"schema": GATE_VERSION, "code_digest": response_cache.code_signature(),
        "model": settings.AI_LAB_MODEL, "base_url": base,
        "reasoning_effort": effort.strip().lower(), "source_identity": stamp.identity,
        "source_revision": stamp.revision, "generation": str(reference_index.active_generation(stamp)),
        "lexical": settings.AI_LAB_LEXICAL_ENABLED, "local_selection": settings.AI_LAB_LOCAL_SELECTION_ENABLED,
        "preprocessed_mode": settings.AI_LAB_PREPROCESSED_MODE, "cache": settings.AI_LAB_RESPONSE_CACHE_ENABLED,
        "http_pool": settings.AI_LAB_HTTP_POOL_ENABLED, "timeout": None,
        "max_requests": settings.AI_LAB_OUTLINE_MAX_PROVIDER_REQUESTS, "capacity": settings.AI_LAB_MAX_CONCURRENT_JOBS, "pipeline": "outline-v1"}
    profile["engine"] = settings.AI_LAB_SEARCH_ENGINE
    if settings.AI_LAB_SEARCH_ENGINE == "hybrid":
        from apps.ai_retrieval import embeddings
        from apps.ai_retrieval.models import RetrievalHead
        head = RetrievalHead.objects.filter(source_identity=stamp.identity).select_related("active").first()
        profile.update(pipeline="hybrid-v1", hybrid_generation=str(head.active_id) if head else None,
            semantic_ready=bool(head and head.active and head.active.embedding_ready),
            local_lexical_pilot=settings.AI_LAB_LOCAL_LEXICAL_PILOT,
            embedding_profile=embeddings.profile(), top_k=settings.AI_LAB_HYBRID_TOP_K,
            candidates=settings.AI_LAB_HYBRID_CANDIDATES,
            context_tokens=settings.AI_LAB_HYBRID_CONTEXT_TOKENS,
            max_search_rounds=settings.AI_LAB_HYBRID_MAX_SEARCH_ROUNDS, executor=settings.AI_LAB_EXECUTOR,
            regimen_enrichment=settings.AI_LAB_HYBRID_REGIMEN_ENRICHMENT,
            evidence_focus=settings.AI_LAB_HYBRID_EVIDENCE_FOCUS,
            evidence_max_passages=settings.AI_LAB_HYBRID_EVIDENCE_MAX_PASSAGES,
            answer_drafts=settings.AI_LAB_STREAM_ANSWER_DRAFTS)
    return profile


def _sign(payload):
    return salted_hmac("ai-lab-release-approval", json.dumps(payload, sort_keys=True), algorithm="sha256").hexdigest()


def approval(report, *, hours=24):
    if report.get("decision") != "pass" or not 0 < hours <= 72:
        raise evaluation.EvaluationError("RELEASE_GATE_NOT_PASSED")
    payload = {"schema": GATE_VERSION, "profile_digest": evaluation.digest(runtime_profile()),
               "frontend_digest": report.get("frontend_bundle_digest"),
               "report_digest": evaluation.digest(report), "issued_at": time.time(), "expires_at": time.time() + hours * 3600}
    return {"payload": payload, "signature": _sign(payload)}


@lru_cache(maxsize=8)
def _approved(path, size, mtime_ns, inode, bucket):
    try:
        file = Path(path)
        if size > 100000 or file.stat().st_mode & 0o077:
            return False
        record = json.loads(file.read_text())
        payload = record["payload"]
        now = time.time()
        valid = (payload.get("schema") == GATE_VERSION and constant_time_compare(record["signature"], _sign(payload))
            and payload["issued_at"] <= now < payload["expires_at"] <= payload["issued_at"] + 72 * 3600
            and payload["profile_digest"] == evaluation.digest(runtime_profile()))
        valid = valid and payload.get("frontend_digest") is not None and payload["frontend_digest"] == frontend_digest()
        return payload["expires_at"] if valid else 0
    except Exception:
        return False


def approved():
    try:
        path = settings.AI_LAB_RELEASE_APPROVAL_FILE
        if not path:
            return False
        stat = Path(path).stat()
        expires = _approved(path, stat.st_size, stat.st_mtime_ns, stat.st_ino, int(time.time() // 10))
        return bool(expires and time.time() < expires)
    except OSError:
        return False


def cohort(user):
    percent = settings.AI_LAB_ROLLOUT_PERCENT
    if not 0 < percent <= 100 or not approved():
        return False
    value = salted_hmac("ai-lab-rollout-cohort", str(user.pk), algorithm="sha256").hexdigest()
    return int(value[:8], 16) % 100 < percent


def checked_rows(rows, dataset, configuration, evidence, reviews):
    cases = {case["id"]: case for case in dataset["cases"]}
    result = deepcopy(rows)
    for row in result:
        case = cases.get(row.get("case_id"))
        if case is None or row.get("response_digest_schema") != 2:
            raise evaluation.EvaluationError("UNBOUND_RELEASE_RESPONSE")
        binding = evidence.bind(case)
        if row.get("expected_sources") != binding or row.get("response_digest") != evaluation.clinical_digest(
                case, binding, configuration, row.get("result"), row.get("error_code")):
            raise evaluation.EvaluationError("RELEASE_RESPONSE_CHANGED")
        row.update(expect=case["expect"], category=case.get("category", "unspecified"))
        row["assessment"] = evaluation.assess(case, row.get("result", {}), binding, evidence)
    evaluation.apply_reviews(result, reviews)
    return result


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0


def configuration_current(configuration, profile):
    if configuration.get("model") != profile.get("model"):
        return False
    for key in ["base_url", "reasoning_effort"]:
        if key in profile and str(configuration.get(key, "")).strip().rstrip("/") != str(profile[key]).strip().rstrip("/"):
            return False
    if profile.get("engine") == "hybrid" and any(configuration.get(key) != profile.get(key)
            for key in HYBRID_CONFIGURATION_KEYS):
        return False
    if "pipeline_code_digest" in configuration:
        from . import document, outline, http_transport, lexical, provider, retrieval, selection, services
        modules = [services, provider, http_transport, response_cache, retrieval, document, reference_index, lexical,
                   selection, evaluation, evaluation.telemetry, outline]
        if profile.get("engine") == "hybrid":
            from . import hybrid_agent, streaming, transport_pool
            from apps.ai_retrieval import embeddings, chunking, vectors, indexing, evidence, retrieval as hybrid_retrieval
            if (configuration.get("engine") != "hybrid" or configuration.get("hybrid_generation") != profile.get("hybrid_generation")
                    or configuration.get("embedding_profile") != profile.get("embedding_profile")):
                return False
            modules += [hybrid_agent, streaming, transport_pool, embeddings, chunking, vectors, indexing, evidence, hybrid_retrieval]
        current = evaluation.digest({(module.__name__ if profile.get("engine") == "hybrid" else Path(module.__file__).name):
            Path(module.__file__).read_text() for module in modules})
        return configuration["pipeline_code_digest"] == current
    return configuration.get("code_digest") == profile.get("code_digest")


def _qualified(row, elapsed):
    assessment = row.get("assessment", {})
    return (row.get("status") == "complete" and _number(elapsed) and elapsed < 20000
        and assessment.get("machine_complete") and assessment.get("citation_integrity")
        and (assessment.get("expected_sources_matched") or assessment.get("alternative_sources_accepted"))
        and assessment.get("correct_and_sufficient") is True and not row.get("evaluation_budget_exhausted"))


def evaluate_gate(suite, load, browser, reviews, *, dataset=None, evidence=None, min_api=20, min_browser=10):
    dataset = dataset or evaluation.load_dataset()
    evidence = evidence or evaluation.SourceEvidence()
    blockers = []
    profile = runtime_profile()
    if profile.get("generation") == "None":
        blockers.append("PREPARED_INDEX_REQUIRED")
    if profile.get("engine") == "hybrid":
        if not profile.get("semantic_ready"):
            blockers.append("HYBRID_EMBEDDINGS_REQUIRED")
        if profile.get("local_lexical_pilot"):
            blockers.append("LOCAL_PILOT_NOT_RELEASABLE")
    if not configuration_current(suite["configuration"], profile):
        blockers.append("SUITE_RUNTIME_CHANGED")
    suite_rows = checked_rows(suite["runs"], dataset, suite["configuration"], evidence, reviews)
    expected = {case["id"] for case in dataset["cases"]}
    seen = [row["case_id"] for row in suite_rows]
    if set(seen) != expected or len(seen) != len(expected):
        blockers.append("FULL_SUITE_REQUIRED")
    answerable = [row for row in suite_rows if row["expect"] == "answerable"]
    passed = sum(_qualified(row, row.get("metrics", {}).get("server_elapsed_ms"))
                 and row.get("metrics", {}).get("response_cache") != "hit" for row in answerable)
    if not answerable or passed / len(answerable) < .95:
        blockers.append("QUALITY_AND_SERVICE_TARGET_NOT_MET")
    pending = sum(row["assessment"].get("correct_and_sufficient") is None for row in suite_rows)
    if pending:
        blockers.append("INDEPENDENT_REVIEW_REQUIRED")
    abstentions = [row for row in suite_rows if row["expect"] == "abstain"]
    if any(row["status"] != "complete" or not row["assessment"].get("abstained")
           or row["assessment"].get("correct_and_sufficient") is not True for row in abstentions):
        blockers.append("ABSTENTION_CHECK_FAILED")
    traffic = {}
    profile_digest = evaluation.digest(profile)
    for name, report, minimum, latency in [("api", load, min_api, "client_elapsed_ms"),
                                           ("browser", browser, min_browser, "browser_elapsed_ms")]:
        if not report:
            blockers.append(f"{name.upper()}_EVIDENCE_REQUIRED")
            continue
        if report.get("runtime_profile_digest") != profile_digest:
            blockers.append(f"{name.upper()}_RUNTIME_CHANGED")
        if not configuration_current(report["configuration"], profile):
            blockers.append(f"{name.upper()}_CONFIGURATION_CHANGED")
        if name == "browser" and (not frontend_digest() or report.get("served_bundle_digest") != frontend_digest()):
            blockers.append("BROWSER_BUILD_CHANGED")
        rows = checked_rows(report.get("runs", []), dataset, report["configuration"], evidence, reviews)
        groups = {}
        for scenario in ["cold", "hit"]:
            group = [row for row in rows if row.get("scenario") == scenario and row["expect"] == "answerable"]
            success = [row for row in group if _qualified(row, row.get(latency))
                       and (scenario != "cold" or row.get("metrics", {}).get("response_cache") != "hit")
                       and (scenario != "hit" or (row.get("metrics", {}).get("response_cache") == "hit"
                                                  and row["metrics"].get("provider_requests") == 0))
                       and (name != "browser" or row.get("rendered_answer_complete") is True)]
            groups[scenario] = {"samples": len(group), "qualified_under_20s": len(success),
                "p95_machine_complete_ms": evaluation.percentile([row[latency] for row in group if row.get("status") == "complete"
                    and row.get("assessment", {}).get("machine_complete") and _number(row.get(latency))], .95)}
            if len(group) < minimum or len(success) / max(1, len(group)) < .95:
                blockers.append(f"{name.upper()}_{scenario.upper()}_TARGET_NOT_MET")
            if len({row["case_id"] for row in group}) < minimum:
                blockers.append(f"{name.upper()}_{scenario.upper()}_COVERAGE_REQUIRED")
        if name == "api" and (report.get("concurrency", 0) < settings.AI_LAB_MAX_CONCURRENT_JOBS
                or report.get("observed_workers", 0) < 2 or not report.get("shared_cache")):
            blockers.append("SHARED_MULTIWORKER_LOAD_REQUIRED")
        traffic[name] = groups
    return {"schema": GATE_VERSION, "decision": "blocked" if blockers else "pass", "blockers": blockers,
        "frontend_bundle_digest": browser.get("served_bundle_digest") if browser else None,
        "runtime_profile_digest": profile_digest, "suite_cases": len(suite_rows), "expected_cases": len(expected),
        "answerable_cases": len(answerable), "quality_verified_under_20s": passed,
        "pending_reviews": pending, "traffic": traffic, "release_slo_verified": not blockers}
