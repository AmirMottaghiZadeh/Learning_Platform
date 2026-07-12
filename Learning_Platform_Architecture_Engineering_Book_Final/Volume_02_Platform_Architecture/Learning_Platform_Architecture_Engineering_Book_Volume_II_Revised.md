# Learning Platform Architecture & Engineering Book

# Volume II — Platform Architecture

**Subtitle:** Designing the Reusable Core for Multi-Product Learning Systems  
**Version:** 1.1 Revised  
**Status:** Architecture Specification  
**Scope:** Platform-level architecture, independent from any single product  
**Reference Implementation:** Pharmexa appears only as a validation example, not as the architecture itself.

---

## Revision Notes

This revised edition expands Volume II from a high-level outline into an implementation-grade architecture specification.

It defines:
- Architectural style
- Layering
- Dependency rules
- Bounded contexts
- Shared kernel
- Plugin architecture
- Extension points
- Event-driven design
- Contract strategy
- Architecture governance
- Anti-patterns
- Implementation checklist

---

## Table of Contents

1. Purpose of This Volume  
2. Architecture North Star  
3. Architectural Overview  
4. Clean Architecture Model  
5. Layered Architecture  
6. Domain-Centered Design  
7. Bounded Contexts  
8. Shared Kernel  
9. Core Platform Modules  
10. Dependency Rules  
11. Application Services  
12. Rule Engines  
13. Selectors and Query Boundaries  
14. Infrastructure Boundaries  
15. Plugin Architecture  
16. Extension Points  
17. Event-Driven Architecture  
18. API and Contract Architecture  
19. Admin CMS Architecture  
20. Analytics Architecture  
21. Security Architecture Placement  
22. Observability Architecture Placement  
23. Multi-Product Strategy  
24. Reference Implementation Strategy  
25. Architecture Decision Records  
26. Architecture Anti-Patterns  
27. Implementation Checklist  
28. Volume II Summary  

---

# 1. Purpose of This Volume

Volume I defined the philosophy of the Learning Platform Framework.

Volume II defines the architecture.

The goal of this volume is to answer one central question:

> How should the platform be structured so that many learning products can be built on top of one reusable core?

This volume is intentionally product-independent.

It does not design Pharmexa directly.

It designs the platform that Pharmexa and future products will use.

---

# 2. Architecture North Star

The architecture must make this possible:

```text
Learning Platform Core
        |
        |-- Pharmexa
        |-- K_Anatomy
        |-- K_Physiology
        |-- K_Nursing
        |-- K_Chemistry
        |-- Future Products
```

Each product must be able to provide its own:

- Dataset
- Domain mappings
- Question generators
- Product branding
- Product configuration
- Optional domain rules

without rewriting the platform.

The architecture succeeds when creating a new learning product is primarily a matter of configuration, dataset design and plugin implementation.

The architecture fails if every new product requires core platform redesign.

---

# 3. Architectural Overview

The platform follows a layered, domain-centered architecture.

At a high level:

```text
Clients
  |
  |-- Mobile App
  |-- Web App
  |-- Admin CMS
  |
API Layer
  |
Application Services
  |
Rule Engines
  |
Domain Model
  |
Selectors / Repositories
  |
Infrastructure
  |
Database / Cache / Queue / External Services
```

The system has two major kinds of code:

1. Platform Core
2. Product Extensions

## 3.1 Platform Core

Platform Core includes all reusable learning capabilities:

- Identity
- Learning objects
- Assessment
- Review
- Progress
- Analytics
- Admin CMS foundation
- Security
- Observability
- API standards
- Engine contracts

## 3.2 Product Extensions

Product Extensions define domain-specific behavior.

Examples:

Pharmexa extension:
- Drug dataset importer
- Drug question generators
- Drug admin views
- Drug-specific dataset validation

K_Anatomy extension:
- Anatomy dataset importer
- Anatomy question generators
- Anatomy topic mapping

The platform must never depend on a product extension.

---

# 4. Clean Architecture Model

The platform follows Clean Architecture principles.

The most important rule:

> Inner layers must not depend on outer layers.

The domain and rules must not know about:

- HTTP
- React Native
- Django
- PostgreSQL
- Redis
- Render
- Supabase
- Any product-specific UI

