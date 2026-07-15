import uuid

from django.conf import settings
from django.db import models


class LearningTopic(models.Model):
    product_id = models.CharField(max_length=80, default="platform")
    key = models.CharField(max_length=80)
    label = models.CharField(max_length=160)
    detail = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("product_id", "key")]
        indexes = [
            models.Index(fields=["product_id", "key"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.label


class LearningObject(models.Model):
    product_id = models.CharField(max_length=80, default="platform")
    external_id = models.CharField(max_length=120)
    display_name = models.TextField()
    subtitle = models.CharField(max_length=255, blank=True)
    topic = models.ForeignKey(
        LearningTopic,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_objects",
    )
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("product_id", "external_id")]
        indexes = [
            models.Index(fields=["product_id", "external_id"]),
            models.Index(fields=["product_id", "is_active"]),
        ]

    def __str__(self):
        return self.display_name


class KnowledgeSource(models.Model):
    product_id = models.CharField(max_length=80, default="platform")
    external_id = models.CharField(max_length=255)
    learning_object = models.ForeignKey(
        LearningObject,
        on_delete=models.CASCADE,
        related_name="knowledge_sources",
    )
    topic = models.ForeignKey(
        LearningTopic,
        on_delete=models.CASCADE,
        related_name="knowledge_sources",
    )
    source_type = models.CharField(max_length=80)
    prompt = models.TextField()
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("product_id", "external_id")]
        indexes = [
            models.Index(fields=["product_id", "external_id"]),
            models.Index(fields=["product_id", "source_type", "is_active"]),
            models.Index(fields=["product_id", "topic", "is_active"]),
        ]

    def __str__(self):
        return self.prompt[:80]


class LearningEventRecord(models.Model):
    event_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    event_type = models.CharField(max_length=120)
    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="learning_events",
    )
    product_id = models.CharField(max_length=80)
    occurred_at = models.DateTimeField()
    correlation_id = models.CharField(max_length=120, blank=True)
    source = models.CharField(max_length=120, default="backend")
    payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["product_id", "event_type", "occurred_at"]),
            models.Index(fields=["learner", "occurred_at"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.event_type} ({self.product_id})"


class LearnerProgress(models.Model):
    MASTERY_UNSEEN = "unseen"
    MASTERY_SEEN = "seen"
    MASTERY_PRACTICING = "practicing"
    MASTERY_REVIEWING = "reviewing"
    MASTERY_MASTERED = "mastered"
    MASTERY_CHOICES = [
        (MASTERY_UNSEEN, "Unseen"),
        (MASTERY_SEEN, "Seen"),
        (MASTERY_PRACTICING, "Practicing"),
        (MASTERY_REVIEWING, "Reviewing"),
        (MASTERY_MASTERED, "Mastered"),
    ]

    learner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="learning_progress",
    )
    product_id = models.CharField(max_length=80)
    topic = models.ForeignKey(
        LearningTopic,
        on_delete=models.CASCADE,
        related_name="learner_progress",
    )
    questions_answered = models.PositiveIntegerField(default=0)
    correct_answers = models.PositiveIntegerField(default=0)
    wrong_answers = models.PositiveIntegerField(default=0)
    timed_out_answers = models.PositiveIntegerField(default=0)
    xp = models.IntegerField(default=0)
    review_count = models.PositiveIntegerField(default=0)
    mistake_count = models.PositiveIntegerField(default=0)
    mastery_state = models.CharField(
        max_length=20,
        choices=MASTERY_CHOICES,
        default=MASTERY_UNSEEN,
    )
    last_activity_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["learner", "product_id", "topic"],
                name="unique_learner_product_topic_progress",
            ),
        ]
        indexes = [
            models.Index(fields=["learner", "product_id"]),
            models.Index(fields=["learner", "mastery_state"]),
            models.Index(fields=["product_id", "topic"]),
        ]

    @property
    def accuracy_percent(self):
        if not self.questions_answered:
            return 0
        return round((self.correct_answers / self.questions_answered) * 100)

    def __str__(self):
        return f"{self.learner_id}:{self.product_id}:{self.topic.key}"
