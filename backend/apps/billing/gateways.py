"""Payment gateways: send the learner off to pay, then confirm with the
gateway itself that they did -- the return to our callback alone proves
nothing, since anyone can open that URL.

The gateways and their merchant ids come from the console's "درگاه پرداخت"
page, falling back to BILLING_GATEWAY / ZARINPAL_MERCHANT_ID /
ZARINPAL_SANDBOX when none is set up there. Each gateway answers on its own
callback (/pay/callback/<kind>/). "fake" approves everything and exists only
for local development and tests.
"""

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass

from django.conf import settings

from . import config

logger = logging.getLogger(__name__)


class GatewayError(Exception):
    pass


@dataclass
class Verification:
    ok: bool
    ref_id: str = ""
    card_pan: str = ""
    message: str = ""
    gateway_ref: str = ""


def _post_json(url, payload, label):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=settings.BILLING_GATEWAY_TIMEOUT_SECONDS) as response:
            return json.loads(response.read().decode() or "{}")
    except urllib.error.HTTPError as exc:
        # Both gateways answer some rejections with a 4xx carrying JSON.
        try:
            return json.loads(exc.read().decode() or "{}")
        except ValueError:
            raise GatewayError(f"{label} HTTP {exc.code}") from exc
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise GatewayError(f"{label} unreachable: {exc}") from exc


class ZarinpalGateway:
    """Zarinpal's v4 REST API. Amounts go over the wire in Rials. The buyer
    comes back with ?Authority=…&Status=OK|NOK."""

    name = "zarinpal"

    def __init__(self, merchant_id=None, sandbox=None):
        spec = config.gateway_spec("zarinpal")
        if merchant_id is None:
            merchant_id = spec.merchant_id if spec else settings.ZARINPAL_MERCHANT_ID
        if sandbox is None:
            sandbox = spec.sandbox if spec else settings.ZARINPAL_SANDBOX
        self.merchant_id = merchant_id
        host = "sandbox.zarinpal.com" if sandbox else "payment.zarinpal.com"
        self.api = f"https://{host}/pg/v4/payment"
        self.start_url = f"https://{host}/pg/StartPay/"
        if not self.merchant_id:
            raise GatewayError("ZARINPAL_MERCHANT_ID is not set.")

    def _post(self, path, payload):
        return _post_json(f"{self.api}/{path}", payload, "Zarinpal")

    @staticmethod
    def find_order(orders, params):
        authority = (params.get("Authority") or "").strip()
        return orders.filter(authority=authority).first() if authority else None

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

    def test(self, callback_url):
        """Ask for a payment of 1,000 Toman and never send anyone to pay it:
        proves the merchant id is accepted and the gateway answers. Returns
        a Persian message; raises GatewayError when it does not work."""
        body = self._post("request.json", {
            "merchant_id": self.merchant_id,
            "amount": 10_000,
            "callback_url": callback_url,
            "description": "آزمایش اتصال از پنل مدیریت فارمنتا",
        })
        data = body.get("data") or {}
        if data.get("code") != 100:
            raise GatewayError(self._errors(body) or f"Zarinpal refused the request: {body}")
        return "زرین‌پال درخواست را پذیرفت؛ مرچنت‌کد درست است."

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


