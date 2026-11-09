# ۱۰. مرجع سریع دستورها

همهٔ دستورهای پروژه در یک جا. توضیح کامل هر کدام در فایلی است که در ستون آخر آمده.

دستورهای `manage.py`:
- **روی لپ‌تاپ:** از پوشهٔ `backend` با `.venv/bin/python manage.py ...` اجرا می‌شوند.
- **روی سرور:** در کنسول سرویس بک‌اند رانفلر با `python manage.py ...` اجرا می‌شوند.
- **راهنما:** `manage.py <دستور> --help` گزینه‌های هر دستور را نشان می‌دهد.

## توسعهٔ محلی

| دستور | کار |
|---|---|
| `cd backend && python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt` | نصب بک‌اند |
| `.venv/bin/python manage.py migrate` | ساخت یا به‌روزرسانی جدول‌ها |
| `.venv/bin/python manage.py createsuperuser` | ساخت مدیر |
| `.venv/bin/python manage.py runserver 127.0.0.1:8000` | اجرای بک‌اند |
| `.venv/bin/python manage.py shell` | شِل Django |
| `.venv/bin/python manage.py makemigrations <app>` | ساخت مایگریشن بعد از تغییر مدل |
| `cd frontend && npm ci` | نصب اپ |
| `npm run web` | وب‌اپ روی `http://localhost:8081` |
| `npm start` / `npm run android` / `npm run ios` | سرور Expo |
| `npx expo start --dev-client` | اجرا روی گوشی با development build |
| `docker compose up --build` | کل پشته در داکر |

جزئیات: [02-local-setup.md](02-local-setup.md)

## تست و بررسی

| دستور | کار |
|---|---|
| `.venv/bin/python manage.py test` | همهٔ تست‌های بک‌اند |
| `.venv/bin/python manage.py test apps.<app>` | تست یک اپ |
| `.venv/bin/python manage.py check` | بررسی پیکربندی |
| `DJANGO_SETTINGS_MODULE=config.settings.production .venv/bin/python manage.py check --deploy` | بررسی آمادگی production (با env کامل) |
| `.venv/bin/python manage.py makemigrations --check --dry-run` | مایگریشن جاافتاده |
| `cd frontend && npm run typecheck` | TypeScript |
| `npm run build:web` | ساخت خروجی وب در `frontend/dist/` |

بررسی‌های رفتاری موجود، از پوشهٔ `frontend` و پس از `npm ci` اجرا می‌شوند:

| دستور | دامنهٔ بررسی |
|---|---|
| `node scripts/test-uptodate-search.cjs` | جست‌وجوی TypeScript، پیشنهادها و سازگاری بسته‌های قدیمی |
| `node scripts/test-offline-source-refresh.cjs` | بی‌اعتبار شدن پاسخ‌های کش‌شده پس از تعویض build داده |
| `node scripts/test-uptodate-search-navigation.cjs` | اسکریپت جست‌وجو و جابه‌جایی در خوانندهٔ مقاله |
| `node --test scripts/announcement-calculator.test.cjs` | رفتارهای اعلانات و ماشین‌حساب |

این اسکریپت‌ها در مخزن وجود دارند، اما workflow فعلی CI فرانت‌اند فقط `typecheck` و `build:web` را اجرا می‌کند. نقشهٔ فایل‌های مسئول هر مسیر در [16-code-flows.md](16-code-flows.md) است.

## دستورهای مدیریتی Django (همه)

