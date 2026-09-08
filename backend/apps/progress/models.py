"""Per-learner progress: streak, XP, study minutes, recurring mistakes, plan.

Quiz and flashcard apps (Phase 3c) call the helpers in `services.py` to bump
these; on their own the endpoints just report what is here.
"""

from django.conf import settings
from django.db import models
from django.utils import timezone


def default_week():
    return [False] * 7


class LearnerProgress(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="progress",
    )
    xp = models.PositiveIntegerField(default=0)
    streak_days = models.PositiveIntegerField(default=0)
    last_study_date = models.DateField(null=True, blank=True)

    total_quizzes = models.PositiveIntegerField(default=0)
    total_reviews = models.PositiveIntegerField(default=0)
    total_minutes = models.PositiveIntegerField(default=0)
    quiz_answers = models.PositiveIntegerField(default=0)
    quiz_correct = models.PositiveIntegerField(default=0)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"progress<{self.user_id}> xp={self.xp} streak={self.streak_days}"

    @property
    def accuracy_pct(self):
        return round(100 * self.quiz_correct / self.quiz_answers) if self.quiz_answers else 0


class DailyStudy(models.Model):
    """Minutes studied on one calendar day; source for the weekly chart."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="daily_study",
    )
    day = models.DateField(default=timezone.localdate)
    minutes = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["-day"]
        constraints = [
            models.UniqueConstraint(fields=["user", "day"], name="progress_unique_user_day"),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.day} {self.minutes}m"


class Mistake(models.Model):
    """A topic the learner keeps getting wrong. Bumped by the quiz app."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="mistakes",
    )
    topic_key = models.CharField(max_length=60)
    topic_fa = models.CharField(max_length=120)
    topic_en = models.CharField(max_length=120)
    detail_fa = models.TextField(blank=True)
    detail_en = models.TextField(blank=True)
    count = models.PositiveIntegerField(default=1)
    resolved = models.BooleanField(default=False)
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-count", "-last_seen"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "topic_key"], name="progress_unique_user_topic"
            ),
        ]

    def __str__(self):
        return f"{self.user_id}:{self.topic_key} x{self.count}"


class StudyPlan(models.Model):
    """Which weekday(s) the learner plans to study. Index 0..6 = Sat..Fri."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_plan",
    )
    days = models.JSONField(default=default_week)
    reminders_enabled = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"plan<{self.user_id}> {self.days}"
