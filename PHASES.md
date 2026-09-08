kil# PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa

راهنمای وضعیت: ⬜ شروع‌نشده · 🔄 در حال انجام · ✅ تمام‌شده

**هدف کلی:** بازنویسی کامل فرانت‌اند به React (Expo + `react-native-web`) مو‌به‌مو مطابق
طراحی `frontend/Pharmexa App v2.dc.html`، و بازسازی زیرساخت بک‌اند هماهنگ با آن،
با منبع دادهٔ دارویی که از `…/openfda/pipeline_v2/pipeline_v2.db` به PostgreSQL منتقل می‌شود.

**قانون:** پایان هر فاز = این فایل به‌روز می‌شود + یک commit تمیز. هر فاز جدا تأیید و merge می‌شود.

| فاز | عنوان | وضعیت | کامیت |
|----|-------|-------|-------|
| ۰ + ۰.۵ | تثبیت بک‌اند + حذف زیرساخت رهاشده | ✅ | `57ab3f7` (main) |
| ۱ | دیتابیس دارویی (PostgreSQL) | ✅ | `d2af89a` (main) |
| ۲ | قرارداد API + API دانش دارویی + onboarding | ✅ | برنچ `phase-2-api-contract` |
| ۳ | اپ‌های بک‌اند (lessons / flashcards / quiz / me) | ⬜ | — |
| ۴ | اسکلت فرانت + دیزاین‌سیستم | ⬜ | — |
| ۵ | پیاده‌سازی صفحه‌ها + اتصال | ⬜ | — |
| ۶ | uptodate + جمع‌بندی + انتشار | ⬜ | — |

---

## فاز ۰ — تثبیت بک‌اند ✅

**هدف:** بک‌اند دوباره بوت شود و تست‌ها سبز شوند؛ ۷ اپ قدیمی از دیسک حذف شده بودند
ولی هنوز در `settings`/`urls` ارجاع داشتند و `manage.py check` می‌ترکید.

- [x] حذف ارجاع ۷ اپ حذف‌شده (learning, drugs, quizzes, games, league, flashcards, ai_data_pipeline) از `INSTALLED_APPS` و `config/urls.py` و `config/api_urls.py`
- [x] پارک‌کردن `data_quality_center` (هر ماژولش `ai_data_pipeline` را import می‌کند)
- [x] قفل‌کردن مسیرهای `quiz`/`flashcards` با روتر «maintenance» (پاسخ ۵۰۳)
- [x] حذف `test_phase*.py`، `Learning_Platform_Architecture_Engineering_Book_Final/`، `README_MIGRATION.md`، `backend/data/*.js`
- [x] `manage.py check` + `check --deploy` + ۲۸ تست سبز
- [x] CI: حذف env مرده، غیرفعال‌کردن موقت job فرانت

## فاز ۰.۵ — حذف زیرساخت رهاشده ✅

**هدف:** حذف پیچیدگی برنامهٔ چندفازی قبلی از اپ `core`.

- [x] حذف transactional-outbox / audit-chain / idempotency / dead-letter / worker-heartbeat (مدل‌ها، `core/migrations/`، ماژول‌ها، ۵ management command، ~۱۵۰ خط setting و کلیدهای `.env`)
- [x] نگه‌داشتن Celery حداقلی فقط به‌عنوان مسیر async ایمیل reset
- [x] نگه‌داشتن **کامل** احراز هویت فاز۲ `accounts` (توکن مات `UserSession` با چرخش + ابطال آنی، RBAC، security audit، step-up، password reset) — انتخاب نهایی JWT-یا-همین در فاز ۲

## فاز ۱ — دیتابیس دارویی ✅

**هدف:** دادهٔ `pipeline_v2.db` به‌صورت دادهٔ اصلی و **قابل‌ویرایش** در PostgreSQL،
تا فرانت و DQC از آن تغذیه کنند.

- [x] اپ `apps.drugs` — مدل‌ها: `Ingredient` (کلید `rxcui`), `AtcCode`, `IngredientProfileSection` (یک ردیف به‌ازای هر فیلد بالینی: `raw_text`, `n_contributing_products`, `summary_fa`, `summary_en`)
- [x] management command `import_openfda` — idempotent (match روی `rxcui`), `--only-summaries`, `--limit`, `--dry-run`, fallback ATC از جدول `ingredient_atc_codes`
- [x] Django admin برای هر سه مدل (inline سکشن‌ها)
- [x] اجرای کامل: **۱۷۹۴ دارو · ۵۴۲ کد ATC · ۲۱۵۲۸ سکشن** — شمارش‌ها با منبع می‌خواند
- [x] ۸ تست جدید (create، ATC fallback، idempotency، only-summaries، dry-run) → ۳۶/۳۶
- [x] `docker-compose.yml`: Postgres روی پورت هاست `5433` publish شد؛ سرویس `beat` و env مرده حذف؛ سرویس `frontend` تا فاز ۴ پارک شد
- [ ] اجرای `import_openfda` روی Postgresِ داکر (نیاز به دسترسی docker daemon؛ فعلاً روی Postgres محلیِ معادل انجام شد)

**یادداشت:** برند/ژنریک و دادهٔ سطح‌محصول (از `spl_records`، ~۲۶۱ هزار ردیف) در فاز ۳ اضافه می‌شود، وقتی اپ‌های flashcard/quiz لازمشان داشته باشند.