| دستور | گزینه‌های اصلی | کار | جزئیات |
|---|---|---|---|
| `migrate` | `<app> <migration>` | اعمال یا برگرداندن مایگریشن | — |
| `createcachetable` | — | جدول کش دیتابیسی | [07](07-data.md) |
| `collectstatic` | `--no-input` | فایل‌های استاتیک | — |
| `createsuperuser` | — | مدیر | — |
| `bootstrap_superuser` | `--username --email --password` | مدیر از `DJANGO_SUPERUSER_*` | [07](07-data.md) |
| `load_atc_reference` | `--force` | گروه‌های ATC سطح ۱ و ۲ | [07](07-data.md) |
| `seed_website` | `--demo` (نه روی سرور) | محتوای شروع سایت | [07](07-data.md) |
| `seed_seo_content` | `--dry-run` | مقاله‌های اصلی سئو و صفحهٔ «روش تهیه و بازبینی محتوا» به‌صورت پیش‌نویس، و پیوند «دارونامه» در منوها (یک بار) | [12](12-website.md) |
| `import_openfda` | `--source --only-summaries --only-names --limit --dry-run` | داروها از پایپلاین openFDA | [07](07-data.md) |
| `apply_atc_supplement` | `--dry-run` | کد ATC برای ماده‌های بی‌کد | [07](07-data.md) |
| `fix_profile_text` | `--dry-run --show --pipeline` | گروه‌های عوارض در خط جدا، حذف توضیح دربارهٔ متن منبع | [07](07-data.md) |
| `clean_profile_boilerplate` | `--dry-run --pipeline` | پاک‌سازی خلاصه‌ها | [07](07-data.md) |
| `standardize_pipeline_units` | `--source --dry-run` | واحدهای فارسی فایل پایپلاین به نماد انگلیسی | [07](07-data.md) |
| `export_openfda_db` | `--out --max-mb` | خروجی داروها در بخش‌های حداکثر ۲۰۰ مگی | [07](07-data.md) |
| `import_openfda_db` | `--source --dry-run` | ایمپورت آن بخش‌ها (روی سرور) | [07](07-data.md) |
| `import_calculators` | `--source --limit --dry-run` | ماشین‌حساب از پایپلاین ترجمه | [07](07-data.md) |
| `import_medscape_articles` | `--diseases-dir --guidelines-dir --disease-images-dir --guideline-images-dir --limit --dry-run` | مقاله از JSON اسکرپر | [07](07-data.md) |
| `export_reference_db` | `--out --only` | فایل قابل‌حمل ماشین‌حساب، گایدلاین و بیماری | [07](07-data.md) |
| `import_calculators_db` | `--source --dry-run --prune` | ایمپورت `calculators.db` | [07](07-data.md) |
| `import_guidelines_db` | `--source --dry-run --prune` | ایمپورت `guidelines.db` | [07](07-data.md) |
| `import_diseases_db` | `--source --dry-run --prune` | ایمپورت `diseases.db` | [07](07-data.md) |
| `import_study_content` | `--source --statuses --dry-run` | سؤال و نکتهٔ آموزشی از پایپلاین (جایگزین کامل) | [07](07-data.md) |
| `export_study_content_db` | `--out` | فایل قابل‌حمل سؤال و نکتهٔ آموزشی | [07](07-data.md) |
| `import_study_content_db` | `--source --dry-run --prune` | ایمپورت فایل قابل‌حمل سؤال و نکتهٔ آموزشی | [07](07-data.md) |
| `migrate_uptodate_to_mysql` | `--tables --checkpoint-file --reset` | کپی UpToDate به MySQL | [07](07-data.md) |
| `ensure_uptodate_search_index` | — | ایندکس جست‌وجوی عنوان MySQL | [07](07-data.md) |
| `build_search_lexicon` | `--pipeline --source` | نام فارسی داروها ← مفاهیم UpToDate برای جست‌وجوی هوشمند | [search](search/phase-1-concept-lexicon-2026-10-31.fa.md) |
| `build_offline_package` | `uptodate\|lexicomp --out --source --part-size-mb` | ساخت بستهٔ آفلاین | [07](07-data.md) |
| `prepare_offline_upload` | `uptodate\|lexicomp --out --source --part-size-mb --existing` | ساخت و بررسی فایل‌های قابل آپلود و راهنمای ترتیب آپلود | [07](07-data.md) |
| `offline_bucket_cors` | `--origin --show` | تنظیم و بررسی CORS باکت | [07](07-data.md) |
| `backup_database` | `--output-dir --name --dry-run` | بکاپ Postgres | [09](09-operations.md) |
| `delete_guest_accounts` | — | پاک کردن حساب‌های مهمان | [07](07-data.md) |

## ساخت دوبارهٔ بستهٔ UpToDate با جست‌وجوی مفهومی

از پوشهٔ `backend`، با همان `OFFLINE_PACKAGE_SECRET` زمان ساخت بستهٔ قبلی و سرور:

```bash
.venv/bin/python manage.py prepare_offline_upload uptodate \
  --source /home/amir/Documents/UpToDate \
  --out /home/amir/offline-packages
```

این یک دستور کامل برای ساخت فایل‌های قابل آپلود است: بسته را می‌سازد، اندازه و SHA-256 و MD5 تمام قطعه‌ها را بررسی می‌کند، index را با کلید ساخت باز می‌کند و برای UpToDate وجود دادهٔ مفهومی را می‌سنجد. راهنمای نهایی در `<out>/<dataset>/UPLOAD.fa.md` ساخته می‌شود. این دستور خودش چیزی در باکت آپلود نمی‌کند و رمزگشایی تمام مقاله‌ها را انجام نمی‌دهد.

برای بررسی و آماده‌سازی همان بستهٔ ساخته‌شده، بدون ساخت دوباره:

```bash
.venv/bin/python manage.py prepare_offline_upload uptodate \
  --out /home/amir/offline-packages --existing
```

برای Lexicomp نیز همین دستور با `lexicomp` و مسیر منبع خودش قابل استفاده است. `--existing` با `--source` ترکیب نمی‌شود.

خروجی جدید `search_schema: 1` دارد و واژه‌نامه، نگاشت مفهوم‌ها، اولویت پیشنهادها و همهٔ تخصص‌های مقاله را داخل index رمزگذاری‌شده نگه می‌دارد. پس از دانلود و با مجوز معتبر، این جست‌وجو به اینترنت یا دریافت مکمل نیاز ندارد. برای استفاده از آن، **کلاینت جدید اپ هم باید منتشر شود**؛ APK قدیمی صرفاً با دریافت دادهٔ تازه، الگوریتم جدید را اجرا نمی‌کند.

