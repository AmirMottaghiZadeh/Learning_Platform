"""The superuser console at /ops/: users and their access, the plan
builder, features, discount codes, sales and the audit log. Server-rendered,
Persian, right to left; every change goes through apps.billing.services and
is written to the audit log."""

import csv
import json
import re
import socket
import urllib.request
from datetime import datetime, timedelta
from functools import wraps
from urllib.parse import urlsplit

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.cache import caches
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Exists, OuterRef, Prefetch, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from apps.accounts.models import Role, RoleAssignment, UserSession
from apps.accounts.services import (
    assign_platform_role,
    revoke_all_user_sessions,
    revoke_platform_role,
)
from apps.billing import config, services
from apps.billing import guest as guest_tools
from apps.billing.gateways import GatewayError, SepGateway, ZibalGateway, ZarinpalGateway
from apps.billing.catalog import SCOPE_TYPES, TOPIC_CATEGORY_CHOICES
from apps.billing.jalali import fa_digits, month_start
from apps.manage.views import login_url as manage_login_url
from apps.manage.views import logout_view as manage_logout
from apps.manage.views import to_login
from apps.billing.models import (
    PERIOD_CHOICES,
    AdminAction,
    BillingSettings,
    DiscountCode,
    Entitlement,
    Feature,
    Order,
    PaymentGateway,
    Plan,
    PlanFeature,
    PlanPrice,
)

from .forms import (
    DURATION_CHOICES,
    DiscountForm,
    FeatureEditForm,
    FeatureForm,
    PlanBasicsForm,
    latin_digits,
    parse_amount,
)

User = get_user_model()
PAGE_SIZE = 25
FIELD_FA = {"pharmacy": "داروسازی", "medicine": "پزشکی", "nursing": "پرستاری"}
STEPS = [("basics", "اطلاعات پایه"), ("features", "امکانات"), ("prices", "قیمت و مدت"), ("review", "بررسی و انتشار")]


# -- access -------------------------------------------------------------------

def superuser_required(view):
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        user = request.user
        if not (user.is_authenticated and user.is_active and user.is_superuser):
            return redirect(manage_login_url(request.get_full_path()))
        return view(request, *args, **kwargs)

    return wrapper


# Signing in and out is the admin's (apps.manage); these old addresses send there.
login_view = to_login


@require_POST
def logout_view(request):
    return manage_logout(request)


# -- helpers ------------------------------------------------------------------

def user_label(user):
    profile = getattr(user, "learner_profile", None)
    return (
        (profile.display_name if profile else "")
        or user.get_full_name()
        or (profile.phone if profile and profile.phone else "")
        or user.email
        or user.username
    )


def user_contact(user):
    profile = getattr(user, "learner_profile", None)
    return " · ".join(v for v in [profile.phone if profile else None, user.email] if v)


def _active_q(prefix="", when=None):
    when = when or timezone.now()
    return (
        Q(**{f"{prefix}revoked_at__isnull": True, f"{prefix}starts_at__lte": when})
        & (Q(**{f"{prefix}ends_at__isnull": True}) | Q(**{f"{prefix}ends_at__gt": when}))
    )


def _active_entitlements_qs(when=None):
    return Entitlement.objects.filter(_active_q(when=when)).select_related("plan").order_by("ends_at")


def _remaining(entitlements, now):
    """Label, percent left and tone of a user's longest-running access."""
    if not entitlements:
        return {"label": "بدون اشتراک", "pct": 0, "tone": "muted"}
    if any(e.ends_at is None for e in entitlements):
        return {"label": "دائمی", "pct": 100, "tone": "accent"}
    last = max(entitlements, key=lambda e: e.ends_at)
    left = (last.ends_at - now).days
    total = max((last.ends_at - last.starts_at).days, 1)
    tone = "warn" if left < 7 else "accent"
    return {"label": fa_digits(f"{left} روز مانده") if left > 0 else "کمتر از یک روز", "pct": max(3, min(100, round(100 * left / total))), "tone": tone}


def _segment_filter(qs, segment, now):
    has_active = Exists(Entitlement.objects.filter(_active_q(when=now), user=OuterRef("pk")))
    if segment == "subscribed":
        return qs.filter(has_active)
    if segment == "expiring":
        soon = Entitlement.objects.filter(_active_q(when=now), user=OuterRef("pk"), ends_at__lte=now + timedelta(days=7))
        return qs.filter(Exists(soon))
    if segment == "expired":
        return qs.filter(Exists(Entitlement.objects.filter(user=OuterRef("pk")))).exclude(has_active)
    if segment == "blocked":
        return qs.filter(is_active=False)
    return qs


def _search(qs, q):
    q = latin_digits(q).strip()
    if not q:
        return qs
    return qs.filter(
        Q(username__icontains=q) | Q(email__icontains=q) | Q(first_name__icontains=q) | Q(last_name__icontains=q)
        | Q(learner_profile__display_name__icontains=q) | Q(learner_profile__phone__icontains=q)
    )


def _sparkline(counts):
    peak = max(counts) or 1
    return [{"h": max(6, round(44 * c / peak)), "last": i == len(counts) - 1} for i, c in enumerate(counts)]


def _daily_counts(qs, field, days=7):
    today = timezone.localdate()
    return [qs.filter(**{f"{field}__date": today - timedelta(days=d)}).count() for d in range(days - 1, -1, -1)]


def _people():
    """Real accounts: guests (made while guest access is on) are left out of
    the users list, its counts and the export."""
    return User.objects.filter(guest_account__isnull=True)


def _grantable_plans():
    return Plan.objects.filter(is_free=False).exclude(status=Plan.STATUS_INACTIVE).prefetch_related("prices")


# -- users --------------------------------------------------------------------

