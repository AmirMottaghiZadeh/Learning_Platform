"""Deck seeding and due-count helpers (the latter is read by the dashboard)."""

from django.utils import timezone

from apps.drugs.models import Ingredient
from apps.lessons.selectors import read_slugs_for_user

from .models import LeitnerCard

# Fields whose summaries make a good card back, in the order they're joined
# -- the same five the question bank draws on (apps.quiz.bank_generator),
# minus mechanism: too abstract for a one-line recall card.
BACK_FIELDS = ["indications_and_usage", "adverse_reactions", "warnings",
               "contraindications", "dosage_and_administration"]
DEFAULT_SEED_LIMIT = 40


def due_card_count(user, at=None):
    at = at or timezone.now()
    return LeitnerCard.objects.filter(user=user, due_at__lte=at).count()


def _has_enough_content(ingredient):
    summarised = [
        s for s in ingredient.sections.all()
        if s.field in BACK_FIELDS and (s.summary_fa or s.summary_en)
    ]
    return len(summarised) >= 2


def _seed_candidates(user, limit):
    """Ingredients with enough summarised content to make a two-sided card --
    the drugs the learner has actually finished reading in Lessons first
    (reviewing what you just studied is the point of spaced repetition, not
    an arbitrary global "most prescribed" list), falling back to the
    product-count ranking once their reading history runs out, so a learner
    with no lesson history yet (or who has read fewer than `limit` drugs)
    still gets a full starter deck."""
    read_slugs = read_slugs_for_user(user)
    ranked = []
    seen_ids = set()

    if read_slugs:
        read_ingredients = (
            Ingredient.objects.filter(slug__in=read_slugs)
            .prefetch_related("sections")
            .order_by("name")
        )
        for ingredient in read_ingredients:
            if _has_enough_content(ingredient):
                ranked.append(ingredient)
                seen_ids.add(ingredient.id)
            if len(ranked) >= limit:
                return ranked

    qs = (
        Ingredient.objects.exclude(id__in=seen_ids)
        .prefetch_related("sections")
        .order_by("-n_products", "name")
    )
    for ingredient in qs:
        if _has_enough_content(ingredient):
            ranked.append(ingredient)
        if len(ranked) >= limit:
            break
    return ranked


def seed_deck(user, limit=DEFAULT_SEED_LIMIT):
    have = set(
        LeitnerCard.objects.filter(user=user).values_list("ingredient_id", flat=True)
    )
    created = 0
    for ingredient in _seed_candidates(user, limit):
        if ingredient.id in have:
            continue
        LeitnerCard.objects.create(user=user, ingredient=ingredient)
        created += 1
    return {"created": created, "deck_size": LeitnerCard.objects.filter(user=user).count()}
