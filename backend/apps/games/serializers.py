from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.games.services.lifecycle_service import (
    QUESTION_TIMER_MAX_SECONDS,
    question_remaining_seconds,
    question_timer_total_seconds,
)
from apps.quizzes.presentation import (
    interaction_type_for,
    option_layout_for,
)

from .models import GameSession, GameQuestion, GameAnswer, Mistake
from .selectors import get_current_question


class GameQuestionSerializer(serializers.ModelSerializer):
    prompt = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    chip = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    interaction_type = serializers.SerializerMethodField()
    option_layout = serializers.SerializerMethodField()
    instruction = serializers.SerializerMethodField()
    timer_base_seconds = serializers.SerializerMethodField()
    timer_extension_seconds = serializers.IntegerField(read_only=True)
    timer_total_seconds = serializers.SerializerMethodField()
    timer_remaining_seconds = serializers.SerializerMethodField()
    timer_extension_available = serializers.SerializerMethodField()

    class Meta:
        model = GameQuestion
        fields = [
            "id",
            "order",
            "question_type",
            "interaction_type",
            "option_layout",
            "instruction",
            "prompt",
            "subtitle",
            "chip",
            "options",
            "timer_base_seconds",
            "timer_extension_seconds",
            "timer_total_seconds",
            "timer_remaining_seconds",
            "timer_extension_used",
            "timer_extension_available",
        ]

    def _knowledge_source(self, obj):
        return obj.knowledge_source

    def _legacy_source(self, obj):
        return obj.source

    @extend_schema_field(serializers.CharField)
    def get_prompt(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.prompt
        return self._legacy_source(obj).prompt

    @extend_schema_field(serializers.CharField)
    def get_subtitle(self, obj):
        return ""

    @extend_schema_field(serializers.CharField)
    def get_chip(self, obj):
        return ""

    @extend_schema_field(serializers.CharField)
    def get_question_type(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.source_type
        return self._legacy_source(obj).question_type

    @extend_schema_field(serializers.CharField)
    def get_interaction_type(self, obj):
        return interaction_type_for(self.get_question_type(obj), obj.options)

    @extend_schema_field(serializers.CharField)
    def get_option_layout(self, obj):
        return option_layout_for(self.get_question_type(obj))

    @extend_schema_field(serializers.CharField)
    def get_instruction(self, obj):
        return ""

    @extend_schema_field(serializers.IntegerField)
    def get_timer_base_seconds(self, obj):
        return obj.session.timer_seconds

    @extend_schema_field(serializers.IntegerField)
    def get_timer_total_seconds(self, obj):
        return question_timer_total_seconds(obj.session, obj)

    @extend_schema_field(serializers.IntegerField)
    def get_timer_remaining_seconds(self, obj):
        return question_remaining_seconds(obj.session, obj)

    @extend_schema_field(serializers.BooleanField)
    def get_timer_extension_available(self, obj):
        return (
            obj.session.status == GameSession.STATUS_ACTIVE
            and not obj.answered_at
            and not obj.timer_extension_used
            and question_timer_total_seconds(obj.session, obj) < QUESTION_TIMER_MAX_SECONDS
        )


class GameSessionSerializer(serializers.ModelSerializer):
    current_question = serializers.SerializerMethodField()

    class Meta:
        model = GameSession
        fields = [
            "id",
            "topic_key",
            "target_category_key",
            "mode",
            "total_questions",
            "timer_seconds",
            "score",
            "correct_count",
            "streak",
            "status",
            "paused_at",
            "total_paused_seconds",
            "is_finished",
            "current_question",
        ]

    @extend_schema_field(GameQuestionSerializer(allow_null=True))
    def get_current_question(self, obj):
        question = get_current_question(obj)
        return GameQuestionSerializer(question).data if question else None


class StartGameSerializer(serializers.Serializer):
    topic_key = serializers.CharField(default="random")
    target_category_key = serializers.CharField(required=False, allow_blank=True, default="")
    mode = serializers.ChoiceField(
        choices=["random", "category", "all", "mistakes", "league"],
        default="random",
    )
    count = serializers.IntegerField(default=10, min_value=10, max_value=100)
    timer_seconds = serializers.IntegerField(default=30, min_value=5, max_value=120)

    def validate_count(self, value):
        if value % 10 != 0:
            raise serializers.ValidationError("Count must be a multiple of 10.")
        return value

    def validate(self, attrs):
        if attrs.get("mode") == "category" and not attrs.get("target_category_key"):
            raise serializers.ValidationError(
                {"target_category_key": "Category mode requires target_category_key."}
            )
        if attrs.get("mode") != "category":
            attrs["target_category_key"] = ""
        return attrs


class AnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_answer = serializers.CharField(allow_blank=True)
    client_answered_at = serializers.DateTimeField(required=False)


class GameAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = GameAnswer
        fields = [
            "id",
            "is_correct",
            "time_expired",
            "correct_answer",
            "remaining_seconds",
            "score_delta",
            "xp_delta",
            "scoring_rule_version",
        ]


class GameAnswerResultSerializer(serializers.Serializer):
    answer = GameAnswerSerializer()
    game = GameSessionSerializer()


class GameLifecycleSerializer(serializers.Serializer):
    game = GameSessionSerializer()


class MistakeSerializer(serializers.ModelSerializer):
    prompt = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()
    feedback = serializers.SerializerMethodField()

    class Meta:
        model = Mistake
        fields = [
            "id",
            "topic_key",
            "prompt",
            "correct_answer",
            "feedback",
            "wrong_count",
            "last_wrong_answer",
            "last_at",
        ]

    def _knowledge_source(self, obj):
        return obj.knowledge_source

    def _legacy_source(self, obj):
        return obj.source

    @extend_schema_field(serializers.CharField)
    def get_prompt(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.prompt
        return self._legacy_source(obj).prompt

    @extend_schema_field(serializers.CharField)
    def get_correct_answer(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.correct_answer
        return self._legacy_source(obj).correct_answer

    @extend_schema_field(serializers.CharField)
    def get_feedback(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.explanation
        return self._legacy_source(obj).feedback