@superuser_required
def users(request):
    now = timezone.now()
    segment = request.GET.get("seg", "all")
    q = request.GET.get("q", "")
    base = _people().select_related("learner_profile").order_by("-date_joined")
    qs = _search(_segment_filter(base, segment, now), q)
    page = Paginator(qs, PAGE_SIZE).get_page(request.GET.get("page"))
    users_on_page = list(page.object_list)
    active = {}
    for ent in _active_entitlements_qs(now).filter(user__in=users_on_page):
        active.setdefault(ent.user_id, []).append(ent)

    selected_id = request.GET.get("u")
    rows = []
    for user in users_on_page:
        ents = active.get(user.pk, [])
        rows.append({
            "user": user,
            "label": user_label(user),
            "field": FIELD_FA.get(getattr(getattr(user, "learner_profile", None), "study_field", ""), "رشته نامشخص"),
            "plans": " + ".join(e.plan.name_fa for e in ents) or "رایگان",
            "remaining": _remaining(ents, now),
            "selected": str(user.pk) == selected_id,
        })

    subscribed = User.objects.filter(Exists(Entitlement.objects.filter(_active_q(when=now), user=OuterRef("pk"))))
    paid = Order.objects.filter(status=Order.STATUS_PAID)
    expiring = Entitlement.objects.filter(_active_q(when=now), ends_at__lte=now + timedelta(days=7))
    week_ago = now - timedelta(days=7)
    kpis = [
        {"label": "مشترک فعال", "value": subscribed.count(), "bars": _sparkline(_daily_counts(paid, "paid_at"))},
        {"label": "خرید این هفته", "value": paid.filter(paid_at__gte=week_ago).count(), "bars": _sparkline(_daily_counts(paid, "paid_at"))},
        {"label": "انقضا تا ۷ روز", "value": expiring.values("user").distinct().count(), "bars": _sparkline(_daily_counts(_people(), "date_joined")), "warn": True},
    ]
    segments = [
        (key, label, _segment_filter(base, key, now).count())
        for key, label in [("all", "همه"), ("subscribed", "مشترک"), ("expiring", "نزدیک انقضا"), ("expired", "منقضی"), ("blocked", "مسدود")]
    ]

    drawer = None
    if selected_id and selected_id.isdigit():
        drawer = _user_summary(get_object_or_404(User.objects.select_related("learner_profile"), pk=selected_id), now)

    return render(request, "billing/console/users.html", {
        "active": "users", "rows": rows, "page": page, "q": q, "seg": segment, "segments": segments,
        "kpis": kpis, "drawer": drawer, "plans": _grantable_plans(), "durations": DURATION_CHOICES,
    })


def _user_summary(user, now):
    ents = list(_active_entitlements_qs(now).filter(user=user))
    events = []
    for order in Order.objects.filter(user=user, status=Order.STATUS_PAID).select_related("plan")[:3]:
        events.append({"when": order.paid_at, "text": f"خرید {order.plan.name_fa}", "tone": "spec" if order.plan.kind == Plan.KIND_PRODUCT else "accent"})
    for action in AdminAction.objects.filter(target_user=user)[:3]:
        events.append({"when": action.created_at, "text": action.summary, "tone": "muted"})
    events.sort(key=lambda e: e["when"], reverse=True)
    profile = getattr(user, "learner_profile", None)
    return {
        "user": user,
        "label": user_label(user),
        "contact": user_contact(user),
        "field": FIELD_FA.get(getattr(profile, "study_field", ""), "رشته نامشخص"),
        "entitlements": ents,
        "events": events[:4],
    }


@superuser_required
def user_detail(request, pk):
    user = get_object_or_404(User.objects.select_related("learner_profile"), pk=pk)
    now = timezone.now()
    entitlements = Entitlement.objects.filter(user=user).select_related("plan", "order", "granted_by")
    have = services.effective_features(user)
    names = {f.key: f for f in Feature.objects.filter(key__in=have)}
    features = []
    for key, grant in have.items():
        used = services.usage_count(user, key, grant["period"]) if grant["limit"] is not None else 0
        features.append({
            "name": names[key].name_fa if key in names else key,
            "limit": grant["limit"], "period": dict(PERIOD_CHOICES).get(grant["period"], ""), "used": used,
            "pct": min(100, round(100 * used / grant["limit"])) if grant["limit"] else 0,
            "unit": names[key].unit_fa if key in names else "",
            "sources": "، ".join(grant["sources"]),
        })
    roles_active = list(RoleAssignment.objects.filter(user=user, revoked_at__isnull=True).select_related("role"))
    return render(request, "billing/console/user_detail.html", {
        "active": "users",
        "u": user,
        "label": user_label(user),
        "contact": user_contact(user),
        "field": FIELD_FA.get(getattr(getattr(user, "learner_profile", None), "study_field", ""), "رشته نامشخص"),
        "entitlements": [{"e": e, "active": e.is_active_at(now)} for e in entitlements],
        "features": features,
        "orders": Order.objects.filter(user=user).select_related("plan", "discount")[:30],
        "sessions": UserSession.objects.filter(user=user, revoked_at__isnull=True, refresh_expires_at__gt=now).order_by("-last_used_at")[:20],
        "roles_active": roles_active,
        "roles": Role.objects.order_by("name"),
        "actions": AdminAction.objects.filter(target_user=user).select_related("actor")[:30],
        "plans": _grantable_plans(),
        "durations": DURATION_CHOICES,
        "now": now,
    })


def _back_to_user(request, user):
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, request.is_secure()):
        return redirect(nxt)
    return redirect("console:user", pk=user.pk)


def _days(value):
    text = latin_digits(value).strip()
    if text == "":
        return None
    if not text.isdigit() or int(text) <= 0:
        raise ValueError
    return int(text)


@superuser_required
@require_POST
def user_grant(request, pk):
    user = get_object_or_404(User, pk=pk)
    plan = Plan.objects.filter(pk=request.POST.get("plan"), is_free=False).first()
    try:
        days = _days(request.POST.get("custom_days") or request.POST.get("days", ""))
    except ValueError:
        messages.error(request, "مدت را به روز و به شکل عدد بنویسید.")
        return _back_to_user(request, user)
    if plan is None:
        messages.error(request, "یک پلن یا محصول انتخاب کنید.")
        return _back_to_user(request, user)
    note = request.POST.get("note", "").strip()
    ent = services.grant(user, plan, days=days, source=Entitlement.SOURCE_ADMIN, actor=request.user, note=note)
    length = fa_digits(f"{days} روز") if days else "دائمی"
    services.record(request, "grant", f"دادن {plan.name_fa} ({length})", target_user=user, details={"entitlement": ent.pk, "note": note})
    messages.success(request, f"{plan.name_fa} برای {user_label(user)} فعال شد.")
    return _back_to_user(request, user)


