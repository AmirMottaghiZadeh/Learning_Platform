from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from apps.flashcards.models import FlashcardState
from apps.games.models import GameSession, Mistake
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

    due_flashcards = flashcards.filter(due_at__lte=timezone.now()).count()
    active_flashcards = flashcards.exclude(review_state=FlashcardState.REVIEW_STATE_SUSPENDED).count()
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
        "active_flashcards": active_flashcards,
        "current_streak": latest_session.streak if latest_session else 0,
        "weak_topics": get_weak_topics(user, product_id=product_id, limit=5),
    }


def get_weak_topics(user, *, product_id=None, limit=10):
    progress_qs = progress_queryset_for_user(user, product_id=product_id)
    weak_topics = []
    for progress in progress_qs.filter(wrong_answers__gt=0).order_by("-wrong_answers", "topic__label")[:limit]:
        flashcards = FlashcardState.objects.filter(user=user, knowledge_source__topic=progress.topic)
        if product_id:
            flashcards = flashcards.filter(knowledge_source__product_id=product_id)
        due_flashcards = flashcards.filter(due_at__lte=timezone.now()).count()
        weak_topics.append(
            {
                "topic_key": progress.topic.key,
                "topic_label": progress.topic.label,
                "questions_answered": progress.questions_answered,
                "accuracy_percent": progress.accuracy_percent,
                "wrong_answers": progress.wrong_answers,
                "review_count": progress.review_count,
                "mistake_count": progress.mistake_count,
                "due_flashcards": due_flashcards,
                "xp": progress.xp,
                "mastery_state": progress.mastery_state,
            }
        )
    return weak_topics


def get_learning_recommendations(user, *, product_id="k_game"):
    summary = get_learning_progress_summary(user, product_id=product_id)
    recommendations = []

    if summary["due_flashcards"] > 0:
        recommendations.append(
            {
                "id": "review-due-flashcards",
                "priority": 10,
                "action": "review_flashcards",
                "title": "Review due flashcards",
                "reason": "Spaced repetition items are due now.",
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
                "title": "Practice weak topic",
                "reason": f"{weakest['topic_label']} has the most recent mistakes.",
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
                "title": "Review mistakes",
                "reason": "Mistakes are active learning signals.",
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
                "title": "Continue learning",
                "reason": "Start a short quiz to keep progress moving.",
                "topic_key": None,
                "count": 0,
            }
        )

    return sorted(recommendations, key=lambda item: item["priority"])


def get_learning_dashboard(user, *, product_id="k_game"):
    season = get_current_season(product_id=product_id)
    rank = get_user_league_rank(user, product_id=product_id, season_key=season.key)
    return {
        "product_id": product_id,
        "summary": get_learning_progress_summary(user, product_id=product_id),
        "recommendations": get_learning_recommendations(user, product_id=product_id),
        "league": {
            "season_key": season.key,
            "rank": rank["rank"],
            "total_participants": rank["total_participants"],
        },
    }


def get_learning_statistics(user, *, product_id="k_game", days=7):
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
        "topics": topics,
        "daily_activity": list(daily.values()),
        "weak_topics": get_weak_topics(user, product_id=product_id, limit=10),
    }
