"""Leitner flashcards.

A card is a learner + an ingredient: `box` is the Leitner level (1..5),
`due_at` when it next comes up. What the card says lives in FlashcardFact --
each drug's facts in the five card sections (apps.flashcards.sections),
extracted once by the build_flashcards command rather than re-derived from
the profile summaries on every request.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

from .sections import SECTION_CHOICES

# Days a card waits after landing in each box (index 0 unused).
BOX_INTERVAL_DAYS = {1: 0, 2: 3, 3: 7, 4: 16, 5: 35}
MAX_BOX = 5


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
    box = models.PositiveSmallIntegerField(default=1)
    due_at = models.DateTimeField(default=timezone.now)
    times_seen = models.PositiveIntegerField(default=0)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["due_at", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "ingredient"], name="flashcards_unique_user_ingredient"
            ),
        ]
        indexes = [models.Index(fields=["user", "due_at"], name="flashcards_user_due_idx")]

    def __str__(self):
        return f"{self.user_id}:{self.ingredient_id} box{self.box}"

    def review(self, rating):
        """Apply an 'easy' / 'hard' review and reschedule."""
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
