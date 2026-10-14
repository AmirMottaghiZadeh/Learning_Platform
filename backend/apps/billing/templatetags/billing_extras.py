from zoneinfo import ZoneInfo

from django import template
from django.utils import timezone

from apps.billing import jalali

register = template.Library()

TEHRAN = ZoneInfo("Asia/Tehran")


@register.filter
def fa(value):
    """Persian digits."""
    return jalali.fa_digits(value)


@register.filter
def num(value):
    """۱۲٬۴۰۰"""
    try:
        return jalali.fa_digits(f"{int(value):,}").replace(",", "٬")
    except (TypeError, ValueError):
        return value


@register.filter
def toman(value):
    if value in (None, ""):
        return ""
    return f"{num(value)} تومان"


@register.filter
def jdate(value, style=""):
    """A date or datetime in the Jalali calendar, Tehran time:
    "۱۴۰۵/۰۷/۲۲", or with "long" "۲۲ مهر ۱۴۰۵", or with "time"
    "۱۴۰۵/۰۷/۲۲ ۱۴:۰۵"."""
    if not value:
        return ""
    if hasattr(value, "hour"):
        value = timezone.localtime(value, TEHRAN)
    text = jalali.format_date(value.date() if hasattr(value, "hour") else value, with_month_name=style == "long")
    if style == "time" and hasattr(value, "hour"):
        text += " " + jalali.fa_digits(value.strftime("%H:%M"))
    return text


@register.filter
def ago(value):
    if not value:
        return ""
    seconds = (timezone.now() - value).total_seconds()
    if seconds < 60:
        return "همین حالا"
    if seconds < 3600:
        return jalali.fa_digits(f"{int(seconds // 60)} دقیقه پیش")
    if seconds < 86400:
        return jalali.fa_digits(f"{int(seconds // 3600)} ساعت پیش")
    if seconds < 86400 * 30:
        return jalali.fa_digits(f"{int(seconds // 86400)} روز پیش")
    return jdate(value)


@register.filter
def initial(value):
    return (str(value or "?").strip() or "?")[0]


@register.filter
def get_item(mapping, key):
    return mapping.get(key) if mapping else None
