"""Post-search credit debits. Unknown usage never locks a customer's balance."""
from datetime import timedelta
from decimal import Decimal, ROUND_CEILING
from hashlib import sha256
import json

from django.conf import settings
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.core.exceptions import PlatformAPIError
from .models import CreditAttempt, CreditEntry, CreditPackage, CreditReservation, CreditSettings, CreditWallet

ZERO = Decimal("0")
PRECISION = Decimal("0.000001")
MILLION = Decimal("1000000")
RATES = ("input_per_million", "cached_input_per_million", "cache_write_per_million",
         "cache_write_12h_per_million", "output_per_million", "embedding_per_million")


def current_settings():
    return CreditSettings.objects.get_or_create(pk=1)[0]


def model_signature():
    values = [settings.AI_LAB_MODEL, settings.AI_LAB_BASE_URL.rstrip("/"),settings.AI_LAB_SEARCH_ENGINE,
              settings.AI_LAB_EMBEDDING_MODEL, settings.AI_LAB_EMBEDDING_BASE_URL.rstrip("/"),
              settings.AI_LAB_EMBEDDING_DIMENSIONS, settings.AI_LAB_EMBEDDING_REVISION]
    return sha256(json.dumps(values).encode()).hexdigest()


def pricing_ready(config):
    return (settings.AI_LAB_SEARCH_ENGINE == "hybrid"
            and any((getattr(config, key) or 0) > 0 for key in RATES)
            and config.model_signature == model_signature())


def billing_enabled():
    return current_settings().enabled


def _snapshot(config):
    return {"priced": config.enabled, "revision": config.revision, "model_signature": config.model_signature,
            **{key: str(getattr(config, key)) if getattr(config, key) is not None else None for key in RATES}}


def _entry(wallet, amount, *, source_key, kind, note="", actor=None):
    wallet.balance += amount
    wallet.save(update_fields=["balance", "updated_at"])
    return CreditEntry.objects.create(wallet=wallet, source_key=source_key, kind=kind, amount=amount,
        balance_after=wallet.balance, note=note[:255], actor=actor)


@transaction.atomic
def get_wallet(user):
    wallet, _ = CreditWallet.objects.get_or_create(owner=user)
    wallet = CreditWallet.objects.select_for_update().get(pk=wallet.pk)
    config = current_settings()
    if not wallet.initial_awarded and config.initial_credits > 0:
        _entry(wallet, config.initial_credits, source_key="initial:"+str(wallet.pk), kind="initial")
        wallet.initial_awarded = True
        wallet.save(update_fields=["initial_awarded"])
    return wallet


@transaction.atomic
def start_search(user, job_id):
    config = current_settings()
    if config.enabled and not pricing_ready(config):
        raise PlatformAPIError("تعرفهٔ سرچ هوشمند نیاز به تنظیم دارد؛ کمی بعد دوباره تلاش کنید.",
                               code="AI_CREDIT_PRICING_UNAVAILABLE", status_code=503)
    previous_wallet=CreditWallet.objects.filter(owner=user).first()
    if previous_wallet:
        # Settle terminal work before checking the next request. Lock usage
        # rows before the wallet, matching settle() to avoid lock inversion.
        reconcile(previous_wallet)
    wallet = get_wallet(user)
    previous = CreditReservation.objects.filter(pk=job_id).first()
    if previous:
        if previous.wallet_id != wallet.pk:
            raise PlatformAPIError("درخواست معتبر نیست.", code="INVALID", status_code=400)
        return previous
    if config.enabled and wallet.available <= ZERO:
        raise PlatformAPIError("اعتبار سرچ هوشمند کافی نیست؛ برای ادامه، اعتبار خود را شارژ کنید.",
                               code="AI_CREDIT_INSUFFICIENT", status_code=402,
                               details={"available_credits": str(wallet.available)})
    return CreditReservation.objects.create(id=job_id, wallet=wallet, pricing=_snapshot(config))


