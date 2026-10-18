# دستورهای ایمپورت، اکسپورت و دیتابیس

همهٔ دستورهایی که دادهٔ فارمنتا را وارد می‌کنند، بیرون می‌برند یا روی دیتابیس کار می‌کنند، در یک جا. هر دستور مدیریتی Django از داخل پوشهٔ `backend` اجرا می‌شود:

```bash
cd backend
.venv/bin/python manage.py <دستور> [گزینه‌ها]
```

روی سرور (کانتینر Runflare) همان دستور بدون `.venv/bin/` اجرا می‌شود: `python manage.py <دستور>`.

> قبل از هر ایمپورتی که داده را عوض می‌کند، اول با `--dry-run` اجرا کنید (هر جا که این گزینه هست) و قبل از هر کار پرخطر روی سرور، با `backup_database` نسخهٔ پشتیبان بگیرید.

## فهرست کلی

| دستور | برنامه | کار | چه زمانی |
|---|---|---|---|
| `migrate` | Django | ساختار جدول‌ها را به‌روز می‌کند | خودکار، هر بار راه‌اندازی سرور |
| `createcachetable` | Django | جدول کش دیتابیسی را می‌سازد | خودکار، هر بار راه‌اندازی |
| `load_atc_reference` | drugs | گروه‌های سطح ۱ و ۲ ATC را بارگذاری می‌کند | خودکار، هر بار راه‌اندازی |
| `seed_website` | website | محتوای شروع سایت را می‌سازد | خودکار، هر بار راه‌اندازی |
| `bootstrap_superuser` | accounts | ادمین را از متغیرهای محیطی می‌سازد | خودکار در `release.sh` |
| `export_reference_db` | core | ماشین‌حساب‌ها، گایدلاین‌ها و بیماری‌ها را به فایل SQLite می‌برد | دستی، برای انتقال داده |
| `import_calculators_db` | calculators | فایل `calculators.db` را وارد می‌کند | دستی |
| `import_guidelines_db` | medscape | فایل `guidelines.db` را وارد می‌کند | دستی |
| `import_diseases_db` | medscape | فایل `diseases.db` را وارد می‌کند | دستی |
| `import_openfda` | drugs | پروفایل بالینی داروها را از پایپلاین openFDA وارد می‌کند | دستی |
| `import_calculators` | calculators | ماشین‌حساب‌ها را از خروجی پایپلاین ترجمه وارد می‌کند | دستی |
| `import_medscape_articles` | medscape | مقاله‌های بیماری و گایدلاین را از فایل‌های JSON خام وارد می‌کند | دستی |
| `migrate_uptodate_to_mysql` | uptodate | نسخهٔ SQLite آپ‌تودیت را به MySQL کپی می‌کند | دستی، یک بار |
| `apply_atc_supplement` | drugs | به داروهای بی‌کد ATC کد می‌دهد | دستی |
| `clean_profile_boilerplate` | drugs | جمله‌های بی‌فایده را از خلاصه‌های دارویی پاک می‌کند | دستی |
| `backup_database` | core | نسخهٔ پشتیبان Postgres می‌گیرد | دستی |
| `delete_guest_accounts` | billing | همهٔ حساب‌های مهمان را پاک می‌کند | دستی |

## ۱. دستورهایی که خودکار اجرا می‌شوند

سرور در Runflare با `backend/docker-start.sh` بالا می‌آید و این‌ها را به ترتیب، هر بار، اجرا می‌کند. همه تکرارپذیرند و اجرای دوباره چیزی را خراب نمی‌کند:

```bash
python manage.py migrate --no-input
python manage.py createcachetable
python manage.py load_atc_reference
python manage.py seed_website
python manage.py collectstatic --no-input
```

