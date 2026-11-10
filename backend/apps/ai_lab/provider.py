"""Small server-only GapGPT adapter. Never expose upstream bodies or credentials."""
import json
from contextvars import ContextVar
from pathlib import Path
import re
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from django.conf import settings
from django.views.decorators.debug import sensitive_variables

MODELS = {"luna": "gpt-6-luna"}
deadline = ContextVar("ai_lab_deadline", default=None)


class ProviderError(Exception):
    def __init__(self, code, status=0):
        self.code, self.status = code, status
        super().__init__(code)


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


@sensitive_variables()
def credentials():
    keys = {"luna": settings.AI_LAB_LUNA_API_KEY}
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
                alias = next((name for name in MODELS if name in label), None)
                if alias and not keys[alias]:
                    keys[alias] = match.group()
            elif line.strip():
                label = line.lower()
    return keys


@sensitive_variables()
def call(alias, payload):
    if alias not in MODELS:
        raise ProviderError("MODEL_NOT_SUPPORTED")
    key = credentials().get(alias)
    if not key:
        raise ProviderError("KEY_NOT_CONFIGURED")
    base = settings.AI_LAB_BASE_URL.rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ProviderError("INVALID_PROVIDER_URL")
    payload = {**payload, "model": MODELS[alias]}
    request = Request(base + "/chat/completions", data=json.dumps(payload, ensure_ascii=False).encode(),
                      headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, method="POST")
    started = time.monotonic()
    timeout = settings.AI_LAB_TIMEOUT_SECONDS
    if deadline.get() is not None:
        timeout = min(timeout, deadline.get() - started)
        if timeout <= 0:
            raise ProviderError("EXPERIMENT_TIMEOUT")
    try:
        with build_opener(NoRedirect).open(request, timeout=timeout) as response:
            raw = response.read(2_000_001)
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
    except (URLError, TimeoutError, OSError):
        raise ProviderError("PROVIDER_UNAVAILABLE") from None
    except (ValueError, UnicodeError):
        raise ProviderError("INVALID_PROVIDER_RESPONSE") from None
    if not isinstance(data, dict):
        raise ProviderError("INVALID_PROVIDER_RESPONSE")
    usage = data.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    reported = data.get("model")
    if reported is not None and (not isinstance(reported, str) or not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,120}", reported)):
        raise ProviderError("INVALID_PROVIDER_RESPONSE")
    # Keep the reported provider alias, and reject a different model family.
    if reported and alias not in reported.lower():
        raise ProviderError("MODEL_MISMATCH")
    meta = {"model": MODELS[alias], "latency_ms": round((time.monotonic() - started) * 1000),
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
    effort = settings.AI_LAB_LUNA_REASONING_EFFORT
    if effort not in {"none", "low", "medium", "high", "xhigh", "max"}:
        raise ProviderError("INVALID_REASONING_EFFORT")
    request = {"model": MODELS[alias], "messages": [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ], "max_completion_tokens": max_tokens, "reasoning_effort": effort, "stream": False}
    data, meta = call(alias, request)
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
    if alias not in MODELS:
        raise ProviderError("MODEL_NOT_SUPPORTED")
    for attempt in range(2):
        try:
            return _chat_once(alias, system, payload, max_tokens)
        except ProviderError as exc:
            exc.model = MODELS[alias]
            if exc.code not in {"INVALID_MODEL_OUTPUT", "MODEL_OUTPUT_TRUNCATED"} or attempt:
                raise
            if exc.code == "MODEL_OUTPUT_TRUNCATED":
                max_tokens = min(8192, max(2048, max_tokens * 4))
            system += "\nYour previous output could not be parsed. Return ONLY one valid JSON object, no prose or markdown."
