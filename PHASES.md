# PHASES.md — نقشه و پیشرفت بازنویسی Pharmexa

راهنمای وضعیت: ⬜ شروع‌نشده · 🔄 در حال انجام · ✅ تمام‌شده

**هدف کلی:** بازنویسی کامل فرانت‌اند به React (Expo + `react-native-web`) مو‌به‌مو مطابق
طراحی `frontend/Pharmexa App v2.dc.html`، و بازسازی زیرساخت بک‌اند هماهنگ با آن،
با منبع دادهٔ دارویی که از `…/openfda/pipeline_v2/pipeline_v2.db` به PostgreSQL منتقل می‌شود.

**قانون:** پایان هر فاز = این فایل به‌روز می‌شود + یک commit تمیز. هر فاز جدا تأیید و merge می‌شود.

| فاز | عنوان | وضعیت | کامیت |
|----|-------|-------|-------|
| ۰ + ۰.۵ | تثبیت بک‌اند + حذف زیرساخت رهاشده | ✅ | `57ab3f7` (main) |
| ۱ | دیتابیس دارویی (PostgreSQL) | ✅ | `d2af89a` (main) |
| ۲ | قرارداد API + API دانش دارویی + onboarding | ✅ | `feaf761` (main) |
| ۳a | جدول مرجع ATC + `apps.lessons` | ✅ | `4963756` (main) |
| ۳b | `apps.progress` → `/me/{dashboard,mistakes,statistics,plan}` | ✅ | `7e9d06c` (main) |
| ۳c | `apps.flashcards` + `apps.quiz` (ساخته‌شده، قفل) | ✅ | `b7270b3` (main) |
| ۳d | بازنویسی `data_quality_center` | ✅ | `00aee53` (main) |
| ۴ | اسکلت فرانت + دیزاین‌سیستم | ✅ | `ff2e870` (main) |
| ۵a | Auth + Onboarding + shell/nav | ✅ | `f89d37f` (main) |
| ۵b | Dashboard + Lessons + LessonList + LessonDetail | ✅ | برنچ `phase-5b-learning` |
| ۵c–۵d | me / flashcards+quiz+tour | ⬜ | — |
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

## فاز ۳ — اپ‌های بک‌اند (زیرفازی)

**هدف:** پیاده‌سازی همهٔ endpointهای «🔜» در `docs/api-contract.md` (شکل‌ها قفل شده‌اند).

### ۳a — جدول مرجع ATC + `apps.lessons` ✅
- [x] مدل `drugs.AtcCategory` + مرجع دوزبانهٔ bundle‌شده (`apps/drugs/data/atc_reference.py`, ۱۴ L1 + ۸۴ L2) + command `load_atc_reference`
- [x] `apps.lessons` — `GET /lessons/groups/` (درخت با `total`/`done`)، `GET /lessons/chapters/{code}/` (داروها + `exam_points` از هشدار/منع + progress)، `POST /lessons/chapters/{code}/` (ثبت progress)
- [x] ۶ تست جدید → ۵۱/۵۱ · schema سبز · `docs/api-contract.md` به‌روز

### ۳b — `apps.progress` → `/me/*` ✅
- [x] مدل‌ها: `LearnerProgress` (xp، streak، totals، accuracy)، `DailyStudy`، `Mistake`، `StudyPlan` + `services.py` (record_study، bump_mistake، …)
- [x] `GET /me/dashboard` (فصل بعدی از lessons + focus session با ردیف mistake/lesson؛ ردیف leitner در ۳c)، `GET /me/statistics` (نمودار هفتگی از DailyStudy + mastery از پیشرفت درس‌ها)، `GET /me/mistakes` + `POST .../resolve` + `POST .../restore`، `GET|PUT /me/plan`
- [x] ۹ تست جدید → ۶۰/۶۰ · schema سبز · `docs/api-contract.md` به‌روز
- [x] روتر maintenance کوییز از `me/*` پاک شد (progress صاحب `/me/*` است)

