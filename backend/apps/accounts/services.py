import hashlib
import logging
import secrets
from dataclasses import dataclass
from datetime import timedelta
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.db import transaction
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils import timezone

from apps.core.logging import get_request_id

from .models import (
    Role,
    RoleAssignment,
    SecurityAuditEvent,
    SessionRefreshToken,
    UserSession,
)

logger = logging.getLogger(__name__)


class SessionTokenError(ValueError):
    pass


@dataclass(frozen=True)
class IssuedSession:
    session: UserSession
    access_token: str
    refresh_token: str


def hash_session_token(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _new_token(prefix):
    return f"{prefix}_{secrets.token_urlsafe(48)}"


def _request_metadata(request):
    if request is None:
        return {
            "request_id": get_request_id(),
            "ip_address": None,
            "user_agent": "",
        }
    return {
        "request_id": getattr(request, "request_id", get_request_id()),
        "ip_address": request.META.get("REMOTE_ADDR") or None,
        "user_agent": request.META.get("HTTP_USER_AGENT", "")[:255],
    }


def record_security_event(
    event_type,
    *,
    user=None,
    actor=None,
    session=None,
    request=None,
    metadata=None,
):
    request_metadata = _request_metadata(request)
    event_metadata = dict(metadata or {})
    if session is not None:
        # Snapshot the session identifier: retention purges the session row long
        # before the audit row, and the FK would otherwise be nulled out.
        event_metadata.setdefault("session_id", str(session.id))
    return SecurityAuditEvent.objects.create(
        event_type=event_type,
        user=user,
        actor=actor,
        session=session,
        request_id=request_metadata["request_id"],
        ip_address=request_metadata["ip_address"],
        user_agent=request_metadata["user_agent"],
        metadata=event_metadata,
    )


def ensure_default_learner_role(user):
    role, _ = Role.objects.get_or_create(
        key=Role.LEARNER,
        defaults={
            "name": "Learner",
            "description": "Default learning-platform access.",
        },
    )
    assignment = RoleAssignment.objects.filter(
        user=user,
        role=role,
        revoked_at__isnull=True,
    ).first()
    if assignment is None:
        assignment = RoleAssignment.objects.create(user=user, role=role)
    return assignment


def active_role_keys(user):
    if not user or not user.is_authenticated:
        return []
    now = timezone.now()
    return list(
        RoleAssignment.objects.filter(
            user=user,
            revoked_at__isnull=True,
        )
        .filter(
            expires_at__isnull=True,
        )
        .values_list("role__key", flat=True)
    ) + list(
        RoleAssignment.objects.filter(
            user=user,
            revoked_at__isnull=True,
            expires_at__gt=now,
        ).values_list("role__key", flat=True)
    )


def user_has_platform_permission(user, permission_name):
    if not user or not user.is_authenticated or not user.is_active:
        return False
    if user.is_superuser or user.has_perm(permission_name):
        return True
    app_label, codename = permission_name.split(".", 1)
    now = timezone.now()
    return RoleAssignment.objects.filter(
        user=user,
        revoked_at__isnull=True,
        role__permissions__content_type__app_label=app_label,
        role__permissions__codename=codename,
    ).filter(
        expires_at__isnull=True,
    ).exists() or RoleAssignment.objects.filter(
        user=user,
        revoked_at__isnull=True,
        expires_at__gt=now,
        role__permissions__content_type__app_label=app_label,
        role__permissions__codename=codename,
    ).exists()


def _revoke_session_locked(session, *, reason, request=None, actor=None):
    if session.revoked_at is not None:
        return False
    now = timezone.now()
    session.revoked_at = now
    session.revoke_reason = reason
    session.save(update_fields=["revoked_at", "revoke_reason"])
    SessionRefreshToken.objects.filter(
        session=session,
        revoked_at__isnull=True,
    ).update(revoked_at=now)
    record_security_event(
        SecurityAuditEvent.SESSION_REVOKED,
        user=session.user,
        actor=actor or session.user,
        session=session,
        request=request,
        metadata={"reason": reason},
    )
    return True


@transaction.atomic
def issue_user_session(user, *, request=None, device_name=""):
    now = timezone.now()
    access_token = _new_token("phx_access")
    refresh_token = _new_token("phx_refresh")
    access_token_hash = hash_session_token(access_token)
    refresh_token_hash = hash_session_token(refresh_token)
    request_metadata = _request_metadata(request)
    session = UserSession.objects.create(
        user=user,
        access_token_hash=access_token_hash,
        refresh_token_hash=refresh_token_hash,
        access_expires_at=now
        + timedelta(minutes=settings.AUTH_ACCESS_TOKEN_TTL_MINUTES),
        refresh_expires_at=now
        + timedelta(days=settings.AUTH_REFRESH_TOKEN_TTL_DAYS),
        last_used_at=now,
        device_name=device_name.strip()[:120],
        user_agent=request_metadata["user_agent"],
        ip_address=request_metadata["ip_address"],
    )
    SessionRefreshToken.objects.create(
        session=session,
        token_hash=refresh_token_hash,
        expires_at=session.refresh_expires_at,
        issued_at=now,
    )
    active_sessions = list(
        UserSession.objects.select_for_update()
        .filter(
            user=user,
            revoked_at__isnull=True,
            refresh_expires_at__gt=now,
        )
        .exclude(id=session.id)
        .order_by("-last_used_at", "-created_at")
    )
    for stale_session in active_sessions[
        max(0, max(1, settings.AUTH_MAX_ACTIVE_SESSIONS) - 1):
    ]:
        _revoke_session_locked(
            stale_session,
            reason="session_limit",
            request=request,
            actor=user,
        )
    record_security_event(
        SecurityAuditEvent.LOGIN_SUCCEEDED,
        user=user,
        actor=user,
        session=session,
        request=request,
        metadata={"device_name": session.device_name},
    )
    return IssuedSession(
        session=session,
        access_token=access_token,
        refresh_token=refresh_token,
    )


def rotate_refresh_token(refresh_token, *, request=None):
    now = timezone.now()
    token_hash = hash_session_token(refresh_token)
    failure_message = None
    issued_session = None

    with transaction.atomic():
        token_record = (
            SessionRefreshToken.objects.select_for_update()
            .select_related("session__user")
            .filter(token_hash=token_hash)
            .first()
        )
        if not token_record:
            record_security_event(
                SecurityAuditEvent.AUTHORIZATION_DENIED,
                request=request,
                metadata={
                    "reason": "unknown_refresh_token",
                    "token_hash_prefix": token_hash[:12],
                },
            )
            failure_message = "Refresh token is invalid."
        else:
            session = UserSession.objects.select_for_update().get(
                id=token_record.session_id
            )
            if token_record.used_at or token_record.revoked_at:
                _revoke_session_locked(
                    session,
                    reason="refresh_token_reuse",
                    request=request,
                    actor=session.user,
                )
                failure_message = "Refresh token reuse was detected."
            elif (
                session.revoked_at
                or token_record.expires_at <= now
                or session.refresh_expires_at <= now
                or not session.user.is_active
            ):
                _revoke_session_locked(
                    session,
                    reason="refresh_expired_or_inactive",
                    request=request,
                    actor=session.user,
                )
                failure_message = "Refresh token is expired or revoked."
            else:
                access_token = _new_token("phx_access")
                new_refresh_token = _new_token("phx_refresh")
                access_token_hash = hash_session_token(access_token)
                refresh_token_hash = hash_session_token(new_refresh_token)
                access_expires_at = now + timedelta(
                    minutes=settings.AUTH_ACCESS_TOKEN_TTL_MINUTES
                )
                refresh_expires_at = now + timedelta(
                    days=settings.AUTH_REFRESH_TOKEN_TTL_DAYS
                )

                token_record.used_at = now
                token_record.replaced_by_hash = refresh_token_hash
                token_record.save(update_fields=["used_at", "replaced_by_hash"])
                SessionRefreshToken.objects.create(
                    session=session,
                    token_hash=refresh_token_hash,
                    expires_at=refresh_expires_at,
                    issued_at=now,
                )

                session.access_token_hash = access_token_hash
                session.refresh_token_hash = refresh_token_hash
                session.access_expires_at = access_expires_at
                session.refresh_expires_at = refresh_expires_at
                session.last_used_at = now
                session.refresh_rotated_at = now
                session.save(
                    update_fields=[
                        "access_token_hash",
                        "refresh_token_hash",
                        "access_expires_at",
                        "refresh_expires_at",
                        "last_used_at",
                        "refresh_rotated_at",
                    ]
                )
                record_security_event(
                    SecurityAuditEvent.SESSION_REFRESHED,
                    user=session.user,
                    actor=session.user,
                    session=session,
                    request=request,
                )
                issued_session = IssuedSession(
                    session=session,
                    access_token=access_token,
                    refresh_token=new_refresh_token,
                )

    if failure_message:
        raise SessionTokenError(failure_message)
    return issued_session


@transaction.atomic
def revoke_user_session(session, *, request=None, actor=None, reason="logout"):
    locked_session = UserSession.objects.select_for_update().select_related(
        "user"
    ).get(id=session.id)
    _revoke_session_locked(
        locked_session,
        reason=reason,
        request=request,
        actor=actor,
    )
    return locked_session


@transaction.atomic
def revoke_all_user_sessions(user, *, request=None, actor=None, reason="logout_all"):
    sessions = list(
        UserSession.objects.select_for_update()
        .select_related("user")
        .filter(user=user, revoked_at__isnull=True)
    )
    revoked_count = 0
    for session in sessions:
        revoked_count += int(
            _revoke_session_locked(
                session,
                reason=reason,
                request=request,
                actor=actor or user,
            )
        )
    record_security_event(
        SecurityAuditEvent.ALL_SESSIONS_REVOKED,
        user=user,
        actor=actor or user,
        request=request,
        metadata={"revoked_count": revoked_count, "reason": reason},
    )
    return revoked_count


@transaction.atomic
def verify_session_step_up(session, *, request=None):
    locked_session = UserSession.objects.select_for_update().select_related(
        "user"
    ).get(id=session.id)
    if locked_session.revoked_at is not None:
        raise SessionTokenError("This session has been revoked.")
    locked_session.step_up_verified_at = timezone.now()
    locked_session.save(update_fields=["step_up_verified_at"])
    record_security_event(
        SecurityAuditEvent.STEP_UP_VERIFIED,
        user=locked_session.user,
        actor=locked_session.user,
        session=locked_session,
        request=request,
        metadata={"action": "step_up_verified"},
    )
    return locked_session


def session_has_recent_step_up(session):
    if not session or not session.step_up_verified_at:
        return False
    return session.step_up_verified_at >= timezone.now() - timedelta(
        minutes=settings.AUTH_STEP_UP_TTL_MINUTES
    )


@transaction.atomic
def assign_platform_role(
    *,
    user,
    role_key,
    actor,
    reason="",
    expires_at=None,
    request=None,
):
    role = Role.objects.get(key=role_key)
    assignment = (
        RoleAssignment.objects.select_for_update()
        .filter(user=user, role=role, revoked_at__isnull=True)
        .first()
    )
    if assignment:
        assignment.assigned_by = actor
        assignment.reason = reason
        assignment.expires_at = expires_at
        assignment.save(
            update_fields=[
                "assigned_by",
                "reason",
                "expires_at",
            ]
        )
    else:
        assignment = RoleAssignment.objects.create(
            user=user,
            role=role,
            assigned_by=actor,
            reason=reason,
            expires_at=expires_at,
        )
    record_security_event(
        SecurityAuditEvent.ROLE_ASSIGNED,
        user=user,
        actor=actor,
        request=request,
        metadata={
            "role": role.key,
            "reason": reason,
            "expires_at": expires_at.isoformat() if expires_at else None,
        },
    )
    return assignment


@transaction.atomic
def revoke_platform_role(
    assignment,
    *,
    actor,
    reason="",
    request=None,
):
    assignment = (
        RoleAssignment.objects.select_for_update()
        .select_related("user", "role")
        .get(id=assignment.id)
    )
    if assignment.revoked_at is None:
        assignment.revoked_at = timezone.now()
        assignment.revoked_by = actor
        if reason:
            assignment.reason = reason
        assignment.save(
            update_fields=[
                "revoked_at",
                "revoked_by",
                "reason",
            ]
        )
        record_security_event(
            SecurityAuditEvent.ROLE_REVOKED,
            user=assignment.user,
            actor=actor,
            request=request,
            metadata={
                "role": assignment.role.key,
                "reason": reason,
            },
        )
    return assignment


def password_reset_url_for_user(user):
    """Build the public frontend URL that collects the new password."""
    parts = urlsplit(settings.PASSWORD_RESET_FRONTEND_URL)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))
    query.update(
        {
            "reset_uid": urlsafe_base64_encode(force_bytes(user.pk)),
            "reset_token": default_token_generator.make_token(user),
        }
    )
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


