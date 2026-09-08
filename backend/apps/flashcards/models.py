"""Leitner flashcards.

There is no card-content table: a card is a learner + an ingredient, and the
front/back are derived from the ingredient's profile at serialization time.
`box` is the Leitner level (1..5); `due_at` is when it next comes up.
"""

from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone

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
