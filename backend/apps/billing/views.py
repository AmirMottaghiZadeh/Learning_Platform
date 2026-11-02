"""The app's side of billing: what is for sale, what the learner has, and
buying -- an order, then the gateway, then our callback, which confirms the
payment with the gateway before granting anything."""

from django.conf import settings
from django.core import signing
from django.db.models import Prefetch
from django.shortcuts import redirect, render
from django.urls import NoReverseMatch, reverse
from django.views.decorators.csrf import csrf_exempt
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from . import config, services
from .gateways import GatewayError, get_gateway, start_payment
from .guest import is_guest
from .models import Feature, Order, Plan, PlanFeature
from .serializers import (
    CatalogSerializer,
    CheckoutRequestSerializer,
    CheckoutSerializer,
    MyAccessSerializer,
    OrderSerializer,
    PurchaseRequestSerializer,
    QuoteSerializer,
)


def _plans():
    return Plan.objects.prefetch_related(
        "prices", Prefetch("plan_features", queryset=PlanFeature.objects.select_related("feature").order_by("feature__order"))
    )


def _billing_error(exc):
    return PlatformAPIError(exc.message, code=exc.code, status_code=400)


def _priced(request, serializer=PurchaseRequestSerializer):
    if is_guest(request.user):
        raise PlatformAPIError("Sign in to buy.", code="GUEST_CANNOT_BUY", status_code=403)
    body = serializer(data=request.data)
    body.is_valid(raise_exception=True)
    try:
        price = services.purchasable_price(body.validated_data["price_id"])
        discount = services.find_discount(body.validated_data["discount_code"])
        services.quote(price, discount)
    except services.BillingError as exc:
        raise _billing_error(exc) from exc
    if serializer is not PurchaseRequestSerializer:
        return price, discount, body.validated_data
    return price, discount


class CatalogView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CatalogSerializer)
    def get(self, request):
        on_sale = _plans().filter(status=Plan.STATUS_ACTIVE, is_free=False)
        cfg = config.current()
        return Response(CatalogSerializer({
            "free": _plans().filter(is_free=True).exclude(status=Plan.STATUS_INACTIVE).first(),
            "plans": [p for p in on_sale if p.kind == Plan.KIND_PLAN],
            "products": [p for p in on_sale if p.kind == Plan.KIND_PRODUCT],
            "gateways": [{"kind": g.kind, "name": g.name} for g in config.enabled_gateways()],
            "sales_enabled": cfg.sales_enabled,
        }).data)


class MyAccessView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=MyAccessSerializer)
    def get(self, request):
        user = request.user
        have = services.effective_features(user)
        names = dict(Feature.objects.filter(key__in=have).values_list("key", "name_fa"))
        features = [
            {
                "key": key,
                "name_fa": names.get(key, key),
                "limit": grant["limit"],
                "period": grant["period"],
                "used": services.usage_count(user, key, grant["period"]) if grant["limit"] is not None else 0,
            }
            for key, grant in have.items()
        ]
        return Response(MyAccessSerializer({
            "enforced": config.current().enforcement,
            "features": features,
            "entitlements": services.active_entitlements(user),
        }).data)


class QuoteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PurchaseRequestSerializer, responses=QuoteSerializer)
    def post(self, request):
        price, discount = _priced(request)
        amount, off, payable = services.quote(price, discount)
        return Response(QuoteSerializer({"amount_toman": amount, "discount_toman": off, "payable_toman": payable}).data)


