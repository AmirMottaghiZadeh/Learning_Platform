# ۵. قرارداد API (نسخهٔ ۱)

این فایل همهٔ مسیرهای API اپ را فهرست می‌کند. شکل دقیق و به‌روز هر درخواست و پاسخ در Swagger زنده هم هست:

- production: `https://api.pharmenta.ir/api/v1/docs/` (schema خام: `/api/v1/schema/`)
- محلی: `http://127.0.0.1:8000/api/v1/docs/`

نوع‌های سمت اپ در `frontend/src/api/types.ts` و فراخوانی‌ها در `frontend/src/api/endpoints.ts` با این قرارداد هم‌خوان نگه داشته می‌شوند.

## قواعد کلی

| موضوع | قاعده |
|---|---|
| نشانی پایه | `https://api.pharmenta.ir/api/v1/` |
| نام‌های قدیمی | بخش‌های `auth`، `drugs`، `lessons`، `me`، `uptodate` و `quiz` یک نشانی بدون نسخه هم دارند (`/api/...`). برای کد تازه فقط `/api/v1/` را به کار ببرید |
| احراز هویت | `Authorization: Bearer <access_token>`. همهٔ مسیرها احراز هویت می‌خواهند، مگر آن‌هایی که در جدول‌ها «عمومی» علامت خورده‌اند |
| تمدید توکن | `POST /auth/refresh/` با `refresh_token`. هر تمدید توکن تمدید را عوض می‌کند |
| بدنه | JSON. پاسخ‌های بزرگ gzip می‌شوند |
| زبان داده | فیلدهای دوزبانه جفت‌اند (`name_fa` / `name_en`)؛ اپ بر اساس زبان فعال انتخاب می‌کند |
| صفحه‌بندی | مسیرهای صفحه‌بندی‌شده `?page=` و `?page_size=` (پیش‌فرض ۲۰، حداکثر ۱۰۰) می‌گیرند و `{count, next, previous, results}` برمی‌گردانند |
| شناسهٔ درخواست | هر پاسخ هدر `X-Request-ID` دارد؛ همان در لاگ سرور ثبت می‌شود |

ورود موفق با پر بودن ظرفیت نشست‌ها رد نمی‌شود: سرور نشست قدیمی‌تر را با دلیل `session_limit_replaced` باطل و پاسخ عادی ورود را صادر می‌کند. توکن دسترسی/تمدید و کوکی نشست جایگزین‌شده دیگر معتبر نیستند.

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
| GET | `/app/legal/{slug}/` | عمومی | `{title, body_html, updated_at}` صفحهٔ منتشرشدهٔ `terms` یا `privacy` سایت، برای صفحهٔ ثبت‌نام اپ؛ هر نشانی دیگر 404 |

