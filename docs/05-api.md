# ۵. قرارداد API (نسخهٔ ۱)

این فایل همهٔ مسیرهای API اپ را فهرست می‌کند. شکل دقیق و به‌روز هر درخواست و پاسخ در Swagger زنده هم هست:

- production: `https://api.pharmenta.ir/api/v1/docs/` (schema خام: `/api/v1/schema/`)
- محلی: `http://127.0.0.1:8000/api/v1/docs/`

نوع‌های سمت اپ در `frontend/src/api/types.ts` و فراخوانی‌ها در `frontend/src/api/endpoints.ts` با این قرارداد هم‌خوان نگه داشته می‌شوند.

## قواعد کلی

| موضوع | قاعده |
|---|---|
| نشانی پایه | `https://api.pharmenta.ir/api/v1/` |
| نام‌های قدیمی | بخش‌های `auth`، `drugs`، `lessons`، `me`، `uptodate`، `quiz` و `flashcards` یک نشانی بدون نسخه هم دارند (`/api/...`). برای کد تازه فقط `/api/v1/` را به کار ببرید |
| احراز هویت | `Authorization: Bearer <access_token>`. همهٔ مسیرها احراز هویت می‌خواهند، مگر آن‌هایی که در جدول‌ها «عمومی» علامت خورده‌اند |
| تمدید توکن | `POST /auth/refresh/` با `refresh_token`. هر تمدید توکن تمدید را عوض می‌کند |
| بدنه | JSON. پاسخ‌های بزرگ gzip می‌شوند |
| زبان داده | فیلدهای دوزبانه جفت‌اند (`name_fa` / `name_en`)؛ اپ بر اساس زبان فعال انتخاب می‌کند |
| صفحه‌بندی | مسیرهای صفحه‌بندی‌شده `?page=` و `?page_size=` (پیش‌فرض ۲۰، حداکثر ۱۰۰) می‌گیرند و `{count, next, previous, results}` برمی‌گردانند |
| شناسهٔ درخواست | هر پاسخ هدر `X-Request-ID` دارد؛ همان در لاگ سرور ثبت می‌شود |

### قالب خطا

همهٔ خطاها یک شکل دارند:

```json
{ "code": "PREMIUM_REQUIRED", "message": "Your plan does not include this feature.", "details": { "feature": "uptodate" } }
```

`code` ثابت است و اپ بر اساس آن تصمیم می‌گیرد. `message` برای اشکال‌زدایی است. پیام‌های بخش حساب (کد پیامکی، رمز) فارسی و قابل نمایش به کاربرند.

کدهای عمومی:

| HTTP | `code` | معنی |
|---|---|---|
| 400 | `INVALID` یا کد اختصاصی | ورودی نادرست؛ خطای هر فیلد در `details` |
| 401 | `NOT_AUTHENTICATED` / `AUTHENTICATION_FAILED` | توکن نیست یا نامعتبر است؛ اپ یک بار تمدید می‌کند |
| 402 | `PREMIUM_REQUIRED` | پلن کاربر این ویژگی را ندارد (`details.feature`) |
| 402 | `QUOTA_EXCEEDED` | سهمیه تمام شده (`details: {feature, limit, period, used}`) |
| 403 | `PERMISSION_DENIED` | دسترسی کافی نیست |
| 404 | `NOT_FOUND` | پیدا نشد |
| 429 | `THROTTLED` | درخواست زیاد؛ `details` زمان انتظار را دارد |
| 503 | `FEATURE_NOT_AVAILABLE` | بخش خاموش است (پرچم قابلیت) یا دادهٔ آن روی سرور نیست |

## سلامت — عمومی

| روش | مسیر | پاسخ |
|---|---|---|
| GET | `/health/` | وضعیت سرور و دیتابیس. 200 یا 503 |
| GET | `/live/` | فقط زنده بودن پروسه (بدون دیتابیس) |
| GET | `/ready/` | دیتابیس، کش و (اگر لازم باشد) صف. 200 یعنی آمادهٔ سرویس |

