from rest_framework import serializers

from apps.drugs.serializers import IngredientDetailSerializer


class SubgroupSerializer(serializers.Serializer):
    code = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    total = serializers.IntegerField()
    done = serializers.IntegerField()


class LessonGroupSerializer(serializers.Serializer):
    code = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    # The broad body-system/domain this study topic sits under (see
    # apps.lessons.data.study_topics.CATEGORIES) — purely for grouping the 50+
    # topics into a shorter list the learner picks from first.
    category_code = serializers.CharField()
    category_name_fa = serializers.CharField()
    category_name_en = serializers.CharField()
    subgroups = SubgroupSerializer(many=True)


class TopicSerializer(serializers.Serializer):
    code = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()


class ChapterProgressSerializer(serializers.Serializer):
    # Globally-read drugs (apps.lessons.models.ReadDrug) filtered to this
    # chapter's ingredients — not a per-chapter stored list, so a drug read
    # via a different chapter it also belongs to shows as read here too.
    read_drug_slugs = serializers.ListField(child=serializers.CharField())
    scroll_pct = serializers.IntegerField()
    last_opened_at = serializers.DateTimeField()


class ExamPointSerializer(serializers.Serializer):
    drug_name = serializers.CharField()
    drug_slug = serializers.CharField()
    field = serializers.CharField()
    tone = serializers.CharField()
    point_fa = serializers.CharField()
    point_en = serializers.CharField()


class ChapterSerializer(serializers.Serializer):
    code = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    # Primary study topic (see apps.lessons.data.study_topics) — kept under
    # the old field names so existing clients keep working unchanged.
    group_code = serializers.CharField()
    group_name_fa = serializers.CharField()
    group_name_en = serializers.CharField()
    # Every study topic this chapter belongs to; length 1 for most chapters,
    # more for a class that's first-line across several indications.
    topics = TopicSerializer(many=True)
    # The true, unmodified ATC anatomical (L1) group name, for rigour.
    anatomical_name_fa = serializers.CharField()
    anatomical_name_en = serializers.CharField()
    drugs = IngredientDetailSerializer(many=True)
    exam_points = ExamPointSerializer(many=True)
    progress = ChapterProgressSerializer()


class ChapterProgressUpdateSerializer(serializers.Serializer):
    drug_slug = serializers.CharField(required=False, allow_blank=True)
    scroll_pct = serializers.IntegerField(required=False, min_value=0, max_value=100)
