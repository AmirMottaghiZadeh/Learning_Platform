from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import (
    AuthTokenResponseSerializer,
    LoginSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetRequestSerializer,
    PasswordResetResponseSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import (
    issue_auth_token,
    send_password_reset_emails_for_email,
    user_from_reset_uid,
)


class RegisterView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_register"

    @extend_schema(request=RegisterSerializer, responses={201: AuthTokenResponseSerializer})
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = issue_auth_token(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_login"

    @extend_schema(request=LoginSerializer, responses=AuthTokenResponseSerializer)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        username = serializer.validated_data["username"]
        password = serializer.validated_data["password"]

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        token = issue_auth_token(user)

        return Response(
            {
                "user": UserSerializer(user).data,
                "token": token.key,
            }
        )


class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_password_reset_request"

    @extend_schema(request=PasswordResetRequestSerializer, responses={200: PasswordResetResponseSerializer})
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"].strip().lower()
        send_password_reset_emails_for_email(email)
        return Response(
            {
                "message": "اگر این ایمیل در Pharmexa ثبت شده باشد، پیوند بازیابی کلمه عبور برای آن ارسال می‌شود.",
            }
        )


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]
    throttle_scope = "auth_password_reset_confirm"

    @extend_schema(request=PasswordResetConfirmSerializer, responses={200: PasswordResetResponseSerializer})
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = user_from_reset_uid(serializer.validated_data["uid"])
        token = serializer.validated_data["token"]
        if not user or not default_token_generator.check_token(user, token):
            return Response(
                {"detail": "This password-reset link is invalid or has expired."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        Token.objects.filter(user=user).delete()
        return Response(
            {"message": "کلمه عبور با موفقیت تغییر کرد. لطفاً دوباره وارد شوید."}
        )


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None, responses={204: None})
    def post(self, request):
        request.user.auth_token.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)
