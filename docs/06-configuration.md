# ۶. پیکربندی و متغیرهای محیطی

همهٔ تنظیمات قابل‌تغییر بک‌اند از متغیر محیطی خوانده می‌شوند (`decouple.config()` در `backend/config/settings/`). روی لپ‌تاپ مقدارها در `backend/.env` و روی سرور در بخش env سرویس بک‌اند در رانفلر گذاشته می‌شوند. الگوی کامل `.env` در `backend/.env.example` است.

راهنمای ستون‌ها:
- **پیش‌فرض:** مقداری که کد بدون متغیر برمی‌دارد.
- **رانفلر:** مقداری که سرویس بک‌اند production باید داشته باشد. «—» یعنی پیش‌فرض درست است و لازم نیست تنظیم شود. «راز» یعنی مقدار محرمانه است و فقط در env رانفلر و `.env` لپ‌تاپ نوشته می‌شود.

> بعد از تغییر هر متغیر در رانفلر، سرویس بک‌اند را ری‌استارت کنید. متغیرها فقط هنگام شروع پروسه خوانده می‌شوند.

## پایهٔ Django

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `DJANGO_SETTINGS_MODULE` | `manage.py`: `config.settings.local`؛ `wsgi.py`: `config.settings.production` | `config.settings.production` (در `Dockerfile` گذاشته شده) | ماژول تنظیمات. فقط از محیط شِل خوانده می‌شود، نه از `.env` |
| `SECRET_KEY` | `dev-secret` | **راز**؛ ≥۵۰ کاراکتر، ≥۱۲ کاراکتر متمایز | امضای نشست‌ها، توکن‌ها و هش IP آمار سایت. **عوضش نکنید**: آمار بازدیدکنندهٔ یکتا از نو شروع می‌شود |
| `DEBUG` | `False` | — (production همیشه `False`) | |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | `api.pharmenta.ir,localhost,127.0.0.1` به‌علاوهٔ دامنهٔ پیش‌فرض رانفلر | هاست‌های مجاز. هاست‌های `SITE_HOSTS` و `www.` آن‌ها خودکار اضافه می‌شوند |
| `ENVIRONMENT` | `local` | `production` | در پاسخ `/health/` و پیشوند کلید کش |
| `APP_VERSION` | `0.1.0` | اختیاری | در پاسخ `/health/` |
| `RELEASE_SHA` | `local` | اختیاری (شناسهٔ کامیت) | در پاسخ `/health/` |
| `LOG_LEVEL` | `INFO` | — | سطح لاگ |
| `LOG_FORMAT` | `plain` | — (production همیشه `json`) | `plain` یا `json` |

## دیتابیس، کش و آمادگی

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `DATABASE_URL` | `postgresql://postgres:postgres@127.0.0.1:5432/pharmexa` | **راز**؛ رشتهٔ اتصال **داخلی** Postgres رانفلر | دیتابیس اصلی |
| `REDIS_URL` | خالی | خالی (رانفلر Redis ندارد) | اگر تنظیم شود، کش، throttle و صف Celery از آن استفاده می‌کنند |
| `CACHE_URL` | `REDIS_URL` | خالی | |
| `CACHE_BACKEND` | Redis اگر `CACHE_URL` باشد، وگرنه `LocMemCache` | `django.core.cache.backends.db.DatabaseCache` | production کش داخل حافظهٔ پروسه را رد می‌کند |
| `CACHE_LOCATION` | `pharmexa-default-cache` | `pharmexa_cache` | نام جدول کش (با `createcachetable` ساخته می‌شود) |
| `CACHE_KEY_PREFIX` | `pharmexa:<ENVIRONMENT>` | — | |
| `CACHE_VERSION` | `1` | — | |
| `CACHE_DEFAULT_TIMEOUT` | `300` | — | ثانیه |
| `THROTTLE_CACHE_URL` | `CACHE_URL` | خالی | کش جدای شمارنده‌های throttle (Redis) |
| `READINESS_REQUIRE_CACHE` | base: اگر `CACHE_URL` باشد؛ production: `True` | — | `/ready/` بدون کش سالم 503 بدهد |
| `READINESS_REQUIRE_BROKER` | base: `False`؛ production: برعکسِ `CELERY_RUN_TASKS_IN_REQUEST` | — | `/ready/` بدون صف سالم 503 بدهد |

