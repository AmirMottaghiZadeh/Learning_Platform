import re

from django import forms
from django.utils import timezone
from django.utils.text import slugify

from apps.billing import jalali
from apps.billing.catalog import SCOPE_ATC_PREFIX, SCOPE_TOPIC_CATEGORY, TOPIC_CATEGORY_CHOICES
from apps.billing.models import DiscountCode, Feature, Plan

_LATIN = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")

DURATION_CHOICES = [
    ("30", "۱ ماهه"), ("90", "۳ ماهه"), ("180", "۶ ماهه"), ("365", "۱ ساله"), ("", "دائمی"),
]


def latin_digits(value):
    return str(value or "").translate(_LATIN)


def parse_jalali(value):
    """"1405/08/01" (Latin or Persian digits) -> an aware datetime at the
    start of that day, Tehran time; "" -> None."""
    text = latin_digits(value).strip()
    if not text:
        return None
    match = re.fullmatch(r"(\d{4})[/-](\d{1,2})[/-](\d{1,2})", text)
    if not match:
        raise forms.ValidationError("تاریخ را به شکل ۱۴۰۵/۰۸/۰۱ بنویسید.")
    try:
        day = jalali.to_gregorian(*(int(g) for g in match.groups()))
    except (ValueError, IndexError) as exc:
        raise forms.ValidationError("این تاریخ وجود ندارد.") from exc
    from datetime import datetime
    from zoneinfo import ZoneInfo

    return datetime(day.year, day.month, day.day, tzinfo=ZoneInfo("Asia/Tehran"))


class PlanBasicsForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ["kind", "name_fa", "name_en", "slug", "tagline_fa", "audience", "order"]
        labels = {
            "kind": "نوع",
            "name_fa": "نام فارسی",
            "name_en": "نام انگلیسی",
            "slug": "شناسه (انگلیسی، در لینک‌ها)",
            "tagline_fa": "یک خط توضیح برای کاربر",
            "audience": "مخاطب",
            "order": "ترتیب نمایش",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["slug"].required = False
        if self.instance.pk and self.instance.is_free:
            self.fields["kind"].disabled = True

    def clean_slug(self):
        slug = slugify(self.cleaned_data.get("slug") or self.cleaned_data.get("name_en") or "")
        if not slug:
            slug = f"plan-{timezone.now():%y%m%d%H%M%S}"
        clash = Plan.objects.filter(slug=slug).exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError("این شناسه برای پلن دیگری است.")
        return slug


class FeatureForm(forms.ModelForm):
    """A new feature: content (works at once) or custom (waits for code)."""

    KIND_CHOICES = [
        (Feature.KIND_CONTENT, "دسترسی به محتوا (بدون نیاز به کدنویسی)"),
        (Feature.KIND_CUSTOM, "امکان سفارشی (بعد از اتصال در کد فعال می‌شود)"),
    ]
    kind = forms.ChoiceField(choices=KIND_CHOICES, label="نوع")
    scope_category = forms.ChoiceField(
        choices=[("", "—")] + TOPIC_CATEGORY_CHOICES, required=False, label="دسته‌ی مطالعه"
    )
    scope_atc = forms.CharField(required=False, max_length=7, label="کد ATC (مثلاً C09)")
    # Free text, made into a slug by clean_key (a SlugField would reject
    # "Cardio Pack" before clean_key could fix it).
    key = forms.CharField(max_length=60, label="شناسه (برای کد)")

    class Meta:
        model = Feature
        fields = ["name_fa", "name_en", "key", "kind", "countable", "unit_fa", "description_fa", "scope_type"]
        labels = {
            "name_fa": "نام فارسی",
            "name_en": "نام انگلیسی",
            "key": "شناسه (برای کد)",
            "countable": "قابل شمارش؛ می‌شود برایش سقف روزانه یا ماهانه گذاشت",
            "unit_fa": "واحد شمارش (مثلاً «جزوه»)",
            "description_fa": "توضیح",
            "scope_type": "چه محتوایی؟",
        }

    def clean_key(self):
        key = slugify(latin_digits(self.cleaned_data["key"])).replace("-", "_")
        if not key:
            raise forms.ValidationError("شناسه را با حروف انگلیسی بنویسید.")
        if Feature.objects.filter(key=key).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("امکانی با این شناسه هست.")
        return key

    def clean(self):
        data = super().clean()
        if data.get("kind") == Feature.KIND_CONTENT:
            scope = data.get("scope_type")
            if scope == SCOPE_TOPIC_CATEGORY:
                value = data.get("scope_category")
            elif scope == SCOPE_ATC_PREFIX:
                value = latin_digits(data.get("scope_atc")).strip().upper()
            else:
                value = ""
            if not value:
                raise forms.ValidationError("برای امکان محتوایی، محتوای آن را مشخص کنید.")
            data["scope_value"] = value
        else:
            data["scope_type"] = ""
            data["scope_value"] = ""
        return data

    def save(self, commit=True):
        feature = super().save(commit=False)
        feature.scope_type = self.cleaned_data["scope_type"]
        feature.scope_value = self.cleaned_data["scope_value"]
        if commit:
            feature.save()
        return feature


class FeatureEditForm(forms.ModelForm):
    class Meta:
        model = Feature
        fields = ["name_fa", "name_en", "unit_fa", "description_fa", "order"]


class DiscountForm(forms.Form):
    code = forms.CharField(max_length=40, label="کد")
    kind = forms.ChoiceField(choices=[("percent", "درصد"), ("amount", "مبلغ ثابت (تومان)")], label="نوع تخفیف")
    value = forms.CharField(label="مقدار")
    max_uses = forms.CharField(required=False, label="سقف دفعات استفاده (خالی = بی‌نهایت)")
    starts = forms.CharField(required=False, label="شروع (۱۴۰۵/۰۸/۰۱)")
    ends = forms.CharField(required=False, label="پایان (۱۴۰۵/۰۸/۳۰)")
    plans = forms.ModelMultipleChoiceField(
        queryset=Plan.objects.filter(is_free=False), required=False, label="فقط برای این پلن‌ها (خالی = همه)",
        widget=forms.CheckboxSelectMultiple,
    )
    note = forms.CharField(required=False, max_length=160, label="یادداشت")

    def clean_code(self):
        code = latin_digits(self.cleaned_data["code"]).strip().upper()
        if not re.fullmatch(r"[A-Z0-9_-]{3,40}", code):
            raise forms.ValidationError("کد فقط حروف و اعداد انگلیسی، دست‌کم ۳ حرف.")
        if DiscountCode.objects.filter(code=code).exists():
            raise forms.ValidationError("این کد قبلاً ساخته شده.")
        return code

    def clean_value(self):
        text = latin_digits(self.cleaned_data["value"]).replace(",", "").replace("٬", "").strip()
        if not text.isdigit() or int(text) <= 0:
            raise forms.ValidationError("یک عدد مثبت بنویسید.")
        return int(text)

    def clean_max_uses(self):
        text = latin_digits(self.cleaned_data["max_uses"]).strip()
        if not text:
            return None
        if not text.isdigit() or int(text) <= 0:
            raise forms.ValidationError("یک عدد مثبت بنویسید یا خالی بگذارید.")
        return int(text)

    def clean_starts(self):
        return parse_jalali(self.cleaned_data["starts"])

    def clean_ends(self):
        value = parse_jalali(self.cleaned_data["ends"])
        if value is not None:
            from datetime import timedelta

            value += timedelta(days=1)  # through the end of that day
        return value

    def clean(self):
        data = super().clean()
        if data.get("kind") == "percent" and isinstance(data.get("value"), int) and data["value"] > 100:
            self.add_error("value", "درصد تخفیف حداکثر ۱۰۰ است.")
        starts, ends = data.get("starts"), data.get("ends")
        if starts and ends and ends <= starts:
            self.add_error("ends", "پایان باید بعد از شروع باشد.")
        return data


def parse_amount(value):
    text = latin_digits(value).replace(",", "").replace("٬", "").strip()
    return int(text) if text.isdigit() else None
