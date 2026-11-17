# گزارش رخدادها و خطاهای استقرار سرچ هوشمند روی رانفلر

آخرین به‌روزرسانی: ۲۰۲۶-۱۱-۱۸

این سند سابقهٔ استقرار، خروجی‌های گزارش‌شدهٔ مالک و نتیجهٔ عیب‌یابی را نگه می‌دارد. مسیر اجرای مراحل در [راهنمای ۴۷](47-smart-search-server-step-by-step.fa.md) و جزئیات اولیهٔ زیرساخت در [سند ۴۶](46-smart-search-runflare-deployment.fa.md) است. ثبت یک دستور یا پیشنهاد در این گزارش به معنی اجرای آن روی سرور نیست. نتیجهٔ تأییدنشده صریحاً مشخص شده است؛ رمز، URL حاوی رمز و کلید API در گزارش ثبت نشده‌اند.

## وضعیت قطعی در پایان گزارش

| مورد | آخرین نتیجهٔ گزارش‌شده |
|---|---|
| نسل مقصد روی سرور | `b9bbb29c-bada-4f94-803f-54cfce8f5058` |
| بردارهای مورد انتظار | `670991` |
| بردارهای ذخیره‌شده برای همین نسل و profile | `670991`؛ ورود کامل بردارها تأیید شده است |
| ابعاد embedding | `1536` |
| پیشوند شناسهٔ profile | `efdd6c8d9d27`؛ شناسهٔ کامل از `g.embedding_profile["id"]` خوانده می‌شود |
| نام HNSW مورد انتظار | `hybrid_hnsw_b9bbb29cbada4f94803f_efdd6c8d9d27` |
| وضعیت HNSW در مقصد جدید | در `pharmenta_reference_recovered`، هر سه `has_metadata`، `indisvalid` و `indisready` برابر `t` گزارش شدند؛ ساخت معتبر تأیید شد |
| OID مقصد جدید | `2575069`؛ filenode/حجم نهایی مقصد جدید هنوز گزارش نشده‌اند |
| شیء ناسازگار قدیمی | OID/filenode برابر `1296045` و حجم `5239.4 MB` متعلق به `pharmenta_reference` قبلی است؛ به مقصد جدید نسبت داده نشود |
| `embedding_ready` / نسل فعال | مالک پس از Redeploy و اجرای فرمان کنترل، در `pharmenta_reference_recovered` هر دو مقدار را `True` گزارش کرد؛ کنترل منبع، profile، تعداد و تعریف ایندکس پیش از فعال‌سازی پاس شده‌اند |
| اجرای ساخت | فهرست پردازهٔ محلی ساخت و نشست ساخت مورد جست‌وجو خالی بودند؛ ساخت زنده در بررسی‌های گزارش‌شده دیده نشد |
| نتیجهٔ بررسی‌ها | نتیجهٔ قدیمی برنامه `VECTOR_AND_HNSW_CHECK: NOT_READY` مربوط به پیش از بازیابی بود؛ بررسی جدید SQL ایندکس معتبر مقصد جدید را تأیید می‌کند، آزمون کامل برنامه پس از اتصال جدید هنوز انجام نشده است |
| وضعیت بکاپ | فایل custom با حجم نمایشی `3.2G` در `/sd/ai-transfer/reference-before-hnsw-repair-20261117T111324Z.dump` برای بازیابی استفاده شد؛ داده‌های نسل هدف و post-data در مقصد جدید تأیید شدند |
| حذف استاندارد شیء ناسازگار | `DROP INDEX IF EXISTS` با `cache lookup failed for index 1296045` شکست خورد؛ حذف انجام نشده است |
| فضای دیسک فعلی دیتابیس | مالک ابتدا `9.5` گیگابایت آزاد اعلام کرد؛ سپس ظرفیت را به `40 GB` افزایش داد و `25 GB` فضای آزاد گزارش کرد. این ظرفیت، بر اساس اندازه‌های ثبت‌شده، برای بازیابی کنار نسخهٔ قبلی حاشیهٔ مناسبی دارد |
| وضعیت بازیابی | شمارش نسل هدف منطبق، post-data موفق، HNSW معتبر و اتصال/فعال‌سازی نسل در مقصد جدید تأیید شدند؛ ANALYZE، آزمون runtime و آزمون واقعی سرچ هنوز نتیجهٔ گزارش‌شده ندارند |

ناهماهنگی اطلاعات داخلی ایندکسِ **دیتابیس قبلی** همچنان در سابقه باقی است و علت اولیهٔ آن معلوم نشده است. مسیر بازیابی، انتقال منطقی داده‌ها به database جدید و ساخت یک ایندکس معتبر در آن بود؛ حذف یا ترمیم مستقیم کاتالوگ قبلی انجام نشده است. تعداد درست بردارها به‌تنهایی اثبات سلامت همهٔ داده‌ها نیست؛ در مقصد جدید علاوه بر شمارش، موفقیت constraintها و پرچم‌های اعتبار/آمادگی HNSW نیز تأیید شده‌اند.

## محیط‌ها و شناسه‌های ثبت‌شده

| محیط / تنظیم | مقدار گزارش‌شده |
|---|---|
| ترمینال بک‌اند | آخرین فعال‌سازی در `pharmenta-backend-yuf-deploy-65c4774cb-pthnn`، مسیر `/app`؛ رخدادهای قبلی عمدتاً در `6c5b6947f8-drjh6` بودند |
| میزبان اتصال PostgreSQL از Django | `reference-db-xoc-service:8000` |
| alias اتصال | `reference_search`؛ در کد از `indexing.alias()` استفاده می‌شود |
| database / user جست‌وجوی فعلی | database برابر `pharmenta_reference_recovered` و user برابر `pharmenta_reference`؛ database قبلی `pharmenta_reference` حفظ شده است |
| کانتینر واقعی دیتابیس در بررسی آخر | `reference-db-ylj-deploy-c94b6455d-gffh5` |
| آدرس سرور در خروجی SQL | `10.244.37.92`؛ این IP مشاهدهٔ همان زمان است، نشانی ثابت اتصال نیست |
| نسخهٔ PostgreSQL در لاگ | `17.12 (Debian 17.12-1.pgdg12+1)` |
| نسخهٔ vector تأییدشده | `0.8.7` |
| مسیر دادهٔ سرور | `/var/lib/postgresql/data/pgdata` |
| محل mount پایدار دیتابیس | `/var/lib/postgresql/data` |
| محل فایل‌های انتقال و لاگ بک‌اند | `/sd/ai-transfer/` |

تفاوت پسوند نام سرویس شبکه (`xoc`) و نام Pod (`ylj`) به‌تنهایی نشانهٔ اتصال به دیتابیس اشتباه نبود. اتصال Django، `inet_server_addr()` و خواندن `/etc/hostname` از سمت سرور دیتابیس، مقصد واقعی بالا را نشان دادند. مسیر PGDATA در کانتینر بک‌اند وجود ندارد؛ دستورهای بررسی دیسک و cgroup هر کانتینر، فقط منابع همان کانتینر را نشان می‌دهند.

## رخدادهای پیشین آماده‌سازی زیرساخت

این بخش خلاصهٔ سابقهٔ موجود در راهنمای ۴۷ است. برای همهٔ موارد زمان دقیق یا لاگ خام در گفتگو موجود نیست؛ خطاهای صرفاً احتمالیِ جدول عیب‌یابی آن راهنما، رخداد قطعی جدید محسوب نشده‌اند.

| موضوع | اتفاق و اقدام ثبت‌شده | حد تأیید |
|---|---|---|
| انتخاب Dockerfile و شاخه | سرویس دیتابیس به Dockerfile ریشهٔ شاخهٔ `deploy-reference-db` نیاز داشت؛ Dockerfile ریشهٔ `main` متعلق به بک‌اند بود. شاخهٔ آماده‌شده `212df0a` و شاخهٔ قدیمی `0ae2460` در سابقه آمده‌اند | انتخاب شاخه، شبکه و ساخت دیتابیس در گزارش‌های بعدی تأیید شدند |
| دیتابیس منطقی مورد انتظار | خطای `database ... does not exist` در سند ۴۶ ثبت شد؛ بررسی فهرست databaseها و ساخت فقط database لازم داخل سرویس موجود، مسیر اصلاح بود | در ۱۵ نوامبر، `pharmenta_reference` و vector نسخهٔ `0.8.7` از بک‌اند خوانده شدند |
| خطای رمز و توقف startup بک‌اند | `password authentication failed` هنگام migration اتصال جست‌وجو، راه‌اندازی بک‌اند را متوقف کرد. راهنمای بازیابی شامل برداشتن موقت URL جست‌وجو، یکسان‌کردن رمز نقش با `\password`، آزمون `psql -W` و ساخت URL با encoding صحیح بود | علت دقیق اختلاف رمز نقش و URL مشخص نشد؛ اتصال `psql` و سپس alias خود Django در ۱۵ نوامبر موفق شدند |
| migrationها | هر پنج migration اپ `ai_retrieval` از `0001` تا `0005` با `[X]` گزارش شدند. database بازخورد `pharmenta_ai_feedback` و migration آن از alias برابر `ai_feedback` تأیید شدند | آماده‌سازی schema تأیید شده؛ آزمون عملی ثبت بازخورد جداست |
| Redis و override نامعتبر cache | خطای `Redis URL must specify one of the following schemes (redis://, rediss://, unix://)` هنگام parse آدرس cache رخ داد. مالک `CACHE_LOCATION` را حذف و Redeploy کرد | خروجی `{'default': True, 'throttle': True, 'ai_lab': True}` تأیید شد؛ اتصال مستقیم Redis نیز `PONG` و نسخهٔ `8.4.0` داد |
| ناسازگاری کتابخانهٔ worker | خطای `Redis transport requires redis-py versions 6.1.0 or later. You have 5.3.1` باعث خروج worker و توقف دیگر پردازه‌ها توسط مدیر کانتینر شد | اصلاح وابستگی‌ها با `redis==6.4.0`، `celery[redis]==5.6.3`، `kombu==5.6.2` و کنترل transport در build/CI در کد آماده شد. لاگ‌های بعدی دریافت و اجرای task را نشان دادند؛ آزمون مستقل کامل runtime هنوز گزارش نشده است |
| قفل ساخت متن/قطعات | `REFERENCE_INDEX_BUILD_BUSY` هنگام ادامهٔ ساخت و نیاز به حفظ UUID قبلی در راهنما ثبت شد؛ قفل به‌تنهایی پیشرفت را نشان نمی‌داد | ساخت کامل متن/قطعات hybrid، آزاد بودن قفل آن مرحله و UUID مقصد در گزارش ۱۶ نوامبر ثبت شدند |
| انتقال آرشیو حجیم | فایل کامل به ۱۰ قطعه تقسیم و روی سرور متصل شد؛ ابزار مستقل همراه قطعه‌ها استفاده شد | upload ده قطعه و اتصال با checksum منطبق در گزارش ۱۶ نوامبر تأیید شدند |
| ادامهٔ import و verify تکراری | پس از ثبت `247040` بردار، ادامه با همان نسل و گزینهٔ `--skip-verify` پیگیری شد. آخرین شمارندهٔ میانیِ سند قبلی `checked=621312, expected=670991` بود | خروجی‌های بعدی تعداد کامل `670991` بردار را تأیید کردند؛ آن شمارنده‌های میانی دیگر وضعیت نهایی نیستند |

