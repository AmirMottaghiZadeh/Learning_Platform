from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import Profile


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email", "password", "password_confirm"]

    def validate_email(self, value):
        email = value.strip().lower()
        if not email:
            raise serializers.ValidationError("ایمیل الزامی است.")
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("این ایمیل قبلاً ثبت شده است.")
        return email

    def validate_username(self, value):
        username = value.strip()
        if not username:
            raise serializers.ValidationError("نام کاربری الزامی است.")
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("این نام کاربری قبلاً ثبت شده است.")
        return username

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "تکرار کلمه عبور یکسان نیست."})
        if not attrs.get("first_name", "").strip():
            raise serializers.ValidationError({"first_name": "نام الزامی است."})
        if not attrs.get("last_name", "").strip():
            raise serializers.ValidationError({"last_name": "نام خانوادگی الزامی است."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["first_name"].strip(),
            last_name=validated_data["last_name"].strip(),
        )
        Profile.objects.update_or_create(
            user=user,
            defaults={
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
        )
        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "username", "email"]


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AuthTokenResponseSerializer(serializers.Serializer):
    user = UserSerializer()
    token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    uid = serializers.CharField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password_confirm = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "تکرار کلمه عبور یکسان نیست."}
            )
        validate_password(attrs["new_password"])
        return attrs


class PasswordResetResponseSerializer(serializers.Serializer):
    message = serializers.CharField()
