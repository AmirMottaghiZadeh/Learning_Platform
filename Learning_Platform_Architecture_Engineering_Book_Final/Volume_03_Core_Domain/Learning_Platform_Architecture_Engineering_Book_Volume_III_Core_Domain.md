# Learning Platform Architecture & Engineering Book

# Volume III — Core Domain

**Subtitle:** The Universal Domain Model for Reusable Learning Products  
**Version:** 1.0  
**Status:** Architecture Specification  
**Scope:** Core domain model of the Learning Platform Framework  
**Reference Implementation:** Pharmexa is used only as a mapping example.

---

## Table of Contents

1. Purpose of This Volume
2. Core Domain Philosophy
3. Ubiquitous Language
4. Domain Map
5. Learner
6. Learning Object
7. Learning Topic
8. Knowledge Source
9. Assessment Item
10. Question Model
11. Answer Model
12. Learning Session
13. Review Item
14. Progress Model
15. Mastery Model
16. Mistake Model
17. Event Model
18. Analytics Model
19. Domain Services
20. Value Objects
21. Aggregate Boundaries
22. State Machines
23. Repository Contracts
24. Product Domain Mapping
25. Core Domain ADRs
26. Anti-Patterns
27. Implementation Checklist
28. Volume III Summary

---

# 1. Purpose of This Volume

Volume I defined the philosophy of the Learning Platform.

Volume II defined the architecture.

Volume III defines the Core Domain.

The Core Domain is the reusable language and model that every learning product shares.

This volume answers:

> What are the universal concepts that exist in every learning product built on this platform?

The answer must remain independent from any single product.

There must be no platform-level dependency on terms such as Drug, Anatomy Structure, Formula, Word or Legal Article.

Those are product-domain concepts.

The platform-domain concepts are:

- Learner
- Learning Object
- Learning Topic
- Knowledge Source
- Assessment Item
- Answer
- Learning Session
- Review Item
- Progress State
- Mastery State
- Mistake
- Learning Event
- Analytics Signal

These concepts form the domain foundation of the framework.

---

# 2. Core Domain Philosophy

The Core Domain is designed around learning, not content.

A content-management system stores educational material.

A learning platform transforms educational material into personalized learning experiences.

The Core Domain must support:

- Assessment
- Feedback
- Review
- Retention
- Progress
- Personalization
- Analytics
- Mastery

The Core Domain should be small enough to remain stable, but expressive enough to support many products.

## 2.1 Domain Independence

The platform must never assume that learning content belongs to medicine, language, anatomy or any other specific domain.

Instead, every product maps its own domain to the platform domain.

Example:

| Platform Concept | Pharmexa Product Mapping |
|---|---|
| Learning Object | Drug |
| Learning Topic | Drug Topic |
| Knowledge Source | Drug Fact / Question Source |
| Assessment Item | Drug Question |
| Review Item | Drug Flashcard |
| Mistake | Wrong Drug Answer |

The same platform can support an anatomy product:

| Platform Concept | Anatomy Product Mapping |
|---|---|
| Learning Object | Anatomical Structure |
| Learning Topic | Body System |
| Knowledge Source | Structure Function / Location / Innervation |
| Assessment Item | Anatomy Question |
| Review Item | Anatomy Flashcard |

---

# 3. Ubiquitous Language

The platform uses a consistent language across documentation, code, APIs and admin tooling.

## 3.1 Required Terms

Learner:
A user who studies on the platform.

Learning Object:
The primary thing being learned.

Learning Topic:
A grouping or category of learning objects.

Knowledge Source:
Structured information used to generate questions, flashcards or explanations.

Assessment Item:
A question or task used to evaluate knowledge.

Answer:
A learner response to an assessment item.

Learning Session:
A sequence of learning activities.

Review Item:
A scheduled reinforcement item.

Progress State:
A snapshot of learner advancement.

Mastery State:
A state describing reliable knowledge retention.

Learning Event:
A recorded fact about something that happened.

## 3.2 Forbidden Platform Terms

The platform core should not contain product-specific terms such as:

- Drug
- Brand
- Indication
- Anatomy
- Organ
- Word
- Translation
- Formula

These terms belong inside product implementations.

---

# 4. Domain Map

The Core Domain contains several connected aggregates.

```text
Learner
  |
  |-- Learning Session
  |       |
  |       |-- Assessment Item
  |       |-- Answer
  |
  |-- Review Item
  |
  |-- Progress State
  |
  |-- Mastery State
  |
  |-- Learning Event

Learning Object
  |
  |-- Knowledge Source
  |-- Learning Topic
  |-- Assessment Item
  |-- Review Item
```

