"""Deck seeding and due-count helpers (the latter is read by the dashboard)."""

from django.db.models import Count, Q
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


def _with_enough_content():
    """Ingredients with at least two summarised back-of-card sections -- enough
    content for a two-sided card -- decided in the database, so seeding never
    loads profile sections (the whole table, raw label text included) just to
    count them."""
    summarised = Count(
        "sections",
        filter=Q(sections__field__in=BACK_FIELDS)
        & (Q(sections__summary_fa__gt="") | Q(sections__summary_en__gt="")),
    )
    return Ingredient.objects.annotate(n_summarised=summarised).filter(n_summarised__gte=2)


def _seed_candidates(user, limit):
    """Ingredient ids with enough summarised content to make a two-sided card
    -- the drugs the learner has actually finished reading in Lessons first
    (reviewing what you just studied is the point of spaced repetition, not
    an arbitrary global "most prescribed" list), falling back to the
    product-count ranking once their reading history runs out, so a learner
    with no lesson history yet (or who has read fewer than `limit` drugs)
    still gets a full starter deck."""
    read_slugs = read_slugs_for_user(user)
    ranked = []
    if read_slugs:
        ranked = list(
            _with_enough_content()
            .filter(slug__in=read_slugs)
            .order_by("name")
            .values_list("id", flat=True)[:limit]
        )
    if len(ranked) < limit:
        ranked += list(
            _with_enough_content()
            .exclude(id__in=ranked)
            .order_by("-n_products", "name")
            .values_list("id", flat=True)[: limit - len(ranked)]
        )
    return ranked


def seed_deck(user, limit=DEFAULT_SEED_LIMIT):
    have = set(
        LeitnerCard.objects.filter(user=user).values_list("ingredient_id", flat=True)
    )
    new_ids = [i for i in _seed_candidates(user, limit) if i not in have]
    LeitnerCard.objects.bulk_create([LeitnerCard(user=user, ingredient_id=i) for i in new_ids])
    created = len(new_ids)
    return {"created": created, "deck_size": LeitnerCard.objects.filter(user=user).count()}
