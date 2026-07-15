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

        sources = [
            source
            for source in self.adapter.list_knowledge_sources(context)
            if source.correct_answer
        ]

        if len(sources) < 4:
            raise ValueError("Not enough question sources to generate quiz.")

        selected_sources = self._select_sources(
            sources=sources,
            question_count=context.question_count,
        )
        answers_by_type = self._group_unique_answers_by_type(sources)
        all_answers = self._unique_answers(
            source.correct_answer
            for source in sources
        )
        questions = []

        for source in selected_sources:
            wrong_answers = self._sample_unique_wrong_answers(
                answers_by_type.get(source.source_type, []),
                source.correct_answer,
            )
            if len(wrong_answers) < 3:
                fallback_answers = self._sample_unique_wrong_answers(
                    all_answers,
                    source.correct_answer,
                    existing_answers=wrong_answers,
                )
                wrong_answers.extend(fallback_answers[: 3 - len(wrong_answers)])
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

    def _select_sources(
        self,
        *,
        sources: list[KnowledgeSourceRef],
        question_count: int,
    ) -> list[KnowledgeSourceRef]:
        if question_count <= len(sources):
            return random.sample(sources, k=question_count)
        return [random.choice(sources) for _ in range(question_count)]

    def _group_unique_answers_by_type(
        self,
        sources: list[KnowledgeSourceRef],
    ) -> dict[str, list[str]]:
        grouped: dict[str, list[str]] = {}
        seen_by_type: dict[str, set[str]] = {}
        for source in sources:
            answers = grouped.setdefault(source.source_type, [])
            seen_answers = seen_by_type.setdefault(source.source_type, set())
            answer = source.correct_answer
            if not answer or answer in seen_answers:
                continue
            seen_answers.add(answer)
            answers.append(answer)
        return grouped

    def _unique_answers(self, answers: list[str] | tuple[str, ...] | object) -> list[str]:
        unique_answers = []
        seen_answers = set()
        for answer in answers:
            if not answer or answer in seen_answers:
                continue
            seen_answers.add(answer)
            unique_answers.append(answer)
        return unique_answers

    def _sample_unique_wrong_answers(
        self,
        distractor_answers: list[str],
        correct_answer: str,
        *,
        existing_answers: list[str] | None = None,
    ) -> list[str]:
        shuffled = distractor_answers.copy()
        random.shuffle(shuffled)
        answers = list(existing_answers or [])
        seen_answers = set(answers)
        for item in shuffled:
            if item == correct_answer or item in seen_answers:
                continue
            answers.append(item)
            seen_answers.add(item)
            if len(answers) >= 3:
                break
        return answers
