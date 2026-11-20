from django.conf import settings
from django.db import models


class ChapterProgress(models.Model):
    """A learner's visit to one lesson chapter (an ATC L2 subgroup).

    Only `scroll_pct`/`last_opened_at` live here now — whether a *drug* has
    been read is tracked globally in `ReadDrug`, not per chapter, because the
    same ingredient legitimately appears in more than one ATC L2 chapter
    (aspirin: A01 dental, B01 antithrombotic, N02 analgesic) and its content
    is identical wherever it's reached from; a learner who read it under one
    chapter should see it already read under the others, not re-read it.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chapter_progress",
    )
    atc_code = models.CharField(max_length=3)  # L2 code, e.g. "N02"
    scroll_pct = models.PositiveSmallIntegerField(default=0)
    last_opened_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-last_opened_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "atc_code"],
                name="lessons_unique_user_chapter",
            ),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.atc_code}"


class ReadDrug(models.Model):
    """One drug a learner has read to completion, independent of which
    chapter they reached it through. See `ChapterProgress` for why this is
    global rather than per-chapter.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="read_drugs",
    )
    ingredient_slug = models.CharField(max_length=255)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "ingredient_slug"],
                name="lessons_unique_user_read_drug",
            ),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.ingredient_slug}"
