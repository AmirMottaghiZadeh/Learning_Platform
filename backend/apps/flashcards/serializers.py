from rest_framework import serializers

from .leitner import RATINGS
from .models import LeitnerCard
from .sections import CARD_SECTIONS, SECTION_META

# Facts shown per section on an old per-drug card's back -- enough to
# review, few enough that the card stays readable. A one-section card shows
# them all (the pipeline writes 2-6).
FACTS_PER_SECTION = 3
FACTS_PER_CARD = 6


def _card_back_fields(ingredient, lang, section=None):
    """One block per card section, in a fixed order (apps.flashcards.sections),
    each with its own label and tone so the frontend colors its heading, and
    up to FACTS_PER_SECTION facts -- or, for one `section`'s card, only that
    block with all its facts. English falls back to the Persian facts for a
    section with no English summary. Reads the prefetched `flashcard_facts`,
    so a page of cards costs no extra queries."""
    by_key: dict[tuple[str, str], list[str]] = {}
    for fact in ingredient.flashcard_facts.all():
        by_key.setdefault((fact.section, fact.lang), []).append(fact.text)

    blocks = []
    for key, fa, en, tone in CARD_SECTIONS:
        if section and key != section:
            continue
        items = by_key.get((key, lang)) or by_key.get((key, "fa")) or []
        items = items[: FACTS_PER_CARD if section else FACTS_PER_SECTION]
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


class _SectionCard(serializers.Serializer):
    """A one-section card's face: the drug (Persian name first, English
    under it) and which section it asks about; the back is that section's
    facts. Serializes {"ingredient", "section"} -- a deck's card -- or a
    LeitnerCard, which has both."""

    drug_slug = serializers.CharField(source="ingredient.slug")
    section = serializers.CharField()
    section_label_fa = serializers.SerializerMethodField()
    section_label_en = serializers.SerializerMethodField()
    section_tone = serializers.SerializerMethodField()
    front_fa = serializers.SerializerMethodField()
    front_en = serializers.CharField(source="ingredient.name")
    back_fields_fa = serializers.SerializerMethodField()
    back_fields_en = serializers.SerializerMethodField()

    def _section(self, obj):
        return obj["section"] if isinstance(obj, dict) else obj.section

    def get_section_label_fa(self, obj) -> str:
        return SECTION_META[self._section(obj)]["fa"]

    def get_section_label_en(self, obj) -> str:
        return SECTION_META[self._section(obj)]["en"]

    def get_section_tone(self, obj) -> str:
        return SECTION_META[self._section(obj)]["tone"]

    def get_front_fa(self, obj) -> str:
        ingredient = obj["ingredient"] if isinstance(obj, dict) else obj.ingredient
        return ingredient.name_fa or ingredient.name

    def get_back_fields_fa(self, obj) -> list:
        ingredient = obj["ingredient"] if isinstance(obj, dict) else obj.ingredient
        return _card_back_fields(ingredient, "fa", self._section(obj))

    def get_back_fields_en(self, obj) -> list:
        ingredient = obj["ingredient"] if isinstance(obj, dict) else obj.ingredient
        return _card_back_fields(ingredient, "en", self._section(obj))


class DeckCardSerializer(_SectionCard):
    """One card of a topic deck: one drug's one section."""


class RatingOutcomeSerializer(serializers.Serializer):
    box = serializers.IntegerField(help_text="The drawer it would move to; 0 = out of the box.")
    minutes = serializers.IntegerField(help_text="Until it is due again.")


class BoxCardSerializer(_SectionCard):
    """A card in the Leitner box, with what each review button would do to it
    (context["previews"], from leitner.previews)."""

    id = serializers.IntegerField()
    box = serializers.IntegerField()
    outcomes = serializers.SerializerMethodField()

    def get_outcomes(self, obj) -> dict:
        return self.context.get("previews", {}).get(obj.id, {})


class DrawerSerializer(serializers.Serializer):
    box = serializers.IntegerField()
    count = serializers.IntegerField()
    due = serializers.IntegerField()


class LeitnerOverviewSerializer(serializers.Serializer):
    drawers = DrawerSerializer(many=True)
    total = serializers.IntegerField()
    due = serializers.IntegerField()
    today = serializers.IntegerField(help_text="Cards in today's review, within the daily minutes.")
    today_minutes = serializers.IntegerField()
    daily_minutes = serializers.IntegerField()
    reviewed_today = serializers.IntegerField()
    left_box = serializers.IntegerField(help_text="Cards that have left the box.")
    exam_days_left = serializers.IntegerField(allow_null=True)
    preview = BoxCardSerializer(many=True)


class BoxReviewSerializer(serializers.Serializer):
    rating = serializers.ChoiceField(choices=RATINGS)


class NextTopicSerializer(serializers.Serializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    category_key = serializers.CharField()
    category_name_fa = serializers.CharField()
    category_name_en = serializers.CharField()


class TopicSummarySerializer(serializers.Serializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    total = serializers.IntegerField()
    position = serializers.IntegerField()
    finished = serializers.BooleanField()


class CategoryDecksSerializer(serializers.Serializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    topics_finished = serializers.IntegerField()
    topics = TopicSummarySerializer(many=True)


class DeckOverviewSerializer(serializers.Serializer):
    topics_finished = serializers.IntegerField()
    cards_reviewed = serializers.IntegerField()
    categories = CategoryDecksSerializer(many=True)


class DeckProgressSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    position = serializers.IntegerField()
    known = serializers.IntegerField()
    hard = serializers.IntegerField()
    finished = serializers.BooleanField()
    next_topic = NextTopicSerializer(allow_null=True)


class TopicDeckSerializer(DeckProgressSerializer):
    key = serializers.CharField()
    name_fa = serializers.CharField()
    name_en = serializers.CharField()
    category_key = serializers.CharField()
    category_name_fa = serializers.CharField()
    category_name_en = serializers.CharField()
    cards = DeckCardSerializer(many=True)


class DeckAnswerSerializer(serializers.Serializer):
    drug_slug = serializers.CharField(max_length=280)
    # Which of the drug's cards; apps from before one-section cards send
    # none and answer the deck's current card.
    section = serializers.CharField(max_length=20, required=False, allow_blank=True)
    # "hard" is "یادم نبود": the card goes in the Leitner box.
    rating = serializers.ChoiceField(choices=["easy", "hard"])
