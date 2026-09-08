# PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa

راهنمای وضعیت: ⬜ شروع‌نشده · 🔄 در حال انجام · ✅ تمام‌شده

**هدف کلی:** بازنویسی کامل فرانت‌اند به React (Expo + `react-native-web`) مو‌به‌مو مطابق
طراحی `frontend/Pharmexa App v2.dc.html`، و بازسازی زیرساخت بک‌اند هماهنگ با آن،
با منبع دادهٔ دارویی که از `…/openfda/pipeline_v2/pipeline_v2.db` به PostgreSQL منتقل می‌شود.

**قانون:** پایان هر فاز = این فایل به‌روز می‌شود + یک commit تمیز. هر فاز جدا تأیید و merge می‌شود.

| فاز | عنوان | وضعیت | کامیت |
|----|-------|-------|-------|
| ۰ + ۰.۵ | تثبیت بک‌اند + حذف زیرساخت رهاشده | ✅ | `57ab3f7` (main) |
| ۱ | دیتابیس دارویی (PostgreSQL) | ✅ | `d2af89a` (برنچ `phase-1-drug-db`) |
| ۲ | قرارداد API | ⬜ | — |
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

## فاز ۲ — قرارداد API ⬜

**هدف:** تعریف endpointها **دقیقاً** مطابق چیزی که صفحه‌های طراحی مصرف می‌کنند؛ اسکیمای versioned.

- [ ] auth + onboarding (فیلدهای پروفایل onboarding: رشته / هدف / سطح)
- [ ] `GET /api/v1/me/dashboard/` — streak، XP، ورودی‌های «جلسهٔ تمرکز»، «فصل بعدی»
- [ ] lessons — گروه‌های ATC → زیرگروه → فصل ساخته‌شده از فیلدهای `apps.drugs`
- [ ] lesson-detail — بلوک‌های بخش‌بندی‌شده (s2..s5 مثل طراحی) + search + «نکته‌های آزمونی این فصل»
- [ ] `/me/mistakes`، `/me/statistics`، `/me/plan` (روزهای هفته)، `/me/profile` + تنظیمات/نوتیفیکیشن
- [ ] flashcards / quiz — سریالایزر کامل ولی endpoint پشت فلگ خاموش
- [ ] `uptodate` — placeholder (منبع دادهٔ جدا در `/home/amir/Documents/UpToDate/`، فاز ۶)
- [ ] اسکیمای drf-spectacular سبز + به‌روزکردن `config/tests.py::CorsPreflightTests`

## فاز ۳ — اپ‌های بک‌اند ⬜

**هدف:** ساخت تازهٔ همهٔ زیرساخت‌های موردنیاز فرانت.

- [ ] `apps.lessons` — تاکسونومی ATC + تولید فصل از `apps.drugs` + ردیابی progress
- [ ] `apps.flashcards` — کارت + جعبه‌های لایتنر + زمان‌بندی مرور (قفل، پشت فلگ)
- [ ] `apps.quiz` — تولید سؤال از هشدارها/منع‌ها + جلسه + نمره + mistakes (قفل، پشت فلگ)
- [ ] endpointهای `me/*` — streak، XP، آمار، planning (منطق سمت سرور)
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
