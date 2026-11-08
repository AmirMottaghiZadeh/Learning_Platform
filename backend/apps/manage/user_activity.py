from functools import wraps

from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.accounts.models import UserSession
from apps.accounts.services import revoke_user_session
from apps.activity.services import report, click_map, APP_SECTIONS, SITE_SECTIONS
from . import access
from .views import manage_required


def super_required(view):
    @manage_required
    @wraps(view)
    def wrapper(request, *args, **kwargs):
        if not access.platform_admin(request.user):
            return HttpResponseForbidden("این گزارش فقط برای مدیر سامانه قابل دسترسی است.")
        return view(request, *args, **kwargs)
    return wrapper


@super_required
def devices(request):
    qs = UserSession.objects.select_related("user").prefetch_related("addresses")
    q = request.GET.get("q", "").strip()[:120]
    if q:
        qs = qs.filter(Q(user__username__icontains=q) | Q(user__first_name__icontains=q) | Q(device_name__icontains=q) | Q(os_name__icontains=q) | Q(ip_address__icontains=q) | Q(addresses__ip_address__icontains=q)).distinct()
    source = request.GET.get("surface", "")
    if source in {"app", "site", "manage"}:
        qs = qs.filter(surface=source)
    state = request.GET.get("state", "active")
    if state == "active":
        from django.contrib.sessions.models import Session as BrowserSession

        now = timezone.now()
        live_browser_keys = BrowserSession.objects.filter(expire_date__gt=now).values("session_key")
        qs = qs.filter(revoked_at__isnull=True, refresh_expires_at__gt=now).filter(
            Q(django_session_key="") | Q(django_session_key__in=live_browser_keys)
        )
    try:
        page = max(1, int(request.GET.get("page", 1)))
    except ValueError:
        page = 1
    total = qs.count()
    return render(request, "manage/devices.html", {"sessions": qs.order_by("-last_used_at")[(page - 1) * 50:page * 50], "total": total, "q": q, "surface": source, "state": state, "page": page, "has_next": page * 50 < total})


@require_POST
@super_required
def device_revoke(request, session_id):
    session = get_object_or_404(UserSession, pk=session_id)
    revoke_user_session(session, request=request, actor=request.user, reason="device_revoked_by_admin")
    messages.success(request, "دسترسی این دستگاه پایان یافت.")
    return redirect("manage:devices")


@super_required
def usage(request):
    source = request.GET.get("source", "")
    if source not in {"site", "app"}:
        source = ""
    try:
        days = int(request.GET.get("days", 30))
    except ValueError:
        days = 30
    data = report(source=source, days=days)
    names = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]
    rows = []
    for name, values in zip(names, data["matrix"]):
        rows.append({"name": name, "cells": [{"hour": i, "count": count, "level": 0 if not count else min(4, max(1, round(4 * count / (data["peak"] or 1))))} for i, count in enumerate(values)]})
    click_source = request.GET.get("click_source", source or "app")
    if click_source not in {"site", "app"}:
        click_source = "app"
    sections = APP_SECTIONS if click_source == "app" else SITE_SECTIONS
    section = request.GET.get("section", "dashboard" if click_source == "app" else "home")
    if section not in sections:
        section = next(iter(sections))
    area = "article" if request.GET.get("area") == "article" else "screen"
    viewport = request.GET.get("viewport", "mobile")
    if viewport not in {"mobile", "tablet", "desktop"}:
        viewport = "mobile"
    grid = click_map(source=click_source, section=section, days=data["days"], area=area, viewport=viewport)
    peak = max((max(row) for row in grid), default=0)
    click_rows = [[{"count": count, "level": 0 if not count else min(4, max(1, round(4 * count / (peak or 1))))} for count in row] for row in grid]
    return render(request, "manage/usage.html", {"report": data, "heat_rows": rows, "hours": range(24), "click_rows": click_rows, "click_source": click_source, "click_sections": sections.items(), "click_section": section, "click_area": area, "viewport": viewport, "click_total": sum(map(sum, grid))})
