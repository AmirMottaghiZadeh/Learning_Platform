# Learning Platform Architecture & Engineering Book

# Volume IV — Learning Engines

**Subtitle:** Reusable Engines for Assessment, Review, Progress and Adaptive Learning  
**Version:** 1.0  
**Status:** Architecture Specification  
**Scope:** Platform-level specification  
**Reference Implementation:** K_Game is used only as a mapping example.

---

## Table of Contents

1. Purpose of This Volume
2. Engine Architecture Principles
3. Learning Engine
4. Quiz Engine
5. Question Generation Engine
6. Assessment Engine
7. Scoring Engine
8. Review Engine
9. Flashcard Engine
10. Spaced Repetition Engine
11. Recommendation Engine
12. League Engine
13. Progress Engine
14. Analytics Engine
15. Engine Communication
16. Rule Composition
17. Engine Contracts
18. Failure Recovery
19. Engine ADRs
20. Anti-Patterns
21. Implementation Checklist
22. Volume IV Summary

---

# 1. Purpose of This Volume

Volume IV defines the reusable learning engines that power products built on the Learning Platform Framework.

Where Volume III defines the domain, this volume defines the behavior.

Engines are reusable capability modules. They should be independent, testable, rule-driven and extensible.

The core engines are:
- Quiz Engine
- Question Generation Engine
- Assessment Engine
- Scoring Engine
- Review Engine
- Flashcard Engine
- Spaced Repetition Engine
- Recommendation Engine
- League Engine
- Progress Engine
- Analytics Engine

Each engine must expose clear contracts and must avoid product-specific coupling.

---

# 2. Engine Architecture Principles

Engines are not database tables, screens or controllers.

An engine is a reusable decision-making capability.

Every engine must follow these principles:

1. Explicit rules
2. Testable behavior
3. Stable contract
4. Product-independent core
5. Optional product-specific strategy
6. Event emission
7. Observability support

Engines should communicate through application services, events or defined contracts.

An engine must not directly modify unrelated bounded contexts without a contract.

---

# 3. Learning Engine

The Learning Engine coordinates the learner journey.

It does not replace specialized engines. It orchestrates them.

Responsibilities:
- Determine what the learner should do next
- Coordinate quiz, review and progress workflows
- Build daily learning recommendations
- Surface weak topics
- Support dashboard summaries

The Learning Engine may call:
- Recommendation Engine
- Review Engine
- Progress Engine
- Quiz Engine

It must not contain low-level scoring or scheduling rules directly.

---

# 4. Quiz Engine

The Quiz Engine manages quiz sessions.

Responsibilities:
- Start quiz sessions
- Select eligible knowledge sources
- Request generated questions
- Track assigned questions
- Manage session lifecycle
- Provide current question
- Finish session

The Quiz Engine must not trust the client to provide score or correctness.

Quiz modes may include:
- Random practice
- Topic practice
- Mistake review
- League session
- Daily challenge
- Adaptive session

Quiz Engine output should be safe for clients. Correct answers must not be exposed before answer submission.

---

# 5. Question Generation Engine

The Question Generation Engine transforms Knowledge Sources into Assessment Items.

Inputs:
- Knowledge Source
- Question type
- Product plugin
- Difficulty target
- Learner history if adaptive

Outputs:
- Prompt
- Choices
- Correct answer snapshot
- Explanation
- Metadata
- Source reference

Question generation should support:
- Multiple-choice
- True/false
- Matching
- Fill-in-the-blank
- Case-based questions
- Flashcard prompts

Products may provide domain-specific generators.

The platform provides generator contracts and validation rules.

---

# 6. Assessment Engine

The Assessment Engine evaluates learner answers.

Responsibilities:
- Validate submitted answer
- Compare against correct answer or validation rule
- Distinguish correctness from score
- Detect timeout
- Produce assessment result
- Emit answer events

Correctness and scoring are separate.

A late correct answer may be:
- Correct for learning analytics
- Worth zero score in a timed mode

This distinction is essential for learning integrity.

---

# 7. Scoring Engine

The Scoring Engine calculates points, XP and session score.

Inputs:
- Is correct
- Time remaining
- Streak
- Mode
- Difficulty
- Product rules

Outputs:
- Score delta
- XP delta
- Streak update
- Bonus information

The Scoring Engine must be deterministic and testable.

Scoring should be versioned when rules change.

Historical results should preserve the scoring rule version used at the time.

---

# 8. Review Engine

The Review Engine manages reinforcement.

Responsibilities:
- Create review items
- Determine due items
- Process review results
- Update review state
- Emit review events

Review sources:
- Mistakes
- Hard answers
- Saved items
- Weak topics
- Scheduled spaced repetition
- Product recommendations

Review is a core platform feature, not an optional add-on.

---

# 9. Flashcard Engine

The Flashcard Engine provides card-based learning and review.

A flashcard may be generated from:
- Knowledge Source
- Mistake
- Weak topic
- Manually saved item