class CheckoutView(APIView):
    """An order for the app. The payment itself starts on the site (the
    `payment_url` it answers with): the gateways know the site's domain --
    the callback registered with them, the Referer Zibal checks -- and the
    result page is the site's either way."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=CheckoutRequestSerializer, responses=CheckoutSerializer)
    def post(self, request):
        if not config.current().sales_enabled:
            raise PlatformAPIError("Sales are paused for now.", code="SALES_PAUSED", status_code=503)
        price, discount, body = _priced(request, CheckoutRequestSerializer)
        kinds = [g.kind for g in config.enabled_gateways()]
        gateway = body["gateway"]
        if gateway and gateway not in kinds:
            raise PlatformAPIError("That payment gateway is not on.", code="GATEWAY_UNKNOWN", status_code=400)
        channel = Order.CHANNEL_ANDROID if body["client"] == "android" else Order.CHANNEL_WEB
        if services.quote(price, discount)[2] and not kinds:
            raise PlatformAPIError("No payment gateway is on.", code="NO_GATEWAY", status_code=503)
        order = services.create_order(request.user, price, discount, channel=channel)
        if order.payable_toman == 0:
            services.mark_paid(order.pk, gateway="free")
            return Response(CheckoutSerializer({"order_id": order.pk, "status": Order.STATUS_PAID, "payment_url": ""}).data, status=201)
        return Response(
            CheckoutSerializer({"order_id": order.pk, "status": order.status, "payment_url": pay_start_url(order, gateway)}).data,
            status=201,
        )


class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OrderSerializer(many=True))
    def get(self, request):
        orders = Order.objects.filter(user=request.user).select_related("plan")[:50]
        return Response(OrderSerializer(orders, many=True).data)


def callback_url(request, kind):
    """The absolute URL a gateway sends the buyer back to, on the host the
    purchase started from (the site's /pay/callback/<kind>/ or the API's)."""
    return request.build_absolute_uri(reverse("billing-callback-gateway", args=[kind]))


PAY_START_SALT = "billing.pay-start"
# How long the app's link to the gateway keeps working.
PAY_START_MAX_AGE = 3600


def pay_start_url(order, gateway=""):
    """The site's page that starts `order`'s payment and hands the buyer to
    the gateway (`pay_start`)."""
    token = signing.dumps({"o": order.pk, "g": gateway}, salt=PAY_START_SALT, compress=True)
    return settings.SITE_PUBLIC_URL.rstrip("/") + reverse("billing-pay-start", args=[token], urlconf="config.urls_site")


def pay_start(request, token):
    """On the site: start the payment of an order the app made, then go on to
    the gateway from this page -- by a script, not a redirect, so the gateway
    sees the site as the referrer (Zibal checks it). The link is signed and
    lasts an hour; whoever has it can only pay for that order."""
    try:
        data = signing.loads(token, salt=PAY_START_SALT, max_age=PAY_START_MAX_AGE)
        pk, chosen = int(data["o"]), str(data.get("g") or "")
    except (signing.BadSignature, KeyError, TypeError, ValueError):
        return _failed(request, None, "این لینک پرداخت معتبر نیست یا منقضی شده است؛ از اپ دوباره خرید را شروع کنید.", status=404)
    order = Order.objects.select_related("plan", "price").filter(pk=pk).first()
    if order is None:
        return _failed(request, None, "سفارشی برای این پرداخت پیدا نشد.", status=404)
    if order.status != Order.STATUS_PENDING:
        return redirect(result_url(order))
    if not config.current().sales_enabled:
        return _failed(request, order, "فروش موقتاً متوقف است؛ کمی بعد از اپ دوباره امتحان کنید.")
    kinds = [g.kind for g in config.enabled_gateways()]
    profile = getattr(order.user, "learner_profile", None) if order.user else None
    try:
        url = start_payment(
            order, lambda kind: callback_url(request, kind), kind=chosen if chosen in kinds else None,
            description=f"خرید {order.plan.name_fa}" + (f" · {order.price.duration_label}" if order.price else ""),
            mobile=getattr(profile, "phone", None) or "", email=(order.user.email if order.user else "") or "",
        )
    except GatewayError as exc:
        services.mark_failed(order, str(exc))
        return _failed(request, order, "درگاه پرداخت الان در دسترس نیست؛ کمی بعد از اپ دوباره امتحان کنید.")
    response = render(request, "billing/payment_redirect.html", {"gateway_url": url, "order": order})
    response["Referrer-Policy"] = "origin"
    response["Cache-Control"] = "no-store"
    return response


RESULT_SALT = "billing.payment-result"
# How long a result link keeps working: long enough for the buyer to come
# back to the tab, short enough that an old shared link goes dead.
RESULT_MAX_AGE = 7 * 24 * 3600


def result_url(order):
    return reverse("billing-result", args=[signing.dumps(order.pk, salt=RESULT_SALT, compress=True)])


# The Android app, opened from the browser (Chrome's intent link: it falls
# back to the web app when the app is not installed).
ANDROID_RETURN_URL = (
    "intent://payment#Intent;scheme=pharmenta;package=com.pharmenta.learning;"
    "S.browser_fallback_url=https%3A%2F%2Fapp.pharmenta.ir%2F;end"
)


def _result_context(request, order, message=""):
    in_app = bool(order and order.channel == Order.CHANNEL_ANDROID)
    try:
        # an order from the app is tried again in the app
        retry_url = reverse("site:checkout", args=[order.price_id]) if order and order.price_id and order.channel == Order.CHANNEL_SITE else ""
    except NoReverseMatch:  # the API host has no checkout page
        retry_url = ""
    return {
        "order": order, "message": message, "retry_url": retry_url, "in_app": in_app,
        "return_url": ANDROID_RETURN_URL if in_app else config.current().return_url,
        # Links to the site stay relative on the site's own domain.
        "site_url": "" if getattr(request, "is_site", False) else settings.SITE_PUBLIC_URL.rstrip("/"),
    }


def _failed(request, order, message, status=200):
    return render(request, "billing/payment_failed.html", _result_context(request, order, message), status=status)


@csrf_exempt
def payment_callback(request, kind=None):
    """Where a gateway sends the buyer back -- with a GET (Zarinpal) or a POST
    (SEP). The payment is confirmed with the gateway itself, then the buyer is
    sent on to the result page, so a refresh never posts the receipt twice.
    The bare /callback/ is Zarinpal's from before gateways had their own."""
    params = request.POST if request.method == "POST" else request.GET
    orders = Order.objects.select_related("plan")
    try:
        if kind is None:
            authority = (params.get("Authority") or "").strip()
            order = orders.filter(authority=authority).first() if authority else None
            gateway = get_gateway(order.gateway) if order else None
        else:
            gateway = get_gateway(kind)
            order = gateway.find_order(orders, params)
    except GatewayError:
        return _failed(request, None, "این درگاه پرداخت شناخته نشد.", status=404)
    if order is None:
        return _failed(request, None, "سفارشی برای این پرداخت پیدا نشد.", status=404)
    if order.status == Order.STATUS_PAID or order.gateway != gateway.name:
        return redirect(result_url(order))

    try:
        result = gateway.verify(order, params)
    except GatewayError:
        # The order stays pending: the result page says the outcome is not known yet.
        return redirect(result_url(order))
    if result.ok:
        services.mark_paid(
            order.pk, gateway=order.gateway, ref_id=result.ref_id, card_pan=result.card_pan,
            gateway_ref=result.gateway_ref,
        )
    else:
        services.mark_failed(order, result.message)
    return redirect(result_url(order))


