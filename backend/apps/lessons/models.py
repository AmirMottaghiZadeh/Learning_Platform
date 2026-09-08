from django.conf import settings
from django.db import models


class ChapterProgress(models.Model):
    """A learner's progress through one lesson chapter (an ATC L2 subgroup).

    `read_drug_slugs` is the set of ingredient slugs the learner has opened in
    this chapter; `done / total` on the lessons list is derived from it.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chapter_progress",
    )
    atc_code = models.CharField(max_length=3)  # L2 code, e.g. "N02"
    read_drug_slugs = models.JSONField(default=list, blank=True)
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
        return f"{self.user_id}:{self.atc_code} ({len(self.read_drug_slugs)} read)"

    def mark_read(self, slug):
        if slug and slug not in self.read_drug_slugs:
            self.read_drug_slugs = [*self.read_drug_slugs, slug]
