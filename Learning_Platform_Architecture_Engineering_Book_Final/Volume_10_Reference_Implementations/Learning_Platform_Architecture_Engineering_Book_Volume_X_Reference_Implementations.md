# Learning Platform Architecture & Engineering Book

# Volume X — Reference Implementations

**Subtitle:** Mapping the Learning Platform Framework to Real Products such as K_Game  
**Version:** 1.0  
**Status:** Architecture Specification  
**Scope:** Reference implementations and product mappings  
**Primary Reference Implementation:** K_Game

---

## Table of Contents

1. Purpose of This Volume
2. Reference Implementation Philosophy
3. K_Game Product Overview
4. K_Game Domain Mapping
5. K_Game Dataset Model
6. K_Game Knowledge Source Mapping
7. K_Game Question Types
8. K_Game Quiz Flow
9. K_Game Answer Rules
10. K_Game Scoring Rules
11. K_Game Flashcard Mapping
12. K_Game Mistake Review
13. K_Game League Mapping
14. K_Game Progress Mapping
15. K_Game Admin CMS
16. K_Game API Mapping
17. K_Game Frontend Mapping
18. K_Game Design System Mapping
19. K_Game Backend Mapping
20. K_Game Deployment Mapping
21. K_Game MVP Definition
22. Future Reference Implementations
23. Reference Implementation ADRs
24. Reference Implementation Anti-Patterns
25. Implementation Checklist
26. Volume X Summary

---

# 1. Purpose of This Volume

Volume X defines how concrete products are implemented on top of the Learning Platform Framework.

All previous volumes are platform-level.

This volume is different.

It maps the abstract platform concepts to real products.

The first reference implementation is K_Game.

K_Game proves that the framework can support a real learning product with:
- Domain dataset
- Question generation
- Quiz engine
- Flashcards
- Mistake review
- League
- Analytics
- Admin CMS
- Mobile UI
- Deployment

Future products such as K_Anatomy, K_Physiology, K_Nursing or K_Chemistry should follow the same mapping pattern.

---

# 2. Reference Implementation Philosophy

A reference implementation validates the platform.

It must not redefine the platform.

A reference implementation should:
- Use platform contracts
- Implement product-specific plugins
- Provide domain mappings
- Configure engines
- Provide dataset adapters
- Provide product UI theme
- Extend admin CMS where needed

A reference implementation should not:
- Modify platform core for product-only behavior
- Put product-specific concepts into shared kernel
- Duplicate platform rules
- Calculate learning truth in frontend

---

# 3. K_Game Product Overview

K_Game is the first product built on the Learning Platform Framework.

It focuses on pharmacology and drug learning.

Main user value:
- Practice drug knowledge
- Review mistakes
- Build long-term retention
- Track progress
- Compete through league
- Use flashcards for reinforcement

K_Game is not only a quiz app.

It is a pharmacology learning product powered by the platform.

---

# 4. K_Game Domain Mapping

K_Game maps platform concepts as follows:

| Platform Concept | K_Game Mapping |
|---|---|
| Learning Object | Drug |
| Learning Topic | Drug Topic |
| Knowledge Source | Drug Question Source |
| Assessment Item | Drug Question |
| Answer | Drug Answer |
| Learning Session | Game Session |
| Review Item | Flashcard State |
| Mistake | Drug Mistake |
| League Result | Weekly Game Result |
| Progress | User Drug Learning Progress |

This mapping must remain explicit.

---

# 5. K_Game Dataset Model

K_Game datasets may include:

- Drug list
- Generic names
- Brand names
- Persian names
- Drug forms
- Indications
- Side effects
- Food timing
- Classification
- Dosing
- Pregnancy and breastfeeding information
- Dose adjustment
- Educational notes
- Source metadata

The canonical K_Game import format is a versioned JSON document bundle. Each document contains:

- `schema_version`
- `source` file identity, SHA-256 checksum and authoring metadata
- `extraction` method, mode, OCR flag and extraction timestamp
- `content.tables[].records[]`
- `warnings`
- `enrichment.drug_names` provenance and summary

The normalized drug contract contains:

- English generic name
- Persian generic name
- Brand names
- Dosage forms
- Dosing and administration
- Indications
- Food relation
- Pregnancy information
- Breastfeeding information
- Dose adjustment
- Side effects
- Clinical notes
- ATC code, class, subclass and category
- Source category
- Source document, table and row identity

Header aliases such as `رابطه با غذا` and `فاصله با غذا`, `تنظیم دوز` and `تنطیم دوز`, or combined dosing/indication columns must map into the normalized contract. Valid document-specific columns such as opioid equivalence, duration of action or corticosteroid potency remain in `extra_attributes` with their original header names.

`full_text`, table cell geometry and extraction internals are audit material, not duplicated learning-object columns. The complete original record is retained for traceability.

Dataset import must produce:
- Created records
- Updated records
- Invalid rows
- Missing fields
- Duplicate warnings
- Broken question warnings

Replacement import rules:

