from .models import GameQuestion, GameSession


def get_user_game_session(*, user, session_id: int) -> GameSession:
    return GameSession.objects.get(id=session_id, user=user)


def get_current_question(session: GameSession):
    answered_ids = session.answers.values_list("question_id", flat=True)

    return (
        session.questions
        .exclude(id__in=answered_ids)
        .select_related("knowledge_source", "source")
        .order_by("order")
        .first()
    )


def get_game_question(*, session: GameSession, question_id: int) -> GameQuestion:
    return (
        session.questions
        .select_related("knowledge_source", "source")
        .get(id=question_id)
    )