The main relationship is:

Knowledge Source powers Assessment and Review.

Learner activity produces Events.

Events update Progress and Mastery.

---

# 5. Learner

A Learner is a user participating in learning activity.

The platform must treat the Learner as more than an account.

An account identifies a person.

A learner has learning history.

## 5.1 Responsibilities

The Learner participates in:

- Learning sessions
- Assessment
- Review
- Progress tracking
- League ranking
- Personalized recommendations

## 5.2 Learner Identity

The Learner should be connected to identity, but the learning domain should not depend directly on authentication technology.

Authentication answers:

> Who is this user?

The learning domain answers:

> What is this learner learning, forgetting and mastering?

## 5.3 Learner State

A learner may have:

- Current streak
- XP
- Level
- Progress per topic
- Review queue
- Weak topics
- Mistake history
- Session history

Not all of these belong in one model.

Large learner state should be split by bounded context.

---

# 6. Learning Object

A Learning Object is the primary entity a learner studies.

Examples:

- Drug
- Word
- Formula
- Legal rule
- Anatomy structure
- Historical event

## 6.1 Required Attributes

A Learning Object should have:

- Stable ID
- Display name
- Optional subtitle
- Topic membership
- Active/inactive state
- Metadata
- Domain-specific payload

## 6.2 Platform Rule

The platform stores Learning Object identity and relationships.

Product plugins define domain-specific fields.

## 6.3 Example Mapping

Pharmexa:

Learning Object = Drug

Anatomy:

Learning Object = Anatomical Structure

Chemistry:

Learning Object = Chemical Concept

---

# 7. Learning Topic

A Learning Topic groups learning objects.

Topics support:

- Navigation
- Filtering
- Progress tracking
- Weakness detection
- Dashboard summaries
- Learning plans

## 7.1 Topic Hierarchy

The platform should support simple topics first.

Future versions may support:

- Parent topics
- Topic trees
- Topic prerequisites
- Topic difficulty
- Topic sequences

## 7.2 Topic Progress

A learner can have progress per topic.

Topic progress is derived from:

- Assessment history
- Review performance
- Mastery states
- Mistake frequency
- Time spent

---

# 8. Knowledge Source

A Knowledge Source is structured information attached to a Learning Object.

It is the raw material for learning activities.

Examples:

Pharmexa:
- Generic name
- Brand name
- Side effect
- Indication
- Food relation
- Dosing

Language:
- Word meaning
- Pronunciation
- Example sentence
- Grammar usage

Anatomy:
- Location
- Function
- Blood supply
- Innervation

## 8.1 Responsibilities

Knowledge Sources power:

- Question generation
- Flashcard generation
- Explanation generation
- Review scheduling
- Analytics

## 8.2 Quality Requirements

Knowledge Sources must be:

- Structured
- Validated
- Traceable
- Versioned when possible
- Associated with source metadata
- Suitable for assessment generation

## 8.3 Dataset Import

A product may import Knowledge Sources from:

- JSON
- Excel
- CSV
- CMS forms
- External APIs

Every import must produce validation reports.

## 8.4 Source Metadata Boundaries

Imported knowledge must preserve three distinct metadata layers:

1. Dataset document metadata
   - schema version
   - source file identity and checksum
   - authoring metadata
   - extraction method and timestamp
   - extraction warnings
   - enrichment method and reference checksum
2. Learning-object metadata
   - normalized domain fields used by product rules
   - stable source row identity
   - classification and taxonomy values
3. Source-specific attributes
   - validated columns that are meaningful in the source dataset but are not part of the shared product schema
   - original header names and values retained without data loss

Operational extraction metadata must not be mixed with clinical learning fields. The normalized fields are the primary application contract; the original record remains available for traceability and future remapping.

Importers must reject unsupported schema versions, validate the complete batch before replacement, and derive stable identifiers from immutable source identity rather than database sequence values.

---

# 9. Assessment Item

An Assessment Item evaluates learner knowledge.

It can be:

- Multiple-choice question
- True/false question
- Fill-in-the-blank
- Matching task
- Short answer
- Flashcard prompt
- Case-based question

The platform starts with multiple-choice assessment but should not be limited to it.

## 9.1 Required Attributes

- Prompt
- Question type
- Choices if applicable
- Correct answer or validation rule
- Knowledge source reference
- Learning object reference
- Topic reference
- Difficulty estimate
- Explanation or feedback
- Active state

## 9.2 Security Rule

Correct answers must not be trusted from clients.

The backend validates answers.

---

# 10. Question Model

A Question is a presentable Assessment Item.

