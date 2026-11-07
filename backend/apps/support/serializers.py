from rest_framework import serializers
from .models import Conversation, Message


class ConversationSerializer(serializers.ModelSerializer):
    unread = serializers.IntegerField(read_only=True, default=0)

    class Meta:
        model = Conversation
        fields = ["id", "subject", "kind", "status", "unread", "user_read_id", "staff_read_id", "updated_at"]


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ["id", "client_id", "text", "from_staff", "created_at"]


class MessagePageSerializer(serializers.Serializer):
    messages = MessageSerializer(many=True)
    has_older = serializers.BooleanField()
    user_read_id = serializers.IntegerField()
    staff_read_id = serializers.IntegerField()


class SupportSummarySerializer(serializers.Serializer):
    unread = serializers.IntegerField()
    web_push_public_key = serializers.CharField()
    web_push_configured = serializers.BooleanField()


class SubscriptionResponseSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()


class SendSerializer(serializers.Serializer):
    client_id = serializers.UUIDField()
    text = serializers.CharField(max_length=4000, trim_whitespace=True, allow_blank=False)


class ReadSerializer(serializers.Serializer):
    through = serializers.IntegerField(min_value=0)


class ConversationCreateSerializer(serializers.Serializer):
    subject = serializers.CharField(max_length=120, required=False, allow_blank=True)


class SubscriptionSerializer(serializers.Serializer):
    device_id = serializers.RegexField(r"^[A-Za-z0-9_-]{16,64}$")
    platform = serializers.ChoiceField(choices=["android", "web"])
    enabled = serializers.BooleanField(default=True)
    expo_token = serializers.RegexField(r"^(?:ExponentPushToken|ExpoPushToken)\[[A-Za-z0-9_-]+\]$", required=False)
    web_subscription = serializers.JSONField(required=False)

    def validate(self, attrs):
        from .notifications import validate_web_subscription

        if attrs["enabled"]:
            if attrs["platform"] == "android" and not attrs.get("expo_token"):
                raise serializers.ValidationError("توکن اعلان اندروید الزامی است.")
            if attrs["platform"] == "web":
                try:
                    validate_web_subscription(attrs.get("web_subscription", {}))
                except ValueError as exc:
                    raise serializers.ValidationError(str(exc))
                subscription = attrs["web_subscription"]
                attrs["web_subscription"] = {"endpoint": subscription["endpoint"], "keys": {key: subscription["keys"][key] for key in ["p256dh", "auth"]}}
        return attrs