### ۳c — `apps.flashcards` + `apps.quiz` (ساخته‌شده، پشت فلگ خاموش) ✅
- [x] `apps.flashcards` — `LeitnerCard` (بدون جدول محتوا؛ front/back از پروفایل دارو)، جعبه‌های ۱..۵ (فاصله ۰/۳/۷/۱۶/۳۵ روز)، `seed`/`due`/`boxes`/`review` (review به `progress.record_study` وصل)
- [x] `apps.quiz` — تولید سؤال دسته‌بندی ATC (دارو→دسته و دسته→دارو)، نمره‌دهی سمت سرور، `finish` → `record_study` + `bump_mistake`
- [x] فلگ‌ها `QUIZ_API_ENABLED`/`FLASHCARDS_API_ENABLED` پیش‌فرض **خاموش**؛ روتر maintenance `503 FEATURE_NOT_AVAILABLE` (حالا `csrf_exempt`)
- [x] ۱۳ تست جدید (با `ROOT_URLCONF` مخصوص برای هر دو حالت فلگ) → ۷۳/۷۳ · schema هر دو حالت سبز
- [~] برند/ژنریک از `spl_records` — به فاز بعد موکول (فعلاً نام دارو = نام ماده)

### ۳d — بازنویسی `data_quality_center` ✅
- [x] حذف کامل نسخهٔ قدیمی (services/forms/step_up/views/templates وابسته به `ai_data_pipeline`)
- [x] نسخهٔ تازهٔ لاغر: مدل `SectionEdit` (append-only)، ۴ ویو staff-only (list با فیلتر «خلاصهٔ ناقص»، detail با فرم ویرایش هر سکشن، history)، ۴ تمپلیت مینیمال
- [x] فقط `summary_fa`/`summary_en` قابل‌ویرایش (متن خام read-only)؛ reason اجباری (حداقل `DATA_QUALITY_MIN_REASON_LENGTH`)
- [x] `apps.data_quality_center` دوباره در INSTALLED_APPS؛ URLها فقط با `DATA_QUALITY_CENTER_ENABLED` زیر `/ops/data-quality/`
- [x] ۷ تست جدید → **۸۰/۸۰** · schema با همهٔ فلگ‌ها روشن سبز

**فاز ۳ کامل شد.** بعدی: فاز ۴ (اسکلت فرانت + دیزاین‌سیستم).

## فاز ۴ — اسکلت فرانت + دیزاین‌سیستم ✅

**هدف:** پروژهٔ React قابل‌اجرا با تم روشن/تیره، RTL و ناوبری درست.

- [x] پروژهٔ Expo (SDK 57) + `react-native-web` + TypeScript در `frontend/` (طراحی `.dc.html` به‌عنوان مرجع نگه داشته شد)
- [x] **انحراف از نقشه:** به‌جای Expo Router، ناوبری state-machine (مثل `frontend_old`) — برای طراحی سفارشی و pixel-work فاز ۵ ساده‌تر
- [x] `src/theme/tokens.ts` — پالت کامل روشن/تیره از THEME طراحی + spacing/radius/typography/shadow/motion؛ `ThemeProvider` (persist + پیش‌فرض سیستم)
- [x] `src/i18n/` — دیکشنری fa/en از `STR` طراحی، `LanguageProvider` (RTL، ارقام فارسی، persist)، Vazirmatn با `expo-font`
- [x] primitiveها: `AppText`, `Button`, `Card`, `Input`, `Chip`, `Screen` (انیمیشن `fadeUp`), `LoadingState`, `IconImage`
- [x] `AppShell` (شل ۴۳۰px + mesh) + `BottomNav` ۵-تبی + حالت تب «قفل» (نقطهٔ هشدار روی flashcards/quiz)
- [x] `src/api/` — axios client با interceptor refresh توکن `UserSession` + retry ۵۰۳، `types.ts` مطابق قرارداد، `endpoints.ts` (همهٔ مسیرها)، react-query
- [x] `src/store/` — zustand: `auth` (SecureStore/AsyncStorage، hydrate، refresh، logout)، `nav` (state-machine)
- [x] صفحه‌ها: Auth (login/signup واقعی، وصل به بک‌اند)، Onboarding (واقعی)، Dashboard/Lessons/LessonDetail/Profile (واقعی، پایه)، Flashcards/Quiz (حالت قفل)، Mistakes/Statistics/Planning/Uptodate (stub)
- [x] job `frontend` در CI فعال شد (`npm ci` → `typecheck` → `build:web`)
- [x] تأیید: `tsc --noEmit` سبز · `expo export --platform web` موفق (۴۷۸ ماژول، dist ساخته شد)

