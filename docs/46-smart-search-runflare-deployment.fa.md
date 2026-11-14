# استقرار کانتینری سرچ هوشمند در رانفلر

تاریخ: ۲۰۲۶-۱۱-۱۴. بک‌اند و فرانت‌اند فعلی حفظ می‌شوند. ابزار انتقال بردار اکنون در کد وجود دارد؛ برخلاف snapshot قدیمی [سند ۳۹](39-smart-search-status-deployment.fa.md)، انتقال دیگر به restore دیتابیس لوکال روی اطلاعات کاربران نیاز ندارد. اجرای زیرساخت و انتقال کامل روی رانفلر هنوز انجام نشده‌اند.

## ۱. سرویس‌ها

برای محیط PaaS فعلی، سرویس‌های جدا در همان پروژهٔ رانفلر پیشنهاد می‌شود. مستندات رسمیِ در دسترس، اجرای Dockerfile و شبکهٔ خصوصی را توضیح می‌دهند؛ اجرای مستقیم Compose در این حساب تأیید نشده است. `docker compose` را داخل ترمینال کانتینر بک‌اند اجرا نکنید. Compose روی VPS دارای Docker Engine انتخاب دیگری است و با سرویس فعلی رانفلر یکسان نیست.

جدول زیر مسیر فایل‌های آماده در مخزن را نشان می‌دهد. انتخاب Dockerfile غیر از ریشه، گزینهٔ build context و اتصال دیسک مشترک باید با امکانات واقعی پنل حساب تطبیق داده شوند؛ به پنل این حساب دسترسی مستقیم نداشته‌ایم. اگر پنل Dockerfile ریشه را ثابت می‌خواهد، برای سرویس DB یک پوشه/مخزن مستقل با محتوای همان Dockerfile به نام `Dockerfile` لازم است؛ برای Redis، Dockerfile و script باید با تنظیم COPY متناسب در همان context قرار بگیرند. تا مشخص‌شدن روش build پنل، سرویس جدید را اشتباهاً با Dockerfile وب راه‌اندازی نکنید.

| سرویس | Dockerfile از ریشهٔ همین مخزن | تنظیم اصلی | شبکه / فضای پایدار |
|---|---|---|---|
| بک‌اند موجود | `Dockerfile` | `SERVICE_ROLE=web` | پورت وب فعلی، همان دیتابیس کاربران |
| worker جدید | همان `Dockerfile` و همان کامیت بک‌اند | `SERVICE_ROLE=ai-search-worker`، `AI_LAB_WORKER_CONCURRENCY=2` | مصرف صف `ai_search`؛ بدون دامنهٔ عمومی |
| دیتابیس برداری جدید | `deploy/runflare/Dockerfile.reference-db` | PostgreSQL 17 + pgvector | پورت خصوصی 5432؛ دیسک `/var/lib/postgresql/data` |
| Redis جدید | `deploy/runflare/Dockerfile.redis` | رمز زمان اجرا، AOF و `noeviction` | پورت خصوصی 6379؛ دیسک `/data` |
| فرانت‌اند موجود | همان روند انتشار فعلی | نشانی API سرور | فعلاً تغییر زیرساخت ندارد |

مقدار اولیهٔ پیشنهادی برای آزمایش: دیتابیس برداری ۴ vCPU، رم ۸ GiB و دیسک پایدار ۵۰ GiB؛ worker یک vCPU و رم ۲ GiB؛ Redis رم ۱ GiB و دیسک ۵ GiB. این‌ها تخمین شروع بر اساس اندازهٔ لوکال‌اند، نه تأیید ظرفیت ۱۰۰ کاربر یا حداقل قطعی. فضای PostgreSQL باید داده، HNSW، WAL و ساخت بعدی را پوشش دهد؛ HNSW لوکال به‌تنهایی حدود ۵٫۲ GB بود. فضای دیتابیس اصلیِ متن آماده و فایل‌های snapshot جداست. سرویس Redis این مخزن سقف دادهٔ ۵۱۲ MiB دارد؛ مصرف و اوج حافظهٔ AOF باید پایش شوند.

