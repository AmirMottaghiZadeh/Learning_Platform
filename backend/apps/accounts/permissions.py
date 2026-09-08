from functools import wraps

from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission

from .models import SecurityAuditEvent
from .services import (
    record_security_event,
    session_has_recent_step_up,
    user_has_platform_permission,
)


class HasPlatformPermission(BasePermission):
    required_permission = None

    def has_permission(self, request, view):
        permission_name = self.required_permission or getattr(
            view,
            "required_platform_permission",
            None,
        )
        allowed = bool(
            permission_name
            and user_has_platform_permission(request.user, permission_name)
        )
        if not allowed and request.user.is_authenticated:
            record_security_event(
                SecurityAuditEvent.AUTHORIZATION_DENIED,
                user=request.user,
                actor=request.user,
                session=getattr(request, "auth", None),
                request=request,
                metadata={
                    "permission": permission_name,
                    "path": request.path,
                    "method": request.method,
                },
            )
        return allowed


class CanViewRawDrugData(HasPlatformPermission):
    required_permission = "accounts.view_raw_drug_data"


class CanViewSecurityAudit(HasPlatformPermission):
    required_permission = "accounts.view_security_audit"


class CanManagePlatformRoles(HasPlatformPermission):
    required_permission = "accounts.manage_platform_roles"


class HasRecentStepUp(BasePermission):
    def has_permission(self, request, view):
        allowed = session_has_recent_step_up(getattr(request, "auth", None))
        if not allowed and request.user.is_authenticated:
            record_security_event(
                SecurityAuditEvent.AUTHORIZATION_DENIED,
                user=request.user,
                actor=request.user,
                session=getattr(request, "auth", None),
                request=request,
                metadata={
                    "reason": "step_up_required",
                    "path": request.path,
                    "method": request.method,
                },
            )
        return allowed


def platform_permission_required(permission_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect_to_login(request.get_full_path())
            if user_has_platform_permission(request.user, permission_name):
                return view_func(request, *args, **kwargs)
            record_security_event(
                SecurityAuditEvent.AUTHORIZATION_DENIED,
                user=request.user,
                actor=request.user,
                request=request,
                metadata={
                    "permission": permission_name,
                    "path": request.path,
                    "method": request.method,
                },
            )
            raise PermissionDenied

        return wrapped

    return decorator


def require_request_permission(request, permission_name):
    if user_has_platform_permission(request.user, permission_name):
        return
    record_security_event(
        SecurityAuditEvent.AUTHORIZATION_DENIED,
        user=request.user if request.user.is_authenticated else None,
        actor=request.user if request.user.is_authenticated else None,
        request=request,
        metadata={
            "permission": permission_name,
            "path": request.path,
            "method": request.method,
        },
    )
    raise PermissionDenied
