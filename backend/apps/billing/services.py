"""Who may use what, and the purchase -> access path.

A learner's features are the free plan's (read live) plus the feature
snapshot of every Entitlement active right now. When two sources give the
same feature, the more generous one wins: unlimited beats any cap, and
between caps the larger per-month equivalent wins.
"""

from dataclasses import dataclass
from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.utils import timezone

from .jalali import month_start
from .models import (
    PERIOD_DAY,
    PERIOD_MONTH,
    AdminAction,
    DiscountCode,
    Entitlement,
    Feature,
    Order,
    Plan,
    PlanPrice,
    UsageRecord,
)

# Days and months roll over on Tehran's clock and calendar, whatever zone
# the server keeps.
TEHRAN = ZoneInfo("Asia/Tehran")


class BillingError(ValueError):
    def __init__(self, message, code="BILLING_ERROR"):
        super().__init__(message)
        self.message = message
        self.code = code


# -- features a learner has -------------------------------------------------

def free_plan():
    return (
        Plan.objects.filter(is_free=True)
        .exclude(status=Plan.STATUS_INACTIVE)
        .prefetch_related("plan_features__feature")
        .first()
    )


def active_entitlements(user, when=None):
    when = when or timezone.now()
    return (
        Entitlement.objects.filter(user=user, revoked_at__isnull=True, starts_at__lte=when)
        .filter(Q(ends_at__isnull=True) | Q(ends_at__gt=when))
        .select_related("plan")
    )


def _monthly(grant):
    if grant["limit"] is None:
        return float("inf")
    return grant["limit"] * (30 if grant["period"] == PERIOD_DAY else 1)


def effective_features(user, when=None):
    """{feature_key: {"limit": int | None, "period": str, "sources": [plan name]}}"""
    merged = {}

    def take(key, grant, source):
        current = merged.get(key)
        if current is None or _monthly(grant) > _monthly(current):
            merged[key] = {"limit": grant["limit"], "period": grant["period"], "sources": [source]}
        elif source not in current["sources"]:
            current["sources"].append(source)

    plan = free_plan()
    if plan is not None:
        for pf in plan.plan_features.all():
            take(pf.feature.key, pf.snapshot(), plan.name_fa)
    for ent in active_entitlements(user, when):
        for key, grant in (ent.features or {}).items():
            take(key, {"limit": grant.get("limit"), "period": grant.get("period") or ""}, ent.plan.name_fa)
    return merged


def period_start(period, when=None):
    today = timezone.localtime(when or timezone.now(), TEHRAN).date()
    return month_start(today) if period == PERIOD_MONTH else today


def usage_count(user, key, period, when=None):
    return UsageRecord.objects.filter(
        user=user, feature_key=key, period=period, period_start=period_start(period, when)
    ).count()


@dataclass
class Access:
    allowed: bool
    reason: str = ""  # "" | "not_in_plan" | "quota"
    limit: int | None = None
    period: str = ""
    used: int = 0


def check_feature(user, key, *, item=None, consume=False):
    """Whether `user` may use feature `key` now; with `consume`, also count
    this use of `item` against the feature's cap. A feature no plan sells
    any more (deactivated) is open to everyone."""
    feature = Feature.objects.filter(key=key).only("is_active").first()
    if feature is None or not feature.is_active:
        return Access(True)
    grant = effective_features(user).get(key)
    if grant is None:
        return Access(False, "not_in_plan")
    # A cap counts items (an article, a question); a call naming no item --
    # an image inside an article already opened -- needs the feature only.
    if grant["limit"] is None or item is None:
        return Access(True)

    period, limit = grant["period"] or PERIOD_DAY, grant["limit"]
    start = period_start(period)
    records = UsageRecord.objects.filter(user=user, feature_key=key, period=period, period_start=start)
    used = records.count()
    if item is not None and records.filter(item_key=str(item)[:200]).exists():
        return Access(True, limit=limit, period=period, used=used)
    if used >= limit:
        return Access(False, "quota", limit=limit, period=period, used=used)
    if consume and item is not None:
        try:
            with transaction.atomic():
                UsageRecord.objects.create(
                    user=user, feature_key=key, period=period, period_start=start, item_key=str(item)[:200]
                )
            used += 1
        except IntegrityError:
            pass  # the same item counted by a concurrent request
    return Access(True, limit=limit, period=period, used=used)


def content_lock(user, scope_type, value):
    """The content features fencing off this content that `user` has none
    of -- empty when the content is open to them."""
    value = (value or "").strip()
    if not value:
        return []
    fences = Feature.objects.filter(kind=Feature.KIND_CONTENT, is_active=True, scope_type=scope_type)
    if scope_type == "atc_prefix":
        matching = [f for f in fences if f.scope_value and value.upper().startswith(f.scope_value.upper())]
    else:
        matching = [f for f in fences if f.scope_value == value]
    if not matching:
        return []
    have = effective_features(user)
    if any(f.key in have for f in matching):
        return []
    return matching


# -- granting access --------------------------------------------------------

def plan_snapshot(plan):
    return {
        pf.feature.key: pf.snapshot()
        for pf in plan.plan_features.select_related("feature").filter(feature__is_active=True)
    }


