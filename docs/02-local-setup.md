# ۲. راه‌اندازی محیط توسعه

این فایل قدم‌به‌قدم توضیح می‌دهد چطور کل پروژه روی لپ‌تاپ اجرا و آزموده می‌شود. همهٔ دستورها از ریشهٔ مخزن (`Learning Platform/`) شروع می‌شوند.

## پیش‌نیازها

| ابزار | نسخه | برای |
|---|---|---|
| Python | 3.11 | بک‌اند |
| PostgreSQL | 16 (یا نزدیک به آن) | دیتابیس محلی و تست‌ها |
| Node.js و npm | Node 20 | اپ Expo |
| Git | — | — |
| `pg_dump` / `pg_restore` | هم‌نسخهٔ Postgres | بکاپ (`backup_database`) |
| Docker و Docker Compose | اختیاری | اجرای کامل در کانتینر |
| `adb` و گوشی اندروید یا شبیه‌ساز | اختیاری | تست اپ بومی |
| `eas-cli` (`npm i -g eas-cli`) | ≥ 21 | بیلد اپ موبایل |

## بک‌اند

### نصب

```bash
cd backend
python3.11 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env
```

در `backend/.env` دست‌کم این‌ها را تنظیم کنید:

- `DATABASE_URL` — دیتابیس محلی؛ روی لپ‌تاپ توسعه نام دیتابیس `pharmexa_dev` است، مثلاً `postgresql://postgres:<رمز>@localhost:5432/pharmexa_dev`.
- `SECRET_KEY` — هر مقدار تصادفی؛ تنظیمات محلی آن را سخت‌گیرانه بررسی نمی‌کنند.

بقیهٔ متغیرها پیش‌فرض محلی مناسبی دارند. فهرست کامل در [06-configuration.md](06-configuration.md).

> `manage.py` همیشه با `config.settings.local` اجرا می‌شود، مگر اینکه `DJANGO_SETTINGS_MODULE` را در **محیط شِل** بدهید. سطر `DJANGO_SETTINGS_MODULE` داخل `.env` روی انتخاب ماژول تنظیمات اثری ندارد. `wsgi.py` (یعنی Gunicorn) پیش‌فرض `config.settings.production` را برمی‌دارد.

### ساخت دیتابیس و اجرای سرور

```bash
createdb pharmexa_dev                              # یک بار
.venv/bin/python manage.py migrate
.venv/bin/python manage.py load_atc_reference      # گروه‌های ATC سطح ۱ و ۲
.venv/bin/python manage.py seed_website            # محتوای شروع سایت
.venv/bin/python manage.py createsuperuser         # حساب مدیر
.venv/bin/python manage.py runserver 127.0.0.1:8000
```

نشانی‌های محلی:

| نشانی | چیست |
|---|---|
| `http://127.0.0.1:8000/api/v1/docs/` | Swagger همهٔ API |
| `http://127.0.0.1:8000/api/v1/health/` | سلامت سرور |
| `http://127.0.0.1:8000/admin/` | ادمین Django |
| `http://127.0.0.1:8000/manage/` | مدیریت یکپارچه: فروش، محتوای سایت، اپ و کیفیت داده، با یک ورود (`/manage/login/`) |
| `http://site.localhost:8000/` | سایت؛ `site.localhost` در مرورگر به 127.0.0.1 می‌رود و در `SITE_HOSTS` پیش‌فرض هست |

رفتارهای محیط محلی:

- **پیامک:** بدون `SMSIR_API_KEY`، کد تأیید فرستاده نمی‌شود و در لاگ `runserver` چاپ می‌شود (`SMS (console backend, not sent) to ...: code 12345`).
- **پرداخت:** تنظیمات محلی درگاه `fake` را برمی‌دارند که هر پرداختی را تأیید می‌کند. در production این درگاه رد می‌شود.
- **کش:** بدون Redis، کش داخل حافظهٔ هر پروسه است (`LocMemCache`).
- **ایمیل:** ایمیل‌ها در کنسول چاپ می‌شوند.

### پر کردن دیتابیس محلی

دیتابیس تازه خالی است. ترتیب پیشنهادی (جزئیات هر دستور در [07-data.md](07-data.md)):

```bash
# داروها و خلاصه‌های بالینی (از پایپلاین openFDA)
.venv/bin/python manage.py import_openfda
# ماشین‌حساب‌ها، گایدلاین‌ها و بیماری‌ها (فایل‌های قابل‌حمل)
.venv/bin/python manage.py import_calculators_db --source ~/Documents/pharmenta-reference-data/calculators.db
.venv/bin/python manage.py import_guidelines_db  --source ~/Documents/pharmenta-reference-data/guidelines.db
.venv/bin/python manage.py import_diseases_db    --source ~/Documents/pharmenta-reference-data/diseases.db
# سؤال‌ها و فلش‌کارت‌ها
.venv/bin/python manage.py import_study_content_db --source ~/Documents/pharmenta-reference-data/study_content.db
```

UpToDate و Lexicomp وارد دیتابیس نمی‌شوند و مستقیم از فایل خوانده می‌شوند:

| داده | متغیر | پیش‌فرض روی لپ‌تاپ |
|---|---|---|
| UpToDate | `UPTODATE_DB_DIR` | `/home/amir/Documents/UpToDate` |
| Lexicomp | `LEXICOMP_DB_DIR` | `/home/amir/Documents/Lexicomp_Drug_Interactions` |

