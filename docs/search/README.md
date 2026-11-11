# جست‌وجوی فعلی UpToDate و حذف پایلوت هوشمند آفلاین

آخرین تطبیق: ۲۰۲۶/۱۱/۱۱. به درخواست مالک پروژه، موتور آزمایشی هوشمند آفلاین، واژه‌نامه‌های فارسی مخصوص آن، ابزارهای ارزیابی و فرمان ساخت واژه‌نامه از پروژه حذف شدند. برنامهٔ قبلی embedding، Elasticsearch و بستهٔ مستقل مدل ادامه پیدا نمی‌کند. جزئیات حذف و بررسی عدم تغییر مسیر فعلی در [گزارش حذف](../24-offline-smart-search-removal.fa.md) ثبت شده است.

ابزار تازهٔ [فاز صفر سرچ هوشمند آنلاین](../26-smart-search-phase0.fa.md) مستقل از پایلوت حذف‌شده است: ۱۰۰ سؤال، سنجش زمان و توکن و تطبیق ارجاع را برای مسیر فعلی LLM روی UpToDate فراهم می‌کند. بردارسازی اضافه نشده و مسیر عادی جست‌وجو تغییر نکرده است.

[فاز یک](../27-smart-search-preprocessing.fa.md) دادهٔ آمادهٔ نسخه‌دار و [فاز دو](../28-smart-search-lexical.fa.md) رتبه‌بندی منظور سؤال و بازیابی واژگانیِ محدود از همان مقاله را اضافه می‌کنند؛ این مسیرها متعلق به سرچ هوشمند آنلاین‌اند.

[فاز سه](../29-smart-search-local-selection.fa.md) از همان رتبه‌ها برای انتخاب مستقیم بندهای شاهد روی سرور استفاده و فراخوانی جداگانهٔ مدل برای انتخاب بخش را از مسیر پیش‌فرض حذف می‌کند.

[فاز چهار](../30-smart-search-cache-runtime.fa.md) کش خصوصیِ پاسخ کامل، بررسی مجدد منبع و مجوز در hit، اتصال پایدار مدل و بودجهٔ مشترک اجرا را اضافه می‌کند؛ مسیر معمول جست‌وجو مستقل می‌ماند.

[فاز پنج](../31-smart-search-release-evaluation.fa.md) آزمون واقعی ۱۰۰ سؤال، بار احراز هویت‌شده روی دو worker و Redis، زمان نمایش Chrome و کاربرگ خصوصی بازبینی را اضافه می‌کند. نتیجهٔ فعلی blocked است؛ ۶۳ پاسخ کامل از ۹۵ سؤال پزشکی، جای تأیید بالینی یا هدف ۹۵٪ زیر ۲۰ ثانیه را نمی‌گیرد. rollout عمومی فعال نشده است.

[جزئیات خط اول درمان](../32-smart-search-first-line-regimens.fa.md) در سرچ هوشمند، اطلاعات مصرف داروی توصیه‌شده را هم لازم می‌داند؛ شواهد دوز زودتر بررسی می‌شوند و نام داروی تنها پاسخ کامل حساب نمی‌شود. این اصلاح به جست‌وجوی معمول زیر وارد نشده است.

## مسیر عملیاتی حفظ‌شده

جست‌وجویی که اکنون در اپ استفاده می‌شود، از این زنجیره عبور می‌کند و در حذف پایلوت تغییر نکرده است:

| بخش | مسیر |
|---|---|
| صفحهٔ جست‌وجو و پیشنهادها | [UptodateScreen.tsx](../../frontend/src/screens/UptodateScreen.tsx)، [UptodateSuggestionMenu.tsx](../../frontend/src/components/UptodateSuggestionMenu.tsx) |
| انتخاب منبع | [sources.ts](../../frontend/src/offline/sources.ts): ابتدا بستهٔ نصب‌شدهٔ معتبر، در غیر این صورت API |
| جست‌وجوی روی بسته | [uptodateLocal.ts](../../frontend/src/offline/uptodateLocal.ts)، [uptodateSearchCatalog.ts](../../frontend/src/offline/uptodateSearchCatalog.ts) |
| API | [views.py](../../backend/apps/uptodate/views.py): TopicSearchView → [services.py](../../backend/apps/uptodate/services.py): search_page → [search_catalog.py](../../backend/apps/uptodate/search_catalog.py) |
| دادهٔ مرتبط با tagging | مفهوم‌ها، عبارت‌ها و نام‌های جایگزین و ارتباط مقاله‌های snapshot از search.db / جدول‌های متناظر MySQL؛ داده‌های query و query_topic حفظ شده‌اند |
| سازگاری آفلاین | [uptodateSearchSupplement.ts](../../frontend/src/offline/uptodateSearchSupplement.ts)، search_schema: 1 و سازندهٔ بسته در [pack.py](../../backend/apps/offline/pack.py) |

منطق فیلتر تخصص، صفحه‌بندی، تصحیح املا، جست‌وجوی عنوان، پیشنهادها و خواندن آفلاین مقاله تغییر نکرده‌اند. استخراج مقصد پاراگراف در [search_extraction.py](../../backend/apps/uptodate/search_extraction.py) نیز حفظ شد، چون TopicDetailView برای بررسی content hash و anchor و بازکردن مقصد موجود از آن استفاده می‌کند.

## بررسی‌های مسیر فعلی

از frontend:

```bash
node scripts/test-uptodate-search.cjs
node scripts/test-uptodate-search-navigation.cjs
node scripts/test-offline-source-refresh.cjs
npm run typecheck
```

از backend:

```bash
.venv/bin/python manage.py test apps.uptodate apps.offline --noinput
```

گزارش‌های عملیاتی معتبر: [اصلاح tagging، تخصص‌ها و HTML](uptodate-search-html-fix-2026-11-05.fa.md)، [بستهٔ آفلاین](offline-package-2026-11-05.fa.md)، [نقشهٔ جریان](../16-code-flows.md).

## سابقهٔ طرح کنارگذاشته‌شده

[سند ۱۴](../14-search-architecture-proposal.fa.md) وضعیت لغو طرح را ثبت می‌کند. گزارش‌های فازها و [history/](history/README.md) صرفاً سابقه‌اند؛ دستورها و مسیرهای پیاده‌سازی حذف‌شدهٔ آن‌ها قابل اجرا نیستند. کد و مدل تازه‌ای مانند Jev به‌عنوان جایگزین اضافه نشده است. فایل‌های منبع بیرون از مخزن، مدل‌های دانلودشده و کاربرگ‌های خصوصی آزمون در این تغییر پاک نشده‌اند.
