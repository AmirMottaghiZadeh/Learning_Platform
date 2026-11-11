"""Server-only Chat Completions adapter. Never expose bodies or credentials."""
import json
from http.client import HTTPException
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener as _urllib_opener, getproxies

from django.conf import settings
from django.views.decorators.debug import sensitive_variables

from . import telemetry
from . import http_transport

# Stable wire alias for existing clients/jobs, independent of the upstream model.
MODEL_ALIASES = ("luna",)
deadline = ContextVar("ai_lab_deadline", default=None)
_evaluation_budget = ContextVar("reference_evaluation_budget", default=None)
_request_budget = ContextVar("reference_request_budget", default=None)


class ProviderError(Exception):
    def __init__(self, code, status=0):
        self.code, self.status = code, status
        super().__init__(code)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def build_opener(*handlers):
    # Preserve explicitly configured HTTPS/ALL proxy routing. The direct pool
    # never bypasses a proxy to send credentials along a different route.
    proxies = getproxies()
    pooled = settings.AI_LAB_HTTP_POOL_ENABLED and not (proxies.get("https") or proxies.get("all"))
    return http_transport.opener() if pooled else _urllib_opener(*handlers)


def check_deadline(*, minimum=0):
    remaining = None if deadline.get() is None else deadline.get() - time.monotonic()
    if remaining is not None and remaining <= minimum:
        raise ProviderError("EXPERIMENT_TIMEOUT")
    return remaining


@contextmanager
def request_budget():
    token = _request_budget.set({"used": 0, "limit": settings.AI_LAB_MAX_PROVIDER_REQUESTS})
    try:
        yield
    finally:
        _request_budget.reset(token)


@contextmanager
def evaluation_budget(max_requests, max_seconds):
    """Bound paid requests in an explicit benchmark; never enabled by app traffic."""
    budget = {"max_requests": max_requests, "used": 0,
              "deadline": time.monotonic() + max_seconds, "exhausted": False}
    token = _evaluation_budget.set(budget)
    try:
        yield budget
    finally:
        _evaluation_budget.reset(token)


def configured_models():
    return {alias: settings.AI_LAB_MODEL for alias in MODEL_ALIASES}


@sensitive_variables()
def credentials():
    keys = {"luna": settings.AI_LAB_API_KEY or settings.AI_LAB_LUNA_API_KEY}
    if settings.AI_LAB_CREDENTIALS_FILE and not all(keys.values()):
        path = Path(settings.AI_LAB_CREDENTIALS_FILE)
        try:
            if path.stat().st_mode & 0o077:
                raise ProviderError("CREDENTIAL_FILE_PERMISSIONS")
            text = path.read_text()
        except OSError:
            raise ProviderError("CREDENTIAL_FILE_UNAVAILABLE") from None
        label = ""
        for line in text.splitlines():
            match = re.search(r"sk-[A-Za-z0-9_-]{16,}", line)
            if match:
                alias = next((name for name in MODEL_ALIASES if name in label), None)
                if alias and not keys[alias]:
                    keys[alias] = match.group()
            elif line.strip():
                label = line.lower()
    return keys


