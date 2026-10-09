from django.conf import settings
from django.db import models

COUNT_CHOICES = [5, 10, 15, 20]

BANK_FIELD_CHOICES = [
    ("indications_and_usage", "Indication"),
    ("adverse_reactions", "Adverse reactions"),
    ("warnings", "Warnings"),
    ("contraindications", "Absolute contraindication"),
    ("dosage_and_administration", "Dosing"),
]

# field -> (fa label, tone) -- tone matches the frontend's SectionTone /
# toneColors() used for drug-profile sections on the lesson screen, so a
# question's field tag (and the results breakdown) reads with the same
# color language a learner already knows from Lessons. Mechanism is
# deliberately not a question field (too abstract to quiz as a discrete
# fact); contraindications uses the same "deny" tone the lesson screen's own
# exam-point builder gives it (apps.lessons.selectors.EXAM_POINT_FIELDS).
FIELD_META = {
    "indications_and_usage": ("اندیکاسیون", "info"),
    "adverse_reactions": ("عوارض جانبی", "caution"),
    "warnings": ("هشدار", "caution"),
    "contraindications": ("منع مطلق", "deny"),
    "dosage_and_administration": ("دوز بندی", "info"),
}

DIFFICULTY_CHOICES = [
    ("medium", "Medium"),
    ("hard", "Hard"),
]

# QuizSession.category sentinel for a single-drug self-test (started from
# the end of that drug's lesson page) -- not a study-topic key, so
# mastery_selectors excludes it from the per-topic mastery map rather than
# showing a bogus "drug" topic row on the quiz overview screen.
DRUG_SESSION_CATEGORY = "drug"


class QuizSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_sessions",
    )
    # A clinical study-topic key from apps.lessons.data.study_topics (the
    # same taxonomy the Lessons tab browses by) -- no longer a small fixed
    # enum, since the question source is now the ingredient-level bank, not
    # a handful of hardcoded ATC-letter buckets. Validated against the real
    # topic list in QuizStartSerializer, not here.
    category = models.CharField(max_length=32)
    # An optional ATC L2 chapter within that topic, to narrow the pool
    # further (e.g. just "C03" instead of every antihypertensive class).
    atc_code = models.CharField(max_length=8, blank=True)
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


class BankQuestion(models.Model):
    """A rule-based (no LLM) MCQ pre-generated from one ingredient's clinical
    profile -- see apps.quiz.bank_generator. Persistent and reusable across
    sessions: apps.quiz.bank_selectors samples from here (filtered to a
    clinical study topic / ATC chapter) to build each QuizSession's
    questions, rather than generating them live.
    """

    ingredient = models.ForeignKey(
        "drugs.Ingredient", on_delete=models.CASCADE, related_name="bank_questions"
    )
    field = models.CharField(max_length=40, choices=BANK_FIELD_CHOICES)
    prompt_fa = models.TextField()
    options_fa = models.JSONField(default=list)
    correct_index = models.PositiveSmallIntegerField()
    # Rule-based, not a quality guess: "hard" means every distractor was
    # drawn from an ingredient in the subject's own ATC subclass (so picking
    # the right answer takes knowing the specific fact, not just recognizing
    # an unrelated drug class); "medium" means at least one was. A question
    # whose distractors are all from unrelated classes doesn't get generated
    # at all -- see apps.quiz.bank_generator.
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default="medium")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["ingredient", "field"])]

    def __str__(self):
        return f"{self.ingredient_id}:{self.field} {self.prompt_fa[:40]}"


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
    # Which clinical field this question was drawn from -- drives the
    # field tag on the question card and the results' per-field breakdown.
    # Blank for anything not sourced from the bank.
    field = models.CharField(max_length=40, choices=BANK_FIELD_CHOICES, blank=True)
    # The bank row this question was copied from, so the "explain more"
    # panel can pull sibling facts about the same (ingredient, field) --
    # null if that row is later deleted (a bank rebuild), or for questions
    # not sourced from the bank.
    bank_question = models.ForeignKey(
        BankQuestion, null=True, blank=True, on_delete=models.SET_NULL, related_name="+"
    )

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