## 4.1 Dependency Flow

```text
Presentation
    ↓
Application
    ↓
Domain / Rules
    ↓
Interfaces
    ↑
Infrastructure implements interfaces
```

Infrastructure may depend on domain interfaces.

Domain must not depend on infrastructure.

## 4.2 Practical Meaning

A scoring rule must be testable without:

- Starting a server
- Connecting to a database
- Rendering a UI
- Calling external services

A recommendation rule must be testable as a pure domain behavior.

---

# 5. Layered Architecture

## 5.1 Presentation Layer

Responsible for:

- HTTP endpoints
- Mobile screens
- Admin pages
- Request parsing
- Response formatting
- Authentication boundary

Not responsible for:

- Score calculation
- Correctness validation
- Flashcard scheduling
- League ranking
- Mastery detection

## 5.2 Application Layer

Responsible for use-case orchestration.

Examples:

- Start learning session
- Submit answer
- Finish quiz
- Review flashcard
- Generate dashboard
- Import dataset
- Rebuild analytics

Application services coordinate work but should not hide complex domain rules.

## 5.3 Rule Engine Layer

Responsible for explicit product and platform rules.

Examples:

- Score rule
- Streak rule
- Mistake rule
- Review scheduling rule
- Mastery rule
- League point rule

Rules should be isolated, named and testable.

## 5.4 Domain Layer

Responsible for platform concepts:

- Learning Object
- Knowledge Source
- Assessment Item
- Learning Session
- Review Item
- Progress State
- Learning Event

## 5.5 Infrastructure Layer

Responsible for technical details:

- Database persistence
- Cache
- Background workers
- File storage
- Email
- Push notifications
- External analytics
- Error tracking

---

# 6. Domain-Centered Design

The platform is organized around learning domain concepts, not database tables or UI screens.

The core language of the platform includes:

- Learner
- Learning Object
- Learning Topic
- Knowledge Source
- Assessment
- Answer
- Review
- Progress
- Mastery
- Event
- Recommendation

This language must be used consistently in code, documentation, API design and admin interfaces.

---

# 7. Bounded Contexts

The platform is divided into bounded contexts.

Each context owns its own language, rules and data boundaries.

## 7.1 Identity Context

Owns:

- User
- Profile
- Authentication
- Authorization
- Account status

## 7.2 Learning Content Context

Owns:

- Learning Object
- Learning Topic
- Knowledge Source
- Dataset import
- Dataset validation

## 7.3 Assessment Context

Owns:

- Question generation
- Assessment item
- Answer validation
- Session lifecycle
- Score events

## 7.4 Review Context

Owns:

- Flashcards
- Review queue
- Spaced repetition
- Due items
- Review result

## 7.5 Progress Context

Owns:

- Accuracy
- Mastery
- Topic progress
- XP
- Streak
- Learning history

## 7.6 League Context

Owns:

- Ranking
- Weekly season
- League points
- Leaderboard
- Rank calculation

## 7.7 Analytics Context

Owns:

- Events
- Aggregates
- Retention
- Weak topics
- Question quality
- Product metrics

## 7.8 Administration Context

Owns:

- Admin CMS
- Dataset management
- Question management
- User operations
- System visibility

---

# 8. Shared Kernel

The Shared Kernel contains concepts reused across contexts.

It must remain small.

Shared Kernel may contain:

- Stable IDs
- Time utilities
- Common value objects
- Event envelope
- Pagination contract
- Error contract
- Base result types
- Platform enums

Shared Kernel must not become a dumping ground.

If a concept is not truly shared, it must stay inside its bounded context.

---

# 9. Core Platform Modules

## 9.1 Identity Module

Provides user identity and access control.

## 9.2 Content Module

Manages learning objects and knowledge sources.

## 9.3 Assessment Module

Generates and evaluates learning questions.

## 9.4 Review Module

Schedules and evaluates review activity.

## 9.5 Progress Module

Tracks learning progress and mastery.

## 9.6 Analytics Module

Transforms platform events into insights.

## 9.7 Admin Module

Provides operational control of the product.

## 9.8 Integration Module

Handles external systems.

---

# 10. Dependency Rules

The architecture enforces strict dependency rules.

## Rule 1

Presentation may depend on Application.

## Rule 2