- validate every JSON document before changing active metadata
- accept only supported schema versions
- skip rows explicitly classified as headings or non-generic products by the enrichment report
- generate stable IDs from source checksum, table index and source row
- replace the previous K_Game drug metadata in one transaction
- preserve generic Knowledge Source links used by historical learning records
- synchronize all active question sources after import

---

# 6. K_Game Knowledge Source Mapping

A Drug Question Source is a K_Game implementation of Knowledge Source.

Examples:

Brand to generic:
Prompt: نام ژنریک داروی تجاری X کدام است؟

Indication:
Prompt: کاربرد اصلی داروی X کدام است؟

Side effects:
Prompt: کدام مورد از عوارض جانبی مهم داروی X است؟

Food timing:
Prompt: داروی X چه زمانی نسبت به غذا مصرف می‌شود؟

Additional sources may be generated from:

- dosage form
- dosing and administration
- ATC classification
- pregnancy and breastfeeding guidance
- dose adjustment

Each source must be traceable to a Drug and a Topic.

---

# 7. K_Game Question Types

MVP question types:

- brandGeneric
- genericBrand
- indication
- sideEffects
- timing
- classification
- dosageForm
- dosing
- pregnancy
- doseAdjustment

Each question type should have:
- Generator
- Valid distractor strategy
- Correct answer source
- Explanation source
- Quality validation

---

# 8. K_Game Quiz Flow

K_Game quiz flow:

1. User starts game in random mode or target-category mode.
2. Backend creates GameSession.
3. Quiz Engine selects sources.
4. Question Generation Engine creates GameQuestions.
5. Frontend receives safe question payload.
6. User submits answer.
7. Backend evaluates answer.
8. Score Engine calculates score.
9. Mistake Engine records mistake if needed.
10. Progress Engine updates progress.
11. Session continues or finishes.

Frontend must not calculate correctness or score.

K_Game game modes:
- User first selects question type: brand/generic, food timing, indication or side effects.
- Random mode selects from active K_Game Knowledge Sources.
- Random mode accepts a learner-selected question count from 10 to 100 in multiples of 10.
- Target-category mode filters by broad drug category such as cardiovascular, CNS, respiratory, endocrine, GI or infection.
- Target-category mode still uses server-side source selection and scoring.

---

# 9. K_Game Answer Rules

Answer evaluation rules:

- Correctness is determined server-side.
- Score is determined server-side.
- Correctness and scoring are separate.
- Late correct answers may be correct but worth zero points.
- Mistakes should be created for wrong answers.
- Product rules decide whether late correct answers create mistakes.
- Correct answer snapshot must be stored with answer history.

This preserves analytics integrity.

---

# 10. K_Game Scoring Rules

MVP scoring:

- Correct answer: base score
- Streak bonus: optional
- Time bonus: optional for league
- Wrong answer: zero score
- Timeout: zero score
- Late correct: correct but zero score

Scoring rules must be versioned when changed.

Historical results should preserve original score calculation.

---

# 11. K_Game Flashcard Mapping

Flashcard State maps to Review Item.

Flashcards may be created from:
- All active K_Game Knowledge Sources
- Saved questions
- Weak topics
- Important knowledge sources

For K_Game MVP, the primary new-card entry point is category-based deck creation from active Knowledge Sources. Quiz mistakes remain independent and do not automatically create flashcards.
The flashcard flow starts with a choice between a question type and the learner's global Leitner queue. Choosing a question type advances to target-category selection and then directly to the focused card stage. Opening Leitner bypasses question type and category because its records are learner-wide within K_Game.
Deck creation schedules every active Knowledge Source matching the selected question type and category. It must not sample a random fixed-size subset.

New-card rules:
- Seeded but unseen cards use box 0, state New and no due date.
- New cards are never included in dashboard due counts or Leitner summaries.
- Known completes a new card outside Leitner.
- Unknown moves a new card into box 1.

Prompt naming rules:
- Brand/generic questions use the brand name in the prompt.
- Food timing, indication and side-effect questions use the generic name in the prompt.
- If the imported dataset lacks a dedicated generic field, the product may fall back to the generic-like name field.

Review responses:
- Known
- Unknown

K_Game uses a five-box Leitner review policy:
- Unknown on a new card enters box 1.
- Unknown in an active box moves one box forward.
- Unknown in box 5 remains in box 5.
- Known in an active box moves one box backward.
- Known in box 1 removes the card from active review.
- Leitner contents are not filtered by their original question type or category.
- A reviewed card leaves the current box immediately and follows the box-transition rule.

Flashcards are a learning surface for the full K_Game knowledge graph, not a mistake queue.

---

# 12. K_Game Mistake Review

Mistake review is required for MVP.

A Mistake should store:
- User
- Topic
- Source
- Wrong count
- Last wrong answer
- Last occurrence
- Related learning object

Mistakes power:
- Review sessions
- Weak topic detection
- Dashboard recommendations

---

# 13. K_Game League Mapping

K_Game league is a product implementation of competitive learning.

MVP league:
- Weekly season
- Top 100 leaderboard
- User rank
- Weekly XP or score
- Tie-breaker by accuracy or time

