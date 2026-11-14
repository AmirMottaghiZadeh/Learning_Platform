"""Request-local measurements. Never collect questions, passages or credentials."""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import logging
import re
import time

logger = logging.getLogger(__name__)
_current = ContextVar("reference_search_trace", default=None)
_stage = ContextVar("reference_search_stage", default="unclassified")
_attempt = ContextVar("reference_search_attempt", default=None)
STAGES = frozenset({"planning", "article_selection", "search_repair", "retrieval", "lexical_retrieval", "source_read", "extraction", "index_read",
                    "section_selection", "answering", "verification", "embedding", "cache_lookup", "cache_validation", "cache_write", "unclassified"})
TOKEN_FIELDS = ("prompt_tokens", "completion_tokens", "total_tokens")


def current_trace():
    return _current.get()


def _usage(metadata):
    raw = metadata.get("usage", {}) if isinstance(metadata, dict) else {}
    if not isinstance(raw, dict):
        return {}
    result = {}
    for name, alternate in [("prompt_tokens", "input_tokens"), ("completion_tokens", "output_tokens"),
                            ("total_tokens", "total_tokens")]:
        value = raw.get(name, raw.get(alternate))
        if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
            result[name] = value
    return result


def _error(exc):
    code = getattr(exc, "code", "INTERNAL_ERROR")
    return code if isinstance(code, str) and re.fullmatch(r"[A-Z_]{1,64}", code) else "INTERNAL_ERROR"


class Trace:
    def __init__(self, *, queue_wait_ms=0, credit_reservation_id=None):
        self.started = time.perf_counter()
        self.queue_wait_ms = max(0, queue_wait_ms)
        self.operations = {}
        self.attempts = []
        self.attempt_count = self.request_count = self.unknown_usage_requests = 0
        self.provider_elapsed_ms = 0
        self.tokens = {name: 0 for name in TOKEN_FIELDS}
        self.milestones = {}
        self.finished_ms = None
        self.outcome = "running"
        self.answer_complete = False
        self.response_cache = "bypass"
        self.credit_reservation_id = credit_reservation_id

    def elapsed(self):
        return round((time.perf_counter() - self.started) * 1000, 3)

    @contextmanager
    def activate(self):
        token = _current.set(self)
        try:
            yield self
        finally:
            _current.reset(token)

    def mark(self, name):
        if name in {"first_titles_ms", "first_sections_ms", "first_citation_ms", "first_source_ms", "first_answer_delta_ms"}:
            self.milestones.setdefault(name, self.elapsed())

    def finish(self, outcome, *, answer_complete=False):
        if self.finished_ms is None:
            self.finished_ms = self.elapsed()
            self.outcome = outcome
            self.answer_complete = outcome == "complete" and answer_complete

    def snapshot(self, *, include_attempts=True):
        elapsed = self.elapsed() if self.finished_ms is None else self.finished_ms
        result = {"schema": 1, "scope": "server_worker", "outcome": self.outcome,
                  "worker_elapsed_ms": elapsed, "queue_wait_ms": round(self.queue_wait_ms, 3),
                  "server_elapsed_ms": round(elapsed + self.queue_wait_ms, 3),
                  "machine_answer_complete": self.answer_complete,
                  "final_answer_ms": round(elapsed + self.queue_wait_ms, 3) if self.answer_complete else None,
                  "first_titles_ms": None, "first_sections_ms": None, "first_citation_ms": None,
                  "model_attempts": self.attempt_count, "provider_requests": self.request_count,
                  "provider_elapsed_ms": round(self.provider_elapsed_ms, 3),
                  "known_usage": dict(self.tokens), "unknown_usage_requests": self.unknown_usage_requests,
                  "operations": {name: dict(value) for name, value in self.operations.items()},
                  "attempts_limited": self.attempt_count > len(self.attempts)}
        result["response_cache"] = self.response_cache
        result.update({name: round(value + self.queue_wait_ms, 3) for name, value in self.milestones.items()})
        if include_attempts:
            result["attempts"] = [dict(attempt) for attempt in self.attempts]
        return result


