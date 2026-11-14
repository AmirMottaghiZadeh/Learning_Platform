from decimal import Decimal
from django import forms
from django.conf import settings
from .models import CreditPackage, CreditSettings
from .fx import package_price


class ConsoleFields:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget, (forms.CheckboxInput, forms.HiddenInput)):
                field.widget.attrs["class"] = "fld"
            if isinstance(field, (forms.DecimalField, forms.IntegerField)):
                field.widget.attrs.update({"class": "fld ltr", "inputmode": "decimal"})


class SettingsForm(ConsoleFields, forms.ModelForm):
    class Meta:
        model = CreditSettings
        fields = ["enabled", "initial_credits", "input_per_million", "cached_input_per_million",
                  "cache_write_per_million", "cache_write_12h_per_million", "output_per_million",
                  "embedding_per_million", "usd_per_1000_credits", "usd_to_toman", "fx_mode"]
        labels = {"enabled": "فعال‌سازی کسر اعتبار و فروش بسته‌ها", "initial_credits": "اعتبار اولیهٔ هر کاربر",
            "input_per_million": "اعتبار برای یک میلیون توکن ورودی", "cached_input_per_million": "اعتبار برای یک میلیون توکن ورودی کش‌شده (خالی = نرخ ورودی)",
            "cache_write_per_million": "اعتبار برای یک میلیون توکن نوشتن کش ۳۰ دقیقه‌ای",
            "cache_write_12h_per_million": "اعتبار برای یک میلیون توکن نوشتن کش ۱۲ ساعته",
            "output_per_million": "اعتبار برای یک میلیون توکن خروجی", "embedding_per_million": "اعتبار برای یک میلیون توکن بردارسازی پرسش",
            "usd_per_1000_credits": "قیمت فروش هر ۱۰۰۰ اعتبار (دلار)",
            "usd_to_toman": "قیمت یک دلار (تومان)", "fx_mode": "روش به‌روزرسانی نرخ دلار"}
        help_texts = {"initial_credits": "فقط یک بار به حساب هر کاربر اضافه می‌شود.",
            "cache_write_per_million": "فقط با تعداد واقعیِ گزارش‌شده در usage؛ خالی = نرخ ورودی.",
            "cache_write_12h_per_million": "فقط با تفکیک واقعی ۱۲ ساعته؛ خالی = نرخ نوشتن کش معمول.",
            "usd_to_toman": "در حالت خودکار با آخرین نرخ معتبر دلار آزاد جایگزین می‌شود.",
            "usd_per_1000_credits": "انتخاب فعلی: ۰٫۱ + ۰٫۵ = ۰٫۶ دلار. مستقل از تعرفهٔ مصرف اعتبار."}

    def clean(self):
        values = super().clean()
        for name in self.Meta.fields:
            value = values.get(name)
            if isinstance(value, Decimal) and value < 0:
                self.add_error(name, "مقدار نمی‌تواند منفی باشد.")
        if values.get("enabled"):
            if settings.AI_LAB_SEARCH_ENGINE != "hybrid":
                raise forms.ValidationError("پیش از فعال‌سازی اعتبار، موتور جدید سرچ هوشمند را فعال کنید.")
            if not any((values.get(key) or 0) > 0 for key in ["input_per_million", "output_per_million", "embedding_per_million"]):
                raise forms.ValidationError("برای فعال‌سازی، تعرفهٔ مصرف را تعیین کنید.")
        for key in ["usd_to_toman", "usd_per_1000_credits"]:
            if values.get(key) is not None and values[key] <= 0:
                self.add_error(key, "مقدار باید بیشتر از صفر باشد.")
        return values


class PackageForm(ConsoleFields, forms.ModelForm):
    class Meta:
        model = CreditPackage
        fields = ["name", "credits", "dollar_priced", "price_toman", "active", "order"]
        labels = {"name": "نام بسته", "credits": "مقدار اعتبار", "price_toman": "قیمت ثابت بسته (تومان)",
                  "dollar_priced": "محاسبهٔ قیمت بر اساس نرخ دلار", "active": "قابل خرید", "order": "ترتیب نمایش"}
        help_texts = {"price_toman": "برای بستهٔ دلاری نیاز به ورود نیست؛ قیمت با نرخ و نسبت تعیین‌شده محاسبه می‌شود."}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["price_toman"].required = False

    def clean(self):
        values = super().clean()
        if values.get("dollar_priced") and (values.get("credits") or 0) > 0:
            from .services import current_settings
            package = CreditPackage(credits=values["credits"], dollar_priced=True)
            values["price_toman"] = package_price(package, current_settings())
        if values.get("price_toman") is None:
            self.add_error("price_toman", "قیمت بسته را وارد کنید.")
        for key in ["credits", "price_toman"]:
            if values.get(key) is not None and values[key] <= 0:
                self.add_error(key, "مقدار باید بیشتر از صفر باشد.")
        return values


class AdjustmentForm(ConsoleFields, forms.Form):
    amount = forms.DecimalField(label="تغییر اعتبار (مثبت یا منفی)", max_digits=22, decimal_places=6)
    note = forms.CharField(label="توضیح قابل نمایش به کاربر", max_length=255)
    key = forms.UUIDField(widget=forms.HiddenInput)


class ReviewForm(ConsoleFields, forms.Form):
    charge = forms.DecimalField(label="مجموع اعتبار مصرف‌شدهٔ تأییدشده (صفر = بدون کسر)", min_value=0, max_digits=22, decimal_places=6)
    note = forms.CharField(label="دلیل تسویه", max_length=255)
