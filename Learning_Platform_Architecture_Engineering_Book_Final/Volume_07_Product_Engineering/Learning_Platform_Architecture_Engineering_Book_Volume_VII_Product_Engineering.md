# Learning Platform Architecture & Engineering Book

# Volume VII — Product Engineering

**Subtitle:** Turning the Platform into Complete Learning Products  
**Version:** 1.0  
**Status:** Architecture Specification  
**Scope:** Platform-level specification  
**Reference Implementation:** K_Game is used only as a mapping example.

---

## Table of Contents

1. Purpose of This Volume
2. Product Engineering Principles
3. MVP Definition
4. Learning Loop
5. Personas
6. User Journey
7. User Stories
8. Acceptance Criteria
9. Product Metrics
10. Retention Strategy
11. Admin CMS Product Scope
12. Release Strategy
13. Roadmap Strategy
14. Product Risks
15. Success Criteria
16. Product ADRs
17. Volume VII Summary

---

# 1. Purpose of This Volume

Volume VII defines product engineering for the Learning Platform.

This volume connects architecture to product outcomes.

It defines MVP, user journeys, personas, product metrics, release strategy and acceptance criteria.

---

# 2. Product Engineering Principles

Product engineering principles:

1. Complete learning loop over feature count.
2. Retention over one-time quiz completion.
3. Admin operations are part of product quality.
4. Metrics must influence roadmap.
5. MVP must be usable by real learners.
6. Product scope must be explicit.

---

# 3. MVP Definition

The MVP is the smallest complete learning product.

It must include:
- Authentication
- Learning Dashboard
- Quiz
- Answer validation
- Score and progress
- Mistake review
- Flashcards
- Basic statistics
- Simple league
- Admin CMS
- Deployable production environment

The MVP is not complete until the learner has a reason to return the next day.

---

# 4. Learning Loop

The MVP learning loop:

Login
→ Dashboard
→ Start Quiz
→ Answer
→ Feedback
→ Progress
→ Mistake Review
→ Flashcards
→ Statistics
→ Return Tomorrow

This loop is the product foundation.

---

# 5. Personas

Primary personas:

Learner:
Wants to study efficiently and see progress.

Content Manager:
Manages datasets, questions and corrections.

Admin:
Monitors users, system health and product performance.

Product Owner:
Uses analytics to decide roadmap.

Engineer:
Builds and maintains the platform.

---

# 6. User Journey

Learner journey:

1. Register
2. Choose learning area
3. See dashboard
4. Start session
5. Answer questions
6. Receive feedback
7. Review mistakes
8. Complete flashcards
9. Track progress
10. Return daily

The product should reduce friction at each step.

---

# 7. User Stories

Example MVP user stories:

As a learner, I want to start a quiz quickly so I can practice daily.

As a learner, I want to review mistakes so I can improve weak areas.

As a learner, I want to see progress so I know I am improving.

As an admin, I want to import datasets so content can be updated without code changes.

As a content manager, I want to disable bad questions so learners do not see incorrect content.

---

# 8. Acceptance Criteria

Every feature must define acceptance criteria.

Example: Submit Answer

- Given an active question
- When learner submits an answer
- Then backend validates correctness
- And returns correct answer after evaluation
- And updates score if eligible
- And records event
- And returns next question if available

---

# 9. Product Metrics

MVP metrics:

- Daily active learners
- Quiz completion rate
- Review completion rate
- Accuracy
- Retention
- Flashcards due/completed
- Weak topic count
- Admin import success rate
- Error rate

---

# 10. Retention Strategy

Retention is created through:

- Daily reviews
- Streak
- Progress visibility
- Weak-topic guidance
- Flashcards due
- League standing
- Personalized next action

The product should answer: What should I do next?

---

# 11. Admin CMS Product Scope

Admin CMS is part of MVP.

MVP admin scope:
- User search
- Dataset import
- Dataset validation
- Learning object management
- Knowledge source management
- Question enable/disable
- Basic analytics
- Error visibility

Without admin CMS, the product is not operationally ready.

---

# 12. Release Strategy

Release stages:

v0.1 Internal Prototype
v0.2 Backend MVP
v0.3 Mobile MVP
v0.4 Admin MVP
v0.5 Private Beta
v1.0 Public MVP

Each release must have a definition of done.

---

# 13. Roadmap Strategy

Roadmap layers:

MVP:
Complete learning loop.

v1.1:
Improved analytics and admin tools.

v2.0:
Adaptive learning and richer recommendation.

v3.0:
Multi-product framework expansion.

v4.0:
AI tutor and organization support.

---

# 14. Product Risks

Risks:
- Too many features before learning loop works
- Weak admin tooling
- Poor content quality
- No retention mechanism
- UI complexity
- Metrics added too late
- Product-specific code polluting platform core

---

# 15. Success Criteria

MVP success criteria:

- Learners can complete daily learning loop.
- Admin can manage content without developer help.
- Backend owns learning rules.
- Product can be deployed.
- Progress is visible.
- Flashcards encourage return.
- Analytics show product behavior.

---

# 16. Product ADRs

ADR-0031: MVP requires a complete learning loop.
ADR-0032: Admin CMS is included in MVP.
ADR-0033: Retention metrics are product-critical.
ADR-0034: Product scope is separated from platform core.
ADR-0035: Dashboard is the primary product surface.

---

# 17. Volume VII Summary

Volume VII defines how the platform becomes a product.

A technically strong system is not enough.

A learning product must create a complete and repeatable learning loop.

---