@contextmanager
def operation(name):
    trace = _current.get()
    if trace is None:
        yield
        return
    if name not in STAGES:
        raise ValueError("Unknown measurement stage")
    token = _stage.set(name)
    started, failed = time.perf_counter(), False
    try:
        yield
    except Exception:
        failed = True
        raise
    finally:
        stats = trace.operations.setdefault(name, {"count": 0, "failed": 0, "elapsed_ms": 0})
        stats["count"] += 1
        stats["failed"] += int(failed)
        stats["elapsed_ms"] = round(stats["elapsed_ms"] + (time.perf_counter() - started) * 1000, 3)
        _stage.reset(token)


def model_call(stage, function, *args, **kwargs):
    with operation(stage):
        return function(*args, **kwargs)


@contextmanager
def model_attempt(*, max_completion_tokens=None):
    trace = _current.get()
    if trace is None:
        yield {}
        return
    event = {"stage": _stage.get(), "sent": False, "status": "ok"}
    if type(max_completion_tokens) is int and max_completion_tokens > 0:
        event["max_completion_tokens"] = max_completion_tokens
    trace.attempt_count += 1
    event["sequence"] = trace.attempt_count
    token = _attempt.set(event)
    started = time.perf_counter()
    try:
        yield event
    except Exception as exc:
        event.update(status="failed", error_code=_error(exc))
        metadata = getattr(exc, "metadata", None)
        if metadata is not None:
            event["usage"] = _usage(metadata)
        raise
    finally:
        event["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        usage = event.setdefault("usage", {})
        ticket = event.pop("_credit_ticket",None)
        if ticket is not None:
            try:
                from apps.ai_wallet.services import finish_attempt
                finish_attempt(ticket,event)
            except Exception:
                # The durable started-attempt stays uncertain and its credit
                # remains held; never guess a debit or discard a good answer.
                logger.warning("search_credit_usage_pending")
        if event["sent"]:
            trace.request_count += 1
            trace.provider_elapsed_ms += event.get("transport_ms", event["elapsed_ms"])
            trace.unknown_usage_requests += int(any(name not in usage for name in TOKEN_FIELDS))
        for name, value in usage.items():
            trace.tokens[name] += value
        if len(trace.attempts) < 256:
            trace.attempts.append(event)
        _attempt.reset(token)


def provider_request_sent():
    event = _attempt.get()
    if event is not None:
        trace = _current.get()
        if trace is not None and trace.credit_reservation_id is not None:
            from apps.ai_wallet.services import start_attempt
            event["_credit_ticket"] = start_attempt(trace.credit_reservation_id,event["sequence"],
                "embedding" if event["stage"]=="embedding" else "chat")
        event["sent"] = True


def provider_usage(metadata):
    event = _attempt.get()
    if event is not None:
        event["usage"] = _usage(metadata)
        raw = metadata.get("usage",{}) if isinstance(metadata,dict) else {}
        details = raw.get("prompt_tokens_details",raw.get("input_tokens_details",{})) if isinstance(raw,dict) else {}
        cached = details.get("cached_tokens") if isinstance(details,dict) else None
        if type(cached) is int and cached >= 0:
            event["cached_prompt_tokens"] = cached
        written = details.get("cache_write_tokens") if isinstance(details,dict) else None
        if type(written) is int and written >= 0:
            event["cache_write_prompt_tokens"] = written
        writes = details.get("cache_write_tokens_details",{}) if isinstance(details,dict) else {}
        written_12h = writes.get("ttl_12h_tokens") if isinstance(writes,dict) else None
        if type(written_12h) is int and written_12h >= 0:
            event["cache_write_12h_prompt_tokens"] = written_12h


def provider_transport_ms(elapsed):
    event = _attempt.get()
    if event is not None:
        event["transport_ms"] = round(max(0, elapsed), 3)


def provider_connection(reused):
    event = _attempt.get()
    if event is not None:
        event["connection_reused"] = bool(reused)


def mark(name):
    trace = _current.get()
    if trace is not None:
        trace.mark(name)


def log_summary(trace):
    # Only fixed field names, timings, counts, token totals and safe status codes.
    logger.info("reference_search_metrics %s", json.dumps(trace.snapshot(include_attempts=False), separators=(",", ":")))