def send_password_reset_email(user):
    """Send a reset email without exposing account existence to API clients."""
    reset_url = password_reset_url_for_user(user)
    message = (
        "برای تعیین کلمه عبور جدید Pharmexa، از پیوند زیر استفاده کنید:\n\n"
        f"{reset_url}\n\n"
        f"این پیوند تا {settings.PASSWORD_RESET_TIMEOUT // 3600} ساعت معتبر است و "
        "بعد از استفاده یا تغییر کلمه عبور نامعتبر می‌شود. اگر این درخواست را شما ثبت نکرده‌اید، "
        "می‌توانید این ایمیل را نادیده بگیرید."
    )
    send_mail(
        subject="Pharmexa password reset",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return reset_url


def user_from_reset_uid(uidb64):
    try:
        return get_user_model().objects.get(
            pk=force_str(urlsafe_base64_decode(uidb64))
        )
    except (TypeError, ValueError, OverflowError, UnicodeDecodeError):
        return None
    except get_user_model().DoesNotExist:
        return None


def send_password_reset_emails_for_email(email):
    """Queue delivery for matching active accounts and return no account details.

    Delivery is handed to the queue so a slow or failing mail host cannot stall
    the request. If the broker itself is unreachable the send falls back to the
    request thread rather than silently dropping a reset the user asked for.
    """
    from apps.core.queue import enqueue

    from .tasks import send_password_reset_email_task

    users = get_user_model().objects.filter(email__iexact=email, is_active=True)
    for user in users:
        if not user.has_usable_password():
            continue
        if settings.ASYNC_EMAIL_ENABLED:
            try:
                enqueue(send_password_reset_email_task, user.pk)
                continue
            except Exception:
                logger.warning(
                    "Could not queue password-reset email for user_id=%s; sending inline.",
                    user.pk,
                    exc_info=True,
                )
        try:
            send_password_reset_email(user)
        except Exception:
            logger.exception("Password-reset email delivery failed for user_id=%s", user.pk)