آرشیو منتقل‌شده `5515938591` بایت بود؛ SHA-256 فایل کامل:

```text
ac530b27ca626bccdcd64983de7b9728827785ca06e905536e25847ff9fea213
```

نسل مبدأ لپ‌تاپ `73f89df9-d447-4cb7-a32c-f8296b81fa4b` بود؛ مقصد سرور UUID متفاوتِ ابتدای همین گزارش را دارد. این تفاوت شناسه در مسیر انتقال ثبت شده بود و به‌تنهایی خطا نبود.

مواردی مثل `superuser password is not specified`، `invalid SERVICE_ROLE`، `SOURCE_FILES_MISSING` و mismatch پروفایل در راهنمای ۴۷ به‌عنوان عیب‌یابی یا هشدار اجرایی آمده‌اند؛ در شواهد این گزارش، وقوع مستقل همهٔ آن‌ها تأیید نشده است. پیام‌های تنظیم اعتبار/موتور جست‌وجو نیز در راهنمای ۴۷ و [سند ۴۱](41-smart-search-credits.fa.md) حفظ شده‌اند و علت اثبات‌شدهٔ شکست HNSW نیستند.

## تلاش اول HNSW و بسته‌شدن ترمینال

مالک اعلام کرد verify و import با موفقیت انجام شده و هنگام اجرای HNSW، ترمینال خودبه‌خود بسته شده است. علت بسته‌شدن ترمینال مشخص نشد. بررسی بعدی نشان داد تعداد بردارها کامل است و ساخت هنوز در PostgreSQL اجرا می‌شود:

```text
EXPECTED_VECTORS: 670991
STORED_VECTORS: 670991
EMBEDDING_READY: False
ACTIVE: False
pid: 8125
phase: building index: loading tuples
blocks_done: 7364
blocks_total: 17658
phase_percent: 41.70
indisvalid: False
indisready: False
```

نمونهٔ بعدی همان PID، `7555 / 17658` و `42.79%` را نشان داد؛ در آن فاصله ساخت پیشرفت داشت. این درصد مربوط به همان مرحله و شمارندهٔ بلوک‌هاست؛ تخمین قطعی زمان پایان یا درصد کل عملیات نیست. خالی بودن `wait_event_type` و `wait_event` نیز در خروجی ثبت شد.

بعدتر پرس‌وجوی پیشرفت صفر ردیف برگرداند و بررسی ایندکس، حجم `2300 MB` با هر دو پرچم `False` را نشان داد. حذف ردیف از نمای پیشرفت، به‌تنهایی موفقیت ساخت را ثابت نکرد؛ پایان موفق این تلاش ثبت نشد.

## اجرای پس‌زمینه، اجرای تکراری و خطای سهمیهٔ دیسک

برای مستقل‌کردن تلاش بعدی از ترمینال، دستور `nohup python -u manage.py shell -c ...` با لاگ زیر اجرا شد:

```text
/sd/ai-transfer/hnsw-rebuild-b9bbb29c.log
```

دستور شامل گرفتن قفل `hybrid-embed:<UUID>`، کنترل فعال‌نبودن نسل، بررسی `_source(g)`، تطبیق تعداد بردارها و اجرای `vectors.create_index(g, profile)` بود. تنظیم‌های session گزارش‌شده:

```text
maintenance_work_mem = 512MB
max_parallel_maintenance_workers = 0
statement_timeout = 0
lock_timeout = 30s
application_name = pharmenta-hnsw-rebuild-b9bbb29c
```

سه شروع در لاگ دیده شد؛ زمان‌های زیر UTC هستند:

| زمان | نتیجه |
|---|---|
| `2026-11-16 20:29:02.748590+00:00` | `HNSW_PREFLIGHT` |
| `2026-11-16 20:29:03.348470+00:00` | `HNSW_START`؛ تلاش اول وارد مرحلهٔ ساخت شد |
| `2026-11-16 20:29:31.971940+00:00` | تلاش تکراری در گرفتن قفل با `REFERENCE_INDEX_BUILD_BUSY` متوقف شد |
| `2026-11-16 20:29:46.096097+00:00` | تلاش تکراری بعدی نیز با همان خطای قفل متوقف شد |

قفل این مرحله از `reference_index.acquire_build_lock()` و اتصال پیش‌فرض/اصلی برنامه گرفته می‌شود؛ محل ساخت HNSW اتصال `reference_search` است. در نتیجه بررسی صرفِ نشست‌های دیتابیس برداری، همهٔ اطلاعات صاحب قفل برنامه را نشان نمی‌دهد. داشتن قفل نیز به‌تنهایی شاخص میزان پیشرفت نیست.

خروج `Exit 1` تلاش‌های تکراری به معنی شکست هم‌زمان تلاش اول نبود. نمونهٔ بعدی PostgreSQL نشان داد PID برابر `50`، پس از `00:03:04.7872` در حال `CREATE INDEX CONCURRENTLY` بود و `1452 / 17658`، معادل `8.22%` پیشرفت داشت. این ایندکس روی `ai_retrieval_chunk_vector` با HNSW و `embedding::vector(1536)` ساخته می‌شد.

سپس خطای قطعی زیر در همان لاگ ثبت شد:

```text
psycopg.errors.InternalError_: could not write to file "pg_wal/xlogtemp.50": Disk quota exceeded
django.db.utils.InternalError: could not write to file "pg_wal/xlogtemp.50": Disk quota exceeded
```

محل شکست، `vectors.create_index()` و اجرای `CREATE INDEX CONCURRENTLY` بود. این خطا، شکست آن تلاش به علت ناتوانی در نوشتن WAL به دلیل سهمیهٔ دیسک را تأیید می‌کند؛ از آن نمی‌توان علت همهٔ توقف‌های بعدی را نتیجه گرفت.

در همان دوره، اتصال `reference-db-xoc-service:8000` ابتدا `Connection refused` و `pg_isready` خروجی `no response` داد. در بررسی بعدی `accepting connections` گزارش شد. بعد از بازگشت اتصال، وضعیت چنین بود:

```text
expected_vectors = 670991
stored_vectors = 670991
embedding_ready = f
index_valid = f
index_ready = f
index_size = 5239 MB
```

## حذف موفق ایندکس نامعتبر و اندازه‌گیری فضا

مالک در این مرحله دستور زیر را اجرا کرد و خروجی `DROP INDEX` گرفت:

```sql
DROP INDEX CONCURRENTLY IF EXISTS hybrid_hnsw_b9bbb29cbada4f94803f_efdd6c8d9d27;
```

این **حذف موفقِ همان مرحله** است؛ نباید آن را حذف شیء ناسازگارِ کشف‌شده در پایان گزارش محسوب کرد. بعد از آن، خروجی ظرفیت منطقی دیتابیس و WAL چنین بود:

```text
database_size = 9480 MB
wal_size = 640 MB
max_wal_size = 1GB
archive_mode = off
pg_replication_slots = 0 rows
```

مالک ابتدا حدود ۵ گیگابایت و بعد «دقیقاً ۱۵ گیگابایت فضای خالی» اعلام کرد. نمونهٔ بعدی `df` در کانتینر واقعی دیتابیس وضعیت متفاوتِ همان زمان را ثبت کرد:

```text
volume size = 25G
used = 16G
available = 9.6G
use = 62%
mount = /var/lib/postgresql/data
base = 15G
pg_wal = 1.1G
```

این اعداد مربوط به زمان‌های مختلف‌اند؛ «۱۵ گیگابایت آزاد» آخرین فضای اندازه‌گیری‌شده محسوب نمی‌شود. خروجی `max_wal_size` هم به‌تنهایی فضای آزاد کافی برای ساخت را اثبات نکرده بود.

## تلاش مجدد ۱۷ نوامبر و ناپدیدشدن پردازهٔ ساخت

لاگ تلاش مجدد در مسیر زیر گزارش شد:

```text
/sd/ai-transfer/hnsw-retry-b9bbb29c-20261117.log
```

آخرین خطوط مشاهده‌شدهٔ این لاگ:

```text
HNSW_PREFLIGHT 2026-11-17T04:48:44.927305+00:00
HNSW_START 2026-11-17T04:48:45.404732+00:00
```

در خروجی ارائه‌شده، `HNSW_READY`، traceback پایانی یا کد خروج این تلاش وجود نداشت. پرس‌وجوی پیشرفت و سپس نشست‌های دارای `application_name` تعیین‌شده، صفر ردیف برگرداندند. بررسی `/proc` همان کانتینر بک‌اند نیز داد:

```text
CONTAINER: pharmenta-backend-yuf-deploy-6c5b6947f8-drjh6
RUNNING_BUILD_PIDS: []
```

شمار بردارها همچنان کامل بود؛ بررسی مبتنی بر `pg_index`، `index_valid`، `index_ready` و `index_size` را خالی نشان می‌داد. نبود پردازه و نبود پرچم‌های موفقیت، پایان موفق HNSW را تأیید نکرد. علت دقیق پایان پردازهٔ این تلاش از لاگ موجود قابل تعیین نیست.

