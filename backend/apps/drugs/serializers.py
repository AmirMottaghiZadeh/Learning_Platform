"""Read serializers for the drug-knowledge API.

Two views of the same `IngredientProfileSection` rows:

* `sections` — the raw field-keyed shape (all 12 clinical fields), used by any
  client that wants the whole profile.
* `lesson_sections` — the design's lesson-card shape: a curated, ordered subset
  with bilingual titles, `tone` for colour, and `text_{fa,en}` taken from the
  section summaries. Mirrors `FIELD_MAP` + `LESSON_EXTRA` in the design file.
"""

from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from .models import (
    CLINICAL_FIELD_KEYS,
    AtcCode,
    Ingredient,
    IngredientProfileSection,
)


# key -> (section field, fa title, en title, tone)
LESSON_SECTION_MAP = [
    ("mechanism", "clinical_pharmacology", "مکانیسم", "Mechanism", "info"),
    ("indication", "indications_and_usage", "اندیکاسیون", "Indication", "info"),
    ("dose", "dosage_and_administration", "دوز", "Dose", "info"),
    ("forms", "dosage_forms_and_strengths", "اشکال دارویی", "Dosage forms", "info"),
    ("contraindications", "contraindications", "منع مطلق", "Contraindications", "deny"),
    ("do_not_use", "do_not_use", "چه‌وقت مصرف نکنیم", "Do not use", "deny"),
    ("boxed_warning", "boxed_warning", "جعبه‌سیاه", "Boxed warning", "boxed"),
    ("warning", "warnings", "هشدار", "Warning", "caution"),
    ("side", "adverse_reactions", "عوارض جانبی", "Side effects", "caution"),
    ("interactions", "drug_interactions", "تداخلات", "Interactions", "caution"),
    ("pregnancy", "pregnancy", "بارداری", "Pregnancy", "special"),
    ("abuse", "abuse", "سوءمصرف و وابستگی", "Abuse & dependence", "special"),
]


class AtcCodeSerializer(serializers.ModelSerializer):
    level = serializers.IntegerField(read_only=True)
    ingredient_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = AtcCode
        fields = ["code", "name", "level", "ingredient_count"]


class IngredientListSerializer(serializers.ModelSerializer):
    atc_codes = AtcCodeSerializer(many=True, read_only=True)

    class Meta:
        model = Ingredient
        fields = [
            "rxcui",
            "name",
            "slug",
            "n_products",
            "n_source_records",
            "pharm_classes",
            "atc_codes",
        ]


class ProfileSectionSerializer(serializers.ModelSerializer):
    label = serializers.CharField(source="get_field_display", read_only=True)
    has_content = serializers.BooleanField(read_only=True)
    has_summary = serializers.BooleanField(read_only=True)

    class Meta:
        model = IngredientProfileSection
        fields = [
            "field",
            "label",
            "has_content",
            "has_summary",
            "n_contributing_products",
            "summary_fa",
            "summary_en",
            "raw_text",
        ]


class LessonSectionSerializer(serializers.Serializer):
    key = serializers.CharField()
    field = serializers.CharField()
    title_fa = serializers.CharField()
    title_en = serializers.CharField()
    tone = serializers.CharField()
    text_fa = serializers.CharField()
    text_en = serializers.CharField()
    has_summary = serializers.BooleanField()


class IngredientDetailSerializer(IngredientListSerializer):
    sections = serializers.SerializerMethodField()
    lesson_sections = serializers.SerializerMethodField()

    class Meta(IngredientListSerializer.Meta):
        fields = IngredientListSerializer.Meta.fields + ["sections", "lesson_sections"]

    def _sections_by_field(self, obj):
        return {s.field: s for s in obj.sections.all()}

    @extend_schema_field(ProfileSectionSerializer(many=True))
    def get_sections(self, obj):
        by_field = self._sections_by_field(obj)
        ordered = [by_field[f] for f in CLINICAL_FIELD_KEYS if f in by_field]
        return ProfileSectionSerializer(ordered, many=True).data

    @extend_schema_field(LessonSectionSerializer(many=True))
    def get_lesson_sections(self, obj):
        by_field = self._sections_by_field(obj)
        rows = []
        for key, field, title_fa, title_en, tone in LESSON_SECTION_MAP:
            section = by_field.get(field)
            if section is None:
                continue
            text_fa = (section.summary_fa or "").strip()
            text_en = (section.summary_en or "").strip()
            if not text_fa and not text_en:
                continue
            rows.append({
                "key": key,
                "field": field,
                "title_fa": title_fa,
                "title_en": title_en,
                "tone": tone,
                "text_fa": text_fa,
                "text_en": text_en,
                "has_summary": True,
            })
        return rows
