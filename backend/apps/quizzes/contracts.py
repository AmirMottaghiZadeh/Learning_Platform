from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class QuestionGenerationContext:
    question_count: int = 10
    topic_key: str | None = None
    target_category_key: str | None = None
    difficulty_target: str | None = None
    learner_id: int | None = None


@dataclass(frozen=True)
class GeneratedQuestion:
    question_type: str
    text: str
    choices: list[str]
    correct_answer: str
    knowledge_source_id: int
    explanation: str = ""
    difficulty: str | None = None

    @property
    def source_id(self) -> int:
        return self.knowledge_source_id


class QuestionGenerator(Protocol):
    question_type: str

    def generate(self, source, distractors) -> GeneratedQuestion:
        ...
