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
    """Which weekday(s) the learner plans to study (index 0..6 = Sat..Fri),
    plus which of three distinct planning models is active:

    - "none": free study. No items are generated; `topic_keys`/`daily_minutes`
      /`deadline` are unused.
    - "goal": a finite curriculum over `topic_keys` to be finished by
      `deadline`, studying `daily_minutes`/day on the enabled weekdays.
      Items for the whole remaining date range are generated up front by
      `services.regenerate_items` and only touched again on replanning.
    - "maintenance": no deadline -- a day's items are recomputed fresh each
      time (due flashcards, open mistakes, the stalest fully-read chapter)
      rather than pre-scheduled, since "what's due" changes daily.
    """

    MODE_NONE = "none"
    MODE_GOAL = "goal"
    MODE_MAINTENANCE = "maintenance"
    MODE_CHOICES = [
        (MODE_NONE, "Free study"),
        (MODE_GOAL, "Goal-based path"),
        (MODE_MAINTENANCE, "Ongoing review"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="study_plan",
    )
    days = models.JSONField(default=default_week)
    reminders_enabled = models.BooleanField(default=False)
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_NONE)
    topic_keys = models.JSONField(default=list, blank=True)
    daily_minutes = models.PositiveSmallIntegerField(default=30)
    deadline = models.DateField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"plan<{self.user_id}> {self.mode} {self.days}"


class StudyPlanItem(models.Model):
    """One scheduled task on one day of a `StudyPlan` -- the unit the Today
    screen renders. `topic_key`/`atc_code` are blank when the activity isn't
    scoped to one (e.g. a maintenance-mode mistake review)."""

    LESSON = "lesson"
    QUIZ = "quiz"
    FLASHCARDS = "flashcards"
    MISTAKE_REVIEW = "mistake_review"
    ACTIVITY_CHOICES = [
        (LESSON, "Lesson"),
        (QUIZ, "Quiz"),
        (FLASHCARDS, "Flashcards"),
        (MISTAKE_REVIEW, "Mistake review"),
    ]

    PENDING = "pending"
    DONE = "done"
    SKIPPED = "skipped"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (DONE, "Done"),
        (SKIPPED, "Skipped"),
    ]

    plan = models.ForeignKey(StudyPlan, on_delete=models.CASCADE, related_name="items")
    day = models.DateField()
    order = models.PositiveSmallIntegerField(default=0)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_CHOICES)
    topic_key = models.CharField(max_length=60, blank=True)
    atc_code = models.CharField(max_length=3, blank=True)
    estimated_minutes = models.PositiveSmallIntegerField(default=10)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING)
    reason_fa = models.CharField(max_length=200, blank=True)
    reason_en = models.CharField(max_length=200, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["day", "order"]

    def __str__(self):
        return f"{self.plan_id}:{self.day} {self.activity_type}#{self.order} ({self.status})"