`platform` یکی از `android` و `ios` است. `version_code` همان عددی است که اپ از نسخه‌اش می‌سازد (`major×10000 + minor×100 + patch`). پاسخ از نسخه‌هایی ساخته می‌شود که در پنل سایت «پیشنهاد به‌روزرسانی در اپ» دارند ([08-deployment.md](08-deployment.md#پیام-به‌روزرسانی-داخل-اپ)). کد: `apps/website/api.py`.

```jsonc
{ "update": "optional",            // "none" | "optional" | "required"
  "latest": { "version": "0.2.0", "version_code": 200, "notes": ["…", "…"],
              "released_at": "2026-10-25", "download_url": "https://pharmenta.ir/download/" } }
```

وقتی هیچ نسخه‌ای اعلام نشده، `latest` برابر `null` و `update` برابر `"none"` است.

## اعلانات اپ — `/announcements/`

پیام‌هایی که superuser یا `platform_admin` در مدیریت («اپ › اعلانات اپ») می‌نویسد. کد: `apps/announcements/`.

| روش | مسیر | دسترسی | پاسخ |
|---|---|---|---|
| GET | `/announcements/?version_code=100&pwa_state=browser` | کاربر واردشده | اعلان‌هایی که همین حالا برای این کاربر است، سنجاق‌شده‌ها اول و بعد تازه‌ترین |
| POST | `/announcements/{id}/event/` | کاربر واردشده | `{event: "seen" \| "click" \| "dismiss"}` ← `204` |

- **فهرست شامل:** منتشرشده‌ها در بازهٔ زمانی‌شان و برای مخاطبشان (همه، رایگان، مشترک، یا نسخه‌های پایین‌تر از `below_version`؛ این آخری با `version_code`). پیش‌نویسی هم که مدیر برای آزمایش به گوشی همین کاربر فرستاده، با `is_test: true` می‌آید.
- **فهرست بدون:** آنچه کاربر بسته است (`dismiss`)، مگر اینکه اعلان بسته‌شدنی نباشد.
- **رویدادها:** `seen` وقتی کارت روی صفحه آمد؛ `click` وقتی دکمه را زد؛ `dismiss` وقتی بست. هر کدام فقط بار اول ثبت می‌شود و آمار مدیریت از همین‌هاست.
- **نصب وب‌اپ:** انتخاب دکمهٔ «نصب وب‌اپ (PWA)» در مدیریت، `link_kind: "pwa"`، مخاطب `web_new` و قابلیت بستن را تنظیم می‌کند. پاسخ دکمه `kind: "pwa"` دارد؛ نشانی، بخش و پارامتر خالی‌اند. فقط کلاینتی با `pwa_state=browser` آن را دریافت می‌کند؛ `standalone`، `native` و کلاینت‌های قدیمی بدون این پارامتر آن را نمی‌گیرند، حتی برای پیش‌نویس آزمایشی. وضعیت نصب را کلاینت گزارش می‌کند. `click` به‌تنهایی نصب یا بستن محسوب نمی‌شود. `dismiss` برای همان اعلان و همان حساب دائمی است؛ ویرایش و انتشار مجدد آن را بازنشانی نمی‌کند.

```jsonc
[{ "id": 2, "title": "…", "body": "…", "kind": "update", "kind_label": "به‌روزرسانی",
   "button": { "label": "دریافت نسخه", "kind": "url", "url": "https://pharmenta.ir/download/", "screen": "", "param": "" },
   // یا { "kind": "app", "screen": "lesson", "param": "B01", ... }؛ بدون دکمه: null
   "dismissible": true, "pinned": false, "seen": false, "starts_at": "2026-10-26T09:00:00+03:30", "is_test": false }]
```

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
  "is_reviewed": false,
  "pharm_classes": ["Angiotensin 2 Receptor Blocker"],
  "atc_codes": [{ "code": "C09CA", "name": "…", "level": 4 }] }
// بخش درس‌نامه
{ "key": "mechanism", "field": "clinical_pharmacology", "title_fa": "مکانیسم", "title_en": "Mechanism",
  "tone": "info",            // info | deny | boxed | caution | special
  "text_fa": "…", "text_en": "…", "has_summary": true }
// ترتیب کلیدها: mechanism, indication, dose, forms, contraindications, do_not_use, boxed_warning,
// warning, side, interactions, pregnancy, abuse — کلیدی که نه خلاصه و نه اطلاعات سایر منابع دارد حذف می‌شود
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

**بازبینی و اطلاعات سایر منابع:** `is_reviewed` یک Boolean فقط‌خواندنی در داروهای `/drugs/`، جزئیات دارو، داروهای فصل و نتیجهٔ جست‌وجو است. این مقدار از تأیید مستقلِ کل دارو و نسخهٔ فعلی محتوای منتشرشده محاسبه می‌شود؛ ربطی به `read_drug_slugs` یا صرفاً وجود خلاصه ندارد. جزئیات `sections` دارای `other_sources_fa/en` هستند؛ در `lesson_sections` این دو کلید فقط وقتی حداقل یک زبان متن داشته باشد اضافه می‌شوند. بخشِ دارای فقط اطلاعات تکمیلی هم با `has_summary: false` در `lesson_sections` می‌آید؛ بخشِ کاملاً خالی حذف می‌شود. متن‌های پیش‌نویس/در انتظار هیچ‌گاه از این API خواندنی منتشر نمی‌شوند.

ثبت تأیید کل دارو از فرم مدیریت `POST /manage/data/drugs/{slug}/confirm-review/` با CSRF و `version` صفحه انجام می‌شود؛ مجوز تأیید لازم است. این مسیر یک API ویرایشی عمومی در اپ نیست. جزئیات گردش، نسخهٔ قدیمی، سوابق و مهاجرت در [مدیریت کیفیت داده](11-admin-consoles.md#وضعیت-بازبینی-کل-دارو) آمده است.

## پیشرفت و برنامه — `/me/`

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/me/dashboard/` | نام، استریک، XP، فصل بعدی، و «جلسهٔ تمرکز» (کارت‌های موعد، اشتباه، درس) |
| GET | `/me/statistics/` | `{week_bars[7], accuracy_pct, quizzes, minutes, mastery_pct}` (روز ۰ = شنبه) |
| GET | `/me/mistakes/` · POST `/me/mistakes/{id}/resolve/` · POST `/me/mistakes/restore/` | اشتباهات / حل‌شده کردن یکی / برگرداندن همه |
| GET / PUT | `/me/plan/` | برنامهٔ مطالعه (ویژگی `stats`). پاسخ PUT `fits_deadline` هم دارد. تغییر حالت، موضوع‌ها یا تاریخ یعنی برنامهٔ تازه: شمارش هفته‌ها از همان روز شروع می‌شود |
| GET | `/me/plan/today/?brief=1` | کارهای امروز، خلاصهٔ برنامه و این هفته (پایین). بدون `brief`، پیشرفت و تسلط هر موضوع برنامه هم می‌آید (`topics`)؛ خانهٔ اپ `brief=1` می‌فرستد چون برای آزمون پایان دوره همهٔ موضوع‌ها در برنامه‌اند |
| POST | `/me/plan/items/{id}/complete/` · `/skip/` | انجام‌شده / ردشده کردن یک کار. 404 `NOT_FOUND` |

```jsonc
// GET /me/plan/today/?brief=1
{ "mode": "goal",                       // none | goal | maintenance
  "items": [{ "id": 12, "day": "2026-10-25", "activity_type": "lesson", // lesson | quiz | mistake_review
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

## حذف فلش‌کارت

همهٔ مسیرهای `/flashcards/*` در نشانی نسخه‌دار و بدون نسخه حذف شده‌اند و 404 برمی‌گردانند. پرچم `FLASHCARDS_API_ENABLED` کاربردی ندارد. پاسخ آزمون دیگر `added_to_leitner` ندارد و هیچ کارت یا سابقهٔ مرور ایجاد نمی‌کند. جزئیات حذف داده در [سند ۱۹](19-quiz-navigation-and-flashcard-removal.fa.md).

## آزمون — `/quiz/` (ویژگی `quiz`؛ پرچم `QUIZ_API_ENABLED`)

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/quiz/overview/` | آمار و نشان‌های صفحهٔ انتخاب آزمون |
| GET | `/quiz/preview/?category=&atc_code=&count=` | اینکه آزمون با این انتخاب چه چیزهایی را پوشش می‌دهد. 400 `INVALID_CATEGORY` |
| POST | `/quiz/start/` | `{category, atc_code?, count}` (count: ۵، ۱۰، ۱۵ یا ۲۰) ← جلسه با سؤال‌ها، بدون کلید پاسخ. 422 `INSUFFICIENT_QUESTIONS` |
| POST | `/quiz/{id}/answer/` | `{question_id, selected_index, client_answered_at?}` ← `{correct, correct_index, extra_context}`. 409 `ALREADY_ANSWERED` / `QUIZ_ALREADY_FINISHED`، 400 `INVALID_QUESTION`. با اعمال فروش، هر پاسخ از سهمیه کم می‌کند (402 ممکن است) |
| POST | `/quiz/{id}/finish/` | ← `{score, total, mistakes_added}`؛ فقط یک بار. XP و آمار و اشتباه‌ها را ثبت می‌کند |
| POST | `/quiz/{id}/review-mistakes/` | آزمون تازه از سؤال‌های غلط همان جلسه. 409 `QUIZ_NOT_FINISHED`، 422 `NOTHING_TO_REVIEW` |

## UpToDate — `/uptodate/` (ویژگی `uptodate`)

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/uptodate/topics/?search=&limit=` | مفهوم‌ها، نام‌های جایگزین و ارتباط مقاله‌ها از نگاشت snapshot؛ تطبیق عنوان و تصحیح غلط املایی مسیر پشتیبان است ([03-backend.md](03-backend.md#uptodate-و-lexicomp)). بدون `paged`: صفحهٔ اول به شکل فهرست سازگار با کلاینت قبلی؛ `limit` پیش‌فرض ۲۵ و حداکثر ۵۰. با `paged=1&offset=&limit=&section=`: ← `{total, all, sections[{name,count}], terms[], corrected, suggestions[{query,label,kind,count}], results[]}`؛ `limit` تا ۱۰۰. هر نتیجه: `{id,title,section,sections[],version,updated,terms[],corrected,snippet}`. فیلتر `section` با هر تخصص مقاله تطبیق می‌دهد؛ مقاله در هر تخصص یک بار شمرده می‌شود و جمع شمارنده‌ها می‌تواند بیشتر از `all` باشد. `title` متن ساده و `snippet` خالی است. از سهمیه کم نمی‌کند |
| GET | `/uptodate/topics/{id}/` | ← `{id, title, section, sections[], version, updated, contributors[], outline_html, body_html}`. `title` متن ساده است و HTML بدنه و outline حفظ می‌شود. یک بار از سهمیه کم می‌کند |
| GET | `/uptodate/images/{id}/` | تصویر یا جدول مقاله |
| GET | `/uptodate/search-metadata/?build=&version=` | مکمل جست‌وجوی بستهٔ قدیمی، پاسخ باینری `application/octet-stream`: JSON فشرده با zlib در رکورد AES-GCM با کلید همان build. شامل `{schema:1,version,memberships,search}`؛ `search.queries` ردیف‌های `[word,conceptId,weight]` و `search.topics` نگاشت مفهوم به چهار CSV شناسه‌های عمومی/بزرگسال/کودک/آموزش بیمار است. فقط حساب دارای دسترسی پولی آفلاین؛ بدون مصرف سهمیه. نسخهٔ متفاوت → 409، کاتالوگ یا راز بستهٔ ناموجود → 503. مجوز آفلاین را صادر یا تمدید نمی‌کند |

اگر منبع داده (MySQL یا SQLite) نباشد، 503 `FEATURE_NOT_AVAILABLE`.

برای مقصد نتیجهٔ جست‌وجوی آینده، درخواست جزئیات می‌تواند هر دو پارامتر `search_content_hash` (SHA-256 بدنهٔ اصلی، ۶۴ نویسهٔ hex کوچک) و `search_anchor` (شناسهٔ پاراگراف با قالب `utd-` و ۳۲ نویسهٔ hex کوچک) را بدهد. پاسخ فیلد اختیاری `search_anchor_status` دارد: `matched` یعنی نسخه و پاراگراف منطبق است و HTML ویژگی مقصد دارد؛ `missing` یعنی نسخه منطبق است اما مقصد پیدا یا آماده نشد؛ `stale` یعنی بدنه تغییر کرده است و HTML اصلی برگردانده می‌شود. دادهٔ نامعتبر 400 می‌دهد. همهٔ این حالت‌ها مشمول همان احراز هویت و کنترل دسترسی و سهمیهٔ جزئیات مقاله هستند؛ بدون دو پارامتر، رفتار قبلی حفظ می‌شود. این قرارداد به‌تنهایی endpoint جست‌وجوی هوشمند نیست.

استخراج فعلی `utd-blocks-v4` است. شناسهٔ پاراگراف به نسخهٔ استخراج هم وابسته است. حتی اگر hash بدنه ثابت بماند، anchor نسخهٔ قبلی استخراج می‌تواند `missing` شود.

endpoint جداگانهٔ جست‌وجوی برداری و سلسله‌مراتبی بخش/پاراگراف هنوز وجود ندارد و در فاز ۶ [برنامهٔ جست‌وجو](search/README.md) اضافه می‌شود، به‌علاوهٔ فیلد `interpretation`. مسیر فعلی `/uptodate/topics/` جست‌وجوی مفهومی در سطح مقاله و پیشنهاد خودکار را دارد. قرارداد پیشنهادیِ نتیجهٔ سلسله‌مراتبی در [سند ۱۴](14-search-architecture-proposal.fa.md#قرارداد-نتیجه) آمده است:

- `result_level` و `items[].kind`: یکی از `article`، `section` یا `paragraph`.
- مقصد مقاله فقط `article_id` دارد. مقصد بخش `section_id` هم دارد. مقصد پاراگراف علاوه بر این‌ها `paragraph_id` دارد.

پیشنهادها حداکثر ۱۲ مفهوم متمایز و قابل انتخاب هستند، به ترتیب اولویت snapshot. `kind` یکی از `general`، `treatment`، `diagnosis` و `followup` است و از واژه‌های عبارت برای گروه‌بندی نمایشی تعیین می‌شود؛ برچسب تشخیص پزشکی نیست. `count` عدد صحیحِ تعداد مقاله‌های معتبر و یکتای مرتبط با مفهوم و مخاطب همان عبارت است، پیش از فیلتر تخصص؛ با تعداد تمام نتایج جست‌وجو یکی فرض نشود. بستهٔ آفلاین با همان کاتالوگ همین فیلدها را محلی محاسبه می‌کند.

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

تنظیم دوز اطفال موتور اختصاصی دارد و مسیرش پیش از `{slug}` تعریف شده است. داده و مدل ۵۰ دارو در کد بک‌اند است؛ فهرست خام `/calculators/` همان snapshot معمول می‌ماند و اپ ورودی مستقل این ابزار را با `includePediatricDose` زیر Pediatrics اضافه می‌کند. پاسخ با `Cache-Control: private, no-store` است و کلاینت در صورت ناسازگاری `engine_sha256` محاسبه نمی‌کند. [سند ۲۰](20-pediatric-dose.fa.md).

| روش | مسیر | توضیح |
|---|---|---|
| GET | `/calculators/categories/` | کل درخت دسته‌ها (دوزبانه) |
| GET | `/calculators/` | همهٔ ماشین‌حساب‌ها (بدون صفحه‌بندی؛ فقط نام، توضیح و دسته) |
| GET | `/calculators/pediatric-dose/` | `{schema_version, engine_sha256, source, drugs}`؛ مجموعهٔ منبع برای موتور اختصاصی اطفال. نیازمند ورود و ویژگی `calculators`؛ مصرف سهمیه یک بار برای همین ابزار در هر دوره. سن/وزن دریافت نمی‌کند |
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
| GET | `/billing/catalog/` | `{free, plans[], products[], gateways[{kind, name}], sales_enabled}` (فقط پلن‌های `active`)؛ هر کدام با `badge_fa`، `description_fa`، `cta_label_fa`، `extra_lines[]`، `prices[]` (با `compare_at_toman` و `label_fa`) و `features[]` (با `label_fa`، `is_listed` و `period_fa` مثل «در ماه»). `gateways` درگاه‌های روشن به ترتیب نمایش است |
| GET | `/billing/me/` | `{enforced, features[{key, name_fa, limit, period, used}], entitlements[{id, plan_name_fa, plan_kind, source, starts_at, ends_at, days_left}]}`؛ `source` یکی از `purchase`، `admin` و `trial` (هدیهٔ ثبت‌نام). کارت اشتراک پروفایل اپ از همین ساخته می‌شود |
| POST | `/billing/quote/` | `{price_id, discount_code?}` ← `{amount_toman, discount_toman, payable_toman}`. 400 `PRICE_NOT_AVAILABLE` یا `DISCOUNT_NOT_FOUND` / `DISCOUNT_INACTIVE` / `DISCOUNT_NOT_STARTED` / `DISCOUNT_EXPIRED` / `DISCOUNT_USED_UP` / `DISCOUNT_NOT_FOR_PLAN`. 403 `GUEST_CANNOT_BUY` |
| POST | `/billing/checkout/` | خرید از داخل اپ: `{price_id, discount_code?, gateway?, client: "web" \| "android"}` ← 201 `{order_id, status, payment_url}`. `payment_url` صفحهٔ `/pay/start/<token>/` سایت است، نه خود درگاه (پایین‌تر). سفارش ۱۰۰٪ تخفیف بی‌درنگ `paid` می‌شود و `payment_url` خالی است. 400 `GATEWAY_UNKNOWN`، 503 `SALES_PAUSED` یا `NO_GATEWAY` |
| GET | `/billing/orders/` | ۵۰ سفارش آخر کاربر (`status`، `ref_id`، `error`، ...). اپ بعد از برگشتن از درگاه وضعیت سفارش را از همین می‌خواند |
| GET | `/billing/callback/` · `/billing/callback/{kind}/` — عمومی | بازگشت از درگاه؛ تأیید پرداخت، دادن دسترسی (فقط یک بار) و نمایش صفحهٔ HTML نتیجه |
| GET | `/billing/result/{token}/` — عمومی | صفحهٔ HTML نتیجهٔ پرداخت |

روی سایت همین بازگشت‌ها در `/pay/callback/...` و `/pay/result/...` هم هستند ([12-website.md](12-website.md)).

**خرید از داخل اپ (از ۲۰۲۶-۱۱-۰۲):**
1. اپ با `POST /billing/checkout/` سفارش می‌سازد. `channel` سفارش `android` یا `web` می‌شود.
2. اپ `payment_url` را باز می‌کند: روی اندروید در مرورگر، روی وب‌اپ در همان زبانه. این صفحهٔ `https://pharmenta.ir/pay/start/<token>/` است. توکن امضاشده است، یک ساعت اعتبار دارد و فقط به همان سفارش می‌خورد.
3. همین صفحه پرداخت را روی دامنهٔ سایت شروع می‌کند و با اسکریپت (نه redirect) خریدار را به درگاه می‌برد. دلیلش دو چیز است: آدرس بازگشتی که درگاه‌ها می‌شناسند `https://pharmenta.ir/pay/callback/<kind>/` است، و زیبال دامنه را از Referer بررسی می‌کند (`Referrer-Policy: origin`).
4. درگاه به `/pay/callback/<kind>/` سایت برمی‌گردد. صفحهٔ نتیجه برای سفارش `android` دکمهٔ «بازگشت به اپ فارمنتا» دارد: لینک `intent://payment#Intent;scheme=pharmenta;package=com.pharmenta.learning;...`. اگر اپ نصب نباشد، وب‌اپ باز می‌شود.
5. اپ با برگشتن به جلو (AppState) و هر ۵ ثانیه، تا وقتی سفارش `pending` است، `/billing/orders/` را می‌خواند و نتیجه را نشان می‌دهد.
- **لینک کهنه یا دستکاری‌شده:** `/pay/start/` صفحهٔ خطا با ۴۰۴ نشان می‌دهد.
- **سفارش پرداخت‌شده:** همان لینک به صفحهٔ رسید می‌رود و دوباره پرداخت نمی‌شود.

## مسیرهای غیر API

این‌ها صفحهٔ HTML هستند و در [11-admin-consoles.md](11-admin-consoles.md) و [12-website.md](12-website.md) توضیح داده شده‌اند:

| مسیر | چیست |
|---|---|
| `/admin/` | ادمین Django |
| `/manage/` | مدیریت یکپارچه؛ ورود در `/manage/login/` |
| `/manage/sales/` | کنسول فروش (superuser، `platform_admin`، `billing_admin`؛ عملیات امنیتی فقط مدیر سامانه) |
| `/manage/site/` | پنل محتوای سایت (نقش سایت یا نقش حساب متناظر) |
| `/manage/data/` | مرکز کیفیت داده (staff یا مجوزهای کیفیت داده؛ تأیید و بازگردانی مجوز جدا دارند) |

## تغییر دادن API

1. سریالایزر و ویو را در اپ مربوط تغییر دهید و `@extend_schema` را به‌روز کنید.
2. تست ویو را اضافه یا اصلاح کنید.
3. `frontend/src/api/types.ts` و `endpoints.ts` را هم‌خوان کنید و `npm run typecheck` بزنید.
4. همین فایل را به‌روز کنید.
5. اگر شکل پاسخی ناسازگار عوض شد، `CACHE_BUSTER` در `frontend/src/api/queryClient.ts` را تغییر دهید. اپ‌های نصب‌شدهٔ قدیمی هنوز شکل قبلی را انتظار دارند؛ برای همین فیلد را حذف نکنید و فیلد تازه اضافه کنید.

## پشتیبانی و نقشهٔ فعالیت

فهرست مسیرها، بدنهٔ پیام و رویداد، صفحه‌بندی، اشتراک اعلان و فیلدهای جدید نشست در [قرارداد سند ۱۷](17-sessions-activity-support.fa.md) آمده است. فراخوانی چت در `frontend/src/api/support.ts` و فعالیت در `frontend/src/activity/useActivity.ts` است. Swagger محیط منتشرشده تا انتشار بک‌اند جدید این مسیرها را نشان نمی‌دهد.

اعلان پشتیبانی فعلاً خاموش است: پاسخ `GET /support/summary/` فیلد `push_enabled` دارد؛ در حالت خاموش ثبت اشتراک فعال، خطای `503 SUPPORT_NOTIFICATIONS_DISABLED` می‌دهد. `enabled=false` برای لغو اشتراک همچنان مجاز است. گفت‌وگو و تعداد خوانده‌نشده‌ها فعال می‌مانند. [قرارداد و مراحل فعال‌سازی](18-notifications-setup.fa.md).
