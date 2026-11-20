from urllib.parse import urlsplit
from django import forms
from django.forms import modelformset_factory
from .models import AISettings, AIPromptPreset


class AISettingsForm(forms.ModelForm):
    api_key = forms.CharField(label="کلید API جدید", required=False, strip=True, widget=forms.PasswordInput(render_value=False))
    clear_api_key = forms.BooleanField(label="حذف کلید ذخیره‌شده", required=False)

    class Meta:
        model = AISettings
        fields = ["enabled", "base_url", "model", "reasoning_effort", "timeout_seconds", "max_output_tokens"]
        labels = {"enabled": "فعال‌سازی ویرایش با AI", "base_url": "Base URL", "model": "مدل", "reasoning_effort": "سطح thinking", "timeout_seconds": "مهلت اتصال (ثانیه)", "max_output_tokens": "حداکثر توکن خروجی"}

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for name,field in self.fields.items():
            if not isinstance(field.widget,forms.CheckboxInput):field.widget.attrs.update({"class":"input", "autocomplete":"new-password" if name=="api_key" else "off"})
        for name in ["base_url","model","api_key"]:self.fields[name].widget.attrs["dir"]="ltr"

    def clean_base_url(self):
        value=self.cleaned_data["base_url"].strip().rstrip("/");url=urlsplit(value)
        if url.scheme not in {"http","https"} or not url.hostname or url.username or url.password or url.query or url.fragment:
            raise forms.ValidationError("نشانی پایه بدون کلید، نام کاربری، query یا fragment وارد شود.")
        if url.scheme=="http" and url.hostname not in {"localhost","127.0.0.1","::1"}:
            raise forms.ValidationError("برای سرویس غیرمحلی از HTTPS استفاده کنید.")
        return value

    def clean(self):
        data=super().clean()
        if not 5<=(data.get("timeout_seconds") or 0)<=120:self.add_error("timeout_seconds","مقدار باید بین ۵ و ۱۲۰ باشد.")
        if not 256<=(data.get("max_output_tokens") or 0)<=16000:self.add_error("max_output_tokens","مقدار باید بین ۲۵۶ و ۱۶۰۰۰ باشد.")
        if data.get("api_key") and data.get("clear_api_key"):self.add_error("api_key","ورود و حذف کلید را هم‌زمان انتخاب نکنید.")
        if data.get("enabled") and (not data.get("model") or not (data.get("api_key") or self.instance.encrypted_api_key and not data.get("clear_api_key"))):
            raise forms.ValidationError("برای فعال‌سازی، مدل و کلید API را تنظیم کنید.")
        return data


class AIPresetForm(forms.ModelForm):
    class Meta:
        model=AIPromptPreset
        fields=["name","action","instruction","active","order"]
        labels={"name":"نام دستور","action":"نوع عملیات","instruction":"پرامپت ذخیره‌شده","active":"فعال","order":"ترتیب"}
        widgets={"instruction":forms.Textarea(attrs={"rows":4,"maxlength":6000})}

    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        for field in self.fields.values():
            if not isinstance(field.widget,forms.CheckboxInput):field.widget.attrs["class"]="input"


AIPresetFormSet=modelformset_factory(AIPromptPreset,form=AIPresetForm,extra=1,can_delete=True,max_num=30,validate_max=True)
