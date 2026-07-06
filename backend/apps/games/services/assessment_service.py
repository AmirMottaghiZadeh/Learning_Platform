from apps.games.contracts import AssessmentResult
from apps.quizzes.presentation import answers_match


def evaluate_answer(
    *,
    selected_answer: str,
    correct_answer: str,
    remaining_seconds: int,
    question_type: str | None = None,
) -> AssessmentResult:
    return AssessmentResult(
        selected_answer=selected_answer,
        correct_answer=correct_answer,
        is_correct=answers_match(
            question_type=question_type,
            selected_answer=selected_answer,
            correct_answer=correct_answer,
        ),
        time_expired=remaining_seconds <= 0,
        remaining_seconds=remaining_seconds,
    )
