# راهنمای واحد استقرار سرچ هوشمند در رانفلر

آخرین به‌روزرسانی: ۲۰۲۶-۱۱-۱۵

این فایل مسیر اجرای مرحله‌به‌مرحله است. برای ادامهٔ کار، همین فایل را دنبال کن؛ پیام‌های پراکندهٔ قبلی و سند ۴۶ برای تعیین ترتیب اجرا لازم نیستند. هر کادر مشخص می‌کند دستور در کدام محیط اجرا می‌شود. در صورت خطا، همان مرحله حل شود و سپس به بعدی برو.

**نقطهٔ فعلی کار:** PostgreSQLهای جست‌وجو/بازخورد و cacheهای Redis تأیید شدند. اجرای worker کنار بک‌اند روی سرور آغاز شد ولی با `VersionMismatch` کلاینت Redis نسخهٔ ۵٫۳٫۱ متوقف شد. اصلاح وابستگی‌ها، بررسی transport در ساخت image/CI و اصلاح alias تست رسانه در این تغییر آماده شده‌اند. پس از push و بازسازی image، از **بخش ۷، رفع خطای نسخهٔ کلاینت Redis در worker** ادامه بده. Celery و AI Lab طبق انتخاب مالک فعال می‌مانند؛ انتقال/فعال‌سازی نسل برداری هنوز جداگانه لازم است.

## وضعیت ثبت‌شده تا این لحظه

| مورد | وضعیت |
|---|---|
| بک‌اند، فرانت‌اند و PostgreSQL اصلی برنامه | از قبل موجودند |
| سرویس جدید `reference-db` | ساخته شده؛ ۳ گیگابایت RAM و سهم CPU گزارش‌شدهٔ ۱ گیگاهرتز |
| شاخهٔ سرویس دیتابیس | `deploy-reference-db`؛ Dockerfile ریشه؛ کامیت آماده‌شدهٔ `212df0a` |
| نام دیتابیس برداری و کاربر آن | هر دو `pharmenta_reference` |
| افزونهٔ vector | نسخهٔ `0.8.7` در سرور تأیید شد |
| شبکهٔ داخلی دیتابیس | `reference-db-xoc-service`، پورت `8000` |
| دیسک پایدار دیتابیس | اتصال به `/var/lib/postgresql/data` توسط مالک تأیید شد |
| دسترسی شبکه از بک‌اند | خروجی `accepting connections` تأیید شد |
| اتصال `psql` با رمز از بک‌اند | در ۱۵ نوامبر تأیید شد؛ نام دیتابیس و کاربر هر دو `pharmenta_reference` بودند |
| اتصال از alias خود Django | در ۱۵ نوامبر تأیید شد؛ `pharmenta_reference` و vector نسخهٔ `0.8.7` |
| migrationهای `ai_retrieval` | هر پنج مورد `0001` تا `0005` با `[X]` در ۱۵ نوامبر تأیید شدند |
| دیتابیس بازخورد | `pharmenta_ai_feedback` در ۱۵ نوامبر داخل همان reference-db ساخته شد |
| اتصال و migrationهای بازخورد | پس از Redeploy در ۱۵ نوامبر، `[X] 0001_initial` از alias برابر `ai_feedback` تأیید شد |
| Redis | منابع اعلام‌شده: RAM برابر ۱٫۵ گیگابایت، CPU برابر ۱ گیگاهرتز، فضا برابر ۵ گیگابایت؛ آزمون شبکه از بک‌اند موفق شد |
| اتصال Redis | از بک‌اند با کاربر `default` و رمز روی `ai-redis-yum-service:6379` پاسخ `PONG` تأیید شد؛ نسخهٔ واقعی `8.4.0` |
| Redis در تنظیم‌های Django | پس از حذف `CACHE_LOCATION` و Redeploy، هر سه cache برابر `True` شدند |
| نشانی راه‌دور Redis | `rediss://ai-redis-pharmenta.runflare.cloud:6379` از پنل گزارش شد؛ آزمون شبکه از مسیر داخلی انجام شده است |
| worker | نقش ترکیبی روی سرور اجرا شد ولی transport با کلاینت ۵٫۳٫۱ شکست خورد؛ اصلاح نسخه‌ها آمادهٔ انتشار است |
| انتقال کامل بردارها به سرور | هنوز انجام نشده است |

### محل اجرای دستورها

| برچسب | منظور |
|---|---|
| **لپ‌تاپ** | ترمینال کامپیوتر خودت؛ مسیر پروژه `/home/amir/Documents/Learning Platform` |
| **پنل رانفلر** | تنظیمات سرویس/Secrets/شبکه/دیسک، نه دستور shell |
| **ترمینال reference-db** | ترمینال کانتینر دیتابیس جدید؛ دستورهای `psql` و `createdb` |
| **ترمینال بک‌اند** | ترمینال سرویس اصلی Django، مسیر `/app`؛ دستورهای `python manage.py ...` |
| **ترمینال Redis** | ترمینال سرویس Redis، پس از ساخت آن |
| **ترمینال worker** | در حالت منتخب، همان ترمینال بک‌اند؛ worker پردازهٔ جدا در همان کانتینر است |

دیتابیس اصلی برنامه برای کاربران، اشتراک‌ها و داده‌های برنامه حفظ می‌شود. `reference-db` محل بردارها و ایندکس جست‌وجو است. بک‌اند به هر دو متصل می‌شود. بازخورد هم یک database با نام جدا خواهد داشت و می‌تواند داخل همین سرویس جدید PostgreSQL باشد؛ برای آن الزاماً سرویس دیگری نمی‌خریم.

هیچ رمز، کلید API یا URL واقعیِ حاوی رمز در این فایل نیست. این مقادیر فقط در Secrets پنل یا ورودی خصوصی ترمینال وارد شوند. دیتابیس اصلی یا دیسک PostgreSQL برای رفع خطاهای این راهنما حذف/reset نمی‌شوند.

## صفر ـ بازگرداندن بک‌اند در صورت تکرار کرش اتصال

این بخش برای رخداد قبلیِ رمز نامعتبر ثبت شده است؛ پس از موفقیت آزمون بخش ۳، آن را دوباره به‌صورت پیش‌فرض اجرا نکن.

**محل: پنل رانفلر، تنظیمات سرویس بک‌اند اصلی**

1. مقدار فعلی `REFERENCE_SEARCH_DATABASE_URL` را در محل خصوصی خودت نگه دار؛ سپس آن متغیر را موقتاً حذف یا خالی کن.
2. `AI_LAB_ENABLED=False` بگذار تا قابلیت در حال آماده‌سازی خاموش باشد.
3. `DATABASE_URL` اصلی، تنظیمات پرداخت، ایمیل و بقیهٔ تنظیمات قبلی را همان‌طور نگه دار.
4. بک‌اند را Redeploy کن.

علت: اسکریپت شروع بک‌اند، در صورت وجود URL جست‌وجو، migration همان اتصال را هم اجرا می‌کند. رمز نامعتبر باعث توقف این مرحله و شروع نشدن وب‌سرور شده است. حذف موقت این اتصال، جدول یا داده‌ای را حذف نمی‌کند.

خروجی مورد انتظار: بک‌اند از مرحلهٔ startup عبور کند و وب‌سرور بالا بیاید. در مرورگر، `https://api.pharmenta.ir/api/v1/health/` باید وضعیت سالم دیتابیس اصلی را نشان دهد. در گزارش ۱۵ نوامبر، ترمینال کانتینر جدید بک‌اند در دسترس بود و آزمون `psql` موفق شد؛ وضعیت HTTP سلامت به‌صورت مستقل گزارش نشده است.

## ۱ ـ ساخت سرویس دیتابیس برداری — انجام شده