محدودیت روش اجرا نیز ثبت می‌شود: `nohup` برای جداکردن اجرای shell از ترمینال استفاده شد؛ ماندگاری پردازه پس از restart یا حذف خود کانتینر را تضمین نمی‌کند. علت پایان این تلاش با مشاهدهٔ صرفِ `nohup` یا نبود traceback قابل تعیین نبود.

## قطع غیرعادی PostgreSQL و خطای فایل `postmaster.pid`

لاگ‌های دیتابیس توالی زیر را ثبت کردند. همهٔ زمان‌های این بخش UTC و مربوط به `2026-11-17` هستند:

| زمان | رویداد ثبت‌شده |
|---|---|
| `08:59:50.222` | شروع PostgreSQL `17.12` |
| `08:59:50.259` | `database system was interrupted; last known up at 2026-11-17 08:39:00 UTC` |
| `08:59:51.834` | `database system was not properly shut down; automatic recovery in progress` |
| `08:59:53.762` | پایان checkpoint بازیابی |
| `08:59:53.780` | `database system is ready to accept connections` و سپس `could not open file "postmaster.pid": No such file or directory` |
| `09:00:53.836` | تکرار نبود فایل PID؛ `performing immediate shutdown because data directory lock file is invalid` و `received immediate shutdown request` |
| `09:00:53.860` | `database system is shut down` |
| `09:00:55.239` | شروع مجدد PostgreSQL |
| `09:00:55.341` | بازیابی خودکار پس از خاموش‌شدن نامناسب |
| `09:00:55.362` | `invalid record length at 8/9B000108: expected at least 24, got 0`؛ سپس `redo done` |
| `09:00:55.397` | checkpoint بازیابی کامل شد |
| `09:00:55.405` | سرور آمادهٔ پذیرش اتصال شد |

در SQL ساعت `09:39:09.983545+00`، مقدار `pg_postmaster_start_time()` برابر `2026-11-17 09:00:55.278538+00` بود و این شروع مجدد را تأیید کرد. لاگ `Skipping initialization` هم نشان داد مسیر دارای دیتابیس موجود تشخیص داده شده است.

نبود فایل `postmaster.pid` و خاموش‌شدن ناشی از نامعتبر بودن فایل قفل، در لاگ قطعی‌اند. عامل حذف یا ناپدیدشدن فایل مشخص نشده است. اجرای هم‌زمان چند PostgreSQL روی PGDATA مشترک، تغییر mount، دخالت اسکریپت یا اشکال پلتفرم در گفتگو مطرح شدند، اما هیچ‌کدام اثبات نشدند. پیام `invalid record length` به‌تنهایی اثبات خرابی داده نبود؛ در همان توالی، بازیابی و startup کامل شدند.

## تشخیص‌هایی که در کانتینر اشتباه اجرا شدند

مالک دستور بررسی PGDATA و `psql` محلی را در ترمینال **بک‌اند** اجرا کرد. خروجی‌ها:

```text
df: /var/lib/postgresql/data: No such file or directory
du: cannot access '/var/lib/postgresql/data/pgdata/base': No such file or directory
du: cannot access '/var/lib/postgresql/data/pgdata/pg_wal': No such file or directory
psql: connection to server on socket "/var/run/postgresql/.s.PGSQL.8000" failed: No such file or directory
```

این خطاهای محلی، نبودن فایل‌های PostgreSQL یا خاموش‌بودن دیتابیس راه‌دور را ثابت نمی‌کردند. خروجی دیسک ریشهٔ بک‌اند `876G / 312G used / 520G available` بود؛ این فضا، سهمیهٔ volume دیتابیس نبود. `/dev/shm` بک‌اند نیز `64M` بود و برای تشخیص shared memory دیتابیس کافی نبود.

برخی متن‌های paste‌شدهٔ shell در گفتگو پایان‌های درهم‌رفته‌ای مثل `SHLRE ...` یا `PY ...` داشتند. از نمایش متن ترمینال به‌تنهایی نمی‌توان اجرای صحیح همهٔ خطوط را نتیجه گرفت؛ در این گزارش فقط خروجی‌های قابل مشاهده، اجرای تأییدشده محسوب شده‌اند. خرابی paste علت اثبات‌شدهٔ شکست ساخت داخل PostgreSQL نبود.

بررسی حافظه در بک‌اند چنین بود:

```text
memory.current = 391479296
memory.max = 5114953728
memory.peak = 454914048
memory.events: low 0, high 0, max 0, oom 0, oom_kill 0, oom_group_kill 0
```

سپس با اتصال Django و خواندن فایل‌های سمت سرور، کانتینر واقعی دیتابیس بررسی شد:

```text
memory.max = 5125439488
memory.current = 56483840
memory.peak = 80130048
memory.events: low 0, high 0, max 0, oom 0, oom_kill 0, oom_group_kill 0
```

فایل‌های مسیر cgroup نسخهٔ قدیمی در این نمونه `None` بودند. این اعداد، OOM را در کانتینر فعلی نشان ندادند؛ OOM احتمالی کانتینرهای قبلی یا منابع لحظهٔ ساخت با این نمونه رد یا تأیید نشد. علت قطعی همهٔ شکست‌ها نباید «کمبود RAM» ثبت شود.

## اختلاف اندازه‌ها و پیدا شدن فایل واقعی HNSW

در بررسی راه‌دور، `pg_database_size` حدود `14 GB` بود، اما فهرست ایندکس‌های متصل به جدول بردار فقط سه مورد را نشان می‌داد:

| ایندکس متصل به جدول بردار در `pg_index` | حجم | معتبر / آماده |
|---|---|---|
| `hybrid_vector_input_idx` | `143 MB` | هر دو `True` |
| `ai_retrieval_chunk_vector_pkey` | `93 MB` | هر دو `True` |
| `hybrid_vector_gen_idx` | `4584 kB` | هر دو `True` |

اندازه‌های اصلی جدول‌ها نیز چنین گزارش شدند:

| جدول | داده، شامل TOAST | ایندکس‌های متصل | مجموع |
|---|---|---|---|
| `ai_retrieval_chunk_vector` | `5439 MB` | `241 MB` | `5680 MB` |
| `ai_retrieval_searchchunk` | `2891 MB` | `692 MB` | `3583 MB` |
| `ai_retrieval_searchconcept` | `106 MB` | `19 MB` | `125 MB` |
| `ai_retrieval_searchalias` | `30 MB` | `45 MB` | `75 MB` |
| `ai_retrieval_indexedarticle` | `5616 kB` | `2936 kB` | `8552 kB` |

برای بررسی اختلاف، فایل‌های `base/<database_oid>` با `pg_ls_dir` و `pg_stat_file` خوانده و براساس filenode گروه‌بندی شدند. نتیجه:

```text
UNMAPPED_TOTAL_MB: 0.0
```

گروه‌های مهم:

| filenode | نگاشت ثبت‌شده | حجم / مشاهده |
|---|---|---|
| `616803` | `pg_toast.pg_toast_616800`، مربوط به جدول بردارها | `5243.57 MB`؛ فایل دادهٔ بردارهاست |
| `1296045` | نام دقیق HNSW همین نسل | `5239.4 MB`؛ فایل اصلی و پسوندهای `.1` تا `.5`؛ آخرین تغییر `2026-11-17 08:59:53 UTC` |
| `16766` | `ai_retrieval_searchchunk` | `1917.37 MB` |
| `16771` | `pg_toast.pg_toast_16766` | `958.31 MB` |
| `16822` | `hybrid_chunk_fts_idx` | `295.75 MB` |

فرض اولیهٔ «فایل یتیمِ بدون ثبت در کاتالوگ» با `UNMAPPED_TOTAL_MB: 0.0` تأیید نشد. فایل HNSW به یک شیء `pg_class` نگاشت داشت. همچنین برداشت قبلیِ «ایندکس کاملاً وجود ندارد» دقیق نبود؛ پرس‌وجوهای اولیه از `pg_index` یا join آن شروع می‌کردند و شیء فاقد رکورد متناظر را نشان نمی‌دادند.

## تأیید ناهماهنگی `pg_class` و `pg_index`

آخرین بررسی از خود `pg_class` شروع شد و با `LEFT JOIN` به `pg_index` و جدول مقصد متصل شد. مالک نتیجهٔ یکسان زیر را برای حالت عادی (`NORMAL`) و حالت خواندن ترتیبی (`SEQUENTIAL`) گزارش کرد:

```text
object_oid: 1296045
schema_name: public
object_name: hybrid_hnsw_b9bbb29cbada4f94803f_efdd6c8d9d27
object_kind: i
file_node: 1296045
has_pg_index: False
index_valid: None
index_ready: None
index_live: None
table_oid: None
indexed_table: None
```

در حالت دوم، استفاده از index scan، index-only scan و bitmap scan در همان بررسی غیرفعال شده بود. هر دو روش، شیء را در `pg_class` دیدند و رکورد متناظر آن را در `pg_index` پیدا نکردند. این خروجی با حالت عادیِ «ایندکس موجود با `indisvalid=false`» تفاوت دارد؛ پرچم‌ها اینجا از ردیف موجود خوانده نشده‌اند و `None` هستند.

در [کد فعلی `vectors.create_index`](../backend/apps/ai_retrieval/vectors.py)، تشخیص ایندکس موجود بر join از `pg_index` به `pg_class` تکیه دارد. برای این وضعیت، ردیفی پیدا نمی‌شود؛ کد سپس ساخت با همان نام را امتحان می‌کند، در حالی که نام در `pg_class` اشغال شده است. خطای تازهٔ «نام از قبل وجود دارد» پس از این تشخیص هنوز از سرور گزارش نشده؛ این بخش تحلیل مسیر کد است. اجرای دوبارهٔ همان helper به‌تنهایی راه ترمیم این ناهماهنگی نیست.

در این مقطع خطای احتمالی `cache lookup failed for index 1296045` هنگام حذف معمولی مطرح شده بود و هنوز خروجی آن گزارش نشده بود. در ادامهٔ همین روز، اجرای واقعی این خطا را تأیید کرد؛ بخش بعد نتیجهٔ تازه را ثبت می‌کند. حذف فایل فیزیکی یا تغییر مستقیم کاتالوگ پیشنهاد اجرایی این مسیر نیست.