`backend/release.sh` (برای میزبان‌هایی که مرحلهٔ release جدا دارند) همین‌ها را به‌علاوهٔ `check --deploy` و `bootstrap_superuser` اجرا می‌کند. دادهٔ داروها، ماشین‌حساب‌ها و مقاله‌ها هیچ‌وقت خودکار وارد نمی‌شود؛ با دستورهای بخش ۲ و ۳ وارد می‌شود.

### `load_atc_reference`

گروه‌های ATC سطح ۱ و ۲ (دوزبانه، از `apps/drugs/atc_reference.py`) را در جدول `AtcCategory` می‌گذارد. اگر همهٔ کدها از قبل باشند، کاری نمی‌کند.

| گزینه | کار |
|---|---|
| `--force` | همهٔ ردیف‌ها را دوباره همگام می‌کند؛ بعد از ویرایش نام‌ها در `atc_reference.py` |

### `seed_website`

منوها، بلوک‌های صفحهٔ اصلی، صفحه‌های استاندارد (درباره ما، تماس، قوانین، حریم خصوصی) و لینک دانلود وب‌اپ را می‌سازد. هر گروه فقط وقتی ساخته می‌شود که خالی باشد، پس چیزی که در پنل ویرایش کرده‌اید هرگز بازنویسی نمی‌شود.

| گزینه | کار |
|---|---|
| `--demo` | مقاله، اطلاعیه و نسخهٔ نمونه هم اضافه می‌کند. **روی سرور اصلی اجرا نکنید.** |

### `bootstrap_superuser`

ادمین را از `DJANGO_SUPERUSER_USERNAME`، `DJANGO_SUPERUSER_EMAIL` و `DJANGO_SUPERUSER_PASSWORD` می‌سازد یا به‌روز می‌کند. اگر این سه متغیر تنظیم نباشند، کاری نمی‌کند. گزینه‌های `--username`، `--email` و `--password` جای متغیرها را می‌گیرند؛ رمز را در دستور ننویسید تا در تاریخچهٔ ترمینال نماند.

## ۲. انتقال دادهٔ مرجع بین دو دیتابیس

برای بردن ماشین‌حساب‌ها، گایدلاین‌ها و بیماری‌ها از دیتابیس لپ‌تاپ به سرور (یا هر دیتابیس دیگری). هر مجموعه در یک فایل SQLite مستقل می‌رود. هر فایل یک جدول `meta` دارد که نام مجموعه، نسخهٔ فرمت و تعداد ردیف‌ها را نگه می‌دارد، پس ایمپورت فایل اشتباه یا ناقص را رد می‌کند.

```bash
# روی لپ‌تاپ: خروجی گرفتن
python manage.py export_reference_db --out ~/pharmenta-data
python manage.py export_reference_db --out ~/pharmenta-data --only diseases

# روی مقصد: اول آزمایشی، بعد واقعی
python manage.py import_diseases_db --source ~/pharmenta-data/diseases.db --dry-run
python manage.py import_diseases_db --source ~/pharmenta-data/diseases.db
python manage.py import_guidelines_db --source ~/pharmenta-data/guidelines.db
python manage.py import_calculators_db --source ~/pharmenta-data/calculators.db
```

### `export_reference_db`

| گزینه | پیش‌فرض | کار |
|---|---|---|
| `--out` | `reference-data` | پوشه‌ای که فایل‌های `.db` در آن نوشته می‌شوند |
| `--only` | هر سه | فقط یک مجموعه: `calculators`، `guidelines` یا `diseases`. تکرارپذیر |

فایل اول با پسوند `.partial` نوشته می‌شود و فقط وقتی کامل شد به نام اصلی تغییر می‌کند، پس خروجی نیمه‌کاره هیچ‌وقت شبیه فایل کامل نمی‌شود.

### `import_calculators_db`، `import_guidelines_db`، `import_diseases_db`

هر سه گزینه‌های یکسان دارند. ردیف‌ها اضافه یا در جا به‌روز می‌شوند، پس اجرای دوباره امن است. تصویرهای مقاله‌ها فقط یک بار ذخیره می‌شوند.

