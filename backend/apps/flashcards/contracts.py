from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Protocol


ReviewRating = Literal["known", "unknown", "again", "hard", "good", "easy"]
VALID_REVIEW_RATINGS = {"known", "unknown", "again", "hard", "good", "easy"}


@dataclass(frozen=True)
class ReviewSchedulingContext:
    current_box: int
    rating: ReviewRating
    reviewed_at: datetime


@dataclass(frozen=True)
class ReviewScheduleResult:
    next_box: int
    due_at: datetime | None
    interval_days: int
    rule_version: str


class ReviewSchedulingRule(Protocol):
    version: str

    def schedule(self, context: ReviewSchedulingContext) -> ReviewScheduleResult:
        ...
