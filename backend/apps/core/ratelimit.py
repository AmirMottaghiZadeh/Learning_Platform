"""The app's request limits in force: what the operator set in /manage/
(the RateLimitSettings row), over the environment's defaults.

Two kinds:

- **Request limits** -- the API's throttles (apps.core.throttling): how many
  requests one address, or one signed-in user, may make in a while, per
  scope. One switch turns them all off; each scope can be left at its
  default, given its own rate, or set to no limit.
- **SMS code limits** -- accounts.otp's own checks, per phone number and per
  address: the gap before a new code, codes per window and per day. These
  are what protect the SMS credit, so they have a switch of their own.

The row is read on every throttled request, so it is kept in memory for a
short while: a save clears it at once in that process, and the other
workers pick it up within CACHE_SECONDS.
"""

import re
import time
from dataclasses import dataclass

from django.conf import settings
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import RateLimitSettings

CACHE_SECONDS = 30
_cached = {"at": 0.0, "row": None, "loaded": False}

# scope, what it limits, whose requests are counted
SCOPES = [
    ("anon", "همهٔ درخواست‌های بدون ورود", "هر نشانی IP، روی همهٔ API"),
    ("user", "همهٔ درخواست‌های کاربران واردشده", "هر کاربر، روی همهٔ API"),
    ("auth_login", "ورود با رمز", "هر نشانی IP"),
    ("auth_register", "ثبت‌نام با ایمیل", "هر نشانی IP"),
    ("auth_otp_request", "درخواست کد پیامکی", "هر نشانی IP"),
    ("auth_otp_verify", "وارد کردن کد پیامکی", "هر نشانی IP"),
    ("auth_password_set", "انتخاب رمز بعد از ثبت‌نام پیامکی", "هر نشانی IP"),
    ("auth_password_reset_request", "درخواست بازیابی رمز", "هر نشانی IP"),
    ("auth_password_reset_confirm", "تأیید بازیابی رمز", "هر نشانی IP"),
    ("guest_session", "ساخت حساب مهمان", "هر نشانی IP"),
]
SCOPE_KEYS = [s[0] for s in SCOPES]

UNITS = [("second", "ثانیه"), ("minute", "دقیقه"), ("hour", "ساعت"), ("day", "روز")]
UNIT_NAMES = dict(UNITS)
# DRF reads a rate's period by its first letter ("5/min" -> 60 s)
_RATE_RE = re.compile(r"^\s*(\d+)\s*/\s*([smhd])[a-z]*\s*$", re.I)
_UNIT_BY_LETTER = {"s": "second", "m": "minute", "h": "hour", "d": "day"}
MAX_COUNT = 1_000_000

# name, what it is, smallest value, largest value
OTP_FIELDS = [
    ("resend_seconds", "فاصلهٔ کمینه بین دو کد برای یک شماره (ثانیه)", 0, 3600),
    ("window_seconds", "طول بازهٔ شمارش (ثانیه)", 60, 86400),
    ("max_per_phone_per_window", "حداکثر کد برای یک شماره در این بازه", 1, 1000),
    ("max_per_ip_per_window", "حداکثر کد از یک نشانی IP در این بازه", 1, 10000),
    ("max_per_phone_per_day", "حداکثر کد برای یک شماره در ۲۴ ساعت", 1, 1000),
]
OTP_KEYS = [f[0] for f in OTP_FIELDS]
# with the SMS code limits off: nothing waits or runs out
OTP_UNLIMITED = {
    "resend_seconds": 0,
    "window_seconds": 600,
    "max_per_phone_per_window": 10**9,
    "max_per_ip_per_window": 10**9,
    "max_per_phone_per_day": 10**9,
}


def parse_rate(rate):
    """"5/min" -> (5, "minute"); None when it is not a rate."""
    match = _RATE_RE.match(rate or "")
    if not match:
        return None
    return int(match.group(1)), _UNIT_BY_LETTER[match.group(2).lower()]


def format_rate(count, unit):
    return f"{int(count)}/{unit}"


def describe_rate(rate):
    """"5/minute" -> "۵ در دقیقه"; "بدون سقف" for None."""
    parsed = parse_rate(rate) if rate else None
    if not parsed:
        return "بدون سقف"
    count, unit = parsed
    return f"{count:,} در {UNIT_NAMES[unit]}".translate(str.maketrans("0123456789,", "۰۱۲۳۴۵۶۷۸۹٬"))


def default_rate(scope):
    """The environment's rate for `scope` (REST_FRAMEWORK), or None."""
    return settings.REST_FRAMEWORK.get("DEFAULT_THROTTLE_RATES", {}).get(scope)


def default_otp():
    return {
        "resend_seconds": settings.OTP_RESEND_SECONDS,
        "window_seconds": settings.OTP_WINDOW_SECONDS,
        "max_per_phone_per_window": settings.OTP_MAX_PER_PHONE_PER_WINDOW,
        "max_per_ip_per_window": settings.OTP_MAX_PER_IP_PER_WINDOW,
        "max_per_phone_per_day": settings.OTP_MAX_PER_PHONE_PER_DAY,
    }


@dataclass
class Limits:
    enabled: bool
    # scope -> rate in force ("5/minute"), None = no limit
    rates: dict
    # scope -> "default" | "custom" | "off"
    modes: dict
    otp_enabled: bool
    # the SMS code limits in force
    otp: dict
    # the SMS code limits as set, or the environment's
    otp_set: dict


def _load():
    now = time.monotonic()
    if not _cached["loaded"] or now - _cached["at"] > CACHE_SECONDS:
        try:
            row = RateLimitSettings.objects.first()
        except Exception:
            # no table yet (a migration not run): the environment's limits
            row = None
        _cached.update(row=row, at=now, loaded=True)
    return _cached["row"]


def clear_cache():
    _cached.update(loaded=False, row=None)


@receiver([post_save, post_delete], sender=RateLimitSettings)
def _forget(**kwargs):
    clear_cache()


def current():
    row = _load()
    overrides = dict(row.rates or {}) if row else {}
    rates, modes = {}, {}
    for scope in SCOPE_KEYS:
        value = overrides.get(scope)
        if value == "off":
            rates[scope], modes[scope] = None, "off"
        elif value and parse_rate(value):
            rates[scope], modes[scope] = value, "custom"
        else:
            rates[scope], modes[scope] = default_rate(scope), "default"
    otp_set = default_otp()
    for key, value in ((row.otp or {}) if row else {}).items():
        if key in otp_set and isinstance(value, int):
            otp_set[key] = value
    otp_enabled = row.otp_enabled if row else True
    return Limits(
        enabled=row.enabled if row else True,
        rates=rates,
        modes=modes,
        otp_enabled=otp_enabled,
        otp=otp_set if otp_enabled else dict(OTP_UNLIMITED),
        otp_set=otp_set,
    )


def rate_for(scope, fallback=None):
    """The rate in force for a throttle scope: None means no limit."""
    limits = current()
    if not limits.enabled:
        return None
    if scope in limits.modes:
        return limits.rates[scope]
    return fallback


def otp_limit(name):
    """One of the SMS code limits in force (OTP_KEYS)."""
    return current().otp[name]