@superuser_required
@require_POST
def entitlement_extend(request, pk, eid):
    user = get_object_or_404(User, pk=pk)
    ent = get_object_or_404(Entitlement, pk=eid, user=user)
    try:
        days = _days(request.POST.get("days", ""))
        if days is None:
            raise ValueError
        services.extend(ent, days)
    except ValueError:
        messages.error(request, "تعداد روز تمدید را درست وارد کنید.")
        return _back_to_user(request, user)
    except services.BillingError as exc:
        messages.error(request, exc.message)
        return _back_to_user(request, user)
    services.record(request, "extend", fa_digits(f"تمدید {ent.plan.name_fa} به‌مدت {days} روز"), target_user=user, details={"entitlement": ent.pk})
    messages.success(request, "تمدید شد.")
    return _back_to_user(request, user)


@superuser_required
@require_POST
def entitlement_revoke(request, pk, eid):
    user = get_object_or_404(User, pk=pk)
    ent = get_object_or_404(Entitlement, pk=eid, user=user)
    services.revoke(ent, request.user)
    services.record(request, "revoke", f"لغو {ent.plan.name_fa}", target_user=user, details={"entitlement": ent.pk})
    messages.success(request, "دسترسی لغو شد.")
    return _back_to_user(request, user)


@superuser_required
@require_POST
def user_block(request, pk):
    user = get_object_or_404(User, pk=pk)
    if user == request.user:
        messages.error(request, "نمی‌توانید حساب خودتان را مسدود کنید.")
        return _back_to_user(request, user)
    block = request.POST.get("block") == "1"
    user.is_active = not block
    user.save(update_fields=["is_active"])
    if block:
        revoke_all_user_sessions(user, request=request, actor=request.user, reason="blocked_by_admin")
    services.record(request, "block" if block else "unblock", "مسدود کردن حساب" if block else "رفع مسدودی حساب", target_user=user)
    messages.success(request, "حساب مسدود شد و از همه‌ی دستگاه‌ها خارج شد." if block else "مسدودی برداشته شد.")
    return _back_to_user(request, user)


@superuser_required
@require_POST
def user_logout_all(request, pk):
    user = get_object_or_404(User, pk=pk)
    revoke_all_user_sessions(user, request=request, actor=request.user, reason="logout_all_by_admin")
    services.record(request, "logout_all", "خروج از همه‌ی دستگاه‌ها", target_user=user)
    messages.success(request, "کاربر از همه‌ی دستگاه‌ها خارج شد.")
    return _back_to_user(request, user)


@superuser_required
@require_POST
def user_role(request, pk):
    user = get_object_or_404(User, pk=pk)
    role = get_object_or_404(Role, key=request.POST.get("role", ""))
    if request.POST.get("op") == "revoke":
        for assignment in RoleAssignment.objects.filter(user=user, role=role, revoked_at__isnull=True):
            revoke_platform_role(assignment, actor=request.user, request=request, reason="billing console")
        summary = f"گرفتن نقش {role.name}"
    else:
        assign_platform_role(user=user, role_key=role.key, actor=request.user, request=request, reason="billing console")
        summary = f"دادن نقش {role.name}"
    services.record(request, "role", summary, target_user=user)
    messages.success(request, summary + " انجام شد.")
    return _back_to_user(request, user)


def _confirmation_matches(user, typed):
    """The operator typed this user's mobile number, email or username."""
    typed = latin_digits(typed).strip().lower()
    if not typed:
        return False
    profile = getattr(user, "learner_profile", None)
    known = {(user.email or "").lower(), user.username.lower(), (getattr(profile, "phone", None) or "").lower()}
    return typed in known - {""}


@superuser_required
@require_POST
def user_delete(request, pk):
    user = get_object_or_404(User.objects.select_related("learner_profile"), pk=pk)
    if user == request.user or user.is_superuser:
        messages.error(request, "حساب خودتان و حساب‌های سوپریوزر از پنل حذف نمی‌شوند.")
        return redirect("console:user", pk=user.pk)
    if not _confirmation_matches(user, request.POST.get("confirm", "")):
        messages.error(request, "برای تأیید، شماره‌ی موبایل یا ایمیل همین کاربر را دقیق وارد کنید.")
        return redirect(f"{reverse('console:user', args=[user.pk])}#delete")
    if not request.user.check_password(request.POST.get("password", "")):
        messages.error(request, "رمز حساب درست نیست؛ کاربر حذف نشد.")
        return redirect(f"{reverse('console:user', args=[user.pk])}#delete")

    label = user_label(user)
    contact = user_contact(user)
    snapshot = f"{label} · {contact}" if contact and contact != label else label
    paid = Order.objects.filter(user=user, status=Order.STATUS_PAID)
    with transaction.atomic():
        services.record(request, "user_delete", f"حذف کاربر {snapshot}"[:255], target_user=user, details={
            "user_id": user.pk, "username": user.username, "email": user.email,
            "phone": getattr(getattr(user, "learner_profile", None), "phone", None) or "",
            "paid_orders_kept": paid.count(),
        })
        # Paid orders stay, unlinked, for the sales figures; unpaid ones go.
        paid.update(deleted_user_label=snapshot[:160])
        Order.objects.filter(user=user).exclude(status=Order.STATUS_PAID).delete()
        user.delete()
    messages.success(request, f"کاربر «{label}» و همه‌ی اطلاعاتش حذف شد. پرداخت‌هایش در گزارش فروش ماند.")
    return redirect("console:users")


