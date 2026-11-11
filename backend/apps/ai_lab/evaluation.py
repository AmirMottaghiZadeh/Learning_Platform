"""Reproducible reference-search evaluation, independent of model self-scoring."""
from collections import Counter
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
import time

from apps.uptodate import services as utd
from apps.uptodate.search_extraction import EXTRACTION_VERSION, extract_article
from . import services, telemetry

DEFAULT_DATASET = Path(__file__).parent / "benchmark" / "cases.json"


class EvaluationError(ValueError):
    pass


def digest(value):
    return sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def load_dataset(path=DEFAULT_DATASET):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or data.get("schema") != 1 or not isinstance(data.get("cases"), list):
        raise EvaluationError("INVALID_DATASET")
    if re.search(r"sk-[A-Za-z0-9_-]{16,}", json.dumps(data)):
        raise EvaluationError("CREDENTIAL_IN_DATASET")
    cases, seen = data["cases"], set()
    if not 1 <= len(cases) <= 500:
        raise EvaluationError("INVALID_CASE_COUNT")
    for case in cases:
        if not isinstance(case, dict):
            raise EvaluationError("INVALID_CASE")
        identifier, question = case.get("id"), case.get("question")
        if not isinstance(identifier, str) or not re.fullmatch(r"[a-z0-9_-]{1,80}", identifier) or identifier in seen:
            raise EvaluationError("INVALID_CASE_ID")
        seen.add(identifier)
        if not isinstance(question, str) or not 3 <= len(question) <= 1500:
            raise EvaluationError("INVALID_QUESTION")
        if case.get("expect") not in {"answerable", "abstain"}:
            raise EvaluationError("INVALID_EXPECTATION")
        history = case.get("history", [])
        if not isinstance(history, list) or len(history) > 4 or any(not isinstance(q, str) or len(q) > 1500 for q in history):
            raise EvaluationError("INVALID_HISTORY")
        expected = case.get("expected", [])
        if not isinstance(expected, list) or (case["expect"] == "answerable" and not expected) or (case["expect"] == "abstain" and expected):
            raise EvaluationError("INVALID_EXPECTED_SOURCES")
        for source in expected:
            headings = source.get("headings", [source.get("heading")]) if isinstance(source, dict) else []
            if (not isinstance(source, dict) or not re.fullmatch(r"\d{1,12}", str(source.get("article_id", "")))
                    or not isinstance(headings, list) or not headings or any(not isinstance(h, str) or not h for h in headings)
                    or type(source.get("part_index", 0)) is not int or not 0 <= source.get("part_index", 0) <= 2):
                raise EvaluationError("INVALID_EXPECTED_SOURCE")
    return data


class SourceEvidence:
    """Only reads the source. No new index and no change to normal app search."""
    def __init__(self):
        self.articles = {}

    def article(self, identifier):
        identifier = str(identifier)
        if identifier not in self.articles:
            article = utd.get_topic(identifier)
            if article is None:
                raise EvaluationError("EXPECTED_ARTICLE_MISSING")
            extracted = extract_article(identifier, article["body_html"])
            self.articles[identifier] = (article, extracted)
        return self.articles[identifier]

    def bind(self, case):
        sources = []
        for expected in case.get("expected", []):
            identifier = str(expected["article_id"])
            article, extracted = self.article(identifier)
            # Exact headings, not a model's output, bind the expected source.
            headings = expected.get("headings", [expected.get("heading")])
            blocks = [block for block in extracted.blocks if block.section_title in headings
                      and 40 <= len(block.text) <= 6000 and block.table_context_status != "complex_review"]
            if not blocks or any(not any(block.section_title == heading for block in blocks) for heading in headings):
                raise EvaluationError("EXPECTED_SECTION_MISSING")
            sources.append({"part_index": expected.get("part_index", 0), "article_id": identifier,
                            "title": article["title"], "headings": headings,
                            "content_hash": extracted.content_hash, "source_version": article["version"],
                            "extraction_version": EXTRACTION_VERSION,
                            "paragraph_ids": [block.paragraph_id for block in blocks]})
        return sources

    def citation_valid(self, citation):
        try:
            target = citation["target"]
            params = target["params"]
            identifier = str(params["id"])
            if target["screen"] != "uptodateArticle" or citation["source"] != "uptodate":
                return False
            _, extracted = self.article(identifier)
            if citation["content_hash"] != extracted.content_hash or params["searchContentHash"] != extracted.content_hash:
                return False
            return any(block.paragraph_id == params["searchAnchor"] and block.text == citation["quote"]
                       and block.section_id == params.get("sectionId", "") for block in extracted.blocks)
        except (KeyError, TypeError, EvaluationError):
            return False