## بکاپ و شکست حذف استاندارد ـ ادامهٔ ۱۷ نوامبر

خواندن لاگ پیشنهادی `/sd/ai-transfer/hnsw-recovery-backup.log` خطای نبود فایل داد؛ این مشاهده فقط نبودن همان لاگ را نشان می‌داد. سپس مالک از ترمینال بک‌اند، `pg_dump` را با اتصال خصوصی به `reference-db-xoc-service:8000`، قالب custom و نام دارای timestamp اجرا کرد. رمز با prompt وارد شد و در دستور یا گزارش نیامد. پس از برگشت خط فرمان، مالک گزارش کرد:

```text
PG_DUMP_EXIT=0
-rw------- 1 root root 3.2G Nov 17 11:24 /sd/ai-transfer/reference-before-hnsw-repair-20261117T111324Z.dump
```

این خروجی، پایان موفق فرمان طبق وضعیت خروج گزارش‌شده و وجود فایل بکاپ را تأیید می‌کند. حجم `3.2G` مقدار گرد‌شدهٔ `ls -lh` است؛ تعداد دقیق بایت‌ها یا موفقیت restore از آن نتیجه نمی‌شود. بازیابی آزمایشی هنوز ثبت نشده است.

سپس مالک در بک‌اند دستور زیر را اجرا کرد:

```bash
python manage.py dbshell --database reference_search -- -v ON_ERROR_STOP=1 -c "SET lock_timeout='10s'; SET statement_timeout='60s'; DROP INDEX IF EXISTS public.hybrid_hnsw_b9bbb29cbada4f94803f_efdd6c8d9d27;"
```

خروجی:

```text
SET
SET
ERROR:  cache lookup failed for index 1296045
CommandError: psql returned non-zero exit status 1
```

بنابراین حذف استاندارد موفق نشده است. این خطا با نبود ردیف `pg_index` برای همان OID سازگار است؛ علت اولیهٔ ایجاد ناهماهنگی یا دامنهٔ آن در سایر اشیا همچنان مشخص نیست. تکرار `DROP INDEX`، import یا ساخت با همان نام، راه‌حل اثبات‌شدهٔ این وضعیت نیست.

مسیر پیشنهادی بعدی، بازیابی منطقی بکاپ در یک **database جدید داخل همین سرویس**، با حفظ دیتابیس فعلی تا تأیید نسخهٔ جدید است. تعریف HNSW ناسازگار در برنامهٔ restore نباید بازسازی خودکار شود؛ فهرست آرشیو باید پیش از انتخاب موارد بازیابی بررسی شود. داده‌های بردارها و نسل‌ها از dump بازیابی می‌شوند و تولید embedding با API لازم نیست. فایل‌های کاتالوگ داخلی از دیتابیس قبلی به نسخهٔ جدید کپی نمی‌شوند؛ موفقیت این مسیر هنوز روی سرور تأیید نشده است.

مالک ابتدا `9.5` گیگابایت فضای آزاد در reference-db اعلام کرد. با اندازهٔ قبلی حدود `9480 MB` برای داده‌ها و ایندکس‌های معمولی و حدود `5239 MB` برای HNSW، این فضا برای نگهداری هم‌زمان نسخهٔ فعلی، نسخهٔ جدید، HNSW و WAL حاشیهٔ کافی نداشت. ظرفیت کل `50 GB` به‌عنوان برآورد محافظه‌کارانه پیشنهاد شد، نه حداقل نظری. سپس مالک افزایش ظرفیت به **`40 GB` با `25 GB` فضای آزاد** را گزارش کرد؛ بر اساس اندازه‌های ثبت‌شده، ادامهٔ بازیابی کنار نسخهٔ قبلی با این ظرفیت مناسب است. این برآورد، رشد نامحدود WAL یا مشکلات احتمالی زیرساخت را منتفی نمی‌کند. سرویس یا RAM جدا برای ساخت database جدید لازم نیست.

### مرحلهٔ اول بازیابی پیشنهادی پس از افزایش فضا

**محل: ترمینال بک‌اند.** این دستورها روی سرور از طرف عامل اجرا نشده‌اند. `createdb` یک database تازه داخل همان سرویس می‌سازد و در صورت موجودبودن نام خطا می‌دهد؛ در این حالت دستور بعد اجرا نشود و database موجود پاک نشود:

```bash
createdb -h reference-db-xoc-service -p 8000 -U pharmenta_reference -W -T template0 pharmenta_reference_recovered
```

پس از موفقیت ساخت database خالی، ساختار اولیه و داده‌ها با توقف در اولین خطا و یک پردازه بازیابی شوند:

```bash
PGOPTIONS='-c statement_timeout=0 -c lock_timeout=30s' pg_restore -h reference-db-xoc-service -p 8000 -U pharmenta_reference -W -d pharmenta_reference_recovered --exit-on-error --no-owner --no-acl --jobs=1 --verbose --section=pre-data --section=data /sd/ai-transfer/reference-before-hnsw-repair-20261117T111324Z.dump
```

این مرحله بخش `post-data` را اجرا نمی‌کند؛ ایندکس‌های معمولی، constraintهای آن بخش و HNSW هنوز ساخته نمی‌شوند. بعد از خروج موفق، فهرست آرشیو و اقلام post-data بررسی می‌شوند تا ایندکس‌های معمولی/constraintها بازیابی و HNSW جداگانه ساخته شود. در میانهٔ کار URL بک‌اند عوض نشود؛ دیتابیس جدید هنوز برای استفادهٔ برنامه آماده نیست. در صورت خطای ساخت database یا restore، خروجی ثبت و همان مرحله بررسی شود؛ هیچ دستور `--clean`، حذف دیتابیس قدیمی یا تولید embedding جدید در این مسیر وجود ندارد. باقی‌ماندن فایل dump و نسخهٔ قدیمی تا تأیید نسخهٔ بازیابی‌شده لازم است.

## لاگ‌های هم‌زمان بک‌اند و حدود نتیجه‌گیری از آن‌ها

دو task جست‌وجو در لاگ ۱۷ نوامبر دیده شدند:

| زمان لاگ worker | task | نتیجهٔ ثبت‌شده |
|---|---|---|
| `00:05:08.983` | `7c0cfa3b-d601-4975-a94f-24b0b4ffc2c2` | received؛ سپس Celery نتیجهٔ `succeeded ...: None` ثبت کرد |
| `08:02:37.140` | `c3ebbe60-e2a8-429b-9e0f-09013273fbe4` | received؛ سپس Celery نتیجهٔ `succeeded ...: None` ثبت کرد |

در telemetry مربوط به هر دو، `outcome=failed`، `machine_answer_complete=false`، `model_attempts=0`، `provider_requests=0` و `response_cache=unavailable` بود. زمان worker به‌ترتیب حدود `477.642 ms` و `1057.799 ms` گزارش شد. این خروجی‌ها دریافت و پایان task را نشان می‌دهند؛ موفقیت پاسخ جست‌وجو یا آمادگی HNSW از آن‌ها نتیجه نمی‌شود. علت دقیق شکست کاربردی این دو درخواست در خروجی ارائه‌شده مشخص نبود.

لاگ‌های JSON بک‌اند offset برابر `+0100` داشتند؛ برای نمونه `2026-11-17T08:02:38+0100` برابر `07:02:38 UTC` است. زمان‌های جدول task عین متن لاگ worker نگه داشته شده‌اند و نباید بدون توجه به تنظیم timezone با زمان‌های صریح UTC لاگ ساخت/دیتابیس یکی فرض شوند.

موارد دیگرِ همان لاگ:

- هشدار `StreamingHttpResponse must consume synchronous iterators in order to serve them asynchronously`؛ هشدار مسیر استریم است و شاهد شکست ساخت HNSW نیست.
- لاگ‌های WeasyPrint از parsing CSS تا ساخت PDF و افزودن metadata برای ۷۸ صفحه؛ این‌ها مراحل تولید PDF بودند.
- پاسخ‌های `404` برای مسیرهای دارو، `robots.txt` و `license.txt`؛ `401` برای `/api/v1/auth/me/` و `400` برای درخواست OTP؛ رابطهٔ علّی با توقف HNSW در این گزارش اثبات نشد.

## شروع restore، قطع ترمینال وب و بررسی CLI ـ ادامهٔ ۱۷ نوامبر

مالک خروجی ساخت extension و جدول‌ها در `pharmenta_reference_recovered` و سپس `processing data for table "public.ai_retrieval_chunk_vector"` را فرستاد. بعد از آن prompt دیده شد، اما `RESTORE_DATA_OK` یا وضعیت خروج restore گزارش نشد. بنابراین پایان موفق restore یا حتی توقف قطعی آن هنوز معلوم نیست. مالک همچنین بسته‌شدن دوره‌ای ترمینال وب و پیشنهاد فعال‌سازی مجدد آن را گزارش کرد.

عامل CLI نصب‌شدهٔ `/usr/local/bin/runflare` نسخهٔ `1.3.1` را در لپ‌تاپ بررسی کرد. اتصالِ موجود توانست پروژهٔ `pharmenta` و سرویس‌های `pharmenta-front`، `pharmenta-backend` و `reference-db` را فهرست و لاگ دو سرویس بک‌اند/دیتابیس را دریافت کند. رمز یا token خوانده/چاپ نشد. `runflare event` پس از انتخاب پروژه با `Could not load events` شکست خورد؛ دریافت لاگ‌ها موفق بود. راهنمای نسخهٔ نصب‌شده فرمان `exec`/`shell` ندارد و اجرای مستقیم دستور داخل کانتینر از این CLI تأیید نشده است. هیچ deploy/restart/stop/start از طرف عامل اجرا نشد.

شواهد دریافت‌شده حدود `2026-11-17 11:56 UTC`:

