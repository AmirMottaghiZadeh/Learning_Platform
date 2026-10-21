# Pharmexa

A bilingual (فارسی / English) drug-knowledge learning app: lessons built from
real OpenFDA drug data, spaced-repetition flashcards, quizzes, a personal
progress dashboard, and a read-only UpToDate clinical reference.

- **Backend** — Django REST, PostgreSQL, opaque-session auth.
- **Frontend** — Expo (React Native) + `react-native-web`; one codebase for
  iOS, Android and web.
- **Design system** — `frontend/src/theme/tokens.ts` (palette, spacing, radii,
  shadows) and `frontend/src/i18n/strings.ts` (UI copy, fa/en); RTL and
  light/dark throughout.

> Educational software, not clinical decision support. Generated learning
> content and drug summaries need review by qualified people before production
> use.

Progress and the full plan: **[PHASES.md](PHASES.md)**.
API shapes: **[docs/api-contract.md](docs/api-contract.md)**.
Import, export and database commands: **[docs/data-commands.md](docs/data-commands.md)**.
برنامهٔ سئوی حرفه‌ای، راهنمای تنظیمات گوگل و robots.txt:
**[docs/seo-plan.fa.md](docs/seo-plan.fa.md)**.

---

## Architecture

The backend owns everything that must not be client-trusted: auth, answer
correctness, scoring, streak/XP, review scheduling, mistake attribution.

### Backend apps (`backend/apps/`)

| app | role |
|---|---|
| `accounts` | opaque `UserSession` bearer tokens (rotation + instant revoke), RBAC, security audit, step-up, password reset |
| `core` | health/live/ready, request-id logging, exceptions envelope, throttling, a thin Celery layer for password-reset email |
| `drugs` | `Ingredient` / `IngredientProfileSection` / `AtcCode` / `AtcCategory`; `import_openfda` loads the OpenFDA pipeline SQLite; `load_atc_reference` seeds the bilingual ATC tree |
| `lessons` | ATC taxonomy → chapters (drug + section content), per-chapter progress |
| `progress` | `LearnerProgress` (xp, streak, totals), `DailyStudy`, `Mistake`, `StudyPlan`; the `/me/*` endpoints |
| `flashcards` | Leitner cards. Card content (`FlashcardFact`) is empty until the LLM-built content from `study_content` is loaded (the rule-based builder was retired) — **locked** behind `FLASHCARDS_API_ENABLED` |
| `quiz` | server-scored quiz, feeds progress + mistakes. The question bank (`BankQuestion`) is empty until the LLM-built content from `study_content` is loaded (the rule-based builder was retired) — **locked** behind `QUIZ_API_ENABLED` |
| `uptodate` | read-only search + article API over the bundled UpToDate SQLite snapshot (no models); 503 when the snapshot is absent |
| `website` | the public site and blog on `pharmenta.ir` (served on the `SITE_HOSTS` domains) and its panel at `/panel/` -- see [docs/deploy-site.md](docs/deploy-site.md) |
| `data_quality_center` | staff console at `/ops/data-quality/` to edit section summaries, with superuser approval and an audit trail (off with `DATA_QUALITY_CENTER_ENABLED=False`) |
| `billing` | plans, one-off products, discount codes, Zarinpal payments and per-feature access (`BILLING_ENFORCEMENT_ENABLED`, off by default); superuser console at `/ops/` (off with `BILLING_CONSOLE_ENABLED=False`) |

### Frontend (`frontend/src/`)

`theme/` design tokens + provider · `i18n/` fa/en strings + RTL provider ·
`api/` axios client with a `UserSession` refresh interceptor + typed endpoints ·
`store/` zustand (`auth`, `nav` — an app-managed state machine, not a router) ·
`components/` shared primitives + `AppShell` + `BottomNav` · `screens/` one file
per screen · `navigation/Navigator.tsx` gates on auth + onboarding.

---

## پنل مدیریت محتوای سایت

