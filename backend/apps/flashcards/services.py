"""Deck seeding and due-count helpers (the latter is read by the dashboard)."""

from django.utils import timezone

from apps.drugs.models import Ingredient

from .models import LeitnerCard

# Fields whose summaries make a good card back, in the order they're joined.
BACK_FIELDS = ["clinical_pharmacology", "dosage_and_administration", "warnings",
               "contraindications", "adverse_reactions"]
DEFAULT_SEED_LIMIT = 40


def due_card_count(user, at=None):
    at = at or timezone.now()
    return LeitnerCard.objects.filter(user=user, due_at__lte=at).count()


def _seed_candidates(limit):
    """Ingredients with enough summarised content to make a two-sided card."""
    ranked = []
    qs = Ingredient.objects.prefetch_related("sections").order_by("-n_products", "name")
    for ingredient in qs:
        summarised = [
            s for s in ingredient.sections.all()
            if s.field in BACK_FIELDS and (s.summary_fa or s.summary_en)
        ]
        if len(summarised) >= 2:
            ranked.append(ingredient)
        if len(ranked) >= limit:
            break
    return ranked


def seed_deck(user, limit=DEFAULT_SEED_LIMIT):
    have = set(
        LeitnerCard.objects.filter(user=user).values_list("ingredient_id", flat=True)
    )
    created = 0
    for ingredient in _seed_candidates(limit):
        if ingredient.id in have:
            continue
        LeitnerCard.objects.create(user=user, ingredient=ingredient)
        created += 1
    return {"created": created, "deck_size": LeitnerCard.objects.filter(user=user).count()}