League must not compromise learning integrity.

Leaderboard should use server-side results only.

---

# 14. K_Game Progress Mapping

K_Game progress includes:

- Questions answered
- Accuracy
- Correct count
- Streak
- XP
- Topic progress
- Flashcards due
- Mistakes
- Weak topics
- League rank

Dashboard should surface the most actionable progress information.

---

# 15. K_Game Admin CMS

K_Game Admin CMS must support:

- Drug management
- Topic management
- Question source management
- Dataset import
- Dataset validation
- Question enable/disable
- Duplicate detection
- Broken question detection
- User search
- User progress inspection
- League monitoring
- Error logs
- Import logs
- Analytics dashboard

Admin CMS is part of MVP.

---

# 16. K_Game API Mapping

K_Game API groups:

Auth:
- register
- login
- logout
- me

Content:
- topics
- target categories
- drugs
- question sources

Game:
- start game
- answer question
- finish game
- game detail
- random/count mode
- target-category mode

Review:
- due flashcards
- Leitner box summary
- review flashcard
- seed learning flashcards
- mistakes

League:
- leaderboard
- my rank

Statistics:
- dashboard
- progress
- weak topics

Admin:
- dataset import
- validation report
- content management

---

# 17. K_Game Frontend Mapping

K_Game frontend uses the platform design system.

K_Game uses Expo with React Native Web as its reference frontend runtime.

The same product codebase should support:

- web deployment
- mobile-first browser usage
- future Android builds
- future iOS builds

The frontend remains a rendering and interaction layer. Backend APIs remain the source of truth for correctness, scoring, review scheduling, progress and league ranking.

Screens:
- Auth
- Dashboard
- Quiz
- Result
- Flashcards
- Mistakes
- League
- Statistics
- Profile
- Settings

Official UI direction:
- Calm pastel
- Card-based
- Rounded
- Mobile-first
- Learning dashboard style
- Progress-focused
- Friendly and professional

---

# 18. K_Game Design System Mapping

K_Game theme should define:

- Primary colors
- Accent colors
- Background
- Card colors
- Typography
- Spacing
- Radius
- Shadows
- Icons
- Motion

Design tokens should be reusable by future products.

Product themes should not rewrite component logic.

---

# 19. K_Game Backend Mapping

K_Game backend implements product-specific apps or modules:

- accounts
- drugs
- quizzes
- games
- flashcards
- league
- analytics
- admin
- core

Product-specific code such as Drug models should stay outside platform core.

Reusable logic should be extracted into platform-level modules if needed by future products.

---

# 20. K_Game Deployment Mapping

K_Game MVP deployment may include:

- Backend web service
- PostgreSQL database
- Static file hosting
- Mobile app build
- Admin access
- Error tracking
- Structured logs
- Backups
- Health endpoint

Future scaling may add:
- Redis
- Background workers
- Event processing
- Analytics pipeline

---

# 21. K_Game MVP Definition

K_Game MVP includes:

- Authentication
- Learning dashboard
- Quiz session
- Answer validation
- Score and streak
- Mistake review
- Flashcards
- Basic statistics
- Simple league
- Admin CMS
- Dataset import
- Production deployment

The MVP is complete when a learner can return daily and continue learning.

---

# 22. Future Reference Implementations

Future products should add chapters to this volume.

Each chapter should define:
- Product purpose
- Domain mapping
- Dataset model
- Knowledge source mapping
- Question types
- Engine configuration
- Admin CMS extensions
- UI theme
- API mapping
- Deployment notes

Examples:
- K_Anatomy
- K_Physiology
- K_Nursing
- K_Chemistry
- K_Language

---

# 23. Reference Implementation ADRs

ADR-0046: K_Game is the first reference implementation.
ADR-0047: Product mappings must be explicit.
ADR-0048: Product-specific code must remain outside platform core.
ADR-0049: Admin CMS is required for each serious product.
ADR-0050: Future products must follow the mapping template defined in this volume.

---

# 24. Reference Implementation Anti-Patterns

Anti-patterns:

- Treating K_Game as the platform.
- Moving Drug concepts into platform core.
- Duplicating platform engines inside product code.
- Calculating score in mobile app.
- Building admin tools after launch.
- Ignoring dataset validation.
- Creating new product without domain mapping.
- Rewriting platform for every product.

---

# 25. Implementation Checklist

For each product implementation:

- Define product purpose.
- Define target users.
- Map domain entities to platform concepts.
- Define dataset schema.
- Define knowledge source model.
- Define question types.
- Define generators.
- Configure engines.
- Define admin CMS needs.
- Define API mappings.
- Define UI theme.
- Define analytics.
- Define deployment requirements.
- Document product-specific ADRs.

---

# 26. Volume X Summary

Volume X explains how products are built on top of the Learning Platform Framework.

K_Game is the first reference implementation.

It validates the framework for a real pharmacology learning product.

Future products should follow the same mapping structure instead of redesigning the platform.

The platform is built once.

Products are built on top of it.

---
