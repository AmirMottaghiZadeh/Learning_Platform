from rest_framework import serializers

from .models import LeitnerCard
from .sections import CARD_SECTIONS

# Facts shown per section on the card back -- enough to review, few enough
# that the card stays readable. The quiz bank draws on all of them.
FACTS_PER_SECTION = 3


def _card_back_fields(ingredient, lang):
    """One block per card section, in a fixed order (apps.flashcards.sections),
    each with its own label and tone so the frontend colors its heading, and
    up to FACTS_PER_SECTION facts. English falls back to the Persian facts
    for a section with no English summary. Reads the prefetched
    `flashcard_facts`, so a page of cards costs no extra queries."""
    by_key: dict[tuple[str, str], list[str]] = {}
    for fact in ingredient.flashcard_facts.all():
        by_key.setdefault((fact.section, fact.lang), []).append(fact.text)

    blocks = []
    for key, fa, en, tone in CARD_SECTIONS:
        items = by_key.get((key, lang)) or by_key.get((key, "fa")) or []
        items = items[:FACTS_PER_SECTION]
        if not items:
            continue
        blocks.append({
            "field": key,
            "label": fa if lang == "fa" else en,
            "tone": tone,
            "items": items,
            # Joined form kept for clients cached before `items` existed.
            "text": "\n".join(items),
        })
    return blocks


class LeitnerCardSerializer(serializers.ModelSerializer):
    front_fa = serializers.SerializerMethodField()
    front_en = serializers.SerializerMethodField()
    back_fields_fa = serializers.SerializerMethodField()
    back_fields_en = serializers.SerializerMethodField()
    drug_slug = serializers.CharField(source="ingredient.slug", read_only=True)

    class Meta:
        model = LeitnerCard
        fields = [
            "id", "drug_slug", "box", "due_at", "times_seen",
            "front_fa", "front_en", "back_fields_fa", "back_fields_en",
        ]

    def get_front_fa(self, obj) -> str:
        return obj.ingredient.name

    def get_front_en(self, obj) -> str:
        return obj.ingredient.name

    def get_back_fields_fa(self, obj) -> list:
        return _card_back_fields(obj.ingredient, "fa")

    def get_back_fields_en(self, obj) -> list:
        return _card_back_fields(obj.ingredient, "en")


class BoxSummarySerializer(serializers.Serializer):
    box = serializers.IntegerField()
    count = serializers.IntegerField()
    due = serializers.IntegerField()
    next_due_at = serializers.DateTimeField(allow_null=True)


class ReviewSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(choices=["easy", "hard"])
