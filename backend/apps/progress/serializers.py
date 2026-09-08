from rest_framework import serializers

from .models import Mistake, StudyPlan


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

    class Meta:
        model = StudyPlan
        fields = ["days", "reminders_enabled", "updated_at"]
        read_only_fields = ["updated_at"]
