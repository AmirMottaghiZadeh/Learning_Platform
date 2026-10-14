"""Payment gateways: send the learner off to pay, then confirm with the
gateway itself that they did -- the return to our callback alone proves
nothing, since anyone can open that URL.

BILLING_GATEWAY picks one: "zarinpal" (ZARINPAL_MERCHANT_ID, with
ZARINPAL_SANDBOX for test payments) or "fake", which approves everything
and exists only for local development and tests.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass

from django.conf import settings

logger = logging.getLogger(__name__)


class GatewayError(Exception):
    pass


@dataclass
class Verification:
    ok: bool
    ref_id: str = ""
    card_pan: str = ""
    message: str = ""


class ZarinpalGateway:
    """Zarinpal's v4 REST API. Amounts go over the wire in Rials."""

    name = "zarinpal"

    def __init__(self):
        self.merchant_id = settings.ZARINPAL_MERCHANT_ID
        host = "sandbox.zarinpal.com" if settings.ZARINPAL_SANDBOX else "payment.zarinpal.com"
        self.api = f"https://{host}/pg/v4/payment"
        self.start_url = f"https://{host}/pg/StartPay/"
        if not self.merchant_id:
            raise GatewayError("ZARINPAL_MERCHANT_ID is not set.")

    def _post(self, path, payload):
        request = urllib.request.Request(
            f"{self.api}/{path}",
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "Accept": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=settings.BILLING_GATEWAY_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode() or "{}")
        except urllib.error.HTTPError as exc:
            # Zarinpal answers rejections with a 4xx carrying the same JSON.
            try:
                return json.loads(exc.read().decode() or "{}")
            except ValueError:
                raise GatewayError(f"Zarinpal HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, ValueError) as exc:
            raise GatewayError(f"Zarinpal unreachable: {exc}") from exc

    @staticmethod
    def _errors(body):
        errors = body.get("errors")
        if isinstance(errors, dict) and errors:
            return f"{errors.get('code', '')} {errors.get('message', '')}".strip()
        return ""

    def start(self, order, callback_url, *, description, mobile="", email=""):
        """The URL to send the learner to, and the gateway's id for the payment."""
        metadata = {k: v for k, v in (("mobile", mobile), ("email", email)) if v}
        body = self._post("request.json", {
            "merchant_id": self.merchant_id,
            "amount": order.payable_toman * 10,
            "callback_url": callback_url,
            "description": description[:255],
            "metadata": metadata,
        })
        data = body.get("data") or {}
        if data.get("code") != 100 or not data.get("authority"):
            raise GatewayError(self._errors(body) or f"Zarinpal refused the request: {body}")
        authority = data["authority"]
        return self.start_url + urllib.parse.quote(authority), authority

    def verify(self, order, params):
        if params.get("Status") != "OK":
            return Verification(False, message="پرداخت انجام نشد یا لغو شد.")
        body = self._post("verify.json", {
            "merchant_id": self.merchant_id,
            "amount": order.payable_toman * 10,
            "authority": order.authority,
        })
        data = body.get("data") or {}
        # 100 = verified now, 101 = already verified earlier (a retried callback).
        if data.get("code") in (100, 101):
            return Verification(True, ref_id=str(data.get("ref_id", "")), card_pan=str(data.get("card_pan", "")))
        logger.warning("zarinpal verify rejected", extra={"order": order.pk, "body": body})
        return Verification(False, message=self._errors(body) or "تأیید پرداخت از درگاه ناموفق بود.")


class FakeGateway:
    """Approves every payment without leaving the server. Never in production."""

    name = "fake"

    def start(self, order, callback_url, *, description, mobile="", email=""):
        authority = f"FAKE-{order.pk}"
        query = urllib.parse.urlencode({"Authority": authority, "Status": "OK"})
        return f"{callback_url}?{query}", authority

    def verify(self, order, params):
        if params.get("Status") != "OK":
            return Verification(False, message="پرداخت انجام نشد یا لغو شد.")
        return Verification(True, ref_id=f"FAKE{order.pk}", card_pan="")


def get_gateway():
    name = settings.BILLING_GATEWAY
    if name == "zarinpal":
        return ZarinpalGateway()
    if name == "fake":
        return FakeGateway()
    raise GatewayError(f"Unknown BILLING_GATEWAY {name!r}.")
