from rest_framework import serializers

from .models import LeitnerCard
from .services import BACK_FIELDS

_FIELD_LABEL = {
    "clinical_pharmacology": ("مکانیسم", "Mechanism"),
    "dosage_and_administration": ("دوز", "Dose"),
    "warnings": ("هشدار", "Warning"),
    "contraindications": ("منع مصرف", "Contraindication"),
    "adverse_reactions": ("عوارض", "Side effects"),
}


def _card_back(ingredient, lang):
    parts = []
    by_field = {s.field: s for s in ingredient.sections.all()}
    for field in BACK_FIELDS:
        section = by_field.get(field)
        if not section:
            continue
        text = (section.summary_fa if lang == "fa" else section.summary_en) or ""
        text = text.strip()
        if not text:
            continue
        label = _FIELD_LABEL[field][0 if lang == "fa" else 1]
        parts.append(f"{label}: {text}")
        if len(parts) == 3:
            break
    return "\n\n".join(parts)


class LeitnerCardSerializer(serializers.ModelSerializer):
    front_fa = serializers.SerializerMethodField()
    front_en = serializers.SerializerMethodField()
    back_fa = serializers.SerializerMethodField()
    back_en = serializers.SerializerMethodField()
    drug_slug = serializers.CharField(source="ingredient.slug", read_only=True)

    class Meta:
        model = LeitnerCard
        fields = [
            "id", "drug_slug", "box", "due_at", "times_seen",
            "front_fa", "front_en", "back_fa", "back_en",
        ]

    def get_front_fa(self, obj) -> str:
        return obj.ingredient.name

    def get_front_en(self, obj) -> str:
        return obj.ingredient.name

    def get_back_fa(self, obj) -> str:
        return _card_back(obj.ingredient, "fa")

    def get_back_en(self, obj) -> str:
        return _card_back(obj.ingredient, "en")


class BoxSummarySerializer(serializers.Serializer):
    box = serializers.IntegerField()
    count = serializers.IntegerField()
    due = serializers.IntegerField()
    next_due_at = serializers.DateTimeField(allow_null=True)


class ReviewSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(choices=["easy", "hard"])
