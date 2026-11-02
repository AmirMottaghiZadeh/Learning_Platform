from django.conf import settings
from django.db import models


class RateLimitSettings(models.Model):
    """The app's request limits as set in /manage/ (one row). Anything not
    set here keeps the environment's value; see apps.core.ratelimit."""

    # All per-request limits of the API (DRF throttles), on or off.
    enabled = models.BooleanField(default=True)
    # scope -> "<count>/<second|minute|hour|day>", or "off" for no limit on
    # that scope. A scope left out keeps the environment's rate.
    rates = models.JSONField(default=dict, blank=True)
    # The SMS code's own limits, per number and per address (accounts.otp).
    otp_enabled = models.BooleanField(default=True)
    # name -> number; a name left out keeps the environment's value.
    otp = models.JSONField(default=dict, blank=True)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محدودیت درخواست‌ها"
        verbose_name_plural = "محدودیت درخواست‌ها"

    def __str__(self):
        return "RateLimitSettings"
