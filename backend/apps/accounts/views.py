from django.conf import settings
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from . import otp
from .models import LearnerProfile, OneTimeCode, Role, RoleAssignment, SecurityAuditEvent, UserSession
from .permissions import (
    CanManagePlatformRoles,
    CanViewSecurityAudit,
    HasRecentStepUp,
)
from .serializers import (
    AuthTokenResponseSerializer,
    LoginSerializer,
    OtpRequestResponseSerializer,
    OtpRequestSerializer,
    OtpVerifySerializer,
    PasswordResetConfirmSerializer,
    PasswordSetSerializer,
    PasswordResetRequestSerializer,
    PasswordResetResponseSerializer,
    RefreshSessionSerializer,
    RegisterSerializer,
    RoleAssignmentCreateSerializer,
    RoleAssignmentRevokeSerializer,
    RoleAssignmentSerializer,
    RoleSerializer,
    LearnerProfileSerializer,
    OnboardingSerializer,
    SecurityAuditEventSerializer,
    SessionRevokeSerializer,
    SessionSerializer,
    StepUpSerializer,
    UserSerializer,
)
from .services import (
    SessionTokenError,
    assign_platform_role,
    issue_user_session,
    record_security_event,
    revoke_all_user_sessions,
    revoke_platform_role,
    revoke_user_session,
    rotate_refresh_token,
    send_password_reset_emails_for_email,
    session_has_recent_step_up,
    user_from_reset_uid,
    verify_session_step_up,
)


User = get_user_model()


def _session_response(issued_session):
    session = issued_session.session
    return {
        "user": UserSerializer(session.user).data,
        "access_token": issued_session.access_token,
        "refresh_token": issued_session.refresh_token,
        "token_type": "Bearer",
        "access_expires_at": session.access_expires_at,
        "refresh_expires_at": session.refresh_expires_at,
        "session_id": session.id,
    }


