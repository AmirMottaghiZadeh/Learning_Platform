# Learning Platform / K_Game

Reusable learning-platform architecture with a Django REST backend, a K_Game reference implementation, an Expo + React Native Web client, and an internal data-quality workflow for safe medical/drug data improvement.

K_Game is not designed as a one-off quiz app. It is the first implementation of a broader Learning Platform: a backend-owned learning system where products can plug into shared learning objects, question sources, game rules, review logic, progress tracking, league mechanics, and operational tooling.

## Table Of Contents

- [Purpose](#purpose)
- [Problem](#problem)
- [Solution](#solution)
- [Product Scope](#product-scope)
- [Architecture](#architecture)
- [Repository Layout](#repository-layout)
- [Backend](#backend)
- [Frontend](#frontend)
- [Data Quality Center](#data-quality-center)
- [AI Data Pipeline](#ai-data-pipeline)
- [Local Development](#local-development)
- [Production And Deployment](#production-and-deployment)
- [Testing And Quality Gates](#testing-and-quality-gates)
- [Security And Safety](#security-and-safety)
- [MVP Status](#mvp-status)
- [Roadmap](#roadmap)

## Purpose

The project exists to build a professional learning platform that can support multiple domain-specific learning products. K_Game is the current reference implementation focused on drug knowledge training.

The platform separates reusable learning infrastructure from product-specific content:

- The platform owns authentication, learning objects, knowledge sources, progress, review scheduling, game/session lifecycle, statistics, league primitives, API contracts, operations, and data governance.
- K_Game owns drug-specific datasets, drug categories, question types, prompt generation, and the user-facing learning experience.

This separation keeps the project extensible. A future implementation should be able to reuse the platform without copying K_Game-specific assumptions.

## Problem

Drug learning is usually fragmented across static lists, flashcard tools, quiz banks, and manually maintained spreadsheets. These approaches create several problems:

- Learning data is duplicated and hard to audit.
- Quiz logic often lives in the frontend, making correctness difficult to control.
- Flashcards are disconnected from structured learning objectives.
- User progress, mistakes, weak topics, and review scheduling are not unified.
- Medical/drug data quality improvements are risky when edits are made directly in production records.
- Small MVPs often lack operational maturity: health checks, backups, deploy checks, schema validation, and safe release paths.

This project addresses those issues by treating learning as a platform problem, not only a UI problem.

## Solution

The platform provides a backend-first learning system with:

- Structured learning objects and knowledge sources.
- Drug-specific K_Game data adapters.
- Quiz generation and game sessions controlled by backend rules.
- Flashcards built from the same knowledge-source layer.
- Leitner review logic for independent flashcard learning.
- League, statistics, mistakes, weak-topic, and dashboard APIs.
- Mobile-first Expo + React Native Web frontend.
- Data Quality Center for internal review of rule-based or future AI suggestions.
- Production operations foundation with Docker, health checks, CI, backups, and deployment workflows.

The frontend is intentionally a consumer of backend state. It renders the learning experience, but it does not own scoring, correctness, review scheduling, league ranking, or data mutation rules.

## Product Scope

Current K_Game learning dimensions:

- Brand/generic name learning.
- Food/timing learning.
- Indication learning.
- Side-effect learning.
- Drug category based study flows.
- Random and category-based quiz/game sessions.
- Leitner flashcard boxes.
- Mistake review.
- Dashboard, streak, progress, weak-topic, statistics, and league views.

The UI direction is a calm clinical learning dashboard: mobile-first, card-based, educational, soft clinical colors, clear progress indicators, and low visual noise.

## Architecture

```text
                    +-----------------------------+
                    | Expo + React Native Web     |
                    | Mobile-first K_Game client  |
                    +--------------+--------------+
                                   |
                                   | REST / Token Auth
                                   |
+----------------------------------v----------------------------------+
|                         Django REST Backend                         |
|                                                                     |
|  accounts        auth, tokens, current user                         |
|  core            health, errors, pagination, schema, logging        |
|  learning        learning objects, progress, dashboard, stats       |
|  drugs           K_Game drug data, categories, source sync          |
|  quizzes         selectors and question generation                  |
|  games           sessions, answers, scoring, timer, lifecycle       |
|  flashcards      Leitner states, review, deck summaries             |
|  league          rankings, seasons, leaderboard summaries           |
|  ai_data_pipeline safe batch-based data suggestions and apply flow   |
|  data_quality_center internal review UI                             |
|                                                                     |
+----------------------------------+----------------------------------+
                                   |
                                   | ORM / migrations
                                   |
                    +--------------v--------------+
                    | SQLite local / PostgreSQL   |
                    | production-like deployment  |
                    +-----------------------------+
```

### Platform Principles

- Backend owns learning correctness.
- Frontend renders state and submits user intent.
- Product implementations adapt domain data into platform contracts.
- Medical/drug data changes must be reviewable, auditable, and reversible.
- Every production path should be observable, deployable, and recoverable.
- No AI or rule provider directly modifies production data.

## Repository Layout

```text
.
├── backend/
│   ├── apps/
│   │   ├── accounts/
│   │   ├── ai_data_pipeline/
│   │   ├── core/
│   │   ├── data_quality_center/
│   │   ├── drugs/
│   │   ├── flashcards/
│   │   ├── games/
│   │   ├── league/
│   │   ├── learning/
│   │   └── quizzes/
│   ├── config/
│   ├── data/
│   ├── Dockerfile
│   ├── build.sh
│   ├── gunicorn.conf.py
│   ├── render.yaml
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── api/
│   │   ├── components/
│   │   ├── design/
│   │   ├── navigation/
│   │   ├── screens/
│   │   ├── store/
│   │   └── types/
│   ├── App.tsx
│   ├── app.config.js
│   ├── app.json
│   ├── Dockerfile
│   └── package.json
├── docs/
│   ├── GITHUB_PRIVATE_SETUP.md
│   └── OPERATIONS_RUNBOOK.md
├── Learning_Platform_Architecture_Engineering_Book_Final/
├── docker-compose.yml
└── README.md
```

## Backend

Technology:

- Python 3.11
- Django 5
- Django REST Framework
- Token Authentication
- drf-spectacular OpenAPI
- SQLite for local development
- PostgreSQL for production-like deployment
- Gunicorn and WhiteNoise for production serving

Important local URLs:

- `GET /api/v1/health/`
- `GET /api/v1/live/`
- `GET /api/v1/ready/`
- `GET /api/v1/schema/`
- `GET /api/v1/docs/`
- `/admin/`
- `/data-quality/`

API modules under `/api/v1/`:

- `auth/`
- `topics/`
- `target-categories/`
- `drugs/`
- `me/dashboard/`
- `me/progress/`
- `me/statistics/`
- `me/weak-topics/`
- `games/`
- `flashcards/`
- `league/`

## Frontend

Technology:

- Expo
- React Native Web
- TypeScript
- lucide-react-native icons
- Mobile-first layout
- Clinical calm dashboard theme

Production frontend:

```text
https://AmirMottaghiZadeh.github.io/Learning_Platform/
```

Production API base:

```text
https://amirmtz.runflare.run/api/v1
```

The GitHub Pages build uses:

```text
EXPO_BASE_URL=/Learning_Platform
EXPO_PUBLIC_API_BASE_URL=https://amirmtz.runflare.run/api/v1
```

Local development still uses the local API by default:

```text
http://127.0.0.1:8000/api/v1
```

## Data Quality Center

The Data Quality Center is an internal web application for reviewing and validating data-quality suggestions.

URL:

```text
/data-quality/
```

It provides:

- Dashboard with health score and issue counts.
- Batch center.
- Job center.
- Suggestion review center.
- Side-by-side diff review.
- Record inspector.
- Health center.
- Report pages and downloads.

The Data Quality Center is the primary daily interface for reviewing data improvements. Django Admin remains available for developer inspection, but direct admin CRUD is not the preferred operational workflow.

## AI Data Pipeline

The AI Data Pipeline is currently local and rule-based. It does not call OpenAI, Ollama, or any external AI provider.

Safety model:

1. Scan the database.
2. Generate pending suggestions.
3. Review suggestions manually.
4. Approve, reject, or edit suggestions.
5. Apply only approved suggestions through the safe apply command.
6. Create backup before applying.
7. Write all applied changes to audit history.

Provider structure:

- `rules`: deterministic local provider, active today.
- `mock`: test provider.
- `openai`: placeholder, disabled.
- `ollama`: placeholder, disabled.
- `manual`: manual source marker.

Core tables:

- `ai_data_batches`
- `ai_data_jobs`
- `ai_data_suggestions`
- `ai_data_change_history`
- `ai_data_reports`
- `ai_data_translations`

Useful commands:

```bash
cd backend
python manage.py ai_health_check
python manage.py ai_generate_suggestions --provider rules --limit 500 --include-normalization --include-terminology --include-duplicates --include-medical-validation --batch-name "Initial local cleanup review"
python manage.py ai_generate_report --batch-id 1
```

Apply approved suggestions only after manual review:

```bash
python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

## Local Development

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py import_drugs
python manage.py sync_learning_sources
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

### Frontend Setup

```bash
cd frontend
npm ci
cp .env.example .env
npm run web -- --port 8081
```

The frontend expects:

```text
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### Docker Production-Like Stack

```bash
docker compose up --build
```

Services:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8081`
- PostgreSQL: internal Docker network

## Production And Deployment

Backend production support:

- `backend/config/settings/production.py`
- `backend/render.yaml`
- `backend/Dockerfile`
- `backend/gunicorn.conf.py`
- structured JSON logging
- request IDs through `X-Request-ID`
- health, liveness, and readiness endpoints
- backup command

Frontend production support:

- GitHub Pages workflow in `.github/workflows/frontend-pages.yml`
- Expo static web export
- GitHub Pages base path `/Learning_Platform`
- client-side fallback through `404.html`
- `.nojekyll` artifact marker

Operational docs:

- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`

## Testing And Quality Gates

Backend:

```bash
cd backend
python manage.py check
python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run
python manage.py backup_database --dry-run
python manage.py test
```

Frontend:

```bash
cd frontend
npm run typecheck
npm run build:web
```

CI runs on push to `main` and pull requests:

- Backend install.
- Django check.
- Django deploy check.
- Migration drift check.
- Backup dry-run.
- Backend test suite.
- Frontend typecheck.
- Frontend web build.

GitHub Pages deployment runs on push to `main`.

## Security And Safety

Do not commit secrets or generated runtime data.

Ignored examples:

- `backend/.env`
- `backend/db.sqlite3`
- `backend/.venv/`
- `backend/backups/`
- `backend/exports/`
- `backend/staticfiles/`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/.expo/`

Production expectations:

- Use a strong `SECRET_KEY`.
- Use PostgreSQL through `DATABASE_URL`.
- Configure `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `CORS_ALLOWED_ORIGINS`.
- Use HTTPS for browser-facing API calls.
- Run migrations through controlled deployment.
- Create backups before data-quality apply operations.
- Never apply AI/rule suggestions without approval.

Medical safety note:

This project is an educational software system. Drug data and generated learning content must be reviewed by qualified humans before production use. The application should not be treated as clinical decision support.

## MVP Status

Completed or substantially implemented:

- Project architecture and Django app boundaries.
- Authentication.
- Drug database import and learning-source sync.
- Quiz and question generation.
- Game/session lifecycle.
- Timer, scoring, streak, mistakes, pause/resume.
- Flashcards with Leitner logic.
- League, statistics, dashboard, weak topics.
- Expo + React Native Web frontend.
- Data Quality Center.
- AI data pipeline with local rules provider.
- Production operations foundation.
- GitHub Pages frontend deployment.

Still evolving:

- Full external AI provider integration.
- Richer Data Quality Center charts and reviewer collaboration.
- Production monitoring and error tracking integration.
- Deeper medical validation rules.
- Native mobile packaging.
- Expanded test coverage for UI workflows.

## Roadmap

Near-term:

- Validate production GitHub Pages frontend against Runflare backend.
- Review CORS and HTTPS configuration in production backend.
- Continue data-quality cleanup through review batches.
- Improve frontend polish based on real user testing.

Mid-term:

- Add monitored background jobs when async workloads become necessary.
- Add provider-backed AI suggestions after safety review.
- Add richer analytics and learning recommendations.
- Improve report export formats.

Long-term:

- Add additional learning-product implementations on top of the platform.
- Formalize product plugin contracts.
- Support multi-product or multi-tenant deployment if needed.

## Related Documentation

- `Learning_Platform_Architecture_Engineering_Book_Final/`
- `frontend/README.md`
- `backend/apps/ai_data_pipeline/README.md`
- `backend/apps/data_quality_center/README.md`
- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`

## Maintainer Notes

This repository is prepared for private GitHub hosting. Keep generated data, backups, local databases, virtual environments, and frontend build output out of version control.

Use the architecture book as the source of product and engineering direction. Code changes should preserve the platform/implementation boundary: K_Game is an implementation; the learning platform is the reusable system.