اگر پوشه نباشد، آن بخش‌ها `503 FEATURE_NOT_AVAILABLE` می‌دهند و اپ حالت «به‌زودی» نشان می‌دهد.

### تست بستهٔ آفلاین بدون باکت

برای امتحان دانلود آفلاین روی لپ‌تاپ، بسته را محلی بسازید و بک‌اند را به جای باکت به آن پوشه وصل کنید. در `backend/.env`:

```
OFFLINE_PACKAGE_SECRET=<یک مقدار آزمایشی؛ نه مقدار سرور>
OFFLINE_PACKAGES_DIR=/home/amir/offline-packages-dev
```

سپس `build_offline_package` را با `--out` همان پوشه اجرا کنید. اگر متغیرهای `OFFLINE_S3_*` هم در `.env` باشند، باکت اولویت دارد.

## اپ (Expo)

### نسخهٔ وب

```bash
cd frontend
npm ci
cp .env.example .env          # EXPO_PUBLIC_API_BASE_URL=http://127.0.0.1:8000/api/v1
npm run web                   # http://localhost:8081
```

`EXPO_PUBLIC_API_BASE_URL` هنگام ساخت داخل بسته قرار می‌گیرد. بعد از تغییرش سرور Expo را دوباره اجرا کنید.

### اندروید و iOS

اپ ماژول‌های بومی‌ای دارد که در Expo Go نیستند (`@kesha-antonov/react-native-background-downloader` برای دانلود پس‌زمینه). برای اجرای کامل روی گوشی یک **development build** بسازید. پروفایل `development` در `eas.json` به بستهٔ `expo-dev-client` نیاز دارد که هنوز در `package.json` نیست؛ بار اول نصبش کنید:

```bash
cd frontend
npx expo install expo-dev-client                      # یک بار
eas build --profile development --platform android    # یک بار؛ APK را روی گوشی نصب کنید
npx expo start --dev-client
```

راه ساده‌تر برای فقط امتحان کردن: APK پروفایل `preview` (`eas build --profile preview --platform android`). این APK به API production وصل است.

روی گوشی واقعی به‌جای `127.0.0.1` نشانی IP لپ‌تاپ در شبکهٔ محلی را در `EXPO_PUBLIC_API_BASE_URL` بگذارید، و همان نشانی را به `ALLOWED_HOSTS` و `CORS_ALLOWED_ORIGINS` بک‌اند اضافه کنید.

## اجرای کامل با Docker

```bash
echo 'SECRET_KEY=<دست‌کم ۵۰ کاراکتر تصادفی>' > .env     # در ریشهٔ مخزن
docker compose up --build
```

| سرویس | درگاه روی لپ‌تاپ | توضیح |
|---|---|---|
| `db` | 5433 | Postgres 16؛ کاربر و دیتابیس `pharmexa` |
| `redis` | — | کش و صف Celery |
| `backend` | 8000 | با تنظیمات production؛ هنگام شروع `migrate` می‌کند |
| `worker` | — | Celery (فعلاً فقط ایمیل بازیابی رمز) |
| `frontend` | 8081 | خروجی وب Expo پشت nginx، وصل به `http://localhost:8000/api/v1` |

برای وصل کردن `manage.py` لپ‌تاپ به همین دیتابیس:
`DATABASE_URL=postgresql://pharmexa:pharmexa_local_password@127.0.0.1:5433/pharmexa`.

## تست و بررسی

| دستور | چه چیزی را می‌سنجد |
|---|---|
| `cd backend && .venv/bin/python manage.py test` | همهٔ تست‌های بک‌اند (نیاز به Postgres دارد) |
| `.venv/bin/python manage.py test apps.offline` | تست‌های یک اپ |
| `.venv/bin/python manage.py check` | بررسی پیکربندی |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | مایگریشن جاافتاده |
| `cd frontend && npm run typecheck` | TypeScript (`tsc --noEmit`) |
| `cd frontend && npm run build:web` | ساخت خروجی وب (همان که دیپلوی می‌شود) |

CI همین‌ها را روی هر push به `main` و هر Pull Request اجرا می‌کند ([08-deployment.md](08-deployment.md#ci)). اپ تست خودکار رابط کاربری ندارد؛ تغییرات ظاهری را در مرورگر و گوشی ببینید.

## روال کار با مخزن

- شاخهٔ اصلی `main` است. هر push به `main` بک‌اند را از نو دیپلوی می‌کند و اگر `frontend/` عوض شده باشد، شاخهٔ `deploy-web` را هم از نو می‌سازد ([08-deployment.md](08-deployment.md)).
- پیام کامیت کوتاه، انگلیسی و امری باشد، مثل `Add offline UpToDate and Lexicomp packages`. تغییرات نامرتبط در یک کامیت نروند.
- قالب فایل‌ها طبق `.editorconfig`: UTF-8، پایان خط LF، تورفتگی ۴ فاصله برای Python و ۲ فاصله برای `js/ts/tsx/json/yml`.
- هیچ رازی (`.env`، کلید، رمز) کامیت نشود؛ `.gitignore` جلوی `.env` را می‌گیرد.
- دستیارهای هوش مصنوعی پیش از جست‌وجو در کد از `graphify query` استفاده می‌کنند و بعد از تغییر کد `graphify update .` را اجرا می‌کنند (`CLAUDE.md`).