- **پنل مدیریت:** [https://pharmenta.ir/panel/](https://pharmenta.ir/panel/)
- **ورود مستقیم:** [https://pharmenta.ir/panel/login/](https://pharmenta.ir/panel/login/)
- **اجرای محلی با بک‌اند روی پورت ۸۰۰۰:** [http://site.localhost:8000/panel/](http://site.localhost:8000/panel/)

از این پنل می‌توانید مطالب و برگه‌ها، رسانه‌ها، منوها، محتوای صفحهٔ اصلی،
نظرات و تنظیمات سئوی سایت را مدیریت کنید. دسترسی هر حساب به نقش آن بستگی دارد.
برای ورود از حساب فعال مدیر (`is_superuser`) یا حسابی استفاده کنید که مدیر
در بخش «کاربران و نقش‌ها» به آن نقش داده است. برای ساخت حساب مدیر، در محیط
بک‌اند متصل به پایگاه‌دادهٔ موردنظر اجرا کنید:

```bash
cd backend
python manage.py createsuperuser
```

پنل روی دامنه‌های تنظیم‌شده در `SITE_HOSTS` ارائه می‌شود؛ پیش‌فرض آن
`pharmenta.ir,site.localhost` است. مسیرها در `backend/config/urls_site.py` و
`backend/apps/website/panel/urls.py` تعریف شده‌اند.
جزئیات راه‌اندازی و نقش‌ها: [docs/deploy-site.md](docs/deploy-site.md).

## Running it

### Docker (backend + db + redis + web frontend)

```bash
export SECRET_KEY="a strong 50+ character secret"
docker compose up --build
# backend  http://localhost:8000   (API docs at /api/v1/docs/)
# frontend http://localhost:8081
```

### Backend, locally

```bash
cd backend
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # point DATABASE_URL at your Postgres
python manage.py migrate
python manage.py load_atc_reference
python manage.py import_openfda            # needs the OpenFDA pipeline SQLite
python manage.py import_calculators_db --source calculators.db   # from export_reference_db
python manage.py import_guidelines_db  --source guidelines.db
python manage.py import_diseases_db    --source diseases.db
python manage.py runserver
```

`import_openfda` reads `UPTODATE`-style upstreams read-only; re-run any time
(idempotent), or `--only-summaries` to sync just the fa/en summaries, or
`--only-names` to sync just the Persian drug names (`ingredient_name_fa`).

### Frontend, locally

```bash
cd frontend
npm install
npm run web            # or: npm run ios / npm run android / npm start
```

Set `EXPO_PUBLIC_API_BASE_URL` (see `.env.example`); on a device use your
machine's LAN IP, not `127.0.0.1`.

To preview the locked features: run the backend with
`QUIZ_API_ENABLED=True FLASHCARDS_API_ENABLED=True`.

The UpToDate reference needs the snapshot directory (`UPTODATE_DB_DIR`,
default `/home/amir/Documents/UpToDate`); without it those endpoints answer 503
and the screen shows a "coming soon" state.

---

## Tests

```bash
cd backend && python manage.py test          # Django test runner
cd frontend && npm run typecheck             # tsc --noEmit
cd frontend && npm run build:web             # expo export (bundles the app)
```

CI (`.github/workflows/ci.yml`) runs the backend suite + deploy checks and the
frontend typecheck + web build on every push and PR.

---

## Deploy

- **Backend** — `backend/render.yaml` (Render blueprint); `config.settings.production`
  enforces a real broker + cache and a strong secret.
- **Web frontend** — `frontend/Dockerfile` (nginx) or GitHub Pages via
  `.github/workflows/frontend-pages.yml` (manual dispatch).
- **Native** — `frontend/eas.json`; `eas build --platform ios|android`.



هر سه کار آماده است و هر کدام را آزمایش کردم.

۱. دستور داخل study_content: فایل 10_import_to_pharmenta.py. هر بار که محتوای جدید ساخته شد، این را اجرا کنید:
cd /home/amir/Documents/openfda/study_content
python3 10_import_to_pharmenta.py                 # وارد فارمنتای محلی می‌کند
python3 10_import_to_pharmenta.py --dry-run       # فقط گزارش، بدون نوشتن
python3 10_import_to_pharmenta.py --statuses verified,approved   # فقط موارد بررسی‌شده
python3 10_import_to_pharmenta.py --export        # بعدش فایل قابل‌حمل را هم می‌سازد
این دستور backend را با virtualenv خودش اجرا می‌کند، پس نیازی نیست جای دیگری بروید. مثل دستور ایمپورت قبلی، جدول‌های سؤال و فلش‌کارت را کامل جایگزین می‌کند. توضیحش به README همان پوشه اضافه شد.

۲. دستور اکسپورت در Learning Platform: export_study_content_db
cd backend && .venv/bin/python manage.py export_study_content_db
فایل study_content.db را در /home/amir/Documents/pharmenta-reference-data/ می‌سازد، کنار calculators.db و بقیه. همین الان یک بار اجرا کردم: ۷۸۳ سؤال و ۲۲۰۴ عبارت فلش‌کارت، حجم ۱٫۳ مگابایت. روش نوشتنش مثل export_reference_db است: اول فایل موقت، و فقط وقتی کامل شد نام اصلی می‌گیرد.

۳. دستور ایمپورت برای سرور: import_study_content_db
python manage.py import_study_content_db --source study_content.db --dry-run
python manage.py import_study_content_db --source study_content.db
- اجرای دوباره‌اش امن است: سؤال‌ها با شناسه‌ی پایپلاین به‌روز یا اضافه می‌شوند، و فلش‌کارت‌های هر دارو به تفکیک بخش و زبان جایگزین می‌شوند.
- داروها با RxCUI تطبیق می‌خورند؛ داروی ناموجود روی سرور رد می‌شود و در گزارش می‌آید.
- --prune سؤال‌ها و فلش‌کارت‌هایی را که در فایل نیستند پاک می‌کند (پیش‌فرض خاموش).
- همه‌ی کار در یک تراکنش است؛ اگر خطا بدهد چیزی عوض نمی‌شود.

آزمایش‌ها: ایمپورت را روی دیتابیس پر (۷۸۳ به‌روزشده) و روی دیتابیس خالی (۷۸۳ و ۲۲۰۴ اضافه‌شده، مثل سرور تازه) امتحان کردم؛ هر دو در تراکنشی که برگردانده شد. هر دو دستور و روش کار در docs/data-commands.md هم ثبت شد.

برای سرور یادتان باشد: قبل از ایمپورت باید دو migration جدید (quiz 0008 و flashcards 0005) روی سرور اجرا شده باشند. docker-start.sh خودش migrate را اجرا می‌کند، پس با دیپلوی بعدی اجرا می‌شوند. همه‌ی تغییرات پروژه‌ی Learning Platform هنوز commit نشده‌اند.






**بیلد اندروید:**

```
eas build --platform android --profile production
```

**بیلد iOS با تنظیم فعلی:**

```
eas build --platform ios --profile production
```
