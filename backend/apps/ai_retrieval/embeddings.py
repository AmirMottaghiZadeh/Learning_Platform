"""Private embedding adapter with strict shape validation and no implicit replay."""
from hashlib import sha256
import json
import math
import re
import time
from urllib.parse import urlsplit

import httpx
from django.conf import settings
from django.views.decorators.debug import sensitive_variables

from apps.ai_lab.provider import ProviderError, credentials, reserve_request
from apps.ai_lab import transport_pool, telemetry
from .chunking import token_count


def base_url():
    base = settings.AI_LAB_EMBEDDING_BASE_URL.strip().rstrip("/")
    try:
        parsed = urlsplit(base)
        invalid_port = parsed.port is not None and not 1 <= parsed.port <= 65535
    except ValueError:
        raise ProviderError("INVALID_EMBEDDING_URL") from None
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or invalid_port or re.search(r"\s", base)):
        raise ProviderError("INVALID_EMBEDDING_URL")
    return base


def profile():
    if settings.AI_LAB_EMBEDDING_BACKEND == "onnx":
        from .local_embeddings import profile as local_profile
        return local_profile()
    if settings.AI_LAB_EMBEDDING_BACKEND != "openai":
        raise ProviderError("INVALID_EMBEDDING_BACKEND")
    model, dimensions = settings.AI_LAB_EMBEDDING_MODEL, settings.AI_LAB_EMBEDDING_DIMENSIONS
    if not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,120}", model) or type(dimensions) is not int or not 1 <= dimensions <= 2000:
        raise ProviderError("INVALID_EMBEDDING_CONFIGURATION")
    value = {"model": model, "dimensions": dimensions, "base_url": base_url(),
             "revision": settings.AI_LAB_EMBEDDING_REVISION, "normalization": "l2-v1"}
    value["id"] = sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()
    return value


@sensitive_variables()
def api_key():
    if settings.AI_LAB_EMBEDDING_API_KEY:
        return settings.AI_LAB_EMBEDDING_API_KEY
    if settings.AI_LAB_EMBEDDING_USE_CHAT_KEY:
        if base_url() != settings.AI_LAB_BASE_URL.strip().rstrip("/"):
            raise ProviderError("EMBEDDING_KEY_PROVIDER_MISMATCH")
        key = credentials().get("luna")
        if key:
            return key
    raise ProviderError("EMBEDDING_KEY_NOT_CONFIGURED")


def validate_vector(value, dimensions):
    if (not isinstance(value, list) or len(value) != dimensions
            or any(type(n) not in {int, float} or not math.isfinite(n) for n in value)):
        raise ProviderError("INVALID_EMBEDDING_RESPONSE")
    norm = math.sqrt(sum(n * n for n in value))
    if not math.isfinite(norm) or norm <= 0:
        raise ProviderError("INVALID_EMBEDDING_RESPONSE")
    return [n / norm for n in value]


def embed(texts, *, check_cancelled=lambda:None, purpose="document"):
    if not isinstance(texts,list) or not 1<=len(texts)<=128 or any(not isinstance(t,str) or not t.strip() for t in texts):
        raise ProviderError("INVALID_EMBEDDING_INPUT")
    if purpose not in {"document","query"}:
        raise ProviderError("INVALID_EMBEDDING_PURPOSE")
    if settings.AI_LAB_EMBEDDING_BACKEND == "onnx":
        from .local_embeddings import embed as local_embed
        with telemetry.operation("embedding"):
            return local_embed(texts,purpose=purpose,check_cancelled=check_cancelled)
    if settings.AI_LAB_EMBEDDING_BACKEND != "openai":
        raise ProviderError("INVALID_EMBEDDING_BACKEND")
    if not settings.AI_LAB_EMBEDDING_REMOTE_ENABLED:
        raise ProviderError("REMOTE_EMBEDDING_DISABLED")
    with telemetry.operation("embedding"), telemetry.model_attempt():
        values, metadata = _embed(texts, check_cancelled=check_cancelled)
        # Embedding has no completion output; this is not unknown chat usage.
        telemetry.provider_usage({"usage": {"completion_tokens": 0, **metadata.get("usage", {})}})
        return values, metadata


def embed_query(text, *, check_cancelled=lambda:None):
    if settings.AI_LAB_EMBEDDING_BACKEND == "onnx":
        return embed([text],purpose="query",check_cancelled=check_cancelled)
    return embed([text],check_cancelled=check_cancelled)


@sensitive_variables()
def _embed(texts, *, check_cancelled=lambda:None):
    configuration = profile()
    if not isinstance(texts, list) or not 1 <= len(texts) <= 128 or any(not isinstance(t, str) or not t.strip() for t in texts):
        raise ProviderError("INVALID_EMBEDDING_INPUT")
    sizes = [token_count(text) for text in texts]
    if max(sizes) > 8000 or sum(sizes) > 200000:
        raise ProviderError("EMBEDDING_INPUT_TOO_LARGE")
    key = api_key()
    payload = {"model": configuration["model"], "input": texts, "encoding_format": "float"}
    # Some compatible models fix their native dimension and don't accept this.
    # Set the desired native dimension in settings; only v3 models get shortening.
    if "text-embedding-3-" in configuration["model"]:
        payload["dimensions"] = configuration["dimensions"]
    started = time.monotonic()
    try:
        timeout = min(reserve_request(), settings.AI_LAB_EMBEDDING_TIMEOUT_SECONDS)
        check_cancelled()
        telemetry.provider_request_sent()
        with transport_pool.client(timeout) as client:
            with client.stream("POST", base_url() + "/embeddings", json=payload,
                               headers={"Authorization": "Bearer " + key}, timeout=timeout) as response:
                if response.status_code != 200:
                    raise ProviderError("EMBEDDING_HTTP_ERROR", response.status_code)
                body = bytearray()
                for chunk in response.iter_bytes():
                    check_cancelled()
                    body.extend(chunk)
                    if len(body) > 16_000_000:
                        raise ProviderError("EMBEDDING_RESPONSE_TOO_LARGE")
        raw = body.decode()
        check_cancelled()
        if key in raw or re.search(r"sk-[A-Za-z0-9_-]{16,}", raw):
            raise ProviderError("UNSAFE_EMBEDDING_RESPONSE")
        data = json.loads(raw)
    except (httpx.HTTPError, OSError, TimeoutError):
        raise ProviderError("EMBEDDING_UNAVAILABLE") from None
    except (ValueError, UnicodeError):
        raise ProviderError("INVALID_EMBEDDING_RESPONSE") from None
    if not isinstance(data, dict) or data.get("model", configuration["model"]) != configuration["model"]:
        raise ProviderError("EMBEDDING_MODEL_MISMATCH")
    rows = data.get("data")
    if (not isinstance(rows, list) or len(rows) != len(texts) or any(not isinstance(row, dict) for row in rows)
            or any(type(row.get("index")) is not int for row in rows)
            or {row["index"] for row in rows} != set(range(len(texts)))):
        raise ProviderError("INVALID_EMBEDDING_RESPONSE")
    vectors = [validate_vector(row.get("embedding"), configuration["dimensions"])
               for row in sorted(rows, key=lambda row: row["index"])]
    usage = data.get("usage") or {}
    if not isinstance(usage, dict):
        usage = {}
    return vectors, {"latency_ms": round((time.monotonic() - started) * 1000),
                     "inputs": len(texts), "estimated_input_tokens": sum(sizes),
                     "usage": {k: v for k, v in usage.items() if k in {"prompt_tokens", "total_tokens"} and type(v) is int and v >= 0}}
