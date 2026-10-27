"""Website sign-up, password login and recovery using the app's accounts,
SMS codes and password rules, followed by subscription checkout."""

from math import ceil
from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate, get_user_model, login, logout
from django.db import transaction
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.cache import never_cache
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.http import require_http_methods, require_POST

from apps.accounts import otp
from apps.accounts.models import LearnerProfile, OneTimeCode, SecurityAuditEvent
from apps.accounts.services import record_security_event, revoke_all_user_sessions
from apps.accounts.sms import mask
from apps.billing import config as billing_config
from apps.billing import services as billing
from apps.billing.gateways import GatewayError, start_payment
from apps.billing.views import callback_url
from apps.billing.models import Order

from . import services
from .forms_account import CodeForm, LoginForm, PasswordForm, PhoneForm
from .models import DailyStat, SiteSettings

SESSION_KEY = "site_login"
PASSWORD_SESSION_KEY = "site_password"


def _safe_next(request, target):
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return reverse("site:account")


def _next(request):
    return _safe_next(request, request.POST.get("next") or request.GET.get("next") or "")


def _login_url(mode, target):
    return reverse("site:login") + "?" + urlencode({"mode": mode, "next": target})


def _meta(title):
    return {"meta_title": f"{title} {SiteSettings.get().title_suffix}".strip(), "meta_noindex": True, "meta_description": "", "meta_canonical": "", "meta_image": "", "meta_type": "website"}


def _sign_in(request, user):
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    DailyStat.bump(DailyStat.SIGNIN)