| گزینه | کار |
|---|---|
| `--source` (الزامی) | مسیر فایل `.db` که `export_reference_db` ساخته |
| `--dry-run` | کل ایمپورت را اجرا می‌کند و گزارش می‌دهد، بعد همه را برمی‌گرداند |
| `--prune` | ردیف‌هایی از این مجموعه را که در فایل نیستند **پاک می‌کند**. قبلش پشتیبان بگیرید |

همهٔ ایمپورت در یک تراکنش انجام می‌شود؛ اگر وسط کار خطا بدهد، هیچ تغییری نمی‌ماند.

## ۳. ایمپورت از منبع‌های خام

این دستورها دادهٔ اولیه را از خروجی پایپلاین‌ها و اسکرپرها می‌خوانند. منبع‌ها روی لپ‌تاپ‌اند و در گیت نیستند؛ مسیرهای پیش‌فرض مال همان لپ‌تاپ است.

### `import_openfda` — پروفایل بالینی داروها

از دیتابیس SQLite پایپلاین openFDA (فقط خواندنی) دو جدول را می‌خواند: `ingredient_clinical_profiles` (هر ماده با همهٔ بخش‌های بالینی و خلاصهٔ فارسی و انگلیسی) و `ingredient_atc_codes` (منبع پشتیبان کدهای ATC). هر ماده با RXCUI تطبیق داده می‌شود، پس اجرای دوباره امن است.

```bash
python manage.py import_openfda --dry-run
python manage.py import_openfda
python manage.py import_openfda --only-summaries   # فقط خلاصه‌ها
python manage.py import_openfda --only-names       # فقط نام فارسی ماده‌ها
```

| گزینه | پیش‌فرض | کار |
|---|---|---|
| `--source` | `/home/amir/Documents/openfda/pipeline_v2/pipeline_v2.db` | فایل SQLite پایپلاین |
| `--only-summaries` | — | فقط `summary_fa` و `summary_en` بخش‌های موجود را به‌روز می‌کند |
| `--only-names` | — | فقط `name_fa` ماده‌های موجود را از `ingredient_name_fa` به‌روز می‌کند |
| `--limit` | `0` (همه) | حداکثر این تعداد ماده |
| `--dry-run` | — | می‌خواند و گزارش می‌دهد، همهٔ نوشتن‌ها را برمی‌گرداند |

### `import_calculators` — ماشین‌حساب‌ها از پایپلاین ترجمه

نسخهٔ دوزبانهٔ ماشین‌حساب‌ها را از SQLite پایپلاین ترجمه وارد می‌کند و سؤال‌ها، نتیجه‌ها و بررسی‌های خطا را به‌صورت JSON روی هر ماشین‌حساب می‌گذارد. دسته‌ها و برچسب‌ها با `external_id` و ماشین‌حساب‌ها با `uid` تطبیق داده می‌شوند.

| گزینه | پیش‌فرض | کار |
|---|---|---|
| `--source` | `backend/data/calculators_all.sqlite` | فایل SQLite ماشین‌حساب‌ها |
| `--limit` | `0` (همه) | حداکثر این تعداد ماشین‌حساب |
| `--dry-run` | — | گزارش بدون نوشتن |

نکته: الان فایل موجود در `backend/data` به نام `calculators.sqlite` است، نه `calculators_all.sqlite`؛ مسیر را با `--source` بدهید.

### `import_medscape_articles` — مقاله‌های بیماری و گایدلاین

فایل‌های JSON اسکرپر Medscape را وارد می‌کند:

- **بیماری‌ها:** `<dir>/{medicine,pediatrics,surgery}/<specialty>.json`؛ هر مقاله `article_id`، دسته و تخصص خودش را دارد.
- **گایدلاین‌ها:** `<dir>/*.json`؛ دسته همیشه `guideline` است و تخصص از نام فایل گرفته می‌شود.