def _totals(attempts, pricing):
    totals = {"prompt_tokens": 0, "completion_tokens": 0, "embedding_tokens": 0, "cached_tokens": 0, "cache_write_tokens": 0}
    unknown, cost = 0, ZERO
    input_rate = Decimal(pricing.get("input_per_million") or "0")
    cached_rate = Decimal(pricing.get("cached_input_per_million") or str(input_rate))
    write_rate = Decimal(pricing.get("cache_write_per_million") or str(input_rate))
    write_12h_rate = Decimal(pricing.get("cache_write_12h_per_million") or str(write_rate))
    for attempt in attempts:
        if not attempt.known:
            unknown += 1
            continue
        usage = attempt.usage
        prompt = usage.get("prompt_tokens", 0)
        if attempt.kind == "embedding":
            totals["embedding_tokens"] += prompt
            cost += Decimal(prompt) * Decimal(pricing.get("embedding_per_million") or "0") / MILLION
        else:
            cached = min(prompt, usage.get("cached_tokens", 0))
            written = min(prompt-cached, usage.get("cache_write_tokens", 0))
            written_12h = min(written, usage.get("cache_write_12h_tokens", 0))
            completion = usage.get("completion_tokens", 0)
            totals["prompt_tokens"] += prompt
            totals["completion_tokens"] += completion
            totals["cached_tokens"] += cached
            totals["cache_write_tokens"] += written
            cost += (Decimal(prompt-cached-written)*input_rate + Decimal(cached)*cached_rate
                     + Decimal(written-written_12h)*write_rate + Decimal(written_12h)*write_12h_rate
                     + Decimal(completion)*Decimal(pricing.get("output_per_million") or "0")) / MILLION
    return totals, unknown, min(cost,Decimal("9999999999999999.999999")).quantize(PRECISION, rounding=ROUND_CEILING)


@transaction.atomic
def start_attempt(job_id, sequence, kind):
    reservation = CreditReservation.objects.select_for_update().filter(pk=job_id).first()
    if reservation is None:  # A pre-wallet job remains unpriced.
        return None
    if reservation.status != "tracking":
        from apps.ai_lab.provider import ProviderError
        raise ProviderError("AI_CREDIT_RUN_CLOSED")
    attempt, created = CreditAttempt.objects.get_or_create(reservation=reservation, sequence=sequence, defaults={"kind": kind})
    if not created:
        from apps.ai_lab.provider import ProviderError
        raise ProviderError("AI_CREDIT_ATTEMPT_REPLAY")
    return attempt.pk


def finish_attempt(attempt_id, event):
    if attempt_id is None:
        return
    attempt = CreditAttempt.objects.get(pk=attempt_id)
    raw = event.get("usage", {})
    usage = {name: value for name, value in raw.items()
             if name in {"prompt_tokens", "completion_tokens", "total_tokens"}
             and type(value) is int and 0 <= value <= 10**10}
    required = {"prompt_tokens"} if attempt.kind == "embedding" else {"prompt_tokens", "completion_tokens"}
    cached = event.get("cached_prompt_tokens", 0)
    usage["cached_tokens"] = min(usage.get("prompt_tokens", 0), cached) if type(cached) is int and cached >= 0 else 0
    written = event.get("cache_write_prompt_tokens", 0)
    usage["cache_write_tokens"] = min(usage.get("prompt_tokens", 0)-usage["cached_tokens"], written) if type(written) is int and written >= 0 else 0
    written_12h = event.get("cache_write_12h_prompt_tokens", 0)
    usage["cache_write_12h_tokens"] = min(usage["cache_write_tokens"], written_12h) if type(written_12h) is int and written_12h >= 0 else 0
    CreditAttempt.objects.filter(pk=attempt_id, finished_at__isnull=True).update(
        usage=usage, known=required.issubset(usage), finished_at=timezone.now())


