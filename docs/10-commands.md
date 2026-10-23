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
| `import_openfda` | `--source --only-summaries --only-names --limit --dry-run` | داروها از پایپلاین openFDA | [07](07-data.md) |
| `apply_atc_supplement` | `--dry-run` | کد ATC برای ماده‌های بی‌کد | [07](07-data.md) |
| `clean_profile_boilerplate` | `--dry-run` | پاک‌سازی خلاصه‌ها | [07](07-data.md) |
| `import_calculators` | `--source --limit --dry-run` | ماشین‌حساب از پایپلاین ترجمه | [07](07-data.md) |
| `import_medscape_articles` | `--diseases-dir --guidelines-dir --disease-images-dir --guideline-images-dir --limit --dry-run` | مقاله از JSON اسکرپر | [07](07-data.md) |
| `export_reference_db` | `--out --only` | فایل قابل‌حمل ماشین‌حساب، گایدلاین و بیماری | [07](07-data.md) |
| `import_calculators_db` | `--source --dry-run --prune` | ایمپورت `calculators.db` | [07](07-data.md) |
| `import_guidelines_db` | `--source --dry-run --prune` | ایمپورت `guidelines.db` | [07](07-data.md) |
| `import_diseases_db` | `--source --dry-run --prune` | ایمپورت `diseases.db` | [07](07-data.md) |
| `import_study_content` | `--source --statuses --dry-run` | سؤال و فلش‌کارت از پایپلاین (جایگزین کامل) | [07](07-data.md) |
| `export_study_content_db` | `--out` | فایل قابل‌حمل سؤال و فلش‌کارت | [07](07-data.md) |
| `import_study_content_db` | `--source --dry-run --prune` | ایمپورت فایل قابل‌حمل سؤال و فلش‌کارت | [07](07-data.md) |
| `migrate_uptodate_to_mysql` | `--tables --checkpoint-file --reset` | کپی UpToDate به MySQL | [07](07-data.md) |
| `ensure_uptodate_search_index` | — | ایندکس جست‌وجوی عنوان MySQL | [07](07-data.md) |
| `build_offline_package` | `uptodate\|lexicomp --out --source --part-size-mb` | ساخت بستهٔ آفلاین | [07](07-data.md) |
| `offline_bucket_cors` | `--origin --show` | تنظیم و بررسی CORS باکت | [07](07-data.md) |
| `backup_database` | `--output-dir --name --dry-run` | بکاپ Postgres | [09](09-operations.md) |
| `delete_guest_accounts` | — | پاک کردن حساب‌های مهمان | [07](07-data.md) |

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
| `eas build --platform android --profile production` | APK انتشار |
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