## کار پس‌زمینه (Celery)

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `CELERY_RUN_TASKS_IN_REQUEST` | `False` (فقط production می‌خواند) | `True` | کار را داخل همان درخواست اجرا می‌کند؛ بدون صف و worker |
| `ASYNC_EMAIL_ENABLED` | `True` | `False` | ایمیل بازیابی رمز از صف فرستاده شود یا مستقیم |
| `CELERY_BROKER_URL` | `REDIS_URL` یا `memory://` | خالی | |
| `CELERY_RESULT_BACKEND` | خالی | — | |
| `CELERY_TASK_ALWAYS_EAGER` | `True` اگر صف نباشد | تنظیم نکنید | `CELERY_RUN_TASKS_IN_REQUEST` خودش آن را روشن می‌کند |
| `CELERY_TASK_EAGER_PROPAGATES` | `False` | — | |
| `CELERY_WORKER_PREFETCH_MULTIPLIER` / `CELERY_WORKER_MAX_TASKS_PER_CHILD` | `1` / `500` | — | فقط با worker |
| `CELERY_TASK_SOFT_TIME_LIMIT` / `CELERY_TASK_TIME_LIMIT` | `120` / `180` | — | ثانیه |
| `CELERY_BROKER_VISIBILITY_TIMEOUT` | ۴ برابر `CELERY_TASK_TIME_LIMIT` | — | |
| `CELERY_TASK_MAX_RETRIES` / `CELERY_TASK_RETRY_BACKOFF_SECONDS` / `CELERY_TASK_RETRY_BACKOFF_MAX_SECONDS` | `5` / `5` / `600` | — | |

## HTTPS، CORS و CSRF

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `SECURE_SSL_REDIRECT` | production: `True`؛ ولی `Dockerfile` آن را `False` می‌گذارد | فعلاً — (`False` از ایمیج) | هدایت http به https. اگر روشن شد، مطمئن شوید health check رانفلر روی https است |
| `SECURE_HSTS_SECONDS` | production: `31536000`؛ `Dockerfile`: `0` | — | |
| `SECURE_HSTS_INCLUDE_SUBDOMAINS` / `SECURE_HSTS_PRELOAD` | `True` / `True` | — | فقط وقتی `SECURE_HSTS_SECONDS` بزرگ‌تر از صفر است اثر دارند |
| `CORS_ALLOWED_ORIGINS` | خالی | `https://app.pharmenta.ir` | مبدأهای مجاز وب‌اپ؛ بدون اسلش آخر |
| `CORS_ALLOW_CREDENTIALS` | `False` | — | |
| `CSRF_TRUSTED_ORIGINS` | خالی | `https://app.pharmenta.ir,https://api.pharmenta.ir` | `https://` هاست‌های سایت خودکار اضافه می‌شود |