ساخت تأییدشدهٔ ۵ نوامبر ۲۰۲۶: `uptodate-1-20261105-11f5a4`، شامل ۱۱ قطعه با مجموع ۱٬۰۸۵٬۴۸۵٬۱۰۸ بایت. ابتدا همهٔ فایل‌های پوشهٔ این build را زیر `uptodate/<build>/` آپلود کنید؛ سپس `uptodate/latest.json` محلی را جایگزین کنید. دیتابیس خام، فایل env یا کلیدها جزو آپلود نیستند. Lexicomp در این به‌روزرسانی تغییر نکرده است.

گزارش ساخت و آزمون: [search/offline-package-2026-11-05.fa.md](search/offline-package-2026-11-05.fa.md). جزئیات نگهداری و جایگزینی: [13-offline-storage.md](13-offline-storage.md).

## دیپلوی و گیت

| دستور | کار |
|---|---|
| `git push origin main` | دیپلوی بک‌اند و (اگر `frontend/` عوض شده) ساخت دوبارهٔ `deploy-web` |
| `git fetch origin && git log -1 --format='%h %s' origin/deploy-web` | بررسی به‌روز بودن `deploy-web` |
| `git diff --stat main origin/deploy-web` | باید فقط `Dockerfile` فرق کند |
| `git revert <sha> && git push` | برگرداندن یک دیپلوی خراب |

جزئیات: [08-deployment.md](08-deployment.md)

## اپ موبایل (EAS)

| دستور | کار |
|---|---|
| `npm i -g eas-cli && eas login` | نصب و ورود (یک بار) |
| `npm run release -- patch\|minor\|major [--dry-run]` | بالا بردن نسخه، CHANGELOG، کامیت و تگ `app-vX.Y.Z` (در `frontend/`) |
| `eas build --platform android --profile production` | APK انتشار (arm64 و armv7) |
| `eas build --platform android --profile production-arm64` | APK کوچک‌تر، فقط arm64 |
| `eas build --platform android --profile play` | app bundle برای Google Play |
| `eas build --platform android --profile preview` | APK آزمایشی |
| `eas build --platform android --profile development` | development build |
| `eas build --platform ios --profile production` | بیلد iOS |
| `eas credentials` | دیدن و پشتیبان‌گیری کلید امضا |

## عیب‌یابی

| دستور | کار |
|---|---|
| `curl -s https://api.pharmenta.ir/api/v1/ready/` | سلامت بک‌اند، دیتابیس و کش |
| `curl -sSI https://app.pharmenta.ir/ \| head -1` | وب‌اپ باز است؟ |
| `echo \| openssl s_client -connect <host>:443 -servername <host> 2>/dev/null \| openssl x509 -noout -issuer -enddate` | صادرکننده و انقضای گواهی SSL |
| `.venv/bin/python manage.py offline_bucket_cors --show` | CORS و خصوصی بودن باکت |
| `adb devices` | گوشی اندروید وصل است؟ (برای اشکال‌زدایی وب‌اپ در Chrome گوشی از `chrome://inspect`) |

## پایپلاین study_content (بیرون از مخزن)

| دستور | کار |
|---|---|
| `cd /home/amir/Documents/openfda/study_content && python3 10_import_to_pharmenta.py` | ورود محتوای تازه به فارمنتای محلی |
| `python3 10_import_to_pharmenta.py --dry-run` | فقط گزارش |
| `python3 10_import_to_pharmenta.py --statuses verified,approved` | فقط موارد بررسی‌شده |
| `python3 10_import_to_pharmenta.py --export` | بعد از ورود، فایل قابل‌حمل را هم می‌سازد |

## پشتیبانی، دستگاه و فعالیت

از `backend/`:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py create_support_push_keys --configure-local
.venv/bin/python manage.py retry_support_notifications
.venv/bin/python manage.py test apps.accounts.test_devices apps.support apps.activity --noinput
```

از `frontend/`:

```bash
node scripts/test-reference-updates.cjs
node scripts/test-uptodate-search-navigation.cjs
npm run typecheck
npm run build:web
```

ساخت کلید، هویت موجود را بازنویسی نمی‌کند. تنظیم Firebase، کلید FCM v1 و بیلد جدید اندروید طبق [سند ۱۷](17-sessions-activity-support.fa.md) انجام می‌شود.

فرمان `retry_support_notifications` به پرچم `SUPPORT_PUSH_NOTIFICATIONS_ENABLED` وابسته است: در حالت `False`، pending/failedها را کنار می‌گذارد و هیچ ارسال یا enqueue انجام نمی‌دهد؛ در حالت `True`، ارسال مجدد را انجام می‌دهد. [راهنمای کامل اعلان‌ها](18-notifications-setup.fa.md).


## دریافت اطلاعات شیمیایی دارو

از `backend`: `python manage.py import_pubchem --workers 4`؛ برای نمونه `--limit 20` یا `--rxcui 161`. نامزدها خودکار تأیید نمی‌شوند؛ [دریافت، بازبینی و انتشار](21-drug-chemistry.fa.md).
