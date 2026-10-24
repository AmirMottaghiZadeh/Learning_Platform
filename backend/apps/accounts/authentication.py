from datetime import timedelta

from django.utils import timezone
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.exceptions import AuthenticationFailed

from .models import UserSession
from .services import hash_session_token


class SessionTokenAuthentication(BaseAuthentication):
    keyword = "Bearer"

    def authenticate(self, request):
        authorization = get_authorization_header(request).split()
        if not authorization:
            return None
        if authorization[0].decode("ascii", errors="ignore") != self.keyword:
            return None
        if len(authorization) != 2:
            raise AuthenticationFailed("Invalid authorization header.")

        try:
            token = authorization[1].decode("ascii")
        except UnicodeError as exc:
            raise AuthenticationFailed("Invalid access token.") from exc

        token_hash = hash_session_token(token)
        session = (
            UserSession.objects.select_related("user")
            .filter(access_token_hash=token_hash)
            .first()
        )
        now = timezone.now()
        if not session:
            raise AuthenticationFailed("Invalid access token.")
        if session.revoked_at is not None:
            raise AuthenticationFailed("This session has been revoked.")
        if session.access_expires_at <= now:
            raise AuthenticationFailed("Access token has expired.")
        if session.refresh_expires_at <= now:
            raise AuthenticationFailed("This session has expired.")
        if not session.user.is_active:
            raise AuthenticationFailed("This account is inactive.")

        if session.last_used_at <= now - timedelta(minutes=1):
            UserSession.objects.filter(
                id=session.id,
                revoked_at__isnull=True,
            ).update(
                last_used_at=now,
                ip_address=request.META.get("REMOTE_ADDR") or session.ip_address,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:255]
                or session.user_agent,
            )
            session.last_used_at = now

        return session.user, session

    def authenticate_header(self, request):
        return self.keyword


class SessionTokenAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = SessionTokenAuthentication
    name = "bearerAuth"

    def get_security_definition(self, auto_schema):
        return {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "Opaque access token",
        }
