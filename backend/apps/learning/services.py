from django.db import transaction
from django.utils import timezone

from .models import LearnerProgress, LearningEventRecord


EVENT_QUESTION_ANSWERED = "QuestionAnswered"
EVENT_MISTAKE_CREATED = "MistakeCreated"
EVENT_REVIEW_SCHEDULED = "ReviewScheduled"
EVENT_REVIEW_COMPLETED = "ReviewCompleted"
EVENT_TOPIC_PROGRESS_UPDATED = "TopicProgressUpdated"
PROGRESS_RULE_VERSION = "mvp-topic-progress-v1"


def record_learning_event(
    *,
    event_type,
    learner,
    product_id,
    payload=None,
    occurred_at=None,
    correlation_id="",
    source="backend",
):
    return LearningEventRecord.objects.create(
        event_type=event_type,
        learner=learner,
        product_id=product_id,
        occurred_at=occurred_at or timezone.now(),
        correlation_id=correlation_id,
        source=source,
        payload=payload or {},
    )


def calculate_mastery_state(*, answered, accuracy_percent, review_count):
    if answered <= 0:
        return LearnerProgress.MASTERY_UNSEEN
    if answered < 3:
        return LearnerProgress.MASTERY_SEEN
    if accuracy_percent >= 85 and answered >= 10 and review_count >= 2:
        return LearnerProgress.MASTERY_MASTERED
    if review_count > 0 or accuracy_percent < 60:
        return LearnerProgress.MASTERY_REVIEWING
    return LearnerProgress.MASTERY_PRACTICING


def _update_mastery(progress):
    progress.mastery_state = calculate_mastery_state(
        answered=progress.questions_answered,
        accuracy_percent=progress.accuracy_percent,
        review_count=progress.review_count,
    )


@transaction.atomic
def record_answer_outcome(
    *,
    learner,
    knowledge_source,
    answer,
    session,
    occurred_at=None,
):
    occurred_at = occurred_at or timezone.now()
    progress, _ = LearnerProgress.objects.select_for_update().get_or_create(
        learner=learner,
        product_id=knowledge_source.product_id,
        topic=knowledge_source.topic,
    )

    progress.questions_answered += 1
    progress.xp += max(0, answer.xp_delta)
    progress.last_activity_at = occurred_at

    if answer.is_correct:
        progress.correct_answers += 1
    else:
        progress.wrong_answers += 1
        progress.mistake_count += 1

    if answer.time_expired:
        progress.timed_out_answers += 1

    _update_mastery(progress)
    progress.save(
        update_fields=[
            "questions_answered",
            "correct_answers",
            "wrong_answers",
            "timed_out_answers",
            "xp",
            "mistake_count",
            "mastery_state",
            "last_activity_at",
            "updated_at",
        ]
    )

    base_payload = {
        "session_id": session.id,
        "answer_id": answer.id,
        "question_id": answer.question_id,
        "topic_key": knowledge_source.topic.key,
        "knowledge_source_id": knowledge_source.id,
        "learning_object_id": knowledge_source.learning_object_id,
        "is_correct": answer.is_correct,
        "time_expired": answer.time_expired,
        "score_delta": answer.score_delta,
        "xp_delta": answer.xp_delta,
        "scoring_rule_version": answer.scoring_rule_version,
    }
    record_learning_event(
        event_type=EVENT_QUESTION_ANSWERED,
        learner=learner,
        product_id=knowledge_source.product_id,
        occurred_at=occurred_at,
        correlation_id=f"game-session:{session.id}",
        payload=base_payload,
    )
    record_learning_event(
        event_type=EVENT_TOPIC_PROGRESS_UPDATED,
        learner=learner,
        product_id=knowledge_source.product_id,
        occurred_at=occurred_at,
        correlation_id=f"game-session:{session.id}",
        payload={
            **base_payload,
            "progress_id": progress.id,
            "questions_answered": progress.questions_answered,
            "accuracy_percent": progress.accuracy_percent,
            "mastery_state": progress.mastery_state,
            "progress_rule_version": PROGRESS_RULE_VERSION,
        },
    )
    return progress


@transaction.atomic
def record_review_completed(*, learner, flashcard_state, review, occurred_at=None):
    occurred_at = occurred_at or timezone.now()
    knowledge_source = flashcard_state.knowledge_source
    if not knowledge_source:
        return None

    progress, _ = LearnerProgress.objects.select_for_update().get_or_create(
        learner=learner,
        product_id=knowledge_source.product_id,
        topic=knowledge_source.topic,
    )
    progress.review_count += 1
    progress.last_activity_at = occurred_at
    _update_mastery(progress)
    progress.save(update_fields=["review_count", "mastery_state", "last_activity_at", "updated_at"])

    payload = {
        "flashcard_state_id": flashcard_state.id,
        "review_id": review.id,
        "topic_key": knowledge_source.topic.key,
        "knowledge_source_id": knowledge_source.id,
        "learning_object_id": knowledge_source.learning_object_id,
        "rating": review.rating,
        "box_before": review.box_before,
        "box_after": review.box_after,
        "interval_days": review.interval_days,
        "due_at": review.scheduled_due_at.isoformat() if review.scheduled_due_at else None,
        "rule_version": review.rule_version,
        "progress_id": progress.id,
        "mastery_state": progress.mastery_state,
    }
    record_learning_event(
        event_type=EVENT_REVIEW_COMPLETED,
        learner=learner,
        product_id=knowledge_source.product_id,
        occurred_at=occurred_at,
        correlation_id=f"flashcard:{flashcard_state.id}",
        payload=payload,
    )
    record_learning_event(
        event_type=EVENT_TOPIC_PROGRESS_UPDATED,
        learner=learner,
        product_id=knowledge_source.product_id,
        occurred_at=occurred_at,
        correlation_id=f"flashcard:{flashcard_state.id}",
        payload={**payload, "progress_rule_version": PROGRESS_RULE_VERSION},
    )
    return progress
