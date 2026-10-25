# ۳. بک‌اند (Django)

کد بک‌اند در `backend/` است: یک پروژهٔ Django با Django REST Framework که هم API اپ را می‌دهد، هم سایت `pharmenta.ir` و پنل‌های مدیریت را.

## پیکربندی (`backend/config/`)

| فایل | کار |
|---|---|
| `settings/base.py` | همهٔ تنظیمات مشترک؛ هر مقدار قابل‌تغییر با `decouple.config()` از متغیر محیطی یا `backend/.env` خوانده می‌شود |
| `settings/local.py` | `DEBUG=True` و درگاه پرداخت پیش‌فرض `fake`. پیش‌فرض `manage.py` |
| `settings/production.py` | پیش‌فرض `wsgi.py`. اجبار فروش روشن، کلید قوی، کش مشترک، HTTPS و کوکی امن، لاگ JSON، فقط پاسخ JSON در DRF، رد درگاه `fake` |
| `security.py` | سه بررسی production: قدرت `SECRET_KEY` (≥۵۰ کاراکتر، ≥۱۲ کاراکتر متمایز، بدون کلمه‌های ضعیف)، کش مشترک (نه `LocMemCache`)، صف واقعی Celery (مگر `CELERY_RUN_TASKS_IN_REQUEST`) |
| `urls.py` | urlconf هاست API: `/api/v1/`، Swagger، `/admin/`، `/ops/`، `/ops/data-quality/` و نام‌های قدیمی بدون نسخه (`/api/...`) |
| `api_urls.py` | مسیرهای `/api/v1/` به تفکیک اپ |
| `urls_site.py` | urlconf هاست‌های سایت (`SITE_HOSTS`): سایت، `/panel/`، بازگشت درگاه `/pay/...`، `/ops/` |
| `celery.py` | اپ Celery با سه صف `default`، `events`، `maintenance` |

### زنجیرهٔ middleware

به همین ترتیب اجرا می‌شوند (`settings/base.py`):

1. `CorsMiddleware` — CORS برای وب‌اپ (`CORS_ALLOWED_ORIGINS`).
2. `SecurityMiddleware`.
3. `website.middleware.SiteHostMiddleware` — هاست‌های `SITE_HOSTS` را به urlconf سایت می‌فرستد، `www.` را به نشانی بدون www هدایت می‌کند و ریدایرکت‌های تعریف‌شده در پنل را اعمال می‌کند.
4. `core.logging.RequestIdMiddleware` — به هر درخواست شناسه می‌دهد (`X-Request-ID` ورودی یا یک UUID تازه) و آن را در لاگ‌ها و هدر پاسخ می‌گذارد.
5. `WhiteNoiseMiddleware` — فایل‌های استاتیک.
6. `GZipMiddleware` — فشرده‌سازی پاسخ‌های JSON (پروکسی رانفلر فشرده نمی‌کند).
7. نشست، Common، CSRF، احراز هویت، پیام‌ها.
8. `website.middleware.SiteMaintenanceMiddleware` — صفحهٔ «در حال تعمیر» سایت وقتی در پنل روشن است (کارکنان رد می‌شوند).
9. `XFrameOptionsMiddleware`.

## اپ‌ها (`backend/apps/`)