@never_cache
@sensitive_post_parameters("password")
@require_http_methods(["GET", "POST"])
def login_phone(request):
    if request.user.is_authenticated:
        return redirect(_next(request))
    mode = request.POST.get("mode") or request.GET.get("mode") or "login"
    if mode not in {"login", "signup", "reset"}:
        mode = "login"
    form_class = LoginForm if mode == "login" else PhoneForm
    form = form_class(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        if not services.throttle(request, "login", 8, 600):
            form.add_error(None, "تلاش‌های ورود زیاد بود؛ چند دقیقه بعد دوباره امتحان کنید.")
        elif mode == "login":
            user = authenticate(request, username=form.cleaned_data["phone"], password=form.cleaned_data["password"])
            if user is None or not user.is_active:
                form.add_error(None, "شماره، ایمیل یا رمز عبور درست نیست.")
            else:
                request.session.pop(SESSION_KEY, None)
                request.session.pop(PASSWORD_SESSION_KEY, None)
                _sign_in(request, user)
                return redirect(_next(request))
        else:
            phone = form.cleaned_data["phone"]
            purpose = OneTimeCode.RESET if mode == "reset" else OneTimeCode.SIGNUP
            try:
                otp.request_code(phone, purpose, request=request)
            except otp.OtpError as exc:
                if exc.code != "OTP_TOO_SOON":
                    form.add_error(None, str(exc))
                else:
                    _pending_login(request, phone, purpose, exc.details.get("retry_after", 0))
                    return redirect("site:login_code")
            else:
                _pending_login(request, phone, purpose, settings.OTP_RESEND_SECONDS)
                return redirect("site:login_code")
    ctx = {"next": _next(request), "nav": "", "mode": mode, "form": form}
    ctx.update(_meta("بازیابی رمز عبور" if mode == "reset" else "ثبت‌نام / ورود"))
    return render(request, "website/login.html", ctx)


def _pending_login(request, phone, purpose, wait):
    request.session.pop(PASSWORD_SESSION_KEY, None)
    request.session[SESSION_KEY] = {
        "phone": phone, "purpose": purpose, "next": _next(request),
        "resend_at": timezone.now().timestamp() + wait,
    }


@never_cache
@sensitive_post_parameters("code")
@require_http_methods(["GET", "POST"])
def login_code(request):
    if request.user.is_authenticated:
        return redirect(_next(request))
    pending = request.session.get(SESSION_KEY)
    if not pending:
        return redirect("site:login")
    form = CodeForm(request.POST if request.method == "POST" and request.POST.get("action") != "resend" else None)
    if request.method == "POST" and request.POST.get("action") == "resend":
        if not services.throttle(request, "login", 8, 600):
            messages.error(request, "تلاش‌ها زیاد بود؛ کمی بعد دوباره امتحان کنید.")
        else:
            try:
                otp.request_code(pending["phone"], pending["purpose"], request=request)
            except otp.OtpError as exc:
                messages.error(request, str(exc))
                if exc.code == "OTP_TOO_SOON":
                    pending["resend_at"] = timezone.now().timestamp() + exc.details.get("retry_after", 0)
                    request.session[SESSION_KEY] = pending
            else:
                pending["resend_at"] = timezone.now().timestamp() + settings.OTP_RESEND_SECONDS
                request.session[SESSION_KEY] = pending
                messages.success(request, "کد تأیید تازه ارسال شد.")
                return redirect("site:login_code")
    elif request.method == "POST" and form.is_valid():
        if not services.throttle(request, "login-code", 12, 600):
            messages.error(request, "تلاش‌ها زیاد بود؛ کمی بعد دوباره امتحان کنید.")
            return redirect(request.path)
        phone, purpose = pending["phone"], pending["purpose"]
        try:
            otp.verify_code(phone, purpose, form.cleaned_data["code"], request=request)
            if purpose == OneTimeCode.SIGNUP:
                user, _ = otp.account_for_signup(phone)
            else:
                user = otp.user_for_phone(phone)
        except otp.OtpError as exc:
            form.add_error(None, str(exc))
        else:
            if user is None or not user.is_active:
                request.session.pop(SESSION_KEY, None)
                messages.error(request, "حسابی با این شماره پیدا نشد.")
                return redirect("site:login")
            request.session.pop(SESSION_KEY, None)
            request.session.cycle_key()
            request.session[PASSWORD_SESSION_KEY] = {
                "user_id": user.pk, "verified_at": timezone.now().timestamp(),
                "next": _safe_next(request, pending.get("next")),
            }
            record_security_event(
                SecurityAuditEvent.OTP_VERIFIED, user=user, actor=user, request=request,
                metadata={"purpose": purpose},
            )
            return redirect("site:set_password")
    ctx = {
        "phone": mask(pending["phone"]), "nav": "", "form": form,
        "mode": "reset" if pending["purpose"] == OneTimeCode.RESET else "signup",
        "next": _safe_next(request, pending.get("next")),
        "code_length": max(4, settings.OTP_CODE_LENGTH),
        "resend_in": max(0, ceil(pending.get("resend_at", 0) - timezone.now().timestamp())),
    }
    ctx.update(_meta("کد تأیید"))
    return render(request, "website/login_code.html", ctx)


@never_cache
@sensitive_post_parameters("new_password", "new_password_confirm")
@require_http_methods(["GET", "POST"])
def set_password(request):
    pending = request.session.get(PASSWORD_SESSION_KEY)
    if request.user.is_authenticated:
        return redirect(_next(request))
    if not pending:
        return redirect("site:login")
    elapsed = timezone.now().timestamp() - pending.get("verified_at", 0)
    if elapsed < 0 or elapsed > settings.AUTH_STEP_UP_TTL_MINUTES * 60:
        request.session.pop(PASSWORD_SESSION_KEY, None)
        messages.error(request, "مهلت انتخاب رمز تمام شد؛ دوباره کد تأیید بگیرید.")
        return redirect(_login_url("reset", _safe_next(request, pending.get("next"))))
    user = get_user_model().objects.filter(pk=pending["user_id"], is_active=True).first()
    if user is None:
        request.session.pop(PASSWORD_SESSION_KEY, None)
        return redirect("site:login")
    form = PasswordForm(request.POST if request.method == "POST" else None, user=user)
    if request.method == "POST" and form.is_valid():
        if not services.throttle(request, "password-set", 10, 3600):
            form.add_error(None, "تلاش‌ها زیاد بود؛ کمی بعد دوباره امتحان کنید.")
        else:
            with transaction.atomic():
                user.set_password(form.cleaned_data["new_password"])
                fields = ["password"]
                name = form.cleaned_data.get("name")
                if name:
                    first, _, last = name.partition(" ")
                    user.first_name, user.last_name = first, last
                    fields += ["first_name", "last_name"]
                    LearnerProfile.objects.update_or_create(user=user, defaults={"display_name": name})
                user.save(update_fields=fields)
                revoke_all_user_sessions(user, request=request, actor=user, reason="password_set")
                record_security_event(SecurityAuditEvent.PASSWORD_SET, user=user, actor=user, request=request)
            request.session.pop(PASSWORD_SESSION_KEY, None)
            _sign_in(request, user)
            return redirect(_safe_next(request, pending.get("next")))
    ctx = {
        "form": form, "is_new_account": not user.has_usable_password(), "nav": "",
        "password_min_length": settings.AUTH_PASSWORD_MIN_LENGTH,
    }
    ctx.update(_meta("انتخاب رمز عبور"))
    return render(request, "website/set_password.html", ctx)


@require_POST
def logout_view(request):
    logout(request)
    return redirect("site:home")


def account(request):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('site:login')}?next={request.path}")
    profile = getattr(request.user, "learner_profile", None)
    orders = Order.objects.filter(user=request.user).select_related("plan").order_by("-created_at")[:20]
    ctx = {
        "profile": profile, "orders": orders, "entitlements": billing.active_entitlements(request.user),
        "app_url": SiteSettings.get().app_url, "nav": "",
    }
    ctx.update(_meta("حساب من"))
    return render(request, "website/account.html", ctx)


