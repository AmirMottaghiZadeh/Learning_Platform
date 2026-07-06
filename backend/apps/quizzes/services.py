import random

from apps.learning.contracts import KnowledgeSourceRef, LearningProductAdapter
from apps.learning.registry import get_learning_adapter
from apps.quizzes.contracts import GeneratedQuestion, QuestionGenerationContext
from apps.quizzes.presentation import choices_for_source


class QuizGenerator:
    def __init__(self, adapter: LearningProductAdapter | None = None):
        self.adapter = adapter or get_learning_adapter()

    def generate(self, *, question_count: int = 10, context: QuestionGenerationContext | None = None):
        context = context or QuestionGenerationContext(question_count=question_count)

        sources = self.adapter.list_knowledge_sources(context)

        if len(sources) < 4:
            raise ValueError("Not enough question sources to generate quiz.")

        questions = []

        for _ in range(context.question_count):
            source = random.choice(sources)

            distractors_pool = [
                item for item in sources
                if item.id != source.id
                and item.source_type == source.source_type
                and item.correct_answer
                and item.correct_answer != source.correct_answer
            ]

            if len(distractors_pool) < 3:
                distractors_pool = [
                    item for item in sources
                    if item.id != source.id
                    and item.correct_answer
                    and item.correct_answer != source.correct_answer
                ]

            wrong_answers = self._sample_unique_wrong_answers(distractors_pool)

            questions.append(
                self._build_generated_question(source, wrong_answers)
            )

        return questions

    def _build_generated_question(
        self,
        source: KnowledgeSourceRef,
        wrong_answers: list[str],
    ) -> GeneratedQuestion:
        return GeneratedQuestion(
            question_type=source.source_type,
            text=source.prompt,
            choices=choices_for_source(source.source_type, source.correct_answer, wrong_answers),
            correct_answer=source.correct_answer,
            knowledge_source_id=source.id,
            explanation=source.explanation,
        )

    def _sample_unique_wrong_answers(self, distractors_pool: list[KnowledgeSourceRef]) -> list[str]:
        shuffled = distractors_pool.copy()
        random.shuffle(shuffled)
        answers = []
        for item in shuffled:
            if item.correct_answer in answers:
                continue
            answers.append(item.correct_answer)
            if len(answers) >= 3:
                break
        return answers