- شروع بک‌اند در لاگ `08:35:06 UTC` بود؛ نام کانتینر همان `6c5b6947f8-drjh6` و لاگ فعالیت چندساعته داشت. در لاگ دریافتی ری‌استارت‌های هرچنددقیقه‌ای دیده نشدند.
- شروع PostgreSQL در لاگ فعلی `09:00:55 UTC` بود و تا `11:54:42 UTC` checkpoint/WAL جدید دیده می‌شد. در این خروجی بعد از شروع restore، خطای قطع COPY، قطع اتصال یا restart تازه دیده نشد؛ این نبودن پیام، موفقیت یا ادامهٔ قطعی restore را ثابت نمی‌کند.
- در `11:36:26` و `11:36:32 UTC` دو خطای احراز هویت نقش `pharmenta_reference` ثبت شده‌اند؛ دستور/کارخواه ایجادکننده مشخص نشده است. بعد از آن checkpointهای ناشی از WAL پیوسته دیده شدند. این خطاها به‌تنهایی شکست همهٔ تلاش‌های اتصال یا restore را ثابت نمی‌کنند.

با این شواهد، قطع نشست وب محتمل‌تر از restart دوره‌ای کانتینرهاست؛ timeout مشخص یا علت WebSocket/نشست هنوز توسط پلتفرم تأیید نشده است. برای تعیین وضعیت فعلی، پرس‌وجوی کوتاه `pg_stat_activity` و `pg_stat_progress_copy` برای `application_name='pg_restore'` و `datname='pharmenta_reference_recovered'` پیشنهاد می‌شود؛ این پرس‌وجو از alias فعلی `reference_search` در همان سرور PostgreSQL قابل اجراست و اسکن جدول بردارها لازم ندارد. صفر ردیف، به‌تنهایی پایان موفق restore را ثابت نمی‌کند. تا تعیین نتیجه، restore تکرار و URL بک‌اند عوض نشود.

### زنده‌بودن نشست restore پس از قطع ترمینال تأیید شد

مالک پرس‌وجوی پیشرفت را از بک‌اند اجرا و نتیجهٔ زیر را گزارش کرد:

```text
pid=185
state=active
wait_event_type=IO
wait_event=WalSync
command=COPY FROM
tuples_processed=1178126
copied_mb=2436.5
```

در زمان این نمونه، نشست `pg_restore` در `pharmenta_reference_recovered` هنوز وجود داشته و دستور COPY آن پایان نیافته بود؛ قطع ترمینال وب حداقل در این مشاهده باعث پایان restore نشده است. `WalSync` انتظار برای ثبت پایدار WAL روی دیسک است و به‌تنهایی خطای عملیات محسوب نمی‌شود. یک نمونه نرخ پیشرفت یا نبود مشکل I/O را ثابت نمی‌کند؛ برای سنجش پیشرفت، همان پرس‌وجو با فاصلهٔ زمانی مقایسه شود.

شمارنده‌های بالا متعلق به COPY جاری‌اند؛ نام جدول در این خروجی مشخص نشده و تعداد `1178126` نباید به شمار `670991` بردارِ نسل هدف نسبت داده شود. مقدار `copied_mb` نیز حجم پردازش‌شدهٔ COPY است، نه میزان خواندن فایل فشردهٔ dump. بنابراین از این دو عدد درصد تکمیل کل restore محاسبه نمی‌شود. خروج موفق کل بازیابی، آماده‌بودن constraintها/ایندکس‌های معمولی یا آمادگی HNSW همچنان تأیید نشده است. اجرای restore جدید، توقف PID برابر `185` یا تغییر URL بک‌اند در این مرحله لازم نیست.

## تأیید شمارش داده‌ها و آماده‌سازی post-data

نمونهٔ بعدی پرس‌وجوی نشست restore، `0 rows` بود. سپس مالک با اتصال مستقیم به `pharmenta_reference_recovered`، شمارش نسل `b9bbb29c-bada-4f94-803f-54cfce8f5058` را گزارش کرد:

```text
expected | vectors | chunks | articles | expected_articles
670991   | 670991  | 670991 | 21273    | 21273
```

بنابراین تعداد بردارها با همان profile، قطعات و مقاله‌های نسل هدف در مقصد منطبق است. این بررسی، آماده‌بودن ایندکس‌ها/constraintها یا سلامت کامل تک‌تک مقادیر و تمام داده‌های سایر نسل‌ها را ثابت نمی‌کند. داده‌های نسل هدف دوباره از آرشیو JSONL وارد یا با API تولید نشوند.

**مرحلهٔ بعد، فقط در ترمینال بک‌اند:** ابتدا فهرست کوچک metadata آرشیو خوانده و نام‌های `hybrid_hnsw_` از برنامهٔ restore حذف شوند. این فرمان داده‌های حجیم dump را دوباره اسکن نمی‌کند؛ فقط فهرست TOC را می‌خواند و یک فایل برنامهٔ بازیابی می‌سازد:

```bash
python -c 'import os,subprocess; from pathlib import Path; os.umask(0o077); r=subprocess.run(["pg_restore","--list","/sd/ai-transfer/reference-before-hnsw-repair-20261117T111324Z.dump"],check=True,capture_output=True,text=True); lines=r.stdout.splitlines(); kept=[s for s in lines if "hybrid_hnsw_" not in s]; assert any(" INDEX " in s or " CONSTRAINT " in s for s in kept), "POSTDATA_LIST_EMPTY"; Path("/sd/ai-transfer/reference-recovery-postdata.list").write_text("\n".join(kept)+"\n"); print("RESTORE_LIST_READY; HNSW_SKIPPED:",len(lines)-len(kept))'
```

پس از `RESTORE_LIST_READY`، دستور زیر فقط اقلام بخش post-data منتخب را در دیتابیس بازیابی‌شده اعمال می‌کند. `HNSW_SKIPPED: 0` خطا نیست؛ ممکن است شیء ناسازگار از ابتدا در metadata آرشیو ثبت نشده باشد. در صورت خطای فرمان اول، دستور دوم اجرا نشود:

```bash
PGOPTIONS='-c statement_timeout=0 -c lock_timeout=30s -c max_parallel_maintenance_workers=0 -c maintenance_work_mem=512MB' pg_restore -h reference-db-xoc-service -p 8000 -U pharmenta_reference -W -d pharmenta_reference_recovered --single-transaction --no-owner --no-acl --verbose --section=post-data --use-list=/sd/ai-transfer/reference-recovery-postdata.list /sd/ai-transfer/reference-before-hnsw-repair-20261117T111324Z.dump && printf 'RESTORE_POSTDATA_OK\n'
```

این مرحله تک‌پردازه است و داده‌های مرحلهٔ قبل را دوباره کپی نمی‌کند. `--single-transaction` اجرای این بخش را یک‌جا commit می‌کند؛ در خطای SQL، تغییرات همین بخش rollback می‌شوند و داده‌های قبلاً بازیابی‌شده حفظ می‌شوند. پایان موفق فقط با نتیجهٔ اجرای این مرحله یا بررسی مستقل آن ثبت می‌شود؛ بسته‌شدن ترمینال به‌تنهایی موفقیت/شکست را تعیین نمی‌کند. در صورت قطع نشست، تا تعیین وضعیت اجرای قبلی دستور تکرار نشود. URL بک‌اند هنوز به دیتابیس جدید تغییر نکند. پس از موفقیت این مرحله، ساخت مستقل HNSW، بررسی آن و فعال‌سازی نسل انجام می‌شوند. در زمان آماده‌سازی این فرمان، نتیجهٔ اجرای آن هنوز گزارش نشده بود؛ بخش بعد موفقیت بعدی را ثبت می‌کند.

## موفقیت post-data و فرمان ساخت مستقل HNSW

مالک خروجی ساخت primary keyها، constraintهای یکتا، ایندکس‌های معمولی/GIN و foreign keyها را فرستاد و در انتها **`RESTORE_POSTDATA_OK`** ثبت شد. بنابراین بخش post-data منتخب در `pharmenta_reference_recovered` با موفقیت commit شده است. شیء ناسازگار دیتابیس قبلی به کاتالوگ مقصد منتقل نشده است؛ هیچ بازیابی یا حذف فیزیکی فایل‌های کاتالوگ انجام نشده است.

مرحلهٔ بعد، ساخت ایندکس برای همان نسل و profile با `CREATE INDEX` عادی است. این دیتابیس هنوز مقصد اپ نشده و ساخت اولیه نیاز به حفظ نوشتن هم‌زمان ندارد. `DO` زیر فقط metadata نسل را می‌خواند و ایندکس را ایجاد می‌کند؛ هیچ API یا import دوباره‌ای اجرا نمی‌شود. ابعاد باید `1536` و نسل باید ready/catalog_ready باشد؛ profile کامل از همان نسل خوانده و اعتبار قالب آن کنترل می‌شود. نام ایندکس مطابق `vectors.create_index()` از UUID و ۱۲ نویسهٔ اول profile ساخته می‌شود. `IF NOT EXISTS` استفاده نمی‌شود تا وجود یک شیء هم‌نام، به‌اشتباه موفقیت ساخت حساب نشود.

**محل: ترمینال بک‌اند؛ فقط یک بار اجرا شود:**

```bash
PGOPTIONS='-c maintenance_work_mem=1GB -c max_parallel_maintenance_workers=0 -c statement_timeout=0 -c lock_timeout=30s -c application_name=pharmenta-hnsw-recovered' psql -h reference-db-xoc-service -p 8000 -U pharmenta_reference -W -d pharmenta_reference_recovered -v ON_ERROR_STOP=1 -c "DO \$hnsw\$ DECLARE p text; n text; BEGIN SELECT embedding_profile->>'id' INTO STRICT p FROM public.ai_retrieval_retrievalgeneration WHERE id='b9bbb29c-bada-4f94-803f-54cfce8f5058' AND status='ready' AND catalog_ready AND (embedding_profile->>'dimensions')::int=1536; IF p IS NULL OR NOT (p ~ '^[0-9a-f]{64}$') THEN RAISE EXCEPTION 'INVALID_PROFILE'; END IF; n := 'hybrid_hnsw_b9bbb29cbada4f94803f_' || left(p,12); RAISE NOTICE 'HNSW_START: %',n; EXECUTE format('CREATE INDEX %I ON public.ai_retrieval_chunk_vector USING hnsw ((embedding::vector(1536)) vector_cosine_ops) WHERE generation_id=%L::uuid AND profile_id=%L',n,'b9bbb29c-bada-4f94-803f-54cfce8f5058',p); END \$hnsw\$;" && printf 'HNSW_BUILD_OK\n'
```

