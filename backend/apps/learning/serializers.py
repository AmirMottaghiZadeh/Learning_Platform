from rest_framework import serializers

from .models import LearnerProgress


class LearnerProgressSerializer(serializers.ModelSerializer):
    topic_key = serializers.CharField(source="topic.key")
    topic_label = serializers.CharField(source="topic.label")
    accuracy_percent = serializers.IntegerField(read_only=True)

    class Meta:
        model = LearnerProgress
        fields = [
            "id",
            "product_id",
            "topic_key",
            "topic_label",
            "questions_answered",
            "correct_answers",
            "wrong_answers",
            "timed_out_answers",
            "accuracy_percent",
            "xp",
            "review_count",
            "mistake_count",
            "mastery_state",
            "last_activity_at",
        ]


class WeakTopicSerializer(serializers.Serializer):
    topic_key = serializers.CharField()
    topic_label = serializers.CharField()
    questions_answered = serializers.IntegerField()
    accuracy_percent = serializers.IntegerField()
    wrong_answers = serializers.IntegerField()
    review_count = serializers.IntegerField()
    mistake_count = serializers.IntegerField()
    due_flashcards = serializers.IntegerField()
    xp = serializers.IntegerField()
    mastery_state = serializers.CharField()


class LearningProgressSummarySerializer(serializers.Serializer):
    product_id = serializers.CharField(allow_null=True)
    questions_answered = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    accuracy_percent = serializers.IntegerField()
    xp = serializers.IntegerField()
    review_count = serializers.IntegerField()
    mistake_count = serializers.IntegerField()
    due_flashcards = serializers.IntegerField()
    active_flashcards = serializers.IntegerField()
    current_streak = serializers.IntegerField()
    weak_topics = WeakTopicSerializer(many=True)


class RecommendationSerializer(serializers.Serializer):
    id = serializers.CharField()
    priority = serializers.IntegerField()
    action = serializers.CharField()
    title = serializers.CharField()
    reason = serializers.CharField()
    topic_key = serializers.CharField(allow_blank=True, allow_null=True)
    count = serializers.IntegerField()


class LeagueSummarySerializer(serializers.Serializer):
    season_key = serializers.CharField()
    rank = serializers.IntegerField(allow_null=True)
    total_participants = serializers.IntegerField()


class LearningDashboardSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    summary = LearningProgressSummarySerializer()
    recommendations = RecommendationSerializer(many=True)
    league = LeagueSummarySerializer()


class DailyActivitySerializer(serializers.Serializer):
    date = serializers.DateField()
    questions_answered = serializers.IntegerField()
    reviews_completed = serializers.IntegerField()
    mistakes_created = serializers.IntegerField()
    xp = serializers.IntegerField()


class LearningStatisticsSerializer(serializers.Serializer):
    product_id = serializers.CharField()
    days = serializers.IntegerField()
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    summary = LearningProgressSummarySerializer()
    topics = LearnerProgressSerializer(many=True)
    daily_activity = DailyActivitySerializer(many=True)
    weak_topics = WeakTopicSerializer(many=True)