در مسیر ورود، کدهای تبلیغاتی و شماره‌های ارجاع بی‌لینک (مثل «[8, 6]») از متن پاک می‌شوند و هر تصویر یک بار در جدول `ArticleImage` ذخیره می‌شود. تکرارپذیر است.

| گزینه | پیش‌فرض |
|---|---|
| `--diseases-dir` | `/home/amir/Documents/Medscape/Diseases & Conditions` |
| `--guidelines-dir` | `/home/amir/Documents/Medscape/guidlines` |
| `--disease-images-dir` | `/home/amir/Documents/Medscape/emedicine_images` |
| `--guideline-images-dir` | `/home/amir/Documents/Medscape/guideline_images` |
| `--limit` | `0` (همه)؛ حداکثر مقاله از هر فایل |
| `--dry-run` | — |

برای بردن همین مقاله‌ها به سرور، از بخش ۲ (`export_reference_db` و `import_*_db`) استفاده کنید؛ لازم نیست فایل‌های خام روی سرور باشند.

### `migrate_uptodate_to_mysql` — آپ‌تودیت به MySQL

نسخهٔ SQLite محلی آپ‌تودیت را به دیتابیس MySQL که در `UPTODATE_MYSQL_URL` تعریف شده کپی می‌کند. یک بار بعد از راه‌اندازی آن دیتابیس، و دوباره هر بار که نسخهٔ محلی به‌روز شد.

پیشرفت هر جدول در یک فایل JSON نگه داشته می‌شود و فقط بعد از تأیید MySQL جلو می‌رود؛ اگر ارتباط قطع شود، همان دسته دوباره فرستاده می‌شود.

```bash
python manage.py migrate_uptodate_to_mysql
python manage.py migrate_uptodate_to_mysql --tables content,toc
python manage.py migrate_uptodate_to_mysql --reset --tables fts
```

| گزینه | پیش‌فرض | کار |
|---|---|---|
| `--tables` | همه | زیرمجموعه‌ای از `content`، `toc`، `fts`، `images`، `thumbs`، `abstracts`، `search_topic`، `search_query`، `search_query_topic` |
| `--checkpoint-file` | `~/.uptodate_mysql_migration_checkpoint.json` | فایل پیشرفت |
| `--reset` | — | پیشرفت جدول‌های انتخاب‌شده را صفر می‌کند. `fts` و `search_query` کلید طبیعی ندارند؛ فقط وقتی ریست کنید که آن جدول‌ها را در MySQL هم خالی کرده باشید، وگرنه ردیف تکراری می‌سازد |

## ۴. نگهداری دادهٔ داروها

### `apply_atc_supplement`

به ماده‌هایی که هیچ کد ATC ندارند، کد ATC از فهرست تکمیلی `apps/drugs/data/atc_supplement` می‌دهد، بدون ایمپورت دوبارهٔ openFDA. کدی که منبع داده، هرگز عوض نمی‌شود. اجرای دوم کاری برای انجام پیدا نمی‌کند. درس‌نامه‌ها داروهای تازه را فوراً نشان می‌دهند.

| گزینه | کار |
|---|---|
| `--dry-run` | فقط گزارش تغییرات |

نکته: متن این دستور می‌گوید بعدش `build_question_bank` را اجرا کنید، ولی آن دستور با بانک سؤال قدیمی حذف شده است. سؤال‌ها و فلش‌کارت‌ها حالا از `study_content` می‌آیند (`docs/study-content.md`).

### `clean_profile_boilerplate`

جمله‌های بی‌اطلاعات را از خلاصه‌های فارسی و انگلیسی پروفایل داروها پاک می‌کند: «حساسیت به اجزای دارو»، جمله‌های «اینجا چیزی نیست» و جمله‌های منفی‌ای که اشتباهی زیر موارد مصرف آمده‌اند.

| گزینه | کار |
|---|---|
| `--dry-run` | فقط گزارش |

## ۵. پشتیبان‌گیری و بازگردانی دیتابیس