**محل: پنل رانفلر**

این بخش را برای سرویس موجود دوباره اجرا نکن. مشخصات ساخته‌شده:

| گزینه | مقدار |
|---|---|
| نوع | Docker |
| مخزن | همین مخزن پروژه |
| شاخه | `deploy-reference-db` |
| Dockerfile | فایل `Dockerfile` در ریشهٔ همان شاخه |
| پورت برنامه | `8000` |
| دیسک پایدار | `/var/lib/postgresql/data` |
| image | `pgvector/pgvector:0.8.7-pg17` |

Dockerfile دیتابیس، PostgreSQL را واقعاً با `postgres -p 8000` اجرا می‌کند. Dockerfile ریشهٔ `main` برای بک‌اند باقی مانده است؛ معرفی `main` به سرویس دیتابیس روش درستی نیست.

متغیرهای **همین سرویس دیتابیس**:

```dotenv
POSTGRES_DB=pharmenta_reference
POSTGRES_USER=pharmenta_reference
```

`POSTGRES_PASSWORD` یک secret خصوصی است. مسیر داخلی داده در image برابر `/var/lib/postgresql/data/pgdata` است و زیر همان دیسک پایدار قرار دارد. این سرویس برای ارتباط داخلی زیردامنهٔ وب لازم ندارد.

**محل: ترمینال reference-db، فقط برای بررسی**

```bash
psql -p 8000 -U pharmenta_reference -d pharmenta_reference -c "SELECT current_database(), extversion FROM pg_extension WHERE extname='vector';"
```

نتیجهٔ تأییدشده:

```text
pharmenta_reference | 0.8.7
```

اگر در راه‌اندازی تازه نام دیتابیس موجود نبود، ابتدا فهرست را ببین:

```bash
psql -p 8000 -U pharmenta_reference -d postgres -c '\l'
```

فقط در صورت نبود نام مورد انتظار:

```bash
createdb -p 8000 -U pharmenta_reference pharmenta_reference
psql -p 8000 -U pharmenta_reference -d pharmenta_reference -c 'CREATE EXTENSION IF NOT EXISTS vector;'
```

این ایجاد یک database داخل سرویس موجود است، نه ساخت کانتینر یا خرید سرویس دیگر.

## ۲ ـ شبکهٔ داخلی دیتابیس — انجام شده

**محل: پنل رانفلر، reference-db → شبکه‌ها**

| گزینه | مقدار |
|---|---|
| نوع | `ClusterIP` |
| نام شبکه | `reference-db-xoc-service` |
| Port | `8000` |
| Target Port | `8000` |

Port برای اتصال سرویس‌های دیگر است و Target Port، پورت داخل کانتینر است. این اتصال PostgreSQL/TCP است، نه HTTP.

**محل: ترمینال بک‌اند**

```bash
pg_isready -h reference-db-xoc-service -p 8000 -U pharmenta_reference -d pharmenta_reference -t 5
```

خروجی تأییدشده:

```text
reference-db-xoc-service:8000 - accepting connections
```

