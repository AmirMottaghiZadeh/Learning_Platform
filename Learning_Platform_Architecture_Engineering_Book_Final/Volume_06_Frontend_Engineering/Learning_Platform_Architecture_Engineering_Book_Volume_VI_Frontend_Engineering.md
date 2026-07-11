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

The official product UI direction is an immersive, dark, mobile-first learning game dashboard.

Characteristics:
- Deep navy and blue-green foundations with high-contrast off-white text
- Electric green and turquoise accents reserved for progress, selection and primary actions
- Rounded, layered cards with translucent borders and controlled depth
- Dashboard-first information hierarchy with one obvious next action
- Compact metric pills, progress rings, streak indicators and leaderboard states
- Floating pill-shaped bottom navigation
- Clean, bold typography with restrained supporting copy
- Purposeful motion for entrance, selection, progress and answer feedback
- Premium game-like energy without sacrificing clinical-learning clarity
- Responsive mobile composition centered inside a wider atmospheric web stage

K_Game uses this direction as its first reference implementation.

The default theme tokens are:
- Background: deep navy-green
- Surface: dark teal
- Elevated surface: brighter blue-green
- Primary accent: electric green
- Secondary accent: turquoise
- Primary text: cool off-white
- Secondary text: muted blue-gray
- Border: translucent white

Pastel colors may only appear as low-opacity semantic glows. They are not the primary surface language.

Brand and launch assets follow the same visual contract:
- The product-provided Pharmexa artwork is the source of truth for application icons.
- Square application icons place the artwork on the official deep navy-green background.
- PWA icon sets provide both standard and maskable variants with platform-safe padding.
- Browser favicon and Apple touch icons derive from the same source artwork.
- Native and PWA launch surfaces use the official background color and a centered brand icon.
- The initial web document paints the launch surface before JavaScript loads so a white flash is never visible.
- Launch motion is a short opacity and scale transition and must not delay application readiness.

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

The persistent mobile navigation contains five destinations:
- Home
- Quiz
- Review
- League
- Profile

Planning, Mistakes and Statistics remain first-class screens but are entered contextually from dashboard cards, profile shortcuts or learning-result actions.

The mobile navigation is a floating rounded dock. The active destination uses an accent-filled capsule and may display its label; inactive destinations remain compact and icon-led. Navigation must be simple enough for daily use, preserve safe-area spacing and remain usable at narrow widths.

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
- BrandMark
- LearningCard
- GlassCard
- QuizCard
- ChoiceButton
- ProgressRing
- MetricPill
- SectionHeader
- AnimatedEntrance
- Avatar
- StreakBadge
- XPBadge
- Flashcard
- LeaderboardRow
- MistakeCard
- EmptyState
- ErrorState
- LoadingState

Components must be documented and reusable.

Shared components must use semantic design tokens rather than screen-specific literal colors. Pressable components provide visible pressed, selected, disabled and keyboard-focus states. Repeated information patterns such as metrics, ranking rows, choice states and progress visualization belong in the component library instead of individual screens.

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

The active quiz state uses a focused single-task composition: compact session metrics, a prominent timer/progress visualization, one question card and clearly separated answers. Selection and backend feedback are visually distinct. Setup controls may use horizontally wrapping chips, but must preserve all supported question types.

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

The dashboard visual hierarchy is:
1. Personal greeting and account affordance
2. Daily mission with progress ring and primary CTA
3. Compact learning-mode shortcuts
4. Actionable upcoming or recommended sessions
5. Performance, weak-topic and league summaries

Secondary metrics must not compete visually with the primary next action.

---

# 12. Flashcard UI

Flashcard UI should support quick review.

The K_Game flashcard entry is a progressive flow rather than one long configuration page:
1. Choose one question type or open the global Leitner box.
2. For a new-card path, choose a target category.
3. Enter the focused card stage.

Only the current step is presented as the primary surface. Back navigation may return to the previous choice without mixing all configuration controls into the card stage.

The global Leitner action is displayed beside the question-type choices in the first step. It is independent of question type and category. Unseen cards are labelled New and are never presented as Due or as members of a Leitner box.

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
- Screen fade and short vertical entrance
- Card stagger on first presentation
- Press scale and selected-state transitions
- Answer feedback
- Card transitions
- Progress changes
- Success moments

Haptics may support:
- Correct answer
- Wrong answer
- Streak milestone
- Review completion

Default motion is short and responsive:
- Micro interaction: 120–180 ms
- Component transition: 180–260 ms
- Screen entrance: 260–360 ms

Movement should use opacity and transform where possible. Continuous decorative motion is avoided. Reduced-motion preferences must disable non-essential movement while retaining state feedback.

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
