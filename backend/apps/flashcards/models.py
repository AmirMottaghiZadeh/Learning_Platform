"""Flashcards and the Leitner box.

A flashcard is one drug's one card section (indication, common side
effects, interactions ...; apps.flashcards.sections): its facts live in
FlashcardFact, loaded from the study_content pipeline. A topic deck shows
its drugs' cards in order (apps.flashcards.decks).

The Leitner box holds only the cards the learner did not know -- "یادم نبود"
in a deck or a review, or a wrong quiz answer on that drug and field.
`LeitnerCard.box` is how often it was missed, 1 to 5: a missed card enters
drawer 1 and climbs a drawer each time it is missed again; each "یادم بود"
in a review brings it down a drawer, and out of the box (`box` 0) from
drawer 1. When a card comes back is the smart scheduler's own interval per
card (apps.flashcards.leitner), never shown as days.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .sections import SECTION_CHOICES

# Days a legacy card waits after landing in each box (index 0 unused).
BOX_INTERVAL_DAYS = {1: 0, 2: 3, 3: 7, 4: 16, 5: 35}
MAX_BOX = 5
# A card that left the box: `box` 0, kept for its history (a new miss
# brings it back to drawer 1).
OUT_OF_BOX = 0


class LeitnerCardQuerySet(models.QuerySet):
    def in_box(self):
        """The cards in the box now: Phase 5 cards (one per drug and section)
        still in a drawer. Rows with no section are the per-drug cards of
        the old box, kept but no longer used."""
        return self.exclude(section="").filter(box__gte=1)


class LeitnerCard(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="leitner_cards",
    )
    ingredient = models.ForeignKey(
        "drugs.Ingredient",
        on_delete=models.CASCADE,
        related_name="leitner_cards",
    )
    # The card section; blank on the old per-drug cards.
    section = models.CharField(max_length=20, choices=SECTION_CHOICES, blank=True, default="")
    box = models.PositiveSmallIntegerField(default=1)
    due_at = models.DateTimeField(default=timezone.now)
    # The scheduler's state: the last interval and how easily the card is
    # recalled (it falls with every miss), and how often it was missed.
    interval_days = models.FloatField(default=0)
    ease = models.FloatField(default=2.3)
    lapses = models.PositiveIntegerField(default=0)
    times_seen = models.PositiveIntegerField(default=0)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = LeitnerCardQuerySet.as_manager()

    class Meta:
        ordering = ["due_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "ingredient", "section"], name="flashcards_unique_user_ingredient_section"
            ),
        ]
        indexes = [models.Index(fields=["user", "due_at"], name="flashcards_user_due_idx")]

    def __str__(self):
        return f"{self.user_id}:{self.ingredient_id}:{self.section or '-'} box{self.box}"

    def review(self, rating):
        """Apply an 'easy' / 'hard' review to an old per-drug card and
        reschedule (the old box, still answering apps installed before it
        was replaced)."""
        if rating == "easy":
            self.box = min(MAX_BOX, self.box + 1)
        else:
            self.box = max(1, self.box - 1)
        self.due_at = timezone.now() + timedelta(days=BOX_INTERVAL_DAYS[self.box])
        self.times_seen += 1
        self.last_reviewed_at = timezone.now()


class FlashcardFact(models.Model):
    """One fact on a drug's card back, in one of the five card sections --
    rebuilt wholesale by build_flashcards, and the same facts the quiz
    question bank asks about (apps.quiz.bank_generator)."""

    LANG_CHOICES = [("fa", "Persian"), ("en", "English")]

    ingredient = models.ForeignKey(
        "drugs.Ingredient",
        on_delete=models.CASCADE,
        related_name="flashcard_facts",
    )
    section = models.CharField(max_length=20, choices=SECTION_CHOICES)
    lang = models.CharField(max_length=2, choices=LANG_CHOICES)
    # Source order within (ingredient, section, lang).
    order = models.PositiveSmallIntegerField()
    text = models.TextField()

    class Meta:
        ordering = ["ingredient_id", "section", "lang", "order"]
        constraints = [
            models.UniqueConstraint(
                fields=["ingredient", "section", "lang", "order"],
                name="flashcards_unique_fact_slot",
            ),
        ]
        indexes = [
            models.Index(fields=["section", "lang"], name="flashcards_fact_section_idx"),
        ]

    def __str__(self):
        return f"{self.ingredient_id}:{self.section}:{self.lang}#{self.order}"


class TopicProgress(models.Model):
    """How far a learner is through one study topic's deck (apps.lessons'
    clinical topics are the flashcard sub-categories): the topic's drugs are
    shown in a fixed order (apps.flashcards.decks), and `position` is how
    many of them this pass has answered. `known` / `hard` count this pass's
    answers for the end-of-deck summary; a restart clears all three."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="flashcard_topic_progress",
    )
    topic_key = models.CharField(max_length=60)
    position = models.PositiveSmallIntegerField(default=0)
    known = models.PositiveSmallIntegerField(default=0)
    hard = models.PositiveSmallIntegerField(default=0)
    finished_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic_key"], name="flashcards_unique_user_topic"
            ),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.topic_key} {self.position}"