@transaction.atomic
def settle(job_id, *, outcome="", reviewed_charge=None, actor=None, note=""):
    reservation = CreditReservation.objects.select_for_update().filter(pk=job_id).first()
    if reservation is None or reservation.status == "settled":
        return reservation
    totals, unknown, cost = _totals(reservation.attempts.all(), reservation.pricing)
    for name, value in totals.items():
        setattr(reservation, name, value)
    reservation.unknown_attempts = unknown
    reservation.outcome = outcome or reservation.outcome
    pending = bool(unknown and reservation.pricing.get("priced") and reviewed_charge is None)
    charge = cost if reservation.pricing.get("priced") else ZERO
    if reviewed_charge is not None:
        from apps.accounts.access import billing_admin
        if actor is None or not billing_admin(actor) or reservation.status != "pending" or not note.strip():
            raise PlatformAPIError("این مصرف قابل تسویهٔ دستی نیست.", code="INVALID", status_code=400)
        charge = Decimal(reviewed_charge)
        if not charge.is_finite() or not ZERO <= charge <= Decimal("9999999999999999.999999"):
            raise PlatformAPIError("مبلغ مصرف معتبر نیست.", code="INVALID", status_code=400)
    wallet = CreditWallet.objects.select_for_update().get(pk=reservation.wallet_id)
    delta = charge - reservation.charged
    if delta:
        _entry(wallet, -delta, source_key=f"search:{reservation.pk}:{'review' if reviewed_charge is not None else format(charge, 'f')}",
               kind="search", note=note, actor=actor)
    reservation.status, reservation.charged = "pending" if pending else "settled", charge
    reservation.settled_at = None if pending else timezone.now()
    reservation.save()
    return reservation


def reconcile(wallet):
    """Finish terminal jobs after a lost worker/finalization, without inference."""
    from apps.ai_lab.models import SearchRun
    from apps.ai_lab import jobs
    for reservation in wallet.reservations.exclude(status="settled").order_by("-status","created_at")[:20]:
        run = SearchRun.objects.filter(pk=reservation.pk).first()
        if run and run.status in {"admitting", "queued", "running"}:
            jobs.read(str(run.pk), run.owner_id)
            run.refresh_from_db()
        if run is None or run.status in {"complete", "failed"}:
            settle(reservation.pk, outcome=run.status if run else "expired")


@transaction.atomic
def adjust(user, amount, *, actor, note, key):
    from apps.accounts.access import billing_admin
    if not billing_admin(actor):
        raise PlatformAPIError("دسترسی مدیریت اعتبار ندارید.",code="FORBIDDEN",status_code=403)
    wallet = get_wallet(user)
    source = "adjustment:"+str(key)
    existing = CreditEntry.objects.filter(source_key=source).first()
    if existing:
        if existing.wallet_id != wallet.pk or existing.amount != Decimal(amount):
            raise PlatformAPIError("شناسهٔ اصلاح تکراری است.", code="INVALID", status_code=409)
        return existing
    if not note.strip():
        raise PlatformAPIError("توضیح اصلاح اعتبار الزامی است.", code="INVALID", status_code=400)
    return _entry(wallet, Decimal(amount), source_key=source, kind="adjustment", actor=actor, note=note)


@transaction.atomic
def credit_order(order):
    wallet = get_wallet(order.user)
    source = "order:"+str(order.pk)
    existing = CreditEntry.objects.filter(source_key=source).first()
    if existing:
        return existing
    return _entry(wallet, order.credit_amount, source_key=source, kind="topup", note=order.item_name)


def summary(user):
    wallet = get_wallet(user)
    reconcile(wallet)
    wallet.refresh_from_db()
    config = current_settings()
    ready = not config.enabled or pricing_ready(config)
    usage = wallet.reservations.filter(created_at__gte=timezone.now()-timedelta(days=30)).aggregate(charged=Sum("charged"))
    return {"balance": str(wallet.balance), "available": str(wallet.available),
            "billing_enabled": config.enabled, "pricing_ready": ready,
            "exhausted": bool(config.enabled and wallet.balance <= ZERO),
            "can_search": ready and (not config.enabled or wallet.available > ZERO),
            "usage_30_days": {"credits": str(usage["charged"] or ZERO)}}
