from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.db import transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    LearnerProfile,
    Role,
    RoleAssignment,
    SecurityAuditEvent,
    UserSession,
)
from .services import active_role_keys, ensure_default_learner_role


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=12)
    password_confirm = serializers.CharField(write_only=True, min_length=12)
    name = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "name", "email", "password", "password_confirm"]

    def validate_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError("ایمیل الزامی است.")
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return email

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "تکرار کلمه عبور یکسان نیست."})
        name = attrs.pop("name", "").strip()
        if not name:
            raise serializers.ValidationError({"name": "نام الزامی است."})
        parts = name.strip().split(" ", 1)
        attrs["first_name"] = parts[0]
        attrs["last_name"] = parts[1] if len(parts) > 1 else ""
        if not attrs.get("username"):
            attrs["username"] = attrs.get("email", "").split("@")[0]
        attrs["username"] = attrs["username"].strip()
        if not attrs["username"]:
            raise serializers.ValidationError({"name": "نام کاربری نمی‌تواند خالی باشد."})
        if User.objects.filter(username__iexact=attrs["username"]).exists():
            raise serializers.ValidationError({"name": "این نام کاربری قبلاً ثبت شده است."})
        prospective_user = User(
            username=attrs["username"],
            email=attrs["email"],
            first_name=attrs["first_name"],
            last_name=attrs["last_name"],
        )
        validate_password(attrs["password"], user=prospective_user)
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"].strip(),
            last_name=validated_data["last_name"].strip(),
        )
        ensure_default_learner_role(user)
        return user


class LearnerProfileSerializer(serializers.ModelSerializer):
    is_onboarded = serializers.BooleanField(read_only=True)

    class Meta:
        model = LearnerProfile
        fields = [
            "display_name",
            "study_field",
            "study_goal",
            "study_level",
            "language",
            "onboarded_at",
            "is_onboarded",
        ]
        read_only_fields = ["onboarded_at", "is_onboarded"]


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    profile = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "first_name",
            "last_name",
            "username",
            "email",
            "roles",
            "profile",
        ]

    def get_roles(self, obj) -> list[str]:
        return sorted(set(active_role_keys(obj)))

    @extend_schema_field(LearnerProfileSerializer)
    def get_profile(self, obj):
        profile, _ = LearnerProfile.objects.get_or_create(
            user=obj,
            defaults={"display_name": obj.get_full_name() or obj.username},
        )
        return LearnerProfileSerializer(profile).data


class OnboardingSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    study_field = serializers.ChoiceField(choices=LearnerProfile.FIELD_CHOICES)
    study_goal = serializers.ChoiceField(choices=LearnerProfile.GOAL_CHOICES)
    study_level = serializers.ChoiceField(choices=LearnerProfile.LEVEL_CHOICES)
    language = serializers.ChoiceField(choices=["fa", "en"], required=False)

    def save(self, **kwargs):
        user = self.context["request"].user
        profile, _ = LearnerProfile.objects.get_or_create(user=user)
        data = self.validated_data
        profile.study_field = data["study_field"]
        profile.study_goal = data["study_goal"]
        profile.study_level = data["study_level"]
        if data.get("display_name"):
            profile.display_name = data["display_name"]
        elif not profile.display_name:
            profile.display_name = user.get_full_name() or user.username
        if data.get("language"):
            profile.language = data["language"]
        if profile.onboarded_at is None:
            profile.onboarded_at = timezone.now()
        profile.save()
        return profile


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    device_name = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=120,
    )


class AuthTokenResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    token_type = serializers.CharField()
    access_expires_at = serializers.DateTimeField()
    refresh_expires_at = serializers.DateTimeField()
    session_id = serializers.UUIDField()


class RefreshSessionSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class SessionSerializer(serializers.ModelSerializer):
    current = serializers.SerializerMethodField()

    class Meta:
        model = UserSession
        fields = [
            "id",
            "device_name",
            "ip_address",
            "user_agent",
            "created_at",
            "last_used_at",
            "access_expires_at",
            "refresh_expires_at",
            "revoked_at",
            "current",
        ]

    def get_current(self, obj) -> bool:
        current_session_id = self.context.get("current_session_id")
        return bool(current_session_id and obj.id == current_session_id)


class SessionRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=120,
    )


class StepUpSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = ["key", "name", "description"]


class RoleAssignmentSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.key", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)

    class Meta:
        model = RoleAssignment
        fields = [
            "id",
            "user_id",
            "username",
            "role",
            "reason",
            "created_at",
            "expires_at",
            "revoked_at",
        ]


class RoleAssignmentCreateSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    role = serializers.SlugRelatedField(
        slug_field="key",
        queryset=Role.objects.all(),
    )
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )
    expires_at = serializers.DateTimeField(required=False, allow_null=True)

    def validate_user_id(self, value):
        if not User.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError("Active user was not found.")
        return value

    def validate_expires_at(self, value):
        if value is not None and value <= timezone.now():
            raise serializers.ValidationError(
                "Role expiry must be in the future."
            )
        return value


class RoleAssignmentRevokeSerializer(serializers.Serializer):
    reason = serializers.CharField(
        required=False,
        allow_blank=True,
        max_length=255,
    )


class SecurityAuditEventSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    actor_username = serializers.CharField(
        source="actor.username",
        read_only=True,
    )

    class Meta:
        model = SecurityAuditEvent
        fields = [
            "id",
            "event_type",
            "user_id",
            "username",
            "actor_id",
            "actor_username",
            "session_id",
            "request_id",
            "ip_address",
            "user_agent",
            "metadata",
            "occurred_at",
        ]


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=12)
    new_password_confirm = serializers.CharField(write_only=True, min_length=12)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "تکرار کلمه عبور یکسان نیست."}
            )
        validate_password(attrs["new_password"], user=self.context.get("user"))
        return attrs


class PasswordResetResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
