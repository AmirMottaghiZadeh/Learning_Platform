# Learning Platform / Pharmexa

Pharmexa is a drug-knowledge learning product built on a reusable learning-platform architecture. It combines a Django REST backend, an Expo + React Native Web client, structured drug metadata, quiz and flashcard learning flows, and an internal Data Quality Center for controlled data maintenance.

> Medical safety: this is educational software, not clinical decision support. Drug data and generated learning content must be reviewed by qualified people before production use.

## زبان‌ها

- [English](#overview)
- [فارسی](#راهنمای-فارسی)

## Overview

The project keeps learning rules and sensitive data changes in the backend:

- The backend owns answer correctness, scoring, review scheduling, progress, and league calculations.
- The frontend presents the learning experience and sends user actions to the API.
- Drug metadata is the source for quiz and flashcard learning sources.
- Data Quality Center changes are controlled, audited, and immediately reflected in the learning data for the changed drug.

## Product capabilities

Pharmexa currently includes:

- Token-based authentication.
- Dashboard, progress, streak, weak-topic, statistics, profile, mistakes, and league views.
- Drug quizzes with random and category-based sessions.
- Flashcards with Leitner review.
- Learning for brand/generic names, indications, food or timing information, side effects, and drug categories.
- An internal Data Quality Center for reviewing suggestions and managing the drug database.

The quiz does not reveal the answer under a question before the user answers. Flashcards show the main answer without the former secondary feedback text.

## Architecture

```text
Expo + React Native Web
          |
          | REST API / token authentication
          v
Django REST backend
  ├── accounts              authentication and current user
  ├── learning              learning objects, progress, dashboard, statistics
  ├── drugs                 drug metadata and learning-source synchronization
  ├── quizzes / games       question selection, sessions, answers, scoring
  ├── flashcards            Leitner review and card state
  ├── league                rankings and leaderboard data
  ├── ai_data_pipeline      safe, reviewable rule-based suggestions
  └── data_quality_center   internal data-management interface
          |
          v
PostgreSQL
```

## Repository layout

```text
.
├── backend/                         Django project
│   ├── apps/                        domain applications
│   ├── config/                      Django settings and URLs
│   ├── data/                        import fixtures and source data
│   ├── manage.py
│   └── requirements.txt
├── frontend/                        Expo / React Native Web application
│   ├── src/
│   │   ├── api/ components/ design/ screens/ store/ types/
│   ├── App.tsx
│   └── package.json
├── docs/                            operational documentation
├── docker-compose.yml
└── README.md
```

## Services and important URLs

When the backend is running locally:

- Health: `GET /api/v1/health/`
- Liveness: `GET /api/v1/live/`
- Readiness: `GET /api/v1/ready/`
- OpenAPI schema: `GET /api/v1/schema/`
- API documentation: `/api/v1/docs/`
- Django admin: `/admin/`
- Data Quality Center: `/data-quality/`

Current deployed endpoints:

```text
Frontend: https://AmirMottaghiZadeh.github.io/Learning_Platform/
API:      https://amirmtz.runflare.run/api/v1
```

The GitHub Pages deployment is configured with:

```text
EXPO_BASE_URL=/Learning_Platform
EXPO_PUBLIC_API_BASE_URL=https://amirmtz.runflare.run/api/v1
```

For local frontend development, use:

```text
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Data Quality Center

Data Quality Center is an internal, staff-only web application at `/data-quality/`. It is the normal operational interface for controlled drug-data maintenance; Django Admin remains available for developer administration.

### Drug database

The Database area contains:

- `Search`
- `Search in`
- Sort controls
- Key records navigation
- Clear filters

An administrator can search drug metadata by supported fields such as brand name, generic name, indication, side effects, and other drug attributes; open a matching record; edit its permitted fields; and confirm the change.

Routes:

```text
/data-quality/database/           search and filter drug records
/data-quality/database/new/       create a drug record
/data-quality/database/<id>/      edit a drug record
```

Every create or edit action is recorded in `AIDataChangeHistory`.

### Adding a drug

The **Add Drug** workflow accepts the same drug attributes used by the database. The administrator does not enter a database ID or external identifier:

- The database assigns the primary-key ID.
- The server assigns a unique `external_id` in the form `drug-<uuid>`.

This prevents accidental identifier collisions.

### Automatic learning-source synchronization

Creating or editing a drug through Data Quality Center automatically regenerates and synchronizes that drug’s quiz and flashcard learning sources. Once the deployed version includes this behavior, no manual synchronization command is required for normal Data Quality Center edits.

## Drug imports and learning-source commands

Run commands from `backend/` after activating the virtual environment.

### Import a JSON or backup dataset

```bash
python manage.py import_drug_json <directory-or-fixture.json>
```

Validate an import without changing the database:

```bash
python manage.py import_drug_json <directory-or-fixture.json> --validate-only
```

The JSON importer replaces Pharmexa drug metadata atomically and regenerates/synchronizes learning sources for imported drugs.

### Import legacy JavaScript source files

This importer requires both arguments:

```bash
python manage.py import_drugs --drugs-js <path> --topics-js <path>
```

Do not run bare `python manage.py import_drugs`; it has no default source files.

### Repair or inspect existing learning sources

For normal maintenance, the default command incrementally checks existing sources and updates only records that differ:

```bash
python manage.py sync_learning_sources
```

Synchronize one drug only:

```bash
python manage.py sync_learning_sources --drug-id 123
```

Rebuild all drugs only for an explicit recovery, major import, or repair operation:

```bash
python manage.py sync_learning_sources --all --progress-every 100
```

`--all` can take a significant amount of time on a populated database and is not a normal post-edit or routine deployment step.

## AI Data Pipeline

The current AI Data Pipeline is local and rule-based; it does not call an external OpenAI, Ollama, or other AI service.

Safe workflow:

1. Scan records and create pending suggestions.
2. Review suggestions in Data Quality Center.
3. Approve, reject, or edit suggestions.
4. Apply only approved suggestions.
5. Keep audit history and create a backup before applying.

Useful commands:

```bash
cd backend
python manage.py ai_health_check
python manage.py ai_generate_suggestions --provider rules --limit 500 --include-normalization --include-terminology --include-duplicates --include-medical-validation --batch-name "Initial local cleanup review"
python manage.py ai_generate_report --batch-id 1
python manage.py ai_apply_approved --batch-id 1 --applied-by amir
```

No rule or AI provider directly changes production data without review and approval.

## Local development

### Full stack with Docker

```bash
docker compose up --build
```

- Backend: `http://127.0.0.1:8000`
- Frontend: `http://127.0.0.1:8081`
- PostgreSQL: internal Docker network

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

`createsuperuser` interactively asks for a username, email when configured, and password. The resulting superuser can access `/admin/` and the staff-only Data Quality Center.

Import drug data only when a valid import source is available. For routine local startup, importing or rebuilding learning sources is not required if the database already contains them.

### Frontend

```bash
cd frontend
npm ci
cp .env.example .env
npm run web -- --port 8081
```

Set the local API base URL in `frontend/.env`:

```text
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## Testing and quality gates

### Backend

```bash
cd backend
python manage.py check
python manage.py check --deploy --settings=config.settings.production
python manage.py makemigrations --check --dry-run
python manage.py backup_database --dry-run
python manage.py test
```

### Frontend

```bash
cd frontend
npm run test:typecheck
npm test -- --ci --coverage
npm run typecheck
npm run build:web
```

GitHub Actions runs these backend and frontend checks on pull requests and pushes to `main`. The frontend GitHub Pages deployment also runs on pushes to `main`.

## Production notes

Backend production support includes Docker, Gunicorn, WhiteNoise, structured logging, request IDs, health endpoints, backup tooling, and production settings in `backend/config/settings/production.py`.

Before production deployment:

- Set a strong `SECRET_KEY`.
- Configure `DATABASE_URL`.
- Configure `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, and `CORS_ALLOWED_ORIGINS`.
- Use HTTPS for browser-facing API traffic.
- Run migrations through the deployment process.
- Back up data before bulk data-apply operations.

Do not commit secrets, local databases, backups, virtual environments, `node_modules`, Expo runtime files, or generated frontend output.

## Related documentation

- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`
- `backend/apps/ai_data_pipeline/README.md`
- `backend/apps/data_quality_center/README.md`
- `Learning_Platform_Architecture_Engineering_Book_Final/`

---

# راهنمای فارسی

Pharmexa یک محصول آموزشی برای یادگیری اطلاعات دارویی است که روی یک سکوی یادگیری قابل استفاده مجدد ساخته شده است. پشتیبان Django REST مسئول منطق یادگیری و داده‌ها است و رابط Expo/React Native Web تجربه کاربری را نمایش می‌دهد.

> نکته ایمنی پزشکی: این پروژه ابزار آموزشی است، نه سامانه پشتیبان تصمیم‌گیری بالینی. داده‌های دارویی و محتوای آموزشی باید پیش از استفاده عملی توسط فرد متخصص بازبینی شوند.

## قابلیت‌های فعلی

- ورود با توکن، پیشخوان، پیشرفت، زنجیره یادگیری، آمار، اشتباهات، موضوع‌های ضعیف، پروفایل و لیگ.
- آزمون‌های دارویی تصادفی و مبتنی بر دسته‌بندی.
- فلش‌کارت با مرور Leitner.
- آموزش نام تجاری/ژنریک، اندیکاسیون، مصرف با غذا یا زمان مصرف، عوارض و دسته‌بندی دارویی.
- مرکز داخلی کنترل کیفیت داده برای مدیریت امن داده‌های دارویی.

در آزمون، پاسخ پیش از انتخاب کاربر زیر سؤال نمایش داده نمی‌شود. در فلش‌کارت نیز فقط پاسخ اصلی نمایش داده می‌شود و متن بازخورد ثانویه قبلی حذف شده است.

## مرکز کنترل کیفیت داده

آدرس مرکز:

```text
/data-quality/
```

این بخش فقط برای کاربران staff/admin است و مسیر اصلی عملیات داخلی داده محسوب می‌شود.

### بخش Database

در صفحه Database فقط ابزارهای اصلی مدیریت رکورد فعال هستند:

- `Search`
- `Search in`
- مرتب‌سازی
- `Key records`
- `Clear filters`

مدیر می‌تواند با ستون‌های داده دارویی مانند نام تجاری، نام ژنریک، اندیکاسیون، عوارض و ویژگی‌های مرتبط جست‌وجو و فیلتر کند؛ رکورد را باز کند؛ فیلدهای مجاز را ویرایش کند؛ و تغییر را تأیید نهایی کند.

مسیرها:

```text
/data-quality/database/           جست‌وجو و فیلتر داروها
/data-quality/database/new/       افزودن داروی جدید
/data-quality/database/<id>/      ویرایش دارو
```

تمام ایجادها و ویرایش‌ها در `AIDataChangeHistory` ثبت می‌شوند.

### افزودن داروی جدید و شناسه یکتا

فرم **Add Drug** همان ویژگی‌های دیتابیس دارویی را از مدیر دریافت می‌کند، اما مدیر نباید شناسه وارد کند:

- شناسه اصلی رکورد را دیتابیس تولید می‌کند.
- `external_id` توسط سرور و در قالب `drug-<uuid>` تولید می‌شود.

بنابراین خطای انسانی در اختصاص شناسه یکتا رخ نمی‌دهد.

### همگام‌سازی خودکار آزمون و فلش‌کارت

پس از ایجاد یا ویرایش دارو از طریق Data Quality Center، منابع یادگیری آزمون و فلش‌کارت همان دارو به‌صورت خودکار بازتولید و همگام می‌شوند. در ویرایش‌های عادی Data Quality Center نیازی به اجرای دستی دستور sync نیست.

## دستورهای ورود داده و sync

دستورها را از پوشه `backend/` اجرا کنید.

### ورود داده JSON یا نسخه پشتیبان

```bash
python manage.py import_drug_json <directory-or-fixture.json>
```

بررسی فایل بدون اعمال تغییر:

```bash
python manage.py import_drug_json <directory-or-fixture.json> --validate-only
```

این ورود، متادیتای Pharmexa را به‌صورت اتمی جایگزین می‌کند و منابع یادگیری داروهای واردشده را نیز همگام می‌کند.

### ورود فایل JavaScript قدیمی

```bash
python manage.py import_drugs --drugs-js <path> --topics-js <path>
```

اجرای `python manage.py import_drugs` بدون آرگومان درست نیست؛ هر دو مسیر فایل لازم هستند.

### بررسی یا ترمیم منابع موجود

برای بررسی افزایشی رکوردهای فعلی:

```bash
python manage.py sync_learning_sources
```

برای یک دارو:

```bash
python manage.py sync_learning_sources --drug-id 123
```

بازسازی کامل فقط برای ورود عمده داده یا عملیات ترمیم:

```bash
python manage.py sync_learning_sources --all --progress-every 100
```

گزینه `--all` روی دیتابیس پرحجم زمان‌بر است و نباید بعد از هر ویرایش یا هر استقرار اجرا شود.

## اجرای محلی

### Docker

```bash
docker compose up --build
```

- پشتیبان: `http://127.0.0.1:8000`
- رابط کاربری: `http://127.0.0.1:8081`

### پشتیبان

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver 127.0.0.1:8000
```

فرمان `createsuperuser` به‌صورت تعاملی نام کاربری، در صورت نیاز ایمیل، و گذرواژه را می‌پرسد. این کاربر به `/admin/` و بخش staff-only مرکز کنترل کیفیت داده دسترسی خواهد داشت.

اگر دیتابیس قبلاً داده و منابع یادگیری دارد، برای اجرای معمول محلی لازم نیست import یا بازسازی کامل منابع را اجرا کنید.

### رابط کاربری

```bash
cd frontend
npm ci
cp .env.example .env
npm run web -- --port 8081
```

در `frontend/.env`:

```text
EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

## تست و کنترل کیفیت

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
npm run test:typecheck
npm test -- --ci --coverage
npm run typecheck
npm run build:web
```

این کنترل‌ها در GitHub Actions برای pull request و push به شاخه `main` اجرا می‌شوند. استقرار GitHub Pages رابط کاربری نیز با push به `main` انجام می‌شود.

## آدرس‌های مهم

```text
رابط کاربری تولید: https://AmirMottaghiZadeh.github.io/Learning_Platform/
API تولید:         https://amirmtz.runflare.run/api/v1
```

نشانی‌های مهم پشتیبان:

- `/api/v1/health/`
- `/api/v1/live/`
- `/api/v1/ready/`
- `/api/v1/docs/`
- `/admin/`
- `/data-quality/`

## امنیت و استقرار

- رازها، فایل `.env`، دیتابیس محلی، فایل‌های پشتیبان، محیط مجازی، `node_modules` و خروجی‌های build را commit نکنید.
- برای تولید، `SECRET_KEY` قوی، `DATABASE_URL`، `ALLOWED_HOSTS`، `CSRF_TRUSTED_ORIGINS` و `CORS_ALLOWED_ORIGINS` را تنظیم کنید.
- پیش از عملیات دسته‌ای اعمال تغییرات داده، پشتیبان تهیه کنید.
- پیشنهادهای قانون‌محور یا هوش مصنوعی بدون بازبینی و تأیید دستی نباید اعمال شوند.

## مستندات مرتبط

- `docs/OPERATIONS_RUNBOOK.md`
- `docs/GITHUB_PRIVATE_SETUP.md`
- `backend/apps/ai_data_pipeline/README.md`
- `backend/apps/data_quality_center/README.md`
- `Learning_Platform_Architecture_Engineering_Book_Final/`
