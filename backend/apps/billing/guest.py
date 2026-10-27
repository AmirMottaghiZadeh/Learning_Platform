"""Guest access: while the console's switch is on, the app opens without
signing in -- each visitor gets a throwaway account of their own, already
onboarded, holding only the free plan. Switching it off deactivates every
guest and ends their sessions; delete_guests() then removes them."""

import uuid

from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import LearnerProfile, UserSession
from apps.accounts.serializers import AuthTokenResponseSerializer, UserSerializer
from apps.accounts.services import issue_user_session
from apps.core.exceptions import PlatformAPIError

from . import config
from .models import GuestAccount

User = get_user_model()


def is_guest(user):
    return bool(getattr(user, "is_authenticated", False)) and hasattr(user, "guest_account")


def guests():
    return User.objects.filter(guest_account__isnull=False)


def end_guest_sessions():
    """Deactivate every guest and revoke their sessions (guest access off)."""
    guests().update(is_active=False)
    return UserSession.objects.filter(user__guest_account__isnull=False, revoked_at__isnull=True).update(
        revoked_at=timezone.now(), revoke_reason="guest_access_disabled"
    )


def delete_guests():
    count = guests().count()
    guests().delete()
    return count


@transaction.atomic
def create_guest(request):
    user = User.objects.create(username=f"guest-{uuid.uuid4().hex[:12]}")
    user.set_unusable_password()
    user.save(update_fields=["password"])
    LearnerProfile.objects.create(
        user=user, display_name="مهمان", study_field="pharmacy", study_goal="comprehensive",
        study_level="beginner", onboarded_at=timezone.now(),
    )
    GuestAccount.objects.create(user=user, ip_address=request.META.get("REMOTE_ADDR") or None)
    return user


class GuestStatusView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    @extend_schema(responses=inline_serializer("GuestStatus", {"enabled": serializers.BooleanField()}))
    def get(self, request):
        return Response({"enabled": config.current().guest_access})


class GuestSessionView(APIView):
    """A new guest account and a session for it, while guest access is on."""

    permission_classes = [AllowAny]
    authentication_classes = []
    throttle_scope = "guest_session"

    @extend_schema(request=None, responses={201: AuthTokenResponseSerializer})
    def post(self, request):
        if not config.current().guest_access:
            raise PlatformAPIError("Guest access is off.", code="GUEST_ACCESS_DISABLED", status_code=403)
        user = create_guest(request)
        issued = issue_user_session(user, request=request, device_name="guest")
        session = issued.session
        return Response({
            "user": UserSerializer(user).data,
            "access_token": issued.access_token,
            "refresh_token": issued.refresh_token,
            "token_type": "Bearer",
            "access_expires_at": session.access_expires_at,
            "refresh_expires_at": session.refresh_expires_at,
            "session_id": session.id,
        }, status=201)
