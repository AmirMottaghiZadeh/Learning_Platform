from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol
from uuid import uuid4

from django.utils import timezone


@dataclass(frozen=True)
class LearningEvent:
    event_type: str
    learner_id: int | None
    product_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    occurred_at: datetime = field(default_factory=timezone.now)
    correlation_id: str = field(default_factory=lambda: str(uuid4()))
    source: str = "backend"

    def __post_init__(self):
        if not self.event_type:
            raise ValueError("event_type is required.")
        if not self.product_id:
            raise ValueError("product_id is required.")


class LearningEventPublisher(Protocol):
    def publish(self, event: LearningEvent) -> None:
        ...


class NullLearningEventPublisher:
    """Discards events. Only for tests and products that opt out of eventing."""

    def publish(self, event: LearningEvent) -> None:
        return None


def build_learning_event(
    *,
    event_type: str,
    learner_id: int | None,
    product_id: str = "pharmexa",
    payload: dict[str, Any] | None = None,
    correlation_id: str | None = None,
    source: str = "backend",
    occurred_at: datetime | None = None,
) -> LearningEvent:
    return LearningEvent(
        event_type=event_type,
        learner_id=learner_id,
        product_id=product_id,
        payload=payload or {},
        occurred_at=occurred_at or timezone.now(),
        correlation_id=correlation_id or str(uuid4()),
        source=source,
    )
