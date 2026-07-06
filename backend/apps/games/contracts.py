from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class AssessmentResult:
    selected_answer: str
    correct_answer: str
    is_correct: bool
    time_expired: bool
    remaining_seconds: int

    @property
    def is_scored_correct(self) -> bool:
        return self.is_correct and not self.time_expired


@dataclass(frozen=True)
class ScoringContext:
    is_correct: bool
    time_expired: bool
    remaining_seconds: int
    streak: int
    mode: str = "random"
    difficulty: str | None = None


@dataclass(frozen=True)
class ScoringResult:
    score_delta: int
    xp_delta: int
    streak_delta: int
    rule_version: str
    bonus: dict[str, int]


class ScoringRule(Protocol):
    version: str

    def calculate(self, context: ScoringContext) -> ScoringResult:
        ...
