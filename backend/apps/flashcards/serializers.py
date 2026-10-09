from rest_framework import serializers

from apps.drugs.management.commands.clean_profile_boilerplate import is_null_placeholder
from apps.quiz.bank_facts import extract_facts
from apps.quiz.models import FIELD_META

from .models import LeitnerCard
from .services import BACK_FIELDS

# (fa label, en label) -- FIELD_META (apps.quiz.models) already has the tone
# for each of these fields (shared with the question bank's field tags) but
# is fa-only, so the bilingual label stays here.
_FIELD_LABEL = {
    "indications_and_usage": ("اندیکاسیون", "Indication"),
    "adverse_reactions": ("عوارض جانبی", "Side effects"),
    "warnings": ("هشدار", "Warning"),
    "contraindications": ("منع مطلق", "Contraindication"),
    "dosage_and_administration": ("دوز", "Dosing"),
}

MIN_FACT_LEN = 10


def _fact_text(fact: dict) -> str:
    if fact["label"]:
        return f'{fact["label"]}: {fact["text"]}'
    return fact["text"]


def _best_fact(summary: str) -> str | None:
    """The single most useful atomic fact in this field's summary -- the
    same extraction the question bank uses (apps.quiz.bank_facts), so a card
    back is one short, real fact per field rather than the whole raw
    paragraph dumped onto the card. Source order (the first bullet/sentence
    that clears the quality bar) rather than random, so a card reviews the
    same fact every time -- the point of spaced repetition."""
    for fact in extract_facts(summary):
        text = _fact_text(fact)
        if len(text) >= MIN_FACT_LEN and not is_null_placeholder(text):
            return text
    return None


def _card_back_fields(ingredient, lang):
    """One block per clinical field, in a fixed order (BACK_FIELDS), each
    carrying the field's own label/tone -- not a single flattened string --
    so the frontend can render it as the same kind of field-tagged list the
    quiz question cards already use, instead of one undifferentiated block
    of text with no visual structure."""
    blocks = []
    by_field = {s.field: s for s in ingredient.sections.all()}
    for field in BACK_FIELDS:
        section = by_field.get(field)
        if not section:
            continue
        summary = (section.summary_fa if lang == "fa" else section.summary_en) or ""
        fact = _best_fact(summary)
        if not fact:
            continue
        label = _FIELD_LABEL[field][0 if lang == "fa" else 1]
        tone = FIELD_META.get(field, (None, "info"))[1]
        blocks.append({"field": field, "label": label, "tone": tone, "text": fact})
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
