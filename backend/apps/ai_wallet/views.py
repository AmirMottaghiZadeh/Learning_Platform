from hashlib import sha256
import json

from django.conf import settings
from django.core import signing
from django.db import IntegrityError, transaction
from django.urls import reverse
from drf_spectacular.utils import extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.ai_lab.views import require_lab
from apps.billing import config as billing_config
from apps.billing.models import Order
from apps.billing.views import PAY_START_SALT, pay_start_url
from apps.core.exceptions import PlatformAPIError
from . import services
from . import fx
from .models import CreditPackage


def private_response(data, status=200):
    response = Response(data, status=status)
    response["Cache-Control"] = "private, no-store"
    return response


class WalletView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=dict)
    def get(self, request):
        config = fx.refresh(services.current_settings())
        data = services.summary(request.user)
        gateways = billing_config.enabled_gateways()
        data.update(packages=[{"id": p.pk, "name": p.name, "credits": str(p.credits), "price_toman": fx.package_price(p,config)}
                              for p in CreditPackage.objects.filter(active=True)],
            gateways=[{"kind": g.kind, "name": g.name} for g in gateways],
            completed_topups=list(Order.objects.filter(user=request.user,purpose=Order.PURPOSE_SEARCH_CREDIT)
                .exclude(status=Order.STATUS_PENDING).values_list("credit_request_id",flat=True)[:20]),
            topups_enabled=bool(data["billing_enabled"] and data["pricing_ready"] and gateways and billing_config.current().sales_enabled
                and (fx.quote_ready(config) or not CreditPackage.objects.filter(active=True,dollar_priced=True).exists())))
        return private_response(data)


class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=dict)
    def get(self, request):
        try:
            offset = int(request.query_params.get("offset", 0))
            if not 0 <= offset <= 100000:
                raise ValueError
        except (TypeError, ValueError):
            raise PlatformAPIError("صفحه معتبر نیست.", code="INVALID", status_code=400) from None
        wallet = services.get_wallet(request.user)
        services.reconcile(wallet)
        entries = list(wallet.entries.all()[offset:offset+21])
        searches = {str(row.pk): row for row in wallet.reservations.filter(pk__in=[
            entry.source_key.split(":")[1] for entry in entries if entry.kind == "search"])}
        def usage(row):
            return {"usage_pending": bool(row.unknown_attempts)}
        transactions = [{"id": str(entry.pk), "kind": entry.kind, "label": entry.get_kind_display(),
            "amount": str(entry.amount), "balance_after": str(entry.balance_after),
            "note": entry.note, "created_at": entry.created_at.isoformat(),
            **(usage(searches[entry.source_key.split(":")[1]]) if entry.kind == "search" and entry.source_key.split(":")[1] in searches else {})} for entry in entries[:20]]
        pending = [{"id": str(row.pk), "status": row.status,
                    "created_at": row.created_at.isoformat(), **usage(row)} for row in wallet.reservations.exclude(status="settled")[:20]]
        return private_response({"transactions": transactions, "pending": pending,
                                 "next_offset": offset+20 if len(entries)>20 else None})


class TopUpSerializer(serializers.Serializer):
    package_id = serializers.IntegerField(min_value=1)
    request_id = serializers.RegexField(r"^[A-Za-z0-9_.:-]{1,128}$")
    gateway = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")
    client = serializers.ChoiceField(choices=["web", "android"], default="web")
    expected_price_toman = serializers.IntegerField(min_value=1, required=False)


class TopUpView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=TopUpSerializer, responses={201: dict})
    def post(self, request):
        require_lab(request.user)
        serializer = TopUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        body = serializer.validated_data
        fingerprint = sha256(json.dumps(dict(body), sort_keys=True).encode()).hexdigest()
        order = Order.objects.filter(user=request.user, purpose=Order.PURPOSE_SEARCH_CREDIT,
                                     credit_request_id=body["request_id"]).first()
        if order is not None and order.credit_request_fingerprint != fingerprint:
            raise PlatformAPIError("شناسهٔ خرید قبلاً برای درخواست دیگری استفاده شده است.", code="IDEMPOTENCY_CONFLICT", status_code=409)
        if order is None:
            config = fx.refresh(services.current_settings())
            if not config.enabled or not services.pricing_ready(config) or not billing_config.current().sales_enabled:
                raise PlatformAPIError("شارژ اعتبار فعلاً فعال نیست.", code="AI_CREDIT_TOPUP_DISABLED", status_code=503)
            package = CreditPackage.objects.filter(pk=body["package_id"], active=True).first()
            if package is None:
                raise PlatformAPIError("این بستهٔ شارژ در دسترس نیست.", code="NOT_FOUND", status_code=404)
            kinds = [g.kind for g in billing_config.enabled_gateways()]
            if not kinds or (body["gateway"] and body["gateway"] not in kinds):
                raise PlatformAPIError("درگاه انتخاب‌شده در دسترس نیست.", code="NO_GATEWAY", status_code=503)
            try:
                with transaction.atomic():
                    config = services.CreditSettings.objects.select_for_update().get(pk=1)
                    package = CreditPackage.objects.select_for_update().get(pk=package.pk)
                    if not package.active or not config.enabled or not services.pricing_ready(config):
                        raise PlatformAPIError("این بسته فعلاً قابل خرید نیست.",code="AI_CREDIT_TOPUP_DISABLED",status_code=503)
                    if package.dollar_priced and not fx.quote_ready(config):
                        raise PlatformAPIError("دریافت نرخ تازهٔ بسته انجام نشد؛ کمی بعد دوباره تلاش کنید.",code="AI_CREDIT_RATE_UNAVAILABLE",status_code=503)
                    price = fx.package_price(package,config)
                    if "expected_price_toman" in body and body["expected_price_toman"] != price:
                        raise PlatformAPIError("قیمت بسته به‌روز شد؛ قیمت تازه را بررسی و دوباره خرید را انتخاب کنید.",
                            code="AI_CREDIT_PRICE_CHANGED",status_code=409,details={"price_toman":price})
                    order = Order.objects.create(user=request.user, purpose=Order.PURPOSE_SEARCH_CREDIT,
                        credit_package=package, credit_amount=package.credits, item_label=package.name,
                        amount_toman=price, payable_toman=price,
                        credit_request_id=body["request_id"], credit_request_fingerprint=fingerprint, channel=body["client"])
            except IntegrityError:
                order = Order.objects.get(user=request.user, purpose=Order.PURPOSE_SEARCH_CREDIT, credit_request_id=body["request_id"])
                if order.credit_request_fingerprint != fingerprint:
                    raise PlatformAPIError("شناسهٔ خرید تکراری است.", code="IDEMPOTENCY_CONFLICT", status_code=409) from None
        payment_url = pay_start_url(order, body["gateway"])
        if settings.ENVIRONMENT == "local":
            token = signing.dumps({"o": order.pk, "g": body["gateway"]}, salt=PAY_START_SALT, compress=True)
            payment_url = request.build_absolute_uri(reverse("ai-credit-pay-start", args=[token]))
        return private_response({"order_id": order.pk, "status": order.status, "payment_url": payment_url}, status=201)