Application may depend on Domain and Rule Engines.

## Rule 3

Domain must not depend on Presentation.

## Rule 4

Domain must not depend on Infrastructure.

## Rule 5

Product extensions may depend on Platform Core contracts.

## Rule 6

Platform Core must never depend on product extensions.

## Rule 7

Shared Kernel must stay minimal.

## Rule 8

Business rules must be testable without external services.

---

# 11. Application Services

Application services represent use cases.

Examples:

- StartQuizSessionService
- SubmitAnswerService
- FinishSessionService
- ReviewFlashcardService
- GenerateDashboardService
- ImportDatasetService

Application services coordinate:

- Validation
- Domain rules
- Persistence
- Events
- Response objects

They should not become large procedural scripts.

When a service grows too large, extract:

- Rule object
- Policy
- Selector
- Domain service
- Event handler

---

# 12. Rule Engines

Rule engines are explicit modules that own decision logic.

Examples:

## Assessment Rules

- Correct answer
- Late answer
- Timeout
- Score
- Streak
- Mistake creation

## Review Rules

- Review interval
- Difficulty adjustment
- Due date
- Mastery state

## League Rules

- Points
- Ranking
- Season reset
- Tie-breaking

## Progress Rules

- XP
- Accuracy
- Mastery
- Weakness detection

Rules must be:

- Named
- Documented
- Tested
- Versioned when necessary

---

# 13. Selectors and Query Boundaries

Selectors isolate read queries.

A selector answers a read question.

Examples:

- get_current_question
- get_due_reviews
- get_user_dashboard_summary
- get_weekly_leaderboard
- get_weak_topics
- get_learning_object_history

Selectors prevent query logic from spreading into views and services.

Complex queries belong in selectors, not presentation code.

---

# 14. Infrastructure Boundaries

Infrastructure implements technical behavior.

Examples:

- ORM models
- Database queries
- Cache adapters
- Queue workers
- File storage
- Email services
- Push notification services

Infrastructure must be replaceable.

If the platform moves from one hosting provider to another, core rules should not change.

---

# 15. Plugin Architecture

Products extend the platform through plugins.

A plugin may provide:

- Dataset schema
- Importer
- Validator
- Question generators
- Admin panels
- Product configuration
- UI theme
- Domain rules
- Analytics dimensions

## 15.1 Plugin Contract

Each plugin must declare:

- Name
- Version
- Supported platform version
- Capabilities
- Required datasets
- Question types
- Admin extensions
- Events emitted
- Events consumed

## 15.2 Plugin Isolation

A plugin may depend on platform contracts.

The platform must not import plugin internals.

---

# 16. Extension Points

The platform exposes extension points.

## Dataset Adapter

Transforms external content into platform knowledge sources.

## Question Generator

Creates assessment items from knowledge sources.

## Review Strategy

Determines review scheduling.

## Scoring Strategy

Calculates score and XP.

## Recommendation Strategy

Suggests what to learn next.

## Admin Extension

Adds product-specific admin capabilities.

## Analytics Processor

Adds domain-specific analytics.

## Theme Extension

Provides product visual identity.

---

# 17. Event-Driven Architecture

Learning products generate many meaningful events.

Events should be first-class architecture elements.

## 17.1 Core Events

- UserRegistered
- LearningSessionStarted
- QuestionPresented
- QuestionAnswered
- MistakeCreated
- ReviewScheduled
- ReviewCompleted
- LearningObjectMastered
- TopicProgressUpdated
- LeagueRankChanged

## 17.2 Event Benefits

Events support:

- Analytics
- Recommendations
- Notifications
- Audit logs
- Debugging
- Future automation

## 17.3 Event Rule

Events describe facts that already happened.

They should be named in past tense.

---

# 18. API and Contract Architecture

APIs are public contracts.

They must be stable, versioned and documented.

## API Standards

- Use versioning
- Use consistent error format
- Use pagination
- Use authentication consistently
- Never expose sensitive rule internals
- Never trust client-side score

## Error Format

Errors should be predictable.

Example:

```json
{
  "code": "QUESTION_ALREADY_ANSWERED",
  "message": "This question has already been answered.",
  "details": {}
}
```

---

# 19. Admin CMS Architecture

Admin CMS is a platform capability.

