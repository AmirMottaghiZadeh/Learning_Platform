from django.conf import settings
from django.db import models

class FlashcardState(models.Model):
    REVIEW_STATE_NEW = "new"
    REVIEW_STATE_LEARNING = "learning"
    REVIEW_STATE_REVIEW = "review"
    REVIEW_STATE_MATURE = "mature"
    REVIEW_STATE_SUSPENDED = "suspended"
    REVIEW_STATE_CHOICES = [
        (REVIEW_STATE_NEW, "New"),
        (REVIEW_STATE_LEARNING, "Learning"),
        (REVIEW_STATE_REVIEW, "Review"),
        (REVIEW_STATE_MATURE, "Mature"),
        (REVIEW_STATE_SUSPENDED, "Suspended"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="flashcard_states")
    knowledge_source = models.ForeignKey(
        "learning.KnowledgeSource",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="flashcard_states",
    )
    source = models.ForeignKey("drugs.DrugQuestionSource", on_delete=models.CASCADE, null=True, blank=True)
    box = models.PositiveIntegerField(default=1)
    review_state = models.CharField(
        max_length=20,
        choices=REVIEW_STATE_CHOICES,
        default=REVIEW_STATE_NEW,
    )
    interval_days = models.PositiveIntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    lapse_count = models.PositiveIntegerField(default=0)
    last_rating = models.CharField(max_length=20, blank=True)
    schedule_rule_version = models.CharField(max_length=80, blank=True)
    due_at = models.DateTimeField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("user", "source")]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "knowledge_source"],
                name="unique_user_knowledge_flashcard",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "box", "review_state"]),
        ]

class FlashcardReview(models.Model):
    state = models.ForeignKey(FlashcardState, on_delete=models.CASCADE, related_name="reviews")
    rating = models.CharField(max_length=20)
    box_before = models.PositiveIntegerField(default=1)
    box_after = models.PositiveIntegerField(default=1)
    interval_days = models.PositiveIntegerField(default=0)
    scheduled_due_at = models.DateTimeField(null=True, blank=True)
    rule_version = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
