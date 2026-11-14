import uuid
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.conf import settings
from django.utils import timezone
from django.views.decorators.http import require_POST
from apps.billing.console.views import billing_required, user_label
from apps.billing.services import record
from apps.core.exceptions import PlatformAPIError
from . import services
from . import fx
from .forms import AdjustmentForm, PackageForm, ReviewForm, SettingsForm
from .models import CreditPackage, CreditReservation, CreditSettings, CreditWallet


@billing_required
def dashboard(request):
    config = services.current_settings()
    form = SettingsForm(request.POST if request.method == "POST" else None, instance=config)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            locked = CreditSettings.objects.select_for_update().get(pk=1)
            rate_changed = locked.usd_to_toman != form.cleaned_data["usd_to_toman"]
            for key in form.Meta.fields:
                setattr(locked, key, form.cleaned_data[key])
            if locked.fx_mode == "manual" or rate_changed:
                locked.fx_source = "manual"
                locked.fx_quoted_at = timezone.now()
                locked.fx_checked_at = None
            locked.revision += 1
            locked.model_signature = services.model_signature()
            locked.save()
            fx.reprice_packages(locked)
            record(request,"search_credit_settings","تغییر تعرفه و اعتبار اولیهٔ سرچ هوشمند",details={"revision":locked.revision})
        messages.success(request,"تنظیمات اعتبار سرچ هوشمند ذخیره شد.")
        return redirect("ai_wallet_admin:dashboard")
    query = request.GET.get("q", "").strip()[:150]
    wallets = CreditWallet.objects.select_related("owner").filter(owner__isnull=False)
    if query:
        wallets = wallets.filter(Q(owner__username__icontains=query)|Q(owner__email__icontains=query)
            |Q(owner__learner_profile__phone__icontains=query)|Q(owner__learner_profile__display_name__icontains=query))
    packages = CreditPackage.objects.all()
    return render(request,"ai_wallet/dashboard.html",{"form":form,"packages":packages,"config":config,
        "package_count":packages.filter(active=True).count(),"wallet_count":wallets.count(),
        "reference_luna":settings.AI_LAB_MODEL == "gpt-6-luna", "reference_small":settings.AI_LAB_EMBEDDING_MODEL == "text-embedding-3-small",
        "fx_ready":fx.quote_ready(config),
        "wallets":Paginator(wallets.order_by("-created_at"),25).get_page(request.GET.get("page")),"q":query,
        "pending":CreditReservation.objects.filter(status="pending").select_related("wallet__owner")[:30],
        "pricing_matches":not config.enabled or services.pricing_ready(config),"review_form":ReviewForm()})


@require_POST
@billing_required
def refresh_rate(request):
    config = services.current_settings()
    try:
        updated = fx.refresh(config,force=True,enable=True)
        if updated.fx_mode == "tgju" and fx.quote_ready(updated):
            record(request,"search_credit_fx","به‌روزرسانی نرخ دلار و قیمت بسته‌های سرچ هوشمند از TGJU",details={"toman":updated.usd_to_toman})
            messages.success(request,"نرخ TGJU دریافت شد؛ قیمت بسته‌های دلاری به‌روز و به‌روزرسانی خودکار فعال شد.")
        else:
            messages.error(request,"نرخ تازه تأیید نشد؛ نرخ و قیمت قبلی حفظ شده‌اند.")
    except fx.QuoteUnavailable:
        messages.error(request,"دریافت نرخ تازه انجام نشد؛ نرخ قبلی حفظ شده است.")
    return redirect("ai_wallet_admin:dashboard")


@billing_required
def package_edit(request, pk=None):
    package = get_object_or_404(CreditPackage,pk=pk) if pk else None
    form = PackageForm(request.POST if request.method=="POST" else None,instance=package)
    if request.method=="POST" and form.is_valid():
        package=form.save()
        record(request,"search_credit_package","ذخیرهٔ بستهٔ شارژ سرچ هوشمند",details={"package":package.pk})
        messages.success(request,"بستهٔ شارژ ذخیره شد.")
        return redirect("ai_wallet_admin:dashboard")
    return render(request,"ai_wallet/package.html",{"form":form,"package":package})


@billing_required
def user_wallet(request, pk):
    user=get_object_or_404(get_user_model(),pk=pk)
    wallet=services.get_wallet(user)
    services.reconcile(wallet);wallet.refresh_from_db()
    form=AdjustmentForm(request.POST if request.method=="POST" else None,initial={"key":uuid.uuid4()})
    if request.method=="POST" and form.is_valid():
        try:
            services.adjust(user,form.cleaned_data["amount"],actor=request.user,note=form.cleaned_data["note"],key=form.cleaned_data["key"])
            record(request,"search_credit_adjustment","اصلاح اعتبار سرچ هوشمند",target_user=user,
                details={"amount":str(form.cleaned_data["amount"]),"key":str(form.cleaned_data["key"])})
            messages.success(request,"اعتبار کاربر به‌روزرسانی شد.")
            return redirect("ai_wallet_admin:user",pk=pk)
        except PlatformAPIError as exc:
            form.add_error(None,str(exc.detail.get("message",exc.detail)) if isinstance(exc.detail,dict) else str(exc.detail))
    return render(request,"ai_wallet/user.html",{"wallet":wallet,"target_user":user,"label":user_label(user),"form":form,
        "entries":wallet.entries.all()[:50],"reservations":wallet.reservations.all()[:30]})


@require_POST
@billing_required
def review(request, pk):
    reservation=get_object_or_404(CreditReservation,pk=pk)
    form=ReviewForm(request.POST)
    if form.is_valid():
        try:
            services.settle(pk,reviewed_charge=form.cleaned_data["charge"],actor=request.user,note=form.cleaned_data["note"])
            record(request,"search_credit_review","تسویهٔ مصرف نامشخص سرچ هوشمند",
                details={"search":str(pk),"charge":str(form.cleaned_data["charge"])})
            messages.success(request,"تسویه ثبت شد.")
        except PlatformAPIError:
            messages.error(request,"مبلغ یا وضعیت این مصرف برای تسویه معتبر نیست.")
    else:
        messages.error(request,"مبلغ و دلیل تسویه را کامل و معتبر وارد کنید.")
    return redirect("ai_wallet_admin:dashboard")