این دستور پاسخ‌گویی سرور را ثابت می‌کند؛ صحت رمز یا اتصال Django را ثابت نمی‌کند. [مرجع pg_isready](https://www.postgresql.org/docs/17/app-pg-isready.html)

## ۳ ـ تنظیم رمز واقعی PostgreSQL و آزمون آن — اتصال psql تأیید شد

**آزمون انتهای این بخش در سرور موفق شده است.** دستور تنظیم رمز برای سابقه و رفع احتمالی خطای مشابه نگه داشته شده؛ برای ادامهٔ عادی، رمز را دوباره تغییر نده و به بخش ۴ برو.

مقدار `POSTGRES_PASSWORD` فقط هنگام initialization روی مسیر دادهٔ خالی رمز را می‌سازد؛ تغییر این متغیر پس از ساخته‌شدن PostgreSQL، رمز نقش موجود را تغییر نمی‌دهد. علت دقیق اختلاف فعلی بین رمز نقش و URL هنوز مشخص نیست؛ رمز نامنطبق یا واردکردن نادرست URL از علت‌های ممکن‌اند. [مرجع image](https://hub.docker.com/_/postgres)

**محل: ترمینال reference-db**

وارد محیط PostgreSQL شو:

```bash
psql -p 8000 -U pharmenta_reference -d postgres
```

در محیط `psql`، این دستور را وارد کن:

```psql
\password pharmenta_reference
```

یک رمز تصادفی طولانی انتخاب کن، دو بار وارد کن و در محل خصوصی خودت نگه دار. تایپ رمز نمایش داده نمی‌شود. این روش رمز خام را داخل فرمان SQL یا history نمی‌گذارد. سپس:

```psql
\q
```

**محل: پنل رانفلر، Secrets سرویس reference-db**

مقدار `POSTGRES_PASSWORD` را با همین رمز یکسان نگه دار. اصلاح رمز نقش در مرحلهٔ قبل انجام شد؛ فقط عوض‌کردن متغیر پنل جای آن دستور را نمی‌گیرد.

**محل: ترمینال بک‌اند، پس از بالا آمدن مجدد آن در بخش صفر**

اتصال واقعی با رمز را پیش از ثبت دوبارهٔ URL امتحان کن:

```bash
psql -h reference-db-xoc-service -p 8000 -U pharmenta_reference -d pharmenta_reference -W -c 'SELECT current_database(), current_user;'
```

رمز جدید را در prompt وارد کن. خروجی مورد انتظار دو مقدار `pharmenta_reference` است. اگر همین دستور خطای رمز داد، هنوز URL بک‌اند را ثبت نکن؛ رمز نقش، ورود دقیق رمز و مقصد شبکه باید بررسی شوند.

خروجی گزارش‌شده در ۱۵ نوامبر:

```text
current_database    | current_user
pharmenta_reference | pharmenta_reference
```

## ۴ ـ ثبت اتصال جست‌وجو در بک‌اند

**پیش‌نیاز: آزمون رمز بخش ۳ موفق باشد.**

**محل: ترمینال بک‌اند، `/app`**

برای ساخت URL با encoding درست و آزمودن **همان URL** پیش از ثبت آن در پنل:

```bash
python -c 'from getpass import getpass; from urllib.parse import quote; import psycopg; url="postgresql://pharmenta_reference:"+quote(getpass("Reference DB password: "),safe="")+"@reference-db-xoc-service:8000/pharmenta_reference"; conn=psycopg.connect(url,connect_timeout=5); conn.close(); print(url)'
```

دقیقاً همان رمزی را وارد کن که در آزمون موفق `psql` استفاده شد. دستور با URL ساخته‌شده اتصال می‌زند و فقط در صورت موفقیت، URL را چاپ می‌کند. این خروجی حاوی رمز است؛ فقط خودت آن را در پنل وارد کن و در گفتگو نفرست. تنظیم دائمی سرویس در این مرحله تغییر نمی‌کند. اگر خطا داد و URL چاپ نشد، قبل از ذخیرهٔ متغیر علت را حل کن.

**محل: پنل رانفلر، Secrets بک‌اند اصلی**

| کلید | مقدار |
|---|---|
| `REFERENCE_SEARCH_DATABASE_URL` | فقط URL تولیدشده، بدون عنوان متغیر یا کوتیشن اضافی |
| `AI_LAB_ENABLED` | در راه‌اندازی اولیهٔ این بخش `False` بود؛ انتخاب فعلی `True` همراه تنظیم‌های بخش ۷ اعمال می‌شود |

`DATABASE_URL` اصلی حفظ می‌شود. بک‌اند را با آخرین کد `main` که این alias را پشتیبانی می‌کند Redeploy کن؛ کدهای مربوط در کامیت‌های `d029f15` و `ca56155` ثبت شده‌اند.

**محل: ترمینال بک‌اند، `/app`**

```bash
python manage.py dbshell --database reference_search -- -c "SELECT current_database(), extversion FROM pg_extension WHERE extname='vector';"
```

خروجی مورد انتظار: `pharmenta_reference` و `0.8.7`. این بار تنظیم اتصال خود Django و رمز آن استفاده می‌شوند. مالک در ۱۵ نوامبر همین خروجی را از کانتینر جدید بک‌اند گزارش کرد؛ اتصال این alias تأیید شد.

## ۵ ـ آماده‌سازی schema و دیتابیس بازخورد

**محل: ترمینال بک‌اند**

ابتدا وضعیت migrationهای دیتابیس جست‌وجو را بررسی کن؛ این دستور فقط وضعیت را می‌خواند:

```bash
python manage.py showmigrations ai_retrieval --database reference_search
```

مالک در ۱۵ نوامبر خروجی هر پنج migration، از `0001_initial` تا `0005_reference_media_catalog`، را با `[X]` گزارش کرد؛ این بررسی انجام شده است. اسکریپت شروع بک‌اند هنگام راه‌اندازی migrationها را اجرا می‌کند. در راه‌اندازی دیگر یا نسخهٔ بعدی، اگر موردی با `[ ]` وجود داشت، migrationهای همان اتصال را اعمال کن:

```bash
python manage.py migrate --database reference_search --no-input
```

برای آماده‌سازی اولیه یا نسخهٔ بک‌اندی که migration را خودکار اجرا نمی‌کند، دستورهای کامل زیر نیز در همین ترمینال اجرا می‌شوند؛ embedding تولید نمی‌کنند:

```bash
python manage.py migrate
python manage.py migrate --database reference_search
```

اسکریپت شروع جدید بک‌اند این دو کار را هنگام boot نیز انجام می‌دهد؛ خروجی «No migrations to apply» در اجرای دوباره طبیعی است.

### بررسی تنظیم اتصال بازخورد

**محل: ترمینال بک‌اند**

ابتدا فقط وجود تنظیم صریح اتصال را بررسی کن؛ رمز یا URL چاپ نمی‌شود:

```bash
python manage.py shell -c 'from django.conf import settings; print("FEEDBACK_CONFIGURED:", bool(settings.AI_LAB_FEEDBACK_DATABASE_URL))'
```

اگر `True` بود، اتصال موجود را حفظ کن و وضعیت migrationهای همان دیتابیس را بررسی کن:

```bash
python manage.py showmigrations ai_feedback --database ai_feedback
```

خروجی باید migrationهای بازخورد را با `[X]` نشان دهد. خطای اتصال در همین مرحله بررسی می‌شود؛ اتصال موجود را خودکار با database دیگری جایگزین نکن.

مالک در ۱۵ نوامبر ابتدا خروجی `FEEDBACK_CONFIGURED: False` و سپس ایجاد موفق database بازخورد در همین reference-db را گزارش کرد. پس از مرحلهٔ ثبت URL و Redeploy نیز خروجی `[X] 0001_initial` تأیید شد. مراحل این بخش برای سابقه نگه داشته شده‌اند؛ برای ادامه به بخش ۶ برو.

### آماده‌کردن دیتابیس بازخورد

**محل: همان ترمینال بک‌اند، مسیر `/app`**

با اتصال تأییدشدهٔ `reference_search` بررسی کن آیا `pharmenta_ai_feedback` در همان سرویس PostgreSQL وجود دارد. فقط اگر موجود نبود ساخته می‌شود؛ دیتابیس موجود پاک یا بازسازی نمی‌شود. `CREATE DATABASE` به نقش دارای مجوز ساخت دیتابیس نیاز دارد؛ کاربر اولیهٔ image این مجوز را دارد. این دستور هیچ embedding تولید نمی‌کند و URL یا رمز را چاپ نمی‌کند:

```bash
python manage.py shell -c 'from django.db import connections; cursor=connections["reference_search"].cursor(); cursor.execute("SELECT 1 FROM pg_database WHERE datname=%s", ["pharmenta_ai_feedback"]); exists=cursor.fetchone() is not None; cursor.execute("CREATE DATABASE pharmenta_ai_feedback") if not exists else None; cursor.close(); print("Feedback database already exists." if exists else "Feedback database created.")'
```

مالک پیام `Feedback database created.` را در ۱۵ نوامبر گزارش کرد؛ این مرحله انجام شده است. اتصال بازخورد و جدول‌های آن هنوز در مراحل بعد تنظیم می‌شوند.

### ساخت و ثبت URL بازخورد

**محل: ترمینال بک‌اند؛ پس از تأیید database بازخورد در reference-db**

از همان URL تأییدشدهٔ جست‌وجو، URL بازخورد را بساز. دستور فقط نام database را عوض می‌کند، با همان رمز و تنظیمات اتصال آزمایش می‌کند و فقط در صورت موفقیت URL را چاپ می‌کند:

```bash
python manage.py shell -c 'from django.conf import settings; from urllib.parse import urlsplit, urlunsplit; import psycopg; parts=urlsplit(settings.REFERENCE_SEARCH_DATABASE_URL); url=urlunsplit(parts._replace(path="/pharmenta_ai_feedback")); conn=psycopg.connect(url,connect_timeout=5); conn.close(); print(url)'
```

خروجی حاوی رمز است؛ فقط خودت آن را در Secrets پنل ثبت کن و در گفتگو نفرست. اگر اتصال خطا داد، قبل از ذخیرهٔ متغیر همان خطا بررسی شود.

**محل: پنل بک‌اند**

فقط خروجی URL پس از اتصال موفق را در `AI_LAB_FEEDBACK_DATABASE_URL` بگذار و `AI_LAB_FEEDBACK_ENABLED=True` تنظیم کن. مقدار این اتصال با اتصال اصلی و `reference_search` متفاوت است، چون نام database آن جداست. در راه‌اندازی اولیه، اتصال‌های معتبر قبلی و مقدار موقت فلگ حفظ می‌شدند؛ برای ادامهٔ فعلی، فعال‌سازی `AI_LAB_ENABLED=True` طبق انتخاب مالک با مجموعهٔ تنظیم‌های بخش ۷ انجام می‌شود. بک‌اند را Redeploy کن؛ اسکریپت شروع، migrationهای بازخورد را نیز اجرا می‌کند. پس از اعمال تنظیمات:

**محل: ترمینال بک‌اند**

پس از Redeploy، وضعیت migrationهای بازخورد را بررسی کن:

```bash
python manage.py showmigrations ai_feedback --database ai_feedback
```

خروجی `[X] 0001_initial` در ۱۵ نوامبر از کانتینر جدید بک‌اند گزارش شد؛ اتصال alias بازخورد و اعمال migration آن تأیید شدند. ثبت عملی لایک/دیسلایک هنگام آزمون نهایی سرچ بررسی خواهد شد. در راه‌اندازی دیگر، اگر migration اعمال نشده بود:

```bash
python manage.py migrate ai_feedback --database ai_feedback
```

## ۶ ـ Redis آمادهٔ رانفلر

**مسیر منتخب مالک: اپ آمادهٔ Redis در بخش ایجاد دیتابیس رانفلر.** سرویس Redis سفارشی از مخزن Docker ساخته نمی‌شود. رانفلر Redis را در فهرست سرویس‌های دادهٔ پشتیبانی‌شده معرفی کرده است؛ جزئیات پلن، نسخه، پورت و گزینه‌های پنل این حساب از خود پنل دریافت می‌شوند. [سرویس‌های رانفلر](https://runflare.com/)

شاخهٔ محلی `deploy-ai-redis` با کامیت `0ae2460` و چهار آزمون موفق، برای سابقه محفوظ است. دستورهای push و Deploy آن به مسیر جاری تعلق ندارند؛ شاخه یا worktree آن هم حذف نشده‌اند. نسخهٔ `8.4.0` و اتصال واقعی سرویس تأیید شده‌اند؛ وضعیت persistence و سیاست eviction هنوز تأیید نشده‌اند.

### ۶.۱ ـ ساخت Redis آماده

**محل: پنل رانفلر، همان پروژه و ناحیه/کلاستر بک‌اند**

1. در بخش ایجاد دیتابیس، اپ آمادهٔ `Redis` را انتخاب کن.
2. نام پیشنهادی سرویس `ai-redis` است. مالک گزینه‌های `6`، `6.2`، `7.2.3`، `8.0`، `7.2.0` و `8.4` را اعلام کرد؛ `7.4` موجود نیست. پیشنهاد از میان گزینه‌های موجود **Redis 8.4** است؛ این سری انتشار پایدار دارد. نسخهٔ واقعی `8.4.0` و آزمون cacheها پس از ساخت تأیید شدند؛ آزمون مستقل صف و استریم هنوز باقی است. [یادداشت انتشار Redis 8.4](https://redis.io/docs/latest/operate/oss_and_stack/stack-with-enterprise/release-notes/redisce/redisos-8.4-release-notes/)
3. دسترسی داخلی و احراز هویت را تنظیم کن. نام شبکه/host داخلی، پورت، نسخه و نام کاربری احتمالی را از مشخصات واقعی همان سرویس بردار. پورت `8000` به Dockerfile قبلی مربوط بود؛ پورت سرویس آماده حدس زده نمی‌شود و مقدار پنل ملاک است.
4. رمز یا URL کامل اتصال را فقط در Secrets/محل خصوصی نگه دار. فقط host، پورت، نسخه و نام کاربری غیرمحرمانه برای ادامه گزارش شوند. زیردامنهٔ وب لازم نیست.

منابع Redis برای راه‌اندازی و آزمون اولیه با هم‌زمانی محدود:

| منبع | پیشنهاد اولیه | تخصیص اعلام‌شدهٔ مالک |
|---|---|---|
| RAM سرویس | یک گیگابایت | ۱٫۵ گیگابایت |
| CPU در واحد نمایش‌داده‌شدهٔ پنل رانفلر | ۰٫۵ گیگاهرتز | ۱ گیگاهرتز؛ این واحد با vCPU معادل فرض نمی‌شود |
| فضای دیسک | ۲ گیگابایت پایدار | ۵ گیگابایت؛ وضعیت persistence سرویس هنوز بررسی نشده است |

این تخصیص برای شروع آزمون با هم‌زمانی محدود مناسب است؛ ظرفیت واقعی هنوز آزمون بار نشده است. مقالات، بردارها و HNSW در PostgreSQL باقی می‌مانند؛ این منابع Redis برای صف، رویدادها و کش‌اند. مصرف حافظه، CPU و فضای AOF پس از آزمون بررسی می‌شوند؛ منابع worker هم باید در همان بودجهٔ کلی حساب شوند.

### ۶.۲ ـ تنظیم‌های سرویس و آزمون اتصال

**قدم فعلی، محل: پنل رانفلر، مشخصات اتصال Redis**

از مشخصات سرویس، host یا نام شبکهٔ داخلی، پورت، نام کاربری احتمالی و فعال‌بودن TLS را بگیر. فقط همین اطلاعات غیرمحرمانه گزارش شوند؛ رمز و URL کامل در گفتگو فرستاده نشوند. آدرس اتصال داخلی باید از بک‌اند همان پروژه قابل دسترسی باشد. سپس آزمون `PING` با احراز هویت از داخل بک‌اند اجرا می‌شود؛ پیش از موفقیت آن، متغیرهای اصلی cache و broker تغییر نکنند تا اتصال نامعتبر مانع شروع بک‌اند نشود.

**اطلاعات گزارش‌شده:** میزبان داخلی `ai-redis-yum-service` و کاربر `default` هستند. نشانی راه‌دورِ بدون رمز `rediss://ai-redis-pharmenta.runflare.cloud:6379` است. آزمون زیر در بک‌اند روی مسیر داخلی و پورت `6379` موفق شد؛ بنابراین برای ادامهٔ این مسیر از پروتکل `redis://` روی شبکهٔ داخلی استفاده می‌شود. نشانی راه‌دور TLS، مسیر متفاوتی است و تنظیم آن جایگزین تنظیم مسیر داخلی نمی‌شود.

**محل: ترمینال بک‌اند، `/app`؛ آزمون اولیه بدون ارسال رمز**

پورت `6379` اعلام‌شده را روی میزبان داخلی به‌صورت یک probe محدود آزمایش کن. این دستور هیچ تنظیمی تغییر نمی‌دهد و فقط یک `PING` بدون احراز هویت می‌فرستد:

```bash
python -c 'import socket; s=socket.create_connection(("ai-redis-yum-service",6379),timeout=5); s.sendall(b"*1\r\n$4\r\nPING\r\n"); print(s.recv(512).decode(errors="replace").strip() or "NO_RESPONSE"); s.close()'
```

مالک خروجی `-NOAUTH Authentication required.` را گزارش کرد؛ دسترسی به Redis و پاسخ‌گویی پروتکل معمولی روی مسیر داخلی تأیید شدند. صحت رمز هنوز تأیید نشده است. در راه‌اندازی دیگر، پاسخ `+PONG` یعنی این probe بدون رمز پذیرفته شده و سیاست احراز هویت باید پیش از ادامه بررسی شود؛ timeout، قطع اتصال، پاسخ نامفهوم یا `NO_RESPONSE` به بررسی پورت/مسیر/TLS نیاز دارد.

**محل: ترمینال بک‌اند، `/app`؛ آزمون اتصال با رمز — انجام شده**

```bash
python -c 'from getpass import getpass; import redis; r=redis.Redis(host="ai-redis-yum-service",port=6379,username="default",password=getpass("Redis password: "),socket_connect_timeout=5,socket_timeout=5); print("PONG" if r.ping() else "FAILED"); print("Redis version:",r.info("server").get("redis_version")); r.close()'
```

مالک خروجی `PONG` و `Redis version: 8.4.0` را گزارش کرد؛ احراز هویت و خواندن نسخه تأیید شدند. رمز این آزمون در ورودی مخفی ترمینال وارد شد و در این سند یا گفتگو ذخیره نشده است. در اجرای تازه، اگر `PONG` چاپ شد ولی `INFO` خطای مجوز داد، احراز هویت تأیید شده است و فقط مجوز خواندن مشخصات سرور باید بررسی شود.

این Redis علاوه بر cache، پیام صف و رویدادهای استریم را هم نگه می‌دارد. در تنظیم‌های قابل‌دسترسی سرویس، persistence مناسب صف (ترجیحاً AOF) و سیاست `noeviction` بررسی شوند؛ گزینه‌های script سفارشی قبلی به سرویس آماده منتقل‌شده فرض نمی‌شوند. اگر پنل این گزینه‌ها را نشان نمی‌دهد، تنظیم واقعی باید از ابزار مجاز سرویس یا پشتیبانی مشخص شود. پرشدن حافظه با `noeviction` هم نیاز به پایش دارد.

برای تخصیص اعلام‌شدهٔ ۱٫۵ گیگابایتی، نقطهٔ شروع پیشنهادیِ `maxmemory` برابر `512mb` است تا برای سربار Redis، بافرها و افزایش موقت حافظه هنگام ذخیره/بازنویسی فضای آزاد بماند. پیشنهاد قبلی `384mb` برای تخصیص یک‌گیگابایتی بود. این سقف داخلی با RAM کل سرویس متفاوت است و هنوز اعمال نشده؛ باید پیش از اعمال از دسترسی به تنظیم و مقدار واقعی سرویس مطمئن شد. `appendonly yes` و `appendfsync everysec` نیز در صورت قابل‌تنظیم‌بودن برای صف بررسی شوند. [حافظه و eviction](https://redis.io/docs/latest/develop/reference/eviction/)، [ذخیره‌سازی پایدار Redis](https://redis.io/docs/latest/operate/oss_and_stack/management/persistence/)

در زمان اتصال، دسترسی کلاینت به عملیات cache/قفل، Lua، Redis Streams و صف Celery بررسی می‌شود. برای تقسیم اتصال‌ها طبق بخش بعد باید دیتابیس‌های منطقی ۰ تا ۴ قابل استفاده باشند؛ سرویس cluster یا تک‌دیتابیس نیاز به تطبیق جدا دارد و پشتیبانی چند دیتابیس از پیش فرض نمی‌شود.

**پس از آماده‌شدن مشخصات سرویس:** URL واقعی پنل، شامل username احتمالی و `redis://` یا `rediss://`، در secret بک‌اند ثبت و اتصال از خود بک‌اند آزمایش خواهد شد. رمزهای دارای کاراکتر رزروشده باید در URL درست encode شوند. TLS و سایر گزینه‌های URL حفظ می‌شوند. هیچ دستور تستی نباید URL یا رمز را در خروجی عمومی چاپ کند.

در این مرحله، شبکه و احراز هویت مسیر داخلی تأیید شده‌اند؛ ساخت URLهای نهایی و ثبت متغیرهای بک‌اند در بخش بعد انجام می‌شود. ساخت Redis به‌تنهایی ساخت/اجرای worker نیست؛ وضعیت worker در بخش ۷ جدا بررسی می‌شود.

### ۶.۳ ـ اتصال بک‌اند به Redis

**محل: ترمینال بک‌اند، `/app`؛ ساخت و آزمون URLها پیش از ثبت Secrets**

دستور زیر رمز را در ورودی مخفی می‌گیرد، کاراکترهای رزروشده را encode می‌کند و با هر پنج URL، `PING` و انتخاب دیتابیس را آزمایش می‌کند. فقط پس از موفقیت همهٔ اتصال‌ها، پنج خط تنظیم را چاپ می‌کند:

```bash
python -c 'from getpass import getpass; from urllib.parse import quote; import redis; base="redis://default:"+quote(getpass("Redis password: "),safe="")+"@ai-redis-yum-service:6379/"; names=("REDIS_URL","CACHE_URL","THROTTLE_CACHE_URL","CELERY_BROKER_URL","AI_LAB_EVENT_REDIS_URL"); clients=[redis.Redis.from_url(base+str(i),socket_connect_timeout=5,socket_timeout=5) for i in range(5)]; assert all(c.ping() for c in clients), "REDIS_DB_CHECK_FAILED"; [c.close() for c in clients]; print("\n".join(name+"="+base+str(i) for i,name in enumerate(names)))'
```

**این خروجی حاوی رمز است؛ فقط در Secrets بک‌اند ذخیره شود و در گفتگو فرستاده نشود.** هر خط یک کلید و مقدار است؛ در فیلد مقدار فقط بخش بعد از اولین `=`، بدون کوتیشن اضافه، وارد شود. اگر دستور خطا داد، هیچ‌کدام از URLهای جدید ثبت نشوند و همان خطا بررسی شود.

**محل: Secrets بک‌اند**

برای مسیر داخلی تأییدشده، URLها با پروتکل `redis://`، میزبان `ai-redis-yum-service`، پورت `6379`، کاربر `default` و رمز encodeشده ساخته می‌شوند. برای پنج اتصال فقط شمارهٔ دیتابیس منطقی انتهای مسیر تغییر می‌کند؛ مقادیر واقعی پس از موفقیت آزمون اتصال با رمز ساخته می‌شوند:

| متغیر | شمارهٔ دیتابیس منطقی |
|---|---|
| `REDIS_URL` | `0` |
| `CACHE_URL` | `1` |
| `THROTTLE_CACHE_URL` | `2` |
| `CELERY_BROKER_URL` | `3` |
| `AI_LAB_EVENT_REDIS_URL` | `4` |

```dotenv
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
READINESS_REQUIRE_CACHE=True
```

اگر متغیر `CACHE_LOCATION` وجود دارد، حذف شود تا مقدار معتبر `CACHE_URL` استفاده شود؛ مقدار لفظی `$CACHE_URL` در پنل وارد نمی‌شود. متغیرهای معتبر PostgreSQL اصلی، `reference_search` و بازخورد حفظ شوند. در ادامهٔ فعلی، Celery و `AI_LAB_ENABLED=True` با نقش ترکیبی و کد جدید بخش ۷ فعال می‌شوند. سپس بک‌اند Redeploy شود.

**محل: ترمینال بک‌اند پس از Redeploy؛ آزمون واقعی هر سه cache**

```bash
python manage.py shell -c 'from django.conf import settings; from django.core.cache import caches; from uuid import uuid4; names=("default","throttle","ai_lab"); assert all("redis" in settings.CACHES[n]["BACKEND"].lower() for n in names), "REDIS_CACHE_NOT_ACTIVE"; key="deployment-probe:"+uuid4().hex; print({n:(caches[n].set(key,"ok",30),caches[n].get(key)=="ok",caches[n].delete(key))[1] for n in names})'
```

خروجی مورد انتظار: `{'default': True, 'throttle': True, 'ai_lab': True}`. فقط همین خروجی یا خطای بدون رمز گزارش شود. این آزمون یک کلید موقت با TTL می‌سازد، می‌خواند و حذف می‌کند؛ دادهٔ کاربران تغییر نمی‌کند. آزمون صف و استریم همراه worker در بخش ۷ اجرا می‌شود. تنظیم‌های persistence/حافظه/eviction نیز باید پیش از بهره‌برداری صف بررسی شوند.

### تشخیص URL نامعتبر بدون نمایش رمز

مالک پس از Redeploy خطای `Redis URL must specify one of the following schemes (redis://, rediss://, unix://)` را گزارش کرد. این خطا هنگام parse آدرس cache پیش‌فرض و پیش از اتصال رخ داد. مالک با حذف `CACHE_LOCATION` و Redeploy مشکل را رفع کرد و خروجی `{'default': True, 'throttle': True, 'ai_lab': True}` را گزارش کرد. این قسمت برای سابقهٔ عیب‌یابی حفظ شده است؛ در ادامهٔ فعلی آزمون تشخیصی زیر دوباره لازم نیست.

**محل: ترمینال بک‌اند، `/app`**

```bash
python manage.py shell -c 'from django.conf import settings; from decouple import config; valid=lambda v:isinstance(v,str) and v.startswith(("redis://","rediss://","unix://")); print("URLS:",{n:valid(getattr(settings,n,None)) for n in ("REDIS_URL","CACHE_URL","THROTTLE_CACHE_URL","CELERY_BROKER_URL","AI_LAB_EVENT_REDIS_URL")}); print("CACHES:",{n:valid(settings.CACHES[n].get("LOCATION")) for n in ("default","throttle","ai_lab")}); print("CACHE_LOCATION_DEFINED:",config("CACHE_LOCATION",default=None) is not None)'
```

این دستور فقط نام متغیرها و مقدارهای `True/False` را چاپ می‌کند. اگر URLها `True` باشند ولی cache پیش‌فرض `False` و `CACHE_LOCATION_DEFINED` برابر `True` باشد، override قدیمی باید از Secrets حذف شود. خالی‌کردن مقدار با حذف متغیر فرق دارد؛ مقدار خالی نیز default را بازنویسی می‌کند. اگر خود URLها `False` باشند، در فیلد مقدار پنل فقط URLِ بعد از اولین `=` ذخیره شود؛ نام متغیر، کوتیشن، فاصلهٔ اضافی یا عبارت لفظی `$CACHE_URL` جزو URL نیستند. پس از اصلاح، Redeploy و آزمون cache تکرار شود. رمز یا URL واقعی در گزارش فرستاده نشود.

### ۶.۴ ـ خواندن تنظیم‌های حافظه و persistence Redis

**محل: ترمینال بک‌اند، `/app`**

پیش از استفاده از Redis برای صف، تنظیم‌های فعلی را فقط بخوان؛ این دستور هیچ تنظیمی تغییر نمی‌دهد و چهار گزینهٔ غیرمحرمانه را چاپ می‌کند:

```bash
python manage.py shell -c 'from django.conf import settings; import redis; r=redis.Redis.from_url(settings.REDIS_URL,socket_connect_timeout=5,socket_timeout=5); print(r.config_get("maxmemory","maxmemory-policy","appendonly","appendfsync")); r.close()'
```

خروجی برای انتخاب تنظیم نهایی گزارش شود. برای تخصیص فعلی، هدف پیشنهادی `maxmemory=536870912` (۵۱۲ MiB)، `maxmemory-policy=noeviction`، `appendonly=yes` و `appendfsync=everysec` است؛ این مقادیر هنوز اعمال یا تأیید نشده‌اند. اگر `CONFIG GET` مجاز نبود، خطای مجوز گزارش و تنظیم‌ها از پنل/روش پشتیبانی‌شدهٔ سرویس بررسی شوند. `CONFIG GET *` یا خروجی همهٔ تنظیم‌ها درخواست نمی‌شود، چون ممکن است شامل secret باشد. روش ثبت پایدار تنظیم‌ها پس از دیدن وضعیت واقعی سرویس مشخص می‌شود.

## ۷ ـ worker کنار Django در همان کانتینر بک‌اند

**انتخاب مالک:** worker فعلاً داخل همان سرویس بک‌اند اجرا شود؛ منابع همان سرویس قابل افزایش‌اند. Redis آماده و reference-db به سرویس‌های موجود خود ادامه می‌دهند.

### رفع خطای نسخهٔ کلاینت Redis در worker

در اجرای گزارش‌شدهٔ سرور، transport خطای `Redis transport requires redis-py versions 6.1.0 or later. You have 5.3.1` داد و مدیر پردازه‌ها پس از خروج worker بقیه را متوقف کرد. اتصال مستقیم و cache قبلاً موفق بودند؛ آن دو آزمون سازگاری transport صف را نمی‌سنجیدند. این خطا به نسخهٔ کتابخانهٔ Python مربوط است، نه نسخه یا رمز سرور Redis.

وابستگی‌ها اکنون روی `redis==6.4.0`، `celery[redis]==5.6.3` و `kombu==5.6.2` تثبیت شده‌اند. نصب با extras مخصوص Redis، نیازمندی‌های transport را هم وارد حل وابستگی‌ها می‌کند. `pip check` و `check_queue_dependencies.py` در CI و ساخت image اجرا می‌شوند؛ تست integration نیز ارسال/دریافت/ack پیام، cache و استریم واقعی را با کلیدهای مستقل می‌آزماید. اصلاح قبلی CI هم فهرست دیتابیس تست رسانه را از alias واقعی می‌گیرد تا نبود `reference_search` در CI خطا نسازد.

پس از push همین اصلاح و **ساخت image جدید** در رانفلر، در ترمینال بک‌اند اجرا کن:

```bash
python check_queue_dependencies.py
python manage.py check_search_runtime
```

دستور اول باید نسخه‌های بالا را چاپ کند و دستور دوم باید `model requests=0` بدهد. اجرای این بررسی به مهاجرت جدید یا تغییر secretهای معتبر نیاز ندارد. فعال‌بودن AI Lab و Celery طبق انتخاب مالک حفظ می‌شود؛ آماده‌بودن نسل برداری همچنان با دستورهای مراحل بعد بررسی می‌شود. به‌روزرسانی موقت package داخل کانتینر جای بازسازی image را نمی‌گیرد.

### ۷.۱ ـ انتشار کد و انتخاب نقش

ابتدا کد جدید باید در main کامیت، push و در سرویس بک‌اند Deploy شود. نقش `web-with-ai-worker` در نسخهٔ قبلی ناشناخته است؛ تنظیم آن پیش از رسیدن کد جدید باعث خطای `invalid SERVICE_ROLE` می‌شود. فایل‌های این تغییر برای کامیت آماده‌اند؛ push و Deploy بر عهدهٔ مالک و هنوز تأیید نشده‌اند.

پس از رسیدن کد جدید، این متغیرها در **همان سرویس بک‌اند** تنظیم شوند؛ تنظیم‌های معتبر PostgreSQL، Redis، مدل، پرداخت، ایمیل و secretهای برنامه حفظ می‌شوند:

```dotenv
SERVICE_ROLE=web-with-ai-worker
APP_SERVER=asgi
WEB_CONCURRENCY=1
AI_LAB_WORKER_CONCURRENCY=1
AI_LAB_WORKER_SHUTDOWN_SECONDS=60
AI_LAB_EXECUTOR=celery
CELERY_RUN_TASKS_IN_REQUEST=False
CELERY_TASK_ALWAYS_EAGER=False
READINESS_REQUIRE_BROKER=True
AI_LAB_MAX_CONCURRENT_JOBS=1
AI_LAB_ENABLED=True
```

فعال‌بودن فلگ به‌تنهایی آماده‌بودن نسل برداری را ثابت نمی‌کند؛ تا انتقال و فعال‌سازی نسل معتبر، درخواست ممکن است خطای آمادگی بگیرد. بررسی‌های freshness، اعتبار و دسترسی حفظ شده‌اند. این نقطهٔ شروع، یک جست‌وجوی هم‌زمان را می‌پذیرد؛ افزایش ظرفیت بعد از مشاهدهٔ مصرف حافظه، CPU و محدودیت provider انجام می‌شود. RAM/CPU فعلی بک‌اند هنوز گزارش نشده و عدد قطعی برای ظرفیت آن اندازه‌گیری نشده است. پردازه‌های worker از منابع همان بک‌اند مصرف می‌کنند.

### ۷.۲ ـ رفتار راه‌اندازی و توقف

`docker-start.sh` migrationها و آماده‌سازی را یک بار انجام می‌دهد، سپس `container_runtime.py` سه پردازه را مدیریت می‌کند:

| پردازه | وظیفه |
|---|---|
| وب | اجرای `web-start.sh`؛ ASGI یا Gunicorn با تنظیم قبلی |
| `search-worker` | فقط صف `ai_search`، با concurrency انتخابی |
| `platform-worker` | صف‌های `default,events,maintenance` با concurrency برابر ۱؛ ایمیل بازیابی رمز و اعلان پشتیبانی پشت جست‌وجوی طولانی نمی‌مانند |

هر worker یک پردازهٔ Celery با pool پیش‌فرض prefork دارد؛ فرزندان اجرای task نیز در مصرف حافظه حساب می‌شوند. صف `ai_indexing` خودکار مصرف نمی‌شود؛ ساخت/انتقال فعلی ایندکس با دستورهای مدیریت این راهنما انجام می‌شود. حالت‌های قدیمی `web` و `ai-search-worker` برای اجرای جدا نیز حفظ شده‌اند.

Tini در image، سیگنال توقف را به مدیر پردازه‌ها می‌رساند و فرزندان یتیم را جمع می‌کند. خروج غیرمنتظرهٔ هر پردازه، حتی با کد صفر، باعث توقف بقیه و خروج ناموفق مدیر می‌شود تا وب با worker مرده به سرویس‌دهی ادامه ندهد. در توقف عادی، SIGTERM به والدها ارسال می‌شود تا Celery فرصت پایان کار داشته باشد؛ پس از مهلت تعیین‌شده، پردازه‌های باقی‌مانده و فرزندانشان پایان اجباری می‌یابند. مهلت واقعی میزبان نیز باید فرصت توقف کانتینر را بدهد. `AI_LAB_WORKER_SHUTDOWN_SECONDS` فقط مهلت **توقف کانتینر** است و زمان اجرای عادی سرچ را محدود نمی‌کند. [مدیریت چند پردازه در Docker](https://docs.docker.com/engine/containers/multi-service_container/)، [توقف worker در Celery](https://docs.celeryq.dev/en/stable/userguide/workers.html#stopping-the-worker)

### ۷.۳ ـ منبع مشترک و آزمون واقعی

در این حالت، API و worker همان mount بک‌اند در `/sd/uptodate`، محیط و تنظیم‌های اتصال را به ارث می‌برند؛ سرویس و دیسک جدا برای worker ساخته نمی‌شود. pin منبع SQLite همچنان بررسی می‌شود و مسیر فایل‌های سرور باید معتبر باشد.

**محل: همان ترمینال بک‌اند، پس از Deploy نقش جدید**

```bash
python manage.py shell -c 'from apps.ai_lab.reference_index import source_stamp; s=source_stamp(); print(s.backend, s.identity, s.revision)'
python manage.py check_search_runtime
```

خروجی موفق آزمون دوم:

```text
Redis stream and separate Celery worker passed; model requests=0.
```

واژهٔ `separate` در این خروجی به پردازهٔ مستقل Celery اشاره دارد؛ لازم نیست کانتینر جدا باشد. آزمون، Redis Streams و اجرای task در worker مستقل را با درخواست ازپیش‌لغوشده بررسی می‌کند و API مدل را صدا نمی‌زند. انتشار عمومی سرچ و انتقال بردارها هنوز مراحل بعدی‌اند.

## ۸ ـ تنظیم مدل و embedding

**محل: پنل همان بک‌اند؛ workerهای داخل کانتینر همین محیط را به ارث می‌برند**

```dotenv
AI_LAB_ENABLED=True
AI_LAB_SEARCH_ENGINE=hybrid
AI_LAB_LOCAL_LEXICAL_PILOT=False
AI_LAB_ROLLOUT_PERCENT=0
AI_LAB_STREAM_ANSWER_DRAFTS=False
AI_LAB_MODEL=gpt-6-luna
AI_LAB_BASE_URL=https://api.gapgpt.app/v1
AI_LAB_REASONING_EFFORT=none
AI_LAB_EMBEDDING_BACKEND=openai
AI_LAB_EMBEDDING_REMOTE_ENABLED=True
AI_LAB_EMBEDDING_MODEL=text-embedding-3-small
AI_LAB_EMBEDDING_BASE_URL=https://api.gapgpt.app/v1
AI_LAB_EMBEDDING_DIMENSIONS=1536
AI_LAB_EMBEDDING_REVISION=1
AI_LAB_EMBEDDING_USE_CHAT_KEY=False
```

دو secret مستقل:

| کلید | منبع |
|---|---|
| `AI_LAB_API_KEY` | کلید chat معرفی‌شده در فایل خصوصی مالک |
| `AI_LAB_EMBEDDING_API_KEY` | کلید مستقل خریداری‌شدهٔ embedding |

فایل‌های کلید دسکتاپ در image کپی نمی‌شوند. `none` تنظیم لوکال بررسی‌شده است؛ `low` را بعداً می‌توان با همان متغیر reasoning آزمایش کرد. مدل و Base URL پاسخ‌گو قابل تنظیم‌اند. مشخصات embedding باید دقیقاً با profile بردارهای موجود برابر بمانند؛ مقدار پیش‌فرض 768 ابعاد در بعضی templateهای قدیمی برای این نسل مناسب نیست.

## ۹ ـ schema و قطعات متن روی سرور

**محل: ترمینال بک‌اند، `/app`؛ قبل از تغییر schema، پشتیبان موجود برنامه حفظ/تهیه شود**

```bash
python manage.py migrate
python manage.py migrate --database reference_search
python manage.py migrate ai_feedback --database ai_feedback
python manage.py build_reference_index --status
```

اگر خروجی آخر `Ready generation=...` برای منبع فعلی است، همان متن آماده را حفظ کن. در صورت نبود نسل سازگار:

```bash
python manage.py build_reference_index --workers 1 --batch-size 20
```

`UPTODATE_DB_DIR=/sd/uptodate` باید به فایل‌های واقعی سرور اشاره کند؛ برای MySQL، تنظیم منبع مشترک خودش استفاده می‌شود. فقط تغییر مسیر پوشه یا وجود فایل‌ها، ساخت آمادهٔ سازگار را ثابت نمی‌کند.

سپس:

```bash
python manage.py build_hybrid_index
python manage.py build_hybrid_index --status
```

**UUID نسل جدیدی که در همین سرور چاپ شد را نگه دار.** در ادامه هر `SERVER_GENERATION_UUID` باید با این مقدار جایگزین شود، نه UUID لپ‌تاپ. اگر build قطع شد، همان نسل با `--resume SERVER_GENERATION_UUID` ادامه می‌یابد؛ ساخت تازهٔ تکراری لازم نیست.

تا اینجا API embedding برای corpus صدا زده نشده است. `migrate` فقط schema و `build_hybrid_index` متن/تگ/قطعات را آماده می‌کنند.

## ۱۰ ـ خروجی بردارهای موجود از لپ‌تاپ

**محل: لپ‌تاپ؛ این دستورات در ترمینال رانفلر اجرا نمی‌شوند**

```bash
cd '/home/amir/Documents/Learning Platform/backend'
.venv/bin/python manage.py export_hybrid_vectors 73f89df9-d447-4cb7-a32c-f8296b81fa4b --output .private/uptodate-small-1536.jsonl.gz
sha256sum .private/uptodate-small-1536.jsonl.gz
```

نسل کامل فعلی ۶۷۰٬۹۹۱ بردار small با ۱۵۳۶ بُعد دارد. export به‌صورت batch و foreground است، API صدا نمی‌زند و فایل 0600 تولید می‌کند. آرشیو، کاربران، متن مقاله، کلید API یا شناسهٔ paragraph لوکال را منتقل نمی‌کند.

فایل موجود بازنویسی نمی‌شود. پس از خطای کنترل‌شده/Ctrl+C فایل ناقص پاک می‌شود؛ قطع اجباری سیستم ممکن است فایل ناقص باقی بگذارد. فایل بدون پایان معتبر منتقل نشود و برای export دوباره نام تازه انتخاب شود. هیچ دستور ساختی با `&`، `nohup` یا اجرای مخفی در این روند نیست.

## ۱۱ ـ انتقال فایل و import بردارها

فایل export را با File Manager یا روش upload خصوصیِ پشتیبانی‌شدهٔ حساب به دیسک پایدار **بک‌اند**، مثلاً مسیر زیر منتقل کن:

```text
/sd/ai-transfer/uptodate-small-1536.jsonl.gz
```

سقف اندازه/روش upload فایل چندگیگابایتی این حساب هنوز تأیید نشده است. اگر File Manager آن را نمی‌پذیرد، روش CLI یا انتقال خصوصی مناسب حساب باید مشخص شود. فایل در Git، image Docker یا مسیر دانلود عمومی کاربران قرار نمی‌گیرد.

**محل: ترمینال بک‌اند**

```bash
sha256sum /sd/ai-transfer/uptodate-small-1536.jsonl.gz
```

checksum باید دقیقاً با لپ‌تاپ برابر باشد. فضای فایل انتقال را جدا از فضای داده/WAL/index PostgreSQL حساب کن.

### فقط بررسی، بدون درج بردار

```bash
python manage.py import_hybrid_vectors SERVER_GENERATION_UUID --input /sd/ai-transfer/uptodate-small-1536.jsonl.gz --verify-only
```

profile، chunker، تعداد، ترتیب قطعه‌ها، hashها، ابعاد/اعداد و checksum باید معتبر باشند. اختلاف شناسه‌های ردیف و مسیر دو محیط مجاز است؛ اختلاف متن/ورودی یا profile خطاست. در mismatch، علت بررسی شود و embedding جدید خودکار خریداری نشود.

### import و ساخت HNSW مقصد

```bash
PGOPTIONS='-c max_parallel_maintenance_workers=0 -c maintenance_work_mem=512MB' python manage.py import_hybrid_vectors SERVER_GENERATION_UUID --input /sd/ai-transfer/uptodate-small-1536.jsonl.gz --build-index
```

ساخت سریالی برای محدودیت shared memory انتخاب شده است. RAM هشت‌گیگابایتی پیش‌نیاز نیست، ولی زمان ساخت و کارایی روی ظرفیت فعلی باید سنجیده شوند. این مرحله هزینهٔ API embedding ندارد؛ مصرف دیسک/CPU و زمان دارد.

import قبل از اولین write کل آرشیو را بررسی می‌کند و هنگام درج دوباره اعتبار آن را می‌سنجد. batchها commit می‌شوند؛ اجرای دوبارهٔ همان فرمان پس از قطع، بردارهای مطابق را reuse می‌کند. نسل فعال عوض نمی‌شود. در خطا، نسل کامل و آماده علامت نمی‌خورد. **برای انتقال، `embed_hybrid_index` اجرا نمی‌شود**؛ آن فرمان می‌تواند API پولی را صدا بزند.

## ۱۲ ـ فعال‌سازی، رسانه و آزمون مدیر

**محل: ترمینال بک‌اند، پس از import/index موفق**

```bash
python manage.py activate_hybrid_index SERVER_GENERATION_UUID
python manage.py build_reference_media --workers 1
python manage.py build_reference_media --status
python manage.py check_search_runtime
```

ساخت metadata رسانه هزینهٔ مدل ندارد. ابزار فعال‌سازی فقط نسل کامل، سازگار و دارای بردار/ایندکس آماده را می‌پذیرد.

**محل: پنل همان بک‌اند در حالت ترکیبی**

اکنون `AI_LAB_ENABLED=True` بگذار، `AI_LAB_ROLLOUT_PERCENT=0` را نگه دار و همان سرویس بک‌اند را با محیط یکسان برای همهٔ پردازه‌ها اعمال/راه‌اندازی مجدد کن. ASGI بک‌اند (`APP_SERVER=asgi`) برای استریم استفاده می‌شود.

**محل: مرورگر/اپ سرور**

- `/api/v1/health/` و `/api/v1/ready/` سالم باشند.
- مدیر بتواند سؤال بدهد و منبع مستقیم و پاسخ فارسی را ببیند.
- جدول/تصویر، پاسخ ناقص، بازخورد و اعتبار با حساب آزمایشی بررسی شوند.
- پراکسی باید استریم را بدون buffering طولانی عبور دهد.

آزمون‌های زیر درخواست پولی کوچک دارند و فقط پس از آمادگی تنظیمات اجرا می‌شوند:

```bash
python manage.py check_search_model
python manage.py check_embedding_provider
```

مدیر و شناسه‌های صریح `AI_LAB_USER_IDS` برای تست محدود هستند. افزایش صرف درصد rollout، گیت انتشار معتبر را جایگزین نمی‌کند. انتشار عمومی، بازبینی بالینی، تعرفهٔ اعتبار در `/manage/app/search-credit/` و ظرفیت هم‌زمانی پس از آزمون سرور بررسی شوند. رسیدن پاسخ کامل به زیر ۲۰ ثانیه روی سرور هنوز اثبات نشده است.

## خطاهای مهم همین روند

| خطا | اقدام |
|---|---|
| `superuser password is not specified` | secret سرویس reference-db برای اولین initialization لازم است؛ trust عمومی جایگزین آن نیست |
| `database ... does not exist` | فهرست databaseها در همان reference-db بررسی و فقط نام لازم داخل آن ساخته شود؛ سرویس یا فایل جدید لازم نیست |
| `pg_isready ... accepting connections` | شبکه و پاسخ‌گویی سرور تأیید شده‌اند؛ صحت رمز هنوز معلوم نیست |
| `password authentication failed` | بخش صفر، تنظیم رمز واقعی با `\password`، آزمون `psql -W` از بک‌اند و سپس ساخت URL جدید |
| `reference_search` شناخته نمی‌شود | وجود متغیر اتصال، اجرای جدید بک‌اند و نسخهٔ کد دارای alias بررسی شود |
| `SOURCE_FILES_MISSING` | مسیر واقعی snapshot یا تنظیم MySQL بررسی شود |
| `REFERENCE_INDEX_STALE` یا mismatch پروفایل/ورودی | pin منبع، profile و hashها بررسی شوند؛ کنترل سازگاری حذف نمی‌شود |
| worker پاسخ نمی‌دهد | صف `ai_search`، broker، رمزهای مشترک و وضعیت پردازه بررسی شوند |

تغییر رمز با `\password` در [مستند psql](https://www.postgresql.org/docs/17/app-psql.html) و رفتار initialization در [مستند image PostgreSQL](https://hub.docker.com/_/postgres) توضیح داده شده‌اند. شبکهٔ داخلی در [مستند رانفلر](https://docs.runflare.com/general/network-settings/) آمده است.

### حدود تأیید این فایل

ساخت دیتابیس، نصب vector، نام شبکه، تست شبکه، اتصال `psql` با رمز، اتصال alias خود Django، اعمال هر پنج migration اپ جست‌وجو و ساخت/اتصال/migration دیتابیس بازخورد بر اساس خروجی‌های مالک ثبت شدند. مسیر داخلی Redis روی `ai-redis-yum-service:6379` از بک‌اند با کاربر `default` و رمز پاسخ `PONG` داد و نسخهٔ `8.4.0` گزارش شد. رفع override برابر `CACHE_LOCATION` و کارکرد هر سه cache در Django نیز پس از Redeploy تأیید شدند. آزمون مستقل broker و استریم، تنظیم‌های persistence/حافظه/eviction و راه‌اندازی worker هنوز تأیید نشده‌اند. شاخهٔ Docker قبلی با کامیت `0ae2460` فقط برای سابقه محفوظ است و در مسیر جاری استفاده نمی‌شود. آزمون عملی ثبت بازخورد، سلامت HTTP، تنظیم و اجرای Redis و worker، اشتراک snapshot، روش upload حجیم و انتقال کامل هنوز روی این سرور انجام/تأیید نشده‌اند. حالت اجرای worker کنار بک‌اند در کد آماده شده و آزمون‌های مدیریت پردازهٔ آن موفق‌اند؛ ساخت image جدید و اجرای واقعی این حالت روی رانفلر هنوز تأیید نشده‌اند. آزمون‌های محلی قبلیِ ابزار انتقال و سرچ، تأیید خودکار این مراحل روی رانفلر نیستند. به‌روزرسانی این فایل هیچ تغییری روی سرور اعمال نکرده است.
