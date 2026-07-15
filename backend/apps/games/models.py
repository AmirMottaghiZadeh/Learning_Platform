from django.conf import settings
from django.db import models


class GameSession(models.Model):
    MODE_CHOICES = [
        ("random", "Random"),
        ("category", "Category"),
        ("all", "All"),
        ("mistakes", "Mistakes"),
        ("league", "League"),
    ]
    STATUS_ACTIVE = "active"
    STATUS_PAUSED = "paused"
    STATUS_FINISHED = "finished"
    STATUS_ARCHIVED = "archived"
    STATUS_CHOICES = [
        (STATUS_ACTIVE, "Active"),
        (STATUS_PAUSED, "Paused"),
        (STATUS_FINISHED, "Finished"),
        (STATUS_ARCHIVED, "Archived"),
    ]
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="game_sessions")
    topic_key = models.CharField(max_length=50)
    target_category_key = models.CharField(max_length=80, blank=True)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    total_questions = models.PositiveIntegerField(default=0)
    timer_seconds = models.PositiveIntegerField(default=30)
    score = models.IntegerField(default=0)
    correct_count = models.PositiveIntegerField(default=0)
    streak = models.PositiveIntegerField(default=0)
    time_remaining_total = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    paused_at = models.DateTimeField(null=True, blank=True)
    total_paused_seconds = models.PositiveIntegerField(default=0)
    finished_at = models.DateTimeField(null=True, blank=True)
    is_finished = models.BooleanField(default=False)


class GameQuestion(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="questions")
    knowledge_source = models.ForeignKey(
        "learning.KnowledgeSource",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="game_questions",
    )
    source = models.ForeignKey("drugs.DrugQuestionSource", on_delete=models.PROTECT, null=True, blank=True)
    order = models.PositiveIntegerField()
    options = models.JSONField(default=list)
    question_started_at = models.DateTimeField(null=True, blank=True)
    paused_seconds = models.PositiveIntegerField(default=0)
    timer_extension_seconds = models.PositiveIntegerField(default=0)
    timer_extension_used = models.BooleanField(default=False)
    timer_extended_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = [("session", "order")]
        ordering = ["order"]


class GameAnswer(models.Model):
    session = models.ForeignKey(GameSession, on_delete=models.CASCADE, related_name="answers")
    question = models.OneToOneField(GameQuestion, on_delete=models.CASCADE, related_name="answer")
    selected_answer = models.TextField(blank=True)
    correct_answer = models.TextField()
    is_correct = models.BooleanField()
    time_expired = models.BooleanField(default=False)
    remaining_seconds = models.PositiveIntegerField(default=0)
    score_delta = models.IntegerField(default=0)
    xp_delta = models.IntegerField(default=0)
    scoring_rule_version = models.CharField(max_length=80, default="mvp-scoring-v1")
    client_answered_at = models.DateTimeField(null=True, blank=True)
    answered_at = models.DateTimeField(auto_now_add=True)


class Mistake(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="mistakes")
    topic_key = models.CharField(max_length=50)
    knowledge_source = models.ForeignKey(
        "learning.KnowledgeSource",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="mistakes",
    )
    source = models.ForeignKey("drugs.DrugQuestionSource", on_delete=models.CASCADE, null=True, blank=True)
    wrong_count = models.PositiveIntegerField(default=0)
    last_wrong_answer = models.TextField(blank=True)
    last_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("user", "topic_key", "source")]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic_key", "knowledge_source"],
                name="unique_user_topic_knowledge_mistake",
            ),
        ]


class QuizReminder(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_reminders",
    )
    game_session = models.ForeignKey(
        GameSession,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reminders",
    )
    game_question = models.ForeignKey(
        GameQuestion,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reminders",
    )
    knowledge_source = models.ForeignKey(
        "learning.KnowledgeSource",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="quiz_reminders",
    )
    question_type = models.CharField(max_length=50)
    prompt = models.TextField()
    selected_answer = models.TextField(blank=True)
    correct_answer = models.TextField()
    explanation = models.TextField(blank=True)
    options = models.JSONField(default=list, blank=True)
    is_reviewed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["is_reviewed", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "game_question"],
                name="unique_user_game_question_reminder",
            ),
        ]
