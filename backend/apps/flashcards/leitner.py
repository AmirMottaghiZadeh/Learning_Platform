"""The Leitner box's smart review.

Only what the learner did not know goes in: a deck's "یادم نبود" or a wrong
quiz answer puts that drug's card section in drawer 1, and every further
miss moves it a drawer up, to 5. A review rates the card two ways:

- "forgot" (یادم نبود): a drawer up, closer to 5; it comes round once more
  at the end of the same review (the app re-queues it) and is due again
  tomorrow;
- "good" (یادم بود): a drawer down, and out of the box from drawer 1.

When a card comes back is its own interval, grown by its own ease -- which
falls with every miss -- so a card missed often returns sooner (SM-2's
idea, simplified). The learner never sees days, only how many cards are
due today. An exam date in the study plan caps every interval at half the
time left, so each card comes up again before the exam.

Today's review takes the due cards from the highest drawer down, as many as
the plan's daily minutes allow (SECONDS_PER_CARD each). Any drawer can also
be opened and reviewed on its own, due or not.
"""

import math
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from apps.drugs.models import Ingredient
from apps.progress.models import StudyPlan

from .models import MAX_BOX, OUT_OF_BOX, FlashcardFact, LeitnerCard
from .sections import SECTION_KEYS

FORGOT, GOOD = "forgot", "good"
RATINGS = [FORGOT, GOOD]

SECONDS_PER_CARD = 20
DEFAULT_DAILY_MINUTES = 15
START_EASE, MIN_EASE = 2.3, 1.3

# A quiz question's field -> the card sections that hold its fact, the
# first one the drug has a card for winning.
QUIZ_FIELD_SECTIONS = {
    "indication": ["indication"],
    "mechanism": ["mechanism"],
    "class_level": ["mechanism", "indication"],
    "adverse_effect": ["adr_serious", "adr_common"],
    "interaction": ["interaction"],
    "contra_boxed": ["contra_boxed", "warning"],
    "counseling": ["warning"],
    "pregnancy": ["warning", "contra_boxed"],
    "monitoring": ["warning", "adr_serious"],
}


def _start_of_tomorrow():
    now = timezone.localtime()
    return now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)


def card_sections(ingredient_ids=None) -> dict[int, list[str]]:
    """The card sections each drug has Persian facts for, in card order:
    {ingredient id: ["indication", "adr_common", ...]}. All carded drugs
    when `ingredient_ids` is None."""
    facts = FlashcardFact.objects.filter(lang="fa")
    if ingredient_ids is not None:
        facts = facts.filter(ingredient_id__in=ingredient_ids)
    found: dict[int, set[str]] = {}
    for ingredient_id, section in facts.values_list("ingredient_id", "section").distinct():
        found.setdefault(ingredient_id, set()).add(section)
    return {i: [s for s in SECTION_KEYS if s in sections] for i, sections in found.items()}


def add_miss(user, ingredient, section):
    """The learner did not know this card: into drawer 1, or a drawer up
    (a card that had left the box comes back to drawer 1), and up for
    review by tomorrow."""
    tomorrow = _start_of_tomorrow()
    card, created = LeitnerCard.objects.get_or_create(
        user=user, ingredient=ingredient, section=section,
        defaults={"box": 1, "lapses": 1, "due_at": tomorrow, "interval_days": 0, "ease": START_EASE},
    )
    if created:
        return card
    was_out = card.box == OUT_OF_BOX
    card.box = min(MAX_BOX, card.box + 1)
    card.lapses += 1
    card.ease = max(MIN_EASE, card.ease - 0.2)
    card.interval_days = 0
    card.due_at = tomorrow if was_out else min(card.due_at, tomorrow)
    card.save(update_fields=["box", "lapses", "ease", "interval_days", "due_at"])
    return card


def add_quiz_miss(user, drug_slug, field):
    """A wrong quiz answer: the card holding that fact goes in the box.
    None when the drug has no card for the question's field."""
    ingredient = Ingredient.objects.filter(slug=drug_slug).first()
    if not ingredient:
        return None
    sections = card_sections([ingredient.id]).get(ingredient.id, [])
    section = next((s for s in QUIZ_FIELD_SECTIONS.get(field, []) if s in sections), None)
    return add_miss(user, ingredient, section) if section else None


