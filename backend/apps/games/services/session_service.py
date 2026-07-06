from django.db import transaction
from django.utils import timezone

from apps.learning.registry import get_learning_adapter
from apps.quizzes.contracts import QuestionGenerationContext
from apps.quizzes.services import QuizGenerator

from apps.games.models import GameSession, GameQuestion


VALID_GAME_COUNTS = tuple(range(10, 101, 10))


def validate_game_start(*, mode, count, target_category_key=""):
    if count not in VALID_GAME_COUNTS:
        raise ValueError("Question count must be a multiple of 10 between 10 and 100.")
    if mode == "category" and not target_category_key:
        raise ValueError("Category mode requires target_category_key.")


@transaction.atomic
def start_game(
    user,
    *,
    topic_key="random",
    target_category_key="",
    mode="random",
    count=10,
    timer_seconds=30,
):
    validate_game_start(mode=mode, count=count, target_category_key=target_category_key)
    category_filter = target_category_key if mode == "category" else ""
    adapter = get_learning_adapter()
    generated_questions = QuizGenerator(adapter=adapter).generate(
        question_count=count,
        context=QuestionGenerationContext(
            question_count=count,
            topic_key=topic_key,
            target_category_key=category_filter or None,
            learner_id=user.id,
        ),
    )

    session = GameSession.objects.create(
        user=user,
        topic_key=topic_key,
        target_category_key=category_filter,
        mode=mode,
        status=GameSession.STATUS_ACTIVE,
        total_questions=len(generated_questions),
        timer_seconds=timer_seconds,
    )

    for index, generated in enumerate(generated_questions):
        knowledge_source = adapter.get_source_instance(generated.knowledge_source_id)

        GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=index,
            options=generated.choices,
            question_started_at=timezone.now() if index == 0 else None,
        )

    return session
