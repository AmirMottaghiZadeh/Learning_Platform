from django import forms
from django.conf import settings


class SectionEditForm(forms.Form):
    summary_fa = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 8}))
    summary_en = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 8}))
    reason = forms.CharField(widget=forms.Textarea(attrs={"rows": 2}))

    def clean_reason(self):
        reason = self.cleaned_data["reason"].strip()
        minimum = getattr(settings, "DATA_QUALITY_MIN_REASON_LENGTH", 12)
        if len(reason) < minimum:
            raise forms.ValidationError(
                f"Give a reason of at least {minimum} characters."
            )
        return reason
