"""Step-up re-authentication for the operations console.

Phase 2 added step-up for the API, where freshness lives on ``UserSession``.
The Data Quality Center runs on a Django login session instead, so it needs its
own recent-proof-of-identity check: holding a browser session open all day must
not be enough to apply or roll back production data.
"""

from datetime import timedelta
from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import authenticate
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.accounts.models import SecurityAuditEvent
from apps.accounts.permissions import platform_permission_required
from apps.accounts.services import record_security_event


STEP_UP_NEXT_SESSION_KEY = "data_quality_step_up_next"


def _session_key():
    return settings.DATA_QUALITY_STEP_UP_SESSION_KEY


def mark_step_up_verified(request):
    request.session[_session_key()] = timezone.now().isoformat()
    record_security_event(
        SecurityAuditEvent.STEP_UP_VERIFIED,
        user=request.user,
        actor=request.user,
        request=request,
        metadata={"scope": "data_quality_center"},
    )


def clear_step_up(request):
    request.session.pop(_session_key(), None)


def has_recent_step_up(request):
    raw = request.session.get(_session_key())
    if not raw:
        return False
    verified_at = parse_datetime(raw) if isinstance(raw, str) else None
    if verified_at is None:
        return False
    ttl = timedelta(minutes=settings.DATA_QUALITY_STEP_UP_TTL_MINUTES)
    return timezone.now() - verified_at <= ttl


def step_up_required(view_func):
    """Send the operator through re-authentication before a sensitive write.

    Only unsafe methods are gated: browsing the console stays frictionless, and
    the confirmation step happens where the damage would be done.
    """

    @wraps(view_func)
    def wrapped(request, *args, **kwargs):
        if request.method in {"GET", "HEAD", "OPTIONS"} or has_recent_step_up(request):
            return view_func(request, *args, **kwargs)

        record_security_event(
            SecurityAuditEvent.AUTHORIZATION_DENIED,
            user=request.user,
            actor=request.user,
            request=request,
            metadata={
                "reason": "step_up_required",
                "scope": "data_quality_center",
                "path": request.path,
                "method": request.method,
            },
        )
        request.session[STEP_UP_NEXT_SESSION_KEY] = request.get_full_path()
        messages.warning(
            request,
            "Confirm your password to continue with this change.",
        )
        return redirect(reverse("data_quality_center:step_up"))

    return wrapped


@platform_permission_required("accounts.view_data_quality_center")
def step_up_view(request):
    """Re-enter the password to refresh the step-up window."""
    next_url = request.session.get(STEP_UP_NEXT_SESSION_KEY) or reverse(
        "data_quality_center:dashboard"
    )
    error = ""

    if request.method == "POST":
        password = request.POST.get("password", "")
        user = authenticate(
            request,
            username=request.user.get_username(),
            password=password,
        )
        if user is None or user.pk != request.user.pk:
            error = "That password is not correct."
            record_security_event(
                SecurityAuditEvent.LOGIN_FAILED,
                user=request.user,
                actor=request.user,
                request=request,
                metadata={"reason": "step_up_failed", "scope": "data_quality_center"},
            )
        else:
            mark_step_up_verified(request)
            request.session.pop(STEP_UP_NEXT_SESSION_KEY, None)
            return redirect(next_url)

    return render(
        request,
        "data_quality_center/step_up.html",
        {
            "nav_section": "",
            "next_url": next_url,
            "error": error,
            "ttl_minutes": settings.DATA_QUALITY_STEP_UP_TTL_MINUTES,
        },
    )
