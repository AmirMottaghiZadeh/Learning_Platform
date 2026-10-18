"""The billing configuration in force: the console's BillingSettings row
where it sets a value, the environment otherwise; and the payment gateways
-- the console's PaymentGateway rows, or with none set up, the one the
environment names.

Content views read this on every request, so the rows are kept in memory
for a short while; a save in the console clears them at once in that
process, and the other workers pick them up within CACHE_SECONDS.
"""

import time
from dataclasses import dataclass

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import BillingSettings, PaymentGateway

CACHE_SECONDS = 30
_cached = {"at": 0.0, "row": None, "gateways": (), "loaded": False}


@dataclass(frozen=True)
class GatewaySpec:
    kind: str
    name: str
    merchant_id: str
    sandbox: bool
    enabled: bool
    # "panel" (a PaymentGateway row) or "env".
    source: str


@dataclass
class BillingConfig:
    # Every gateway set up, enabled or not, in the order they are offered.
    gateways: tuple
    return_url: str
    enforcement: bool
    sales_enabled: bool
    guest_access: bool
    # Where each value came from, for the console: "panel" or "env".
    sources: dict


def _load():
    now = time.monotonic()
    if not _cached["loaded"] or now - _cached["at"] > CACHE_SECONDS:
        _cached.update(
            row=BillingSettings.objects.first(), gateways=tuple(PaymentGateway.objects.all()), at=now, loaded=True
        )


def row():
    _load()
    return _cached["row"]


def clear_cache():
    _cached.update(row=None, gateways=(), at=0.0, loaded=False)


@receiver(post_save, sender=BillingSettings)
@receiver(post_delete, sender=BillingSettings)
@receiver(post_save, sender=PaymentGateway)
@receiver(post_delete, sender=PaymentGateway)
def _settings_changed(**kwargs):
    clear_cache()


ENV_NAMES = {"zarinpal": "زرین‌پال", "sep": "سامان (سپ)", "zibal": "زیبال", "fake": "آزمایشی محلی"}


def _gateways():
    _load()
    rows = _cached["gateways"]
    if rows:
        return tuple(
            GatewaySpec(g.kind, g.display_name, g.merchant_id, g.sandbox, g.is_enabled, "panel") for g in rows
        )
    kind = settings.BILLING_GATEWAY
    merchant = ""
    sandbox = False
    if kind == "zarinpal":
        merchant, sandbox = settings.ZARINPAL_MERCHANT_ID, settings.ZARINPAL_SANDBOX
    elif kind == "zibal":
        merchant = getattr(settings, "ZIBAL_MERCHANT", "") or getattr(settings, "ZIBAL_MERCHANT_ID", "")
        sandbox = settings.ZIBAL_SANDBOX
    return (GatewaySpec(kind, ENV_NAMES.get(kind, kind), merchant, sandbox, True, "env"),)


def current():
    r = row()
    sources = {}

    def pick(name, panel_value, env_value, use_panel):
        sources[name] = "panel" if use_panel else "env"
        return panel_value if use_panel else env_value

    return BillingConfig(
        gateways=_gateways(),
        return_url=pick("return_url", r and r.return_url, settings.BILLING_RETURN_URL, bool(r and r.return_url)),
        enforcement=pick(
            "enforcement", r and r.enforcement_enabled, settings.BILLING_ENFORCEMENT_ENABLED,
            r is not None and r.enforcement_enabled is not None,
        ),
        sales_enabled=r.sales_enabled if r is not None else True,
        guest_access=bool(r and r.guest_access_enabled),
        sources=sources,
    )


def enabled_gateways():
    return [g for g in current().gateways if g.enabled]


def gateway_spec(kind):
    """The gateway of this kind, enabled or not: a payment started before it
    was switched off still has to be verified."""
    return next((g for g in current().gateways if g.kind == kind), None)
