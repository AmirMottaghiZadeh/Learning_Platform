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
    return {"schema": GATE_VERSION, "code_digest": response_cache.code_signature(),
        "model": settings.AI_LAB_MODEL, "base_url": base,
        "reasoning_effort": effort.strip().lower(), "source_identity": stamp.identity,
        "source_revision": stamp.revision, "generation": str(reference_index.active_generation(stamp)),
        "lexical": settings.AI_LAB_LEXICAL_ENABLED, "local_selection": settings.AI_LAB_LOCAL_SELECTION_ENABLED,
        "preprocessed_mode": settings.AI_LAB_PREPROCESSED_MODE, "cache": settings.AI_LAB_RESPONSE_CACHE_ENABLED,
        "http_pool": settings.AI_LAB_HTTP_POOL_ENABLED, "timeout": settings.AI_LAB_TOTAL_TIMEOUT_SECONDS,
        "max_requests": settings.AI_LAB_MAX_PROVIDER_REQUESTS, "capacity": settings.AI_LAB_MAX_CONCURRENT_JOBS}


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
    if "pipeline_code_digest" in configuration:
        from . import document, http_transport, lexical, provider, retrieval, selection, services
        modules = [services, provider, http_transport, response_cache, retrieval, document, reference_index, lexical,
                   selection, evaluation, evaluation.telemetry]
        current = evaluation.digest({Path(module.__file__).name: Path(module.__file__).read_text() for module in modules})
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
