from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from .models import FlashcardState, FlashcardReview

class FlashcardStateSerializer(serializers.ModelSerializer):
    prompt = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()
    source_type = serializers.SerializerMethodField()
    target_category_key = serializers.SerializerMethodField()
    target_category_label = serializers.SerializerMethodField()
    is_in_leitner_box = serializers.SerializerMethodField()

    class Meta:
        model = FlashcardState
        fields = [
            "id",
            "prompt",
            "correct_answer",
            "source_type",
            "target_category_key",
            "target_category_label",
            "is_in_leitner_box",
            "box",
            "review_state",
            "interval_days",
            "review_count",
            "lapse_count",
            "last_rating",
            "schedule_rule_version",
            "due_at",
            "last_reviewed_at",
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
    def get_source_type(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.source_type
        return self._legacy_source(obj).question_type

    @extend_schema_field(serializers.CharField)
    def get_target_category_key(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.metadata.get("target_category_key", "")
        return ""

    @extend_schema_field(serializers.CharField)
    def get_target_category_label(self, obj):
        knowledge_source = self._knowledge_source(obj)
        if knowledge_source:
            return knowledge_source.metadata.get("target_category_label", "")
        return ""

    @extend_schema_field(serializers.BooleanField)
    def get_is_in_leitner_box(self, obj):
        return obj.box >= 1 and obj.review_state != FlashcardState.REVIEW_STATE_SUSPENDED

class FlashcardReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlashcardReview
        fields = [
            "id",
            "rating",
            "box_before",
            "box_after",
            "interval_days",
            "scheduled_due_at",
            "rule_version",
            "created_at",
        ]


class FlashcardReviewRequestSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(
        choices=["known", "unknown", "again", "hard", "good", "easy"],
        default="known",
    )


class FlashcardSeedRequestSerializer(serializers.Serializer):
    product_id = serializers.CharField(default="pharmexa")
    count = serializers.IntegerField(
        default=0,
        min_value=0,
        max_value=10000,
        required=False,
        help_text="Deprecated and ignored. Deck creation always schedules the full selected source set.",
    )
    target_category_key = serializers.CharField(required=False, allow_blank=True, default="")
    source_type = serializers.ChoiceField(
        choices=[
            "brandGeneric",
            "timing",
            "indication",
            "sideEffects",
            "classification",
            "dosageForm",
            "dosing",
            "pregnancy",
            "doseAdjustment",
        ],
        required=False,
        allow_blank=True,
        default="",
    )


class FlashcardSeedResultSerializer(serializers.Serializer):
    created_count = serializers.IntegerField()


class FlashcardBoxSerializer(serializers.Serializer):
    box = serializers.IntegerField()
    count = serializers.IntegerField()


class FlashcardBoxSummarySerializer(serializers.Serializer):
    new = serializers.IntegerField()
    total = serializers.IntegerField()
    boxes = FlashcardBoxSerializer(many=True)


class FlashcardDeckSummarySerializer(serializers.Serializer):
    product_id = serializers.CharField()
    target_category_key = serializers.CharField(allow_blank=True)
    source_type = serializers.CharField(allow_blank=True)
    eligible_sources = serializers.IntegerField()
    scheduled_cards = serializers.IntegerField()
    unscheduled_sources = serializers.IntegerField()
    active_cards = serializers.IntegerField()
    new_cards = serializers.IntegerField()
    due_cards = serializers.IntegerField()
    leitner = FlashcardBoxSummarySerializer()