def payment_result(request, token):
    """The page the buyer lands on after the gateway: success, or what went
    wrong and what to do next. The link carries the order signed, so nobody
    can read another buyer's receipt by changing a number."""
    try:
        pk = signing.loads(token, salt=RESULT_SALT, max_age=RESULT_MAX_AGE)
    except signing.BadSignature:
        return _failed(request, None, "این لینک نتیجهٔ پرداخت معتبر نیست یا منقضی شده است.", status=404)
    order = Order.objects.select_related("plan").filter(pk=pk).first()
    if order is None:
        return _failed(request, None, "سفارشی برای این پرداخت پیدا نشد.", status=404)
    if order.status == Order.STATUS_PAID:
        return render(request, "billing/payment_success.html", _result_context(request, order))
    if order.status == Order.STATUS_PENDING:
        return _failed(request, order, (
            "پاسخ درگاه هنوز به ما نرسیده و وضعیت پرداخت روشن نیست. اگر مبلغ از حساب شما کم شده، "
            "یا تا چند دقیقهٔ دیگر اشتراک فعال می‌شود یا بانک ظرف ۷۲ ساعت آن را برمی‌گرداند."
        ))
    return _failed(request, order, order.error if _is_persian(order.error) else "")


def _is_persian(text):
    return any("\u0600" <= ch <= "\u06ff" for ch in text or "")