## حساب و احراز هویت

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `AUTH_ACCESS_TOKEN_TTL_MINUTES` | `15` | — | عمر توکن دسترسی |
| `AUTH_REFRESH_TOKEN_TTL_DAYS` | `30` | — | عمر توکن تمدید |
| `AUTH_MAX_ACTIVE_SESSIONS` | `10` | — | حداکثر نشست هم‌زمان هر کاربر |
| `AUTH_STEP_UP_TTL_MINUTES` | `10` | — | اعتبار تأیید دوباره (و انتخاب رمز بعد از کد پیامکی) |
| `AUTH_PASSWORD_MIN_LENGTH` | `6` | — | |
| `AUTH_EMAIL_REGISTRATION_ENABLED` | `False` | — | ثبت‌نام قدیمی با ایمیل |
| `PASSWORD_RESET_TIMEOUT` | `86400` | — | اعتبار لینک بازیابی ایمیلی (ثانیه) |
| `PASSWORD_RESET_FRONTEND_URL` | `http://localhost:8081` | `https://app.pharmenta.ir/reset-password` | لینک ایمیل بازیابی |
| `DJANGO_SUPERUSER_USERNAME` / `_EMAIL` / `_PASSWORD` | خالی | معمولاً خالی؛ رمز **راز** است | فقط `bootstrap_superuser` (در `release.sh`) می‌خواند. روی رانفلر مدیر با `createsuperuser` از کنسول ساخته می‌شود |

## پیامک و کد تأیید

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `SMSIR_API_KEY` | خالی | **راز** | کلید API پنل sms.ir |
| `SMSIR_OTP_TEMPLATE_ID` | `0` | شناسهٔ قالب تأییدشده | |
| `SMSIR_OTP_PARAMETER` | `CODE` | — | نام پارامتر کد در قالب |
| `SMSIR_VERIFY_URL` | `https://api.sms.ir/v1/send/verify` | — | |
| `SMSIR_TIMEOUT_SECONDS` | `10` | — | |
| `SMS_BACKEND` | `smsir` اگر کلید باشد، وگرنه `console` | — | `console` فقط در لاگ می‌نویسد |
| `OTP_CODE_LENGTH` | `5` | — | |
| `OTP_TTL_SECONDS` | `120` | — | |
| `OTP_MAX_ATTEMPTS` | `5` | — | |
| `OTP_RESEND_SECONDS` | `60` | — | |
| `OTP_MAX_PER_PHONE_PER_DAY` | `8` | — | |

`manage.py check --deploy` اگر پیامک تنظیم نباشد هشدار `accounts.W001` و اگر قالب نباشد `accounts.W002` می‌دهد. اگر کلید sms.ir در پنل به IP محدود شده باشد، IP خروجی سرور رانفلر باید در پنل sms.ir ثبت شود.

## ایمیل

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `EMAIL_BACKEND` | کنسول | در صورت نیاز `django.core.mail.backends.smtp.EmailBackend` | فقط برای بازیابی رمز حساب‌های قدیمی ایمیلی |
| `EMAIL_HOST` / `EMAIL_PORT` / `EMAIL_USE_TLS` | خالی / `587` / `True` | | |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | خالی | رمز **راز** است | |
| `DEFAULT_FROM_EMAIL` | `no-reply@pharmexa.local` | | |

## محدودیت نرخ (throttling)

| متغیر | پیش‌فرض | کار |
|---|---|---|
| `DRF_ANON_THROTTLE_RATE` | `1000/hour` | درخواست بدون ورود، هر IP |
| `DRF_BURST_THROTTLE_RATE` / `DRF_SUSTAINED_THROTTLE_RATE` | `120/min` / `5000/day` | |
| `DRF_AUTH_LOGIN_THROTTLE_RATE` | `5/min` | ورود |
| `DRF_AUTH_REGISTER_THROTTLE_RATE` | `5/hour` | ثبت‌نام ایمیلی |
| `DRF_AUTH_PASSWORD_RESET_REQUEST_THROTTLE_RATE` / `..._CONFIRM_...` | `3/hour` / `5/hour` | بازیابی ایمیلی |
| `DRF_AUTH_OTP_REQUEST_THROTTLE_RATE` | `20/hour` | درخواست کد، هر IP (سقف هر شماره جداست) |
| `DRF_AUTH_OTP_VERIFY_THROTTLE_RATE` | `30/hour` | تأیید کد |
| `DRF_AUTH_PASSWORD_SET_THROTTLE_RATE` | `10/hour` | انتخاب رمز |
| `DRF_GUEST_SESSION_THROTTLE_RATE` | `20/hour` | ساخت حساب مهمان |
| `THROTTLE_FAIL_CLOSED_SCOPES` | ورود، ثبت‌نام، بازیابی، کد پیامکی، انتخاب رمز | این scopeها اگر کش در دسترس نباشد درخواست را رد می‌کنند |

