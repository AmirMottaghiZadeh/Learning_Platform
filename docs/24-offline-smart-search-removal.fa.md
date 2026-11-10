# ۲۴. حذف پایلوت جست‌وجوی هوشمند آفلاین

تاریخ: ۲۰۲۶/۱۱/۱۰. درخواست مالک: حذف کامل پروژهٔ قبلی جست‌وجوی هوشمند آفلاین، با شرط صریح دست‌نخوردن جست‌وجوی مورد استفادهٔ اپ. این تغییر جایگزین تازه‌ای اضافه نمی‌کند.

## نتیجه

۲۷ فایلِ مخصوص پایلوت از مخزن حذف شدند: موتور فارسی و سلسله‌مراتبی، منطق عمق درخواست، اتصال snapshot مخصوص آن موتور، واژه‌نامهٔ اختصاصی، فرمان تولید واژه‌نامه، تست‌های همان موتور و ابزارها و داده‌های ارزیابی. طرح ۱۰ فازیِ embedding/Elasticsearch/بستهٔ مستقل مدل لغو شد؛ گزارش‌های قدیمی با هشدار «سند تاریخی و غیرقابل اجرا» باقی ماندند و ارجاع به فایل حذف‌شده به متن مسیر تاریخی تبدیل شد.

در بررسی وابستگی‌ها هیچ ارجاعی از کد عملیاتی باقی‌مانده به این ماژول‌های حذف‌شده وجود نداشت. هیچ endpoint، مدل دیتابیس، migration، وابستگی npm/pip، startup script یا فایل فرانت‌اند برای حذف این پایلوت نیاز به تغییر نداشت.

## جست‌وجوی فعلی که حفظ شد

- صفحهٔ UpToDate، پیشنهادها، فیلتر تخصص، تعداد نتایج و صفحه‌بندی.
- نگاشت query و query_topic، مفاهیم، نام‌های جایگزین و tagging دیتابیس snapshot؛ مسیر آنلاین و مسیر خواندن بستهٔ آفلاین.
- search_catalog.py، services.py، views.py، urls.py و mysql_schema.py در backend/apps/uptodate، از جمله فرمان ensure_uptodate_search_index.
- frontend/src/offline/ شامل sources.ts، uptodateLocal.ts، uptodateSearchCatalog.ts، uptodateSearchSupplement.ts؛ ساخت و نصب و مجوز بسته‌ها و کش‌ها.
- search_extraction.py، تست آن و قرارداد search_content_hash/search_anchor؛ TopicDetailView و خوانندهٔ فعلی برای مقصد مقاله از این قابلیت استفاده می‌کنند. حفظ این فایل به معنی حفظ موتور پایلوت نیست.
- دادهٔ منبع UpToDate، فایل‌های search.db/fts.db/content.db/toc.db، جدول‌های MySQL، محتوای PostgreSQL و بسته‌های دانلودی.

[زنجیرهٔ فعلی فایل‌ها](search/README.md) و [نقشهٔ جریان](16-code-flows.md) مرجع رفتار جاری‌اند. حذف «هوشمند آفلاین» به معنی حذف قابلیت آفلاین جست‌وجوی فعلی اپ یا دانلود مقاله‌ها نیست.

## فهرست فایل‌های حذف‌شده