تنظیم `maintenance_work_mem=1GB` فقط متعلق به همین اتصال ساخت است، با توجه به حد حافظهٔ حدود ۵ گیگابایتی گزارش‌شدهٔ دیتابیس انتخاب شده و الزام به جاگرفتن کل گراف در RAM ایجاد نمی‌کند. ساخت سریالی باقی می‌ماند. احتمال انتقال بخشی از ساخت به دیسک و طولانی‌شدن وجود دارد؛ زمان قطعی پایان از داده‌های موجود معلوم نیست. پیام `hnsw graph no longer fits into maintenance_work_mem` به‌تنهایی خطا نیست. `fsync` و دوام WAL غیرفعال نمی‌شوند.

**اصلاح فرمان Bash پس از اولین تلاش:** مالک `bash: !~: event not found` دریافت کرد. در نسخهٔ اولیهٔ فرمان، عملگر PostgreSQL به شکل `p !~ ...` داخل کوتیشن دوتایی shell قرار داشت؛ Bash تعاملیِ دارای history expansion، علامت `!` را پیش از اجرای psql پردازش کرد. بنابراین در این تلاش ساخت HNSW شروع نشد و این پیام، خطای PostgreSQL یا دیتابیس بازیابی‌شده نیست. فرمان بالا به `NOT (p ~ ...)` اصلاح شد و هیچ علامت `!` ندارد. آزمون اولیهٔ عامل غیرتعاملی بود و این تعارض را پوشش نمی‌داد؛ در آزمون بعدی، خطای نسخهٔ قبلی در Bash تعاملی با `set -H` بازتولید و عبور نسخهٔ اصلاح‌شده تا psql ساختگی تأیید شد. این آزمون به سرور وصل نشد و HNSW تازه‌ای روی رانفلر نساخت.

در صورت قطع ترمینال، اجرای تازه شروع نشود؛ از یک ترمینال بک‌اند وضعیت سرور خوانده شود:

```bash
python manage.py dbshell --database reference_search -- -c "SELECT pid,phase,blocks_done,blocks_total,round(100.0*blocks_done/nullif(blocks_total,0),1) AS phase_pct FROM pg_stat_progress_create_index WHERE datname='pharmenta_reference_recovered';"
```

درصد مربوط به مرحلهٔ فعلی است، نه تضمین درصد کل زمان. صفر ردیف به‌تنهایی موفقیت را ثابت نمی‌کند. بعد از `HNSW_BUILD_OK` یا پایان نشست، پرچم‌های `indisvalid`/`indisready`، تعریف/مقصد ایندکس و تعداد بردارهای profile بررسی می‌شوند؛ سپس با کنترل source/profile خود برنامه، نسل آماده و فعال می‌شود. در این فرمان `embedding_ready` یا head فعال تغییر نمی‌کند و URL بک‌اند هنوز به مقصد جدید تغییر نکند. **خروجی موفق ساخت HNSW هنوز از سرور گزارش نشده است.**

## شروع HNSW مقصد جدید و خالی‌شدن نمای پیشرفت

مالک نسخهٔ اصلاح‌شدهٔ فرمان را اجرا و این خروجی را گزارش کرد:

```text
NOTICE: HNSW_START: hybrid_hnsw_b9bbb29cbada4f94803f_efdd6c8d9d27
NOTICE: hnsw graph no longer fits into maintenance_work_mem after 156041 tuples
DETAIL: Building will take significantly more time.
HINT: Increase maintenance_work_mem to speed up builds.
```

پس از برگشت prompt، پرس‌وجوی `pg_stat_progress_create_index` برای `pharmenta_reference_recovered` صفر ردیف برگرداند. `HNSW_BUILD_OK` یا خطای SQL نهایی گزارش نشد. پیام عبور گراف از حافظه، notice کاهش سرعت است و به‌تنهایی به معنی شکست نیست. صفر ردیف نیز پایان موفق یا شکست را از هم تفکیک نمی‌کند؛ وضعیت خود شیء در کاتالوگ **دیتابیس جدید** و نشست `application_name='pharmenta-hnsw-recovered'` باید بررسی شوند. کاتالوگ دیتابیس قدیمی هنوز مربوط به شیء ناسازگار قبلی است و معیار این ساخت تازه نیست.

عامل حدود `2026-11-17 18:44 UTC` دوباره از CLI لاگ `reference-db` را دریافت کرد. در خروجی دریافتی شروع PostgreSQL همچنان `09:00:55 UTC` بود و restart یا خطای تازهٔ SQL/کمبود فضا بعد از آغاز این ساخت دیده نشد؛ نبود خطا در این لاگ به‌تنهایی موفقیت ساخت را اثبات نمی‌کند. آخرین checkpoint گزارش‌شده `14:27:29 UTC` بود. در `14:26:10 UTC` هشدار `checkpoints are occurring too frequently (29 seconds apart)` و پیشنهاد افزایش `max_wal_size` ثبت شده بود؛ این مشاهده فشار checkpoint/I/O را نشان می‌دهد، نه علت قطعی پایان ساخت. هیچ تغییر تنظیم WAL یا اجرای مجدد ساخت از طرف عامل انجام نشد.

ادامهٔ فعلی، بررسی فقط‌خواندنی uptime، نشست ساخت و `pg_class LEFT JOIN pg_index` در `pharmenta_reference_recovered` است. اگر ایندکس موجود و معتبر/آماده باشد، ساخت تکرار نمی‌شود. تا مشخص‌شدن این نتیجه، `embedding_ready`، head فعال و اتصال دائمی اپ تغییر نمی‌کنند. نتیجهٔ این بررسی هنوز از مالک دریافت نشده است.

## تأیید HNSW معتبر مقصد جدید و اتصال برنامه

مالک در `pharmenta_reference_recovered` پرس‌وجوی uptime، نشست ساخت و خود شیء را اجرا و نتیجهٔ زیر را گزارش کرد:

```text
postgres_started=2026-11-17 09:00:55.278538+00
build_sessions=0 rows
oid=2575069
relname=hybrid_hnsw_b9bbb29cbada4f94803f_efdd6c8d9d27
has_metadata=t
indisvalid=t
indisready=t
```

ساخت HNSW در مقصد جدید با این خروجی تأیید شد. نبود `HNSW_BUILD_OK` در ترمینال، در این مورد به معنی شکست ساخت نبود. شروع PostgreSQL هم تغییر نکرده است. هیچ ساخت دوباره یا حذف ایندکس معتبر پیشنهاد نمی‌شود. SQL ساخت، `embedding_ready` و head فعال برنامه را عوض نکرده بود؛ این مرحله جداگانه تکمیل می‌شود.

**مرحلهٔ بعد ـ پنل بک‌اند:** مقدار موجود `REFERENCE_SEARCH_DATABASE_URL` با حفظ host، port، user، password و query parameterهای فعلی ویرایش شود؛ فقط نام database در path از `pharmenta_reference` به `pharmenta_reference_recovered` تغییر کند. URL واقعی در گفتگو یا Git ثبت نشود. `DATABASE_URL` اصلی و URL مستقل بازخورد حفظ شوند. برای مسیر هدف، `AI_LAB_ENABLED=True` و `AI_LAB_SEARCH_ENGINE=hybrid` برقرار باشند و همان بک‌اند Redeploy شود تا API و workerهای داخل کانتینر اتصال جدید را بگیرند. انجام این تغییر در سرور هنوز گزارش نشده است.

**پس از Redeploy ـ ترمینال تازهٔ بک‌اند:** فرمان زیر فقط وقتی اتصال به نام database جدید باشد پیش می‌رود. profile جاری، pin منبع، تعداد بردارهای profile، نوع/جدول/تعریف و پرچم‌های ایندکس کنترل می‌شوند؛ سپس آمادگی و head فعال با توابع برنامه ثبت می‌شوند. در mismatch هیچ بازسازی یا فراخوانی مدل انجام نمی‌شود:

```bash
python manage.py shell -c 'from django.db import connections; from apps.ai_retrieval import indexing,vectors,portable_vectors; from apps.ai_retrieval.models import RetrievalGeneration,RetrievalHead; c=connections["reference_search"]; assert c.settings_dict["NAME"]=="pharmenta_reference_recovered", "WRONG_DATABASE"; g=RetrievalGeneration.objects.get(pk="b9bbb29c-bada-4f94-803f-54cfce8f5058"); portable_vectors._source(g); p=vectors._configuration(g); assert vectors.count(g,p["id"])==g.chunk_count, "VECTOR_COUNT_MISMATCH"; n="public.hybrid_hnsw_"+g.pk.hex[:20]+"_"+p["id"][:12]; cur=c.cursor(); cur.execute("SELECT i.indisvalid,i.indisready,i.indrelid=%s::regclass,a.amname,pg_get_expr(i.indpred,i.indrelid),pg_get_expr(i.indexprs,i.indrelid) FROM pg_index i JOIN pg_class t ON t.oid=i.indexrelid JOIN pg_am a ON a.oid=t.relam WHERE i.indexrelid=to_regclass(%s)",["public.ai_retrieval_chunk_vector",n]); r=cur.fetchone(); assert r and r[:4]==(True,True,True,"hnsw") and str(g.pk) in (r[4] or "") and p["id"] in (r[4] or "") and ("vector(%s)"%p["dimensions"]) in (r[5] or ""), "HNSW_NOT_READY"; g.embedding_ready=True; g.save(update_fields=["embedding_ready"]); indexing.activate_generation(g); print({"database":c.settings_dict["NAME"],"embedding_ready":g.embedding_ready,"active":RetrievalHead.objects.filter(active_id=g.pk).exists()})'
```

خروجی مورد انتظار `database=pharmenta_reference_recovered`، `embedding_ready=True` و `active=True` است. این فرمان نه `vectors.create_index`، نه import، نه `embeddings.embed` را صدا می‌زند؛ بنابراین ایندکس معتبر را دوباره نمی‌سازد. بررسی `_source` و profile قبل از تغییر آمادگی انجام می‌شوند و `activate_generation` دوباره pin منبع را کنترل می‌کند. در خطا، متن آن بررسی شود و کنترل‌ها حذف نشوند.

