from apps.learning.registry import get_learning_adapter
from apps.quizzes.contracts import QuestionGenerationContext


def active_question_sources(context: QuestionGenerationContext | None = None):
    return get_learning_adapter().list_knowledge_sources(
        context or QuestionGenerationContext()
    )


def sources_for_question_type(question_type: str):
    return [
        source
        for source in active_question_sources()
        if source.source_type == question_type
    ]
