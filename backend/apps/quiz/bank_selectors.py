"""Resolves a quiz setup choice (clinical topic, optional ATC chapter) into a
sample of pre-generated BankQuestion rows.

Deliberately reuses apps.lessons' own clinical-topic -> ATC-L2-chapter
taxonomy (apps.lessons.selectors) rather than inventing a second, separately
organized way to pick a subject -- the whole point is that quiz setup looks
and groups exactly like Lessons, so picking a topic there and here means the
same thing.
"""

import random
from collections import Counter

from apps.drugs.models import Ingredient
from apps.lessons.selectors import slugs_for_topic

from .models import BANK_FIELD_CHOICES, FIELD_META, BankQuestion

# Mirrors apps.quiz.views' record_study() minutes-per-question estimate, so
# the setup screen's time estimate matches what actually gets logged.
MINUTES_PER_QUESTION = 0.5
_FIELD_ORDER = [key for key, _ in BANK_FIELD_CHOICES]

# Caps one data-rich drug (e.g. one with all 7 fields populated) from
# crowding out the rest of a topic's drugs in a single session; relaxed
# below if the topic is too narrow to reach `count` otherwise.
MAX_PER_INGREDIENT = 2


def ingredient_ids_for_selection(topic_key: str, atc_code: str = "") -> list[int]:
    if atc_code:
        slugs = set(
            Ingredient.objects.filter(atc_codes__code__startswith=atc_code)
            .values_list("slug", flat=True)
        )
    else:
        slugs = slugs_for_topic(topic_key)
    if not slugs:
        return []
    return list(Ingredient.objects.filter(slug__in=slugs).values_list("id", flat=True))


def _sample_rows(topic_key: str, atc_code: str, count: int, seed: int | None):
    """The sampling itself, over (id, ingredient_id, field) tuples only -- a
    broad topic has thousands of bank questions, and the full rows (prompt,
    options, ingredient) are only needed for the few actually picked."""
    ingredient_ids = ingredient_ids_for_selection(topic_key, atc_code)
    if not ingredient_ids:
        return []

    rows = list(
        BankQuestion.objects.filter(ingredient_id__in=ingredient_ids)
        .order_by("id")
        .values_list("id", "ingredient_id", "field")
    )
    rng = random.Random(seed)
    rng.shuffle(rows)

    picked = []
    per_ingredient: dict[int, int] = {}
    leftover = []
    for row in rows:
        if len(picked) >= count:
            leftover.append(row)
            continue
        used = per_ingredient.get(row[1], 0)
        if used >= MAX_PER_INGREDIENT:
            leftover.append(row)
            continue
        picked.append(row)
        per_ingredient[row[1]] = used + 1

    # The per-ingredient cap can't fill `count` in a narrow topic (e.g. a
    # one-drug ATC chapter) -- top up from whatever's left over.
    if len(picked) < count:
        picked.extend(leftover[: count - len(picked)])
    return picked


def sample_bank_questions(
    topic_key: str, atc_code: str, count: int, seed: int | None = None
) -> list[BankQuestion]:
    picked = _sample_rows(topic_key, atc_code, count, seed)
    by_id = BankQuestion.objects.select_related("ingredient").in_bulk([row[0] for row in picked])
    return [by_id[row[0]] for row in picked]


def preview_selection(topic_key: str, atc_code: str, count: int) -> dict:
    """What a quiz of this size, on this selection, would actually contain --
    the setup screen's "this quiz covers..." breakdown. Runs the same sample
    the real start would (unseeded, so it's a representative draw, not a
    promise of the exact set start will produce) and tabulates by field,
    rather than reporting the whole available pool, so a topic with 200
    mechanism facts but a 10-question quiz doesn't claim it'll ask all 200."""
    picked = _sample_rows(topic_key, atc_code, count, seed=None)
    counts = Counter(field for _, _, field in picked)
    by_field = [
        {"field": key, "label_fa": FIELD_META[key][0], "tone": FIELD_META[key][1], "count": counts[key]}
        for key in _FIELD_ORDER
        if counts[key] > 0
    ]
    return {
        "available": len(picked),
        "estimated_minutes": max(1, round(count * MINUTES_PER_QUESTION)),
        "by_field": by_field,
    }