def grant(user, plan, *, days, source, order=None, actor=None, note=""):
    """Give `user` the plan for `days` (None = permanent). A renewal of a
    plan they still hold starts when the current one ends, so no paid day
    is lost."""
    now = timezone.now()
    starts = now
    if days is not None:
        latest = (
            active_entitlements(user, now)
            .filter(plan=plan, ends_at__isnull=False)
            .order_by("-ends_at")
            .first()
        )
        if latest is not None:
            starts = latest.ends_at
    return Entitlement.objects.create(
        user=user,
        plan=plan,
        source=source,
        order=order,
        starts_at=starts,
        ends_at=starts + timedelta(days=days) if days is not None else None,
        features=plan_snapshot(plan),
        granted_by=actor,
        note=note[:255],
    )


def extend(entitlement, days):
    if entitlement.ends_at is None:
        raise BillingError("این دسترسی دائمی است و تمدید لازم ندارد.", "PERMANENT")
    base = max(entitlement.ends_at, timezone.now())
    entitlement.ends_at = base + timedelta(days=days)
    entitlement.save(update_fields=["ends_at"])
    return entitlement


def revoke(entitlement, actor=None):
    if entitlement.revoked_at is None:
        entitlement.revoked_at = timezone.now()
        entitlement.revoked_by = actor
        entitlement.save(update_fields=["revoked_at", "revoked_by"])
    return entitlement


# -- buying -----------------------------------------------------------------

def find_discount(code):
    code = (code or "").strip().upper()
    if not code:
        return None
    discount = DiscountCode.objects.filter(code=code).first()
    if discount is None:
        raise BillingError("این کد تخفیف وجود ندارد.", "DISCOUNT_NOT_FOUND")
    return discount


def quote(price, discount=None):
    """(amount, discount_toman, payable) for buying `price` with `discount`,
    or a BillingError saying why the code does not apply."""
    amount = price.price_toman
    if discount is None:
        return amount, 0, amount
    now = timezone.now()
    if not discount.is_active:
        raise BillingError("این کد تخفیف غیرفعال است.", "DISCOUNT_INACTIVE")
    if discount.starts_at and discount.starts_at > now:
        raise BillingError("زمان استفاده از این کد هنوز نرسیده است.", "DISCOUNT_NOT_STARTED")
    if discount.ends_at and discount.ends_at <= now:
        raise BillingError("مهلت این کد تخفیف تمام شده است.", "DISCOUNT_EXPIRED")
    if discount.max_uses is not None and discount.used_count >= discount.max_uses:
        raise BillingError("ظرفیت استفاده از این کد تمام شده است.", "DISCOUNT_USED_UP")
    if discount.plans.exists() and not discount.plans.filter(pk=price.plan_id).exists():
        raise BillingError("این کد برای این پلن نیست.", "DISCOUNT_NOT_FOR_PLAN")
    if discount.percent is not None:
        off = amount * discount.percent // 100
    else:
        off = min(discount.amount_toman, amount)
    return amount, off, amount - off


def purchasable_price(price_id):
    price = (
        PlanPrice.objects.select_related("plan")
        .filter(pk=price_id, is_active=True, plan__status=Plan.STATUS_ACTIVE, plan__is_free=False)
        .first()
    )
    if price is None:
        raise BillingError("این قیمت برای خرید در دسترس نیست.", "PRICE_NOT_AVAILABLE")
    return price


def create_order(user, price, discount=None):
    amount, off, payable = quote(price, discount)
    return Order.objects.create(
        user=user,
        plan=price.plan,
        price=price,
        duration_days=price.duration_days,
        amount_toman=amount,
        discount=discount,
        discount_toman=off,
        payable_toman=payable,
    )


def mark_paid(order_id, *, gateway, ref_id="", card_pan=""):
    """Settle a verified payment: idempotent -- a second call (the gateway
    retrying the callback, a double click) changes nothing."""
    with transaction.atomic():
        order = Order.objects.select_for_update().select_related("plan").get(pk=order_id)
        if order.status == Order.STATUS_PAID:
            return order
        order.status = Order.STATUS_PAID
        order.gateway = gateway
        order.ref_id = ref_id[:64]
        order.card_pan = card_pan[:32]
        order.paid_at = timezone.now()
        order.error = ""
        order.save(update_fields=["status", "gateway", "ref_id", "card_pan", "paid_at", "error"])
        if order.discount_id:
            DiscountCode.objects.filter(pk=order.discount_id).update(used_count=F("used_count") + 1)
        grant(order.user, order.plan, days=order.duration_days, source=Entitlement.SOURCE_PURCHASE, order=order)
    return order


def mark_failed(order, message):
    Order.objects.filter(pk=order.pk, status=Order.STATUS_PENDING).update(
        status=Order.STATUS_FAILED, error=message[:255]
    )


# -- audit ------------------------------------------------------------------

def record(request, action, summary, *, target_user=None, details=None):
    ip = request.META.get("REMOTE_ADDR") if request is not None else None
    return AdminAction.objects.create(
        actor=request.user if request is not None else None,
        target_user=target_user,
        action=action,
        summary=summary[:255],
        details=details or {},
        ip_address=ip or None,
    )