Questions may be generated from Knowledge Sources.

## 10.1 Generated Questions

The platform may generate questions dynamically or store generated question records.

Stored generated questions are useful for:

- Reproducibility
- Analytics
- Answer history
- Debugging
- Review

## 10.2 Question Type

Question type defines the assessment pattern.

Examples:

- Identify name
- Match concept
- Choose indication
- Choose side effect
- Select timing
- Recall definition

Question types are platform-extensible.

## 10.3 Question Quality

Question quality can be measured by:

- Correct answer rate
- Discrimination
- Repeated confusion
- Duplicate options
- Ambiguous wording
- Missing explanation

---

# 11. Answer Model

An Answer records a learner response.

## 11.1 Required Attributes

- Learner
- Session
- Question
- Selected answer
- Correct answer snapshot
- Is correct
- Time remaining
- Time expired
- Score delta
- Answered at
- Client answered at if provided

## 11.2 Correct vs Scored

Correctness and score are different.

A learner may answer correctly after time expires.

In that case:

- is_correct = true
- time_expired = true
- score_delta = 0

This distinction improves analytics and feedback.

---

# 12. Learning Session

A Learning Session groups learning activity.

Examples:

- Quiz session
- Flashcard session
- League session
- Mistake review session
- Topic practice session

## 12.1 Session Lifecycle

```text
Created
  ↓
Started
  ↓
Active
  ↓
Completed
  ↓
Archived
```

## 12.2 Session Responsibilities

A session tracks:

- Learner
- Mode
- Topic
- Questions
- Answers
- Score
- Correct count
- Start time
- Finish time
- Status

## 12.3 Session Modes

Possible modes:

- Random practice
- Topic practice
- Mistake retry
- League
- Daily review
- Adaptive session

---

# 13. Review Item

Review Items support long-term retention.

A Review Item represents something the learner should revisit.

## 13.1 Review Source

A Review Item may be created from:

- Incorrect answer
- Hard question
- Manually saved item
- Weak topic
- Scheduled spaced repetition
- Recommendation engine

## 13.2 Review Result

A review can result in:

- Again
- Hard
- Good
- Easy

These values affect the next review date.

## 13.3 Review State

A Review Item may have:

- New
- Learning
- Review
- Mature
- Suspended

---

# 14. Progress Model

Progress describes learner advancement.

Progress should not only count activity.

It should measure learning quality.

## 14.1 Progress Dimensions

- Questions answered
- Accuracy
- Topic progress
- Learning object mastery
- Review completion
- Streak
- XP
- Time spent
- Weak topics
- Improvement trend

## 14.2 Derived Progress

Some progress is derived from events.

Examples:

- Accuracy
- Topic strength
- Mastery
- Retention

Derived data may be cached or materialized.

---

# 15. Mastery Model

Mastery indicates reliable knowledge.

A Learning Object may move through states:

```text
Unseen
  ↓
Seen
  ↓
Practicing
  ↓
Reviewing
  ↓
Mastered
```

## 15.1 Mastery Inputs

Mastery can depend on:

- Correct answers
- Review success
- Time since last review
- Repeated mistakes
- Difficulty
- Confidence
- Topic importance

## 15.2 Mastery Rule

Mastery must not be based on a single correct answer.

Learning requires repeated evidence.

---

# 16. Mistake Model

A Mistake is a meaningful wrong or failed learning event.

Mistakes are valuable signals.

## 16.1 Mistake Creation

A mistake may be created when:

- Answer is wrong
- Answer is correct but too late, depending on product rules
- Learner repeatedly misses a topic
- Review fails

## 16.2 Mistake Data

A Mistake should store:

- Learner
- Learning object
- Knowledge source
- Last wrong answer
- Wrong count
- Last occurred at
- Topic
- Question type

## 16.3 Mistake Usage

Mistakes power:

- Mistake review
- Weak topic detection
- Flashcard creation
- Recommendations
- Dashboard warnings

---

# 17. Event Model

Events record facts.

They should be immutable whenever possible.

## 17.1 Core Events

- LearningSessionStarted
- AssessmentItemPresented
- AnswerSubmitted
- AnswerEvaluated
- MistakeCreated
- ReviewScheduled
- ReviewCompleted
- ProgressUpdated
- MasteryAchieved
- LeagueResultRecorded

## 17.2 Event Envelope

An event should include:

- Event ID
- Event type
- Learner ID
- Product ID
- Timestamp
- Payload
- Correlation ID
- Source

## 17.3 Event Naming

Events should be named in past tense.

Example:

QuestionAnswered

not

AnswerQuestion

---

# 18. Analytics Model

