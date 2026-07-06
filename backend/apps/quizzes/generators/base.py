import random

from apps.quizzes.contracts import GeneratedQuestion, QuestionGenerator
from apps.quizzes.presentation import unique_choices

BaseQuestionGenerator = QuestionGenerator


def make_choices(correct_answer: str, wrong_answers: list[str], total: int = 4) -> list[str]:
    choices = unique_choices(correct_answer, wrong_answers, total=total)
    random.shuffle(choices)
    return choices
