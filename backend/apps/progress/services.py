"""Write helpers other apps call to move a learner's progress forward."""

from datetime import timedelta

from django.db.models import F
from django.utils import timezone

from .models import DailyStudy, LearnerProgress, Mistake, StudyPlan

XP_PER_CORRECT_ANSWER = 10
XP_PER_REVIEW = 4


def get_progress(user):
    progress, _ = LearnerProgress.objects.get_or_create(user=user)
    return progress


def get_plan(user):
    plan, _ = StudyPlan.objects.get_or_create(user=user)
    return plan


def _touch_streak(progress, today):
    if progress.last_study_date == today:
        return
    if progress.last_study_date == today - timedelta(days=1):
        progress.streak_days += 1
    else:
        progress.streak_days = 1
    progress.last_study_date = today


def record_study(user, *, minutes=0, reviews=0, quizzes=0, xp=0):
    """Log study activity for today and roll the streak / totals forward."""
    today = timezone.localdate()
    progress = get_progress(user)
    _touch_streak(progress, today)
    progress.total_minutes += max(0, minutes)
    progress.total_reviews += max(0, reviews)
    progress.total_quizzes += max(0, quizzes)
    progress.xp += max(0, xp)
    progress.save()

    if minutes:
        row, created = DailyStudy.objects.get_or_create(user=user, day=today)
        DailyStudy.objects.filter(pk=row.pk).update(minutes=F("minutes") + minutes)
    return progress


def record_quiz_answers(user, *, answered, correct):
    progress = get_progress(user)
    progress.quiz_answers += max(0, answered)
    progress.quiz_correct += max(0, correct)
    progress.save(update_fields=["quiz_answers", "quiz_correct", "updated_at"])
    return progress


def bump_mistake(user, *, topic_key, topic_fa, topic_en, detail_fa="", detail_en=""):
    mistake, created = Mistake.objects.get_or_create(
        user=user,
        topic_key=topic_key,
        defaults={
            "topic_fa": topic_fa,
            "topic_en": topic_en,
            "detail_fa": detail_fa,
            "detail_en": detail_en,
        },
    )
    if not created:
        mistake.count += 1
        mistake.resolved = False
        if detail_fa:
            mistake.detail_fa = detail_fa
        if detail_en:
            mistake.detail_en = detail_en
        mistake.save(update_fields=["count", "resolved", "detail_fa", "detail_en", "last_seen"])
    return mistake
