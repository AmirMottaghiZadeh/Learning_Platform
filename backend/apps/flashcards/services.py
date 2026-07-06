from django.utils import timezone

from apps.flashcards.contracts import (
    VALID_REVIEW_RATINGS,
    ReviewScheduleResult,
    ReviewSchedulingContext,
)
from apps.learning.models import KnowledgeSource
from apps.learning.services import (
    EVENT_REVIEW_SCHEDULED,
    record_learning_event,
    record_review_completed,
)

from .models import FlashcardReview, FlashcardState

LEITNER_MIN_BOX = 1
LEITNER_MAX_BOX = 5
REVIEW_SCHEDULE_RULE_VERSION = "k-game-leitner-box-v1"
KNOWN_RATINGS = {"known", "good", "easy"}
UNKNOWN_RATINGS = {"unknown", "again", "hard"}


def normalize_review_rating(rating):
    if rating not in VALID_REVIEW_RATINGS:
        raise ValueError("Invalid review rating.")
    if rating in KNOWN_RATINGS:
        return "known"
    return "unknown"


def calculate_review_schedule(context: ReviewSchedulingContext) -> ReviewScheduleResult:
    outcome = normalize_review_rating(context.rating)
    current_box = max(0, min(LEITNER_MAX_BOX, context.current_box))

    if outcome == "unknown":
        next_box = LEITNER_MIN_BOX if current_box < LEITNER_MIN_BOX else min(LEITNER_MAX_BOX, current_box + 1)
        due_at = None
    elif current_box <= LEITNER_MIN_BOX:
        next_box = 0
        due_at = None
    else:
        next_box = current_box - 1
        due_at = None

    return ReviewScheduleResult(
        next_box=next_box,
        due_at=due_at,
        interval_days=0,
        rule_version=REVIEW_SCHEDULE_RULE_VERSION,
    )


def review_card(state, rating):
    reviewed_at = timezone.now()
    box_before = state.box
    outcome = normalize_review_rating(rating)
    schedule = calculate_review_schedule(
        ReviewSchedulingContext(
            current_box=state.box,
            rating=rating,
            reviewed_at=reviewed_at,
        )
    )
    state.box = schedule.next_box
    state.review_state = _review_state_for_box(schedule.next_box)
    state.interval_days = schedule.interval_days
    state.review_count += 1
    state.lapse_count += 1 if outcome == "unknown" else 0
    state.last_rating = rating
    state.schedule_rule_version = schedule.rule_version
    state.last_reviewed_at = reviewed_at
    state.due_at = schedule.due_at
    state.save(
        update_fields=[
            "box",
            "review_state",
            "interval_days",
            "review_count",
            "lapse_count",
            "last_rating",
            "schedule_rule_version",
            "last_reviewed_at",
            "due_at",
        ]
    )
    review = FlashcardReview.objects.create(
        state=state,
        rating=rating,
        box_before=box_before,
        box_after=schedule.next_box,
        interval_days=schedule.interval_days,
        scheduled_due_at=schedule.due_at,
        rule_version=schedule.rule_version,
    )
    record_review_completed(
        learner=state.user,
        flashcard_state=state,
        review=review,
        occurred_at=reviewed_at,
    )
    return review


def _review_state_for_box(box):
    if box <= 0:
        return FlashcardState.REVIEW_STATE_SUSPENDED
    if box == 1:
        return FlashcardState.REVIEW_STATE_LEARNING
    if box >= LEITNER_MAX_BOX:
        return FlashcardState.REVIEW_STATE_MATURE
    return FlashcardState.REVIEW_STATE_REVIEW


def seed_flashcards_for_user(
    *,
    user,
    product_id="k_game",
    count=0,
    target_category_key="",
    source_type="",
):
    due_at = timezone.now()
    existing_source_ids = set(
        FlashcardState.objects
        .filter(user=user, knowledge_source__isnull=False)
        .values_list("knowledge_source_id", flat=True)
    )

    sources = (
        KnowledgeSource.objects
        .filter(product_id=product_id, is_active=True)
        .exclude(prompt="")
        .exclude(correct_answer="")
        .exclude(id__in=existing_source_ids)
        .select_related("learning_object", "topic")
        .order_by("metadata__target_category_key", "source_type", "id")
    )
    if target_category_key:
        sources = sources.filter(metadata__target_category_key=target_category_key)
    if source_type:
        sources = sources.filter(source_type=source_type)

    states = []
    if count and count > 0:
        sources = sources[:count]
    for source in sources:
        states.append(schedule_flashcard_from_source(user=user, knowledge_source=source, due_at=due_at))
    return states


def schedule_flashcard_from_source(*, user, knowledge_source, due_at=None):
    due_at = due_at or timezone.now()
    state, created = FlashcardState.objects.get_or_create(
        user=user,
        knowledge_source=knowledge_source,
        defaults={
            "box": 0,
            "review_state": FlashcardState.REVIEW_STATE_NEW,
            "due_at": due_at,
            "interval_days": 0,
            "schedule_rule_version": REVIEW_SCHEDULE_RULE_VERSION,
        },
    )
    if created:
        _record_review_scheduled(
            user=user,
            knowledge_source=knowledge_source,
            state=state,
            occurred_at=due_at,
            correlation_id=f"flashcard-seed:{state.id}",
            reason="learning_seed",
            created=True,
        )
    return state


def get_leitner_box_counts(*, user, product_id="k_game", target_category_key="", source_type=""):
    queryset = (
        FlashcardState.objects
        .filter(user=user, knowledge_source__product_id=product_id)
        .exclude(review_state=FlashcardState.REVIEW_STATE_SUSPENDED)
    )
    if target_category_key:
        queryset = queryset.filter(knowledge_source__metadata__target_category_key=target_category_key)
    if source_type:
        queryset = queryset.filter(knowledge_source__source_type=source_type)
    return {
        "new": queryset.filter(box=0, review_state=FlashcardState.REVIEW_STATE_NEW).count(),
        "boxes": [
            {"box": box, "count": queryset.filter(box=box).count()}
            for box in range(LEITNER_MIN_BOX, LEITNER_MAX_BOX + 1)
        ],
    }


def _record_review_scheduled(
    *,
    user,
    knowledge_source,
    state,
    occurred_at,
    correlation_id,
    reason,
    created,
    extra_payload=None,
):
    record_learning_event(
        event_type=EVENT_REVIEW_SCHEDULED,
        learner=user,
        product_id=knowledge_source.product_id,
        occurred_at=occurred_at,
        correlation_id=correlation_id,
        payload={
            "flashcard_state_id": state.id,
            "topic_key": knowledge_source.topic.key,
            "knowledge_source_id": knowledge_source.id,
            "learning_object_id": knowledge_source.learning_object_id,
            "target_category_key": knowledge_source.metadata.get("target_category_key", ""),
            "created": created,
            "reason": reason,
            "box": state.box,
            "due_at": state.due_at.isoformat() if state.due_at else None,
            "rule_version": REVIEW_SCHEDULE_RULE_VERSION,
            **(extra_payload or {}),
        },
    )