## پرچم‌های قابلیت

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `QUIZ_API_ENABLED` | `False` | `True` | بدون آن، `/quiz/*` پاسخ 503 می‌دهد |
| `FLASHCARDS_API_ENABLED` | `False` | `True` | بدون آن، `/flashcards/*` پاسخ 503 می‌دهد |
| `DATA_QUALITY_CENTER_ENABLED` | `True` | — | `/ops/data-quality/` |
| `DATA_QUALITY_MIN_REASON_LENGTH` | `12` | — | حداقل طول دلیل هر درخواست ویرایش |
| `BILLING_CONSOLE_ENABLED` | `True` | — | `/ops/` |

## صورتحساب و پرداخت

مقدارهایی که در کنسول فروش (`/ops/gateway/`) تنظیم شوند بر این متغیرها مقدم‌اند.

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `BILLING_ENFORCEMENT_ENABLED` | base: `False`؛ production: `True` | — | اعمال پلن‌ها و سهمیه‌ها |
| `BILLING_GATEWAY` | base: `zarinpal`؛ local: `fake` | — | درگاه پیش‌فرض وقتی کنسول درگاهی ندارد. `fake` در production رد می‌شود |
| `BILLING_GATEWAY_TIMEOUT_SECONDS` | `15` | — | |
| `ZARINPAL_MERCHANT_ID` / `ZARINPAL_SANDBOX` | خالی / `False` | در کنسول یا اینجا؛ شناسه **راز** است | |
| `ZIBAL_MERCHANT` (یا `ZIBAL_MERCHANT_ID`) / `ZIBAL_SANDBOX` | خالی / `False` | در کنسول یا اینجا | |
| `BILLING_RETURN_URL` | `http://localhost:8081` | `https://app.pharmenta.ir` | دکمهٔ «برگشت به اپ» در صفحهٔ نتیجهٔ پرداخت |

درگاه سپ فقط از کنسول تنظیم می‌شود.

## دادهٔ مرجع (UpToDate و Lexicomp)

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `UPTODATE_MYSQL_URL` | خالی | **راز**؛ رشتهٔ اتصال MySQL نسخهٔ UpToDate | اگر باشد، UpToDate از MySQL خوانده می‌شود |
| `UPTODATE_DB_DIR` | `/home/amir/Documents/UpToDate` | — (با MySQL استفاده نمی‌شود) | پوشهٔ SQLite |
| `LEXICOMP_DB_DIR` | `/home/amir/Documents/Lexicomp_Drug_Interactions` | مسیر پوشه روی دیسک سرویس بک‌اند | `interact.db` و `info.json` |

## بستهٔ آفلاین

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `OFFLINE_PACKAGE_SECRET` | خالی | **راز**؛ دقیقاً همان مقدار `.env` لپ‌تاپ | کلید اصلی همهٔ بسته‌ها. بعد از انتشار اولین بسته **هرگز** عوض نشود |
| `OFFLINE_S3_ENDPOINT_URL` | خالی | `https://s3-pish.runflare.cloud` | فقط نشانی سرور، بدون باکت و مسیر |
| `OFFLINE_S3_BUCKET` | خالی | `pharmenta-dl` | |
| `OFFLINE_S3_ACCESS_KEY_ID` / `OFFLINE_S3_SECRET_ACCESS_KEY` | خالی | **راز** | کلیدهای Object Storage |
| `OFFLINE_S3_REGION` | خالی | — | |
| `OFFLINE_S3_ADDRESSING_STYLE` | `path` | — | `path` یا `virtual` |
| `OFFLINE_S3_PREFIX` | خالی | — | پوشهٔ بسته‌ها داخل باکت |
| `OFFLINE_PACKAGES_DIR` | خالی | خالی | فقط توسعه: سرو بسته از پوشهٔ محلی |
| `OFFLINE_LICENSE_DAYS` | `30` | — | مدت استفادهٔ بدون اینترنت |
| `OFFLINE_URL_TTL_SECONDS` | `86400` | — | عمر لینک امضاشدهٔ دانلود |

