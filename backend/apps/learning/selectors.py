from datetime import timedelta

from django.db.models import Count, Q, Sum
from django.utils import timezone

from apps.flashcards.models import FlashcardReview, FlashcardState
from apps.games.models import GameAnswer, GameSession, Mistake, QuizReminder
from apps.league.services import get_current_season, get_user_league_rank

from .models import LearnerProgress, LearningEventRecord
from .services import (
    EVENT_MISTAKE_CREATED,
    EVENT_QUESTION_ANSWERED,
    EVENT_REVIEW_COMPLETED,
)


def progress_queryset_for_user(user, *, product_id=None):
    qs = (
        LearnerProgress.objects
        .filter(learner=user)
        .select_related("topic")
        .order_by("topic__label", "topic__key")
    )
    if product_id:
        qs = qs.filter(product_id=product_id)
    return qs


def get_learning_progress_summary(user, *, product_id=None):
    progress_qs = progress_queryset_for_user(user, product_id=product_id)
    totals = progress_qs.aggregate(
        questions_answered=Sum("questions_answered"),
        correct_answers=Sum("correct_answers"),
        xp=Sum("xp"),
        review_count=Sum("review_count"),
        mistake_count=Sum("mistake_count"),
    )
    questions_answered = totals["questions_answered"] or 0
    correct_answers = totals["correct_answers"] or 0
    accuracy_percent = round((correct_answers / questions_answered) * 100) if questions_answered else 0

    flashcards = FlashcardState.objects.filter(user=user)
    mistakes = Mistake.objects.filter(user=user)
    sessions = GameSession.objects.filter(user=user)
    if product_id:
        flashcards = flashcards.filter(knowledge_source__product_id=product_id)
        mistakes = mistakes.filter(knowledge_source__product_id=product_id)

    leitner_flashcards = flashcards.filter(box__gte=1).exclude(
        review_state=FlashcardState.REVIEW_STATE_SUSPENDED
    )
    due_flashcards = leitner_flashcards.count()
    latest_session = sessions.order_by("-started_at").first()

    return {
        "product_id": product_id,
        "questions_answered": questions_answered,
        "correct_answers": correct_answers,
        "accuracy_percent": accuracy_percent,
        "xp": totals["xp"] or 0,
        "review_count": totals["review_count"] or 0,
        "mistake_count": mistakes.count() if not product_id else totals["mistake_count"] or 0,
        "due_flashcards": due_flashcards,
        "active_flashcards": due_flashcards,
        "current_streak": latest_session.streak if latest_session else 0,
        "weak_topics": get_weak_topics(user, product_id=product_id, limit=5),
    }


def get_weak_topics(user, *, product_id=None, limit=10):
    progress_qs = progress_queryset_for_user(user, product_id=product_id)
    due_flashcard_filters = (
        Q(topic__knowledge_sources__flashcard_states__user=user)
        & Q(topic__knowledge_sources__flashcard_states__box__gte=1)
        & ~Q(
            topic__knowledge_sources__flashcard_states__review_state=FlashcardState.REVIEW_STATE_SUSPENDED
        )
    )
    if product_id:
        due_flashcard_filters &= Q(topic__knowledge_sources__product_id=product_id)

    weak_progress = (
        progress_qs
        .filter(wrong_answers__gt=0)
        .annotate(
            due_flashcards=Count(
                "topic__knowledge_sources__flashcard_states",
                filter=due_flashcard_filters,
            )
        )
        .order_by("-wrong_answers", "topic__label")[:limit]
    )
    weak_topics = []
    for progress in weak_progress:
        weak_topics.append(
            {
                "topic_key": progress.topic.key,
                "topic_label": progress.topic.label,
                "questions_answered": progress.questions_answered,
                "accuracy_percent": progress.accuracy_percent,
                "wrong_answers": progress.wrong_answers,
                "review_count": progress.review_count,
                "mistake_count": progress.mistake_count,
                "due_flashcards": progress.due_flashcards,
                "xp": progress.xp,
                "mastery_state": progress.mastery_state,
            }
        )
    return weak_topics