```jsonc
{ "status": "ok", "service": "learning-platform-api", "version": "0.1.0", "environment": "production",
  "release_sha": "…", "time": "…", "checks": { "database": "ok", "database_latency_ms": 2.1 } }
```

## نسخهٔ اپ — `/app/`

| روش | مسیر | دسترسی | پاسخ |
|---|---|---|---|
| GET | `/app/release/?platform=android&version_code=100` | عمومی | آیا این نسخهٔ نصب‌شده باید به‌روز شود |

`platform` یکی از `android` و `ios` است. `version_code` همان عددی است که اپ از نسخه‌اش می‌سازد (`major×10000 + minor×100 + patch`). پاسخ از نسخه‌هایی ساخته می‌شود که در پنل سایت «پیشنهاد به‌روزرسانی در اپ» دارند ([08-deployment.md](08-deployment.md#پیام-به‌روزرسانی-داخل-اپ)). کد: `apps/website/api.py`.

```jsonc
{ "update": "optional",            // "none" | "optional" | "required"
  "latest": { "version": "0.2.0", "version_code": 200, "notes": ["…", "…"],
              "released_at": "2026-10-25", "download_url": "https://pharmenta.ir/download/" } }
```

وقتی هیچ نسخه‌ای اعلام نشده، `latest` برابر `null` و `update` برابر `"none"` است.

## حساب و احراز هویت — `/auth/`

| روش | مسیر | توضیح |
|---|---|---|
| POST | `/auth/otp/request/` — عمومی | `{phone, purpose: "signup"\|"reset"}` ← `{phone, code_length, expires_in, resend_in}`. خطاها: 409 `PHONE_REGISTERED` (ثبت‌نام با شماره‌ای که رمز دارد)، 404 `PHONE_NOT_REGISTERED` (بازیابی)، 429 `OTP_TOO_SOON` (`details.retry_after`) یا `OTP_DAILY_LIMIT`، 503 `SMS_SEND_FAILED` |
| POST | `/auth/otp/verify/` — عمومی | `{phone, purpose, code, device_name?}` ← `AuthTokenResponse` (201 اگر حساب همین الان ساخته شد). خطاها: 400 `OTP_INVALID` (`details.attempts_left`)، `OTP_EXPIRED`، `OTP_LOCKED` |
| POST | `/auth/password/set/` | `{new_password, new_password_confirm, name?, current_password?}` ← `User`. `current_password` فقط وقتی لازم است که حساب رمز دارد و نشست تازه با کد پیامکی تأیید نشده. نشست‌های دیگر بسته می‌شوند |
| POST | `/auth/login/` — عمومی | `{username, password, device_name?}` ← `AuthTokenResponse`. `username` شمارهٔ موبایل (هر نوشتار)، ایمیل یا نام کاربری. 400 `INVALID_CREDENTIALS` |
| POST | `/auth/refresh/` — عمومی | `{refresh_token}` ← `AuthTokenResponse`. 401 `INVALID_REFRESH_TOKEN` |
| POST | `/auth/logout/` · `/auth/logout-all/` | بستن نشست فعلی / همهٔ نشست‌ها |
| GET / PATCH | `/auth/me/` | کاربر فعلی با `profile` / ویرایش بخشی از پروفایل (`display_name`، `language`...) |
| POST | `/auth/onboarding/` | `{study_field, study_goal, study_level, display_name?, language?}` و فیلدهای برنامه ← `User`؛ `profile.onboarded_at` را می‌گذارد. با `daily_minutes` و `study_days` (۷ مقدار، از شنبه)، برنامهٔ مطالعه هم ساخته می‌شود ([پایین](#برنامهٔ-ساخته‌شده-از-آنبوردینگ)) |
| GET | `/auth/sessions/` · POST `/auth/sessions/{id}/revoke/` | فهرست دستگاه‌ها / بستن یکی (404 `SESSION_NOT_FOUND`) |
| POST | `/auth/step-up/` | تأیید دوبارهٔ رمز برای کار حساس. 400 `STEP_UP_FAILED` |
| POST | `/auth/register/` — عمومی | ثبت‌نام ایمیلی؛ تا `AUTH_EMAIL_REGISTRATION_ENABLED` خاموش است، 403 `EMAIL_REGISTRATION_CLOSED` |
| POST | `/auth/password-reset/` · `/auth/password-reset/confirm/` — عمومی | بازیابی ایمیلی برای حساب‌های قدیمی ایمیلی. 400 `INVALID_PASSWORD_RESET_TOKEN` |
| GET | `/auth/roles/` · GET/POST `/auth/role-assignments/` · POST `/auth/role-assignments/{id}/revoke/` · GET `/auth/security-events/` | نقش‌ها و رویدادهای امنیتی (کارکنان) |

```jsonc
// User
{ "id": 1, "username": "…", "email": "…", "first_name": "…", "last_name": "…",
  "roles": ["learner"], "has_password": true, "is_guest": false,
  "profile": { "display_name": "…", "study_field": "pharmacy",   // "" | pharmacy | medicine
               "study_goal": "comprehensive",                     // "" | comprehensive | final | clinical
               "study_level": "advanced",                         // "" | beginner | intermediate | advanced
               "language": "fa", "onboarded_at": "…" | null, "is_onboarded": true } }
// AuthTokenResponse
{ "user": { /* User */ }, "access_token": "phx_access_…", "refresh_token": "phx_refresh_…",
  "token_type": "Bearer", "access_expires_at": "…", "refresh_expires_at": "…", "session_id": "uuid" }
```

## مهمان — `/guest/`

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/guest/status/` — عمومی | `{enabled}` |
| POST | `/guest/session/` — عمومی | حساب یک‌بارمصرف (`user.is_guest: true`، بدون رمز، پروفایل تکمیل‌شده) با همان پاسخ ورود. محدود به ۲۰ بار در ساعت برای هر IP. 403 `GUEST_ACCESS_DISABLED` |

## داروها — `/drugs/` و `/atc/`

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/drugs/?search=&atc=&page=` | فهرست صفحه‌بندی‌شده. `search`: پیشوند نام یا RXCUI دقیق. `atc`: پیشوند کد ATC |
| GET | `/drugs/{slug}/` | جزئیات ماده با همهٔ بخش‌های بالینی (`sections`) و بخش‌های درس‌نامه (`lesson_sections`) |
| GET | `/atc/?prefix=` | کدهای ATC موجود با تعداد ماده (بدون صفحه‌بندی) |

```jsonc
// یک ماده در فهرست
{ "rxcui": "52175", "name": "losartan", "slug": "losartan-52175", "n_products": 7, "n_source_records": 206,
  "pharm_classes": ["Angiotensin 2 Receptor Blocker"],
  "atc_codes": [{ "code": "C09CA", "name": "…", "level": 4 }] }
// بخش درس‌نامه
{ "key": "mechanism", "field": "clinical_pharmacology", "title_fa": "مکانیسم", "title_en": "Mechanism",
  "tone": "info",            // info | deny | boxed | caution | special
  "text_fa": "…", "text_en": "…", "has_summary": true }
// ترتیب کلیدها: mechanism, indication, dose, forms, contraindications, do_not_use, boxed_warning,
// warning, side, interactions, pregnancy, abuse — کلیدی که خلاصه ندارد حذف می‌شود
```

## درس‌نامه — `/lessons/` (ویژگی `lessons`)

ساختار: **دسته** (۱۲ دستهٔ بدن/حوزه) ← **موضوع** بالینی (`apps/lessons/data/study_topics.py`) ← **فصل** (زیرگروه ATC سطح ۲) ← **دارو**. یک فصل می‌تواند زیر چند موضوع بیاید و پیشرفتش در همه یکی است.

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/lessons/groups/` | درخت موضوع‌ها با فصل‌ها و پیشرفت هر فصل (`total`، `done`) |
| GET | `/lessons/chapters/{atc_code}/` | یک فصل: موضوع‌ها، فهرست داروها (بدون متن درس) و پیشرفت (`read_drug_slugs`، `scroll_pct`، `last_opened_at`) |
| POST | `/lessons/chapters/{atc_code}/` | ثبت پیشرفت: `{drug_slug?, scroll_pct?}`؛ دارو باید در همین فصل باشد، وگرنه 400 `INVALID_DRUG`. پاسخ همان شکل GET |
| GET | `/lessons/search/?q=` | جست‌وجوی دارو با نام انگلیسی یا فارسی (دست‌کم ۲ حرف، یکسان‌سازی ی/ي، ک/ك، نیم‌فاصله)؛ حداکثر ۲۰؛ هر نتیجه فصل‌هایش را دارد |
| GET | `/lessons/drugs/{slug}/` | درس یک دارو (`lesson_sections`) |

خوانده‌شدن دارو سراسری است: دارویی که در چند فصل هست، با یک بار خواندن همه‌جا خوانده‌شده نشان داده می‌شود.

## پیشرفت و برنامه — `/me/`

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/me/dashboard/` | نام، استریک، XP، فصل بعدی، و «جلسهٔ تمرکز» (کارت‌های موعد، اشتباه، درس) |
| GET | `/me/statistics/` | `{week_bars[7], accuracy_pct, quizzes, reviews, minutes, mastery_pct}` (روز ۰ = شنبه) |
| GET | `/me/mistakes/` · POST `/me/mistakes/{id}/resolve/` · POST `/me/mistakes/restore/` | اشتباهات / حل‌شده کردن یکی / برگرداندن همه |
| GET / PUT | `/me/plan/` | برنامهٔ مطالعه (ویژگی `stats`). پاسخ PUT `fits_deadline` هم دارد. تغییر حالت، موضوع‌ها یا تاریخ یعنی برنامهٔ تازه: شمارش هفته‌ها از همان روز شروع می‌شود |
| GET | `/me/plan/today/?brief=1` | کارهای امروز، خلاصهٔ برنامه و این هفته (پایین). بدون `brief`، پیشرفت و تسلط هر موضوع برنامه هم می‌آید (`topics`)؛ خانهٔ اپ `brief=1` می‌فرستد چون برای آزمون پایان دوره همهٔ موضوع‌ها در برنامه‌اند |
| POST | `/me/plan/items/{id}/complete/` · `/skip/` | انجام‌شده / ردشده کردن یک کار. 404 `NOT_FOUND` |

```jsonc
// GET /me/plan/today/?brief=1
{ "mode": "goal",                       // none | goal | maintenance
  "items": [{ "id": 12, "day": "2026-10-25", "activity_type": "lesson", // lesson | quiz | flashcards | mistake_review
              "topic_key": "cv-htn", "atc_code": "C02", "estimated_minutes": 10, "status": "pending",
              "title_fa": "درسنامه: ضدفشارخون‌ها", "title_en": "Lesson: Antihypertensives", "…": "…" }],
  "total_minutes": 28, "topics": [],
  "summary": { "daily_minutes": 30, "study_days": 5, "deadline": "2026-12-06",
               "days_left": 42, "week_index": 2, "week_count": 6, "progress_pct": 18 },  // سه‌تای آخر فقط در حالت goal
  "week": [{ "date": "2026-10-24", "study_day": true, "state": "done" }, …] }  // ۷ روز از شنبه
// state: done | missed | today | planned | free | off (پیش از شروع برنامه)
```

- **خودکار انجام‌شدن:** کار امروز وقتی بیرون از برنامه انجام شده باشد، خودش «انجام‌شده» می‌شود:
  - درس: وقتی فصلش کامل خوانده شده باشد.
  - آزمون: وقتی آزمونی روی همان موضوع تمام شده باشد.
  - فلش‌کارت: وقتی دستهٔ همان موضوع مرور شده باشد، یا در مرور سررسیده‌ها، وقتی کارتی سررسیده نمانده باشد.
  - مرور اشتباه: وقتی اشتباه بازی نمانده باشد.
- **روز جامانده:** در حالت goal، اگر از روزهای گذشته کاری مانده باشد، با اولین درخواست هر روز باقی برنامه از امروز دوباره چیده می‌شود. کارهای آن روز در هفته «missed» نشان داده می‌شوند و فقط یک بار در پیشرفت حساب می‌شوند.

### برنامهٔ ساخته‌شده از آنبوردینگ

کد: `apps/progress/planning.py`، تابع `plan_from_onboarding`.

| `study_goal` | برنامه | فیلدهای لازم |
|---|---|---|
| `comprehensive` (آزمون پایان دوره) | goal روی همهٔ موضوع‌ها تا `exam_date` | `exam_date`، `daily_minutes`، `study_days` |
| `final` (امتحانات ترم) | goal روی موضوع‌های دسته‌های انتخاب‌شده تا `exam_date` | به‌اضافهٔ `category_keys` (کلیدهای ۱۲ دستهٔ درسنامه) |
| `clinical` (مرور بالینی روزانه) | maintenance، بدون تاریخ | `daily_minutes`، `study_days` |

- **تاریخ آزمون:** `exam_date` باید بعد از امروز باشد.
- **سطح:** سرعت برنامه را تعیین می‌کند؛ هر فصل برای مبتدی ۱۴، متوسط ۱۰ و پیشرفته ۷ دقیقه برنامه‌ریزی می‌شود.
- **رشته:** پزشکی و داروسازی هر دو همان درسنامهٔ داروها را برنامه‌ریزی می‌کنند.

## فلش‌کارت — `/flashcards/` (ویژگی `flashcards`؛ پرچم `FLASHCARDS_API_ENABLED`)

کارت برای هر (کاربر، دارو) است. پشت کارت پنج بخش دارد: `indication`، `adr_common`، `adr_serious`، `dosage_forms`، `contra_boxed`. پنج جعبه با فاصلهٔ ۰ / ۳ / ۷ / ۱۶ / ۳۵ روز.

| روش | مسیر | توضیح |
|---|---|---|
| POST | `/flashcards/seed/` | ساخت کارت‌های جعبهٔ ۱ (تکرارپذیر) ← `{created, deck_size}` |
| GET | `/flashcards/` | حداکثر ۲۰ کارت موعدرسیده |
| GET | `/flashcards/boxes/` | `[{box, count, due, next_due_at}]` |
| POST | `/flashcards/{id}/review/` | `{rating: "easy"\|"hard"}`؛ easy جعبه را بالا و hard پایین می‌برد |
| GET | `/flashcards/decks/` | دسته‌ها و موضوع‌ها با پیشرفت |
| GET | `/flashcards/decks/{topic}/` | کارت‌های یک موضوع به ترتیب ثابت، با `position`، `known`، `hard`، `finished`، `next_topic` |
| POST | `/flashcards/decks/{topic}/answer/` | `{drug_slug, rating}`؛ 422 `NOT_IN_DECK` |
| POST | `/flashcards/decks/{topic}/restart/` | شروع دوبارهٔ موضوع |

## آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`)

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/quiz/overview/` | آمار و نشان‌های صفحهٔ انتخاب آزمون |
| GET | `/quiz/preview/?category=&atc_code=&count=` | اینکه آزمون با این انتخاب چه چیزهایی را پوشش می‌دهد. 400 `INVALID_CATEGORY` |
| POST | `/quiz/start/` | `{category, atc_code?, count}` (count: ۵، ۱۰، ۱۵ یا ۲۰) ← جلسه با سؤال‌ها، بدون کلید پاسخ. 422 `INSUFFICIENT_QUESTIONS` |
| POST | `/quiz/{id}/answer/` | `{question_id, selected_index, client_answered_at?}` ← `{correct, correct_index}`. 409 `ALREADY_ANSWERED` / `QUIZ_ALREADY_FINISHED`، 400 `INVALID_QUESTION`. با اعمال فروش، هر پاسخ از سهمیه کم می‌کند (402 ممکن است) |
| POST | `/quiz/{id}/finish/` | ← `{score, total, mistakes_added}`؛ فقط یک بار. XP و آمار و اشتباه‌ها را ثبت می‌کند |
| POST | `/quiz/{id}/review-mistakes/` | آزمون تازه از سؤال‌های غلط همان جلسه. 409 `QUIZ_NOT_FINISHED`، 422 `NOTHING_TO_REVIEW` |

## UpToDate — `/uptodate/` (ویژگی `uptodate`)

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/uptodate/topics/?search=&limit=` | جست‌وجو فقط در عنوان (پیشوند کلمه‌ها با AND)؛ `limit` پیش‌فرض ۲۵، حداکثر ۵۰. ← `[{id, title, section, version, updated, snippet}]`. باز است و از سهمیه کم نمی‌کند |
| GET | `/uptodate/topics/{id}/` | ← `{id, title, section, version, updated, contributors[], outline_html, body_html}`. یک بار از سهمیه کم می‌کند |
| GET | `/uptodate/images/{id}/` | تصویر یا جدول مقاله |

اگر منبع داده (MySQL یا SQLite) نباشد، 503 `FEATURE_NOT_AVAILABLE`.

## Lexicomp — `/lexicomp/` (ویژگی `lexicomp`)

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/lexicomp/drugs/?search=&limit=` | ← `[{id, name, generic_id, kind: "generic"\|"brand"}]`؛ `limit` پیش‌فرض ۲۰، حداکثر ۵۰ |
| POST | `/lexicomp/interactions/` | `{generic_ids: [...]}` ← فهرست تداخل‌ها مرتب بر اساس شدت: `{monograph_id, drug_ids, object_generic_id, object_name, precipitant_generic_id, precipitant_name, severity, reliability, summary, management, discussion, footnotes}`. هر بررسی یک بار از سهمیه کم می‌کند |

## Medscape — `/medscape/` (ویژگی `medscape`)

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/medscape/tree/?kind=disease\|guideline` | درخت دسته و تخصص |
| GET | `/medscape/articles/?kind=&search=&category=&specialty=&recent=&limit=` | فهرست مقاله‌ها `{slug, title, kind, latest_update}` |
| GET | `/medscape/articles/{slug}/` | مقاله با `meta`، `url`، `categories`، `sections`. یک بار از سهمیه کم می‌کند |
| GET | `/medscape/images/{id}/` | `{id, content_type, data_base64}` |

## ماشین‌حساب — `/calculators/` (ویژگی `calculators`)

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/calculators/categories/` | کل درخت دسته‌ها (دوزبانه) |
| GET | `/calculators/` | همهٔ ماشین‌حساب‌ها (بدون صفحه‌بندی؛ فقط نام، توضیح و دسته) |
| GET | `/calculators/{slug}/` | سؤال‌ها، فرمول‌ها و نتیجه‌ها برای موتور سمت اپ. یک بار از سهمیه کم می‌کند |

## دانلود آفلاین — `/offline/`

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/offline/packages/` | `[{dataset, entitled, license_days, package}]`؛ `package` همان manifest نسخهٔ فعلی یا `null` (منتشر نشده) |
| POST | `/offline/packages/{dataset}/urls/` | `{build?}` ← `{build, expires_at, files: [{name, size, sha256, md5, url}]}` با لینک امضاشدهٔ هر قطعه. 402 `PREMIUM_REQUIRED`، 503 (منتشر نشده)، 409 `PACKAGE_REPLACED` (نسخهٔ درخواستی دیگر نسخهٔ فعلی نیست) |
| POST | `/offline/packages/{dataset}/license/` | `{build, public_key?}` ← `{build, server_time, valid_until, key}` در اپ بومی، یا `wrapped_key` (رمزشده با کلید عمومی RSA مرورگر) در وب. 402، 404 (نسخه به این مجموعه نمی‌خورد)، 400 `VALIDATION_ERROR` (کلید نادرست)، 503 (`OFFLINE_PACKAGE_SECRET` تنظیم نیست) |
| GET | `/offline/files/{token}/` — عمومی با توکن امضاشده | فقط در توسعه (`OFFLINE_PACKAGES_DIR`)؛ جانشین باکت، با پشتیبانی Range |

`dataset` یکی از `uptodate` یا `lexicomp` است. دانلود و مجوز فقط برای staff یا پلن پولی فعالی است که آن ویژگی را دارد، حتی وقتی اعمال فروش خاموش است.

## صورتحساب — `/billing/`

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/billing/catalog/` | `{free, plans[], products[]}`؛ هر کدام با `prices[]` و `features[]` (فقط پلن‌های `active`) |
| GET | `/billing/me/` | `{enforced, features[{key, name_fa, limit, period, used}], entitlements[...]}` |
| POST | `/billing/quote/` | `{price_id, discount_code?}` ← `{amount_toman, discount_toman, payable_toman}`. 400 `PRICE_NOT_AVAILABLE` یا `DISCOUNT_NOT_FOUND` / `DISCOUNT_INACTIVE` / `DISCOUNT_NOT_STARTED` / `DISCOUNT_EXPIRED` / `DISCOUNT_USED_UP` / `DISCOUNT_NOT_FOR_PLAN`. 403 `GUEST_CANNOT_BUY` |
| POST | `/billing/checkout/` | همان بدنه ← 201 `{order_id, status, payment_url}`؛ سفارش ۱۰۰٪ تخفیف بی‌درنگ `paid` می‌شود. 502 `GATEWAY_ERROR`، 503 `SALES_PAUSED` |
| GET | `/billing/orders/` | ۵۰ سفارش آخر کاربر |
| GET | `/billing/callback/` · `/billing/callback/{kind}/` — عمومی | بازگشت از درگاه؛ تأیید پرداخت، دادن دسترسی (فقط یک بار) و نمایش صفحهٔ HTML نتیجه |
| GET | `/billing/result/{token}/` — عمومی | صفحهٔ HTML نتیجهٔ پرداخت |

روی سایت همین بازگشت‌ها در `/pay/callback/...` و `/pay/result/...` هم هستند ([12-website.md](12-website.md)).

## مسیرهای غیر API

این‌ها صفحهٔ HTML هستند و در [11-admin-consoles.md](11-admin-consoles.md) و [12-website.md](12-website.md) توضیح داده شده‌اند:

| مسیر | چیست |
|---|---|
| `/admin/` | ادمین Django |
| `/ops/` | کنسول فروش (superuser) |
| `/ops/data-quality/` | مرکز کیفیت داده (staff) |
| `/panel/` (روی `pharmenta.ir`) | پنل محتوای سایت |

## تغییر دادن API

1. سریالایزر و ویو را در اپ مربوط تغییر دهید و `@extend_schema` را به‌روز کنید.
2. تست ویو را اضافه یا اصلاح کنید.
3. `frontend/src/api/types.ts` و `endpoints.ts` را هم‌خوان کنید و `npm run typecheck` بزنید.
4. همین فایل را به‌روز کنید.
5. اگر شکل پاسخی ناسازگار عوض شد، `CACHE_BUSTER` در `frontend/src/api/queryClient.ts` را تغییر دهید. اپ‌های نصب‌شدهٔ قدیمی هنوز شکل قبلی را انتظار دارند؛ برای همین فیلد را حذف نکنید و فیلد تازه اضافه کنید.
