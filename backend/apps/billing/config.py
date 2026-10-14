"""The billing configuration in force: the console's BillingSettings row
where it sets a value, the environment otherwise.

Content views read this on every request, so the row is kept in memory for
a short while; a save in the console clears it at once in that process, and
the other workers pick it up within CACHE_SECONDS.
"""

import time
from dataclasses import dataclass

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import BillingSettings

CACHE_SECONDS = 30
_cached = {"at": 0.0, "row": None, "loaded": False}


@dataclass
class BillingConfig:
    gateway: str
    merchant_id: str
    sandbox: bool
    return_url: str
    enforcement: bool
    sales_enabled: bool
    # Where each value came from, for the console: "panel" or "env".
    sources: dict


def row():
    now = time.monotonic()
    if not _cached["loaded"] or now - _cached["at"] > CACHE_SECONDS:
        _cached.update(row=BillingSettings.objects.first(), at=now, loaded=True)
    return _cached["row"]


def clear_cache():
    _cached.update(row=None, at=0.0, loaded=False)


@receiver(post_save, sender=BillingSettings)
@receiver(post_delete, sender=BillingSettings)
def _settings_changed(**kwargs):
    clear_cache()


def current():
    r = row()
    sources = {}

    def pick(name, panel_value, env_value, use_panel):
        sources[name] = "panel" if use_panel else "env"
        return panel_value if use_panel else env_value

    return BillingConfig(
        gateway=pick("gateway", r and r.gateway, settings.BILLING_GATEWAY, bool(r and r.gateway)),
        merchant_id=pick("merchant_id", r and r.zarinpal_merchant_id, settings.ZARINPAL_MERCHANT_ID, bool(r and r.zarinpal_merchant_id)),
        sandbox=pick("sandbox", r and r.zarinpal_sandbox, settings.ZARINPAL_SANDBOX, r is not None and r.zarinpal_sandbox is not None),
        return_url=pick("return_url", r and r.return_url, settings.BILLING_RETURN_URL, bool(r and r.return_url)),
        enforcement=pick(
            "enforcement", r and r.enforcement_enabled, settings.BILLING_ENFORCEMENT_ENABLED,
            r is not None and r.enforcement_enabled is not None,
        ),
        sales_enabled=r.sales_enabled if r is not None else True,
        sources=sources,
    )
