"""Public USD/Rial quote, converted explicitly to toman. No API credentials."""
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_CEILING
import json
import re
from urllib.request import HTTPRedirectHandler, Request, build_opener
from zoneinfo import ZoneInfo

from django.core.cache import caches
from django.db import transaction
from django.utils import timezone

from .models import CreditPackage, CreditSettings

QUOTE_URL = "https://call1.tgju.org/ajax.json"
QUOTE_TTL = timedelta(minutes=5)
MAX_QUOTE_AGE = timedelta(days=3)


class QuoteUnavailable(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None


def package_price(package, config):
    if not package.dollar_priced:
        return package.price_toman
    return int((package.credits / Decimal(1000) * config.usd_per_1000_credits
                * config.usd_to_toman).to_integral_value(rounding=ROUND_CEILING))


def parse_quote(data, *, now=None):
    try:
        row = data["current"]["price_dollar_rl"]
        value = str(row["p"])
        if not re.fullmatch(r"[0-9]+(?:,[0-9]{3})*", value):
            raise ValueError
        rial = Decimal(value.replace(",", ""))
        rate = int((rial / 10).to_integral_value(rounding=ROUND_CEILING))
        quoted_at = datetime.strptime(row["ts"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=ZoneInfo("Asia/Tehran"))
        now = now or timezone.now()
        if not 1 <= rate <= 10000000 or not -timedelta(minutes=5) <= now-quoted_at <= MAX_QUOTE_AGE:
            raise ValueError
        return rate, quoted_at
    except (KeyError, TypeError, ValueError, ArithmeticError):
        raise QuoteUnavailable from None


def fetch_quote():
    try:
        request = Request(QUOTE_URL, headers={"Accept": "application/json", "User-Agent": "Pharmenta-CreditPricing/1.0"})
        with build_opener(NoRedirect).open(request, timeout=3) as response:
            raw = response.read(2000001)
        if len(raw) > 2000000:
            raise ValueError
        return parse_quote(json.loads(raw))
    except Exception:
        raise QuoteUnavailable from None


def quote_ready(config):
    # A manually entered rate is an explicit manager choice. Automatic pricing
    # must have a fresh, confirmed quote; an old fallback is never called live.
    return config.fx_mode == "manual" or (config.fx_source == "tgju"
        and -timedelta(minutes=5) <= timezone.now()-config.fx_quoted_at <= MAX_QUOTE_AGE)


def reprice_packages(config):
    for package in CreditPackage.objects.filter(dollar_priced=True):
        CreditPackage.objects.filter(pk=package.pk).update(price_toman=package_price(package, config))


def refresh(config, *, force=False, enable=False):
    if config.fx_mode != "tgju" and not enable:
        return config
    if not force and config.fx_checked_at and timezone.now()-config.fx_checked_at < QUOTE_TTL:
        return config
    cache = caches["throttle"]
    if not cache.add("ai-credit:fx-refresh", True, 30):
        if force:
            raise QuoteUnavailable
        return CreditSettings.objects.get(pk=config.pk)
    # Keep the short lock until TTL so another process never deletes a newer
    # refresh lease. A failed fetch has a cooldown too, without replacing price.
    checked_at = timezone.now()
    try:
        rate, quoted_at = fetch_quote()
    except QuoteUnavailable:
        CreditSettings.objects.filter(pk=config.pk, fx_mode="tgju").update(fx_checked_at=checked_at)
        if force:
            raise
        return CreditSettings.objects.get(pk=config.pk)
    with transaction.atomic():
        locked = CreditSettings.objects.select_for_update().get(pk=config.pk)
        if locked.fx_mode != "tgju" and not enable:
            return locked
        if not Decimal("0.5") <= Decimal(rate)/locked.usd_to_toman <= Decimal("1.5"):
            locked.fx_checked_at = checked_at
            locked.save(update_fields=["fx_checked_at"])
            if force:
                raise QuoteUnavailable
            return locked
        locked.usd_to_toman, locked.fx_quoted_at = rate, quoted_at
        locked.fx_mode = "tgju"
        locked.fx_source, locked.fx_checked_at = "tgju", checked_at
        locked.save(update_fields=["usd_to_toman", "fx_mode", "fx_quoted_at", "fx_source", "fx_checked_at", "updated_at"])
        reprice_packages(locked)
        return locked