## فاز ۵ — پیاده‌سازی صفحه‌ها + اتصال (زیرفازی)

**هدف:** اپ کامل، هر صفحه مطابق `.dc.html` (پالت/فاصله/شعاع/تایپوگرافی دقیق)، وصل به API فاز ۲/۳.

### ۵a — Auth + Onboarding + پرداخت shell/nav ✅
- [x] `HeaderMesh` (گرادیان accent) + `GlassToggles` (زبان/تم شیشه‌ای) با `react-native-svg`
- [x] `AuthScreen` بازطراحی: لوگو، sheet گرد سفید، login/signup واقعی، سوییچ حالت، شرایط
- [x] `OnboardingScreen` ۴ مرحله: ۳ اسلاید (آیکون SVG + عنوان + توضیح) + فرم چیپ‌ها (۳ گروه) + نقطه‌های پیشرفت + Next/Start/Back، وصل به `POST /auth/onboarding/`
- [x] `BottomNav`: قرص لغزندهٔ انیمیشنی پشت تب فعال + نگاشت صفحه→تب (mistakes/stats/planning زیر profile)

### ۵b — Dashboard + focus session + Lessons + LessonDetail ✅
- [x] `DashboardScreen` مطابق طراحی: هدر accent (لوگو/تم/زبان + خوش‌آمد زمان‌محور)، کارت مرجع UpToDate، گرید ۶ مسیر، بخش «فصل بعدی» با کارت **جلسهٔ تمرکز** تاشو (ردیف‌های tinted + دکمهٔ شروع) — از `/me/dashboard/`
- [x] `LessonsScreen`: آکاردئون گروه‌های ATC (badge کد، نوار پیشرفت جمع‌شونده)، بازشدن → زیرگروه‌ها با نوار fill — از `/lessons/groups/`
- [x] `LessonListScreen` (جدید): overlay تمام‌صفحه، eyebrow گروه + نام فصل + `code · تعداد`، لیست داروها با شمارهٔ/تیک خوانده‌شده — از `/lessons/chapters/{code}/`
- [x] `LessonDetailScreen`: نام دارو (۲۶/۹۰۰) + خط ATC + بج‌ها (جعبه‌سیاه/کنترل‌شده/زمان مطالعه)، بلوک‌های `lesson_sections` با رنگ tone (deny/boxed/caution/special)، toggle «نسخهٔ انگلیسی» هر بلوک، جست‌وجوی درون‌فصل، نوار پیشرفت اسکرول + ثبت خودکار خوانده‌شدن (`POST /lessons/chapters/{code}/`)، CTA خودآزمایی
- [x] flow: tab → آکاردئون → زیرگروه → LessonList → دارو → LessonDetail
- [x] tsc سبز · `expo export` موفق (۵۱۰ ماژول)

### ۵c — Mistakes + Statistics + Planning + Profile ⬜
### ۵d — Flashcards + Quiz (UI کامل، قفل) + تور راهنما/help ⬜

## فاز ۶ — uptodate + جمع‌بندی + انتشار ⬜

**هدف:** قابل‌عرضه.

- [ ] `apps.uptodate` روی دیتابیس‌های `/home/amir/Documents/UpToDate/` (content / toc / search / fts) + API خواندنی + صفحهٔ `uptodate`
- [ ] نهایی‌سازی `docker-compose` / `Dockerfile` فرانت / CI
- [ ] حذف `frontend_old/`
- [ ] `render.yaml` / deploy، کانفیگ EAS build (iOS/Android)