It must support:

- Content management
- Dataset import
- Dataset validation
- Question management
- User management
- Analytics
- System health
- Feature flags
- Operational logs

Product plugins may add domain-specific admin sections.

Admin CMS must never require direct database editing for normal operations.

---

# 20. Analytics Architecture

Analytics is built on events and aggregates.

## Raw Events

Store facts.

## Aggregates

Summarize behavior.

Examples:

- Daily active users
- Questions answered
- Accuracy by topic
- Weak learning objects
- Review completion
- Retention
- League participation

## Analytics Rule

Analytics should not block user-facing requests when possible.

Heavy analytics should run asynchronously.

---

# 21. Security Architecture Placement

Security exists across layers.

## Presentation

- Authentication
- Rate limiting
- Request validation

## Application

- Authorization
- Ownership checks
- Operation rules

## Domain

- Rule integrity
- Server-side correctness

## Infrastructure

- Secrets
- Database permissions
- Encryption
- Backups

Security is not a single module.

---

# 22. Observability Architecture Placement

Observability includes:

- Logs
- Metrics
- Traces
- Errors
- Audit events
- Health checks

Each platform module should emit useful signals.

Important operations must be observable:

- Login failures
- Answer submission
- Dataset import
- League calculation
- Background jobs
- Admin actions

---

# 23. Multi-Product Strategy

A platform product portfolio may look like:

```text
Learning Platform
  ├── Shared Core
  ├── Shared Engines
  ├── Shared Admin CMS
  ├── Shared Mobile Design System
  └── Product Extensions
       ├── Pharmexa
       ├── K_Anatomy
       └── K_Chemistry
```

Product-specific code must stay in product boundaries.

Shared improvements should move into the platform only when they are useful across products.

---

# 24. Reference Implementation Strategy

Reference implementations validate the platform.

Pharmexa validates:

- Domain mapping
- Dataset import
- Quiz engine
- Flashcards
- Mistake review
- League
- Dashboard
- Admin CMS
- Mobile UI system

A reference implementation is not allowed to redefine core architecture.

It must prove the architecture.

---

# 25. Architecture Decision Records

## ADR-0006: Layered Architecture

Status: Accepted

Decision:
The platform uses layered architecture with strict dependency direction.

Rationale:
This protects learning rules from infrastructure and UI changes.

## ADR-0007: Bounded Contexts

Status: Accepted

Decision:
The platform is divided into bounded contexts.

Rationale:
Learning products contain multiple domains of behavior.

## ADR-0008: Plugin-Based Product Extensions

Status: Accepted

Decision:
Products extend the platform through plugins.

Rationale:
This enables reuse without core modification.

## ADR-0009: Events as Platform Signals

Status: Accepted

Decision:
Learning events are first-class architecture elements.

Rationale:
Analytics, recommendations and automation depend on event history.

## ADR-0010: Admin CMS as Platform Module

Status: Accepted

Decision:
Admin CMS belongs to the platform, not to individual products.

Rationale:
All products need operational control.

---

# 26. Architecture Anti-Patterns

## Product Coupling

Putting product-specific concepts into platform core.

## God Service

One service controlling too many use cases.

## View Logic

Business decisions inside controllers or views.

## Hidden Rules

Rules embedded in serializers, database scripts or UI code.

## Plugin Leakage

Platform imports product plugin internals.

## Analytics Afterthought

Events and metrics added after product launch.

## Admin Afterthought

Admin tools delayed until operations become painful.

---

# 27. Implementation Checklist

Before implementing any module:

- Identify bounded context.
- Define contracts.
- Define services.
- Define rules.
- Define selectors.
- Define events.
- Define tests.
- Define admin needs.
- Define monitoring signals.
- Document ADR if architectural.

A module is not complete until it is:

- Implemented
- Tested
- Documented
- Observable
- Secure
- Integrated with admin if needed

---

# 28. Volume II Summary

Volume II defines the architecture of the reusable Learning Platform Framework.

The platform is:

- Domain-independent
- Layered
- Rule-driven
- Plugin-extensible
- Event-aware
- Contract-based
- Admin-operable
- Analytics-ready

This architecture enables multiple learning products to be built from one core foundation.

Pharmexa is the first validation of this architecture, not the architecture itself.