## سایت

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `SITE_HOSTS` | `pharmenta.ir,site.localhost` | — | هاست‌هایی که سایت و پنل را می‌گیرند |
| `SITE_APP_URL` | `https://app.pharmenta.ir` | — | مقصد دکمه‌های «ورود به وب‌اپ» |
| `SITE_PUBLIC_URL` | `https://pharmenta.ir` | — | نشانی canonical، نقشهٔ سایت و فید |
| `SITE_DRUG_ATC_PREFIXES` | `J01` | — | دسته‌هایی که صفحهٔ عمومی دارو روی سایت دارند (`/drugs/`)؛ پیشوند ATC با ویرگول، مثلاً `J01,C09`. خالی = دارونامه خاموش ([12-website.md](12-website.md)) |
| `SITE_EDITORIAL_NAME` | `تیم علمی فارمنتا` | — | نام نویسندهٔ صفحه‌های دارو و مقاله‌های بی‌نویسنده (روی صفحه و در دادهٔ ساختاریافته) |

## کانتینر و Gunicorn

| متغیر | پیش‌فرض | رانفلر | کار |
|---|---|---|---|
| `PORT` | `8000` | معمولاً رانفلر می‌گذارد | درگاه گوش دادن (`docker-start.sh`) |
| `WEB_CONCURRENCY` | `max(2, 2×CPU+1)` | پیشنهاد: صریح، مثلاً `3` | تعداد worker. در کانتینر، تعداد CPU میزبان دیده می‌شود نه سهم کانتینر، پس بدون این متغیر ممکن است worker زیادی ساخته شود |
| `GUNICORN_THREADS` | `2` | — | |
| `GUNICORN_TIMEOUT` / `GUNICORN_GRACEFUL_TIMEOUT` | `60` / `30` | — | ثانیه |
| `GUNICORN_KEEPALIVE` | `5` | — | |
| `GUNICORN_LOG_LEVEL` | `info` | — | |
| `GUNICORN_BIND` | `0.0.0.0:8000` | — | `docker-start.sh` با `--bind` بر آن مقدم است |

## اپ (فرانت‌اند)

متغیرهای اپ هنگام **ساخت** داخل بسته قرار می‌گیرند. تغییرشان یعنی بیلد دوباره، نه ری‌استارت.

| متغیر | کجا تنظیم می‌شود | مقدار production | کار |
|---|---|---|---|
| `EXPO_PUBLIC_API_BASE_URL` | محلی: `frontend/.env`؛ وب‌اپ: `ARG` در `Dockerfile.frontend`؛ موبایل: `env` در `eas.json` | `https://api.pharmenta.ir/api/v1` | نشانی API |
| `EXPO_BASE_URL` | `ARG` در `Dockerfile.frontend` | خالی | زیرمسیر سرو وب (مثلاً `/Learning_Platform` برای GitHub Pages) |
| `NGINX_ENTRYPOINT_WORKER_PROCESSES_AUTOTUNE` | `Dockerfile.frontend` | `1` | تعداد worker nginx بر اساس سهم CPU کانتینر |

## متغیرهای منسوخ

این‌ها مال کد پیش از بازنویسی‌اند و نباید تنظیم شوند: `LEARNING_PRODUCT_ADAPTER`، `AI_DATA_PIPELINE_PROVIDER`.