class RegisterView(APIView):
    """Email sign-up -- closed unless AUTH_EMAIL_REGISTRATION_ENABLED: new
    accounts sign up with a mobile number (OtpRequestView/OtpVerifyView)."""

    permission_classes = [AllowAny]
    throttle_scope = "auth_register"

    @extend_schema(
        request=RegisterSerializer,
        responses={201: AuthTokenResponseSerializer},
    )
    def post(self, request):
        if not settings.AUTH_EMAIL_REGISTRATION_ENABLED:
            raise PlatformAPIError(
                "ثبت‌نام با ایمیل بسته است؛ با شمارهٔ موبایل ثبت‌نام کن.",
                code="EMAIL_REGISTRATION_CLOSED",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        issued_session = issue_user_session(
            user,
            request=request,
            device_name=request.data.get("device_name", ""),
        )
        return Response(
            _session_response(issued_session),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_login"

    @extend_schema(
        request=LoginSerializer,
        responses=AuthTokenResponseSerializer,
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        user = authenticate(
            username=username,
            password=serializer.validated_data["password"],
        )
        if not user:
            record_security_event(
                SecurityAuditEvent.LOGIN_FAILED,
                request=request,
                metadata={"username": username[:150]},
            )
            raise PlatformAPIError(
                "Invalid username or password.",
                code="INVALID_CREDENTIALS",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        issued_session = issue_user_session(
            user,
            request=request,
            device_name=serializer.validated_data.get("device_name", ""),
        )
        return Response(_session_response(issued_session))


def _otp_error(exc):
    return PlatformAPIError(str(exc), code=exc.code, details=exc.details, status_code=exc.status)


class OtpRequestView(APIView):
    """Sends an SMS code: `purpose` "signup" for a new number (or one whose
    sign-up was never finished with a password), "reset" for a forgotten
    password."""

    permission_classes = [AllowAny]
    throttle_scope = "auth_otp_request"

    @extend_schema(request=OtpRequestSerializer, responses=OtpRequestResponseSerializer)
    def post(self, request):
        serializer = OtpRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        phone = serializer.validated_data["phone"]
        try:
            otp.request_code(phone, serializer.validated_data["purpose"], request=request)
        except otp.OtpError as exc:
            raise _otp_error(exc) from exc
        return Response({
            "phone": phone,
            "code_length": settings.OTP_CODE_LENGTH,
            "expires_in": settings.OTP_TTL_SECONDS,
            "resend_in": settings.OTP_RESEND_SECONDS,
        })


class OtpVerifyView(APIView):
    """Checks an SMS code and signs the number's account in -- creating it,
    for a sign-up. The session counts as freshly verified, so the app can
    have the user choose a password (PasswordSetView) right away. 201 when
    the account was just created."""

    permission_classes = [AllowAny]
    throttle_scope = "auth_otp_verify"

    @extend_schema(request=OtpVerifySerializer, responses=AuthTokenResponseSerializer)
    def post(self, request):
        serializer = OtpVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        phone, purpose = data["phone"], data["purpose"]
        try:
            otp.verify_code(phone, purpose, data["code"], request=request)
            if purpose == OneTimeCode.SIGNUP:
                user, created = otp.account_for_signup(phone)
            else:
                user, created = otp.user_for_phone(phone), False
        except otp.OtpError as exc:
            raise _otp_error(exc) from exc
        if user is None or not user.is_active:
            raise PlatformAPIError(
                "حسابی با این شماره پیدا نشد.",
                code="PHONE_NOT_REGISTERED",
                status_code=status.HTTP_404_NOT_FOUND,
            )

        issued_session = issue_user_session(user, request=request, device_name=data.get("device_name", ""))
        verify_session_step_up(issued_session.session, request=request)
        record_security_event(
            SecurityAuditEvent.OTP_VERIFIED,
            user=user,
            actor=user,
            session=issued_session.session,
            request=request,
            metadata={"purpose": purpose, "created": created},
        )
        return Response(
            _session_response(issued_session),
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class PasswordSetView(APIView):
    """Chooses or changes the signed-in user's password. No current
    password is asked for when the account has none yet (just signed up)
    or the session proved itself with an SMS code moments ago (a forgotten
    password); otherwise `current_password` must be right. Every other
    signed-in device is signed out."""

    permission_classes = [IsAuthenticated]
    throttle_scope = "auth_password_set"

    @extend_schema(request=PasswordSetSerializer, responses=UserSerializer)
    def post(self, request):
        user = request.user
        serializer = PasswordSetSerializer(data=request.data, context={"user": user})
        serializer.is_valid(raise_exception=True)
        proven = not user.has_usable_password() or session_has_recent_step_up(request.auth)
        if not proven and not user.check_password(serializer.validated_data.get("current_password") or ""):
            record_security_event(
                SecurityAuditEvent.AUTHORIZATION_DENIED,
                user=user,
                actor=user,
                session=request.auth,
                request=request,
                metadata={"reason": "password_set_wrong_current_password"},
            )
            raise PlatformAPIError(
                "رمز عبور فعلی درست نیست.",
                code="INVALID_CURRENT_PASSWORD",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        fields = ["password"]
        name = " ".join((serializer.validated_data.get("name") or "").split())
        if name:
            first, _, last = name.partition(" ")
            user.first_name, user.last_name = first[:150], last[:150]
            fields += ["first_name", "last_name"]
            LearnerProfile.objects.update_or_create(user=user, defaults={"display_name": name[:150]})
        user.save(update_fields=fields)
        others = UserSession.objects.filter(user=user, revoked_at__isnull=True).exclude(id=request.auth.id)
        for other in others:
            revoke_user_session(other, request=request, actor=user, reason="password_set")
        record_security_event(
            SecurityAuditEvent.PASSWORD_SET,
            user=user,
            actor=user,
            session=request.auth,
            request=request,
        )
        return Response(UserSerializer(user).data)


class RefreshSessionView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=RefreshSessionSerializer,
        responses=AuthTokenResponseSerializer,
    )
    def post(self, request):
        serializer = RefreshSessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            issued_session = rotate_refresh_token(
                serializer.validated_data["refresh_token"],
                request=request,
            )
        except SessionTokenError as exc:
            raise PlatformAPIError(
                str(exc),
                code="INVALID_REFRESH_TOKEN",
                status_code=status.HTTP_401_UNAUTHORIZED,
            ) from exc
        return Response(_session_response(issued_session))


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_password_reset_request"

    @extend_schema(
        request=PasswordResetRequestSerializer,
        responses={200: PasswordResetResponseSerializer},
    )
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        send_password_reset_emails_for_email(email)
        return Response(
            {
                "message": "اگر این ایمیل در فارمنتا ثبت شده باشد، پیوند بازیابی کلمه عبور برای آن ارسال می‌شود.",
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_password_reset_confirm"

    @extend_schema(
        request=PasswordResetConfirmSerializer,
        responses={200: PasswordResetResponseSerializer},
    )
    def post(self, request):
        user = user_from_reset_uid(request.data.get("uid"))
        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={"user": user},
        )
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data["token"]
        if not user or not default_token_generator.check_token(user, token):
            raise PlatformAPIError(
                "This password-reset link is invalid or has expired.",
                code="INVALID_PASSWORD_RESET_TOKEN",
                status_code=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        revoke_all_user_sessions(
            user,
            request=request,
            actor=user,
            reason="password_reset",
        )
        record_security_event(
            SecurityAuditEvent.PASSWORD_RESET_COMPLETED,
            user=user,
            actor=user,
            request=request,
        )
        return Response(
            {"message": "کلمه عبور با موفقیت تغییر کرد. لطفاً دوباره وارد شوید."}
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        revoke_user_session(
            request.auth,
            request=request,
            actor=request.user,
            reason="logout",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class LogoutAllView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        revoke_all_user_sessions(
            request.user,
            request=request,
            actor=request.user,
            reason="logout_all",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SessionListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=SessionSerializer(many=True))
    def get(self, request):
        sessions = UserSession.objects.filter(user=request.user).order_by(
            "-last_used_at",
            "-created_at",
        )
        return Response(
            SessionSerializer(
                sessions,
                many=True,
                context={"current_session_id": request.auth.id},
            ).data
        )


class SessionRevokeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=SessionRevokeSerializer, responses={204: None})
    def post(self, request, session_id):
        serializer = SessionRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = UserSession.objects.filter(
            id=session_id,
            user=request.user,
        ).first()
        if not session:
            raise PlatformAPIError(
                "The requested session was not found.",
                code="SESSION_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        revoke_user_session(
            session,
            request=request,
            actor=request.user,
            reason=serializer.validated_data.get("reason") or "device_revoked",
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class StepUpView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=StepUpSerializer, responses={204: None})
    def post(self, request):
        serializer = StepUpSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not request.user.check_password(
            serializer.validated_data["password"]
        ):
            record_security_event(
                SecurityAuditEvent.AUTHORIZATION_DENIED,
                user=request.user,
                actor=request.user,
                session=request.auth,
                request=request,
                metadata={"reason": "step_up_invalid_password"},
            )
            raise PlatformAPIError(
                "Password confirmation failed.",
                code="STEP_UP_FAILED",
                status_code=status.HTTP_403_FORBIDDEN,
            )
        verify_session_step_up(request.auth, request=request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class RoleListView(APIView):
    permission_classes = [CanManagePlatformRoles]

    @extend_schema(responses=RoleSerializer(many=True))
    def get(self, request):
        return Response(RoleSerializer(Role.objects.all(), many=True).data)


class RoleAssignmentListCreateView(APIView):
    def get_permissions(self):
        permission_classes = [CanManagePlatformRoles]
        if self.request.method == "POST":
            permission_classes.append(HasRecentStepUp)
        return [permission() for permission in permission_classes]

    @extend_schema(responses=RoleAssignmentSerializer(many=True))
    def get(self, request):
        assignments = RoleAssignment.objects.select_related(
            "user",
            "role",
        ).order_by("-created_at")
        return Response(
            RoleAssignmentSerializer(assignments[:200], many=True).data
        )

    @extend_schema(
        request=RoleAssignmentCreateSerializer,
        responses={201: RoleAssignmentSerializer},
    )
    def post(self, request):
        serializer = RoleAssignmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = assign_platform_role(
            user=User.objects.get(id=serializer.validated_data["user_id"]),
            role_key=serializer.validated_data["role"].key,
            actor=request.user,
            reason=serializer.validated_data.get("reason", ""),
            expires_at=serializer.validated_data.get("expires_at"),
            request=request,
        )
        return Response(
            RoleAssignmentSerializer(assignment).data,
            status=status.HTTP_201_CREATED,
        )


class RoleAssignmentRevokeView(APIView):
    permission_classes = [CanManagePlatformRoles, HasRecentStepUp]

    @extend_schema(
        request=RoleAssignmentRevokeSerializer,
        responses=RoleAssignmentSerializer,
    )
    def post(self, request, assignment_id):
        serializer = RoleAssignmentRevokeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        assignment = RoleAssignment.objects.filter(id=assignment_id).first()
        if not assignment:
            raise PlatformAPIError(
                "Role assignment was not found.",
                code="ROLE_ASSIGNMENT_NOT_FOUND",
                status_code=status.HTTP_404_NOT_FOUND,
            )
        assignment = revoke_platform_role(
            assignment,
            actor=request.user,
            reason=serializer.validated_data.get("reason", ""),
            request=request,
        )
        return Response(RoleAssignmentSerializer(assignment).data)


class SecurityAuditListView(APIView):
    permission_classes = [CanViewSecurityAudit]

    @extend_schema(responses=SecurityAuditEventSerializer(many=True))
    def get(self, request):
        events = SecurityAuditEvent.objects.select_related(
            "user",
            "actor",
            "session",
        ).order_by("-occurred_at", "-id")[:200]
        return Response(SecurityAuditEventSerializer(events, many=True).data)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)

    @extend_schema(request=LearnerProfileSerializer, responses=UserSerializer)
    def patch(self, request):
        from .models import LearnerProfile

        profile, _ = LearnerProfile.objects.get_or_create(user=request.user)
        serializer = LearnerProfileSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data)


class OnboardingView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=OnboardingSerializer, responses=UserSerializer)
    def post(self, request):
        serializer = OnboardingSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)
