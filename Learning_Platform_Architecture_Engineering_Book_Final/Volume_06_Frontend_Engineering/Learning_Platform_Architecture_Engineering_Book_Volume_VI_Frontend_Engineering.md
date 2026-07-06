# Learning Platform Architecture & Engineering Book

# Volume VI — Frontend Engineering

**Subtitle:** Designing the Product Experience Layer of the Learning Platform  
**Version:** 1.0  
**Status:** Architecture Specification  
**Scope:** Platform-level specification  
**Reference Implementation:** K_Game is used only as a mapping example.

---

## Table of Contents

1. Purpose of This Volume
2. Frontend Architecture Principles
3. Universal Runtime Architecture
4. Design System Foundation
5. Official Visual Direction
6. Navigation Architecture
7. State Management
8. API Integration
9. Component Library
10. Quiz UI
11. Dashboard UI
12. Flashcard UI
13. Statistics UI
14. Accessibility
15. RTL and Internationalization
16. Animation and Haptics
17. Offline Strategy
18. Frontend Testing
19. Frontend Anti-Patterns
20. Frontend ADRs
21. Volume VI Summary

---

# 1. Purpose of This Volume

Volume VI defines the frontend engineering architecture for products built on the Learning Platform Framework.

The frontend is responsible for user experience, navigation, visual hierarchy, accessibility and interaction.

The frontend is not responsible for learning correctness, scoring, review scheduling, mastery or league calculation.

Those responsibilities belong to the trusted backend platform.

---

# 2. Frontend Architecture Principles

The frontend must follow these principles:

1. UI renders platform state.
2. Business logic remains backend-owned.
3. Design system is shared across products.
4. Product branding is configurable.
5. Components are reusable.
6. Accessibility is part of MVP quality.
7. Loading, empty and error states are first-class.
8. Offline behavior is designed explicitly, not accidentally.

---

# 3. Universal Runtime Architecture

The reference frontend runtime is Expo with React Native Web.

This creates one universal product codebase that can run as:

- Web application
- Mobile-first browser experience
- Android application
- iOS application

The first deployable surface may be web, but the interaction model should remain mobile-first.

The frontend must be built as a consumer of platform APIs. It must not duplicate:

- scoring
- correctness
- review scheduling
- mastery evaluation
- league ranking
- progress calculation

Shared layers:

- API client
- authentication state
- server-state caching
- design tokens
- reusable screen components
- navigation contracts

Platform-specific differences should be isolated behind thin runtime adapters.

Examples:

- storage adapter
- haptics adapter
- safe-area adapter
- web metadata adapter
- platform-specific build configuration

The architecture should preserve future native builds without forcing the MVP to be native-only.

---

# 4. Design System Foundation

The platform design system defines:

- Color tokens
- Typography tokens
- Spacing scale
- Radius scale
- Shadows
- Motion rules
- Iconography
- Cards
- Buttons
- Inputs
- Progress indicators
- Charts
- Bottom sheets
- Modals

Products may theme the design system but should not rewrite it.

---

# 5. Official Visual Direction

The official product UI direction is a calm, pastel, mobile-first education dashboard.

Characteristics:
- Rounded cards
- Soft contrast
- Pastel visual language
- Dashboard-first layout
- Progress-driven feedback
- Clean typography
- Friendly learning tone
- Lightweight gamification

K_Game uses this direction as its first reference implementation.

---

# 6. Navigation Architecture

Navigation should reflect learning flows.

Core areas:
- Dashboard
- Learn / Quiz
- Review
- Flashcards
- Mistakes
- League
- Statistics
- Profile
- Admin if web-based

Navigation must be simple enough for daily use.

---

# 7. State Management

Frontend state should be divided into:

Server state:
- User profile
- Dashboard
- Questions
- Progress
- Flashcards
- Leaderboard

Client state:
- UI toggles
- Form state
- Navigation state
- Temporary animations

Server state should be fetched, cached and invalidated through a consistent API client strategy.

---

# 8. API Integration

API clients must:

- Attach authentication
- Handle standard errors
- Support retries where safe
- Normalize responses
- Avoid duplicating backend rules
- Provide typed request/response models

The frontend must never calculate score or decide correctness.

---

# 9. Component Library

Core components:

- AppShell
- ScreenContainer
- LearningCard
- QuizCard
- ChoiceButton
- ProgressRing
- StreakBadge
- XPBadge
- Flashcard
- LeaderboardRow
- MistakeCard
- EmptyState
- ErrorState
- LoadingState

Components must be documented and reusable.

---

# 10. Quiz UI

Quiz UI should prioritize clarity.

Required elements:
- Prompt card
- Optional subtitle/chip
- Choice buttons
- Timer
- Progress indicator
- Feedback state
- Next action

Correct answer should only be shown after backend evaluation.

---

# 11. Dashboard UI

Dashboard is the home of the learning loop.

It should include:
- Continue Learning
- Daily goal
- Streak
- XP
- Flashcards due
- Weak topics
- Recent progress
- League summary

Dashboard should create a reason to return tomorrow.

---

# 12. Flashcard UI

Flashcard UI should support quick review.

Required controls:
- Again
- Hard
- Good
- Easy

The UI sends review result to backend. Backend decides schedule.

---

# 13. Statistics UI

Statistics should be understandable.

MVP metrics:
- Questions answered
- Accuracy
- Streak
- XP
- Review completion
- Topic progress
- Weak topics

Charts must be simple and actionable.

---

# 14. Accessibility

Accessibility requirements:
- Sufficient contrast
- Scalable text
- Screen-reader labels
- Touch targets
- Reduced motion support
- RTL readiness
- Clear focus states where applicable

Accessibility is not optional.

---

# 15. RTL and Internationalization

The platform should support RTL products.

Text, icons, navigation and layout should be tested in RTL.

Future internationalization should support:
- Product copy
- Question content
- Admin labels
- Error messages
- Notification text

---

# 16. Animation and Haptics

Animations should support comprehension, not distract.

Use animation for:
- Answer feedback
- Card transitions
- Progress changes
- Success moments

Haptics may support:
- Correct answer
- Wrong answer
- Streak milestone
- Review completion

---

# 17. Offline Strategy

Offline must be explicit.

MVP may support limited offline:
- Cached dashboard
- Cached current session if safe
- Retry queue for non-critical actions

Critical operations like scoring should sync with backend.

---

# 18. Frontend Testing

Frontend tests include:
- Component tests
- Screen tests
- API integration mocks
- Navigation tests
- Snapshot tests for design system components
- E2E flows for MVP learning loop

---

# 19. Frontend Anti-Patterns

Anti-patterns:
- Calculating score in UI
- Duplicating backend rules
- Hardcoding product-specific UI everywhere
- Ignoring loading/error states
- No design tokens
- One-off components
- No RTL planning

---

# 20. Frontend ADRs

ADR-0026: Frontend does not own learning rules.
ADR-0027: Design system is shared across products.
ADR-0028: Product branding is theme-based.
ADR-0029: Dashboard is the primary learning entry point.
ADR-0030: Accessibility is part of MVP definition.
ADR-0031: Expo with React Native Web is the reference universal frontend runtime.

---

# 21. Volume VI Summary

Volume VI defines the frontend engineering model.

The frontend provides a polished learning experience while the backend remains the trusted source of learning truth.

Products may look different, but they should share platform UI principles and component architecture.

---
