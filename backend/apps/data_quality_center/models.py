from django.conf import settings
from django.db import models


class SectionEdit(models.Model):
    """Append-only record of one edit to an ingredient section's summaries.

    The Data Quality Center only edits `summary_fa` / `summary_en` on
    `drugs.IngredientProfileSection`; the raw label text stays read-only.
    """

    section = models.ForeignKey(
        "drugs.IngredientProfileSection",
        on_delete=models.CASCADE,
        related_name="edits",
    )
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="section_edits",
    )
    editor_username = models.CharField(max_length=150, blank=True)

    ingredient_name = models.CharField(max_length=255)
    field = models.CharField(max_length=40)
    before_fa = models.TextField(blank=True)
    after_fa = models.TextField(blank=True)
    before_en = models.TextField(blank=True)
    after_en = models.TextField(blank=True)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["-created_at"], name="dqc_edit_recent_idx")]

    def __str__(self):
        return f"{self.ingredient_name}.{self.field} by {self.editor_username}"

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValueError("SectionEdit rows are append-only.")
        return super().save(*args, **kwargs)