def get_learning_recommendations(user, *, product_id="pharmexa", summary=None):
    if summary is None:
        summary = get_learning_progress_summary(user, product_id=product_id)
    recommendations = []

    if summary["due_flashcards"] > 0:
        recommendations.append(
            {
                "id": "review-due-flashcards",
                "priority": 10,
                "action": "review_flashcards",
                "title": "مرور فلش‌کارت‌های آماده",
                "reason": "الان بهترین زمان برای مرور کارت‌های زمان‌دار است.",
                "topic_key": None,
                "count": summary["due_flashcards"],
            }
        )

    if summary["weak_topics"]:
        weakest = summary["weak_topics"][0]
        recommendations.append(
            {
                "id": f"practice-weak-topic-{weakest['topic_key']}",
                "priority": 20,
                "action": "start_topic_quiz",
                "title": "تمرین موضوع ضعیف‌تر",
                "reason": f"در {weakest['topic_label']} بیشترین خطای اخیر ثبت شده است.",
                "topic_key": weakest["topic_key"],
                "count": weakest["wrong_answers"],
            }
        )

    if summary["mistake_count"] > 0:
        recommendations.append(
            {
                "id": "review-mistakes",
                "priority": 30,
                "action": "review_mistakes",
                "title": "مرور اشتباهات",
                "reason": "اشتباهات، مهم‌ترین سیگنال برای تمرین هدفمند هستند.",
                "topic_key": None,
                "count": summary["mistake_count"],
            }
        )

    if not recommendations:
        recommendations.append(
            {
                "id": "continue-learning",
                "priority": 40,
                "action": "start_quiz",
                "title": "ادامه مسیر یادگیری",
                "reason": "یک آزمون کوتاه، روند پیشرفت امروز را فعال نگه می‌دارد.",
                "topic_key": None,
                "count": 0,
            }
        )

    return sorted(recommendations, key=lambda item: item["priority"])


def get_activity_summary(user, *, product_id="pharmexa"):
    sessions = GameSession.objects.filter(user=user, is_finished=True).order_by("-finished_at")
    answers = GameAnswer.objects.filter(session__user=user)
    if product_id and product_id != "pharmexa":
        sessions = sessions.none()
        answers = answers.none()

    answered_questions = answers.count()
    correct_answers = answers.filter(is_correct=True).count()
    wrong_answers = max(0, answered_questions - correct_answers)
    flashcard_reviews = FlashcardReview.objects.filter(state__user=user)
    if product_id:
        flashcard_reviews = flashcard_reviews.filter(state__knowledge_source__product_id=product_id)
    reminders = QuizReminder.objects.filter(user=user)

    total_seconds = 0
    for session in sessions:
        if not session.started_at:
            continue
        finished_at = session.finished_at or session.started_at
        total_seconds += max(
            0,
            int((finished_at - session.started_at).total_seconds()) - session.total_paused_seconds,
        )

    return {
        "completed_quizzes": sessions.count(),
        "answered_questions": answered_questions,
        "correct_answers": correct_answers,
        "wrong_answers": wrong_answers,
        "quiz_accuracy_percent": round((correct_answers / answered_questions) * 100) if answered_questions else 0,
        "flashcard_reviews": flashcard_reviews.count(),
        "saved_reminders": reminders.count(),
        "pending_reminders": reminders.filter(is_reviewed=False).count(),
        "total_study_minutes": round(total_seconds / 60),
    }


def get_learning_dashboard(user, *, product_id="pharmexa"):
    season = get_current_season(product_id=product_id)
    rank = get_user_league_rank(user, product_id=product_id, season_key=season.key)
    summary = get_learning_progress_summary(user, product_id=product_id)
    return {
        "product_id": product_id,
        "summary": summary,
        "activity_summary": get_activity_summary(user, product_id=product_id),
        "recommendations": get_learning_recommendations(
            user,
            product_id=product_id,
            summary=summary,
        ),
        "league": {
            "season_key": season.key,
            "rank": rank["rank"],
            "total_participants": rank["total_participants"],
        },
    }


def get_learning_statistics(user, *, product_id="pharmexa", days=7):
    days = min(max(int(days), 1), 90)
    summary = get_learning_progress_summary(user, product_id=product_id)
    topics = list(progress_queryset_for_user(user, product_id=product_id))
    start_date = timezone.localdate() - timedelta(days=days - 1)
    end_date = timezone.localdate()
    daily = {
        start_date + timedelta(days=offset): {
            "date": start_date + timedelta(days=offset),
            "questions_answered": 0,
            "reviews_completed": 0,
            "mistakes_created": 0,
            "xp": 0,
        }
        for offset in range(days)
    }

    events = LearningEventRecord.objects.filter(
        learner=user,
        product_id=product_id,
        occurred_at__date__gte=start_date,
        event_type__in=[
            EVENT_QUESTION_ANSWERED,
            EVENT_REVIEW_COMPLETED,
            EVENT_MISTAKE_CREATED,
        ],
    )
    for event in events:
        event_date = timezone.localtime(event.occurred_at).date()
        if event_date not in daily:
            continue
        if event.event_type == EVENT_QUESTION_ANSWERED:
            daily[event_date]["questions_answered"] += 1
            daily[event_date]["xp"] += max(0, int(event.payload.get("xp_delta") or 0))
        elif event.event_type == EVENT_REVIEW_COMPLETED:
            daily[event_date]["reviews_completed"] += 1
        elif event.event_type == EVENT_MISTAKE_CREATED:
            daily[event_date]["mistakes_created"] += 1

    return {
        "product_id": product_id,
        "days": days,
        "start_date": start_date,
        "end_date": end_date,
        "summary": summary,
        "activity_summary": get_activity_summary(user, product_id=product_id),
        "topics": topics,
        "daily_activity": list(daily.values()),
        "weak_topics": get_weak_topics(user, product_id=product_id, limit=10),
    }