- `backend/apps/uptodate/search_concepts.py`
- `backend/apps/uptodate/search_hierarchy.py`
- `backend/apps/uptodate/search_hierarchy_source.py`
- `backend/apps/uptodate/search_request.py`
- `backend/apps/uptodate/test_search_concepts.py`
- `backend/apps/uptodate/test_search_hierarchy.py`
- `backend/apps/uptodate/test_search_request.py`
- `backend/apps/uptodate/management/commands/build_search_lexicon.py`
- `backend/apps/uptodate/search_lexicon/common_fa.txt`
- `backend/apps/uptodate/search_lexicon/concepts_fa.csv`
- `backend/apps/uptodate/search_lexicon/disambiguation.csv`
- `backend/apps/uptodate/search_lexicon/drug_stems.csv`
- `backend/apps/uptodate/search_lexicon/drugs_fa.csv`
- `backend/apps/uptodate/search_lexicon/monograph_sections.csv`
- `backend/apps/uptodate/search_lexicon/terms.csv`
- `docs/search/eval/build_common_words.py`
- `docs/search/eval/build_judging_workbook.py`
- `docs/search/eval/build_lexicon_review.py`
- `docs/search/eval/dev-judgments.csv`
- `docs/search/eval/dev-queries.csv`
- `docs/search/eval/embedding_eval.py`
- `docs/search/eval/import_judgments.py`
- `docs/search/eval/lexicon_coverage.py`
- `docs/search/eval/lexicon_parallel.py`
- `docs/search/eval/negative-queries.csv`
- `docs/search/eval/negative_queries.py`
- `docs/search/eval/translit_recall.py`

## محدودهٔ داده‌های بیرون از مخزن

مدل‌های دانلودشده، محیط آزمایشی embedding و کاربرگ‌های خصوصی در مسیرهای قبلی بیرون از مخزن (مانند pharmenta-search-eval) در این تغییر حذف نشده‌اند. کدی برای استفاده از آن‌ها در پروژه باقی نمانده است. آزمون‌های پنهان خوانده یا تغییر داده نشدند. نسخهٔ قدیمی کد و گزارش‌ها همچنان از تاریخچهٔ Git قابل بازیابی است.

## اعتبارسنجی

پیش از حذف، SHA-256 تعداد ۳۹۳ فایل عملیاتی شامل تمام فایل‌های tracked فرانت‌اند و مسیرهای uptodate/offline/config بک‌اند (به‌جز فایل‌های مخصوص حذف) ثبت شد. پس از حذف، **هر ۳۹۳ فایل دقیقاً با مقدار اولیه برابر بود**؛ هیچ تغییر محتوایی در کد جست‌وجوی فعال یا اپ انجام نشد. بررسی ارجاع‌های اجرایی نیز وابستگی باقی‌مانده به ماژول‌های حذف‌شده نشان نداد.

تست‌های موجود، بدون تغییر خود تست‌های مسیر فعال، اجرا شدند:

| بررسی | نتیجه |
|---|---|
| backend: apps.uptodate و apps.offline | ۱۰۱ تست، موفق |
| test-uptodate-search.cjs | مفهوم/tagging، تخصص، صفحه‌بندی، عنوان و بستهٔ قدیمی موفق؛ قبل و بعد حذف |
| test-uptodate-search-navigation.cjs | مقصد جست‌وجو و HTML خواننده موفق؛ قبل و بعد حذف |
| test-offline-source-refresh.cjs | نصب، تعویض، حذف بسته و بی‌اعتبارسازی کش جست‌وجو بدون شبکه موفق |
| npm run typecheck | موفق |

دستورها از frontend:

```bash
node scripts/test-uptodate-search.cjs
node scripts/test-uptodate-search-navigation.cjs
node scripts/test-offline-source-refresh.cjs
npm run typecheck
```

دستور تست بک‌اند از backend:

```bash
.venv/bin/python manage.py test apps.uptodate apps.offline --noinput
```

اجرای ثبت‌شده از تنظیمات موقت تست با hasher سریع استفاده کرد؛ تغییری در تنظیمات واقعی برنامه داده نشد. فایل‌های هش و لاگ در /tmp هستند و وارد مخزن نمی‌شوند. بررسی رابط تصویری یا بیلد مجدد وب ضرورت نداشت، چون تمام کد فرانت‌اند بدون تغییر باقی ماند و تست‌های رفتاری و بررسی TypeScript گذشتند.

## انتشار

این حذف migration یا بازسازی/آپلود بستهٔ محتوا نمی‌خواهد؛ با انتشار کد بک‌اند، ماژول‌های پایلوت دیگر در پروژه نیستند. برای این کار هیچ تغییری روی سرور یا باکت انجام نشده است. اتصال Jev یا مدل دیگر در این تغییر پیاده‌سازی نشده است.