def _exam_cap_days(user):
    """Half the days left to the study plan's exam, or None without one."""
    plan = StudyPlan.objects.filter(user=user, mode=StudyPlan.MODE_GOAL).first()
    today = timezone.localdate()
    if not plan or not plan.deadline or plan.deadline <= today:
        return None
    return max(1.0, (plan.deadline - today).days / 2)


def outcome(card, rating, cap=None):
    """What a rating would do to the card: its new drawer (OUT_OF_BOX when
    it leaves), interval, ease, and the minutes until it is due again."""
    if rating == FORGOT:
        box, ease, interval = min(MAX_BOX, card.box + 1), max(MIN_EASE, card.ease - 0.2), 1.0
    else:
        box, ease = card.box - 1, card.ease
        interval = max(1.0, card.interval_days) * card.ease
    if cap:
        interval = min(interval, cap)
    return {"box": max(OUT_OF_BOX, box), "interval_days": interval, "ease": ease, "minutes": round(interval * 24 * 60)}


def previews(user, cards):
    """{card id: {rating: {"box", "minutes"}}} -- what each button would do,
    for its label ("به کشوی ۴", "خروج از جعبه")."""
    cap = _exam_cap_days(user)
    out = {}
    for card in cards:
        out[card.id] = {}
        for rating in RATINGS:
            o = outcome(card, rating, cap)
            out[card.id][rating] = {"box": o["box"], "minutes": o["minutes"]}
    return out


def review(user, card, rating):
    """Apply a review and reschedule. Returns the card (box 0 once it left)."""
    o = outcome(card, rating, _exam_cap_days(user))
    now = timezone.now()
    card.box = o["box"]
    card.ease = o["ease"]
    card.interval_days = o["interval_days"]
    card.due_at = now + timedelta(minutes=o["minutes"])
    card.times_seen += 1
    card.last_reviewed_at = now
    if rating == FORGOT:
        card.lapses += 1
    card.save(update_fields=["box", "ease", "interval_days", "due_at", "times_seen", "last_reviewed_at", "lapses"])
    return card


def daily_minutes(user):
    plan = StudyPlan.objects.filter(user=user).exclude(mode=StudyPlan.MODE_NONE).first()
    return plan.daily_minutes if plan else DEFAULT_DAILY_MINUTES


def reviewed_today(user):
    today = timezone.localdate()
    return LeitnerCard.objects.filter(user=user, last_reviewed_at__date=today).exclude(section="").count()


def today_queue(user):
    """Today's review: due cards, highest drawer first, as many as the
    day's minutes still allow. Returns (cards, due count, budget in cards)."""
    budget = max(5, daily_minutes(user) * 60 // SECONDS_PER_CARD)
    left = max(0, budget - reviewed_today(user))
    due = LeitnerCard.objects.in_box().filter(user=user, due_at__lte=timezone.now()).order_by("-box", "due_at", "id")
    return list(due.select_related("ingredient")[:left]), due.count(), budget


def drawer_cards(user, box):
    """Every card in one drawer, soonest due first."""
    return list(
        LeitnerCard.objects.in_box().filter(user=user, box=box).select_related("ingredient").order_by("due_at", "id")
    )


def overview(user):
    """The box at a glance: each drawer's cards and how many are due, and
    today's review."""
    now = timezone.now()
    rows = {
        r["box"]: r
        for r in LeitnerCard.objects.in_box().filter(user=user).values("box").annotate(
            count=Count("id"), due=Count("id", filter=Q(due_at__lte=now))
        )
    }
    queue, due, budget = today_queue(user)
    cap = _exam_cap_days(user)
    return {
        "drawers": [
            {"box": b, "count": rows.get(b, {}).get("count", 0), "due": rows.get(b, {}).get("due", 0)}
            for b in range(1, MAX_BOX + 1)
        ],
        "total": sum(r["count"] for r in rows.values()),
        "due": due,
        "today": len(queue),
        "today_minutes": math.ceil(len(queue) * SECONDS_PER_CARD / 60),
        "daily_minutes": daily_minutes(user),
        "reviewed_today": reviewed_today(user),
        "left_box": LeitnerCard.objects.filter(user=user, box=OUT_OF_BOX).exclude(section="").count(),
        "exam_days_left": None if cap is None else (
            StudyPlan.objects.get(user=user).deadline - timezone.localdate()
        ).days,
        "preview": queue[:3],
    }
