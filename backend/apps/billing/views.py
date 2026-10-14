"""The app's side of billing: what is for sale, what the learner has, and
buying -- an order, then the gateway, then our callback, which confirms the
payment with the gateway before granting anything."""

from django.db.models import Prefetch
from django.shortcuts import render
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from . import config, services
from .gateways import GatewayError, get_gateway
from .guest import is_guest
from .models import Feature, Order, Plan, PlanFeature
from .serializers import (
    CatalogSerializer,
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


def _priced(request):
    if is_guest(request.user):
        raise PlatformAPIError("Sign in to buy.", code="GUEST_CANNOT_BUY", status_code=403)
    body = PurchaseRequestSerializer(data=request.data)
    body.is_valid(raise_exception=True)
    try:
        price = services.purchasable_price(body.validated_data["price_id"])
        discount = services.find_discount(body.validated_data["discount_code"])
        services.quote(price, discount)
    except services.BillingError as exc:
        raise _billing_error(exc) from exc
    return price, discount


class CatalogView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=CatalogSerializer)
    def get(self, request):
        on_sale = _plans().filter(status=Plan.STATUS_ACTIVE, is_free=False)
        return Response(CatalogSerializer({
            "free": _plans().filter(is_free=True).exclude(status=Plan.STATUS_INACTIVE).first(),
            "plans": [p for p in on_sale if p.kind == Plan.KIND_PLAN],
            "products": [p for p in on_sale if p.kind == Plan.KIND_PRODUCT],
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
    permission_classes = [IsAuthenticated]

    @extend_schema(request=PurchaseRequestSerializer, responses=CheckoutSerializer)
    def post(self, request):
        if not config.current().sales_enabled:
            raise PlatformAPIError("Sales are paused for now.", code="SALES_PAUSED", status_code=503)
        price, discount = _priced(request)
        order = services.create_order(request.user, price, discount)
        if order.payable_toman == 0:
            services.mark_paid(order.pk, gateway="free")
            return Response(CheckoutSerializer({"order_id": order.pk, "status": Order.STATUS_PAID, "payment_url": ""}).data, status=201)

        profile = getattr(request.user, "learner_profile", None)
        try:
            gateway = get_gateway()
            url, authority = gateway.start(
                order,
                request.build_absolute_uri(reverse("billing-callback")),
                description=f"خرید {price.plan.name_fa} · {price.duration_label}",
                mobile=getattr(profile, "phone", None) or "",
                email=request.user.email or "",
            )
        except GatewayError as exc:
            services.mark_failed(order, str(exc))
            raise PlatformAPIError(
                "The payment gateway is not available right now.", code="GATEWAY_ERROR", status_code=502
            ) from exc
        order.gateway, order.authority = gateway.name, authority
        order.save(update_fields=["gateway", "authority"])
        return Response(CheckoutSerializer({"order_id": order.pk, "status": order.status, "payment_url": url}).data, status=201)


class MyOrdersView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OrderSerializer(many=True))
    def get(self, request):
        orders = Order.objects.filter(user=request.user).select_related("plan")[:50]
        return Response(OrderSerializer(orders, many=True).data)


def payment_callback(request):
    """Where the gateway sends the learner back. A plain page, not JSON: it
    opens in their browser, says how it went and links back to the app."""
    authority = (request.GET.get("Authority") or "").strip()
    order = Order.objects.select_related("plan").filter(authority=authority).first() if authority else None
    context = {"order": order, "return_url": config.current().return_url, "ok": False, "message": ""}
    if order is None:
        context["message"] = "سفارشی برای این پرداخت پیدا نشد."
        return render(request, "billing/payment_result.html", context, status=404)

    if order.status == Order.STATUS_PAID:
        context["ok"] = True
        return render(request, "billing/payment_result.html", context)

    try:
        result = get_gateway().verify(order, request.GET)
    except GatewayError:
        context["message"] = "ارتباط با درگاه برقرار نشد. اگر مبلغ از حساب شما کم شده، تا ۷۲ ساعت برمی‌گردد یا با پشتیبانی تماس بگیرید."
        return render(request, "billing/payment_result.html", context, status=502)
    if result.ok:
        order = services.mark_paid(order.pk, gateway=order.gateway, ref_id=result.ref_id, card_pan=result.card_pan)
        context.update(order=order, ok=True)
        return render(request, "billing/payment_result.html", context)
    services.mark_failed(order, result.message)
    context["message"] = result.message
    return render(request, "billing/payment_result.html", context)