Analytics transforms events into insight.

## 18.1 Analytics Layers

Raw Events:
Facts.

Aggregates:
Summaries.

Insights:
Interpretations.

Recommendations:
Actions suggested by the system.

## 18.2 Example Analytics

- Accuracy by topic
- Most missed learning objects
- Review completion rate
- Weak question types
- Daily active learners
- Retention
- Average session score
- Learning velocity

---

# 19. Domain Services

Domain Services contain domain logic that does not naturally belong to one entity.

Examples:

- ScoreCalculator
- ReviewScheduler
- MasteryEvaluator
- WeakTopicDetector
- RecommendationBuilder
- LeagueRankCalculator

Domain services must be testable independently.

---

# 20. Value Objects

Value Objects represent small immutable domain concepts.

Examples:

- Score
- XP
- Accuracy
- TimeRemaining
- Difficulty
- ReviewInterval
- MasteryLevel
- QuestionType
- TopicKey

Value Objects should protect invalid states.

---

# 21. Aggregate Boundaries

Aggregates protect consistency.

## 21.1 Learning Session Aggregate

Owns:

- Session state
- Questions assigned
- Answer submission lifecycle
- Completion status

## 21.2 Review Item Aggregate

Owns:

- Review state
- Review interval
- Due date
- Review history

## 21.3 Progress Aggregate

Owns:

- Derived learning state
- Topic progress
- Mastery state

## 21.4 Dataset Aggregate

Owns:

- Imported content
- Validation status
- Source metadata

---

# 22. State Machines

## 22.1 Session State

```text
Created -> Started -> Active -> Finished -> Archived
```

## 22.2 Review State

```text
New -> Learning -> Review -> Mature
```

## 22.3 Mastery State

```text
Unseen -> Seen -> Practicing -> Reviewing -> Mastered
```

State transitions must be explicit.

---

# 23. Repository Contracts

Repositories hide persistence details.

A repository contract may define:

- Get learning object
- List active knowledge sources
- Save learning session
- Record answer
- Get due reviews
- Get progress summary

The domain should not know how data is stored.

---

# 24. Product Domain Mapping

Products implement mapping from their domain to the core model.

## 24.1 Pharmexa Mapping

Learning Object:
Drug

Learning Topic:
DrugTopic

Knowledge Source:
DrugQuestionSource

Assessment Item:
Generated drug question

Review Item:
Drug flashcard

## 24.2 Future Product Mapping

A new product should define:

- Learning Object schema
- Topic schema
- Knowledge Source schema
- Question types
- Admin import process
- Review behavior
- Product UI terms

---

# 25. Core Domain ADRs

## ADR-0011: Learning Object as Universal Entity

Status: Accepted

Decision:
The platform uses Learning Object as the universal studied entity.

## ADR-0012: Knowledge Source Powers Assessment

Status: Accepted

Decision:
Questions and flashcards are generated from Knowledge Sources.

## ADR-0013: Correctness and Scoring Are Separate

Status: Accepted

Decision:
Answer correctness must be tracked separately from awarded score.

## ADR-0014: Events Are Domain Facts

Status: Accepted

Decision:
Important learning actions are stored as domain events.

## ADR-0015: Product Concepts Stay Outside Core

Status: Accepted

Decision:
Product-specific entities are mapped to platform abstractions.

---

# 26. Anti-Patterns

## Product-Specific Core Models

Putting Drug or Anatomy concepts directly into the platform core.

## Single Giant Progress Table

Storing all progress logic in one unstructured table.

## Questions Without Source

Every question should be traceable to a Knowledge Source.

## No Review Model

A quiz-only system cannot support long-term retention.

## No Event History

Without events, analytics and recommendations become weak.

## Correctness Equals Score

Late correct answers prove knowledge but may not earn points.

---

# 27. Implementation Checklist

A product implementation must define:

- Learning Object mapping
- Learning Topic mapping
- Knowledge Source schema
- Assessment item generation
- Answer validation
- Session lifecycle
- Review behavior
- Progress calculations
- Mastery rules
- Events emitted
- Admin management
- Dataset validation

The platform core must provide reusable contracts for all of these.

---

# 28. Volume III Summary

Volume III defines the Core Domain of the Learning Platform Framework.

The central domain concepts are:

- Learner
- Learning Object
- Learning Topic
- Knowledge Source
- Assessment Item
- Answer
- Learning Session
- Review Item
- Progress
- Mastery
- Mistake
- Event
- Analytics

These concepts allow the same platform to power many educational products.

Pharmexa is one mapping of this domain.

Future products will define their own mappings while reusing the same core.