class SepGateway:
    """Saman's SEP: ask for a token, send the buyer to SEP with it, and on
    their return (a POST carrying State, RefNum, ResNum, Token…) verify the
    RefNum with SEP within its 30 minutes -- unverified payments are reversed
    by SEP itself. Amounts are in Rials. SEP only answers calls from the
    server IPs registered for the terminal."""

    name = "sep"
    TOKEN_URL = "https://sep.shaparak.ir/onlinepg/onlinepg"
    PAY_URL = "https://sep.shaparak.ir/OnlinePG/SendToken"
    VERIFY_URL = "https://sep.shaparak.ir/verifyTxnRandomSessionkey/ipg/VerifyTransaction"
    REVERSE_URL = "https://sep.shaparak.ir/verifyTxnRandomSessionkey/ipg/ReverseTransaction"
    # The commonest verify answers, in words a buyer or an operator can act on.
    RESULTS = {
        -2: "تراکنش در سپ پیدا نشد.",
        -6: "بیش از ۳۰ دقیقه از پرداخت گذشته و سپ آن را برگردانده است.",
        -104: "ترمینال سپ غیرفعال است.",
        -105: "ترمینال سپ وجود ندارد.",
        -106: "IP سرور برای ترمینال سپ ثبت نشده است.",
        2: "این پرداخت پیش‌تر تأیید شده است.",
        5: "این پرداخت برگشت خورده است.",
    }
    STATUSES = {"1": "پرداخت را لغو کردید.", "3": "پرداخت انجام نشد.", "4": "زمان پرداخت تمام شد."}

    def __init__(self, terminal_id=None):
        if terminal_id is None:
            spec = config.gateway_spec("sep")
            terminal_id = spec.merchant_id if spec else ""
        self.terminal_id = terminal_id
        if not self.terminal_id:
            raise GatewayError("SEP terminal id is not set.")

    def _token(self, amount_rial, res_num, callback_url, mobile=""):
        payload = {
            "action": "token",
            "TerminalId": self.terminal_id,
            "Amount": amount_rial,
            "ResNum": res_num,
            "RedirectUrl": callback_url,
        }
        if mobile:
            payload["CellNumber"] = mobile
        body = _post_json(self.TOKEN_URL, payload, "SEP")
        if body.get("status") != 1 or not body.get("token"):
            raise GatewayError(
                f"SEP refused the token request: {body.get('errorCode', '')} {body.get('errorDesc', '')}".strip()
            )
        return body["token"]

    def start(self, order, callback_url, *, description, mobile="", email=""):
        token = self._token(order.payable_toman * 10, str(order.pk), callback_url, mobile)
        return f"{self.PAY_URL}?token={urllib.parse.quote(token)}", token

    def test(self, callback_url):
        """Ask for a token of 1,000 Toman that nobody pays: proves the terminal
        and this server's IP are accepted. Raises GatewayError otherwise."""
        self._token(10_000, f"test-{uuid.uuid4().hex[:16]}", callback_url)
        return "سپ درخواست را پذیرفت؛ شمارهٔ ترمینال و IP سرور درست است."

    @staticmethod
    def _field(params, name):
        for key in (name, name.lower(), name.upper()):
            if params.get(key):
                return str(params.get(key)).strip()
        return ""

    @classmethod
    def find_order(cls, orders, params):
        res_num, token = cls._field(params, "ResNum"), cls._field(params, "Token")
        if not res_num.isdigit():
            return None
        order = orders.filter(pk=int(res_num)).first()
        # The token ties this return to the payment we started for the order.
        if order is None or not token or order.authority != token:
            return None
        return order

    def verify(self, order, params):
        state, status = self._field(params, "State"), self._field(params, "Status")
        ref_num = self._field(params, "RefNum")
        if state.upper() != "OK" or not ref_num:
            return Verification(False, message=self.STATUSES.get(status, "پرداخت انجام نشد یا لغو شد."))
        # A receipt already used for another order is somebody else's payment.
        if order.__class__.objects.filter(gateway=self.name, gateway_ref=ref_num).exclude(pk=order.pk).exists():
            logger.warning("sep receipt reused", extra={"order": order.pk})
            return Verification(False, message="این رسید پرداخت پیش‌تر برای سفارش دیگری استفاده شده است.")
        body = _post_json(self.VERIFY_URL, {"RefNum": ref_num, "TerminalNumber": int(self.terminal_id)}, "SEP")
        detail = body.get("TransactionDetail") or {}
        code = body.get("ResultCode")
        if not (body.get("Success") and code == 0):
            logger.warning("sep verify rejected", extra={"order": order.pk, "body": body})
            return Verification(False, message=self.RESULTS.get(code, body.get("ResultDescription") or "تأیید پرداخت از سپ ناموفق بود."))
        expected = order.payable_toman * 10
        paid = detail.get("OrginalAmount", detail.get("AffectiveAmount"))
        if paid != expected:
            logger.warning("sep amount mismatch", extra={"order": order.pk, "paid": paid, "expected": expected})
            self.reverse(ref_num)
            return Verification(False, message="مبلغ پرداخت‌شده با مبلغ سفارش یکی نبود؛ پرداخت برگشت داده شد.")
        return Verification(
            True,
            ref_id=str(detail.get("RRN") or detail.get("StraceNo") or ref_num),
            card_pan=str(detail.get("MaskedPan") or ""),
            gateway_ref=ref_num,
        )

    def reverse(self, ref_num):
        try:
            _post_json(self.REVERSE_URL, {"RefNum": ref_num, "TerminalNumber": int(self.terminal_id)}, "SEP")
        except GatewayError:
            logger.exception("sep reverse failed", extra={"ref_num": ref_num})


class FakeGateway:
    """Approves every payment without leaving the server. Never in production."""

    name = "fake"

    def start(self, order, callback_url, *, description, mobile="", email=""):
        authority = f"FAKE-{order.pk}"
        query = urllib.parse.urlencode({"Authority": authority, "Status": "OK"})
        return f"{callback_url}?{query}", authority

    find_order = staticmethod(ZarinpalGateway.find_order)

    def verify(self, order, params):
        if params.get("Status") != "OK":
            return Verification(False, message="پرداخت انجام نشد یا لغو شد.")
        return Verification(True, ref_id=f"FAKE{order.pk}", card_pan="")


CLASSES = {"zarinpal": ZarinpalGateway, "sep": SepGateway, "fake": FakeGateway}


def get_gateway(kind=None):
    """The gateway of `kind` (enabled or not -- a payment in flight still has
    to be verified), or with no kind, the first enabled one."""
    if kind is None:
        enabled = config.enabled_gateways()
        if not enabled:
            raise GatewayError("No payment gateway is enabled.")
        kind = enabled[0].kind
    if kind == "fake":
        return FakeGateway()
    spec = config.gateway_spec(kind)
    if kind not in CLASSES or spec is None:
        raise GatewayError(f"Unknown payment gateway {kind!r}.")
    if kind == "zarinpal":
        return ZarinpalGateway(spec.merchant_id, spec.sandbox)
    return SepGateway(spec.merchant_id)


def start_payment(order, callback_for, *, kind=None, description, mobile="", email=""):
    """Send `order` to a gateway: the one asked for, or else each enabled
    gateway in turn until one accepts. `callback_for(kind)` is the absolute
    callback URL for that gateway. Saves which gateway took the order and
    returns the URL to send the buyer to; raises the last GatewayError when
    none would take it."""
    kinds = [kind] if kind else [g.kind for g in config.enabled_gateways()]
    if not kinds:
        raise GatewayError("No payment gateway is enabled.")
    error = None
    for name in kinds:
        try:
            gateway = get_gateway(name)
            url, authority = gateway.start(
                order, callback_for(name), description=description, mobile=mobile, email=email
            )
        except GatewayError as exc:
            logger.warning("gateway would not start", extra={"order": order.pk, "gateway": name, "error": str(exc)})
            error = exc
            continue
        order.gateway, order.authority = gateway.name, authority
        order.save(update_fields=["gateway", "authority"])
        return url
    raise error
