from django.utils import timezone
from rest_framework import serializers

from apps.drugs.data.atc_reference import ATC_L1
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
            "mode", "topic_keys", "atc_groups", "daily_minutes", "deadline",
            "days", "reminders_enabled", "updated_at",
        ]
        read_only_fields = ["updated_at", "atc_groups"]

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
    # Set by planning.today_items; an item serialized elsewhere falls back
    # to its reason.
    title_fa = serializers.SerializerMethodField()
    title_en = serializers.SerializerMethodField()

    class Meta:
        model = StudyPlanItem
        fields = [
            "id", "day", "order", "activity_type", "topic_key", "atc_code",
            "estimated_minutes", "status", "reason_fa", "reason_en", "completed_at",
            "title_fa", "title_en",
        ]
        read_only_fields = fields

    def get_title_fa(self, item):
        return getattr(item, "title_fa", "") or item.reason_fa

    def get_title_en(self, item):
        return getattr(item, "title_en", "") or item.reason_en


class AtcGroupSerializer(serializers.Serializer):
    code = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()


class AtcPlanConfigSerializer(serializers.Serializer):
    atc_groups = serializers.ListField(child=serializers.ChoiceField(choices=list(ATC_L1)), min_length=1, max_length=len(ATC_L1))
    days = serializers.ListField(child=serializers.BooleanField(), min_length=7, max_length=7)
    daily_minutes = serializers.IntegerField(min_value=15, max_value=240)
    deadline = serializers.DateField(required=False, default=None, allow_null=True)

    def validate_atc_groups(self, value):
        return list(dict.fromkeys(value))

    def validate_days(self, value):
        if not any(value):
            raise serializers.ValidationError("دست‌کم یک روز مطالعه انتخاب کنید.")
        return value

    def validate_deadline(self, value):
        if value is not None and value <= timezone.localdate():
            raise serializers.ValidationError("تاریخ آزمون باید بعد از امروز باشد.")
        return value


class AtcFirstActivitySerializer(serializers.Serializer):
    atc_code = serializers.CharField()
    activity_type = serializers.ChoiceField(choices=[StudyPlanItem.LESSON, StudyPlanItem.QUIZ])
    day = serializers.DateField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()


class AtcPlanPreviewSerializer(serializers.Serializer):
    fits_deadline = serializers.BooleanField()
    chapter_count = serializers.IntegerField()
    missing_quiz_count = serializers.IntegerField()
    remaining_minutes = serializers.IntegerField()
    study_sessions = serializers.IntegerField()
    first_activity = AtcFirstActivitySerializer(allow_null=True)
    first_lesson = AtcFirstActivitySerializer(allow_null=True)
    estimated_finish = serializers.DateField(allow_null=True)
    empty_groups = serializers.ListField(child=serializers.CharField())


class PlanChapterSerializer(serializers.Serializer):
    quiz_day = serializers.DateField(allow_null=True)
    quiz_status = serializers.ChoiceField(choices=["done", "scheduled", "unavailable"])
    flashcard_status = serializers.ChoiceField(choices=["coming_soon"])
    flashcard_after = serializers.ChoiceField(choices=["quiz"])


class PlanTopicSerializer(serializers.Serializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    progress_pct = serializers.IntegerField()
    mastery_pct = serializers.IntegerField()


class PlanSummarySerializer(serializers.Serializer):
    daily_minutes = serializers.IntegerField()
    study_days = serializers.IntegerField()
    deadline = serializers.DateField(allow_null=True)
    days_left = serializers.IntegerField(allow_null=True)
    week_index = serializers.IntegerField(allow_null=True)
    week_count = serializers.IntegerField(allow_null=True)
    progress_pct = serializers.IntegerField(allow_null=True)


class PlanDaySerializer(serializers.Serializer):
    date = serializers.DateField()
    study_day = serializers.BooleanField()
    state = serializers.ChoiceField(choices=["done", "missed", "today", "planned", "free", "off"])


class PlanTodaySerializer(serializers.Serializer):
    mode = serializers.CharField()
    items = StudyPlanItemSerializer(many=True)
    total_minutes = serializers.IntegerField()
    topics = PlanTopicSerializer(many=True)
    summary = PlanSummarySerializer()
    week = PlanDaySerializer(many=True)


class StudyPlanSaveResponseSerializer(serializers.Serializer):
    """Schema-only: the PUT response is the plan's own fields plus whether
    the newly generated schedule fits before the deadline."""

    mode = serializers.CharField()
    topic_keys = serializers.ListField(child=serializers.CharField())
    atc_groups = serializers.ListField(child=serializers.CharField())
    daily_minutes = serializers.IntegerField()
    deadline = serializers.DateField(allow_null=True)
    days = serializers.ListField(child=serializers.BooleanField())
    reminders_enabled = serializers.BooleanField()
    updated_at = serializers.DateTimeField()
    fits_deadline = serializers.BooleanField()