@superuser_required
def users_export(request):
    now = timezone.now()
    qs = _search(_segment_filter(_people().select_related("learner_profile").order_by("-date_joined"), request.GET.get("seg", "all"), now), request.GET.get("q", ""))
    active = {}
    for ent in _active_entitlements_qs(now).filter(user__in=qs):
        active.setdefault(ent.user_id, []).append(ent)
    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="pharmenta-users-{timezone.localdate():%Y%m%d}.csv"'
    response.write("﻿")  # so Excel reads the Persian text as UTF-8
    writer = csv.writer(response)
    writer.writerow(["id", "نام", "موبایل", "ایمیل", "رشته", "پلن‌های فعال", "پایان اشتراک", "تاریخ عضویت", "وضعیت"])
    for user in qs.iterator(chunk_size=500):
        profile = getattr(user, "learner_profile", None)
        ents = active.get(user.pk, [])
        ends = [e.ends_at for e in ents]
        writer.writerow([
            user.pk, user_label(user), getattr(profile, "phone", "") or "", user.email,
            FIELD_FA.get(getattr(profile, "study_field", ""), ""),
            " + ".join(e.plan.name_fa for e in ents),
            "دائمی" if None in ends else (max(ends).date().isoformat() if ends else ""),
            user.date_joined.date().isoformat(), "فعال" if user.is_active else "مسدود",
        ])
    services.record(request, "export", "خروجی گرفتن از فهرست کاربران")
    return response


# -- plans --------------------------------------------------------------------

@superuser_required
def plans(request):
    rows = (
        Plan.objects.annotate(
            n_features=Count("plan_features", distinct=True),
            n_prices=Count("prices", filter=Q(prices__is_active=True), distinct=True),
            n_active=Count("entitlements", filter=_active_q("entitlements__"), distinct=True),
        ).order_by("kind", "order", "id")
    )
    return render(request, "billing/console/plans.html", {
        "active": "plans",
        "plans": [p for p in rows if p.kind == Plan.KIND_PLAN],
        "products": [p for p in rows if p.kind == Plan.KIND_PRODUCT],
    })


def feature_line(pf):
    """How a feature reads on the plan's card: its own wording, or its name
    with the cap."""
    if pf.label_fa:
        return pf.label_fa
    if pf.feature.countable and pf.limit is not None:
        return fa_digits(f"{pf.limit} {pf.feature.unit_fa or 'بار'} {dict(PERIOD_CHOICES)[pf.period]}") + f" · {pf.feature.name_fa}"
    return pf.feature.name_fa


def _wizard(request, plan, step, extra):
    done = {"basics": plan is not None}
    if plan is not None:
        done["features"] = plan.plan_features.exists()
        done["prices"] = plan.is_free or plan.prices.exists()
    steps = [
        {"key": key, "label": label, "n": fa_digits(i), "current": key == step, "done": done.get(key, False) and key != step}
        for i, (key, label) in enumerate(STEPS, start=1)
    ]
    preview = []
    if plan is not None:
        for pf in plan.plan_features.select_related("feature").order_by("feature__order"):
            if pf.is_listed:
                preview.append(feature_line(pf))
        preview += plan.extra_lines
    cheapest = plan.prices.filter(is_active=True).order_by("price_toman").first() if plan else None
    return render(request, f"billing/console/plan_{step}.html", {
        "active": "plans", "plan": plan, "steps": steps, "step": step, "preview": preview, "cheapest": cheapest, **extra,
    })


@superuser_required
def plan_new(request):
    kind = request.GET.get("kind", Plan.KIND_PLAN)
    form = PlanBasicsForm(request.POST or None, initial={"kind": kind})
    if request.method == "POST" and form.is_valid():
        plan = form.save(commit=False)
        plan.status = Plan.STATUS_HIDDEN  # published from the last step
        plan.save()
        services.record(request, "plan_create", f"ساخت {plan.get_kind_display()} «{plan.name_fa}»", details={"plan": plan.pk})
        return redirect("console:plan_features", pk=plan.pk)
    return _wizard(request, None, "basics", {"form": form})