### `backup_database`

با `pg_dump` (فرمت custom) یک فایل پشتیبان با تاریخ و ساعت می‌سازد. فقط می‌خواند و هیچ داده‌ای را عوض نمی‌کند. فقط Postgres را پشتیبانی می‌کند و `pg_dump` باید نصب باشد.

```bash
python manage.py backup_database
python manage.py backup_database --output-dir ~/backups --name before-prune
python manage.py backup_database --dry-run    # فقط مسیر فایل را نشان می‌دهد
```

| گزینه | پیش‌فرض | کار |
|---|---|---|
| `--output-dir` | `backend/backups` | پوشهٔ فایل پشتیبان |
| `--name` | `database` | پیشوند نام فایل؛ نتیجه: `<name>-YYYYMMDD-HHMMSS.dump` |
| `--dry-run` | — | فقط مسیر را چاپ می‌کند |

برای بازگرداندن یک فایل پشتیبان (پاک‌کردن و جایگزینی دادهٔ مقصد):

```bash
pg_restore --clean --if-exists --no-owner -d "<DATABASE_URL>" backups/database-20261018-120000.dump
```

### اسکریپت‌های انتقال به Runflare (فقط روی لپ‌تاپ)

این‌ها در `backend/exports/` هستند و در گیت نیستند. برای بار اول انتقال دیتابیس لپ‌تاپ به Postgres در Runflare ساخته شدند. رمز دیتابیس را خودشان می‌پرسند؛ آن را در فایل یا دستور ننویسید.

| فایل | کار |
|---|---|
| `transfer_to_runflare.py` | کل دیتابیس محلی را تکه‌تکه و قابل ادامه به Runflare کپی می‌کند: ساختار، داده (INSERT دسته‌ای، چون COPY از پروکسی Runflare رد نمی‌شود)، بعد ایندکس‌ها و کلیدها و مقایسهٔ تعداد ردیف‌ها. بعد از قطع ارتباط، همان دستور را دوباره اجرا کنید. `--target-url` مقصد دیگری می‌دهد. اندازهٔ تکه با `XFER_CHUNK_BYTES` |
| `restore_to_runflare.sh` | فایل `pharmexa_full.dump` را با `pg_restore` در Runflare بازمی‌گرداند و تعداد ردیف‌های جدول‌های اصلی را نشان می‌دهد |
| `reset_runflare_db.sh` | **همهٔ** جدول‌های دیتابیس Runflare را پاک می‌کند. اول فهرست را نشان می‌دهد و فقط با تایپ `YES` ادامه می‌دهد. برگشت‌ناپذیر است |

## ۶. حساب‌ها و سایت

### `delete_guest_accounts`

همهٔ حساب‌های مهمان و پیشرفتشان را پاک می‌کند. تا وقتی دسترسی مهمان در پنل (`/ops/` ← تنظیمات دسترسی) روشن است، اجرا نمی‌شود.

```bash
python manage.py delete_guest_accounts
```

### خروجی از پنل

- **فهرست کاربران (CSV):** در پنل مدیریت فروش (`/ops/users/`) دکمهٔ خروجی، کاربران را با همان فیلتر و جست‌وجوی فعلی در فایل `pharmenta-users-YYYYMMDD.csv` می‌دهد (`/ops/users/export.csv`).

## منبع‌هایی که وارد دیتابیس نمی‌شوند

- **آپ‌تودیت و لکسی‌کامپ:** از فایل SQLite روی دیسک خوانده می‌شوند (۲٫۷ گیگابایت و ۹۵ مگابایت) و روی سرور نیستند؛ آپ‌تودیت می‌تواند با `migrate_uptodate_to_mysql` به MySQL برود.
- **سؤال‌ها و فلش‌کارت‌ها:** در `study_content.db` بیرون از مخزن ساخته می‌شوند و هنوز دستور ایمپورتی ندارند (`docs/study-content.md`).
