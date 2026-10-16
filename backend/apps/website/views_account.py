"""Signing in on the site and buying a plan: the app has no payment screen
yet, so the site takes the whole purchase -- sign in with an SMS code (the
same codes the app uses), see the price, pay at the gateway."""

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts import otp
from apps.accounts.models import OneTimeCode
from apps.accounts.phone import InvalidPhone, normalize_phone
from apps.accounts.sms import mask
from apps.billing import config as billing_config
from apps.billing import services as billing
from apps.billing.gateways import GatewayError, get_gateway
from apps.billing.models import Order

from . import services
from .models import DailyStat, SiteSettings

SESSION_KEY = "site_login"


def _next(request):
    target = request.POST.get("next") or request.GET.get("next") or ""
    if target and url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return target
    return reverse("site:account")


def _meta(title):
    return {"meta_title": f"{title} {SiteSettings.get().title_suffix}".strip(), "meta_noindex": True, "meta_description": "", "meta_canonical": "", "meta_image": "", "meta_type": "website"}


def _sign_in(request, user):
    login(request, user, backend="django.contrib.auth.backends.ModelBackend")
    DailyStat.bump(DailyStat.SIGNIN)


def login_phone(request):
    if request.user.is_authenticated:
        return redirect(_next(request))
    if request.method == "POST":
        try:
            phone = normalize_phone(request.POST.get("phone"))
        except InvalidPhone as exc:
            messages.error(request, str(exc))
            return redirect(f"{request.path}?next={_next(request)}")
        if not services.throttle(request, "login", 8, 600):
            messages.error(request, "تلاش‌های ورود زیاد بود؛ چند دقیقه بعد دوباره امتحان کنید.")
            return redirect(request.path)
        password = request.POST.get("password") or ""
        if password:
            user = authenticate(request, username=phone, password=password)
            if user is None or not user.is_active:
                messages.error(request, "شماره یا رمز عبور درست نیست.")
                return redirect(f"{request.path}?next={_next(request)}")
            _sign_in(request, user)
            return redirect(_next(request))
        user = otp.user_for_phone(phone)
        purpose = OneTimeCode.RESET if user is not None and user.has_usable_password() else OneTimeCode.SIGNUP
        try:
            otp.request_code(phone, purpose, request=request)
        except otp.OtpError as exc:
            messages.error(request, str(exc))
            return redirect(f"{request.path}?next={_next(request)}")
        request.session[SESSION_KEY] = {"phone": phone, "purpose": purpose, "next": _next(request)}
        return redirect("site:login_code")
    ctx = {"next": _next(request), "nav": ""}
    ctx.update(_meta("ورود یا ثبت‌نام"))
    return render(request, "website/login.html", ctx)


def login_code(request):
    pending = request.session.get(SESSION_KEY)
    if not pending:
        return redirect("site:login")
    if request.method == "POST":
        if not services.throttle(request, "login-code", 12, 600):
            messages.error(request, "تلاش‌ها زیاد بود؛ کمی بعد دوباره امتحان کنید.")
            return redirect(request.path)
        phone, purpose = pending["phone"], pending["purpose"]
        try:
            otp.verify_code(phone, purpose, request.POST.get("code"), request=request)
            if purpose == OneTimeCode.SIGNUP:
                user, _ = otp.account_for_signup(phone)
            else:
                user = otp.user_for_phone(phone)
        except otp.OtpError as exc:
            messages.error(request, str(exc))
            return redirect(request.path)
        if user is None or not user.is_active:
            messages.error(request, "حسابی با این شماره پیدا نشد.")
            return redirect("site:login")
        request.session.pop(SESSION_KEY, None)
        _sign_in(request, user)
        return redirect(pending.get("next") or reverse("site:account"))
    ctx = {"phone": mask(pending["phone"]), "nav": ""}
    ctx.update(_meta("کد تأیید"))
    return render(request, "website/login_code.html", ctx)


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
    if request.method == "POST" and request.POST.get("action") == "pay" and not error:
        if not billing_config.current().sales_enabled:
            messages.error(request, "فروش موقتاً متوقف است؛ کمی بعد دوباره تلاش کنید.")
            return redirect(request.path)
        order = billing.create_order(request.user, price, discount)
        if order.payable_toman == 0:
            billing.mark_paid(order.pk, gateway="free")
            messages.success(request, "اشتراک شما فعال شد.")
            return redirect("site:account")
        profile = getattr(request.user, "learner_profile", None)
        try:
            gateway = get_gateway()
            url, authority = gateway.start(
                order, request.build_absolute_uri(reverse("billing-callback")),
                description=f"خرید {price.plan.name_fa} · {price.duration_label}",
                mobile=getattr(profile, "phone", None) or "", email=request.user.email or "",
            )
        except GatewayError as exc:
            billing.mark_failed(order, str(exc))
            messages.error(request, "درگاه پرداخت الان در دسترس نیست؛ کمی بعد دوباره امتحان کنید.")
            return redirect(request.path)
        order.gateway, order.authority = gateway.name, authority
        order.save(update_fields=["gateway", "authority"])
        return redirect(url)
    amount, off, payable = quote
    ctx = {"price": price, "amount": amount, "off": off, "payable": payable, "code": code if not error else "", "error": error, "nav": "plans"}
    ctx.update(_meta("خرید اشتراک"))
    return render(request, "website/checkout.html", ctx)