def assess(case, result, bindings, evidence):
    parts = result.get("parts", [])
    expected_parts = max((source.get("part_index", 0) for source in case.get("expected", [])), default=0) + 1
    complete = bool(parts) and len(parts) == expected_parts and all(part.get("status") == "answered" and part.get("items") for part in parts)
    citations = [(index, citation) for index, part in enumerate(parts) for citation in part.get("items", [])]
    integrity = bool(citations) and all(evidence.citation_valid(citation) for _, citation in citations)
    matches = []
    for binding in bindings:
        matched = any(index == binding["part_index"] and
                      str(citation.get("target", {}).get("params", {}).get("id")) == binding["article_id"] and
                      citation.get("target", {}).get("params", {}).get("searchAnchor") in binding["paragraph_ids"]
                      for index, citation in citations)
        matches.append(matched)
    abstained = not citations and all(part.get("status") == "not_found" for part in parts)
    return {"machine_complete": bool(complete), "citation_integrity": integrity,
            "expected_sources_matched": bool(matches) and all(matches), "source_matches": matches,
            "abstained": abstained, "citation_count": len(citations),
            "clinical_review": "pending", "correct_and_sufficient": None}


def clinical_digest(case, bindings, configuration, result=None, error_code=None):
    """Bind reviews to clinical content, not timing/cache/traffic metadata."""
    profile = {key: configuration.get(key) for key in ["model", "base_url", "reasoning_effort", "snapshot_version",
        "source_version", "pipeline_code_digest", "code_digest", "prompt_digest", "lexical_version", "selection_version"]}
    parts = [{key: part.get(key) for key in ["question_fa", "status", "clarification_fa", "overview_fa", "items"]}
             for part in (result or {}).get("parts", [])]
    return digest({"schema": 2, "case": case, "bindings": bindings, "configuration": profile,
                   "parts": parts, "error_code": error_code})


def run_case(case, bindings, evidence, configuration, *, budget=None, request=None):
    trace = telemetry.Trace()
    row = {"case_id": case["id"], "category": case.get("category", "unspecified"),
           "expect": case["expect"], "question": case["question"], "expected_sources": bindings}
    started = time.perf_counter()
    try:
        result = services.answer(case["question"], "luna", ["uptodate"], case.get("history", []), request, trace=trace)
        row.update(status="complete", result=result, assessment=assess(case, result, bindings, evidence))
    except Exception as exc:
        trace.finish("failed")
        code = getattr(exc, "code", "EVALUATION_FAILED")
        if not isinstance(code, str) or not re.fullmatch(r"[A-Z_]{1,64}", code):
            code = "EVALUATION_FAILED"
        row.update(status="failed", error_code=code, assessment={"clinical_review": "pending", "correct_and_sufficient": None})
    row["metrics"] = trace.snapshot()
    row["evaluation_wall_ms"] = round((time.perf_counter() - started) * 1000, 3)
    row["evaluation_budget_exhausted"] = bool(budget and budget["exhausted"])
    row["response_digest_schema"] = 2
    row["response_digest"] = clinical_digest(case, bindings, configuration, row.get("result"), row.get("error_code"))
    return row


def apply_reviews(rows, reviews):
    if not isinstance(reviews, dict) or reviews.get("schema") != 1 or not isinstance(reviews.get("reviews"), list):
        raise EvaluationError("INVALID_REVIEWS")
    lookup = {}
    for review in reviews["reviews"]:
        if (not isinstance(review, dict) or type(review.get("correct_and_sufficient")) is not bool
                or not isinstance(review.get("reviewer"), str) or not review["reviewer"].strip()
                or not isinstance(review.get("response_digest"), str)):
            raise EvaluationError("INVALID_REVIEW")
        alternative = review.get("accept_alternative_sources", False)
        if type(alternative) is not bool or (alternative and (not isinstance(review.get("source_review_reason"), str)
                or len(review["source_review_reason"].strip()) < 15)):
            raise EvaluationError("INVALID_SOURCE_REVIEW")
        key = (review.get("case_id"), review["response_digest"])
        if key in lookup:
            raise EvaluationError("DUPLICATE_REVIEW")
        lookup[key] = review
    for row in rows:
        row.setdefault("assessment", {}).update(clinical_review="pending", correct_and_sufficient=None,
                                               alternative_sources_accepted=False)
        row["assessment"].pop("reviewer", None)
        row["assessment"].pop("source_review_reason", None)
        review = lookup.get((row["case_id"], row["response_digest"]))
        if review is not None:
            row["assessment"].update(clinical_review="approved" if review["correct_and_sufficient"] else "rejected",
                                     correct_and_sufficient=review["correct_and_sufficient"], reviewer=review["reviewer"],
                                     alternative_sources_accepted=review.get("accept_alternative_sources", False),
                                     source_review_reason=review.get("source_review_reason", ""))


