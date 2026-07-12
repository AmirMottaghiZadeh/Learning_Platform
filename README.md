# Learning Platform / Pharmexa

Reusable learning-platform architecture with a Django REST backend, a Pharmexa reference implementation, an Expo + React Native Web client, and an internal data-quality workflow for safe medical/drug data improvement.

Pharmexa is not designed as a one-off quiz app. It is the first implementation of a broader Learning Platform: a backend-owned learning system where products can plug into shared learning objects, question sources, game rules, review logic, progress tracking, league mechanics, and operational tooling.

## Languages

- [English](#learning-platform--pharmexa)
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

The project exists to build a professional learning platform that can support multiple domain-specific learning products. Pharmexa is the current reference implementation focused on drug knowledge training.

The platform separates reusable learning infrastructure from product-specific content:

- The platform owns authentication, learning objects, knowledge sources, progress, review scheduling, game/session lifecycle, statistics, league primitives, API contracts, operations, and data governance.
- Pharmexa owns drug-specific datasets, drug categories, question types, prompt generation, and the user-facing learning experience.

This separation keeps the project extensible. A future implementation should be able to reuse the platform without copying Pharmexa-specific assumptions.

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
- Drug-specific Pharmexa data adapters.
- Quiz generation and game sessions controlled by backend rules.
- Flashcards built from the same knowledge-source layer.
- Leitner review logic for independent flashcard learning.
- League, statistics, mistakes, weak-topic, and dashboard APIs.
- Mobile-first Expo + React Native Web frontend.
- Data Quality Center for internal review of rule-based or future AI suggestions.
- Production operations foundation with Docker, health checks, CI, backups, and deployment workflows.

The frontend is intentionally a consumer of backend state. It renders the learning experience, but it does not own scoring, correctness, review scheduling, league ranking, or data mutation rules.

## Product Scope

Current Pharmexa learning dimensions:

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
                    | Mobile-first Pharmexa client  |
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
|  drugs           Pharmexa drug data, categories, source sync          |
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

Use the architecture book as the source of product and engineering direction. Code changes should preserve the platform/implementation boundary: Pharmexa is an implementation; the learning platform is the reusable system.

---

# نسخه فارسی

این مخزن یک سکوی یادگیریِ قابل استفاده دوباره است که شامل پشتیبان مبتنی بر Django REST، پیاده‌سازی مرجع Pharmexa، رابط کاربری مبتنی بر Expo و React Native Web، و مسیر داخلی کنترل کیفیت داده‌های دارویی و پزشکی است.

Pharmexa فقط یک برنامه ساده آزمون نیست. این پروژه نخستین پیاده‌سازی از یک سکوی یادگیری بزرگ‌تر است؛ یعنی سامانه‌ای که منطق اصلی یادگیری در پشتیبان قرار دارد و پیاده‌سازی‌های مختلف می‌توانند از شیءهای یادگیری، منابع پرسش، قوانین بازی، مرور، آمار، لیگ و ابزارهای عملیاتی مشترک استفاده کنند.

## فهرست فارسی

- [هدف](#هدف)
- [مسئله](#مسئله)
- [راه حل](#راه-حل)
- [محدوده محصول](#محدوده-محصول)
- [معماری](#معماری)
- [ساختار مخزن](#ساختار-مخزن)
- [پشتیبان](#پشتیبان)
- [رابط کاربری](#رابط-کاربری)
- [مرکز کنترل کیفیت داده](#مرکز-کنترل-کیفیت-داده)
- [مسیر داده هوشمند](#مسیر-داده-هوشمند)
- [اجرای محلی](#اجرای-محلی)
- [تولید و استقرار](#تولید-و-استقرار)
- [آزمون و کنترل کیفیت](#آزمون-و-کنترل-کیفیت)
- [امنیت و ایمنی](#امنیت-و-ایمنی)
- [وضعیت نسخه اولیه](#وضعیت-نسخه-اولیه)
- [نقشه راه](#نقشه-راه)

## هدف

هدف پروژه ساخت یک سکوی یادگیری حرفه‌ای است که بتواند چند محصول آموزشی تخصصی را پشتیبانی کند. در وضعیت فعلی، Pharmexa پیاده‌سازی مرجع این سکو برای آموزش دانش دارویی است.

پروژه بین زیرساخت قابل استفاده دوباره و منطق اختصاصی محصول مرز مشخص ایجاد می‌کند:

- سکو مسئول احراز هویت، شیءهای یادگیری، منابع دانش، پیشرفت، زمان‌بندی مرور، چرخه عمر بازی و نشست، آمار، لیگ، قراردادهای رابط برنامه‌نویسی، عملیات تولید و حاکمیت داده است.
- Pharmexa مسئول مجموعه داده دارویی، دسته‌بندی‌های دارویی، نوع پرسش‌ها، تولید درخواست متنی و تجربه کاربری آموزش دارویی است.

این جداسازی باعث می‌شود پروژه در آینده قابل گسترش باشد. پیاده‌سازی‌های بعدی باید بتوانند از هسته سکو استفاده کنند، بدون اینکه به فرضیات اختصاصی Pharmexa وابسته باشند.

## مسئله

یادگیری داروها معمولا بین فهرست‌های ثابت، فلش‌کارت‌های جدا، بانک پرسش‌های پراکنده و فایل‌های دستی تقسیم می‌شود. این مدل چند مشکل جدی ایجاد می‌کند:

- داده‌های آموزشی تکراری می‌شوند و بازرسی آن‌ها سخت است.
- منطق آزمون گاهی در رابط کاربری قرار می‌گیرد و کنترل درستی پاسخ‌ها دشوار می‌شود.
- فلش‌کارت‌ها از هدف‌های یادگیری ساختاریافته جدا هستند.
- پیشرفت، اشتباهات، موضوع‌های ضعیف و مرور زمان‌بندی‌شده در یک مدل واحد جمع نمی‌شوند.
- اصلاح داده‌های پزشکی و دارویی اگر مستقیم روی رکوردهای محیط تولید انجام شود پرریسک است.
- بسیاری از نسخه‌های اولیه از ابتدا بررسی سلامت، پشتیبان‌گیری، بررسی استقرار، اعتبارسنجی طرح‌واره و مسیر انتشار ایمن ندارند.

این پروژه با این نگاه ساخته شده که یادگیری فقط یک رابط کاربری نیست؛ یک مسئله سکویی است.

## راه حل

این سکو یک سامانه یادگیری با محوریت پشتیبان فراهم می‌کند:

- شیءهای یادگیری و منابع دانش ساختاریافته.
- مبدل‌های اختصاصی برای داده‌های دارویی Pharmexa.
- تولید پرسش و نشست بازی تحت کنترل قوانین پشتیبان.
- فلش‌کارت‌هایی که از همان منبع دانش مشترک تغذیه می‌شوند.
- منطق Leitner برای مرور مستقل فلش‌کارت.
- رابط‌های برنامه‌نویسی برای پیشخوان، آمار، اشتباهات، موضوع‌های ضعیف و لیگ.
- رابط کاربری موبایل‌محور با Expo و React Native Web.
- مرکز کنترل کیفیت داده برای بازبینی داخلی پیشنهادهای قانون‌محور یا هوش مصنوعی در آینده.
- زیرساخت تولید شامل Docker، بررسی سلامت، یکپارچه‌سازی پیوسته، پشتیبان‌گیری و گردش‌کارهای استقرار.

رابط کاربری فقط وضعیت و تجربه کاربر را نمایش می‌دهد و قصد کاربر را ارسال می‌کند. امتیازدهی، درستی پاسخ‌ها، زمان‌بندی مرور، رتبه‌بندی لیگ و تغییرات مهم داده در پشتیبان کنترل می‌شوند.

## محدوده محصول

در Pharmexa فعلی این حوزه‌های یادگیری پوشش داده شده‌اند:

- یادگیری نام تجاری و ژنریک.
- یادگیری مصرف با غذا یا بدون غذا و زمان مصرف.
- یادگیری اندیکاسیون.
- یادگیری عوارض جانبی.
- جریان مطالعه بر اساس دسته‌بندی دارویی.
- آزمون و نشست بازی به صورت تصادفی یا مبتنی بر دسته‌بندی.
- جعبه‌های Leitner برای فلش‌کارت.
- مرور اشتباهات.
- پیشخوان، زنجیره یادگیری، پیشرفت، موضوع‌های ضعیف، آمار و لیگ.

جهت بصری رابط کاربری یک پیشخوان آموزشی آرام و بالینی است: موبایل‌محور، کارت‌محور، با رنگ‌های ملایم، نشانگر پیشرفت واضح و بدون شلوغی بصری.

## معماری

```text
                    +-----------------------------+
                    | Expo + React Native Web     |
                    | رابط موبایل‌محور Pharmexa    |
                    +--------------+--------------+
                                   |
                                   | REST / احراز هویت توکنی
                                   |
+----------------------------------v----------------------------------+
|                         پشتیبان Django REST                         |
|                                                                     |
|  accounts        احراز هویت، توکن‌ها، کاربر فعلی                  |
|  core            سلامت، خطاها، صفحه‌بندی، طرح‌واره، رخدادنگاری    |
|  learning        شیءهای یادگیری، پیشرفت، پیشخوان، آمار            |
|  drugs           داده دارویی Pharmexa، دسته‌ها، همگام‌سازی منابع    |
|  quizzes         انتخاب‌گرها و تولید پرسش                         |
|  games           نشست‌ها، پاسخ‌ها، امتیازدهی، زمان‌سنج، چرخه عمر  |
|  flashcards      وضعیت‌های Leitner، مرور، خلاصه دسته‌ها           |
|  league          رتبه‌ها، فصل‌ها، خلاصه جدول امتیازها             |
|  ai_data_pipeline پیشنهادهای داده دسته‌ای و اعمال ایمن             |
|  data_quality_center رابط بازبینی داخلی                            |
|                                                                     |
+----------------------------------+----------------------------------+
                                   |
                                   | ORM / مهاجرت‌ها
                                   |
                    +--------------v--------------+
                    | SQLite محلی / PostgreSQL    |
                    | استقرار شبیه تولید          |
                    +-----------------------------+
```

### اصول سکو

- پشتیبان مالک درستی منطق یادگیری است.
- رابط کاربری فقط وضعیت را نمایش می‌دهد و قصد کاربر را ارسال می‌کند.
- پیاده‌سازی‌های محصول، داده تخصصی خود را به قراردادهای سکو تبدیل می‌کنند.
- تغییرات داده پزشکی و دارویی باید قابل بازبینی، بازرسی و بازگردانی باشند.
- مسیر تولید باید قابل مشاهده، قابل استقرار و قابل بازیابی باشد.
- هیچ ارائه‌دهنده هوش مصنوعی یا موتور قانون‌محور اجازه ندارد مستقیم داده تولید را تغییر دهد.

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

## پشتیبان

فناوری‌ها:

- Python 3.11
- Django 5
- Django REST Framework
- احراز هویت با توکن
- مستندسازی OpenAPI با drf-spectacular
- SQLite برای توسعه محلی
- PostgreSQL برای استقرار شبیه تولید
- Gunicorn و WhiteNoise برای اجرای محیط تولید

آدرس‌های مهم محلی:

- `GET /api/v1/health/`
- `GET /api/v1/live/`
- `GET /api/v1/ready/`
- `GET /api/v1/schema/`
- `GET /api/v1/docs/`
- `/admin/`
- `/data-quality/`

ماژول‌های رابط برنامه‌نویسی زیر `/api/v1/`:

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

## رابط کاربری

فناوری‌ها:

- Expo
- React Native Web
- TypeScript
- آیکون‌های lucide-react-native
- طراحی موبایل‌محور
- ظاهر پیشخوان آرام و بالینی

آدرس رابط کاربری تولید:

```text
https://AmirMottaghiZadeh.github.io/Learning_Platform/
```

آدرس رابط برنامه‌نویسی تولید:

```text
https://amirmtz.runflare.run/api/v1
```

ساخت مربوط به GitHub Pages از این متغیرهای محیطی استفاده می‌کند:

```text
EXPO_BASE_URL=/Learning_Platform
EXPO_PUBLIC_API_BASE_URL=https://amirmtz.runflare.run/api/v1
```

توسعه محلی به صورت پیش‌فرض از رابط برنامه‌نویسی محلی استفاده می‌کند:

```text
http://127.0.0.1:8000/api/v1
```

## مرکز کنترل کیفیت داده

مرکز کنترل کیفیت داده یک برنامه وب داخلی برای بازبینی و اعتبارسنجی پیشنهادهای اصلاح داده است.

آدرس:

```text
/data-quality/
```

امکانات:

- پیشخوان امتیاز سلامت و تعداد مسئله‌ها.
- مرکز دسته‌ها.
- مرکز کارها.
- مرکز بازبینی پیشنهادها.
- نمایش تفاوت قبل و بعد.
- بازرس رکورد.
- مرکز سلامت.
- صفحه گزارش‌ها و دانلود خروجی.

مرکز کنترل کیفیت داده رابط اصلی روزمره برای بازبینی اصلاحات داده است. مدیریت Django همچنان برای بررسی‌های توسعه‌دهنده موجود است، اما مسیر اصلی عملیات داده نیست.

## مسیر داده هوشمند

مسیر داده هوشمند فعلا محلی و قانون‌محور است. در وضعیت فعلی هیچ تماس خارجی با OpenAI، Ollama یا ارائه‌دهنده‌های دیگر انجام نمی‌شود.

مدل ایمنی:

1. پایگاه داده پویش می‌شود.
2. پیشنهادها با وضعیت در انتظار ساخته می‌شوند.
3. پیشنهادها به صورت دستی بازبینی می‌شوند.
4. پیشنهادها تأیید، رد یا ویرایش می‌شوند.
5. فقط پیشنهادهای تأییدشده از طریق فرمان اعمال ایمن اجرا می‌شوند.
6. پیش از اعمال، پشتیبان گرفته می‌شود.
7. همه تغییرات اعمال‌شده در تاریخچه بازرسی ذخیره می‌شوند.

ارائه‌دهنده‌ها:

- `rules`: ارائه‌دهنده قطعی و محلی که اکنون فعال است.
- `mock`: ارائه‌دهنده مخصوص آزمون.
- `openai`: جایگاه آماده و غیرفعال.
- `ollama`: جایگاه آماده و غیرفعال.
- `manual`: نشانگر برای منبع دستی.

جدول‌های اصلی:

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

اعمال پیشنهادهای تأییدشده فقط بعد از بازبینی دستی:

```bash
python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

## اجرای محلی

### راه‌اندازی پشتیبان

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

### راه‌اندازی رابط کاربری

```bash
cd frontend
npm ci
cp .env.example .env
npm run web -- --port 8081
```

رابط کاربری این متغیر محیطی را انتظار دارد:

```text
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

### اجرای Docker به شکل شبیه تولید

```bash
docker compose up --build
```

سرویس‌ها:

- پشتیبان: `http://127.0.0.1:8000`
- رابط کاربری: `http://127.0.0.1:8081`
- PostgreSQL داخل شبکه Docker

## تولید و استقرار

پشتیبانی تولید در پشتیبان:

- `backend/config/settings/production.py`
- `backend/render.yaml`
- `backend/Dockerfile`
- `backend/gunicorn.conf.py`
- ثبت رخداد ساختاریافته با JSON
- شناسه درخواست از طریق `X-Request-ID`
- نشانی‌های بررسی سلامت، زنده‌بودن و آمادگی
- فرمان پشتیبان‌گیری

پشتیبانی تولید در رابط کاربری:

- گردش‌کار مربوط به GitHub Pages در `.github/workflows/frontend-pages.yml`
- خروجی وب ایستا از Expo
- مسیر پایه مربوط به GitHub Pages یعنی `/Learning_Platform`
- مسیر جایگزین برای مسیریابی سمت کاربر از طریق `404.html`
- نشانگر مربوط به `.nojekyll`

مستندات عملیاتی:

- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`

## آزمون و کنترل کیفیت

پشتیبان:

```bash
cd backend
python manage.py check
python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run
python manage.py backup_database --dry-run
python manage.py test
```

رابط کاربری:

```bash
cd frontend
npm run typecheck
npm run build:web
```

یکپارچه‌سازی پیوسته روی ارسال به `main` و درخواست ادغام اجرا می‌شود:

- نصب وابستگی‌های پشتیبان.
- بررسی معمول Django.
- بررسی استقرار Django.
- بررسی اختلاف مهاجرت‌ها.
- اجرای آزمایشی پشتیبان‌گیری.
- آزمون پشتیبان.
- بررسی نوع‌های رابط کاربری.
- ساخت وب رابط کاربری.

استقرار مربوط به GitHub Pages روی ارسال به `main` اجرا می‌شود.

## امنیت و ایمنی

رازها و داده‌های زمان اجرا نباید ثبت شوند.

نمونه موارد نادیده‌گرفته‌شده:

- `backend/.env`
- `backend/db.sqlite3`
- `backend/.venv/`
- `backend/backups/`
- `backend/exports/`
- `backend/staticfiles/`
- `frontend/node_modules/`
- `frontend/dist/`
- `frontend/.expo/`

انتظارات تولید:

- استفاده از `SECRET_KEY` قوی.
- استفاده از PostgreSQL از طریق `DATABASE_URL`.
- تنظیم `ALLOWED_HOSTS`، `CSRF_TRUSTED_ORIGINS` و `CORS_ALLOWED_ORIGINS`.
- استفاده از HTTPS برای رابط‌های برنامه‌نویسی مصرفی مرورگر.
- اجرای مهاجرت‌ها از مسیر کنترل‌شده استقرار.
- گرفتن پشتیبان قبل از عملیات اعمال اصلاحات داده.
- عدم اعمال پیشنهادهای هوش مصنوعی یا قانون‌محور بدون تأیید.

نکته ایمنی پزشکی:

این پروژه یک سامانه آموزشی است. داده‌های دارویی و محتوای تولیدشده باید پیش از استفاده در محیط تولید توسط انسان متخصص بازبینی شوند. این نرم‌افزار نباید به عنوان پشتیبان تصمیم‌گیری بالینی استفاده شود.

## وضعیت نسخه اولیه

انجام‌شده یا تا حد زیادی پیاده‌سازی‌شده:

- معماری پروژه و مرزبندی برنامه‌های Django.
- احراز هویت.
- ورود پایگاه داده دارویی و همگام‌سازی منابع یادگیری.
- تولید آزمون و پرسش.
- چرخه عمر مربوط به بازی و نشست.
- زمان‌سنج، امتیازدهی، زنجیره یادگیری، اشتباهات، توقف و ادامه.
- فلش‌کارت با منطق Leitner.
- لیگ، آمار، پیشخوان و موضوع‌های ضعیف.
- رابط کاربری مبتنی بر Expo و React Native Web.
- مرکز کنترل کیفیت داده.
- مسیر داده هوشمند با ارائه‌دهنده قانون‌محور محلی.
- زیرساخت عملیات و تولید.
- استقرار رابط کاربری روی GitHub Pages.

در حال تکامل:

- اتصال ارائه‌دهنده خارجی هوش مصنوعی.
- نمودارها و همکاری بهتر در مرکز کنترل کیفیت داده.
- پایش و رهگیری خطا در محیط تولید.
- قواعد عمیق‌تر اعتبارسنجی پزشکی.
- بسته‌بندی موبایل بومی.
- پوشش آزمون بیشتر برای گردش‌کارهای رابط کاربری.

## نقشه راه

نزدیک‌مدت:

- اعتبارسنجی رابط کاربری تولید روی GitHub Pages در کنار پشتیبان Runflare.
- بررسی CORS و HTTPS در پشتیبان تولید.
- ادامه پاک‌سازی داده از طریق دسته‌های بازبینی.
- بهبود رابط کاربری بر اساس آزمون واقعی کاربر.

میان‌مدت:

- اضافه کردن کار پس‌زمینه پایش‌شده در صورت نیاز واقعی.
- اضافه کردن ارائه‌دهنده‌های هوش مصنوعی پس از بازبینی ایمنی.
- تحلیل داده و پیشنهادهای آموزشی پیشرفته‌تر.
- بهبود قالب‌های خروجی گزارش.

بلندمدت:

- اضافه کردن پیاده‌سازی‌های آموزشی دیگر روی همین سکو.
- رسمی کردن قرارداد افزونه و محصول.
- پشتیبانی از چندمحصولی یا چندمستاجری در صورت نیاز.

## مستندات مرتبط

- `Learning_Platform_Architecture_Engineering_Book_Final/`
- `frontend/README.md`
- `backend/apps/ai_data_pipeline/README.md`
- `backend/apps/data_quality_center/README.md`
- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`

## یادداشت نگهداری

این مخزن برای میزبانی خصوصی در GitHub آماده شده است. فایل‌های تولیدی، پشتیبان‌ها، پایگاه داده محلی، محیط مجازی و خروجی ساخت رابط کاربری نباید وارد سامانه کنترل نسخه شوند.

کتاب معماری پروژه منبع اصلی جهت‌گیری محصولی و مهندسی است. تغییرات کد باید مرز بین سکو و پیاده‌سازی را حفظ کنند: Pharmexa یک پیاده‌سازی است و سکوی یادگیری سامانه قابل استفاده دوباره پروژه است.