@sensitive_variables()
def call(alias, payload):
    if alias not in MODEL_ALIASES:
        raise ProviderError("MODEL_NOT_SUPPORTED")
    model = configured_models()[alias]
    if not isinstance(model, str) or not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,120}", model):
        raise ProviderError("INVALID_MODEL_CONFIGURATION")
    key = credentials().get(alias)
    if not key:
        raise ProviderError("KEY_NOT_CONFIGURED")
    base = settings.AI_LAB_BASE_URL.strip().rstrip("/")
    try:
        parsed = urlsplit(base)
        invalid_port = parsed.port is not None and not 1 <= parsed.port <= 65535
    except ValueError:
        raise ProviderError("INVALID_PROVIDER_URL") from None
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or invalid_port or re.search(r"\s", base)):
        raise ProviderError("INVALID_PROVIDER_URL")
    payload = {**payload, "model": model}
    request = Request(base + "/chat/completions", data=json.dumps(payload, ensure_ascii=False).encode(),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    timeout = settings.AI_LAB_TIMEOUT_SECONDS
    remaining = check_deadline(minimum=settings.AI_LAB_MIN_CALL_BUDGET_SECONDS)
    if remaining is not None:
        timeout = min(timeout, remaining)
    request_limit = _request_budget.get()
    if request_limit is not None and request_limit["used"] >= request_limit["limit"]:
        raise ProviderError("SEARCH_REQUEST_LIMIT")
    budget = _evaluation_budget.get()
    if budget is not None:
        remaining = budget["deadline"] - time.monotonic()
        if budget["used"] >= budget["max_requests"] or remaining <= 0:
            budget["exhausted"] = True
            raise ProviderError("EVALUATION_BUDGET_EXCEEDED")
        timeout = min(timeout, remaining)
        budget["used"] += 1
    if request_limit is not None:
        request_limit["used"] += 1
    try:
        telemetry.provider_request_sent()
        with build_opener(NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
        check_deadline()
        if len(raw) > 2_000_000:
            raise ProviderError("RESPONSE_TOO_LARGE")
        # An upstream echo cannot leak keys through answers, usage, or debug metadata.
        text = raw.decode()
        if any(secret and secret in text for secret in credentials().values()) or re.search(r"sk-[A-Za-z0-9_-]{16,}", text):
            raise ProviderError("UNSAFE_PROVIDER_RESPONSE")
        data = json.loads(text)
    except HTTPError as exc:
        # Deliberately do not read/log the provider error body or repr(request).
        raise ProviderError("PROVIDER_HTTP_ERROR", exc.code) from None
    except (URLError, TimeoutError, OSError, HTTPException):
        check_deadline()
        raise ProviderError("PROVIDER_UNAVAILABLE") from None
    except (ValueError, UnicodeError):
        raise ProviderError("INVALID_PROVIDER_RESPONSE") from None
    finally:
        telemetry.provider_transport_ms((time.monotonic() - started) * 1000)
    if not isinstance(data, dict):
        raise ProviderError("INVALID_PROVIDER_RESPONSE")
    usage = data.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    reported = data.get("model")
    if reported is not None and (not isinstance(reported, str) or not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,120}", reported)):
        raise ProviderError("INVALID_PROVIDER_RESPONSE")
    # Accept the configured ID (or its dated snapshot), never a different family.
    if reported and not re.fullmatch(re.escape(model) + r"(?:-\d{4}-\d{2}-\d{2})?", reported, re.IGNORECASE):
        raise ProviderError("MODEL_MISMATCH")
    meta = {"model": model, "latency_ms": round((time.monotonic() - started) * 1000),
            "reported_model": reported,
            "usage": {k: v for k, v in usage.items() if k in {"prompt_tokens", "completion_tokens", "total_tokens", "input_tokens", "output_tokens"} and isinstance(v, int)}}
    return data, meta


def parse_json(text):
    if not isinstance(text, str):
        raise ProviderError("INVALID_MODEL_OUTPUT")
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    try:
        result = json.loads(text)
    except ValueError:
        raise ProviderError("INVALID_MODEL_OUTPUT") from None
    if isinstance(result, list) and len(result) == 1 and isinstance(result[0], dict):
        result = result[0]
    if not isinstance(result, dict):
        raise ProviderError("INVALID_MODEL_OUTPUT")
    return result


def _chat_once(alias, system, payload, max_tokens):
    effort = settings.AI_LAB_REASONING_EFFORT
    if effort is None:
        effort = settings.AI_LAB_LUNA_REASONING_EFFORT
    effort = effort.strip().lower()
    if effort not in {"", "none", "low", "medium", "high", "xhigh", "max"}:
        raise ProviderError("INVALID_REASONING_EFFORT")
    request = {"messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ], "max_completion_tokens": max_tokens, "stream": False}
    # An explicitly empty setting omits the parameter for compatible models
    # that do not support reasoning_effort. "none" still sends the literal value.
    if effort:
        request["reasoning_effort"] = effort
    data, meta = call(alias, request)
    telemetry.provider_usage(meta)
    try:
        choice = data["choices"][0]
        text = choice["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ProviderError("INVALID_PROVIDER_RESPONSE") from None
    if choice.get("finish_reason") == "length":
        error = ProviderError("MODEL_OUTPUT_TRUNCATED")
        error.metadata = meta
        raise error
    try:
        return parse_json(text), meta
    except ProviderError as exc:
        exc.metadata = meta
        raise


def chat(alias, system, payload, max_tokens=1000):
    if alias not in MODEL_ALIASES:
        raise ProviderError("MODEL_NOT_SUPPORTED")
    for attempt in range(2):
        try:
            with telemetry.model_attempt(max_completion_tokens=max_tokens):
                return _chat_once(alias, system, payload, max_tokens)
        except ProviderError as exc:
            exc.model = configured_models()[alias]
            if exc.code not in {"INVALID_MODEL_OUTPUT", "MODEL_OUTPUT_TRUNCATED"} or attempt:
                raise
            if exc.code == "MODEL_OUTPUT_TRUNCATED":
                max_tokens = min(8192, max(2048, max_tokens * 4))
            system += "\nYour previous output could not be parsed. Return ONLY one valid JSON object, no prose or markdown."