| اپ | مسئولیت | مدل‌های اصلی | نکته |
|---|---|---|---|
| `core` | سلامت (`health/live/ready`)، شناسهٔ درخواست و لاگ JSON، قالب خطا، صفحه‌بندی، throttling توزیع‌شده، ابزار SQLite قابل‌حمل (`reference_db.py`)، روتر نگهداری آزمون و فلش‌کارت | — | دستورهای `backup_database` و `export_reference_db` |
| `accounts` | کاربر، نشست با توکن مات، کد پیامکی، رمز، نقش‌ها، رویدادهای امنیتی، پروفایل یادگیرنده | `UserSession`، `SessionRefreshToken`، `OneTimeCode`، `Role`، `RoleAssignment`، `SecurityAuditEvent`، `LearnerProfile` | بررسی‌های deploy: `accounts.W001` و `W002` (پیکربندی sms.ir) |
| `drugs` | ماده‌های دارویی (کلید RXCUI)، بخش‌های بالینی با خلاصهٔ fa/en، کدها و گروه‌های ATC | `Ingredient`، `IngredientProfileSection`، `AtcCode`، `AtcCategory` | دادهٔ ATC سطح ۱ و ۲ در `drugs/atc_reference.py` |
| `lessons` | درخت درسی: موضوع‌های بالینی (`lessons/data/study_topics.py`) ← فصل (زیرگروه ATC سطح ۲) ← دارو؛ جست‌وجوی دارو؛ پیشرفت خواندن | `ChapterProgress`، `ReadDrug` | یک فصل می‌تواند زیر چند موضوع بیاید |
| `progress` | XP، استریک، آمار روزانه، اشتباهات، برنامهٔ مطالعه و کارهای روزانه | `LearnerProgress`، `DailyStudy`، `Mistake`، `StudyPlan`، `StudyPlanItem` | اپ‌های آزمون و فلش‌کارت از `progress.services` شمارنده‌ها را بالا می‌برند. `progress.planning` برنامه را می‌سازد: از پاسخ‌های آنبوردینگ (`plan_from_onboarding`)، با سرعتی که سطح کاربر تعیین می‌کند، و با جابه‌جا کردن کارهای روز جامانده (`rollover`) ([05-api.md](05-api.md#پیشرفت-و-برنامه--me)) |
| `flashcards` | کارت لایتنر هر (کاربر، دارو)، ۵ جعبه با فاصلهٔ ۰/۳/۷/۱۶/۳۵ روز، دسته‌های موضوعی | `LeitnerCard`، `FlashcardFact`، `TopicProgress` | با `FLASHCARDS_API_ENABLED` روشن می‌شود |
| `quiz` | بانک سؤال، جلسهٔ آزمون، نمره‌دهی سمت سرور، ثبت اشتباه | `BankQuestion`، `QuizSession`، `QuizQuestion`، `QuizAnswer` | با `QUIZ_API_ENABLED` روشن می‌شود؛ محتوا از پایپلاین `study_content` |
| `uptodate` | جست‌وجو و خواندن مقاله‌ها و تصویرهای UpToDate | — | از SQLite (`UPTODATE_DB_DIR`) یا MySQL (`UPTODATE_MYSQL_URL`)؛ بدون منبع → 503 |
| `lexicomp` | جست‌وجوی دارو و بررسی تداخل | — | از `interact.db` در `LEXICOMP_DB_DIR`؛ بدون منبع → 503 |
| `offline` | ساخت بستهٔ رمزنگاری‌شدهٔ آفلاین، لینک دانلود امضاشده، مجوز ۳۰ روزه | — | جزئیات در «بستهٔ آفلاین» پایین‌تر |
| `calculators` | ماشین‌حساب‌های بالینی دوزبانه (سؤال، فرمول و نتیجه به‌صورت JSON) | `Calculator`، `CalculatorCategory`، `CalculatorTag` | محاسبه سمت اپ انجام می‌شود (`frontend/src/utils/calculatorEngine.ts`) |
| `medscape` | مقاله‌های بیماری و گایدلاین با تصویرهای ذخیره‌شده با هش محتوا | `Article`، `ArticleImage` | — |
| `billing` | ویژگی، پلن و محصول، قیمت، کد تخفیف، سفارش، حق دسترسی، سهمیه، درگاه پرداخت، مهمان، کنسول `/ops/` | `Feature`، `Plan`، `PlanFeature`، `PlanPrice`، `DiscountCode`، `Order`، `Entitlement`، `UsageRecord`، `PaymentGateway`، `BillingSettings`، `GuestAccount`، `AdminAction` | جزئیات در «صورتحساب» پایین‌تر |
| `website` | سایت و بلاگ، پنل محتوا، آمار بازدید، ریدایرکت، حالت تعمیر، و مسیر API نسخهٔ اپ (`/app/release/`) | ۲۰ مدل، از جمله `SiteSettings`، `Post`، `Page`، `Media`، `StaffRole`، `DailyStat` | [12-website.md](12-website.md) |
| `data_quality_center` | ویرایش خلاصه‌های بالینی با بازبینی superuser و سابقهٔ تغییرناپذیر | `SectionEditRequest`، `SectionEdit`، `ReviewEvent` | [11-admin-consoles.md](11-admin-consoles.md) |

ساختار معمول هر اپ: `models.py`، `serializers.py`، `views.py`، `urls.py`، `services.py` (منطق کسب‌وکار)، `tests.py` یا `tests/`، `management/commands/`.

## احراز هویت و حساب

### نشست و توکن

- احراز هویت DRF با `accounts.authentication.SessionTokenAuthentication` است: هدر `Authorization: Bearer <access_token>`.
- توکن‌ها مات‌اند (JWT نیستند) و با پیشوند `phx_access_` و `phx_refresh_` ساخته می‌شوند. هر ورود یک `UserSession` می‌سازد.
- عمر توکن دسترسی `AUTH_ACCESS_TOKEN_TTL_MINUTES` (۱۵ دقیقه) و توکن تمدید `AUTH_REFRESH_TOKEN_TTL_DAYS` (۳۰ روز) است. هر تمدید، توکن تمدید را عوض می‌کند. هر کاربر حداکثر `AUTH_MAX_ACTIVE_SESSIONS` (۱۰) نشست فعال دارد.
- ابطال نشست فوری است (`logout`، `logout-all`، کنسول فروش).
- برای کارهای حساس، «تأیید دوباره» (`step-up`) لازم است که `AUTH_STEP_UP_TTL_MINUTES` (۱۰ دقیقه) معتبر می‌ماند.

### ثبت‌نام و ورود

1. **ثبت‌نام:** شمارهٔ موبایل ← کد پیامکی (`/auth/otp/request/` با `purpose=signup`) ← تأیید کد (`/auth/otp/verify/`) که حساب را می‌سازد و وارد می‌کند ← انتخاب رمز (`/auth/password/set/`). تا رمز انتخاب نشود، `has_password` کاربر `false` است و اپ صفحهٔ انتخاب رمز را نشان می‌دهد.
2. **ورود:** شماره (با هر نوشتاری، فارسی یا انگلیسی)، ایمیل یا نام کاربری + رمز (`/auth/login/`). پیامکی فرستاده نمی‌شود.
3. **فراموشی رمز:** کد پیامکی با `purpose=reset` ← تأیید ← رمز تازه. همهٔ نشست‌های دیگر بسته می‌شوند.
4. **ثبت‌نام با ایمیل:** خاموش است (`AUTH_EMAIL_REGISTRATION_ENABLED=False`). حساب‌های قدیمی ایمیلی هنوز وارد می‌شوند و بازیابی ایمیلی دارند.

قواعد کد پیامکی (`accounts/otp.py`):
- **ذخیره:** کد به‌صورت هش ذخیره می‌شود.
- **طول و انقضا:** کد `OTP_CODE_LENGTH` رقمی (۵) است و بعد از `OTP_TTL_SECONDS` (۱۲۰ ثانیه) منقضی می‌شود.
- **تلاش اشتباه:** `OTP_MAX_ATTEMPTS` (۵) بار تلاش اشتباه مجاز است.
- **فاصلهٔ ارسال:** هر شماره هر `OTP_RESEND_SECONDS` (۶۰ ثانیه) یک کد می‌گیرد.
- **سقف ۱۰ دقیقه:** هر شماره در هر `OTP_WINDOW_SECONDS` (۶۰۰ ثانیه) حداکثر `OTP_MAX_PER_PHONE_PER_WINDOW` (۳) کد می‌گیرد. پاسخ چهارمین درخواست `429 OTP_WINDOW_LIMIT` است و `retry_after` را دارد.
- **سقف هر آدرس:** از یک IP در همان بازه حداکثر `OTP_MAX_PER_IP_PER_WINDOW` (۱۰) کد خواسته می‌شود. پاسخ اضافه `429 OTP_IP_LIMIT` است. این سقف بیشتر از سقف هر شماره است، چون اپراتورها چندین گوشی را پشت یک IP می‌گذارند (CGNAT). کارش فقط این است که یک منبع نتواند پشت‌سرهم برای شماره‌های مختلف کد بخواهد.
- **سقف روزانه:** هر شماره حداکثر `OTP_MAX_PER_PHONE_PER_DAY` (۸) کد در روز می‌گیرد.
- **خطای ارسال:** اگر ارسال sms.ir شکست بخورد، پاسخ `503 SMS_SEND_FAILED` است. علت در لاگ ثبت می‌شود و آن ارسال در سقف‌ها حساب نمی‌شود.

ارسال پیامک (`accounts/sms.py`):
- **پشتیبان `smsir`:** از API «verify» استفاده می‌کند؛ قالب تأییدشده با شناسهٔ `SMSIR_OTP_TEMPLATE_ID` و پارامتر `SMSIR_OTP_PARAMETER` (`CODE`).
- **پشتیبان `console`:** کد را فقط در لاگ می‌نویسد. بدون `SMSIR_API_KEY` همین پشتیبان انتخاب می‌شود.

> برای پر شدن خودکار کد در Chrome اندروید (WebOTP)، آخرین خط پیامک باید دقیقاً `@app.pharmenta.ir #12345` باشد. در قالب sms.ir عبارت `#CODE#` با هر دو `#` جایگزین می‌شود، پس آخرین خط قالب باید `@app.pharmenta.ir ##CODE#` نوشته شود. کد اپ این خط را در `frontend/src/screens/AuthScreen.tsx` می‌خواند.

### رمز عبور

- **تنها قاعده:** طول حداقل `AUTH_PASSWORD_MIN_LENGTH` (۶) کاراکتر است. هر رمزی با این طول پذیرفته می‌شود، حتی فقط‌عددی یا رایج. این تصمیم عمدی است: امنیت حساب را محدودیت‌های ورود و پیامک تأمین می‌کنند، نه سخت‌گیری روی رمز.

### نقش‌ها و رویدادهای امنیتی

- **نقش‌ها** (`accounts.Role`): `learner`، `verified_professional`، `content_editor`، `medical_reviewer`، `data_quality_reviewer`، `data_quality_approver`، `support_agent`، `billing_admin`، `platform_admin`. مدیریتشان با `/auth/roles/` و `/auth/role-assignments/` است.
- **رویدادهای امنیتی** (`SecurityAuditEvent`): ورود موفق و ناموفق، تمدید و ابطال نشست، step-up، بازیابی و انتخاب رمز، ارسال، تأیید و شکست کد پیامکی، دادن و گرفتن نقش، و ردِ دسترسی. فهرستشان از `/auth/security-events/` خوانده می‌شود.
- **دسترسی کارکنان:** کاربر `is_staff` هیچ‌وقت با اشتراک قفل نمی‌شود. `is_superuser` به همهٔ کنسول‌ها دسترسی دارد.

## صورتحساب و دسترسی (`apps.billing`)

- **ویژگی (Feature):** هر بخش فروشی یک کلید دارد. کلیدهای داخلی در `billing/catalog.py`: `lessons`، `uptodate`، `lexicomp`، `medscape`، `calculators`، `flashcards`، `quiz`، `stats`. مدیر در کنسول می‌تواند ویژگی «محتوایی» (قفل یک دستهٔ مطالعه یا پیشوند ATC) یا «سفارشی» بسازد. ویژگی سفارشی فقط وقتی اعمال می‌شود که کد آن کلید را بررسی کند و کلید در `WIRED_CUSTOM_KEYS` ثبت شود.
- **پلن و محصول:** مجموعه‌ای از ویژگی‌ها، هر کدام با سقف روزانه یا ماهانه (تقویم تهران، ماه شمسی) یا بی‌سقف، و یک یا چند قیمت با مدت (`duration_days`؛ خالی یعنی دائمی). پلنی که `is_free` دارد را همه دارند.
- **حق دسترسی (Entitlement):** با خرید یا با دادن دستی در کنسول ساخته می‌شود. نسخه‌ای از ویژگی‌های پلن در لحظهٔ خرید را نگه می‌دارد، پس ویرایش پلن فقط روی خریدهای بعدی اثر دارد. اگر دو منبع یک ویژگی را بدهند، دست‌ودل‌بازترش حساب می‌شود.
- **اعمال (`billing/enforcement.py`):** ویوهای محتوا `require_feature(request, key, item=..., consume=...)` را صدا می‌زنند.
  - اگر پلن کاربر آن ویژگی را نداشته باشد، پاسخ `402 PREMIUM_REQUIRED` است.
  - اگر سهمیه تمام شده باشد، پاسخ `402 QUOTA_EXCEEDED` است.
  - جست‌وجو و فهرست‌ها باز می‌مانند؛ فقط باز کردن هر آیتم یک بار در هر دوره شمرده می‌شود.
- **روشن و خاموش بودن اعمال:** مقدار کنسول («درگاه پرداخت») بر متغیر محیطی مقدم است. پیش‌فرض `BILLING_ENFORCEMENT_ENABLED` در `production.py` روشن (`True`) و در `base.py` خاموش است.
  - تنظیمات کنسول در هر پروسه ۳۰ ثانیه کش می‌شوند.
  - ذخیرهٔ تنظیمات در کنسول، کش همان پروسه را فوراً پاک می‌کند. بقیهٔ workerها حداکثر بعد از ۳۰ ثانیه مقدار تازه را می‌خوانند.
- **درگاه‌ها (`billing/gateways.py`):**
  - درگاه‌های پشتیبانی‌شده: `zarinpal`، `sep` (سامان)، `zibal` و `fake` (فقط توسعه).
  - هر درگاه در کنسول (`/ops/gateway/`) تنظیم می‌شود. اگر کنسول درگاهی نداشته باشد، درگاهی که `BILLING_GATEWAY` نام می‌برد استفاده می‌شود.
  - بازگشت از درگاه به `/pay/callback/<kind>/` روی سایت (یا `/api/v1/billing/callback/`) است. همان‌جا پرداخت تأیید و دسترسی فقط یک بار داده می‌شود.
- **مهمان (`billing/guest.py`):** با کلید «تنظیمات دسترسی» کنسول روشن می‌شود.
  - مهمان حساب یک‌بارمصرف می‌گیرد که فقط پلن رایگان دارد و نمی‌تواند خرید کند.
  - با خاموش کردن کلید، همهٔ مهمان‌ها غیرفعال می‌شوند. `delete_guest_accounts` آن‌ها را پاک می‌کند.

## UpToDate و Lexicomp

- **UpToDate** (`apps/uptodate/services.py`):
  - **منبع:** اگر `UPTODATE_MYSQL_URL` تنظیم باشد، از MySQL می‌خواند؛ وگرنه از فایل‌های SQLite در `UPTODATE_DB_DIR` (`fts.db`، `content.db`، `toc.db`، `images.db`، `info.json`). در production منبع MySQL است.
  - **جست‌وجو:** فقط در عنوان مقاله است؛ پیشوند کلمه‌ها با AND ترکیب می‌شود. MySQL برای این جست‌وجو به ایندکس FULLTEXT روی `title` نیاز دارد که `ensure_uptodate_search_index` آن را در هر شروع کانتینر بررسی می‌کند.
- **Lexicomp** (`apps/lexicomp/`):
  - **منبع:** `interact.db` و `info.json` در `LEXICOMP_DB_DIR`. در production این پوشه روی دیسک سرویس بک‌اند است.
  - **بررسی تداخل:** هر بررسی یک بار از سهمیهٔ `lexicomp` کم می‌کند.

## بستهٔ آفلاین (`apps.offline`)

- **قالب (`pack.py`):**
  - هر رکورد جدا با AES-256-GCM رمز می‌شود. متن و JSON قبل از رمز با zlib فشرده می‌شوند.
  - کلید هر نسخه از `OFFLINE_PACKAGE_SECRET` و شناسهٔ نسخه (`build`) مشتق می‌شود: `HMAC-SHA256(secret, "pharmenta-offline-v1:" + build)`.
  - هر بسته شامل `part-NNN.bin`ها، `manifest.json` و `latest.json` است.
- **ساخت:** روی لپ‌تاپ با `build_offline_package` (`builders.py`). سرور هیچ‌وقت بسته نمی‌سازد.
- **نگهداری (`storage.py`):**
  - بسته‌ها در باکت خصوصی Object Storage نگه داشته می‌شوند. `latest.json` در سرور ۵ دقیقه کش می‌شود.
  - اپ با لینک امضاشدهٔ ۲۴ ساعته (`OFFLINE_URL_TTL_SECONDS`) مستقیم از باکت دانلود می‌کند.
- **مجوز (`services.py`):**
  - **چه کسی:** فقط staff یا کاربری با پلن پولی فعال که ویژگی مربوط را دارد. این شرط حتی وقتی اعمال فروش خاموش است برقرار است. مهمان و پلن رایگان هرگز مجوز نمی‌گیرند.
  - **چه چیزی:** مجوز کلید بسته را با اعتبار `OFFLINE_LICENSE_DAYS` (۳۰ روز) می‌دهد. در وب، کلید با کلید عمومی RSA مرورگر رمز (wrap) می‌شود.
  - **قفل شدن:** اگر اشتراک تمام شود و اپ آنلاین باشد، بسته فوراً قفل می‌شود.
- **محدودیت امنیتی:** کاربر مجاز می‌تواند با صدا زدن مستقیم API کلید را بگیرد. رمزنگاری فقط کپی کردن فایل‌ها را بی‌فایده می‌کند.

## قواعد مشترک API

- **قالب خطا** (`core/exceptions.py`): همهٔ خطاها `{"code": "...", "message": "...", "details": {...}}` هستند. برای خطای سفارشی `PlatformAPIError(message, code=..., status_code=..., details=...)` را raise کنید.
- **صفحه‌بندی** (`core/pagination.py`): پیش‌فرض ۲۰ آیتم.
- **Throttling** (`core/throttling.py`):
  - شمارنده‌ها در کش `throttle` نگه داشته می‌شوند تا بین workerها مشترک باشند. نرخ‌ها در `DRF_*_THROTTLE_RATE` تنظیم می‌شوند.
  - برای scopeهای `THROTTLE_FAIL_CLOSED_SCOPES` (ورود، ثبت‌نام، بازیابی، کد پیامکی، انتخاب رمز)، اگر کش در دسترس نباشد، درخواست رد می‌شود.
- **مستندات زنده:** drf-spectacular در `/api/v1/schema/` و `/api/v1/docs/`. برای ورودی و خروجی هر ویو از `@extend_schema` استفاده کنید.
- **پرچم‌های قابلیت:** `QUIZ_API_ENABLED` و `FLASHCARDS_API_ENABLED`. اگر خاموش باشند، روتر نگهداری به همهٔ مسیرهای آن بخش `503 FEATURE_NOT_AVAILABLE` می‌دهد. کنسول‌ها هم `DATA_QUALITY_CENTER_ENABLED` و `BILLING_CONSOLE_ENABLED` را دارند.

## کار پس‌زمینه

- تنها کار Celery ارسال ایمیل بازیابی رمز است (`accounts/tasks.py`، صف `default`).
- روی رانفلر Redis نیست. با `CELERY_RUN_TASKS_IN_REQUEST=True` کار داخل همان درخواست اجرا می‌شود و با `ASYNC_EMAIL_ENABLED=False` ایمیل هم مستقیم فرستاده می‌شود.
- در Docker محلی، worker جدا با Redis اجرا می‌شود.

## قواعد کدنویسی بک‌اند

- **منطق کسب‌وکار:** در `services.py` بنویسید، نه در ویو یا سریالایزر. ویو فقط ورودی را اعتبارسنجی، سرویس را صدا و پاسخ را برمی‌گرداند.
- **محتوای فروشی:** هر ویویی که محتوای فروشی سرو می‌کند، پیش از پاسخ `require_feature` را صدا بزند.
- **تست:** کنار اپ در `tests.py` یا `tests/` و با اسم `test_...`. سرویس، سریالایزر و ویو را پوشش دهد.
- **مایگریشن:** بعد از تغییر مدل `makemigrations` بزنید و فایل مایگریشن را کامیت کنید. CI با `makemigrations --check` جلوی فراموشی را می‌گیرد.
- **متن کاربر:** پیام خطایی که کاربر می‌بیند فارسی باشد. `code` خطا ثابت، انگلیسی و با حروف بزرگ باشد (`PREMIUM_REQUIRED`).
- **متغیر محیطی جدید:**
  1. در `settings/base.py` با `config(...)` و یک پیش‌فرض امن تعریف شود.
  2. در `backend/.env.example` اضافه شود.
  3. در [06-configuration.md](06-configuration.md) ثبت شود.
- **راز:** هیچ رازی در کد یا لاگ نوشته نشود. `sms.py` کد پیامکی را لاگ نمی‌کند و شماره را با `mask()` کوتاه می‌کند.

### افزودن یک قابلیت فروشی تازه

1. ویژگی را در `BUILTIN_FEATURES` (`billing/catalog.py`) تعریف کنید، یا در کنسول بسازید و کلیدش را در `WIRED_CUSTOM_KEYS` بگذارید.
2. در ویوی محتوا `require_feature(request, "<key>", item=<شناسهٔ آیتم>, consume=True)` را صدا بزنید.
3. در کنسول ویژگی را به پلن‌ها اضافه کنید.
4. در اپ، خطای `402` را با پیام «پلن شما شامل این بخش نیست» نشان دهید (الگوی صفحه‌های موجود).
