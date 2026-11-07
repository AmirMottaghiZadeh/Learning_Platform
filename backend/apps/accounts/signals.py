"""Track Django website/admin logins alongside app token sessions."""

from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone

from .models import UserSession
from .services import SessionLimitError, issue_user_session, revoke_user_session


@receiver(user_logged_in, dispatch_uid="accounts.track_browser_login")
def browser_signed_in(sender, request, user, **kwargs):
    surface = "manage" if request.path.startswith(("/manage/", "/admin/")) else "site"
    prior_id = request.session.get("tracked_session_id")
    if prior_id:
        prior = UserSession.objects.filter(pk=prior_id, user=user, revoked_at=None, refresh_expires_at__gt=timezone.now()).first()
        if prior:
            # Reauthentication of the same Django cookie is the same device,
            # including when Django has just cycled its session key.
            from .devices import touch_session

            prior.django_session_key = request.session.session_key or ""
            prior.surface = surface
            prior.save(update_fields=["django_session_key", "surface"])
            touch_session(prior, request, force=True)
            return
    try:
        issued = issue_user_session(user, request=request, surface=surface)
    except SessionLimitError as exc:
        # Authentication has already set the Django cookie by the time this
        # signal runs. The middleware flushes it before sending any response.
        request.session["device_limit_error"] = exc.message
        return
    session = issued.session
    session.django_session_key = request.session.session_key or ""
    session.save(update_fields=["django_session_key"])
    request.session["tracked_session_id"] = str(session.pk)


@receiver(user_logged_out, dispatch_uid="accounts.track_browser_logout")
def browser_signed_out(sender, request, user, **kwargs):
    if request is None:
        return
    session = UserSession.objects.filter(pk=request.session.get("tracked_session_id")).first() if request.session.get("tracked_session_id") else None
    if session:
        revoke_user_session(session, request=request, actor=user, reason="browser_logout")