## فاز ۲ — قرارداد API + API دانش دارویی + onboarding ✅

**هدف:** سند قرارداد کامل همهٔ صفحه‌ها + پیاده‌سازی واقعی بخش‌های بدون state کاربر.

- [x] **`docs/api-contract.md`** — قرارداد کامل v1 برای همهٔ صفحه‌ها (✅ ساخته‌شده / 🔜 فاز ۳)
- [x] auth + onboarding — مدل `LearnerProfile` (`study_field`/`goal`/`level`/`display_name`/`onboarded_at`)؛ `POST /api/v1/auth/onboarding/`؛ `GET`+`PATCH /api/v1/auth/me/` با بلوک `profile`
- [x] `GET /api/v1/drugs/` — لیست صفحه‌بندی‌شده + `?search=` + `?atc=` (پیشوند)
- [x] `GET /api/v1/drugs/{slug}/` — جزئیات + `sections` (۱۲ فیلد) + `lesson_sections` (شکل کارت درس طراحی: `FIELD_MAP` + `LESSON_EXTRA` + `tone`)
- [x] `GET /api/v1/atc/` — کدهای ATC موجود + `ingredient_count` + `level`
- [x] اسکیمای drf-spectacular سبز (`spectacular --validate --fail-on-warn` → ۰) + به‌روزکردن `config/tests.py::CorsPreflightTests`
- [x] ۹ تست جدید (drug API + onboarding) → ۴۵/۴۵
- [~] **contract-only** (شکل در سند، پیاده‌سازی فاز ۳): `/lessons/*`، `/me/{dashboard,mistakes,statistics,plan,profile}`، flashcards، quiz، uptodate

## فاز ۳ — اپ‌های بک‌اند ⬜

**هدف:** پیاده‌سازی همهٔ endpointهای «🔜 فاز ۳» در `docs/api-contract.md` (شکل‌ها قفل شده‌اند).

- [ ] جدول مرجع ATC (L1/L2 با نام fa/en) برای تاکسونومی درس‌ها — از `pipeline_v2.db` نمی‌آید، باید bundle شود
- [ ] `apps.lessons` — `/lessons/groups/`، `/lessons/chapters/{code}/` + ردیابی progress
- [ ] `apps.flashcards` — کارت + جعبه‌های لایتنر + زمان‌بندی مرور (قفل، پشت فلگ)
- [ ] `apps.quiz` — تولید سؤال از هشدارها/منع‌ها + جلسه + نمره + mistakes (قفل، پشت فلگ)
- [ ] `apps.progress` / endpointهای `me/*` — `/me/{dashboard,mistakes,statistics,plan}`، streak، XP
- [ ] برند/ژنریک از `spl_records` (اگر flashcard/quiz لازم داشت)
- [ ] **بازنویسی** `data_quality_center` روی `apps.drugs` و فعال‌سازی مجدد
- [ ] تست هر اپ

## فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ⬜

**هدف:** پروژهٔ React قابل‌اجرا با تم روشن/تیره، RTL و ناوبری درست (صفحه‌ها خالی).

- [ ] پروژهٔ Expo + Expo Router + `react-native-web` + TypeScript در `frontend/`
- [ ] توکن‌های تم از `.dc.html` — پالت روشن/تیره، Vazirmatn، RTL با `I18nManager`، شل ۴۳۰px، شعاع/سایه/انیمیشن‌ها (`fadeUp/popIn/flip/...`)
- [ ] لایهٔ primitive مشترک (Button، Card، Input، Sheet، Chip، …) مطابق طراحی
- [ ] shell ناوبری + نوار پایین ۵-تبی (خانه/درس‌ها/فلش‌کارت/آزمون/پروفایل) + حالت تب «قفل»
- [ ] کلاینت API (axios + interceptor برای refresh توکن `UserSession`) + react-query + zustand
- [ ] i18n (fa پیش‌فرض / en)
- [ ] فعال‌سازی مجدد job `frontend` در CI

## فاز ۵ — پیاده‌سازی صفحه‌ها + اتصال ⬜

**هدف:** اپ کامل، هر صفحه مو‌به‌مو مطابق `.dc.html`، وصل به API فاز ۲/۳.

- [ ] login / signup + onboarding (۴ مرحله)
- [ ] dashboard + «جلسهٔ تمرکز»
- [ ] lessons list (گروه‌های ATC) + lesson detail (بخش‌بندی، search، نکته‌های آزمونی)
- [ ] flashcards + Leitner (حالت «به‌زودی» تا باز شدن فلگ)
- [ ] quiz setup / running / result (حالت «به‌زودی»)
- [ ] mistakes، statistics، planning، profile
- [ ] تور راهنما / help / tipها

## فاز ۶ — uptodate + جمع‌بندی + انتشار ⬜

**هدف:** قابل‌عرضه.

- [ ] `apps.uptodate` روی دیتابیس‌های `/home/amir/Documents/UpToDate/` (content / toc / search / fts) + API خواندنی + صفحهٔ `uptodate`
- [ ] نهایی‌سازی `docker-compose` / `Dockerfile` فرانت / CI
- [ ] حذف `frontend_old/`
- [ ] `render.yaml` / deploy، کانفیگ EAS build (iOS/Android)