def percentile(values, fraction):
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * fraction) - 1)]


def summarize(rows, *, target_ms=20000, expected_suite_size=None):
    answerable = [row for row in rows if row["expect"] == "answerable"]
    completed, qualified = [], []
    for row in answerable:
        assessment = row.get("assessment", {})
        if row["status"] == "complete" and assessment.get("machine_complete") and not row.get("evaluation_budget_exhausted"):
            completed.append(row)
            if (assessment.get("citation_integrity") and (assessment.get("expected_sources_matched") or assessment.get("alternative_sources_accepted"))
                    and assessment.get("correct_and_sufficient") is True):
                qualified.append(row)
    measured = [row["metrics"]["server_elapsed_ms"] for row in completed]
    within = [row for row in qualified if row["metrics"]["server_elapsed_ms"] < target_ms]
    machine_within = [row for row in completed if row["metrics"]["server_elapsed_ms"] < target_ms]
    pending = sum(row.get("assessment", {}).get("correct_and_sufficient") is None for row in answerable)
    counts = Counter(row["status"] for row in rows)
    groups = {}
    for category in sorted({row["category"] for row in rows}):
        group = [row for row in rows if row["category"] == category]
        groups[category] = {"cases": len(group), "failed": sum(row["status"] == "failed" for row in group),
                            "machine_complete": sum(bool(row.get("assessment", {}).get("machine_complete")) for row in group)}
    known = {field: sum(row.get("metrics", {}).get("known_usage", {}).get(field, 0) for row in rows)
             for field in telemetry.TOKEN_FIELDS}
    abstentions = [row for row in rows if row["expect"] == "abstain"]
    return {"scope": "service_baseline_not_browser_latency", "target_ms": target_ms,
            "cases": len(rows), "answerable_cases": len(answerable), "status_counts": dict(counts),
            "machine_complete": len(completed), "clinically_reviewed_complete": len(qualified),
            "machine_complete_under_target": len(machine_within),
            "quality_verified_under_target": len(within),
            "quality_verified_success_rate": len(within) / len(answerable) if answerable else None,
            "pending_clinical_reviews": pending,
            "abstention_cases": len(abstentions),
            "structurally_correct_abstentions": sum(row["status"] == "complete" and row.get("assessment", {}).get("abstained", False) for row in abstentions),
            "complete_answer_latency_ms": {"p50": percentile(measured, .5), "p95": percentile(measured, .95)},
            "known_usage": known,
            "unknown_usage_requests": sum(row.get("metrics", {}).get("unknown_usage_requests", 0) for row in rows),
            "provider_requests": sum(row.get("metrics", {}).get("provider_requests", 0) for row in rows),
            "provisional_service_target_met": bool(answerable) and not pending and len(within) / len(answerable) >= .95,
            "full_suite_measured": expected_suite_size is not None and len({row["case_id"] for row in rows}) == expected_suite_size,
            "release_slo_verified": False, "categories": groups}


def write_private_json(path, value, *, secrets=()):
    text = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    if re.search(r"sk-[A-Za-z0-9_-]{16,}", text) or any(secret and secret in text for secret in secrets):
        raise EvaluationError("CREDENTIAL_IN_REPORT")
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Never truncate existing reports or follow a destination symlink.
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as handle:
        handle.write(text)


def append_private_journal(handle, value, *, secrets=()):
    text = json.dumps(value, ensure_ascii=False) + "\n"
    if re.search(r"sk-[A-Za-z0-9_-]{16,}", text) or any(secret and secret in text for secret in secrets):
        raise EvaluationError("CREDENTIAL_IN_REPORT")
    handle.write(text)
    handle.flush()
    os.fsync(handle.fileno())


def load_baseline(path):
    text = Path(path).read_text()
    try:
        report = json.loads(text)
    except json.JSONDecodeError:
        lines = text.splitlines()
        header = json.loads(lines[0])
        if header.get("kind") != "reference_search_baseline_journal":
            raise EvaluationError("INVALID_BASELINE_REPORT")
        rows = []
        for index, line in enumerate(lines[1:]):
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                # A killed process may leave its last journal line incomplete.
                if index != len(lines) - 2:
                    raise EvaluationError("INVALID_BASELINE_JOURNAL") from None
        report = {**header, "kind": "reference_search_baseline", "runs": rows, "recovered_from_journal": True}
    if isinstance(report, dict) and report.get("kind") == "reference_search_baseline_journal":
        report.update(kind="reference_search_baseline", runs=[], recovered_from_journal=True)
    if not isinstance(report, dict) or report.get("kind") != "reference_search_baseline" or not isinstance(report.get("runs"), list):
        raise EvaluationError("INVALID_BASELINE_REPORT")
    return report
