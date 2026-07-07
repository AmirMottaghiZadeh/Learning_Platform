# Learning Platform / K_Game

Reusable learning-platform architecture with a Django REST backend, a K_Game reference implementation, an Expo + React Native Web client, and an internal data-quality workflow for safe medical/drug data improvement.

K_Game is not designed as a one-off quiz app. It is the first implementation of a broader Learning Platform: a backend-owned learning system where products can plug into shared learning objects, question sources, game rules, review logic, progress tracking, league mechanics, and operational tooling.

## Languages

- [English](#learning-platform--k_game)
- [فارسی](#نسخه-فارسی)

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

---

# نسخه فارسی

این مخزن یک پلتفرم یادگیری قابل استفاده مجدد است که شامل backend مبتنی بر Django REST، پیاده سازی مرجع K_Game، frontend مبتنی بر Expo و React Native Web، و یک مسیر داخلی برای کنترل کیفیت داده های دارویی و پزشکی است.

K_Game فقط یک اپلیکیشن ساده کوییز نیست. این پروژه اولین پیاده سازی از یک Learning Platform بزرگ تر است؛ یعنی سیستمی که منطق اصلی یادگیری در backend قرار دارد و پیاده سازی های مختلف می توانند از آبجکت های یادگیری، منابع سوال، قوانین بازی، مرور، آمار، لیگ و ابزارهای عملیاتی مشترک استفاده کنند.

## فهرست فارسی

- [هدف](#هدف)
- [مسئله](#مسئله)
- [راه حل](#راه-حل)
- [محدوده محصول](#محدوده-محصول)
- [معماری](#معماری)
- [ساختار مخزن](#ساختار-مخزن)
- [بک اند](#بک-اند)
- [فرانت اند](#فرانت-اند)
- [مرکز کنترل کیفیت داده](#مرکز-کنترل-کیفیت-داده)
- [پایپ لاین داده هوشمند](#پایپ-لاین-داده-هوشمند)
- [اجرای محلی](#اجرای-محلی)
- [تولید و استقرار](#تولید-و-استقرار)
- [تست و کنترل کیفیت](#تست-و-کنترل-کیفیت)
- [امنیت و ایمنی](#امنیت-و-ایمنی)
- [وضعیت MVP](#وضعیت-mvp)
- [نقشه راه](#نقشه-راه)

## هدف

هدف پروژه ساخت یک پلتفرم یادگیری حرفه ای است که بتواند چند محصول آموزشی تخصصی را پشتیبانی کند. در وضعیت فعلی، K_Game پیاده سازی مرجع این پلتفرم برای آموزش دانش دارویی است.

پروژه بین زیرساخت قابل استفاده مجدد و منطق اختصاصی محصول مرز مشخص ایجاد می کند:

- پلتفرم مسئول authentication، آبجکت های یادگیری، منابع دانش، progress، زمان بندی مرور، lifecycle بازی و session، آمار، لیگ، قرارداد API، عملیات production و data governance است.
- K_Game مسئول دیتاست دارویی، دسته بندی های دارویی، نوع سوال ها، تولید prompt و تجربه کاربری آموزش دارویی است.

این جداسازی باعث می شود پروژه در آینده قابل گسترش باشد. پیاده سازی های بعدی باید بتوانند از هسته پلتفرم استفاده کنند بدون اینکه وابسته به فرضیات اختصاصی K_Game باشند.

## مسئله

یادگیری داروها معمولا بین لیست های ثابت، فلش کارت های جدا، بانک سوال های پراکنده و فایل های دستی تقسیم می شود. این مدل چند مشکل جدی ایجاد می کند:

- داده های آموزشی تکراری می شوند و audit کردن آن ها سخت است.
- منطق کوییز گاهی در frontend قرار می گیرد و کنترل correctness دشوار می شود.
- فلش کارت ها از learning objectiveهای ساختاریافته جدا هستند.
- progress، اشتباهات، weak topicها و مرور زمان بندی شده در یک مدل واحد جمع نمی شوند.
- اصلاح داده های پزشکی و دارویی اگر مستقیم روی رکوردهای production انجام شود پرریسک است.
- بسیاری از MVPها از ابتدا health check، backup، deploy check، schema validation و release path ایمن ندارند.

این پروژه با این نگاه ساخته شده که یادگیری فقط یک UI نیست؛ یک مسئله پلتفرمی است.

## راه حل

این پلتفرم یک سیستم یادگیری backend-first فراهم می کند:

- آبجکت های یادگیری و knowledge sourceهای ساختاریافته.
- adapterهای اختصاصی برای داده های دارویی K_Game.
- تولید سوال و game session تحت کنترل قوانین backend.
- فلش کارت هایی که از همان knowledge source مشترک تغذیه می شوند.
- منطق Leitner برای مرور مستقل فلش کارت.
- APIهای dashboard، statistics، mistake، weak topic و league.
- frontend موبایل محور با Expo و React Native Web.
- Data Quality Center برای review داخلی پیشنهادهای rule-based یا AI در آینده.
- زیرساخت production شامل Docker، health check، CI، backup و workflowهای deployment.

Frontend فقط state و تجربه کاربری را نمایش می دهد و intent کاربر را ارسال می کند. scoring، correctness، review scheduling، ranking لیگ و mutationهای مهم داده در backend کنترل می شوند.

## محدوده محصول

در K_Game فعلی این حوزه های یادگیری پوشش داده شده اند:

- یادگیری نام تجاری و ژنریک.
- یادگیری مصرف با غذا یا بدون غذا / timing.
- یادگیری اندیکاسیون.
- یادگیری عوارض جانبی.
- جریان مطالعه بر اساس دسته بندی دارویی.
- quiz و game session به صورت random یا category-based.
- جعبه های Leitner برای فلش کارت.
- مرور اشتباهات.
- dashboard، streak، progress، weak topic، statistics و league.

جهت بصری frontend یک داشبورد آموزشی آرام و clinical است: mobile-first، card-based، رنگ های ملایم، progress indicator واضح و بدون شلوغی بصری.

## معماری

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

### اصول پلتفرم

- backend مالک correctness یادگیری است.
- frontend فقط state را نمایش می دهد و intent کاربر را ارسال می کند.
- پیاده سازی های محصول، داده تخصصی خود را به قراردادهای پلتفرم تبدیل می کنند.
- تغییرات داده پزشکی و دارویی باید قابل review، audit و rollback باشند.
- مسیر production باید قابل مشاهده، قابل deploy و قابل recovery باشد.
- هیچ provider هوش مصنوعی یا rule-based اجازه ندارد مستقیم داده production را تغییر دهد.

## ساختار مخزن

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

## بک اند

تکنولوژی ها:

- Python 3.11
- Django 5
- Django REST Framework
- Token Authentication
- drf-spectacular OpenAPI
- SQLite برای توسعه محلی
- PostgreSQL برای production-like deployment
- Gunicorn و WhiteNoise برای اجرای production

آدرس های مهم محلی:

- `GET /api/v1/health/`
- `GET /api/v1/live/`
- `GET /api/v1/ready/`
- `GET /api/v1/schema/`
- `GET /api/v1/docs/`
- `/admin/`
- `/data-quality/`

ماژول های API زیر `/api/v1/`:

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

## فرانت اند

تکنولوژی ها:

- Expo
- React Native Web
- TypeScript
- lucide-react-native icons
- طراحی mobile-first
- تم clinical calm dashboard

آدرس production frontend:

```text
https://AmirMottaghiZadeh.github.io/Learning_Platform/
```

آدرس production API:

```text
https://amirmtz.runflare.run/api/v1
```

Build مربوط به GitHub Pages از این envها استفاده می کند:

```text
EXPO_BASE_URL=/Learning_Platform
EXPO_PUBLIC_API_BASE_URL=https://amirmtz.runflare.run/api/v1
```

توسعه محلی به صورت پیش فرض از API محلی استفاده می کند:

```text
http://127.0.0.1:8000/api/v1
```

## مرکز کنترل کیفیت داده

Data Quality Center یک وب اپلیکیشن داخلی برای review و validation پیشنهادهای اصلاح داده است.

آدرس:

```text
/data-quality/
```

امکانات:

- داشبورد health score و issue count.
- Batch center.
- Job center.
- Suggestion review center.
- نمایش diff قبل و بعد.
- Record inspector.
- Health center.
- صفحه گزارش ها و دانلود خروجی.

Data Quality Center رابط اصلی روزمره برای review اصلاحات داده است. Django Admin همچنان برای بررسی های توسعه دهنده موجود است، اما مسیر اصلی عملیات داده نیست.

## پایپ لاین داده هوشمند

AI Data Pipeline فعلا local و rule-based است. در وضعیت فعلی هیچ تماس خارجی با OpenAI، Ollama یا providerهای دیگر انجام نمی شود.

مدل ایمنی:

1. دیتابیس scan می شود.
2. suggestionها با status pending ساخته می شوند.
3. suggestionها به صورت دستی review می شوند.
4. suggestionها approve، reject یا edit می شوند.
5. فقط suggestionهای approve شده از طریق safe apply command اعمال می شوند.
6. قبل از apply، backup گرفته می شود.
7. تمام تغییرات اعمال شده در audit history ذخیره می شوند.

Providerها:

- `rules`: provider قطعی و local که الان فعال است.
- `mock`: provider مخصوص تست.
- `openai`: placeholder و غیرفعال.
- `ollama`: placeholder و غیرفعال.
- `manual`: marker برای source دستی.

جدول های اصلی:

- `ai_data_batches`
- `ai_data_jobs`
- `ai_data_suggestions`
- `ai_data_change_history`
- `ai_data_reports`
- `ai_data_translations`

دستورهای کاربردی:

```bash
cd backend
python manage.py ai_health_check
python manage.py ai_generate_suggestions --provider rules --limit 500 --include-normalization --include-terminology --include-duplicates --include-medical-validation --batch-name "Initial local cleanup review"
python manage.py ai_generate_report --batch-id 1
```

اعمال suggestionهای approve شده فقط بعد از review دستی:

```bash
python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

## اجرای محلی

### راه اندازی بک اند

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

### راه اندازی فرانت اند

```bash
cd frontend
npm ci
cp .env.example .env
npm run web -- --port 8081
```

Frontend این env را انتظار دارد:

```text
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### اجرای Docker به شکل Production-like

```bash
docker compose up --build
```

سرویس ها:

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8081`
- PostgreSQL داخل شبکه Docker

## تولید و استقرار

پشتیبانی production در backend:

- `backend/config/settings/production.py`
- `backend/render.yaml`
- `backend/Dockerfile`
- `backend/gunicorn.conf.py`
- structured JSON logging
- request ID از طریق `X-Request-ID`
- health، liveness و readiness endpoint
- backup command

پشتیبانی production در frontend:

- workflow مربوط به GitHub Pages در `.github/workflows/frontend-pages.yml`
- خروجی static web از Expo
- base path مربوط به GitHub Pages یعنی `/Learning_Platform`
- fallback مربوط به client-side routing از طریق `404.html`
- marker مربوط به `.nojekyll`

مستندات عملیاتی:

- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`

## تست و کنترل کیفیت

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

CI روی push به `main` و pull request اجرا می شود:

- نصب وابستگی های backend.
- Django check.
- Django deploy check.
- بررسی migration drift.
- backup dry-run.
- تست backend.
- typecheck frontend.
- build وب frontend.

Deployment مربوط به GitHub Pages روی push به `main` اجرا می شود.

## امنیت و ایمنی

secretها و داده های runtime نباید commit شوند.

نمونه موارد ignore شده:

- `backend/.env`
- `backend/db.sqlite3`
- `backend/.venv/`
- `backend/backups/`
- `backend/exports/`
- `backend/staticfiles/`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/.expo/`

انتظارات production:

- استفاده از `SECRET_KEY` قوی.
- استفاده از PostgreSQL از طریق `DATABASE_URL`.
- تنظیم `ALLOWED_HOSTS`، `CSRF_TRUSTED_ORIGINS` و `CORS_ALLOWED_ORIGINS`.
- استفاده از HTTPS برای APIهای مصرفی مرورگر.
- اجرای migrationها از مسیر کنترل شده deployment.
- گرفتن backup قبل از عملیات data-quality apply.
- عدم اعمال suggestionهای AI/rule بدون approval.

نکته ایمنی پزشکی:

این پروژه یک سیستم آموزشی است. داده های دارویی و محتوای تولید شده باید قبل از استفاده production توسط انسان متخصص review شوند. این نرم افزار نباید به عنوان clinical decision support استفاده شود.

## وضعیت MVP

انجام شده یا تا حد زیادی پیاده سازی شده:

- معماری پروژه و مرزبندی appهای Django.
- Authentication.
- Import دیتابیس دارویی و sync منابع یادگیری.
- تولید quiz و question.
- lifecycle مربوط به game/session.
- timer، scoring، streak، mistakes، pause/resume.
- فلش کارت با منطق Leitner.
- League، statistics، dashboard و weak topics.
- frontend مبتنی بر Expo و React Native Web.
- Data Quality Center.
- AI data pipeline با provider local rules.
- زیرساخت operations و production.
- deployment فرانت اند روی GitHub Pages.

در حال تکامل:

- اتصال provider خارجی AI.
- chartها و collaboration بهتر در Data Quality Center.
- monitoring و error tracking production.
- قواعد عمیق تر medical validation.
- بسته بندی native mobile.
- پوشش تست بیشتر برای workflowهای UI.

## نقشه راه

نزدیک مدت:

- اعتبارسنجی frontend production روی GitHub Pages در کنار Runflare backend.
- بررسی CORS و HTTPS در backend production.
- ادامه cleanup داده از طریق batchهای review.
- بهبود UI بر اساس تست واقعی کاربر.

میان مدت:

- اضافه کردن background job مانیتور شده در صورت نیاز واقعی.
- اضافه کردن providerهای AI بعد از safety review.
- analytics و recommendationهای آموزشی پیشرفته تر.
- بهبود فرمت های خروجی report.

بلند مدت:

- اضافه کردن پیاده سازی های آموزشی دیگر روی همین platform.
- رسمی کردن قرارداد plugin/product.
- پشتیبانی از multi-product یا multi-tenant در صورت نیاز.

## مستندات مرتبط

- `Learning_Platform_Architecture_Engineering_Book_Final/`
- `frontend/README.md`
- `backend/apps/ai_data_pipeline/README.md`
- `backend/apps/data_quality_center/README.md`
- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`

## یادداشت نگهداری

این مخزن برای میزبانی private در GitHub آماده شده است. فایل های تولیدی، backupها، دیتابیس محلی، virtual environment و خروجی build فرانت اند نباید وارد version control شوند.

کتاب معماری پروژه منبع اصلی جهت گیری محصولی و مهندسی است. تغییرات کد باید مرز بین platform و implementation را حفظ کنند: K_Game یک implementation است و Learning Platform سیستم قابل استفاده مجدد پروژه است.
