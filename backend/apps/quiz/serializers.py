from rest_framework import serializers

from .models import COUNT_CHOICES, CATEGORY_CHOICES, QuizQuestion, QuizSession


class QuizStartSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=CATEGORY_CHOICES)
    count = serializers.ChoiceField(choices=COUNT_CHOICES, default=10)


class QuizQuestionSerializer(serializers.ModelSerializer):
    """The learner-facing shape: no `correct_index`."""

    class Meta:
        model = QuizQuestion
        fields = ["id", "order", "prompt_fa", "prompt_en", "options_fa", "options_en"]


class QuizSessionSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizSession
        fields = ["id", "category", "question_count", "questions"]


class QuizAnswerInSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_index = serializers.IntegerField(min_value=0, max_value=3)
    client_answered_at = serializers.DateTimeField(required=False)


class QuizAnswerOutSerializer(serializers.Serializer):
    correct = serializers.BooleanField()
    correct_index = serializers.IntegerField()


class QuizResultSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    total = serializers.IntegerField()
    mistakes_added = serializers.IntegerField()
