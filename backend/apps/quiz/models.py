from django.conf import settings
from django.db import models

CATEGORY_CHOICES = [
    ("general", "General pharmacology"),
    ("antibiotics", "Antibiotics"),
    ("cardio", "Cardiovascular"),
    ("interactions", "Drug interactions"),
]
COUNT_CHOICES = [5, 10, 15, 20]


class QuizSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_sessions",
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    question_count = models.PositiveSmallIntegerField()
    score = models.PositiveSmallIntegerField(default=0)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-started_at"]

    def __str__(self):
        return f"quiz<{self.user_id}> {self.category} {self.score}/{self.question_count}"

    @property
    def is_finished(self):
        return self.finished_at is not None


class QuizQuestion(models.Model):
    session = models.ForeignKey(
        QuizSession, on_delete=models.CASCADE, related_name="questions"
    )
    order = models.PositiveSmallIntegerField()
    prompt_fa = models.CharField(max_length=300)
    prompt_en = models.CharField(max_length=300)
    options_fa = models.JSONField(default=list)
    options_en = models.JSONField(default=list)
    correct_index = models.PositiveSmallIntegerField()
    subject_slug = models.CharField(max_length=280, blank=True)

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["session", "order"], name="quiz_unique_session_order"
            ),
        ]


class QuizAnswer(models.Model):
    question = models.OneToOneField(
        QuizQuestion, on_delete=models.CASCADE, related_name="answer"
    )
    selected_index = models.PositiveSmallIntegerField()
    is_correct = models.BooleanField()
    answered_at = models.DateTimeField(auto_now_add=True)
    client_answered_at = models.DateTimeField(null=True, blank=True)