Products may expose flashcards for all implementation learning objects. A mistake may inform recommendations, but a product should not require quiz mistakes before flashcards can be created or reviewed.

Flashcard states:
- New
- Learning
- Review
- Mature
- Suspended

New learning cards and Leitner review items are separate queues:
- A new card is selected by source type and target category.
- A new card has no due date and is never counted as a due review.
- A new card enters Leitner box 1 only after an Unknown response.
- A Known response on a new card completes that card without adding it to Leitner review.
- Leitner review is a learner-wide queue and must not be scoped by the source type or category used to discover the card.

Minimum review responses:
- Known
- Unknown

The Flashcard Engine may use a Leitner-style box policy. A five-box Leitner policy is valid when the product needs explicit learner-controlled review:
- Unknown moves the card one box forward.
- Unknown on a new card places it into box 1.
- Unknown in box 5 keeps it in box 5.
- Known moves the card one box backward.
- Known in box 1 removes the card from active review.

The scheduling strategy must be contract-based and versioned.

---

# 10. Spaced Repetition Engine

The Spaced Repetition Engine schedules future reviews.

Responsibilities:
- Calculate next review interval
- Adjust difficulty
- Update ease factor if used
- Detect mature items
- Reduce interval after failures

The platform should start with a simple algorithm and allow future replacement.

The scheduling strategy must be contract-based.

Products should not hard-code review algorithms.

---

# 11. Recommendation Engine

The Recommendation Engine decides what the learner should do next.

Inputs:
- Due reviews
- Weak topics
- Recent mistakes
- Progress
- Mastery states
- Learning goals
- Product strategy

Outputs:
- Recommended session
- Suggested topic
- Review priority
- Weakness warning
- Daily plan

The first MVP can use rule-based recommendations.

Future versions may use AI or statistical models.

---

# 12. League Engine

The League Engine manages competitive learning.

Responsibilities:
- Record league results
- Calculate weekly points
- Rank learners
- Manage seasons
- Handle ties
- Provide leaderboard

League scoring must be separate from learning correctness.

League behavior must be fair and auditable.

A league result should store:
- Learner
- Season
- Score
- Correct count
- Time bonus
- Rank snapshot if needed

---

# 13. Progress Engine

The Progress Engine tracks learning advancement.

It consumes:
- Answer events
- Review events
- Session events
- Mastery events

It produces:
- Accuracy
- Topic progress
- XP
- Streak
- Weak topics
- Mastery states
- Dashboard summaries

Progress may be calculated synchronously for small products and asynchronously for larger products.

---

# 14. Analytics Engine

The Analytics Engine transforms events into insight.

Layers:
- Raw events
- Aggregates
- Insights
- Recommendations

Analytics should answer:
- Which topics are weak?
- Which questions are low quality?
- Which users are returning?
- Which learning objects are frequently missed?
- Which review items are overdue?

Analytics should not block critical user actions.

---

# 15. Engine Communication

Engines communicate through:
- Application services
- Domain events
- Explicit contracts
- Shared value objects

Direct hidden dependencies are prohibited.

Example:
Answer submission may call Assessment Engine and Scoring Engine, then emit AnswerEvaluated. Review Engine may subscribe or be invoked by application service to schedule review if needed.

---

# 16. Rule Composition

Complex learning behavior comes from composing rules.

Example answer workflow:
1. Validate session
2. Validate question
3. Evaluate answer
4. Detect timeout
5. Calculate score
6. Update streak
7. Create mistake if needed
8. Schedule review if needed
9. Emit events
10. Update progress

Each step should be independently testable.

---

# 17. Engine Contracts

Every engine must publish a contract.

Contract should define:
- Inputs
- Outputs
- Errors
- Events emitted
- Events consumed
- Rule version
- Product extension points

Contracts allow engines to evolve without breaking products.

---

# 18. Failure Recovery

Engine workflows must handle failure safely.

Examples:
- Answer recorded but progress update failed
- Review completed but analytics failed
- League update delayed
- Event processing retried

Critical state should be transactional.

Derived state may be rebuilt from events.

---

# 19. Engine ADRs

ADR-0016: Engines are reusable platform modules.
ADR-0017: Correctness and scoring remain separate.
ADR-0018: Review is core platform behavior.
ADR-0019: Recommendation begins rule-based and can evolve.
ADR-0020: Engine contracts are required for product extensions.

---

# 20. Anti-Patterns

Anti-patterns:
- Putting scoring in frontend
- Combining quiz, review and progress into one giant service
- Creating product-specific engine logic in platform core
- Updating analytics synchronously when not needed
- Hiding learning rules inside database scripts
- Treating review as optional

---

# 21. Implementation Checklist

Before implementing an engine:
- Define responsibility
- Define contract
- Define events
- Define rules
- Define persistence needs
- Define product extension points
- Define tests
- Define observability
- Define admin visibility

---

# 22. Volume IV Summary

Volume IV defines the reusable learning engines of the platform.

The platform becomes valuable because these engines can be reused across many products.

K_Game validates the engines, but does not define them.

---
