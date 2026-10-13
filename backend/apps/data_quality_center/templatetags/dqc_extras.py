from zoneinfo import ZoneInfo

from django import template
from django.utils import timezone

register = template.Library()

_FA_DIGITS = str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹")
# The console's operators work in Iran, whatever zone the server keeps.
TEHRAN = ZoneInfo("Asia/Tehran")

STATUS = {
    "draft": ("پیش‌نویس", "teal"),
    "pending": ("در انتظار تأیید", "warn"),
    "changes_requested": ("نیاز به اصلاح", "orange"),
    "approved": ("تأیید و اعمال شد", "ok"),
    "rejected": ("ردشده", "danger"),
    "discarded": ("کنارگذاشته", "muted"),
}

ACTIONS = {
    "submitted": ("ارسال برای تأیید", "teal"),
    "resubmitted": ("ارسال دوباره", "teal"),
    "withdrawn": ("پس گرفته شد", "muted"),
    "changes_requested": ("درخواست اصلاح", "orange"),
    "approved": ("تأیید و اعمال", "ok"),
    "rejected": ("رد", "danger"),
    "discarded": ("کنار گذاشته شد", "muted"),
    "revert_requested": ("درخواست بازگردانی", "warn"),
}


@register.filter
def dict_get(mapping, key):
    """`{{ some_dict|dict_get:dynamic_key }}` -- Django's dot lookup only
    takes a literal key written in the template, not another template
    variable, so a dict keyed by a per-row value needs this instead."""
    return mapping.get(key)


@register.filter
def fa_digits(value):
    return str(value).translate(_FA_DIGITS)


@register.filter
def status_label(status):
    return STATUS.get(status, (status, "muted"))[0]


@register.filter
def status_tone(status):
    return STATUS.get(status, (status, "muted"))[1]


@register.filter
def action_label(action):
    return ACTIONS.get(action, (action, "muted"))[0]


@register.filter
def action_tone(action):
    return ACTIONS.get(action, (action, "muted"))[1]


@register.filter
def tehran(value, fmt="%Y/%m/%d %H:%M"):
    """A timestamp in Tehran time, with Persian digits."""
    if not value:
        return ""
    return timezone.localtime(value, TEHRAN).strftime(fmt).translate(_FA_DIGITS)


@register.filter
def ago(value):
    """"همین حالا", "۱۲ دقیقه پیش", "۳ روز پیش" -- then the date."""
    if not value:
        return ""
    seconds = (timezone.now() - value).total_seconds()
    if seconds < 60:
        return "همین حالا"
    if seconds < 3600:
        return f"{int(seconds // 60)} دقیقه پیش".translate(_FA_DIGITS)
    if seconds < 86400:
        return f"{int(seconds // 3600)} ساعت پیش".translate(_FA_DIGITS)
    if seconds < 86400 * 7:
        return f"{int(seconds // 86400)} روز پیش".translate(_FA_DIGITS)
    return tehran(value, "%Y/%m/%d")


@register.filter
def percent(part, whole):
    try:
        return round(100 * int(part) / int(whole)) if int(whole) else 0
    except (TypeError, ValueError):
        return 0