در رانفلر، برای DB/Redis از شبکهٔ خصوصی (`ClusterIP` در مستندات) و آدرس داخلی **واقعی پنل** استفاده کنید. نام سرویس در مثال‌ها تضمین DNS پلتفرم نیست؛ `localhost` از داخل worker به دیتابیسِ سرویس دیگری اشاره نمی‌کند. [راهنمای شبکهٔ رانفلر](https://runflare.com/docs/network/)، [دیسک پایدار](https://runflare.com/docs/add-disk-to-service/)، [ایمیج رسمی pgvector](https://github.com/pgvector/pgvector#docker).

## ۲. ساخت دیتابیس برداری

یک سرویس Docker جدید با build context ریشهٔ مخزن و Dockerfile جدول بالا بسازید. نسخهٔ ایمیج را پس از نخستین استقرار موفق ثبت کنید؛ تغییر خودسرانهٔ major PostgreSQL روش ارتقا نیست.

متغیرهای سرویس:

```dotenv
POSTGRES_DB=pharmenta_reference
POSTGRES_USER=pharmenta_reference
```

`POSTGRES_PASSWORD` را با مقدار تصادفی طولانی در secrets پنل بگذارید. مسیر دیسک باید `/var/lib/postgresql/data` باشد؛ Dockerfile، `PGDATA` را به زیردایرکتوری `pgdata` می‌برد تا ریشهٔ mount محل مستقیم initdb نباشد. این تنظیم برای سرویس **جدید** است، نه تغییر مسیر دادهٔ دیتابیس موجود.

در ترمینال همین سرویس جدید اجرا کنید:

```bash
psql -U pharmenta_reference -d pharmenta_reference -c 'CREATE EXTENSION IF NOT EXISTS vector;'
psql -U pharmenta_reference -d pharmenta_reference -c "SELECT extversion FROM pg_extension WHERE extname='vector';"
```

آدرس و پورت داخلی را از پنل بردارید. `REFERENCE_SEARCH_DATABASE_URL` در بک‌اند و worker باید به **این دیتابیس جدید** اشاره کند. دیتابیس اصلی کاربران را جایگزین نکنید.

بازخورد نیز به `AI_LAB_FEEDBACK_DATABASE_URL` برای PostgreSQL جدا نیاز دارد. اگر از قبل وجود ندارد، آن را بسازید؛ حداقل نام database باید از اصلی و reference متفاوت باشد. database منطقی جدا می‌تواند روی یک PostgreSQL instance قرار بگیرد؛ این با instance فیزیکی مستقل تفاوت دارد. برای جداسازی فیزیکی، سرویس جدا لازم است.

## ۳. ساخت Redis

سرویس Docker جدید با `deploy/runflare/Dockerfile.redis` و build context ریشهٔ مخزن بسازید. دیسک `/data` و پورت خصوصی 6379 را تعریف کنید. `REDIS_PASSWORD` یک secret تصادفی ۳۲ تا ۱۲۸ نویسه‌ای از حروف، عدد، `_` و `-` باشد؛ رمز hex طولانی مناسب است. فایل تنظیمات فقط هنگام اجرا با مجوز محدود ساخته می‌شود؛ رمز در image یا آرگومان پردازه قرار نمی‌گیرد.

در ترمینال Redis:

```bash
REDISCLI_AUTH="$REDIS_PASSWORD" redis-cli ping
```

خروجی موردانتظار `PONG` است. نگهداری AOF و سیاست `noeviction` در Dockerfile/launcher آماده‌اند. URLهای زیر را در secrets بک‌اند و worker با **آدرس داخلی پنل و رمز واقعی** تنظیم کنید؛ در این راهنما رمز درج نشده است:

```text
REDIS_URL                 → redis://:PASSWORD@INTERNAL_HOST:6379/0
CACHE_URL                 → redis://:PASSWORD@INTERNAL_HOST:6379/1
THROTTLE_CACHE_URL         → redis://:PASSWORD@INTERNAL_HOST:6379/2
CELERY_BROKER_URL          → redis://:PASSWORD@INTERNAL_HOST:6379/3
AI_LAB_EVENT_REDIS_URL     → redis://:PASSWORD@INTERNAL_HOST:6379/4
```

## ۴. تنظیم مشترک بک‌اند و worker

ابتدا DB/Redis سالم باشند. برای worker، **کل تنظیم‌های معتبر بک‌اند فعلی** را در پنل کپی کنید، سپس فقط نقش سرویس و موارد زیر را تغییر دهید؛ این بلوک جایگزین کامل تنظیم‌های production، پرداخت، ایمیل و منابع نیست. `DATABASE_URL`، `SECRET_KEY` و تنظیم‌های رمزگذاری job/بازخورد باید همان مقادیر معتبر مشترک برنامه باشند؛ برای worker کلید تازهٔ متفاوت نسازید. مقادیر اتصال را فقط در secrets پنل وارد کنید و در پیام یا Git قرار ندهید.

```dotenv
DJANGO_SETTINGS_MODULE=config.settings.production
UPTODATE_DB_DIR=/sd/uptodate
AI_LAB_SEARCH_ENGINE=hybrid
AI_LAB_EXECUTOR=celery
AI_LAB_LOCAL_LEXICAL_PILOT=False
CELERY_RUN_TASKS_IN_REQUEST=False
CELERY_TASK_ALWAYS_EAGER=False
READINESS_REQUIRE_CACHE=True
READINESS_REQUIRE_BROKER=True
CACHE_BACKEND=django.core.cache.backends.redis.RedisCache
AI_LAB_ROLLOUT_PERCENT=0
AI_LAB_MAX_CONCURRENT_JOBS=2
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
AI_LAB_FEEDBACK_ENABLED=True
```

`AI_LAB_API_KEY` از کلید chat فایل معرفی‌شدهٔ مالک و `AI_LAB_EMBEDDING_API_KEY` از کلید مستقل خریداری‌شدهٔ embedding به secrets منتقل شوند. فایل دسکتاپ را داخل image کپی نکنید. `none` مطابق لوکالِ بررسی‌شده است؛ برای آزمون `low` فقط همین متغیر reasoning تغییر می‌کند. مدل و Base URL پاسخ‌گو قابل تغییرند، ولی profile بردارسازی باید دقیقاً با بستهٔ انتقال برابر باشد؛ تغییر ابعاد/ارائه‌دهنده/revision صرفاً با تنظیم یک مقدار جدید، بردارهای قبلی را سازگار نمی‌کند.

اگر `CACHE_LOCATION` قدیمی به نام جدول cache اشاره می‌کند، آن override را از پنل حذف کنید تا مقدار `CACHE_URL` استفاده شود؛ یا آن را صریحاً به همان URL واقعی Redis تغییر دهید. مقدار لفظی `$CACHE_URL` را وارد نکنید؛ تمام پنل‌ها آن را expand نمی‌کنند. backend قدیمیِ DatabaseCache/LocMem نباید بر تنظیم Redis جدید غلبه کند.

`REFERENCE_SEARCH_DATABASE_URL` و `AI_LAB_FEEDBACK_DATABASE_URL` هم به دیتابیس‌های مربوط اشاره کنند. برای مرحلهٔ آماده‌سازی، `AI_LAB_ENABLED=False` بماند و پس از آماده‌شدن نسل و آزمون worker روشن شود. این تنظیم دسترسی عمومی را حین آماده‌سازی می‌بندد، نه قابلیت‌های دیگر اپ را.

worker از همان image/کامیت بک‌اند با `SERVICE_ROLE=ai-search-worker` اجرا می‌شود و migration یا وب‌سرور اجرا نمی‌کند. مهاجرت‌ها در سرویس وب/مرحلهٔ release اجرا شوند. صف‌های دیگر برنامه، در صورت استفاده، workerهای قبلی خود را نیاز دارند؛ worker جدید فقط `ai_search` را مصرف می‌کند.

## ۵. snapshot یکسان برای API و worker

API و worker هر دو باید به snapshot معتبر `/sd/uptodate` دسترسی داشته باشند. برای SQLite، صرفاً داشتن فایل‌هایی با اسم یکسان کافی نیست: revision فعلی مشخصات filesystem از جمله inode/mtime را نیز pin می‌کند. **mount مشترک همان دیسک، با همان مسیر** راه پیشنهادی این مرحله است. قابلیت اشتراک دیسک بین این دو سرویس باید در پنل/پشتیبانی رانفلر تأیید شود؛ از مستندات عمومیِ در دسترس قابل اثبات نبود.

در ترمینال **هر دو سرویس** این دستور را اجرا کنید:

```bash
python manage.py shell -c 'from apps.ai_lab.reference_index import source_stamp; s=source_stamp(); print(s.backend, s.identity, s.revision)'
```

سه مقدار باید یکسان باشند. اگر منبع موجود از MySQL مشترک استفاده می‌کند، تنظیم‌های آن منبع نیز در هر دو سرویس یکسان بمانند؛ الزام یک mount فیزیکی مربوط به مسیر SQLite است. اگر مقادیر متفاوت‌اند، قبل از ساخت یا انتقال حجیم متوقف شوید؛ bypass کردن بررسی freshness یا فرض برابر بودن دو کپی مستقل مجاز نیست. در این حالت باید روش اشتراک snapshot یا backend مشترک منبع مشخص شود.

## ۶. schema و متن آمادهٔ سرور

ابتدا از دیتابیس‌های موجود پشتیبان بگیرید. در ترمینال **بک‌اند**، از `/app`:

```bash
python manage.py migrate
python manage.py migrate --database reference_search
python manage.py migrate ai_feedback --database ai_feedback
python manage.py build_reference_index --status
```

اگر نسل آمادهٔ منبع موجود و سازگار است، همان حفظ می‌شود. فقط در صورت نبود/ناسازگاری:

```bash
python manage.py build_reference_index --workers 2 --batch-size 20
```

سپس قطعه‌ها و تگ‌های مقصد را بسازید؛ این مرحله API embedding ندارد:

```bash
python manage.py build_hybrid_index
python manage.py build_hybrid_index --status
```

UUID نسل جدید مقصد را نگه دارید. در تمام مثال‌های بعد، `SERVER_GENERATION_UUID` باید با **همان UUID چاپ‌شده در سرور** جایگزین شود؛ UUID لوکال را اینجا استفاده نکنید. ساخت قطع‌شده را با `build_hybrid_index --resume SERVER_GENERATION_UUID` ادامه دهید. این‌ها پردازهٔ foreground هستند؛ از `&` یا اجرای مخفی استفاده نکنید.

## ۷. خروجی بردارهای فعلی از لپ‌تاپ

**در لپ‌تاپ، نه ترمینال رانفلر**:

```bash
cd '/home/amir/Documents/Learning Platform/backend'
.venv/bin/python manage.py export_hybrid_vectors 73f89df9-d447-4cb7-a32c-f8296b81fa4b --output .private/uptodate-small-1536.jsonl.gz
sha256sum .private/uptodate-small-1536.jsonl.gz
```

۶۷۰٬۹۹۱ بردار نسل کامل فعلی به‌صورت streaming و batchهای محدود صادر می‌شوند. فایل حاوی profile، کلید تطبیق قطعه، hash و بردار است؛ کاربران، paragraph ID لوکال، متن مقاله و کلید API ندارد. مجوز فایل 0600 است. خروجی موجود بازنویسی نمی‌شود؛ خطای کنترل‌شده یا Ctrl+C فایل ناقص را حذف می‌کند و export باید دوباره آغاز شود. قطع اجباری پردازه/سیستم ممکن است فایل ناقص باقی بگذارد؛ آن فایل checksum/footer معتبر ندارد و نباید به‌عنوان خروجی کامل منتقل شود. در اجرای بعد نام جدید انتخاب کنید. export/import تماس API و هزینهٔ embedding ندارند؛ زمان دیسک و پردازش مصرف می‌شود.

فایل را با روش انتقال خصوصیِ در دسترس حساب رانفلر به مسیر پایدار خارج از مسیر عمومی وب، مثلاً `/sd/ai-transfer/uptodate-small-1536.jsonl.gz` منتقل کنید. روش upload/سقف اندازه در حساب باید بررسی شود؛ Git یا Docker image مسیر انتقال این فایل نیست. با `sha256sum` روی سرور، checksum فایل فشرده را با لپ‌تاپ تطبیق دهید. فضای آرشیو و فضای ساخت ایندکس را جدا حساب کنید.

## ۸. بررسی و import روی سرور

برای تشخیص ناسازگاری بدون نوشتن هیچ برداری:

```bash
python manage.py import_hybrid_vectors SERVER_GENERATION_UUID --input /sd/ai-transfer/uptodate-small-1536.jsonl.gz --verify-only
```

فرمان تمام فایل، profile، chunker، شمارش، ترتیب قطعات، hash متن/ورودی، ابعاد/اعداد و checksum را می‌سنجد. اختلاف مسیر و شناسهٔ دیتابیس مجاز است؛ اختلاف متن/ورودی یا profile خطاست. روی mismatch ادامه ندهید و embedding تازه خریداری نکنید؛ علت را بررسی کنید.

پس از verify موفق، import و ساخت HNSW:

```bash
PGOPTIONS='-c max_parallel_maintenance_workers=0 -c maintenance_work_mem=512MB' python manage.py import_hybrid_vectors SERVER_GENERATION_UUID --input /sd/ai-transfer/uptodate-small-1536.jsonl.gz --build-index
```

این تنظیم ساخت سریالی را برای محدودیت shared memory کانتینر انتخاب می‌کند؛ سرعت و حافظهٔ مناسب بعداً بر اساس ظرفیت واقعی تنظیم شوند. import قبل از نوشتن، کل آرشیو را بررسی می‌کند و هنگام درج دوباره اعتبار آن را می‌سنجد. batchها commit می‌شوند؛ اجرای دوبارهٔ همین فرمان، بردارهای مطابق قبلی را reuse می‌کند. بردار موجودِ متناقض پذیرفته نمی‌شود. نسل فعال تغییر نمی‌کند و import روی نسل فعال رد می‌شود. اگر ساخت HNSW قطع شود، نسل آماده علامت نمی‌خورد؛ اجرای مجدد بعد از بررسی علت، index نامعتبر را از مسیر موجود اصلاح می‌کند.

`embed_hybrid_index` را برای انتقال اجرا نکنید؛ آن فرمان می‌تواند API پولی را صدا بزند. `migrate` نیز بردار نمی‌سازد یا منتقل نمی‌کند. ابزار جدید کاربران یا جدول‌های دیتابیس اصلی را restore نمی‌کند؛ paragraph ID و ارجاع‌های خود سرور حفظ می‌شوند.

## ۹. فعال‌سازی، رسانه و آزمون

بعد از import/index کامل، با قابلیت همچنان محدود:

```bash
python manage.py activate_hybrid_index SERVER_GENERATION_UUID
python manage.py build_reference_media --workers 2
python manage.py build_reference_media --status
python manage.py check_search_runtime
```

رسانه از snapshot سرور ساخته می‌شود و هزینهٔ مدل ندارد. تست runtime انتقال واقعی Redis/worker را با صفر درخواست مدل بررسی می‌کند؛ برای آن worker باید روشن و به همان تنظیم/secret متصل باشد. سپس `AI_LAB_ENABLED=True`، rollout صفر و دسترسی مدیر را نگه دارید و API/worker را با تنظیم نهایی restart کنید. سلامت `/api/v1/health/` و `/api/v1/ready/`، ورود مدیر، یک سؤال ساده، منبع مستقیم، تصویر/جدول، پاسخ ناقص، بازخورد و اعتبار را در اپ سرور بررسی کنید.

آزمون‌های اتصال زیر درخواست پولی کوچک دارند؛ پس از آمادگی زیرساخت اجرا شوند:

```bash
python manage.py check_search_model
python manage.py check_embedding_provider
```

برای استریم، ASGI فعلی (`APP_SERVER=asgi`) و عبور بدون buffering در پراکسی لازم است. گزارش کیفیت و سرعت همین نسخه در [سند ۴۵](45-smart-search-question-understanding.fa.md) است؛ بعضی سؤال‌ها هنوز ناقص‌اند و p95 زیر ۲۰ ثانیه اثبات نشده است. مدیر و شناسه‌های صریح `AI_LAB_USER_IDS` برای آزمون محدود قابل استفاده‌اند؛ صرف افزایش درصد rollout بدون گیت انتشار معتبر، دسترسی عمومی نمی‌دهد. مسیر انتشار در [سند ۳۱](31-smart-search-release-evaluation.fa.md) است. تعیین تعرفه در `/manage/app/search-credit/` و افزایش هم‌زمانی پس از آزمون سرور انجام شوند. افزایش concurrency بدون quota کافی ارائه‌دهنده و ظرفیت DB، تضمین سرعت نیست.

## بررسی ابزار انتقال

آزمون‌های PostgreSQL/pgvector، انتقال به chunk UUID و paragraph ID متفاوت، profile/hash/checksum نامنطبق، توقف قبل از اولین write روی فایل نامعتبر، ادامهٔ batch قطع‌شده، حفاظت نسل فعال، بردار متناقض، عدم ارسال API و مجوز/محتوای خصوصی خروجی را پوشش می‌دهند. launcher worker با فرمان جعلی به‌صورت جدا آزموده می‌شود تا اجرا نشدن migration در نقش worker و رد نقش/concurrency نامعتبر مشخص باشد. این آزمون‌ها جای اجرای انتقال کاملِ ۶۷۰هزار بردار در رانفلر را نمی‌گیرند.

در بررسی نهایی محلی، ۳۵۲ آزمون سرچ/کیف اعتبار/نقش کانتینر گذشت، migration جدیدی لازم نبود و syntax دو script بررسی شد. آزمون Redis، فایل پیکربندی 0600، نبود رمز در خروجی و رد رمز دارای newline/فرمت نامعتبر را نیز کنترل کرد. build یا استقرار این imageهای جدید روی رانفلر، export کامل و import کامل مقصد هنوز اجرا نشده‌اند.
