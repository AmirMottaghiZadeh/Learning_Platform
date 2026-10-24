# ۷. داده: منبع‌ها، ایمپورت، اکسپورت و بستهٔ آفلاین

دادهٔ محتوایی فارمنتا از چند پایپلاین و اسکرپر بیرون از این مخزن می‌آید. این فایل توضیح می‌دهد هر داده کجاست، چطور وارد دیتابیس محلی و سرور می‌شود، و همهٔ دستورهای مربوط چه گزینه‌هایی دارند.

هر دستور مدیریتی از پوشهٔ `backend` اجرا می‌شود:

```bash
cd backend
.venv/bin/python manage.py <دستور> [گزینه‌ها]      # لپ‌تاپ
python manage.py <دستور> [گزینه‌ها]                # کنسول سرویس بک‌اند در رانفلر
```

> **قاعدهٔ ایمنی:** هر ایمپورتی که `--dry-run` دارد، اول با همین گزینه اجرا شود. پیش از هر کار پرخطر روی سرور (`--prune`، ایمپورت جایگزین‌کننده، `reset`) بکاپ بگیرید ([09-operations.md](09-operations.md#بکاپ-و-بازیابی)).

## منبع‌ها

| داده | منبع روی لپ‌تاپ | چطور به سرور می‌رسد | کجا ذخیره می‌شود |
|---|---|---|---|
| داروها و خلاصه‌های بالینی | `/home/amir/Documents/openfda/pipeline_v2/pipeline_v2.db` (پایپلاین openFDA، حدود ۲٫۳ گیگ) | روی لپ‌تاپ `import_openfda`، بعد `export_openfda_db` ← `import_openfda_db` روی سرور ([بالا](#انتقال-داروها-به-سرور-با-فایل-قابل‌حمل))، یا `import_openfda` مستقیم با `DATABASE_URL` سرور | Postgres: `drugs_*` |
| گروه‌های ATC سطح ۱ و ۲ | `backend/apps/drugs/atc_reference.py` (داخل کد) | خودکار، هر شروع کانتینر | Postgres: `drugs_atccategory` |
| کد ATC تکمیلی | `backend/apps/drugs/data/atc_supplement` | `apply_atc_supplement` | Postgres |
| ماشین‌حساب‌ها | `backend/data/calculators.sqlite` (پایپلاین ترجمه) | `export_reference_db` ← `import_calculators_db` | Postgres: `calculators_*` |
| بیماری‌ها و گایدلاین‌های Medscape | `/home/amir/Documents/Medscape/...` (JSON و تصویر اسکرپر) | `export_reference_db` ← `import_diseases_db` / `import_guidelines_db` | Postgres: `medscape_*` (تصویرها داخل دیتابیس) |
| سؤال‌ها و فلش‌کارت‌ها | `/home/amir/Documents/openfda/study_content/study_content.db` (ساختهٔ مدل‌های زبانی) | `import_study_content` ← `export_study_content_db` ← `import_study_content_db` | Postgres: `quiz_bankquestion`، `flashcards_flashcardfact` |
| UpToDate | `/home/amir/Documents/UpToDate/` (حدود ۲٫۷ گیگ SQLite) | `migrate_uptodate_to_mysql` | MySQL (`UPTODATE_MYSQL_URL`) |
| Lexicomp | `/home/amir/Documents/Lexicomp_Drug_Interactions/` (`interact.db` حدود ۹۵ مگ، `info.json`) | کپی دستی فایل‌ها روی دیسک سرویس بک‌اند | دیسک (`LEXICOMP_DB_DIR`) |
| بستهٔ آفلاین | از همان فایل‌های UpToDate و Lexicomp | `build_offline_package` و آپلود دستی | Object Storage |
| فایل‌های قابل‌حمل | `/home/amir/Documents/pharmenta-reference-data/` (`calculators.db`، `guidelines.db`، `diseases.db`، `study_content.db`، و بخش‌های داروها در `openfda/`) | آپلود و ایمپورت | — |

حجم دادهٔ دیتابیس محلی در آبان ۱۴۰۵ (برای مقایسه بعد از هر ایمپورت):

| جدول | ردیف |
|---|---|
| `drugs_ingredient` | 1,794 |
| `drugs_ingredientprofilesection` | 21,528 |
| `drugs_atccode` | 590 |
| `drugs_atccategory` | 98 |
| رابطهٔ ماده و ATC | 2,022 |
| `calculators_calculator` | 483 |
| `medscape_article` | 3,199 بیماری + 808 گایدلاین |
| `medscape_articleimage` | 10,605 |
| `quiz_bankquestion` | 6,789 |
| `flashcards_flashcardfact` | 18,556 |

## فهرست همهٔ دستورهای داده

| دستور | اپ | کار | زمان اجرا |
|---|---|---|---|
| `migrate` | Django | ساختار جدول‌ها | خودکار، هر شروع کانتینر |
| `ensure_uptodate_search_index` | uptodate | ایندکس جست‌وجوی عنوان در MySQL | خودکار، هر شروع |
| `createcachetable` | Django | جدول کش دیتابیسی | خودکار، هر شروع |
| `load_atc_reference` | drugs | گروه‌های ATC سطح ۱ و ۲ | خودکار، هر شروع |
| `seed_website` | website | محتوای شروع سایت (فقط بخش‌های خالی) | خودکار، هر شروع |
| `collectstatic` | Django | فایل‌های استاتیک | خودکار، هر شروع |
| `bootstrap_superuser` | accounts | ساخت مدیر از `DJANGO_SUPERUSER_*` | خودکار فقط در `release.sh` |
| `import_openfda` | drugs | پروفایل بالینی داروها | دستی |
| `apply_atc_supplement` | drugs | کد ATC برای ماده‌های بی‌کد | دستی |
| `clean_profile_boilerplate` | drugs | پاک کردن جمله‌های بی‌فایده از خلاصه‌ها | دستی |
| `standardize_pipeline_units` | drugs | واحدهای خلاصه‌های فارسی در فایل پایپلاین به‌صورت نماد انگلیسی | دستی |
| `export_openfda_db` / `import_openfda_db` | drugs | فایل‌های قابل‌حمل داروها (برای سرور بدون فایل پایپلاین) | دستی |
| `import_calculators` | calculators | ماشین‌حساب‌ها از پایپلاین ترجمه | دستی، روی لپ‌تاپ |
| `import_medscape_articles` | medscape | مقاله‌ها از JSON خام اسکرپر | دستی، روی لپ‌تاپ |
| `export_reference_db` | core | فایل قابل‌حمل ماشین‌حساب، گایدلاین و بیماری | دستی، روی لپ‌تاپ |
| `import_calculators_db` / `import_guidelines_db` / `import_diseases_db` | calculators / medscape | ایمپورت فایل قابل‌حمل | دستی |
| `import_study_content` | quiz | سؤال و فلش‌کارت از دیتابیس پایپلاین | دستی، روی لپ‌تاپ |
| `export_study_content_db` | quiz | فایل قابل‌حمل سؤال و فلش‌کارت | دستی، روی لپ‌تاپ |
| `import_study_content_db` | quiz | ایمپورت آن فایل | دستی |
| `migrate_uptodate_to_mysql` | uptodate | کپی UpToDate به MySQL | دستی، روی لپ‌تاپ |
| `build_offline_package` | offline | ساخت بستهٔ آفلاین | دستی، روی لپ‌تاپ |
| `offline_bucket_cors` | offline | تنظیم و بررسی CORS باکت | دستی، یک بار |
| `backup_database` | core | بکاپ Postgres | دستی |
| `delete_guest_accounts` | billing | پاک کردن حساب‌های مهمان | دستی |

## دستورهای خودکار هنگام شروع

`backend/docker-start.sh` در هر شروع کانتینر رانفلر این‌ها را به همین ترتیب اجرا می‌کند و اگر یکی شکست بخورد، کانتینر بالا نمی‌آید. همه تکرارپذیرند:

```bash
python manage.py migrate --no-input
python manage.py ensure_uptodate_search_index
python manage.py createcachetable
python manage.py load_atc_reference
python manage.py seed_website
python manage.py collectstatic --no-input
```

`backend/release.sh` (برای میزبان‌هایی که مرحلهٔ release جدا دارند) همین‌ها را به‌علاوهٔ `check --deploy` و `bootstrap_superuser` اجرا می‌کند. دادهٔ محتوایی هیچ‌وقت خودکار وارد نمی‌شود.

- **`load_atc_reference`**
  - **کار:** گروه‌های ATC را از `apps/drugs/atc_reference.py` در `AtcCategory` می‌گذارد. اگر همه موجود باشند کاری نمی‌کند.
  - **گزینه:** `--force` همه را دوباره همگام می‌کند؛ بعد از ویرایش نام‌ها لازم است.
- **`seed_website`**
  - **کار:** منوها، بلوک‌های صفحهٔ اصلی، برگه‌های «دربارهٔ ما»، «تماس»، «قوانین» و «حریم خصوصی»، و لینک وب‌اپ را می‌سازد. فقط بخش خالی را پر می‌کند و ویرایش‌های پنل را بازنویسی نمی‌کند.
  - **گزینه:** `--demo` مطلب و نسخهٔ نمونه هم می‌سازد. **روی سرور اجرا نکنید.**
- **`bootstrap_superuser`**
  - **کار:** مدیر را از `DJANGO_SUPERUSER_USERNAME`، `_EMAIL` و `_PASSWORD` می‌سازد یا به‌روز می‌کند. بدون آن‌ها کاری نمی‌کند.
  - **گزینه‌ها:** `--username`، `--email` و `--password` جای متغیرها را می‌گیرند. رمز را در خط فرمان ننویسید تا در تاریخچهٔ ترمینال نماند.

## داروها

### `import_openfda`

از SQLite پایپلاین openFDA (فقط خواندنی) دو جدول را می‌خواند:
- **`ingredient_clinical_profiles`:** هر ماده با بخش‌های بالینی و خلاصهٔ فارسی و انگلیسی.
- **`ingredient_atc_codes`:** منبع پشتیبان کدهای ATC.

ماده‌ها با RXCUI تطبیق داده می‌شوند، پس اجرای دوباره امن است.

```bash
python manage.py import_openfda --dry-run
python manage.py import_openfda
python manage.py import_openfda --only-summaries   # فقط خلاصه‌های fa/en
python manage.py import_openfda --only-names       # فقط نام فارسی ماده‌ها (چند ثانیه)
```

| گزینه | پیش‌فرض | کار |
|---|---|---|
| `--source` | `/home/amir/Documents/openfda/pipeline_v2/pipeline_v2.db` | فایل پایپلاین |
| `--only-summaries` | — | فقط `summary_fa` و `summary_en` بخش‌های موجود |
| `--only-names` | — | فقط `name_fa` ماده‌های موجود |
| `--limit` | `0` (همه) | حداکثر تعداد ماده |
| `--dry-run` | — | گزارش و برگرداندن همهٔ تغییرات |

برای ایمپورت مستقیم روی سرور از لپ‌تاپ، رشتهٔ اتصال **خارجی** Postgres رانفلر را بدهید:

```bash
DATABASE_URL="postgresql://<user>:<رمز>@<host خارجی>:<port>/<db>?sslmode=require" \
  .venv/bin/python manage.py import_openfda
```

### انتقال داروها به سرور با فایل قابل‌حمل

سرور فایل پایپلاین openFDA را ندارد. داده‌ای که `import_openfda` روی لپ‌تاپ وارد کرده، با پاک‌سازی‌ها و استانداردسازی واحدها، در چند فایل SQLite جابه‌جا می‌شود: `openfda.part01.db`، `openfda.part02.db` و الی آخر. هیچ فایلی از `--max-mb` بزرگ‌تر نمی‌شود. محتوای فایل‌ها کدهای ATC، داروها، اتصال داروها به ATC و همهٔ بخش‌های پروفایل است (متن برچسب و خلاصه‌های فارسی و انگلیسی).

```bash
# روی لپ‌تاپ
python manage.py export_openfda_db                      # → /home/amir/Documents/pharmenta-reference-data/openfda/

# روی سرور، بعد از رساندن همهٔ بخش‌ها به یک پوشه
python manage.py import_openfda_db --source <پوشه> --dry-run
python manage.py import_openfda_db --source <پوشه>
```

| دستور | گزینه | کار |
|---|---|---|
| `export_openfda_db` | `--out` | پیش‌فرض `/home/amir/Documents/pharmenta-reference-data/openfda` |
| | `--max-mb` | بیشترین حجم هر بخش؛ پیش‌فرض ۲۰۰ |
| `import_openfda_db` | `--source` | پوشهٔ بخش‌ها یا یک بخش؛ پیش‌فرض همان پوشهٔ بالا |
| | `--dry-run` | ایمپورت کامل و برگرداندن |

- **بخش‌ها:** هر بخش جدول `meta` دارد: شناسهٔ خروجی، شمارهٔ بخش، تعداد کل بخش‌ها و تعداد ردیف‌ها. ایمپورت مجموعهٔ ناقص یا بخش‌هایی از دو خروجی متفاوت را رد می‌کند.
- **خروجی دوباره:** بخش‌های خروجی قبلی در پوشه فقط وقتی جایگزین می‌شوند که مجموعهٔ تازه کامل نوشته شده باشد.
- **ایمپورت:** فقط اضافه یا به‌روزرسانی می‌کند و چیزی را پاک نمی‌کند، چون سؤال‌ها و فلش‌کارت‌های هر دارو به آن وابسته‌اند. ردیف‌ها با RxCUI و (دارو، بخش) تطبیق داده می‌شوند. بخش‌ها با MD5 مقایسه می‌شوند، پس از دیتابیس مقصد فقط ردیف‌هایی خوانده و نوشته می‌شوند که فرق دارند. کل کار در یک تراکنش است.
- **حجم فعلی:** حدود ۱۲۷ مگابایت، یعنی یک بخش.

### `apply_atc_supplement`

- **کار:** به ماده‌هایی که هیچ کد ATC ندارند، از فهرست تکمیلی `apps/drugs/data/atc_supplement` کد می‌دهد، بدون ایمپورت دوبارهٔ openFDA. کدی را که از منبع آمده عوض نمی‌کند. درس‌نامه‌ها داروهای تازه را فوراً نشان می‌دهند.
- **گزینه:** `--dry-run` فقط گزارش می‌دهد.
- **نکته:** پیام پایانی دستور هنوز به `build_question_bank` اشاره می‌کند. آن دستور حذف شده است؛ سؤال‌ها حالا از `study_content` می‌آیند.

### `clean_profile_boilerplate`

- **کار:** جمله‌های بی‌اطلاعات را از خلاصه‌های فارسی و انگلیسی پاک می‌کند:
  - «حساسیت به اجزای دارو»
  - جمله‌های منفی‌ای که اشتباهی زیر موارد مصرف آمده‌اند
  - جمله‌هایی که فقط می‌گویند چیزی نیست، ذکر یا گزارش نشده، یا بررسی نشده است: «ندارد»، «None.»، «مطالعهٔ رسمی تداخل دارویی انجام نشده است»، «X مادهٔ کنترل‌شده نیست»
- **قاعدهٔ جمله‌های خالی (`apps/drugs/null_statements.py`):** خطی حذف می‌شود که همهٔ کلمه‌هایش عمومی باشند یا نام خود دارو. یک کلمهٔ مشخص، مثل یک گروه بیمار، یک داروی دیگر یا «خطر»، خط را نگه می‌دارد. بخش بارداری و شیردهی از این قاعده مستثناست.
- **گزینه‌ها:** `--dry-run` فقط گزارش می‌دهد. `--pipeline` همین پاک‌سازی را در فایل پایپلاین openFDA هم انجام می‌دهد. بدون آن، `import_openfda --only-summaries` جمله‌های پاک‌شده را از فایل پایپلاین برمی‌گرداند.
- **پشتیبان:** متن قبلی هر خانهٔ تغییرکردهٔ فایل پایپلاین در جدول `boilerplate_backup_<تاریخ>` همان فایل می‌ماند.

### واحدهای اندازه‌گیری در متن فارسی

- **قاعده:** واحدها در متن فارسی هم با نماد استاندارد انگلیسی نوشته می‌شوند: «۱۰ میلی‌گرم بر کیلوگرم در روز» ← «۱۰ mg/kg/day»، «میلی‌لیتر در دقیقه بر ۱٫۷۳ متر مربع» ← «mL/min/1.73 m²». عددی که واحد اندازه‌اش را می‌گیرد، همراه بازه یا فهرستش، با رقم لاتین نوشته می‌شود: «۲۵ تا ۵۰ میلی‌گرم» ← «25 تا 50 mg». بقیهٔ جمله و عددهای دیگر عوض نمی‌شوند. مدت‌ها («۷ روز»، «هر ۸ ساعت») فارسی می‌مانند.
- **کجا:** قواعد در `apps/core/units_fa.py` است. `import_openfda` و هر دو ایمپورتر ماشین‌حساب آن را روی متن فارسی اجرا می‌کنند. migrationهای `drugs.0006` و `calculators.0007` داده‌های موجود را تبدیل کرده‌اند.
- **`standardize_pipeline_units`:** همین تبدیل را در خود فایل پایپلاین openFDA انجام می‌دهد (`--source`، `--dry-run`). متن قبلی هر خانه در جدول `units_fa_backup_<تاریخ>` همان فایل می‌ماند. بعد از هر تغییری در فایل پایپلاین، `import_openfda --only-summaries` را اجرا کنید تا به Postgres برسد.

## ماشین‌حساب، گایدلاین و بیماری

### ایمپورت از منبع خام (روی لپ‌تاپ)

- **`import_calculators`**
  - **کار:** ماشین‌حساب‌های دوزبانه را از SQLite پایپلاین ترجمه وارد می‌کند. دسته‌ها و برچسب‌ها با `external_id` و ماشین‌حساب‌ها با `uid` تطبیق داده می‌شوند.
  - **گزینه‌ها:** `--source`، `--limit`، `--dry-run`.
  - **نکته:** پیش‌فرض `--source` فایل `backend/data/calculators_all.sqlite` است، ولی فایل موجود `calculators.sqlite` نام دارد؛ مسیر را صریح بدهید.
- **`import_medscape_articles`**
  - **ورودی:**
    - بیماری‌ها: `<dir>/{medicine,pediatrics,surgery}/<specialty>.json`.
    - گایدلاین‌ها: `<dir>/*.json`؛ تخصص از نام فایل گرفته می‌شود.
  - **پاک‌سازی:** کدهای تبلیغاتی و شماره‌های ارجاع بی‌لینک پاک می‌شوند. هر تصویر یک بار در `ArticleImage` ذخیره می‌شود.
  - **گزینه‌ها:**

    | گزینه | پیش‌فرض |
    |---|---|
    | `--diseases-dir` | `/home/amir/Documents/Medscape/Diseases & Conditions` |
    | `--guidelines-dir` | `/home/amir/Documents/Medscape/guidlines` |
    | `--disease-images-dir` | `/home/amir/Documents/Medscape/emedicine_images` |
    | `--guideline-images-dir` | `/home/amir/Documents/Medscape/guideline_images` |
    | `--limit` | `0`؛ حداکثر مقاله از هر فایل |
    | `--dry-run` | — |

### انتقال بین دو دیتابیس با فایل قابل‌حمل

هر مجموعه در یک فایل SQLite مستقل (با تصویرها) جابه‌جا می‌شود. هر فایل جدول `meta` دارد (نام مجموعه، نسخهٔ قالب، تعداد ردیف). ایمپورت، فایل اشتباه یا ناقص را پیش از نوشتن رد می‌کند.

```bash
# روی لپ‌تاپ
python manage.py export_reference_db --out ~/Documents/pharmenta-reference-data
python manage.py export_reference_db --out ~/Documents/pharmenta-reference-data --only diseases

# روی مقصد (بعد از رساندن فایل)
python manage.py import_diseases_db    --source <مسیر>/diseases.db --dry-run
python manage.py import_diseases_db    --source <مسیر>/diseases.db
python manage.py import_guidelines_db  --source <مسیر>/guidelines.db
python manage.py import_calculators_db --source <مسیر>/calculators.db
```

| دستور | گزینه | کار |
|---|---|---|
| `export_reference_db` | `--out` (پیش‌فرض `reference-data`) | پوشهٔ خروجی |
| | `--only` | فقط `calculators`، `guidelines` یا `diseases`؛ تکرارپذیر |
| `import_*_db` | `--source` (الزامی) | فایل `.db` |
| | `--dry-run` | ایمپورت کامل و برگرداندن |
| | `--prune` | ردیف‌هایی از این مجموعه را که در فایل نیستند **پاک می‌کند** |

- **نوشتن امن خروجی:** فایل خروجی اول با پسوند `.partial` نوشته می‌شود و فقط وقتی کامل شد نام اصلی می‌گیرد.
- **تراکنش و تکرار:** هر ایمپورت در یک تراکنش است و اجرای دوباره امن است.
- **حجم تقریبی فایل‌ها:** `calculators.db` حدود ۷ مگ، `guidelines.db` حدود ۱۶۰ مگ، `diseases.db` حدود ۲۹۰ مگ.

## سؤال‌ها و فلش‌کارت‌ها (study_content)

محتوا را مدل‌های زبانی از متن پروفایل خود هر دارو می‌سازند و یک مدل دوم بررسی می‌کند. پایپلاین بیرون از این مخزن است: `/home/amir/Documents/openfda/study_content/` (با `schema.sql` و `README.md`).

قواعد محتوا:
- **سؤال:**
  - فقط از متن پروفایل خود دارو ساخته می‌شود.
  - دوزبانه است، چهار گزینه و یک پاسخ درست دارد.
  - توضیح و نقل‌قول مستند دارد و نقل‌قول با متن منبع تطبیق داده می‌شود.
- **فلش‌کارت:**
  - تلگرافی است: ۲ تا ۶ عبارت و هر عبارت حداکثر ۸ کلمه.
  - فقط این موضوع‌ها را پوشش می‌دهد: موارد مصرف، عوارض شایع و جدی خاص همان دارو، تداخل‌ها و هشدارهای مهم (با منع مصرف مطلق)، هشدار جعبه‌ای، و مکانیسم به‌اختصار.

مسیر از پایپلاین تا سرور:

```bash
# ۱) روی لپ‌تاپ: پایپلاین ← فارمنتای محلی
python manage.py import_study_content --dry-run
python manage.py import_study_content
#    یا از پوشهٔ پایپلاین: python3 10_import_to_pharmenta.py [--dry-run] [--statuses verified,approved] [--export]

# ۲) روی لپ‌تاپ: فایل قابل‌حمل
python manage.py export_study_content_db          # → /home/amir/Documents/pharmenta-reference-data/study_content.db

# ۳) روی سرور، بعد از رساندن فایل
python manage.py import_study_content_db --source <مسیر>/study_content.db --dry-run
python manage.py import_study_content_db --source <مسیر>/study_content.db
```

| دستور | گزینه | کار |
|---|---|---|
| `import_study_content` | `--source` | پیش‌فرض `/home/amir/Documents/openfda/study_content/study_content.db` |
| | `--statuses` | وضعیت‌های واردشونده؛ پیش‌فرض `draft,verified,approved` |
| | `--dry-run` | — |
| `export_study_content_db` | `--out` | پیش‌فرض `/home/amir/Documents/pharmenta-reference-data` |
| `import_study_content_db` | `--source` (الزامی)، `--dry-run`، `--prune` | — |

**تفاوت رفتار:**
- **`import_study_content`:** جدول‌های سؤال و فلش‌کارت را **کاملاً جایگزین** می‌کند.
- **`import_study_content_db`:** اضافه یا به‌روزرسانی می‌کند؛ سؤال‌ها با شناسهٔ پایپلاین و فلش‌کارت‌ها به‌صورت گروه «دارو، بخش، زبان».
  - داروها با RxCUI تطبیق داده می‌شوند. داروی ناموجود روی سرور رد و گزارش می‌شود.
  - کل کار در یک تراکنش است.

## UpToDate

### `migrate_uptodate_to_mysql`

نسخهٔ SQLite محلی را به MySQL که `UPTODATE_MYSQL_URL` نشان می‌دهد کپی می‌کند. یک بار بعد از ساخت MySQL، و دوباره هر بار که نسخهٔ محلی به‌روز شد اجرا می‌شود. پیشرفت هر جدول در یک فایل JSON نگه داشته می‌شود؛ اگر ارتباط قطع شد، همان دستور را دوباره اجرا کنید.

```bash
UPTODATE_MYSQL_URL="mysql://<user>:<رمز>@<host>:<port>/<db>" \
  .venv/bin/python manage.py migrate_uptodate_to_mysql
python manage.py migrate_uptodate_to_mysql --tables content,toc
python manage.py migrate_uptodate_to_mysql --reset --tables fts
```

| گزینه | پیش‌فرض | کار |
|---|---|---|
| `--tables` | همه | زیرمجموعه‌ای از `content`، `toc`، `fts`، `images`، `thumbs`، `abstracts`، `search_topic`، `search_query`، `search_query_topic` |
| `--checkpoint-file` | `~/.uptodate_mysql_migration_checkpoint.json` | فایل پیشرفت |
| `--reset` | — | پیشرفت جدول‌های انتخاب‌شده را صفر می‌کند. جدول‌های `fts` و `search_query` کلید طبیعی ندارند؛ فقط وقتی ریست کنید که همان جدول‌ها را در MySQL هم خالی کرده باشید، وگرنه ردیف تکراری ساخته می‌شود |

### `ensure_uptodate_search_index`

- **کار:** جست‌وجوی UpToDate فقط در عنوان است و MySQL برای آن به ایندکس FULLTEXT روی `title` نیاز دارد. این دستور ایندکس را فقط اگر نباشد می‌سازد. داده یا ایندکس موجود را پاک نمی‌کند.
- **SQLite:** بی‌کار است.
- **اجرای خودکار:** در هر شروع کانتینر اجرا می‌شود.
- **اولین اجرا روی MySQL:** ممکن است طول بکشد. کاربر MySQL باید دسترسی `ALTER` داشته باشد.

## Lexicomp

Lexicomp وارد هیچ دیتابیسی نمی‌شود. برای به‌روز کردن نسخهٔ سرور، `interact.db` و `info.json` تازه را در پوشه‌ای که `LEXICOMP_DB_DIR` سرویس بک‌اند نشان می‌دهد جایگزین کنید و سرویس را ری‌استارت کنید. بعد از به‌روز کردن Lexicomp یا UpToDate، بستهٔ آفلاین تازه هم بسازید (پایین‌تر).

## بستهٔ آفلاین UpToDate و Lexicomp

اپ (اندروید، iOS و وب) می‌تواند UpToDate و Lexicomp را دانلود کند و بدون اینترنت بخواند. بسته‌ها روی لپ‌تاپ از همان فایل‌های SQLite ساخته و دستی در Object Storage رانفلر آپلود می‌شوند.

### پیش‌نیاز

در `backend/.env` لپ‌تاپ:
- **`OFFLINE_PACKAGE_SECRET`:** **دقیقاً همان مقداری که روی سرور است.** اگر فرق کند، دانلود تمام می‌شود ولی بسته باز نمی‌شود. این مقدار بعد از انتشار اولین بسته هرگز عوض نشود؛ عوض کردنش همهٔ بسته‌های دانلودشده را بی‌استفاده می‌کند.
- **`OFFLINE_S3_*`:** فقط برای `offline_bucket_cors` لازم است.

برای ساخت مقدار تازهٔ `OFFLINE_PACKAGE_SECRET` (فقط یک بار، پیش از اولین انتشار)، این را در ترمینال خودتان اجرا کنید و خروجی را در `.env` لپ‌تاپ و env رانفلر بگذارید:

```bash
.venv/bin/python -c "import secrets; print(secrets.token_urlsafe(48))"
```

### ساخت

```bash
.venv/bin/python manage.py build_offline_package uptodate --out ~/offline-packages
.venv/bin/python manage.py build_offline_package lexicomp --out ~/offline-packages
```

| گزینه | کار |
|---|---|
| `uptodate` یا `lexicomp` | کدام بسته |
| `--out` (الزامی) | پوشهٔ خروجی |
| `--source` | پوشهٔ SQLite؛ پیش‌فرض `UPTODATE_DB_DIR` / `LEXICOMP_DB_DIR` |
| `--part-size-mb` | اندازهٔ هر قطعه؛ پیش‌فرض ۱۰۰ |

- **زمان و حجم:** UpToDate حدود ۴ دقیقه طول می‌کشد (حدود ۱ گیگ در ۱۱ قطعه). Lexicomp چند ثانیه (حدود ۱۴ مگ در ۱ قطعه).
- **بررسی خودکار:** دستور در پایان بسته را با کلید خودش باز می‌کند تا از سالم بودنش مطمئن شود.

ساختار خروجی:

```
~/offline-packages/
  uptodate/
    latest.json
    uptodate-1-20261023-5ad32e/  part-000.bin … part-010.bin, manifest.json
  lexicomp/
    latest.json
    lexicomp-202606-20261023-067e6e/  part-000.bin, manifest.json
```

### آپلود

ساختار پوشه‌ها را عیناً در باکت `pharmenta-dl` نگه دارید (اگر `OFFLINE_S3_PREFIX` دارید، زیر همان پیشوند):

1. اول پوشهٔ نسخه را آپلود کنید: `uptodate/<build>/` با همهٔ `part-*.bin`ها.
2. **آخر از همه** `uptodate/latest.json` را آپلود کنید و نسخهٔ قبلی را جایگزین کنید. اپ هر نسخه‌ای که `latest.json` بگوید دانلود می‌کند؛ اگر این فایل پیش از قطعه‌ها برسد، دانلود کاربران خطا می‌دهد.
3. سرور `latest.json` را ۵ دقیقه کش می‌کند. بعد از آن، نسخهٔ جدید در اپ با نقطهٔ «نسخهٔ جدید» روی دکمهٔ دانلود دیده می‌شود.
4. پوشهٔ نسخهٔ قبلی را چند روز نگه دارید تا دانلودهای نیمه‌کاره تمام شوند، بعد پاکش کنید.
5. همین کار را برای `lexicomp/` تکرار کنید.

### CORS و بررسی باکت

باکت باید **خصوصی** باشد. نسخهٔ وب برای دانلود از باکت به CORS نیاز دارد: `GET` و `HEAD` از `https://app.pharmenta.ir`، با هدر `Range`، و expose کردن `Content-Length`، `Content-Range` و `Accept-Ranges`. پنل رانفلر برای CORS گزینه‌ای ندارد؛ این دستور آن را از راه API خود S3 می‌گذارد و مثل مرورگر امتحان می‌کند:

```bash
.venv/bin/python manage.py offline_bucket_cors            # تنظیم و بررسی (یک بار)
.venv/bin/python manage.py offline_bucket_cors --show     # فقط بررسی
```

خروجی سالم:

```
OK   Preflight from https://app.pharmenta.ir: HTTP 200, allow-origin=https://app.pharmenta.ir
OK   Signed download from https://app.pharmenta.ir: HTTP 206, allow-origin=https://app.pharmenta.ir
The bucket is private (unsigned download: HTTP 403).
```

| گزینه | کار |
|---|---|
| `--origin` | مبدأ مجاز؛ تکرارپذیر؛ پیش‌فرض `https://app.pharmenta.ir` |
| `--show` | فقط قانون فعلی را نشان می‌دهد و بررسی می‌کند |

### بررسی کامل بودن آپلود

این دستور فقط می‌خواند. برای هر بسته نشان می‌دهد همهٔ قطعه‌های نسخهٔ فعلی در باکت هستند و حجمشان درست است:

```bash
.venv/bin/python manage.py shell -c "
from django.conf import settings as s
from apps.offline import storage
c = storage._s3()
for ds in ('uptodate', 'lexicomp'):
    m = storage.latest_manifest(ds)
    if not m: print(ds, 'latest.json not found'); continue
    bad = [f['name'] for f in m['files']
           if c.head_object(Bucket=s.OFFLINE_S3_BUCKET, Key=storage._prefix()+ds+'/'+m['build']+'/'+f['name'])['ContentLength'] != f['size']]
    print(ds, m['build'], 'OK' if not bad else bad)
"
```

## انتقال کامل دیتابیس به رانفلر

برای اولین انتقال دیتابیس لپ‌تاپ به Postgres رانفلر، اسکریپت‌هایی در `backend/exports/` ساخته شده بود. این پوشه در گیت نیست و ممکن است روی لپ‌تاپ نباشد. همهٔ اسکریپت‌ها رمز دیتابیس را خودشان می‌پرسند؛ آن را در فایل یا خط فرمان ننویسید.

| فایل | کار |
|---|---|
| `transfer_to_runflare.py` | کپی تکه‌تکه و قابل ادامهٔ کل دیتابیس: ساختار، داده (INSERT دسته‌ای، چون COPY از پروکسی رانفلر رد نمی‌شود)، ایندکس‌ها و کلیدها، و مقایسهٔ تعداد ردیف. بعد از قطع ارتباط دوباره اجرا شود. `--target-url` مقصد دیگری می‌دهد؛ اندازهٔ تکه با `XFER_CHUNK_BYTES` |
| `restore_to_runflare.sh` | بازگردانی `pharmexa_full.dump` با `pg_restore` و نمایش تعداد ردیف جدول‌های اصلی |
| `reset_runflare_db.sh` | **همهٔ** جدول‌های دیتابیس رانفلر را پاک می‌کند؛ فقط با تایپ `YES`. برگشت‌ناپذیر |

راه دیگر بدون اسکریپت: بکاپ با `backup_database` و بازگردانی با `pg_restore` ([09-operations.md](09-operations.md#بکاپ-و-بازیابی)).

برای به‌روز کردن فقط داروها، انتقال کامل لازم نیست: `export_openfda_db` و `import_openfda_db` ([بالا](#انتقال-داروها-به-سرور-با-فایل-قابل‌حمل)).

## حساب‌ها

- **`delete_guest_accounts`:** همهٔ حساب‌های مهمان و پیشرفتشان را پاک می‌کند. تا وقتی دسترسی مهمان در کنسول روشن است اجرا نمی‌شود.
- **خروجی کاربران:** در کنسول فروش (`/ops/users/`) دکمهٔ خروجی، کاربران را با همان فیلتر فعلی در `pharmenta-users-YYYYMMDD.csv` می‌دهد.
- **خروجی خبرنامه:** در پنل سایت (`/panel/subscribers/`) دکمهٔ خروجی، فهرست مشترکان خبرنامه را می‌دهد.
