# Learning Platform Architecture & Engineering Book

# Volume IX — Engineering Handbook

**Subtitle:** Team Standards for Building and Maintaining the Learning Platform  
**Version:** 1.0  
**Status:** Architecture Specification  
**Scope:** Platform-level engineering handbook  
**Reference Implementation:** Pharmexa is used only as a mapping example.

---

## Table of Contents

1. Purpose of This Volume
2. Engineering Culture
3. Repository Organization
4. Project Structure Standards
5. Naming Conventions
6. Coding Standards
7. Service Layer Standards
8. Rule Standards
9. Selector Standards
10. Event Standards
11. Git Workflow
12. Commit Convention
13. Pull Request Standards
14. Code Review Checklist
15. Definition of Done
16. Sprint Workflow
17. Architecture Decision Records
18. Documentation Standards
19. Testing Standards
20. Security Checklist
21. Performance Checklist
22. Release Checklist
23. Incident Process
24. Technical Debt Policy
25. Contribution Standards
26. Engineering ADRs
27. Engineering Anti-Patterns
28. Volume IX Summary

---

# 1. Purpose of This Volume

Volume IX defines the Engineering Handbook for teams implementing the Learning Platform Framework.

This volume is not about product features.

It defines how engineering work should be performed so that architecture, code quality, documentation, security and delivery remain consistent as the platform grows.

The handbook is intended for:
- Backend engineers
- Frontend engineers
- Mobile engineers
- QA engineers
- DevOps engineers
- Product engineers
- Technical leads
- Future contributors

If Volumes I through VIII define what the platform is, Volume IX defines how teams should build it.

---

# 2. Engineering Culture

The platform requires a culture of disciplined engineering.

Core expectations:
1. Architecture is respected.
2. Product code does not pollute platform core.
3. Business rules are explicit.
4. Documentation changes with code.
5. Tests are part of implementation.
6. Releases are controlled.
7. Incidents generate learning.
8. Technical debt is visible.

Engineering culture is not created by tools. It is created by repeated decisions.

---

# 3. Repository Organization

A recommended repository may contain:

- backend/
- frontend/
- products/
- platform/
- docs/
- BluePrint/
- Architecture_Book/
- scripts/
- tests/
- infra/
- admin/
- datasets/

For early MVP, the repository may be simpler, but the conceptual boundaries should still be respected.

The platform should be organized around domains and modules, not random technical folders.

---

# 4. Project Structure Standards

Backend modules should follow clear responsibility boundaries.

Recommended module structure:

- models.py
- serializers.py or schemas.py
- views.py or controllers.py
- urls.py or routes.py
- services/
- selectors.py
- rules.py
- events.py
- permissions.py
- validators.py
- tests/

Rules:
- Views/controllers do not contain business logic.
- Services orchestrate use cases.
- Rules own decision logic.
- Selectors own read queries.
- Events describe facts.
- Tests live close to the module or in dedicated test packages.

---

# 5. Naming Conventions

Names must communicate intent.

Good names:
- StartLearningSessionService
- SubmitAnswerService
- ReviewScheduler
- ScoreCalculator
- get_due_reviews
- QuestionAnswered
- LearningObjectMastered

Poor names:
- helper.py
- utils.py
- manager.py
- process_data
- do_stuff

Naming rules:
- Use domain language.
- Avoid vague names.
- Use past tense for events.
- Use verbs for services.
- Use nouns for entities and value objects.

---

# 6. Coding Standards

General standards:

- Keep functions small and focused.
- Avoid hidden side effects.
- Prefer explicit dependencies.
- Avoid duplicated business rules.
- Keep rule logic testable.
- Separate reads from writes when useful.
- Avoid overengineering before product need, but preserve boundaries.

Every code change should improve or preserve clarity.

Code should be readable by future engineers who were not present during initial development.

---

# 7. Service Layer Standards

Services represent use cases.

A service may:
- Validate operation state
- Call rule engines
- Use selectors
- Persist changes
- Emit events
- Return application results

A service should not:
- Render responses
- Contain SQL-heavy read logic
- Hide unrelated business rules
- Become a God object
- Directly implement product-specific plugin internals unless inside a product boundary

Large services should be decomposed.

---

# 8. Rule Standards

Rules are first-class engineering assets.

A rule must be:
- Named
- Testable
- Documented
- Versioned if business impact is significant
- Owned by the correct bounded context

Examples:
- TimeoutRule
- ScoringRule
- MistakeCreationRule
- ReviewSchedulingRule
- MasteryRule

Rules should not be duplicated in frontend, admin tools or analytics scripts.

---

# 9. Selector Standards

Selectors own read access patterns.

A selector should answer a clear question.

Examples:
- get_current_question
- get_user_dashboard_summary
- get_due_review_items
- get_weekly_leaderboard
- get_weak_topics

Selectors improve:
- Readability
- Performance tuning
- Testability
- API consistency

Avoid query logic scattered across views and services.

---

# 10. Event Standards

Events are facts.

Events should:
- Use past tense
- Include stable identifiers
- Include timestamp
- Include product/context metadata when needed
- Avoid storing secrets
- Be documented

Examples:
- QuestionAnswered
- ReviewCompleted
- LearningSessionFinished
- DatasetImported
- AdminUserUpdatedQuestion

Events are used for analytics, audit logs and future automation.

---

# 11. Git Workflow

Recommended workflow:

