"""Shared plumbing for the panel: navigation, rendering, logging, Jalali
inputs and the styled form base."""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from django import forms
from django.core.paginator import Paginator
from django.shortcuts import render
from django.utils import timezone
from django.utils.safestring import mark_safe

from apps.billing import jalali

from ..models import ActivityLog, Comment, ContactMessage, SiteSettings, StaffRole
from ..permissions import can, role_of

TEHRAN = ZoneInfo("Asia/Tehran")
_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

# (group, [(key, label, url name, icon, permission)])
NAV = [
    ("", [("dash", "داشبورد", "panel:dashboard", "home", "dashboard.view")]),
    ("محتوا", [
        ("posts", "مطالب", "panel:posts", "file", "post.create"),
        ("pages", "برگه‌ها", "panel:pages", "layout", "page.manage"),
        ("taxonomy", "دسته‌ها و برچسب‌ها", "panel:categories", "tag", "taxonomy.manage"),
        ("media", "رسانه", "panel:media", "image", "media.upload"),
        ("comments", "نظرات", "panel:comments", "chat", "comment.moderate"),
    ]),
    ("صفحهٔ اصلی", [
        ("home", "متن و بلوک‌های صفحهٔ اصلی", "panel:blocks", "block", "content.manage"),
    ]),
    ("فروش", [
        ("plans", "پلن‌ها و قیمت‌ها", "panel:plans", "card", "orders.view"),
        ("orders", "سفارش‌ها", "panel:orders", "receipt", "orders.view"),
        ("subs", "اشتراک‌ها و تخفیف", "panel:subscriptions", "gift", "orders.view"),
    ]),
    ("اپ", [
        ("downloads", "نسخه‌ها و دانلود", "panel:releases", "download", "download.manage"),
        ("ann", "اطلاعیه‌ها", "panel:announcements", "mega", "announcement.manage"),
    ]),
    ("مخاطبان", [
        ("contact", "پیام‌های تماس", "panel:contact", "mail", "contact.view"),
        ("subscribers", "خبرنامه", "panel:subscribers", "users", "subscriber.view"),
    ]),
    ("سایت", [
        ("menus", "منوها", "panel:menus", "menu", "menu.manage"),
        ("seo", "سئو و تغییر مسیر", "panel:seo", "globe", "seo.manage"),
        ("stats", "آمار", "panel:stats", "chart", "dashboard.view"),
        ("staff", "کاربران و نقش‌ها", "panel:staff", "users", "*"),
        ("settings", "تنظیمات", "panel:settings", "gear", "*"),
        ("activity", "گزارش فعالیت", "panel:activity", "list", "*"),
    ]),
]


def allowed(user, perm):
    if perm == "*":
        return can(user, "*")
    return can(user, perm)


def nav_for(request, active):
    from django.urls import reverse

    badges = {}
    if can(request.user, "comment.moderate"):
        badges["comments"] = Comment.objects.filter(status=Comment.PENDING).count()
    if can(request.user, "contact.view"):
        badges["contact"] = ContactMessage.objects.filter(status=ContactMessage.NEW).count()
    groups = []
    for title, items in NAV:
        rows = [
            {"key": k, "label": label, "url": reverse(url), "icon": icon, "on": k == active, "badge": badges.get(k) or ""}
            for k, label, url, icon, perm in items if allowed(request.user, perm)
        ]
        if rows:
            groups.append({"title": title, "items": rows})
    return groups


def render_panel(request, template, ctx=None, *, active="", status=200):
    ctx = dict(ctx or {})
    ctx.setdefault("nav_groups", nav_for(request, active))
    ctx["nav_active"] = active
    ctx["role"] = role_of(request.user)
    ctx["role_label"] = dict(StaffRole.ROLE_CHOICES).get(ctx["role"], "")
    ctx["site_settings"] = SiteSettings.get()
    return render(request, template, ctx, status=status)


def log(request, action, obj=None, detail=""):
    user = request.user if request.user.is_authenticated else None
    ActivityLog.objects.create(
        user=user, user_label=(user.get_full_name() or user.get_username())[:120] if user else "",
        action=action[:40], object_type=obj.__class__.__name__ if obj is not None else "",
        object_repr=str(obj)[:200] if obj is not None else "", detail=detail[:300],
        ip=(request.META.get("REMOTE_ADDR") or None),
    )


def paginate(request, qs, per_page=25):
    return Paginator(qs, per_page).get_page(request.GET.get("page"))


# -- Jalali inputs ----------------------------------------------------------------

def jalali_format(value, with_time=True):
    if not value:
        return ""
    if isinstance(value, datetime):
        value = timezone.localtime(value, TEHRAN)
    text = jalali.format_date(value.date() if hasattr(value, "hour") else value)
    if with_time and hasattr(value, "hour"):
        text += " " + jalali.fa_digits(value.strftime("%H:%M"))
    return text


_JDATE = re.compile(r"^\s*(\d{4})[/\-.](\d{1,2})[/\-.](\d{1,2})(?:\s+(\d{1,2}):(\d{2}))?\s*$")


class JalaliDateTimeField(forms.Field):
    """A date and time typed in the Jalali calendar ("1405/07/24 14:30")."""

    widget = forms.TextInput

    def __init__(self, *args, with_time=True, **kwargs):
        self.with_time = with_time
        kwargs.setdefault("widget", forms.TextInput(attrs={"dir": "ltr", "placeholder": "۱۴۰۵/۰۷/۲۴ ۱۴:۳۰" if with_time else "۱۴۰۵/۰۷/۲۴", "autocomplete": "off"}))
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        return jalali_format(value, self.with_time) if value and not isinstance(value, str) else value

    def to_python(self, value):
        value = (value or "").strip().translate(_DIGITS)
        if not value:
            return None
        m = _JDATE.match(value)
        if not m:
            raise forms.ValidationError("تاریخ را مثل ۱۴۰۵/۰۷/۲۴ ۱۴:۳۰ بنویسید.")
        jy, jm, jd = int(m[1]), int(m[2]), int(m[3])
        hour, minute = (int(m[4]), int(m[5])) if m[4] else (0, 0)
        try:
            day = jalali.to_gregorian(jy, jm, jd)
            if not (1 <= jm <= 12 and 1 <= jd <= 31 and 0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError
        except (ValueError, OverflowError):
            raise forms.ValidationError("این تاریخ معتبر نیست.")
        if not self.with_time:
            return day
        return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TEHRAN)


class RichTextWidget(forms.Textarea):
    """A textarea the panel's script upgrades to the visual editor."""

    def __init__(self, attrs=None):
        super().__init__(attrs={"data-editor": "1", "rows": 12, **(attrs or {})})


class StyledFormMixin:
    """Adds the panel's classes to every widget."""

    def _style(self):
        for name, field in self.fields.items():
            w = field.widget
            cls = w.attrs.get("class", "")
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = (cls + " chk").strip()
            elif isinstance(w, (forms.Select, forms.SelectMultiple)):
                w.attrs["class"] = (cls + " inp sel").strip()
            elif isinstance(w, forms.Textarea):
                w.attrs["class"] = (cls + " inp ta").strip()
            elif isinstance(w, forms.FileInput):
                w.attrs["class"] = (cls + " inp").strip()
            else:
                w.attrs["class"] = (cls + " inp").strip()
            if isinstance(field, (forms.URLField, forms.EmailField)) or name in ("slug", "canonical_url", "url", "from_path"):
                w.attrs.setdefault("dir", "ltr")


class PanelForm(StyledFormMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._style()