پس از خروج موفق، آمار برنامه‌ریز مقصد جدید نیز با `ANALYZE` به‌روز شود؛ این کار جدول یا ایندکس را بازسازی نمی‌کند:

```bash
python manage.py dbshell --database reference_search -- -v ON_ERROR_STOP=1 -c "ANALYZE;"
```

آزمون runtime بعدی، `python manage.py check_search_runtime`، از یک job تشخیصیِ از پیش لغوشده استفاده می‌کند و درخواست مدل ندارد؛ سپس آزمون واقعی مدیر و رسانه/بازخورد/اعتبار طبق راهنمای ۴۷ انجام می‌شوند. URL جدید، فعال‌سازی برنامه، ANALYZE و نتیجهٔ این آزمون‌ها هنوز از سرور گزارش نشده‌اند. دیتابیس قبلی و فایل dump تا تأیید کارکرد نسخهٔ جدید حفظ شوند.

## توقف startup پس از تغییر URL مقصد ـ ۱۷ نوامبر، ۱۸:۵۹ UTC

مالک پس از تغییر environment بک‌اند، توقف راه‌اندازی را گزارش کرد. خطا در import تنظیمات و پیش از اتصال یا اجرای migration رخ داده بود:

```text
[docker-start] 2026-11-17T18:59:25+00:00 settings=config.settings.production port=8000 cwd=/app
DATABASES["reference_search"] = dj_database_url.parse(REFERENCE_SEARCH_DATABASE_URL, conn_max_age=0)
ValueError: No support for ''.
[docker-start] !!! FAILED (exit 1): python manage.py migrate --no-input
```

این خطا یعنی parser برای مقدار فعلی scheme قابل‌تشخیص پیدا نکرده است. خود مقدار environment در گفتگو ارائه نشده؛ قرارگرفتن فقط نام database در مقدار، یا کوتیشن/قالب نامعتبر، از علت‌های ممکن‌اند. عامل با دادهٔ ساختگی بازتولید کرد که مقدار تنها `pharmenta_reference_recovered` دقیقاً همین خطا را می‌دهد؛ URL کامل با رمز URL-encoded به مقصد صحیح parse شد. رمز واقعی در آزمون خوانده/چاپ نشد. این شکستِ import تنظیمات، شاهد خراب‌شدن یا تغییر HNSW موجود نیست.

مقدار متغیر موجود `REFERENCE_SEARCH_DATABASE_URL` باید **URL کامل** باشد و path آن database جدید را مشخص کند. نام database به‌تنهایی مقدار این متغیر نیست. اگر URL قبلی در اختیار مالک باشد، تنها path آن ویرایش شود. برای ساخت مقدار کامل از رمز خامی که در prompt موفق psql استفاده شده، فرمان زیر در **ترمینال لپ‌تاپ مالک** اجرا می‌شود؛ به ترمینال کانتینر کرش‌کرده نیاز ندارد و اتصال شبکه انجام نمی‌دهد:

```bash
python3 -c 'from getpass import getpass; from urllib.parse import quote; print("postgresql://pharmenta_reference:"+quote(getpass("Reference DB password: "),safe="")+"@reference-db-xoc-service:8000/pharmenta_reference_recovered")'
```

خروجی واقعی حاوی رمز است؛ فقط در Value پنل ذخیره شود و به گفتگو، Git یا لاگ ارسال نشود. Value فقط همان URL شروع‌شونده با `postgresql://` است؛ نام متغیر، `=` یا کوتیشن اضافی داخل آن قرار نگیرد. سپس بک‌اند Redeploy و بعد از بالا آمدن، فرمان کنترل/فعال‌سازی بخش قبل اجرا شود. موفقیت اصلاح environment یا فعال‌سازی هنوز از سرور گزارش نشده است. تغییر رمز، حذف دیتابیس، import یا ساخت مجدد HNSW برای رفع خطای قالب URL لازم نیست.

## اصلاح URL و فعال‌سازی نسل در برنامه تأیید شد

مالک اعلام کرد مقدار environment را به‌درستی اصلاح کرده است. پس از Redeploy، فرمان کنترل/فعال‌سازی را در کانتینر `pharmenta-backend-yuf-deploy-65c4774cb-pthnn` اجرا و خروجی زیر را گزارش کرد:

```text
{'database': 'pharmenta_reference_recovered', 'embedding_ready': True, 'active': True}
```

این خروجی تأیید می‌کند alias برنامه به مقصد جدید متصل است و کنترل‌های فرمان شامل pin منبع، profile جاری، شمار بردارها، نوع/جدول/تعریف ایندکس و پرچم‌های valid/ready موفق بوده‌اند. آمادگی و head فعال ثبت شده‌اند. برنامهٔ قبلی و خطای قالب URL، وضعیت جاری سرویس محسوب نمی‌شوند. این مرحله هیچ embedding پولی، import آرشیو یا ساخت دوبارهٔ HNSW انجام نداده است.

عامل حدود `2026-11-17 19:07 UTC` دو درخواست عمومیِ بدون احراز هویت و بدون مدل به دامنهٔ API فرستاد. `/api/v1/health/` پاسخ HTTP `200`، `status=ok` و `database=ok` داد؛ `/api/v1/ready/` نیز HTTP `200`، `status=ok` و `database/cache/broker=ok` داد. زمان هر درخواست از محیط عامل حدود `1.45s` بود؛ این زمان، زمان سرچ هوشمند نیست. کد این endpointها فقط وابستگی‌های عمومی را بررسی می‌کند و سلامت نسل برداری، مصرف‌شدن job توسط worker یا پاسخ مدل را به‌تنهایی اثبات نمی‌کند.

دو مرحلهٔ بعدیِ برنامه‌ریزی‌شده، `ANALYZE` روی مقصد جدید و آزمون `check_search_runtime` از ترمینال بک‌اند هستند؛ نتیجهٔ آن‌ها هنوز گزارش نشده است. سپس سؤال واقعی در اپ با حساب مدیر آزمایش می‌شود. فعال‌بودن head و ایندکس به‌تنهایی سرعت زیر ۲۰ ثانیه، صحت پاسخ، کارکرد API مدل/embedding یا انتشار عمومی برای همهٔ کاربران را ثابت نمی‌کند. دیتابیس قبلی، dump و فایل‌های بردار تا تأیید کارکرد نسخهٔ جدید حفظ می‌شوند؛ حذف خودکار یا دستور حذف در این مرحله وجود ندارد.

## درخواست اتصال مدل پاسخ‌گو به آروان

**به‌روزرسانی ۱۸ نوامبر:** بررسی‌های بدون کلید در ادامه، سابقهٔ مرحلهٔ قبلی هستند. با نمونهٔ Python تازهٔ مالک، یک درخواست واقعیِ کوتاه با Bearer به `/v1/chat/completions` موفق شد: HTTP `200`، پاسخ `ARVAN_OK` و زمان حدود `3.93s`. سپس اشکال واقعی مسیر برنامه با خطای `MODEL_MISMATCH` در هر دو آزمون استریم متن با `low` و استریم ابزار با `none` بازتولید شد. نام درخواست `GPT-6-Luna` است ولی نام برگشتی `openai/gpt-6-luna`؛ درخواست مستقیم با نام دوم HTTP `404` داد. بنابراین موفقیت تست اتصال ساده، سازگاری اعتبارسنجی نام در برنامه را ثابت نمی‌کرد.

اصلاح کد، متغیر `AI_LAB_RESPONSE_MODEL_ALIASES` را اضافه می‌کند: مقدار صریح `openai/gpt-6-luna` در آروان مجاز می‌شود و تطبیق سخت‌گیرانه برای نام‌های دیگر برقرار می‌ماند. این کنترل در هر دو adapter استریم و غیر‌استریم مشترک است؛ فهرست نام‌های مجاز در کلید کش پاسخ و پروفایل تأیید انتشار لحاظ می‌شود. پس از اصلاح، آزمون واقعی کد پروژه با `low` برای tool calling، پاسخ نهایی فارسی استریم پس از دریافت نتیجهٔ ابزار، و JSON غیر‌استریم موفق شد؛ زمان‌های جداگانه تقریباً `5.32s`، `4.92s` و `4.32s` بودند. کلید فقط در حافظهٔ آزمون و ورودی مخفی ترمینال استفاده شد و در فایل پروژه یا خروجی ذخیره نشد. نتیجهٔ انتشار این اصلاح و جست‌وجوی کامل در اپ سرور هنوز گزارش نشده است.

راهنمای جاری و تفکیک تنظیم‌های chat، embedding و تعرفه در بخش ۸ [سند ۴۷](47-smart-search-server-step-by-step.fa.md) است. بدون تنظیم مستقل URL و کلید embedding، تغییر URL chat می‌تواند پروفایل بردارهای موجود را عوض کند؛ بدون ذخیرهٔ دوبارهٔ تعرفهٔ فعال، تغییر مدل/ارائه‌دهنده می‌تواند شروع جست‌وجو را پیش از تماس مدل متوقف کند. این دو مورد وابستگی‌های قطعی کد هستند، ولی علت رخ‌داده در تنظیم‌های فعلی سرور بدون خروجی تشخیص یا کد خطا تأیید نشده‌اند.

کنترل‌های خودکار اصلاح شامل ۳۷ آزمون adapterهای مدل/stream و یک آزمون تفکیک کلید کش پس از تغییر alias بودند و موفق شدند. آزمون کش از پایگاه موقت جدا با موتور `outline` متناسب با fixture آن استفاده کرد؛ اجرای اولیه با موتور `hybrid` لوکال به دلیل نبود نسل hybrid در fixture کلید کش نداد. پایگاه موقت پس از هر اجرا حذف شد و داده‌های اصلی تغییری نکردند.

سابقهٔ پیش از آزمون واقعی:

مالک اجرای `ANALYZE` و `check_search_runtime` را به بعد موکول کرد و دربارهٔ انتقال مدل پاسخ‌گو به endpoint برابر `https://api.arvancloudai.ir/v1` با نام اعلام‌شدهٔ `GPT-6-Luna` پرسید. کلید واقعی در این سند یا فایل پروژه ذخیره نشده و در آزمون‌ها استفاده نشد. اعتبار کلید و شناسهٔ مدل در حساب آروان هنوز آزموده نشده‌اند.

