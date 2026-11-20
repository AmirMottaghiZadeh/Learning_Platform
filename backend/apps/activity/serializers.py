from rest_framework import serializers

from .services import APP_SECTIONS, SITE_SECTIONS


class ActivityEventSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    section = serializers.ChoiceField(choices=list(APP_SECTIONS))
    action = serializers.ChoiceField(choices=["view", "engagement", "click"])
    x = serializers.IntegerField(min_value=0, max_value=100, required=False)
    y = serializers.IntegerField(min_value=0, max_value=100, required=False)
    area = serializers.ChoiceField(choices=["screen", "article"], default="screen")
    viewport = serializers.ChoiceField(choices=["mobile", "tablet", "desktop"], default="mobile")
    duration_seconds = serializers.IntegerField(default=0, min_value=0, max_value=120)

    def validate(self, attrs):
        if attrs["action"] == "click" and ("x" not in attrs or "y" not in attrs):
            raise serializers.ValidationError("مختصات نسبی کلیک الزامی است.")
        if attrs["action"] != "engagement":
            attrs["duration_seconds"] = 0
        return attrs


class EventBatchSerializer(serializers.Serializer):
    events = ActivityEventSerializer(many=True, max_length=100, allow_empty=False)


class SiteClickSerializer(ActivityEventSerializer):
    section = serializers.ChoiceField(choices=list(SITE_SECTIONS))
    action = serializers.ChoiceField(choices=["click", "engagement"])


class SiteClickBatchSerializer(serializers.Serializer):
    events = SiteClickSerializer(many=True, max_length=20, allow_empty=False)


class ActivityReceiptSerializer(serializers.Serializer):
    accepted = serializers.IntegerField()
