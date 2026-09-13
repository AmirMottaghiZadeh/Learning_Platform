from django.utils import timezone
from rest_framework import serializers

from apps.lessons.data.study_topics import STUDY_TOPICS

from .models import Mistake, StudyPlan, StudyPlanItem

_TOPIC_KEYS = {t["key"] for t in STUDY_TOPICS}


class NextChapterSerializer(serializers.Serializer):
    code = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    group_code = serializers.CharField()
    group_name_fa = serializers.CharField()
    group_name_en = serializers.CharField()


class FocusRowSerializer(serializers.Serializer):
    kind = serializers.CharField()
    title_fa = serializers.CharField()
    title_en = serializers.CharField()
    sub_fa = serializers.CharField()
    sub_en = serializers.CharField()
    minutes = serializers.IntegerField()
    count = serializers.IntegerField(required=False)
    mistake_id = serializers.IntegerField(required=False)
    atc_code = serializers.CharField(required=False)


class FocusSessionSerializer(serializers.Serializer):
    rows = FocusRowSerializer(many=True)
    total_minutes = serializers.IntegerField()


class DashboardSerializer(serializers.Serializer):
    greeting_name = serializers.CharField()
    streak_days = serializers.IntegerField()
    xp = serializers.IntegerField()
    next_chapter = NextChapterSerializer(allow_null=True)
    focus_session = FocusSessionSerializer()


class StatisticsSerializer(serializers.Serializer):
    week_bars = serializers.ListField(child=serializers.IntegerField())
    accuracy_pct = serializers.IntegerField()
    quizzes = serializers.IntegerField()
    reviews = serializers.IntegerField()
    minutes = serializers.IntegerField()
    mastery_pct = serializers.IntegerField()


class MistakeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Mistake
        fields = [
            "id", "topic_key", "topic_fa", "topic_en",
            "detail_fa", "detail_en", "count", "resolved", "last_seen",
        ]


class StudyPlanSerializer(serializers.ModelSerializer):
    days = serializers.ListField(
        child=serializers.BooleanField(), min_length=7, max_length=7
    )
    topic_keys = serializers.ListField(child=serializers.CharField(), default=list)

    class Meta:
        model = StudyPlan
        fields = [
            "mode", "topic_keys", "daily_minutes", "deadline",
            "days", "reminders_enabled", "updated_at",
        ]
        read_only_fields = ["updated_at"]

    def validate_topic_keys(self, value):
        unknown = [key for key in value if key not in _TOPIC_KEYS]
        if unknown:
            raise serializers.ValidationError(f"موضوع(های) نامعتبر: {', '.join(unknown)}")
        return value

    def validate_daily_minutes(self, value):
        if not 5 <= value <= 240:
            raise serializers.ValidationError("زمان روزانه باید بین ۵ تا ۲۴۰ دقیقه باشد.")
        return value

    def validate(self, attrs):
        mode = attrs.get("mode", getattr(self.instance, "mode", StudyPlan.MODE_NONE))
        if mode == StudyPlan.MODE_GOAL:
            if not attrs.get("topic_keys", getattr(self.instance, "topic_keys", [])):
                raise serializers.ValidationError(
                    {"topic_keys": "برای مسیر هدف‌محور حداقل یک موضوع لازم است."}
                )
            deadline = attrs.get("deadline", getattr(self.instance, "deadline", None))
            if not deadline:
                raise serializers.ValidationError({"deadline": "ددلاین الزامی است."})
            if deadline <= timezone.localdate():
                raise serializers.ValidationError({"deadline": "ددلاین باید در آینده باشد."})
        return attrs


class StudyPlanItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyPlanItem
        fields = [
            "id", "day", "order", "activity_type", "topic_key", "atc_code",
            "estimated_minutes", "status", "reason_fa", "reason_en", "completed_at",
        ]
        read_only_fields = fields


class PlanTopicSerializer(serializers.Serializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    progress_pct = serializers.IntegerField()
    mastery_pct = serializers.IntegerField()


class PlanTodaySerializer(serializers.Serializer):
    mode = serializers.CharField()
    items = StudyPlanItemSerializer(many=True)
    total_minutes = serializers.IntegerField()
    topics = PlanTopicSerializer(many=True)


class StudyPlanSaveResponseSerializer(serializers.Serializer):
    """Schema-only: the PUT response is the plan's own fields plus whether
    the newly generated schedule fits before the deadline."""

    mode = serializers.CharField()
    topic_keys = serializers.ListField(child=serializers.CharField())
    daily_minutes = serializers.IntegerField()
    deadline = serializers.DateField(allow_null=True)
    days = serializers.ListField(child=serializers.BooleanField())
    reminders_enabled = serializers.BooleanField()
    updated_at = serializers.DateTimeField()
    fits_deadline = serializers.BooleanField()