نگاشت مطابق کد فعلی:

```dotenv
AI_LAB_BASE_URL=https://api.arvancloudai.ir/v1
AI_LAB_MODEL=GPT-6-Luna
AI_LAB_REASONING_EFFORT=none
```

خود secret در Value متغیر `AI_LAB_API_KEY` قرار می‌گیرد؛ پیشوند `Bearer`، عنوان `secret_key:` یا کوتیشن اضافی جزو مقدار نیست. کد header برابر `Authorization: Bearer ...` را خودش می‌سازد و پذیرش مقدار environment به پیشوند `sk-` وابسته نیست؛ parser فایل خصوصی قدیمی محدودیت جداگانه دارد و برای این کلید از متغیر محیطی استفاده شود. کد مسیر `/chat/completions` را خودش به base اضافه می‌کند؛ این مسیر به مقدار `AI_LAB_BASE_URL` اضافه نشود.

انتخاب `none` پیشنهاد سازگاریِ این اتصال با مسیر فعلی Chat Completions و tool calling است؛ ترجیح قبلی مالک `low` بود و تغییر واقعی تنظیم هنوز گزارش نشده است. طبق [مستند رسمی GPT-6 Luna](https://developers.openai.com/api/docs/models/gpt-6-luna)، function calling در Chat Completions این مدل به `reasoning_effort=none` محدود است؛ رفتار gateway آروان یا تبدیل داخلی آن به Responses با درخواست دارای کلید هنوز تأیید نشده است. این محدودیت علت قطعی خطای فعلی مالک محسوب نمی‌شود، چون متن خطای اتصال مدل ارائه نشده است.

نکتهٔ وابستگی تنظیمات: در `base.py`، پیش‌فرض `AI_LAB_EMBEDDING_BASE_URL` همان `AI_LAB_BASE_URL` است. برای حفظ profile نسل فعال، مسیر embedding باید صریحاً روی سرویس قبلی بماند:

```dotenv
AI_LAB_EMBEDDING_BASE_URL=https://api.gapgpt.app/v1
AI_LAB_EMBEDDING_MODEL=text-embedding-3-small
AI_LAB_EMBEDDING_DIMENSIONS=1536
AI_LAB_EMBEDDING_USE_CHAT_KEY=False
AI_LAB_EMBEDDING_REMOTE_ENABLED=True
```

`AI_LAB_EMBEDDING_API_KEY` کلید جداگانهٔ سرویس embedding قبلی است. revision و سایر اجزای profile منطبق حفظ شوند. تغییر provider مدل پاسخ‌گو به‌تنهایی نیاز به ساخت دوبارهٔ بردارها یا HNSW ندارد؛ تغییر ناخواستهٔ base embedding می‌تواند `EMBEDDING_PROFILE_CHANGED` بدهد.

عامل بدون header احراز هویت، `/v1/models` را بررسی کرد و HTTP `401` گرفت؛ این فقط دسترس‌پذیری مسیر از محیط عامل و نیاز به احراز هویت را نشان می‌دهد، نه نامعتبر بودن کلید مالک. `/openapi.json` نیز `404` داد. جست‌وجوی مستند عمومی آروان برای تطبیق دقیق این endpoint نتیجهٔ قابل اتکایی نداد؛ مدل اعلام‌شده جایگزین حدسی نشد. هیچ درخواست دارای کلید یا تولید متن پولی از محیط عامل انجام نشد.

پس از ذخیرهٔ environment و Redeploy، `python manage.py check_search_model` یک درخواست کوتاهِ مصرف‌کنندهٔ API برای بررسی stream/tool calling می‌فرستد و کلید/بدنهٔ خطای ارائه‌دهنده را چاپ نمی‌کند. در صورت خطا، code/status آن برای بررسی بعدی کافی است؛ کلید واقعی ارسال نشود. تغییر مدل یا base ارائه‌دهنده امضای تعرفه را عوض می‌کند؛ اگر کسر اعتبار فعال است، نرخ‌ها در مدیریت بازبینی و دوباره ذخیره شوند. انجام این تنظیمات و نتیجهٔ آزمون آروان هنوز از سرور گزارش نشده‌اند.

## بررسی لینک رسمی AIaaS آروان پس از ناموفق‌بودن اتصال

مالک اعلام کرد اتصال هنوز برقرار نیست و نشانی `https://www.arvancloud.ir/api/aiaas/1.0` را فرستاد. ابزار مرور وب این URL را باز نکرد، اما دریافت مستقیم HTTPS از محیط عامل با User-Agent مرورگر موفق شد: صفحهٔ HTML عنوان `API Documentation | Arvancloud` و ReDoc داشت. فایل رسمی JSON نیز از `https://www.arvancloud.ir/api-docs/aiaas-1.0.json` با HTTP `200` دریافت و بررسی شد؛ فایل دارای Swagger `2.0`، عنوان `ai-ml-backend` و `basePath=/ai/v1` است. نسخهٔ YAML در همان مسیر به‌جای specification یک صفحهٔ HTML برگرداند.

یافته‌های مشخص از JSON رسمی:

- مسیرهای `/endpoints`، `/endpoints/{endpoint_id}`، `/models` و `/providers` مدیریت درگاه‌ها، مدل‌ها و ارائه‌دهندگان هستند؛ ساختار endpoint شامل `endpoint`، `model` و مشخصات مدیریتی است.
- روی عملیات‌ها ارجاع `ApiKeyAuth` وجود دارد، اما `securityDefinitions` در فایل منتشرشده تعریف نشده است. نام این scheme به‌تنهایی شکل هدر اجرای مدل را مشخص نمی‌کند.
- در این فایل، مسیر inference برابر `/chat/completions` یا `/responses`، نمونهٔ curl اجرای مدل و قرارداد `secret_key` برای `api.arvancloudai.ir` تعریف نشده‌اند. روش احراز هویت API مدیریتی نباید به‌طور حدسی جایگزین هدر inference شود.
- صفحهٔ رسمی محصول `https://www.arvancloud.ir/fa/products/aiaas/api/openai` نیز دریافت API Key و Endpoint اختصاصی را توضیح می‌دهد؛ از متن عمومی آن، قرارداد دقیق درخواست همین endpoint مالک مشخص نشد.

عامل چهار GET بدون اعتبار واقعی به `/v1/models` فرستاد: بدون هدر، با Bearer ساختگی، با Apikey ساختگی و با x-api-key ساختگی. همه HTTP `401` دادند؛ این نتایج اعتبار کلید مالک یا هدر صحیح را تعیین نمی‌کنند و درخواست مدل/هزینهٔ تولید متن نداشتند. کلید واقعی مالک استفاده یا ذخیره نشد.

برای رفع ابهام، نمونهٔ curl/Python بخش اتصال همین درگاه در پنل با حذف کلید، و حفظ URL، نام هدر و مقدار model از مالک درخواست شد. همچنین خروجی سانیتایزشدهٔ `python manage.py check_search_model` می‌تواند شکست احراز هویت، HTTP، نام مدل یا stream/tool calling را تفکیک کند؛ نتیجهٔ این آزمون هنوز ارائه نشده است. تا دریافت شواهد، ادعای قطعی دربارهٔ تغییر Bearer به Apikey یا تغییر endpoint/model مطرح نمی‌شود و کد اتصال به‌صورت حدسی ویرایش نشده است.

## پیشنهاد بکاپ پیشین و کارهای باز فعلی

پیشنهاد پیشین، گرفتن dump با `pg_dump` نسخهٔ ۱۷ یا جدیدتر، از اتصال تنظیم‌شدهٔ Django و ذخیرهٔ آن روی دیسک بک‌اند بود؛ رمز از تنظیم‌ها به محیط subprocess منتقل می‌شد و در خروجی چاپ نمی‌شد. مسیرهای آن پیشنهاد:

```text
log: /sd/ai-transfer/hnsw-recovery-backup.log
dump: /sd/ai-transfer/reference-before-hnsw-repair-<UTC timestamp>.dump
markers: BACKUP_START, BACKUP_OK, BACKUP_BYTES
```

لاگ و markerهای پیشنهاد اولیه گزارش نشدند؛ اجرای مستقیم بعدی با نام فایل دقیقِ بخش بالا و کد خروج صفر ثبت شد. پایان موفق ابزار، موفقیت کامل restore را به‌تنهایی تضمین نمی‌کند؛ نتیجهٔ بازیابی باید در ادامه ثبت شود.

فهرست کارهای باز در زمان پیشنهاد اولیهٔ بکاپ، برای حفظ سابقه (بازیابی، ساخت معتبر HNSW و فعال‌سازی در بخش‌های جدیدتر بالا تأیید شده‌اند):

1. تأمین فضای کافی و بررسی پایداری اجرای PostgreSQL/volume؛ علت ناپدیدشدن فایل PID و ناهماهنگی کاتالوگ هنوز باز است.
2. بررسی فهرست بکاپ و بازیابی داده‌ها در database سالم کنار نسخهٔ فعلی، بدون بازسازی خودکار HNSW معیوب؛ سپس ساخت معتبر HNSW با کنترل منابع واقعی دیتابیس و ثبت خروجی پایان/خطا. تکرار import آرشیو JSONL یا خرید embedding تازه پیش‌نیاز این مسیر نیست.
3. بررسی هم‌زمان تعداد بردارها، تعریف ایندکس، وجود ردیف متناظر `pg_index` و هر دو پرچم `indisvalid` و `indisready`؛ سپس آماده‌شدن نسل با کنترل‌های خود برنامه.
4. اجرای موفق `activate_hybrid_index` برای همین UUID؛ در وضعیت فعلی فعال‌سازی انجام‌شده محسوب نمی‌شود.
5. ساخت و بررسی رسانه، `check_search_runtime` و آزمون واقعی سرچ، استریم، اعتبار و بازخورد طبق بخش ۱۲ راهنمای ۴۷.

این به‌روزرسانی فقط مستندسازی است. دستور ترمیم یا ساخت تازه‌ای روی رانفلر اجرا نشده و هیچ وضعیت دیتابیس یا داده‌ای با نوشتن این سند تغییر نکرده است.
