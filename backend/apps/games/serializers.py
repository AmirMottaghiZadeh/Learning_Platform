from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.games.models import QuizReminder
from apps.games.services.lifecycle_service import (
    QUESTION_TIMER_MAX_SECONDS,
    question_remaining_seconds,
    question_timer_total_seconds,
)
from apps.quizzes.presentation import (
    QUESTION_TYPE_LABELS,
    chip_for,
    instruction_for,
    interaction_type_for,
    option_layout_for,
)

from .models import GameSession, GameQuestion, GameAnswer, Mistake
from .selectors import get_current_question


class GameQuestionSerializer(serializers.ModelSerializer):
    prompt = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()
    chip = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()
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
            "explanation",
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
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return (
                knowledge_source.metadata.get("subtitle")
                or knowledge_source.learning_object.subtitle
                or ""
            )
        return ""

    @extend_schema_field(serializers.CharField)
    def get_chip(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            if self.get_question_type(obj) == "timing":
                return ""
            return chip_for(self.get_question_type(obj), knowledge_source.metadata)
        return ""

    @extend_schema_field(serializers.CharField)
    def get_explanation(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.explanation
        return self._legacy_source(obj).feedback

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
        return instruction_for(self.get_question_type(obj))

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
    topic_id = serializers.IntegerField(required=False)
    topic_key = serializers.CharField(required=False, default="random")
    target_category_key = serializers.CharField(required=False, allow_blank=True, default="")
    mode = serializers.ChoiceField(
        choices=["random", "category", "all", "mistakes", "league"],
        default="random",
    )
    count = serializers.IntegerField(default=10, min_value=5, max_value=50)
    timer_seconds = serializers.IntegerField(default=30, min_value=5, max_value=120)

    def validate_count(self, value):
        if value % 5 != 0:
            raise serializers.ValidationError("Count must be a multiple of 5.")
        return value

    def validate(self, attrs):
        topic_id = attrs.pop("topic_id", None)
        if topic_id:
            from apps.drugs.models import DrugTopic

            try:
                attrs["topic_key"] = DrugTopic.objects.get(id=topic_id).key
            except DrugTopic.DoesNotExist as exc:
                raise serializers.ValidationError({"topic_id": "نوع سؤال انتخاب‌شده معتبر نیست."}) from exc
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


class QuizReminderSerializer(serializers.ModelSerializer):
    question_type_label = serializers.SerializerMethodField()

    class Meta:
        model = QuizReminder
        fields = [
            "id",
            "question_type",
            "question_type_label",
            "prompt",
            "selected_answer",
            "correct_answer",
            "explanation",
            "options",
            "is_reviewed",
            "created_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_question_type_label(self, obj):
        return QUESTION_TYPE_LABELS.get(obj.question_type, obj.question_type)


class QuizReminderCreateSerializer(serializers.Serializer):
    game_session_id = serializers.IntegerField(required=False)
    game_question_id = serializers.IntegerField(required=False)
    knowledge_source_id = serializers.IntegerField(required=False)
    question_type = serializers.CharField()
    prompt = serializers.CharField()
    selected_answer = serializers.CharField(required=False, allow_blank=True, default="")
    correct_answer = serializers.CharField()
    explanation = serializers.CharField(required=False, allow_blank=True, default="")
    options = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True,
        default=list,
    )


class QuizReminderUpdateSerializer(serializers.Serializer):
    is_reviewed = serializers.BooleanField()


class QuizHistoryAnswerSerializer(serializers.ModelSerializer):
    question_id = serializers.IntegerField(source="question.id", read_only=True)
    prompt = serializers.SerializerMethodField()
    question_type = serializers.SerializerMethodField()
    question_type_label = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()
    options = serializers.SerializerMethodField()

    class Meta:
        model = GameAnswer
        fields = [
            "id",
            "question_id",
            "prompt",
            "question_type",
            "question_type_label",
            "options",
            "selected_answer",
            "correct_answer",
            "explanation",
            "is_correct",
            "time_expired",
            "remaining_seconds",
            "score_delta",
            "xp_delta",
            "answered_at",
        ]

    @extend_schema_field(serializers.CharField)
    def get_prompt(self, obj):
        question = obj.question
        if question.knowledge_source_id:
            return question.knowledge_source.prompt
        return question.source.prompt

    @extend_schema_field(serializers.CharField)
    def get_question_type(self, obj):
        question = obj.question
        if question.knowledge_source_id:
            return question.knowledge_source.source_type
        return question.source.question_type

    @extend_schema_field(serializers.CharField)
    def get_question_type_label(self, obj):
        question_type = self.get_question_type(obj)
        return QUESTION_TYPE_LABELS.get(question_type, question_type)

    @extend_schema_field(serializers.CharField)
    def get_explanation(self, obj):
        question = obj.question
        if question.knowledge_source_id:
            return question.knowledge_source.explanation
        return question.source.feedback

    @extend_schema_field(serializers.ListField(child=serializers.CharField()))
    def get_options(self, obj):
        return obj.question.options or []


class QuizHistorySessionSerializer(serializers.ModelSerializer):
    answered_questions = serializers.SerializerMethodField()
    wrong_count = serializers.SerializerMethodField()
    accuracy_percent = serializers.SerializerMethodField()
    duration_seconds = serializers.SerializerMethodField()
    question_type_label = serializers.SerializerMethodField()
    answers = QuizHistoryAnswerSerializer(many=True, read_only=True)

    class Meta:
        model = GameSession
        fields = [
            "id",
            "topic_key",
            "question_type_label",
            "target_category_key",
            "mode",
            "status",
            "score",
            "total_questions",
            "answered_questions",
            "correct_count",
            "wrong_count",
            "accuracy_percent",
            "streak",
            "timer_seconds",
            "total_paused_seconds",
            "duration_seconds",
            "started_at",
            "finished_at",
            "answers",
        ]

    @extend_schema_field(serializers.IntegerField)
    def get_answered_questions(self, obj):
        return obj.answers.count()

    @extend_schema_field(serializers.IntegerField)
    def get_wrong_count(self, obj):
        return max(0, self.get_answered_questions(obj) - obj.correct_count)

    @extend_schema_field(serializers.IntegerField)
    def get_accuracy_percent(self, obj):
        answered = self.get_answered_questions(obj)
        if not answered:
            return 0
        return round((obj.correct_count / answered) * 100)

    @extend_schema_field(serializers.IntegerField)
    def get_duration_seconds(self, obj):
        if not obj.started_at:
            return 0
        finished_at = obj.finished_at or obj.started_at
        return max(
            0,
            int((finished_at - obj.started_at).total_seconds()) - obj.total_paused_seconds,
        )

    @extend_schema_field(serializers.CharField)
    def get_question_type_label(self, obj):
        return QUESTION_TYPE_LABELS.get(obj.topic_key, obj.topic_key)