- main: production-ready
- develop or staging: integration branch if needed
- feature branches: short-lived work
- hotfix branches: urgent production fixes

Branch naming examples:
- feature/quiz-engine
- feature/admin-dataset-import
- fix/answer-timeout-rule
- docs/volume-ix-handbook
- hotfix/leaderboard-cache

Every merge should pass automated checks.

---

# 12. Commit Convention

Use meaningful commits.

Recommended format:

type(scope): summary

Examples:
- feat(quiz): add answer submission service
- fix(scoring): handle late correct answers
- docs(architecture): update rule engine section
- test(review): add spaced repetition tests
- refactor(admin): extract dataset validation service

Useful commit types:
- feat
- fix
- docs
- test
- refactor
- chore
- perf
- security

---

# 13. Pull Request Standards

Every pull request should include:

- What changed
- Why it changed
- How it was tested
- Screenshots if UI
- API examples if API changed
- Migration notes if database changed
- Risk level
- Rollback notes if needed

PRs should be small enough to review carefully.

Large architecture changes require ADR updates.

---

# 14. Code Review Checklist

Reviewers should check:

- Is the architecture respected?
- Is business logic in the correct layer?
- Are tests included?
- Are permissions correct?
- Are API contracts stable?
- Are errors handled?
- Are queries efficient?
- Are docs updated?
- Are events emitted when needed?
- Is product-specific logic isolated?
- Are secrets avoided?
- Is the change observable?

---

# 15. Definition of Done

A feature is done only when:

- Code is implemented.
- Tests are written.
- API contract is documented.
- Permissions are reviewed.
- Error cases are handled.
- Observability is considered.
- Admin impact is considered.
- Documentation is updated.
- Product acceptance criteria are met.
- No critical regressions exist.

Done does not mean only that the happy path works.

---

# 16. Sprint Workflow

Recommended sprint flow:

1. Define scope.
2. Confirm architecture placement.
3. Define acceptance criteria.
4. Implement.
5. Test.
6. Document.
7. Review.
8. Merge.
9. Deploy to staging.
10. Validate.
11. Release.

Each sprint should produce a stable increment.

---

# 17. Architecture Decision Records

ADR is required when a decision affects:

- Platform architecture
- Module boundaries
- Data model
- API contract
- Security model
- Deployment strategy
- Plugin system
- Learning rules
- Admin operations

ADR format:
- Title
- Status
- Context
- Decision
- Consequences
- Alternatives considered

---

# 18. Documentation Standards

Documentation is part of the product.

Required documentation types:
- Architecture Book
- API documentation
- Admin guide
- Dataset guide
- Developer setup
- Testing guide
- Deployment guide
- Release notes
- ADRs

Documentation should be updated in the same workflow as code.

---

# 19. Testing Standards

Testing levels:

- Unit tests for rules
- Service tests for use cases
- Selector tests for queries
- API tests for contracts
- Permission tests
- Dataset validation tests
- UI component tests
- E2E tests for critical flows

Critical learning rules require strong coverage.

Untested scoring or review logic is not acceptable.

---

# 20. Security Checklist

Before release, verify:

- Authentication enforced
- Authorization checked
- Admin routes protected
- Rate limiting considered
- Secrets are not committed
- CORS configured
- Inputs validated
- Sensitive data not logged
- Dependencies checked
- Backups secured
- Audit logs available for admin actions

---

# 21. Performance Checklist

Performance review should include:

- API response time
- Query count
- Slow queries
- Indexes
- Cache usage
- Background job duration
- Dashboard load time
- Leaderboard performance
- Dataset import performance

Performance should be measured, not guessed.

---

# 22. Release Checklist

Before release:

- Tests pass
- Migrations reviewed
- Environment variables configured
- Rollback plan ready
- Monitoring active
- Error tracking active
- Admin account secured
- Backup available
- Release notes written
- Product owner approval captured

---

# 23. Incident Process

Incident response steps:

1. Detect
2. Triage
3. Assign owner
4. Mitigate
5. Communicate
6. Resolve
7. Write postmortem
8. Add prevention tasks

Incidents should improve the platform.

---

# 24. Technical Debt Policy

Technical debt must be visible.

Debt items should include:
- Description
- Impact
- Risk
- Owner
- Suggested fix
- Priority

Hidden debt becomes architecture decay.

Debt may be acceptable temporarily, but not invisible.

---

# 25. Contribution Standards

Contributors must follow:

- Architecture boundaries
- Coding standards
- Test requirements
- Documentation requirements
- Security guidelines
- PR review process

A contributor should be able to understand the platform through this book before modifying core modules.

---

# 26. Engineering ADRs

ADR-0041: Business logic must not live in views.
ADR-0042: Every major architectural decision requires ADR.
ADR-0043: Tests are part of definition of done.
ADR-0044: Documentation changes with code.
ADR-0045: Product extensions must not modify platform core directly.

---

# 27. Engineering Anti-Patterns

Anti-patterns:
- Large unreviewable PRs
- Hidden business logic
- No tests for rules
- Documentation afterthought
- Direct production database edits
- Product-specific platform hacks
- Untracked technical debt
- No rollback plan
- Ignored monitoring failures

---

# 28. Volume IX Summary

Volume IX defines how engineering teams should work on the Learning Platform.

The goal is consistency, maintainability and long-term platform health.

Good architecture can still fail if engineering practices are weak.

This handbook protects the architecture during real implementation.

---
