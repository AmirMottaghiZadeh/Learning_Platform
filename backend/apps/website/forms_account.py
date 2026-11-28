from django import forms
from django.conf import settings
from django.contrib.auth.password_validation import validate_password

from apps.accounts.phone import InvalidPhone, normalize_phone


class AccountForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input"


class LoginForm(AccountForm):
    phone = forms.CharField(
        label="شمارهٔ موبایل یا ایمیل", max_length=254,
        widget=forms.TextInput(attrs={"autocomplete": "username", "dir": "ltr", "autofocus": True}),
    )
    password = forms.CharField(
        label="رمز عبور", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )


class PhoneForm(AccountForm):
    phone = forms.CharField(
        label="شمارهٔ موبایل", max_length=40,
        widget=forms.TextInput(attrs={"inputmode": "tel", "autocomplete": "tel", "dir": "ltr", "autofocus": True}),
    )

    def clean_phone(self):
        try:
            return normalize_phone(self.cleaned_data["phone"])
        except InvalidPhone as exc:
            raise forms.ValidationError(str(exc)) from exc


class CodeForm(AccountForm):
    code = forms.CharField(
        label="کد تأیید", max_length=10,
        widget=forms.TextInput(attrs={
            "inputmode": "numeric", "autocomplete": "one-time-code", "dir": "ltr", "autofocus": True,
        }),
    )


class PasswordForm(AccountForm):
    name = forms.CharField(
        label="نام و نام خانوادگی", max_length=150,
        widget=forms.TextInput(attrs={"autocomplete": "name"}),
    )
    new_password = forms.CharField(
        label="رمز عبور", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )
    new_password_confirm = forms.CharField(
        label="تکرار رمز عبور", strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password"}),
    )

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        if user.has_usable_password():
            del self.fields["name"]
        self.fields["new_password"].widget.attrs["minlength"] = settings.AUTH_PASSWORD_MIN_LENGTH

    def clean_name(self):
        return " ".join(self.cleaned_data["name"].split())

    def clean_new_password(self):
        password = self.cleaned_data["new_password"]
        validate_password(password, user=self.user)
        return password

    def clean(self):
        data = super().clean()
        if data.get("new_password") and data.get("new_password_confirm") != data["new_password"]:
            self.add_error("new_password_confirm", "تکرار رمز عبور یکسان نیست.")
        return data