def checkout(request, price_id):
    if not request.user.is_authenticated:
        return redirect(f"{reverse('site:login')}?next={request.path}")
    try:
        price = billing.purchasable_price(price_id)
    except billing.BillingError as exc:
        messages.error(request, str(exc))
        return redirect("site:plans")
    code = (request.POST.get("discount_code") or request.GET.get("code") or "").strip()
    discount, quote, error = None, None, ""
    try:
        discount = billing.find_discount(code)
        quote = billing.quote(price, discount)
    except billing.BillingError as exc:
        error, discount = str(exc), None
        quote = billing.quote(price, None)
    gateways = billing_config.enabled_gateways()
    if request.method == "POST" and request.POST.get("action") == "pay" and not error:
        if not billing_config.current().sales_enabled:
            messages.error(request, "فروش موقتاً متوقف است؛ کمی بعد دوباره تلاش کنید.")
            return redirect(request.path)
        if not gateways:
            messages.error(request, "هیچ درگاه پرداخت فعالی تنظیم نشده است؛ لطفاً کمی بعد دوباره تلاش کنید.")
            return redirect(request.path)
        order = billing.create_order(request.user, price, discount)
        if order.payable_toman == 0:
            billing.mark_paid(order.pk, gateway="free")
            messages.success(request, "اشتراک شما فعال شد.")
            return redirect("site:account")
        profile = getattr(request.user, "learner_profile", None)
        kinds = [g.kind for g in gateways]
        chosen = request.POST.get("gateway") if request.POST.get("gateway") in kinds else None
        try:
            url = start_payment(
                order, lambda kind: callback_url(request, kind), kind=chosen,
                description=f"خرید {price.plan.name_fa} · {price.duration_label}",
                mobile=getattr(profile, "phone", None) or "", email=request.user.email or "",
            )
        except GatewayError as exc:
            billing.mark_failed(order, str(exc))
            messages.error(request, "درگاه پرداخت الان در دسترس نیست؛ کمی بعد دوباره امتحان کنید یا درگاه دیگری را انتخاب کنید.")
            return redirect(request.path)
        response = redirect(url)
        # Zibal validates the merchant domain through the Referer header. The
        # production security policy is intentionally relaxed for this one
        # cross-origin payment navigation.
        if order.gateway == "zibal":
            response["Referrer-Policy"] = "origin"
        return response
    amount, off, payable = quote
    ctx = {
        "price": price, "amount": amount, "off": off, "payable": payable, "code": code if not error else "",
        "error": error, "nav": "plans", "gateways": gateways,
        "has_zibal": any(g.kind == "zibal" for g in gateways),
    }
    ctx.update(_meta("خرید اشتراک"))
    return render(request, "website/checkout.html", ctx)
