"""Sending one-time codes by SMS.

Two backends, picked by `settings.SMS_BACKEND`:
- "smsir": sms.ir's verify API -- an approved template with the code as one
  parameter (POST {SMSIR_VERIFY_URL}, header X-API-KEY, JSON body
  {mobile, templateId, parameters: [{name, value}]}).
- "console": writes the code to the log and appends it to `outbox`, for
  development and tests -- nothing is sent and no credit is spent.

The code itself is never logged by the real backend.
"""

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)

# Codes "sent" by the console backend, newest last -- the SMS counterpart of
# django.core.mail.outbox, for tests.
outbox: list["SentCode"] = []


@dataclass
class SentCode:
    phone: str
    code: str


class SmsSendError(Exception):
    """The code could not be handed to the SMS provider."""


def mask(phone: str) -> str:
    return f"{phone[:4]}***{phone[-4:]}" if len(phone) >= 8 else "***"


def send_code(phone: str, code: str) -> str:
    """Sends `code` to `phone`; returns the provider's message id ("" for
    the console backend). Raises SmsSendError when it couldn't be sent."""
    backend = getattr(settings, "SMS_BACKEND", "console")
    if backend == "smsir":
        return _send_smsir(phone, code)
    if backend == "console":
        outbox.append(SentCode(phone, code))
        logger.warning("SMS (console backend, not sent) to %s: code %s", mask(phone), code)
        return ""
    raise SmsSendError(f"Unknown SMS_BACKEND {backend!r}.")


def _send_smsir(phone: str, code: str) -> str:
    if not settings.SMSIR_API_KEY or not settings.SMSIR_OTP_TEMPLATE_ID:
        raise SmsSendError("SMSIR_API_KEY / SMSIR_OTP_TEMPLATE_ID are not configured.")
    body = json.dumps({
        "mobile": phone,
        "templateId": settings.SMSIR_OTP_TEMPLATE_ID,
        "parameters": [{"name": settings.SMSIR_OTP_PARAMETER, "value": code}],
    }).encode()
    request = urllib.request.Request(
        settings.SMSIR_VERIFY_URL,
        data=body,
        method="POST",
        headers={
            "X-API-KEY": settings.SMSIR_API_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.SMSIR_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read() or b"{}")
    except urllib.error.HTTPError as exc:
        detail = _error_message(exc)
        logger.error("sms.ir rejected the code for %s: HTTP %s %s", mask(phone), exc.code, detail)
        raise SmsSendError(f"sms.ir HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        logger.error("sms.ir unreachable for %s: %s", mask(phone), exc)
        raise SmsSendError(f"sms.ir unreachable: {exc}") from exc

    # {"status": 1, "message": "موفق", "data": {"messageId": ..., "cost": ...}}
    if payload.get("status") != 1:
        logger.error("sms.ir refused the code for %s: %s", mask(phone), payload.get("message"))
        raise SmsSendError(f"sms.ir status {payload.get('status')}: {payload.get('message')}")
    data = payload.get("data") or {}
    return str(data.get("messageId", ""))


def _error_message(exc: urllib.error.HTTPError) -> str:
    try:
        return str(json.loads(exc.read() or b"{}").get("message", ""))
    except (ValueError, AttributeError):
        return ""
