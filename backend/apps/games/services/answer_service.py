from django.db import transaction
from django.utils import timezone

from apps.games.contracts import ScoringContext
from apps.games.models import GameAnswer, Mistake
from apps.games.selectors import get_game_question
from apps.games.services.assessment_service import evaluate_answer
from apps.games.services.lifecycle_service import question_remaining_seconds
from apps.games.services.scoring_service import calculate_score
from apps.learning.services import (
    EVENT_MISTAKE_CREATED,
    record_answer_outcome,
    record_learning_event,
)


@transaction.atomic
def answer_question(user, session, *, question_id, selected_answer, client_answered_at=None):
    if session.user_id != user.id:
        raise PermissionError("Not your game.")

    if session.is_finished or session.status == session.STATUS_FINISHED:
        raise ValueError("Game already finished.")
    if session.status == session.STATUS_PAUSED:
        raise ValueError("Game is paused.")
    if session.status != session.STATUS_ACTIVE:
        raise ValueError("Game is not active.")

    question = get_game_question(session=session, question_id=question_id)

    if GameAnswer.objects.filter(question=question).exists():
        raise ValueError("Question already answered.")

    if not question.question_started_at:
        raise ValueError("Question is not active.")

    now = timezone.now()

    remaining_seconds = question_remaining_seconds(session, question, now=now)

    source = question.knowledge_source or question.source
    correct_answer = source.correct_answer
    assessment = evaluate_answer(
        selected_answer=selected_answer,
        correct_answer=correct_answer,
        remaining_seconds=remaining_seconds,
        question_type=getattr(source, "source_type", None) or getattr(source, "question_type", None),
    )
    scoring = calculate_score(
        ScoringContext(
            is_correct=assessment.is_correct,
            time_expired=assessment.time_expired,
            remaining_seconds=assessment.remaining_seconds,
            streak=session.streak,
            mode=session.mode,
        )
    )

    if assessment.is_scored_correct:
        session.streak += 1
        session.correct_count += 1
        session.score += scoring.score_delta

        if session.mode == "league":
            session.time_remaining_total += remaining_seconds
    else:
        session.streak = 0

        mistake_lookup = {
            "user": user,
            "topic_key": session.topic_key,
        }
        if question.knowledge_source_id:
            mistake_lookup["knowledge_source"] = question.knowledge_source
        else:
            mistake_lookup["source"] = question.source

        mistake, mistake_created = Mistake.objects.get_or_create(**mistake_lookup)
        mistake.wrong_count += 1
        mistake.last_wrong_answer = selected_answer
        mistake.save(update_fields=["wrong_count", "last_wrong_answer", "last_at"])

        if mistake_created and question.knowledge_source_id:
            record_learning_event(
                event_type=EVENT_MISTAKE_CREATED,
                learner=user,
                product_id=question.knowledge_source.product_id,
                occurred_at=now,
                correlation_id=f"game-session:{session.id}",
                payload={
                    "mistake_id": mistake.id,
                    "session_id": session.id,
                    "question_id": question.id,
                    "topic_key": session.topic_key,
                    "knowledge_source_id": question.knowledge_source_id,
                    "learning_object_id": question.knowledge_source.learning_object_id,
                    "wrong_answer": selected_answer,
                },
            )

    answer = GameAnswer.objects.create(
        session=session,
        question=question,
        selected_answer=selected_answer,
        correct_answer=assessment.correct_answer,
        is_correct=assessment.is_correct,
        time_expired=assessment.time_expired,
        remaining_seconds=assessment.remaining_seconds,
        score_delta=scoring.score_delta,
        xp_delta=scoring.xp_delta,
        scoring_rule_version=scoring.rule_version,
        client_answered_at=client_answered_at,
    )

    if question.knowledge_source_id:
        record_answer_outcome(
            learner=user,
            knowledge_source=question.knowledge_source,
            answer=answer,
            session=session,
            occurred_at=now,
        )

    question.answered_at = now
    question.save(update_fields=["answered_at"])

    next_question = (
        session.questions
        .filter(answered_at__isnull=True)
        .exclude(id=question.id)
        .order_by("order")
        .first()
    )

    if next_question and not next_question.question_started_at:
        next_question.question_started_at = now
        next_question.save(update_fields=["question_started_at"])

    session.save(
        update_fields=[
            "score",
            "correct_count",
            "streak",
            "time_remaining_total",
        ]
    )

    return answer
