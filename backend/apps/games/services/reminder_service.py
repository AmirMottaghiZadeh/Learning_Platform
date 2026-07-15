from django.db import transaction

from apps.games.models import GameQuestion, GameSession, QuizReminder


@transaction.atomic
def create_quiz_reminder(
    *,
    user,
    prompt: str,
    correct_answer: str,
    question_type: str,
    selected_answer: str = "",
    explanation: str = "",
    options: list[str] | None = None,
    game_session_id: int | None = None,
    game_question_id: int | None = None,
    knowledge_source_id: int | None = None,
):
    game_session = None
    if game_session_id:
        game_session = GameSession.objects.get(id=game_session_id, user=user)

    game_question = None
    if game_question_id:
        queryset = GameQuestion.objects.select_related("knowledge_source", "session")
        if game_session is not None:
            game_question = queryset.get(id=game_question_id, session=game_session)
        else:
            game_question = queryset.get(id=game_question_id, session__user=user)

    knowledge_source = None
    if knowledge_source_id:
        from apps.learning.models import KnowledgeSource

        knowledge_source = KnowledgeSource.objects.get(id=knowledge_source_id)
    elif game_question and game_question.knowledge_source_id:
        knowledge_source = game_question.knowledge_source

    reminder, _ = QuizReminder.objects.update_or_create(
        user=user,
        game_question=game_question,
        defaults={
            "game_session": game_session or (game_question.session if game_question else None),
            "knowledge_source": knowledge_source,
            "question_type": question_type,
            "prompt": prompt,
            "selected_answer": selected_answer,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "options": options or [],
        },
    )
    return reminder
