# Learning Platform migration starter

This starter is being refactored from a Pharmexa-only backend into a reusable Learning Platform backend, with Pharmexa as the first reference implementation.

## API contract

The official API contract is versioned under `/api/v1/`.

- `GET /api/v1/health/`
- `GET /api/v1/schema/`
- `GET /api/v1/docs/`
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/logout/`
- `GET /api/v1/auth/me/`
- `GET /api/v1/topics/`
- `GET /api/v1/target-categories/`
- `GET /api/v1/drugs/`
- `POST /api/v1/games/`
- `GET /api/v1/games/{id}/`
- `POST /api/v1/games/{id}/answer/`
- `POST /api/v1/games/{id}/finish/`
- `GET /api/v1/me/dashboard/`
- `GET /api/v1/me/mistakes/`
- `GET /api/v1/me/progress/`
- `GET /api/v1/me/progress/summary/`
- `GET /api/v1/me/recommendations/`
- `GET /api/v1/me/statistics/`
- `GET /api/v1/league/`
- `GET /api/v1/league/me/`
- `GET /api/v1/league/seasons/current/`
- `POST /api/v1/league/start/`
- `GET /api/v1/flashcards/`
- `GET /api/v1/flashcards/boxes/`
- `POST /api/v1/flashcards/seed/`
- `POST /api/v1/flashcards/{id}/review/`

Legacy `/api/` aliases remain temporarily for migration compatibility, but the OpenAPI schema documents only `/api/v1/`.

Errors use the platform envelope:

```json
{
  "code": "NOT_AUTHENTICATED",
  "message": "Authentication credentials were not provided.",
  "details": {}
}
```

## Import current JS data

From the original static project root:

```bash
python manage.py import_drugs --drugs-js ../drugs-data.js --topics-js ../drug-topics-data.js
```

## Security direction

Frontend sends only `game_id`, `question_id`, `selected_answer`, and `client_answered_at`.
Django calculates correctness, remaining time, score, mistakes, league rating, and leaderboard data.

Frontend API requests use DRF token authentication:

```http
Authorization: Token <token>
```

## Platform engine contracts

The backend now exposes explicit, testable contracts for the next platformization steps:

- `apps.learning.contracts.LearningObjectRef`
- `apps.learning.contracts.LearningTopicRef`
- `apps.learning.contracts.KnowledgeSourceRef`
- `apps.learning.contracts.LearningProductAdapter`
- `apps.quizzes.contracts.GeneratedQuestion`
- `apps.quizzes.contracts.QuestionGenerationContext`
- `apps.games.contracts.AssessmentResult`
- `apps.games.contracts.ScoringContext`
- `apps.games.contracts.ScoringResult`
- `apps.flashcards.contracts.ReviewSchedulingContext`
- `apps.flashcards.contracts.ReviewScheduleResult`
- `apps.core.events.LearningEvent`

These contracts keep Pharmexa-specific data mapped onto reusable platform concepts without moving `Drug` concepts into platform core.

Pharmexa now provides the first product adapter:

- `apps.drugs.learning_adapter.KGameLearningAdapter`

The Quiz and Game session services use the learning adapter contract instead of importing `DrugQuestionSource` directly. Current `games` and `flashcards` persistence models still reference the Pharmexa source model and should be migrated in a later persistence-focused phase.

Generic platform domain models introduced in `apps.learning`:

- `LearningTopic`
- `LearningObject`
- `KnowledgeSource`
- `LearningEventRecord`

These models represent the platform concepts from the Architecture Book. Pharmexa still keeps its product-specific `Drug`, `DrugTopic`, and `DrugQuestionSource` models as the current reference implementation dataset.

## Persistence alignment

Game and flashcard persistence now store generic platform sources through:

- `GameQuestion.knowledge_source`
- `Mistake.knowledge_source`
- `FlashcardState.knowledge_source`

The legacy `source` fields remain nullable fallback fields during migration:

- `GameQuestion.source`
- `Mistake.source`
- `FlashcardState.source`

To sync Pharmexa's current dataset into generic learning sources:

```bash
python manage.py sync_learning_sources
```

Current local sync result:

- 4 learning topics
- 1484 learning objects
- 3037 knowledge sources

## Game and assessment stabilization

Game sessions now use an explicit state field:

- `active`
- `paused`
- `finished`
- `archived`

The legacy `is_finished` flag remains for compatibility while `status` becomes the platform state-machine field.

Game answers now store assessment/scoring snapshots:

- `time_expired`
- `xp_delta`
- `scoring_rule_version`

Question timers now start only when a question becomes current. Future questions keep `question_started_at = null` until they are presented. Pause/resume freezes the current question timer through `GameQuestion.paused_seconds`.

New lifecycle endpoints:

- `POST /api/v1/games/{id}/pause/`
- `POST /api/v1/games/{id}/resume/`

Rule versions introduced in this phase:

- `mvp-scoring-v1`
- `k-game-leitner-box-v1`

## Review, flashcard, and progress foundation

Phase 5 promotes review and progress to platform behavior.

Generic learner progress is now stored in `apps.learning.LearnerProgress` per learner/product/topic. It tracks:

- questions answered
- correct/wrong/timed-out answers
- XP
- review count
- mistake count
- mastery state
- last learning activity

Answer submission now records first-class learning events:

- `QuestionAnswered`
- `MistakeCreated`
- `TopicProgressUpdated`

Wrong answers record mistakes and progress, but they do not automatically create flashcards. Flashcards are created through the independent category deck flow. `FlashcardState` acts as a platform Review Item with:

- `review_state`
- `interval_days`
- `review_count`
- `lapse_count`
- `last_rating`
- `schedule_rule_version`

Flashcard reviews store scheduling snapshots on `FlashcardReview`:

- `box_before`
- `box_after`
- `interval_days`
- `scheduled_due_at`
- `rule_version`

Review completion records:

- `ReviewCompleted`
- `TopicProgressUpdated`

Dashboard-oriented progress endpoints:

- `GET /api/v1/me/progress/`
- `GET /api/v1/me/progress/summary/`
- `POST /api/v1/flashcards/seed/`

Rule versions introduced or used in this phase:

- `mvp-topic-progress-v1`
- `k-game-leitner-box-v1`

## Pharmexa game modes and Leitner flashcards

Pharmexa now supports two primary game start modes:

- `random`: user-selected question count, restricted to multiples of 10 from 10 to 100.
- `category`: same count contract, filtered by a broad target category such as cardiovascular, CNS, respiratory, endocrine, GI or infection.

Game start also requires a learning source type through `topic_key`:

- `brandGeneric`
- `timing`
- `indication`
- `sideEffects`

Broad target category metadata is stored on Pharmexa `LearningObject` and `KnowledgeSource` records:

- `target_category_key`
- `target_category_label`
- `target_category_source`

The frontend can list available categories through:

- `GET /api/v1/target-categories/?product_id=k_game`

Flashcards are now a learning engine for all active Pharmexa Knowledge Sources. Flashcard deck creation is category-based and independent of quiz mistakes.
Flashcard decks are filtered by both source type and optional target category.
When the learner creates a flashcard deck, all matching sources for the selected source type and category are scheduled, not a random fixed-size subset.

Question prompt naming rules:

- `brandGeneric` prompts use the drug brand name.
- `timing`, `indication`, and `sideEffects` prompts use the generic drug name when available.
- fallback naming may use the imported generic/name field when a dedicated generic field is absent.

Pharmexa uses a five-box Leitner policy:

- `unknown` on a new card places it into box 1.
- `unknown` moves an active card one box forward.
- `unknown` in box 5 keeps it in box 5.
- `known` moves an active card one box backward.
- `known` in box 1 removes it from active review.
- reviewed cards leave the current due deck immediately and are visible by opening their Leitner box.

The frontend can open boxes through:

- `GET /api/v1/flashcards/?product_id=k_game&box=1`
- `GET /api/v1/flashcards/?product_id=k_game&source_type=timing`
- `GET /api/v1/flashcards/?product_id=k_game&source_type=timing&target_category_key=cardiovascular`
- `GET /api/v1/flashcards/boxes/?product_id=k_game`
- `GET /api/v1/flashcards/boxes/?product_id=k_game&source_type=timing&target_category_key=cardiovascular`

## Phase 7 product-behavior cleanup

The frontend must render a refined question contract rather than raw dataset metadata.

Game questions retain presentation fields:

- `interaction_type`
- `option_layout`
- `instruction`

Timing questions use canonical food-timing choices:

- `با غذا`
- `بدون غذا`
- `فرقی نمی‌کند`

Quiz UI should render only the prompt and options for the active question. Raw dataset fields such as dosage form, drug classification, source category and subtitle must not be displayed in the question card.

Flashcards can be activated through:

- `POST /api/v1/flashcards/seed/`

This endpoint creates learning flashcards from active knowledge sources. User feedback then decides whether a card enters or moves inside the Leitner boxes.

## League, statistics, and dashboard APIs

Phase 6 adds backend APIs for the product dashboard and competitive learning layer.

League is now season-aware through `apps.league.LeagueSeason`. League results store:

- product
- season
- season key
- rank snapshot
- league rule version

The current MVP league rule is weekly:

- `mvp-weekly-league-v1`

Leaderboard responses are calculated server-side and return the best result per learner for the requested product/topic/season. This prevents frontend-side ranking logic and keeps repeated attempts from duplicating a learner in the visible leaderboard.

League endpoints:

- `GET /api/v1/league/`
- `GET /api/v1/league/me/`
- `GET /api/v1/league/seasons/current/`
- `POST /api/v1/league/start/`

Dashboard and statistics endpoints:

- `GET /api/v1/me/dashboard/`
- `GET /api/v1/me/statistics/`
- `GET /api/v1/me/recommendations/`

These endpoints are designed for the future Expo + React Native Web frontend. The frontend should render these API responses and must not calculate progress, weak topics, recommendation priority or league rank.

## Frontend runtime decision

Phase 7 will use Expo with React Native Web as the reference frontend runtime.

This means one frontend codebase should support:

- web deployment
- mobile-first browser experience
- future Android builds
- future iOS builds

The frontend remains API-driven. Backend remains the source of truth for scoring, correctness, scheduling, mastery, progress and league ranking.
