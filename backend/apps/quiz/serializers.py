from rest_framework import serializers

from .models import COUNT_CHOICES, FIELD_META, QuizQuestion, QuizSession


class QuizStartSerializer(serializers.Serializer):
    # A study-topic key (apps.lessons.data.study_topics) -- checked against
    # the real list in the view, not here, since it's generated data rather
    # than a fixed enum. Not required when `ingredient_slug` is given (a
    # single-drug self-test from the lesson screen, not a topic pick).
    category = serializers.CharField(max_length=32, required=False, allow_blank=True, default="")
    # An optional ATC L2 chapter to narrow `category` to a single class
    # within it (e.g. just "C03" within the "hypertension" topic).
    atc_code = serializers.CharField(max_length=8, required=False, allow_blank=True, default="")
    count = serializers.ChoiceField(choices=COUNT_CHOICES, default=10)
    # "Test yourself on this drug" from the end of its lesson page: every
    # available bank question for this one ingredient, across all fields,
    # instead of a sampled, topic-scoped set -- `category`/`atc_code`/`count`
    # are ignored by the view when this is set.
    ingredient_slug = serializers.CharField(max_length=280, required=False, allow_blank=True, default="")


class QuizQuestionSerializer(serializers.ModelSerializer):
    """The learner-facing shape: no `correct_index`."""

    field_label_fa = serializers.SerializerMethodField()
    field_tone = serializers.SerializerMethodField()

    class Meta:
        model = QuizQuestion
        fields = [
            "id", "order", "prompt_fa", "prompt_en", "options_fa", "options_en",
            "field", "field_label_fa", "field_tone", "subject_slug",
        ]

    def get_field_label_fa(self, obj) -> str:
        return FIELD_META[obj.field][0] if obj.field in FIELD_META else ""

    def get_field_tone(self, obj) -> str:
        return FIELD_META[obj.field][1] if obj.field in FIELD_META else "info"


class QuizSessionSerializer(serializers.ModelSerializer):
    questions = QuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = QuizSession
        fields = ["id", "category", "atc_code", "question_count", "questions"]


class QuizAnswerInSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    selected_index = serializers.IntegerField(min_value=0, max_value=3)
    client_answered_at = serializers.DateTimeField(required=False)


class QuizAnswerOutSerializer(serializers.Serializer):
    correct = serializers.BooleanField()
    correct_index = serializers.IntegerField()
    extra_context = serializers.ListField(child=serializers.CharField())


class FieldBreakdownSerializer(serializers.Serializer):
    field = serializers.CharField()
    label_fa = serializers.CharField()
    tone = serializers.CharField()
    correct = serializers.IntegerField()
    total = serializers.IntegerField()


class MissedQuestionSerializer(serializers.Serializer):
    prompt_fa = serializers.CharField()
    options_fa = serializers.ListField(child=serializers.CharField())
    correct_index = serializers.IntegerField()
    selected_index = serializers.IntegerField()


class QuizResultSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    total = serializers.IntegerField()
    mistakes_added = serializers.IntegerField()
    by_field = FieldBreakdownSerializer(many=True)
    missed = MissedQuestionSerializer(many=True)
    previous_best_pct = serializers.IntegerField(allow_null=True)


class QuizOverviewSerializer(serializers.Serializer):
    avg_score_pct = serializers.IntegerField()
    total_quizzes = serializers.IntegerField()
    weak_topics_count = serializers.IntegerField()
    mastery = serializers.DictField(child=serializers.IntegerField())


class FieldPreviewSerializer(serializers.Serializer):
    field = serializers.CharField()
    label_fa = serializers.CharField()
    tone = serializers.CharField()
    count = serializers.IntegerField()


class QuizPreviewSerializer(serializers.Serializer):
    available = serializers.IntegerField()
    estimated_minutes = serializers.IntegerField()
    by_field = FieldPreviewSerializer(many=True)
