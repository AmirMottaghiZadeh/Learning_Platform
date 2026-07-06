from django.db import transaction
from django.utils import timezone

from apps.games.models import GameSession
from apps.games.selectors import get_current_question

QUESTION_TIMER_EXTENSION_SECONDS = 30
QUESTION_TIMER_MAX_SECONDS = 60


def ensure_active_session(session: GameSession):
    if session.is_finished or session.status == GameSession.STATUS_FINISHED:
        raise ValueError("Game already finished.")
    if session.status == GameSession.STATUS_PAUSED:
        raise ValueError("Game is paused.")
    if session.status != GameSession.STATUS_ACTIVE:
        raise ValueError("Game is not active.")


def question_timer_total_seconds(session: GameSession, question) -> int:
    return min(
        QUESTION_TIMER_MAX_SECONDS,
        session.timer_seconds + question.timer_extension_seconds,
    )


def question_elapsed_seconds(session: GameSession, question, now=None) -> int:
    if not question.question_started_at:
        return 0

    now = now or timezone.now()
    effective_now = now
    if session.status == GameSession.STATUS_PAUSED and session.paused_at:
        effective_now = session.paused_at

    return max(
        0,
        int((effective_now - question.question_started_at).total_seconds())
        - question.paused_seconds,
    )


def question_remaining_seconds(session: GameSession, question, now=None) -> int:
    return max(
        0,
        question_timer_total_seconds(session, question)
        - question_elapsed_seconds(session, question, now=now),
    )


@transaction.atomic
def extend_current_question_timer(session: GameSession):
    ensure_active_session(session)
    question = get_current_question(session)
    if not question:
        raise ValueError("No active question.")
    if not question.question_started_at:
        raise ValueError("Question is not active.")
    if question.timer_extension_used:
        raise ValueError("Timer extension already used.")

    allowed_extension = min(
        QUESTION_TIMER_EXTENSION_SECONDS,
        max(0, QUESTION_TIMER_MAX_SECONDS - session.timer_seconds),
    )
    if allowed_extension <= 0:
        raise ValueError("Timer cannot be extended.")

    question.timer_extension_seconds = allowed_extension
    question.timer_extension_used = True
    question.timer_extended_at = timezone.now()
    question.save(
        update_fields=[
            "timer_extension_seconds",
            "timer_extension_used",
            "timer_extended_at",
        ]
    )
    return question


@transaction.atomic
def pause_game(session: GameSession) -> GameSession:
    if session.is_finished or session.status == GameSession.STATUS_FINISHED:
        raise ValueError("Game already finished.")
    if session.status == GameSession.STATUS_PAUSED:
        return session

    session.status = GameSession.STATUS_PAUSED
    session.paused_at = timezone.now()
    session.save(update_fields=["status", "paused_at"])
    return session


@transaction.atomic
def resume_game(session: GameSession) -> GameSession:
    if session.is_finished or session.status == GameSession.STATUS_FINISHED:
        raise ValueError("Game already finished.")
    if session.status != GameSession.STATUS_PAUSED:
        return session

    now = timezone.now()
    paused_seconds = 0
    if session.paused_at:
        paused_seconds = max(0, int((now - session.paused_at).total_seconds()))

    current_question = get_current_question(session)
    if current_question and current_question.question_started_at:
        current_question.paused_seconds += paused_seconds
        current_question.save(update_fields=["paused_seconds"])

    session.total_paused_seconds += paused_seconds
    session.status = GameSession.STATUS_ACTIVE
    session.paused_at = None
    session.save(update_fields=["total_paused_seconds", "status", "paused_at"])
    return session


@transaction.atomic
def finish_game(session: GameSession) -> GameSession:
    if session.is_finished:
        return session

    if session.status == GameSession.STATUS_PAUSED:
        resume_game(session)
        session.refresh_from_db()

    session.status = GameSession.STATUS_FINISHED
    session.is_finished = True
    session.finished_at = timezone.now()
    session.paused_at = None
    session.save(update_fields=["status", "is_finished", "finished_at", "paused_at"])

    if session.mode == "league":
        from apps.league.services import save_league_result
        save_league_result(session)

    return session
