"""Stream Chat Completions text/tools without exposing provider bodies or reasoning."""
import json
import re
import time
from urllib.parse import urlsplit

import httpx
from django.conf import settings
from django.views.decorators.debug import sensitive_variables
from . import provider, telemetry
from . import transport_pool
from .provider import ProviderError


def endpoint():
    base = settings.AI_LAB_BASE_URL.strip().rstrip("/")
    try:
        parsed = urlsplit(base)
        bad_port = parsed.port is not None and not 1 <= parsed.port <= 65535
    except ValueError:
        raise ProviderError("INVALID_PROVIDER_URL") from None
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or bad_port or re.search(r"\s", base)):
        raise ProviderError("INVALID_PROVIDER_URL")
    return base + "/chat/completions"


def sse_events(lines):
    """HTTPX incrementally decodes UTF-8; SSE data fields may span lines."""
    parts, size = [], 0
    for line in lines:
        size += len(line)
        if size > 2_000_000:
            raise ProviderError("RESPONSE_TOO_LARGE")
        if line == "":
            if parts:
                yield "\n".join(parts)
                parts = []
        elif line.startswith("data:"):
            parts.append(line[5:].lstrip(" "))
    if parts:
        yield "\n".join(parts)


@sensitive_variables()
def stream_chat(messages, *, tools=(), tool_choice="auto", max_tokens=2400,
                on_delta=lambda _: None, check_cancelled=lambda: None, response_format=None):
    url = endpoint()
    model = settings.AI_LAB_MODEL
    if not re.fullmatch(r"[A-Za-z0-9_.:/-]{1,120}", model):
        raise ProviderError("INVALID_MODEL_CONFIGURATION")
    secret = provider.credentials().get("luna")
    if not secret:
        raise ProviderError("KEY_NOT_CONFIGURED")
    effort = settings.AI_LAB_REASONING_EFFORT
    if effort is None:
        effort = settings.AI_LAB_LUNA_REASONING_EFFORT
    effort = effort.strip().lower()
    if effort not in {"", "none", "low", "medium", "high", "xhigh", "max"}:
        raise ProviderError("INVALID_REASONING_EFFORT")
    payload = {"model":model,"messages":messages,"stream":True,
               "stream_options":{"include_usage":True},"max_completion_tokens":max_tokens}
    if effort:
        payload["reasoning_effort"] = effort
    if tools:
        payload.update(tools=list(tools),tool_choice=tool_choice,parallel_tool_calls=False)
    if response_format:
        payload["response_format"] = response_format
    content, calls, usage, finish, reported, completed, emitted = "", {}, {}, None, None, False, 0
    # Retain enough trailing characters to detect a credential spanning token
    # boundaries BEFORE any part of that credential reaches a client callback.
    lookbehind = max(128, len(secret) + 8)
    started = time.monotonic()
    try:
        with telemetry.model_attempt(max_completion_tokens=max_tokens):
            timeout = provider.reserve_request()
            check_cancelled()
            telemetry.provider_request_sent()
            with transport_pool.client(timeout) as client:
                with client.stream("POST",url,json=payload,headers={"Authorization":"Bearer "+secret}, timeout=timeout) as response:
                    if response.status_code != 200:
                        raise ProviderError("PROVIDER_HTTP_ERROR",response.status_code)
                    for raw in sse_events(response.iter_lines()):
                        check_cancelled(); provider.check_deadline()
                        if raw == "[DONE]":
                            completed = True
                            break
                        if secret in raw or re.search(r"sk-[A-Za-z0-9_-]{16,}",raw):
                            raise ProviderError("UNSAFE_PROVIDER_RESPONSE")
                        try:
                            value = json.loads(raw)
                        except ValueError:
                            raise ProviderError("INVALID_PROVIDER_RESPONSE") from None
                        if not isinstance(value,dict) or value.get("error"):
                            raise ProviderError("INVALID_PROVIDER_RESPONSE")
                        if "model" in value:
                            reported = value["model"]
                            if not isinstance(reported,str) or not re.fullmatch(re.escape(model)+r"(?:-\d{4}-\d{2}-\d{2})?",reported,re.I):
                                raise ProviderError("MODEL_MISMATCH")
                        if isinstance(value.get("usage"),dict):
                            usage = {k:v for k,v in value["usage"].items() if k in {"prompt_tokens","completion_tokens","total_tokens"} and type(v) is int and v>=0}
                            telemetry.provider_usage({"usage":value["usage"]})
                        choices = value.get("choices",[])
                        if not isinstance(choices,list):
                            raise ProviderError("INVALID_PROVIDER_RESPONSE")
                        for choice in choices:
                            if not isinstance(choice,dict) or choice.get("index",0) != 0:
                                raise ProviderError("INVALID_PROVIDER_RESPONSE")
                            finish = choice.get("finish_reason") or finish
                            delta = choice.get("delta") or {}
                            if not isinstance(delta,dict):
                                raise ProviderError("INVALID_PROVIDER_RESPONSE")
                            text = delta.get("content")
                            if text is not None:
                                if not isinstance(text,str):
                                    raise ProviderError("INVALID_PROVIDER_RESPONSE")
                                content += text
                                if len(content)>64000:
                                    raise ProviderError("RESPONSE_TOO_LARGE")
                                if secret in content or re.search(r"sk-[A-Za-z0-9_-]{16,}",content):
                                    raise ProviderError("UNSAFE_PROVIDER_RESPONSE")
                                safe_end = max(emitted,len(content)-lookbehind)
                                if safe_end>emitted:
                                    on_delta(content[emitted:safe_end]); emitted=safe_end
                            deltas = delta.get("tool_calls",[])
                            if not isinstance(deltas,list):
                                raise ProviderError("INVALID_MODEL_OUTPUT")
                            for tool in deltas:
                                if not isinstance(tool,dict) or type(tool.get("index")) is not int or not 0<=tool["index"]<4:
                                    raise ProviderError("INVALID_MODEL_OUTPUT")
                                call = calls.setdefault(tool["index"],{"id":"","type":"function","function":{"name":"","arguments":""}})
                                if tool.get("id"):
                                    if not isinstance(tool["id"],str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,200}",tool["id"]):
                                        raise ProviderError("INVALID_MODEL_OUTPUT")
                                    call["id"] = tool["id"]
                                function = tool.get("function") or {}
                                if not isinstance(function,dict):
                                    raise ProviderError("INVALID_MODEL_OUTPUT")
                                for field in ["name","arguments"]:
                                    piece = function.get(field,"")
                                    if not isinstance(piece,str):
                                        raise ProviderError("INVALID_MODEL_OUTPUT")
                                    call["function"][field] += piece
                                    if len(call["function"][field])>8000:
                                        raise ProviderError("INVALID_MODEL_OUTPUT")
                if not completed or finish not in {"stop","tool_calls","length"}:
                    raise ProviderError("PROVIDER_STREAM_INCOMPLETE")
                if finish == "length":
                    raise ProviderError("MODEL_OUTPUT_TRUNCATED")
                if finish == "tool_calls" and (not calls or any(not c["id"] for c in calls.values())):
                    raise ProviderError("INVALID_MODEL_OUTPUT")
                if calls and finish != "tool_calls":
                    raise ProviderError("INVALID_MODEL_OUTPUT")
                serialized_calls = json.dumps(calls,ensure_ascii=False)
                if secret in serialized_calls or re.search(r"sk-[A-Za-z0-9_-]{16,}",serialized_calls):
                    raise ProviderError("UNSAFE_PROVIDER_RESPONSE")
                if not calls and emitted<len(content):
                    on_delta(content[emitted:])
            meta = {"model":model,"reported_model":reported,"usage":usage,
                    "latency_ms":round((time.monotonic()-started)*1000)}
            telemetry.provider_usage(meta)
            message = {"role":"assistant","content":content or None}
            if calls:
                message["tool_calls"] = [calls[i] for i in sorted(calls)]
            return message, meta
    except (httpx.HTTPError,OSError,TimeoutError):
        raise ProviderError("PROVIDER_UNAVAILABLE") from None
    finally:
        telemetry.provider_transport_ms((time.monotonic()-started)*1000)
