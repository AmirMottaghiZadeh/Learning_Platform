import re
from urllib.parse import urlsplit

from django import forms

from apps.website.panel.ui import JalaliDateTimeField

from .models import AppAnnouncement

SEMVER = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}$")
ATC = re.compile(r"^[A-Z]\d{2}[A-Z]{0,2}$")


class AnnouncementForm(forms.ModelForm):
    starts_at = JalaliDateTimeField(required=False, label="نمایش از")
    ends_at = JalaliDateTimeField(required=False, label="تا")

    class Meta:
        model = AppAnnouncement
        fields = [
            "title", "body", "kind", "cta_label", "link_kind", "link_url", "link_screen", "link_param",
            "audience", "below_version", "starts_at", "ends_at", "is_pinned", "dismissible",
        ]
        labels = {
            "title": "عنوان", "body": "متن", "kind": "نوع", "cta_label": "متن دکمه", "link_kind": "دکمه",
            "link_url": "نشانی", "link_screen": "بخش اپ", "link_param": "کد ATC گروه",
            "audience": "مخاطب", "below_version": "نسخه‌های پایین‌تر از",
            "is_pinned": "سنجاق بالای بقیه", "dismissible": "کاربر بتواند ببندد",
        }
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "maxlength": 180})}

    def clean_link_param(self):
        return (self.cleaned_data.get("link_param") or "").strip().upper()

    def clean_below_version(self):
        return (self.cleaned_data.get("below_version") or "").strip().translate(str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789"))

    def clean(self):
        data = super().clean()
        kind = data.get("link_kind") or ""
        if kind == AppAnnouncement.LINK_NONE:
            data["cta_label"], data["link_url"], data["link_screen"], data["link_param"] = "", "", "", ""
        elif kind == AppAnnouncement.LINK_PWA:
            data.update(cta_label="نصب", link_url="", link_screen="", link_param="", audience=AppAnnouncement.AUDIENCE_WEB_NEW, dismissible=True)
        else:
            if not (data.get("cta_label") or "").strip():
                self.add_error("cta_label", "دکمه متن لازم دارد؛ مثلاً «دریافت نسخه».")
            if kind == AppAnnouncement.LINK_URL:
                url = data.get("link_url") or ""
                if urlsplit(url).scheme not in ("http", "https"):
                    self.add_error("link_url", "یک نشانی کامل بنویسید که با https:// شروع شود.")
                data["link_screen"], data["link_param"] = "", ""
            elif kind == AppAnnouncement.LINK_APP:
                screen = data.get("link_screen") or ""
                if not screen:
                    self.add_error("link_screen", "بخشی از اپ را انتخاب کنید.")
                if screen == "lesson" and not ATC.match(data.get("link_param") or ""):
                    self.add_error("link_param", "کد ATC گروه را بنویسید؛ مثلاً B01.")
                if screen != "lesson":
                    data["link_param"] = ""
                data["link_url"] = ""
        if data.get("audience") == AppAnnouncement.AUDIENCE_OLD_APP:
            if not SEMVER.match(data.get("below_version") or ""):
                self.add_error("below_version", "نسخه را مثل 0.2.0 بنویسید.")
        else:
            data["below_version"] = ""
        starts, ends = data.get("starts_at"), data.get("ends_at")
        if starts and ends and ends <= starts:
            self.add_error("ends_at", "پایان باید بعد از شروع باشد.")
        return data