@superuser_required
def plan_basics(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    form = PlanBasicsForm(request.POST or None, instance=plan)
    if request.method == "POST" and form.is_valid():
        form.save()
        services.record(request, "plan_edit", f"ویرایش اطلاعات «{plan.name_fa}»", details={"plan": plan.pk})
        return redirect("console:plan_features", pk=plan.pk)
    return _wizard(request, plan, "basics", {"form": form})


@superuser_required
def plan_features(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    current = {pf.feature_id: pf for pf in plan.plan_features.all()}
    features = list(Feature.objects.filter(is_active=True))
    if request.method == "POST":
        errors = []
        with transaction.atomic():
            for feature in features:
                on = request.POST.get(f"f_{feature.pk}") == "on"
                pf = current.get(feature.pk)
                if not on:
                    if pf is not None:
                        pf.delete()
                    continue
                limit = None
                period = request.POST.get(f"period_{feature.pk}") or "day"
                if feature.countable:
                    raw = latin_digits(request.POST.get(f"limit_{feature.pk}", "")).strip()
                    if raw:
                        if not raw.isdigit() or int(raw) <= 0:
                            errors.append(feature.name_fa)
                            continue
                        limit = int(raw)
                label = (request.POST.get(f"label_{feature.pk}") or "").strip()[:160]
                # a card only sends "listed" once its form shows the switch
                listed = request.POST.get(f"listed_{feature.pk}") == "on" if f"shown_{feature.pk}" in request.POST else True
                if pf is None:
                    PlanFeature.objects.create(plan=plan, feature=feature, limit=limit, period=period, label_fa=label, is_listed=listed)
                else:
                    pf.limit, pf.period, pf.label_fa, pf.is_listed = limit, period, label, listed
                    pf.save(update_fields=["limit", "period", "label_fa", "is_listed"])
        if errors:
            messages.error(request, "سقف این امکانات باید عدد مثبت یا خالی باشد: " + "، ".join(errors))
            return redirect("console:plan_features", pk=plan.pk)
        services.record(request, "plan_features", f"تغییر امکانات «{plan.name_fa}»", details={"plan": plan.pk})
        if request.POST.get("stay"):
            messages.success(request, "امکانات ذخیره شد.")
            return redirect("console:plan_features", pk=plan.pk)
        return redirect("console:plan_review" if plan.is_free else "console:plan_prices", pk=plan.pk)
    cards = [
        {"f": f, "pf": current.get(f.pk), "on": f.pk in current, "limit": current[f.pk].limit if f.pk in current else None,
         "period": current[f.pk].period if f.pk in current else "day",
         "label": current[f.pk].label_fa if f.pk in current else "", "listed": current[f.pk].is_listed if f.pk in current else True}
        for f in features
    ]
    return _wizard(request, plan, "features", {
        "cards": cards, "periods": PERIOD_CHOICES, "feature_form": FeatureForm(),
        "scope_types": SCOPE_TYPES, "categories": TOPIC_CATEGORY_CHOICES,
    })


@superuser_required
def plan_prices(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if plan.is_free:
        return redirect("console:plan_review", pk=plan.pk)
    if request.method == "POST":
        bad = False
        with transaction.atomic():
            for price in plan.prices.all():
                if request.POST.get(f"delete_{price.pk}") == "on":
                    if price.orders.exists():
                        price.is_active = False
                        price.save(update_fields=["is_active"])
                    else:
                        price.delete()
                    continue
                amount = parse_amount(request.POST.get(f"price_{price.pk}", ""))
                if amount is None:
                    bad = True
                    continue
                price.price_toman = amount
                price.compare_at_toman = parse_amount(request.POST.get(f"compare_{price.pk}", ""))
                price.label_fa = (request.POST.get(f"plabel_{price.pk}") or "").strip()[:40]
                price.is_active = request.POST.get(f"active_{price.pk}") == "on"
                price.save(update_fields=["price_toman", "compare_at_toman", "label_fa", "is_active"])
            new_amount = parse_amount(request.POST.get("new_price", ""))
            if new_amount is not None:
                try:
                    days = _days(request.POST.get("new_custom_days") or request.POST.get("new_days", ""))
                except ValueError:
                    days, bad = None, True
                if not bad:
                    PlanPrice.objects.create(
                        plan=plan, duration_days=days, price_toman=new_amount, order=plan.prices.count(),
                        compare_at_toman=parse_amount(request.POST.get("new_compare", "")),
                        label_fa=(request.POST.get("new_label") or "").strip()[:40],
                    )
        if bad:
            messages.error(request, "قیمت‌ها و مدت‌ها باید عدد باشند.")
            return redirect("console:plan_prices", pk=plan.pk)
        services.record(request, "plan_prices", f"تغییر قیمت‌های «{plan.name_fa}»", details={"plan": plan.pk})
        if request.POST.get("stay"):
            messages.success(request, "قیمت‌ها ذخیره شد.")
            return redirect("console:plan_prices", pk=plan.pk)
        return redirect("console:plan_review", pk=plan.pk)
    return _wizard(request, plan, "prices", {"prices": plan.prices.all(), "durations": DURATION_CHOICES})


@superuser_required
def plan_review(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if request.method == "POST":
        status = request.POST.get("status")
        if status in dict(Plan.STATUS_CHOICES):
            if status == Plan.STATUS_ACTIVE and not plan.is_free and not plan.prices.filter(is_active=True).exists():
                messages.error(request, "برای فروش، دست‌کم یک قیمت فعال لازم است.")
                return redirect("console:plan_prices", pk=plan.pk)
            plan.status = status
            plan.save(update_fields=["status", "updated_at"])
            services.record(request, "plan_status", f"«{plan.name_fa}»: {plan.get_status_display()}", details={"plan": plan.pk})
            messages.success(request, f"وضعیت «{plan.name_fa}» ذخیره شد: {plan.get_status_display()}.")
        return redirect("console:plans")
    return _wizard(request, plan, "review", {
        "statuses": Plan.STATUS_CHOICES,
        "features_rows": plan.plan_features.select_related("feature").order_by("feature__order"),
        "prices": plan.prices.filter(is_active=True),
        "holders": Entitlement.objects.filter(_active_q(), plan=plan).count(),
    })


@superuser_required
@require_POST
def plan_copy(request, pk):
    source = get_object_or_404(Plan, pk=pk)
    with transaction.atomic():
        copy = Plan.objects.create(
            kind=source.kind, slug=f"{source.slug}-copy-{timezone.now():%H%M%S}", name_fa=f"{source.name_fa} (کپی)",
            name_en=source.name_en, tagline_fa=source.tagline_fa, audience=source.audience,
            description_fa=source.description_fa, badge_fa=source.badge_fa, cta_label_fa=source.cta_label_fa,
            extra_lines_fa=source.extra_lines_fa, status=Plan.STATUS_HIDDEN, order=source.order + 1,
        )
        PlanFeature.objects.bulk_create(
            PlanFeature(plan=copy, feature_id=pf.feature_id, limit=pf.limit, period=pf.period, label_fa=pf.label_fa, is_listed=pf.is_listed)
            for pf in source.plan_features.all()
        )
        PlanPrice.objects.bulk_create(
            PlanPrice(plan=copy, duration_days=p.duration_days, price_toman=p.price_toman, order=p.order,
                      compare_at_toman=p.compare_at_toman, label_fa=p.label_fa)
            for p in source.prices.filter(is_active=True)
        )
    services.record(request, "plan_copy", f"کپی «{source.name_fa}»", details={"plan": copy.pk, "from": source.pk})
    messages.success(request, "کپی ساخته شد؛ نامش را عوض کنید و منتشرش کنید.")
    return redirect("console:plan_basics", pk=copy.pk)


@superuser_required
@require_POST
def plan_delete(request, pk):
    plan = get_object_or_404(Plan, pk=pk)
    if not plan.can_be_deleted:
        messages.error(request, "این پلن خریدار یا دسترسی داده‌شده دارد و حذف نمی‌شود؛ وضعیتش را «غیرفعال» کنید.")
        return redirect("console:plan_review", pk=plan.pk)
    name = plan.name_fa
    services.record(request, "plan_delete", f"حذف {plan.get_kind_display()} «{name}»", details={"plan": plan.pk})
    plan.delete()
    messages.success(request, f"«{name}» حذف شد.")
    return redirect("console:plans")


# -- features -----------------------------------------------------------------

@superuser_required
def features(request):
    rows = Feature.objects.annotate(n_plans=Count("plan_features")).order_by("order", "id")
    return render(request, "billing/console/features.html", {
        "active": "features", "rows": rows, "form": FeatureForm(), "scope_types": SCOPE_TYPES,
        "categories": TOPIC_CATEGORY_CHOICES, "edit_forms": {f.pk: FeatureEditForm(instance=f) for f in rows},
    })


def _back(request, fallback):
    nxt = request.POST.get("next", "")
    if nxt and url_has_allowed_host_and_scheme(nxt, {request.get_host()}, request.is_secure()):
        return redirect(nxt)
    return redirect(fallback)


@superuser_required
@require_POST
def feature_new(request):
    form = FeatureForm(request.POST)
    if form.is_valid():
        feature = form.save()
        services.record(request, "feature_create", f"تعریف امکان «{feature.name_fa}» ({feature.get_kind_display()})", details={"feature": feature.key})
        if feature.kind == Feature.KIND_CUSTOM:
            messages.success(request, f"«{feature.name_fa}» ثبت شد. تا وقتی در کد به شناسه‌ی {feature.key} وصل نشود، چیزی را باز یا قفل نمی‌کند.")
        else:
            messages.success(request, f"«{feature.name_fa}» ثبت شد و محتوایش از همین حالا فقط برای پلن‌هایی که آن را دارند باز است.")
    else:
        errors = "؛ ".join(str(e) for errs in form.errors.values() for e in errs)
        messages.error(request, f"امکان ثبت نشد: {errors}")
    return _back(request, "console:features")


@superuser_required
@require_POST
def feature_edit(request, pk):
    feature = get_object_or_404(Feature, pk=pk)
    op = request.POST.get("op")
    if op == "toggle":
        feature.is_active = not feature.is_active
        feature.save(update_fields=["is_active"])
        services.record(request, "feature_toggle", f"«{feature.name_fa}»: {'فعال' if feature.is_active else 'غیرفعال'}")
    elif op == "delete":
        if feature.kind == Feature.KIND_BUILTIN:
            messages.error(request, "امکانات اصلی اپ حذف نمی‌شوند؛ می‌توانید غیرفعالش کنید.")
            return redirect("console:features")
        services.record(request, "feature_delete", f"حذف امکان «{feature.name_fa}»", details={"feature": feature.key})
        feature.delete()
        messages.success(request, "امکان حذف شد.")
    else:
        form = FeatureEditForm(request.POST, instance=feature)
        if form.is_valid():
            form.save()
            services.record(request, "feature_edit", f"ویرایش امکان «{feature.name_fa}»")
            messages.success(request, "ذخیره شد.")
        else:
            messages.error(request, "فیلدها را درست پر کنید.")
    return redirect("console:features")


# -- discounts ----------------------------------------------------------------

@superuser_required
def discounts(request):
    form = DiscountForm(request.POST or None)
    if request.method == "POST":
        if form.is_valid():
            d = form.cleaned_data
            code = DiscountCode.objects.create(
                code=d["code"],
                percent=d["value"] if d["kind"] == DiscountCode.KIND_PERCENT else None,
                amount_toman=d["value"] if d["kind"] == DiscountCode.KIND_AMOUNT else None,
                final_price_toman=d["value"] if d["kind"] == DiscountCode.KIND_FINAL else None,
                max_uses=d["max_uses"], starts_at=d["starts"], ends_at=d["ends"], note=d["note"],
            )
            code.plans.set(d["plans"])
            services.record(request, "discount_create", f"ساخت کد تخفیف {code.code}")
            messages.success(request, f"کد {code.code} ساخته شد.")
            return redirect("console:discounts")
        messages.error(request, "کد ساخته نشد؛ خطاها را ببینید.")
    rows = DiscountCode.objects.prefetch_related("plans").annotate(
        revenue=Sum("orders__payable_toman", filter=Q(orders__status=Order.STATUS_PAID))
    )
    return render(request, "billing/console/discounts.html", {"active": "discounts", "form": form, "rows": rows, "now": timezone.now()})


@superuser_required
@require_POST
def discount_toggle(request, pk):
    code = get_object_or_404(DiscountCode, pk=pk)
    code.is_active = not code.is_active
    code.save(update_fields=["is_active"])
    services.record(request, "discount_toggle", f"کد {code.code}: {'فعال' if code.is_active else 'غیرفعال'}")
    return redirect("console:discounts")


@superuser_required
@require_POST
def discount_delete(request, pk):
    """Gone for good; orders paid with it keep what it took off."""
    code = get_object_or_404(DiscountCode, pk=pk)
    services.record(request, "discount_delete", f"حذف کد تخفیف {code.code}", details={"used": code.used_count})
    code.delete()
    messages.success(request, f"کد {code.code} حذف شد.")
    return redirect("console:discounts")


# -- payment gateways ---------------------------------------------------------

def _masked(merchant_id):
    return f"••••••••{merchant_id[-4:]}" if merchant_id else ""


def _tristate(value):
    return {"on": True, "off": False}.get(value)


# What each gateway calls its merchant id, and what a valid one looks like.
GATEWAY_FIELDS = {
    PaymentGateway.KIND_ZARINPAL: ("مرچنت‌کد زرین‌پال", r"[A-Za-z0-9-]{20,64}", "مرچنت‌کد باید همان کد ۳۶ کاراکتری پنل زرین‌پال باشد."),
    PaymentGateway.KIND_SEP: ("شمارهٔ ترمینال سپ", r"\d{5,12}", "شمارهٔ ترمینال سپ باید فقط رقم باشد (همان TerminalId که سپ داده است)."),
    PaymentGateway.KIND_ZIBAL: ("مرچنت زیبال", r"[A-Za-z0-9_-]{1,64}", "مرچنت زیبال باید فقط شامل حروف لاتین، عدد، خط تیره یا زیرخط باشد."),
}


def _site_url():
    return settings.SITE_PUBLIC_URL.rstrip("/")


def _site_callback(kind):
    """The callback on the site's own domain, which is what gets registered
    with a gateway, whichever host this page is served from."""
    return _site_url() + reverse("billing-callback-gateway", args=[kind], urlconf="config.urls_site")


def _gateway_facts():
    """What a gateway's application form asks for: the site, the callback for
    each kind, the port, and the address the site's domain points at."""
    site = _site_url()
    host = urlsplit(site).hostname or ""
    try:
        inbound_ip = socket.gethostbyname(host) if host else ""
    except OSError:
        inbound_ip = ""
    return {
        "site_url": site,
        "host": host,
        "port": 443 if site.startswith("https://") else 80,
        "inbound_ip": inbound_ip,
        "callbacks": [
            (label, _site_callback(kind))
            for kind, label in PaymentGateway.KIND_CHOICES
        ],
    }


def _gateway_state(g):
    return {"kind": g.kind, "enabled": g.is_enabled, "priority": g.priority, "merchant": _masked(g.merchant_id), "sandbox": g.sandbox}


@superuser_required
def gateway(request):
    current = config.current()
    if request.method == "POST":
        if not request.user.check_password(request.POST.get("password", "")):
            messages.error(request, "رمز حساب درست نیست؛ چیزی ذخیره نشد.")
            return redirect("console:gateway")
        row = BillingSettings.objects.first() or BillingSettings()
        before = {"return_url": current.return_url, "enforcement": current.enforcement, "sales": current.sales_enabled}
        return_url = request.POST.get("return_url", "").strip()
        if return_url and not re.fullmatch(r"https?://\S+", return_url):
            messages.error(request, "لینک بازگشت باید با https:// شروع شود.")
            return redirect("console:gateway")
        row.return_url = return_url
        row.enforcement_enabled = _tristate(request.POST.get("enforcement"))
        row.sales_enabled = request.POST.get("sales_enabled") == "on"
        row.updated_by = request.user
        row.save()
        after = config.current()
        services.record(request, "gateway_settings", "تغییر تنظیمات فروش", details={
            "before": before,
            "after": {"return_url": after.return_url, "enforcement": after.enforcement, "sales": after.sales_enabled},
        })
        messages.success(request, "تنظیمات ذخیره شد. سرورهای دیگر تا نیم دقیقه‌ی دیگر آن را می‌خوانند.")
        return redirect("console:gateway")

    gateways = list(PaymentGateway.objects.all())
    defined = {g.kind for g in gateways}
    return render(request, "billing/console/gateway.html", {
        "active": "gateway",
        "cfg": current,
        "row": BillingSettings.objects.first(),
        "gateways": [(g, _masked(g.merchant_id), GATEWAY_FIELDS[g.kind][0]) for g in gateways],
        "env_gateway": current.gateways[0] if current.gateways and current.gateways[0].source == "env" else None,
        "env_masked": _masked(current.gateways[0].merchant_id) if current.gateways and current.gateways[0].source == "env" else "",
        "addable": [(k, label) for k, label in PaymentGateway.KIND_CHOICES if k not in defined],
        "facts": _gateway_facts(),
        "outbound_ip": caches["default"].get("billing:outbound-ip"),
        "last_paid": Order.objects.filter(status=Order.STATUS_PAID).select_related("plan").order_by("-paid_at").first(),
        "last_failed": Order.objects.filter(status=Order.STATUS_FAILED).exclude(error="").order_by("-created_at").first(),
        "last_change": AdminAction.objects.filter(action__in=["gateway_settings", "gateway_edit"]).select_related("actor").first(),
    })


@superuser_required
def gateway_edit(request, pk=None):
    if pk is None:
        kind = request.GET.get("kind") or request.POST.get("kind")
        if kind not in GATEWAY_FIELDS or PaymentGateway.objects.filter(kind=kind).exists():
            messages.error(request, "این درگاه را نمی‌شود افزود.")
            return redirect("console:gateway")
        gw = PaymentGateway(kind=kind, priority=10 * (PaymentGateway.objects.count() + 1))
    else:
        gw = get_object_or_404(PaymentGateway, pk=pk)
    label, pattern, hint = GATEWAY_FIELDS[gw.kind]
    if request.method == "POST":
        url = reverse("console:gateway_edit", args=[gw.pk]) if gw.pk else f"{reverse('console:gateway_new')}?kind={gw.kind}"
        if not request.user.check_password(request.POST.get("password", "")):
            messages.error(request, "رمز حساب درست نیست؛ چیزی ذخیره نشد.")
            return redirect(url)
        before = _gateway_state(gw) if gw.pk else None
        merchant = latin_digits(request.POST.get("merchant_id", "")).strip()
        if merchant:
            if not re.fullmatch(pattern, merchant):
                messages.error(request, hint)
                return redirect(url)
            gw.merchant_id = merchant
        elif not gw.merchant_id:
            messages.error(request, f"{label} را وارد کنید.")
            return redirect(url)
        try:
            gw.priority = max(0, min(999, int(latin_digits(request.POST.get("priority", "") or "10"))))
        except ValueError:
            messages.error(request, "ترتیب باید عدد باشد.")
            return redirect(url)
        gw.title = request.POST.get("title", "").strip()[:60]
        gw.is_enabled = request.POST.get("is_enabled") == "on"
        gw.sandbox = gw.kind == PaymentGateway.KIND_ZARINPAL and request.POST.get("sandbox") == "on"
        gw.updated_by = request.user
        gw.save()
        services.record(request, "gateway_edit", f"{'افزودن' if before is None else 'ویرایش'} درگاه {gw.display_name}", details={
            "before": before, "after": _gateway_state(gw),
        })
        messages.success(request, f"درگاه {gw.display_name} ذخیره شد.")
        return redirect("console:gateway")
    return render(request, "billing/console/gateway_form.html", {
        "active": "gateway", "gw": gw, "label": label, "masked": _masked(gw.merchant_id),
        "callback": _site_callback(gw.kind),
    })


@superuser_required
@require_POST
def gateway_toggle(request, pk):
    gw = get_object_or_404(PaymentGateway, pk=pk)
    gw.is_enabled = not gw.is_enabled
    gw.updated_by = request.user
    gw.save(update_fields=["is_enabled", "updated_by", "updated_at"])
    services.record(request, "gateway_edit", f"درگاه {gw.display_name}: {'فعال' if gw.is_enabled else 'غیرفعال'}")
    if not PaymentGateway.objects.filter(is_enabled=True).exists():
        messages.warning(request, "هیچ درگاهی فعال نیست؛ تا یکی را فعال نکنید، خرید ممکن نیست.")
    else:
        messages.success(request, f"درگاه {gw.display_name} {'فعال' if gw.is_enabled else 'غیرفعال'} شد.")
    return redirect("console:gateway")


@superuser_required
@require_POST
def gateway_test(request, pk):
    gw = get_object_or_404(PaymentGateway, pk=pk)
    callback = _site_callback(gw.kind)
    try:
        if gw.kind == PaymentGateway.KIND_ZARINPAL:
            message = ZarinpalGateway(gw.merchant_id, gw.sandbox).test(callback)
        elif gw.kind == PaymentGateway.KIND_ZIBAL:
            message = ZibalGateway(gw.merchant_id, gw.sandbox).test(callback)
        else:
            message = SepGateway(gw.merchant_id).test(callback)
        ok = True
    except GatewayError as exc:
        message, ok = f"اتصال ناموفق: {exc}"[:255], False
    gw.last_test_at, gw.last_test_ok, gw.last_test_message = timezone.now(), ok, message
    gw.save(update_fields=["last_test_at", "last_test_ok", "last_test_message", "updated_at"])
    services.record(request, "gateway_test", f"آزمایش اتصال {gw.display_name}: " + ("موفق" if ok else "ناموفق"))
    (messages.success if ok else messages.error)(request, message)
    return redirect("console:gateway")


OUTBOUND_IP_URL = "https://api.ipify.org?format=json"


@superuser_required
@require_POST
def gateway_outbound_ip(request):
    """The address this server's calls to a gateway come from -- the one SEP
    must have on its list. It can differ from the address the domain points
    at, so it is asked of an outside service rather than guessed."""
    try:
        with urllib.request.urlopen(OUTBOUND_IP_URL, timeout=8) as response:
            ip = json.loads(response.read().decode()).get("ip", "")
    except (OSError, ValueError):
        ip = ""
    if ip:
        caches["default"].set("billing:outbound-ip", {"ip": ip, "at": timezone.now()}, 7 * 24 * 3600)
        messages.success(request, f"IP خروجی این سرور: {ip}")
    else:
        messages.error(request, "IP خروجی پیدا نشد؛ سرور به سرویس بررسی IP دسترسی ندارد. آن را از پشتیبانی ران‌فلر بپرسید.")
    return redirect("console:gateway")


# -- sales and audit ----------------------------------------------------------

# -- guest access -------------------------------------------------------------

@superuser_required
def access(request):
    current = config.current()
    if request.method == "POST":
        op = request.POST.get("op")
        if op == "delete_guests":
            if current.guest_access:
                messages.error(request, "اول ورود مهمان را خاموش کنید.")
            else:
                count = guest_tools.delete_guests()
                services.record(request, "guests_delete", fa_digits(f"حذف {count} حساب مهمان"))
                messages.success(request, fa_digits(f"{count} حساب مهمان حذف شد."))
            return redirect("console:access")
        if not request.user.check_password(request.POST.get("password", "")):
            messages.error(request, "رمز حساب درست نیست؛ چیزی تغییر نکرد.")
            return redirect("console:access")
        enable = request.POST.get("guest_access") == "on"
        row = BillingSettings.objects.first() or BillingSettings()
        row.guest_access_enabled = enable
        row.updated_by = request.user
        row.save()
        if enable:
            # Guests deactivated by an earlier switch-off may sign in again.
            guest_tools.guests().update(is_active=True)
            services.record(request, "guest_access", "روشن کردن ورود بدون نام کاربری و رمز")
            messages.success(request, "ورود مهمان روشن شد. سرورهای دیگر تا نیم دقیقه‌ی دیگر آن را می‌خوانند.")
        else:
            ended = guest_tools.end_guest_sessions()
            services.record(request, "guest_access", "خاموش کردن ورود بدون نام کاربری و رمز", details={"sessions_ended": ended})
            messages.success(request, "ورود مهمان خاموش شد و همه‌ی مهمان‌ها خارج شدند.")
        return redirect("console:access")

    guests = guest_tools.guests()
    return render(request, "billing/console/access.html", {
        "active": "access",
        "cfg": current,
        "guest_count": guests.count(),
        "guest_today": guests.filter(date_joined__gte=timezone.now() - timedelta(days=1)).count(),
        "guest_sessions": UserSession.objects.filter(user__guest_account__isnull=False, revoked_at__isnull=True, refresh_expires_at__gt=timezone.now()).count(),
        "last_change": AdminAction.objects.filter(action="guest_access").select_related("actor").first(),
    })


@superuser_required
def sales(request):
    now = timezone.now()
    first = month_start(timezone.localtime(now, services.TEHRAN).date())
    month_from = datetime(first.year, first.month, first.day, tzinfo=services.TEHRAN)
    paid = Order.objects.filter(status=Order.STATUS_PAID)
    this_month = paid.filter(paid_at__gte=month_from)
    revenue = this_month.aggregate(total=Sum("payable_toman"))["total"] or 0
    count = this_month.count()
    by_plan = (
        this_month.values("plan__name_fa").annotate(total=Sum("payable_toman"), n=Count("id")).order_by("-total")
    )
    peak = max([r["total"] or 0 for r in by_plan] or [1]) or 1
    status = request.GET.get("status", "")
    orders = Order.objects.select_related("user", "user__learner_profile", "plan", "discount")
    if status in dict(Order.STATUS_CHOICES):
        orders = orders.filter(status=status)
    page = Paginator(orders, PAGE_SIZE).get_page(request.GET.get("page"))
    return render(request, "billing/console/sales.html", {
        "active": "sales",
        "kpis": [
            {"label": "فروش این ماه", "value": revenue, "money": True},
            {"label": "خرید موفق این ماه", "value": count},
            {"label": "میانگین هر خرید", "value": revenue // count if count else 0, "money": True},
            {"label": "مشترک فعال", "value": User.objects.filter(Exists(Entitlement.objects.filter(_active_q(when=now), user=OuterRef("pk")))).count()},
        ],
        "by_plan": [{**r, "pct": round(100 * (r["total"] or 0) / peak)} for r in by_plan],
        "page": page, "status": status, "statuses": Order.STATUS_CHOICES,
        "labels": {
            o.pk: user_label(o.user) if o.user else f"کاربر حذف‌شده ({o.deleted_user_label or '—'})"
            for o in page.object_list
        },
    })


@superuser_required
def audit(request):
    page = Paginator(AdminAction.objects.select_related("actor", "target_user"), 40).get_page(request.GET.get("page"))
    return render(request, "billing/console/audit.html", {"active": "audit", "page": page})


@superuser_required
def home(request):
    return redirect("console:users")
