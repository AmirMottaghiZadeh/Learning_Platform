# ۱۸. راه‌اندازی اعلان‌های فارمنتا، از تنظیمات تا آزمون نهایی

## وضعیت فعلی: موقتاً غیرفعال

به درخواست مالک پروژه، اعلان‌های پشتیبانی فعلاً خاموش‌اند. تنظیم مرکزی بک‌اند:

```dotenv
SUPPORT_PUSH_NOTIFICATIONS_ENABLED=False
```

این مقدار، پیش‌فرض کد هم هست. خاموش بودن آن گزینهٔ اعلان در پروفایل و تنظیمات اپ، بنر پیام تازهٔ پشتیبانی، ثبت اشتراک Push و ارسال اندروید/وب را غیرفعال می‌کند. کتابخانهٔ اعلان بومی تا روشن شدن قابلیت بارگذاری نمی‌شود و کد اپ درخواست اجازه یا توکن اعلان نمی‌کند. چت پشتیبانی، پاسخ مدیر و شمارندهٔ پیام خوانده‌نشده فعال می‌مانند. «اعلانات اپ» مدیریتی در اپ `announcements` یک قابلیت جداست؛ این راهنما مربوط به اعلان پیام پشتیبانی است.

داده‌ها و کد اتصال حذف نشده‌اند. خاموش/روشن کردن قابلیت migration ندارد. برای اعمال تنظیم سرور، بک‌اند و workerهای Celery باید با همان مقدار دوباره اجرا شوند. فعال‌سازی واقعی اندروید به Firebase/FCM و بیلد تازه نیاز دارد؛ Web Push به HTTPS و کلید VAPID نیاز دارد.

## ۱. آماده بودن نسخهٔ سرور و وب

آخرین کد بک‌اند و وب‌اپ باید منتشر شده باشد. migrationهای `accounts`، `activity` و `support` باید روی دیتابیس محیط اجرا شده باشند. در کنسول سرویس بک‌اند:

```bash
python manage.py migrate
python manage.py check
```

در توسعهٔ محلی، مفسر موجود پروژه `backend/.venv/bin/python` است. دستورهای انتشار، متغیرهای میزبان و امضای اپ در [08-deployment.md](08-deployment.md) و [15-android-signing.fa.md](15-android-signing.fa.md) آمده‌اند.

برای آماده کردن زیرساخت زیر، پرچم اعلان را فعلاً `False` نگه دارید. مرحلهٔ روشن کردن نهایی در بخش ۷ است.

## ۲. ساخت پروژه و ثبت اپ در Firebase

1. وارد [Firebase Console](https://console.firebase.google.com/) شوید و پروژه‌ای برای Pharmenta بسازید، یا پروژهٔ موجود متعلق به همین اپ را انتخاب کنید.
2. یک اپ **Android** اضافه کنید. شناسهٔ package باید دقیقاً مقدار فعلی `frontend/app.json` باشد:

   ```text
   com.pharmenta.learning
   ```

3. فایل `google-services.json` همان اپ را دریافت کنید. فایل به پروژه و شناسهٔ اپی مربوط است که در Firebase ثبت کرده‌اید.
4. در تنظیمات پروژه، بخش **Service accounts** را باز کنید و با **Generate new private key**، فایل JSON کلید Service Account را دریافت کنید.

این دو فایل متفاوت‌اند:

| فایل | کاربرد | محل استفاده |
|---|---|---|
| `google-services.json` | تنظیمات Firebase داخل برنامهٔ اندروید | متغیر فایل در EAS برای بیلد |
| JSON خصوصی Service Account | مجوز ارسال اعلان از Expo به FCM v1 | Credentials پروژهٔ Expo |

هر دو باید از همان پروژهٔ Firebase باشند. کلید Service Account خصوصی است؛ آن را در مخزن یا مستندات قرار ندهید. مراحل مرجع در [راهنمای رسمی FCM v1](https://docs.expo.dev/push-notifications/fcm-credentials/) آمده است.

## ۳. قرار دادن فایل تنظیمات Firebase در EAS

در [داشبورد Expo](https://expo.dev/)، پروژهٔ فعلی فارمنتا را باز کنید. نام نمایشی آن Pharmenta است؛ slug فنی قدیمی `pharmexa-learning` در پروژه باقی مانده است. در بخش متغیرهای محیطی پروژه، متغیر زیر را ایجاد کنید:

| گزینه | مقدار |
|---|---|
| Name | `GOOGLE_SERVICES_JSON` |
| Type | `File` |
| فایل | `google-services.json` مرحلهٔ قبل |
| Environment | `production` |

اگر پروفایل `preview` را هم برای آزمون استفاده می‌کنید، فایل را برای محیط `preview` هم فعال کنید. در `frontend/eas.json` می‌توان انتخاب محیط را صریح کرد: فیلد `environment` پروفایل `production` را برابر `production` و پروفایل `preview` را برابر `preview` قرار دهید.

`frontend/app.config.js` از قبل مقدار `GOOGLE_SERVICES_JSON` را به `android.googleServicesFile` می‌دهد. مقدار متغیر فایل در بیلد EAS، مسیر فایل روی ماشین سازنده است. برای بیلد محلی، همین متغیر باید مسیر واقعی فایل روی همان دستگاه باشد. [مرجع متغیرهای EAS](https://docs.expo.dev/eas/environment-variables/)، [انتخاب محیط بیلد](https://docs.expo.dev/eas/environment-variables/usage/).

## ۴. اتصال کلید ارسال FCM به Expo

در ترمینال:

```bash
cd "/home/amir/Documents/Learning Platform/frontend"
npx eas-cli login
npx eas-cli credentials -p android
```

پروفایل `production` و بخش Google Service Account مربوط به **Push Notifications / FCM V1** را انتخاب کنید. گزینهٔ بارگذاری کلید جدید را بزنید و مسیر JSON خصوصی Service Account را بدهید. این مرحله، بارگذاری `google-services.json` نیست.

روش جایگزین در داشبورد Expo: تنظیمات پروژه ← Credentials ← شناسهٔ اندروید `com.pharmenta.learning` ← کلید FCM v1؛ فایل خصوصی را آنجا بارگذاری و ذخیره کنید. اگر از Service Account موجود استفاده می‌کنید، مجوز Firebase Cloud Messaging API Admin آن را مطابق [راهنمای رسمی Expo](https://docs.expo.dev/push-notifications/fcm-credentials/) بررسی کنید.

بک‌اند این پروژه به سرویس Expo ارسال می‌کند؛ Service Account در Credentials اکسپو نگهداری می‌شود. اگر Push Security را در Expo فعال کرده‌اید، توکن معتبر سرور باید در `SUPPORT_EXPO_ACCESS_TOKEN` بک‌اند و worker هم تنظیم شود؛ در حالت معمولِ بدون این گزینه، متغیر خالی است.

## ۵. ساخت APK دارای پشتیبانی اعلان

پروژه از قبل `expo-notifications`، `expo-device`، شناسهٔ پروژهٔ EAS و کانال `support` را دارد. APK قدیمی این تغییرات بومی را دریافت نمی‌کند؛ بیلد تازه لازم است.

پیش از انتشار عمومی، نسخه را مطابق [جریان انتشار](08-deployment.md) بالا ببرید. برای دیدن تغییرات نسخه بدون نوشتن فایل:

```bash
npm run release -- patch --dry-run
```

دستور واقعی `npm run release -- patch` فایل‌ها را تغییر می‌دهد و کامیت و تگ محلی می‌سازد؛ شرح کامل همان سند انتشار را دنبال کنید. سپس APK را بسازید:

```bash
npx eas-cli build -p android --profile production
```

فایل خروجی را دریافت و با امضای ثابت پروژه روی گوشی واقعی نصب کنید. در کد فعلی، ثبت اعلان اندروید برای گوشی واقعی فعال می‌شود. آزمون را با APK همین پروژه انجام دهید. [مرجع راه‌اندازی اعلان Expo](https://docs.expo.dev/push-notifications/push-notifications-setup/).

## ۶. تنظیم Web Push در بک‌اند

کلیدهای VAPID در محیط محلی این پروژه قبلاً ساخته شده‌اند. مسیرهای پیش‌فرض:

```text
backend/.private/support-vapid.pem
backend/.private/support-vapid-public.txt
```

برای ساخت اولیه در محیطی که کلید ندارد:

```bash
cd "/home/amir/Documents/Learning Platform/backend"
.venv/bin/python manage.py create_support_push_keys --configure-local
```

دستور کلید موجود را بازنویسی نمی‌کند و کلید خصوصی را چاپ نمی‌کند. کلید خصوصی با مجوز `0600` ذخیره می‌شود. فایل خصوصی باید روی سرور بک‌اند به‌صورت امن و پایدار در دسترس باشد؛ برای کانتینر می‌توان از secret mount یا فضای پایدار خصوصی استفاده کرد. مسیر لپ‌تاپ، مسیر سرور نیست.

این متغیرها را در سرویس بک‌اند و worker قرار دهید:

| متغیر | مقدار |
|---|---|
| `SUPPORT_WEB_PUSH_PUBLIC_KEY` | محتوای `support-vapid-public.txt` |
| `SUPPORT_WEB_PUSH_PRIVATE_KEY` | مسیر واقعی فایل PEM روی سرور، مثلاً `/run/secrets/support-vapid.pem` اگر همان‌جا mount شده باشد |
| `SUPPORT_WEB_PUSH_SUBJECT` | `mailto:support@pharmenta.ir` یا نشانی تماس معتبر پروژه |

هویت VAPID را ثابت نگه دارید؛ ساخت کلید تازه می‌تواند اشتراک‌های مرورگر قبلی را نیازمند ثبت مجدد کند. وب‌اپ باید روی HTTPS اجرا شود و مرورگر از Service Worker و Push API پشتیبانی کند. [مرجع Push API مرورگر](https://developer.mozilla.org/en-US/docs/Web/API/PushManager/subscribe).

## ۷. روشن کردن قابلیت پس از آماده شدن زیرساخت

1. در حالی که پرچم هنوز `False` است، برای کنار گذاشتن ارسال‌های قدیمی و جلوگیری از ارسال اعلان‌های عقب‌افتاده اجرا کنید:

   ```bash
   python manage.py retry_support_notifications
   ```

   در حالت خاموش، فرمان pending/failedها و sendingهای رهاشدهٔ بیش از پنج دقیقه را `skipped` می‌کند و هیچ کاری وارد صف نمی‌کند.

2. مقدار زیر را در محیط بک‌اند و worker قرار دهید:

   ```dotenv
   SUPPORT_PUSH_NOTIFICATIONS_ENABLED=True
   ```

3. بک‌اند و workerها را دوباره اجرا کنید. اگر `CELERY_TASK_ALWAYS_EAGER=False` است، broker و worker سالم لازم‌اند؛ در حالت eager ارسال در همان فرایند درخواست اجرا می‌شود.
4. اپ و وب‌اپ، مقدار `push_enabled` را از `/api/v1/support/summary/` می‌خوانند. با دریافت مقدار روشن، بخش اعلان در تنظیمات و پروفایل نمایش داده می‌شود. این خلاصه هر ۳۰ ثانیه بررسی می‌شود؛ باز کردن دوبارهٔ اپ هم آن را تازه می‌کند.
5. کاربر وارد حساب شود، در تنظیمات «اعلان پیام‌های پشتیبانی» را روشن کند و اجازهٔ سیستم/مرورگر را بدهد. اجازه دادن به‌تنهایی کافی نیست؛ ثبت توکن یا اشتراک نیز باید موفق شود.

## ۸. آزمون دریافت و باز شدن گفت‌وگو

برای اندروید، APK تازه را روی گوشی واقعی باز کنید. برای وب، نسخهٔ HTTPS منتشرشده را در مرورگر دارای Push API باز کنید. سپس در هرکدام:

1. با حساب کاربر وارد شوید و اعلان پشتیبانی را روشن کنید.
2. یک پیام پشتیبانی ارسال کنید.
3. از گفت‌وگو خارج شوید و اپ یا تب را به پس‌زمینه ببرید.
4. با حساب مدیر در `/manage/app/support/` به همان پرونده پاسخ بدهید.
5. دریافت اعلان را بررسی کنید؛ متن اعلان عمومی است و محتوای خصوصی پیام را نشان نمی‌دهد.
6. اعلان را لمس کنید؛ باید گفت‌وگوی همان کاربر باز شود.
7. خروج از حساب، تعویض حساب، خاموش کردن اعلان و ابطال نشست را هم بررسی کنید تا دستگاه برای حساب قبلی پیام تازه نگیرد.

موقع خواندن همان چت، نمایش اعلان بومی سرکوب می‌شود؛ برای آزمون، اپ را در پس‌زمینه بگذارید. وضعیت `accepted` در `NotificationDelivery` فقط پذیرش درخواست توسط Expo است، نه اثبات نمایش روی گوشی. این نسخه رسید نهایی Expo را بازیابی نمی‌کند. [مرجع ticket و receipt](https://docs.expo.dev/push-notifications/sending-notifications/).

## ۹. عیب‌یابی

| نشانه | بررسی |
|---|---|
| گزینهٔ اعلان دیده نمی‌شود | پرچم سرور، راه‌اندازی دوبارهٔ سرویس‌ها و پاسخ `push_enabled` را بررسی کنید؛ خاموش بودن فعلی عمدی است |
| خطای `SUPPORT_NOTIFICATIONS_DISABLED` | درخواست ثبت جدید در حالی رسیده که پرچم سرور خاموش است؛ خاموش کردن اشتراک همچنان مجاز است |
| دریافت توکن اندروید شکست می‌خورد | APK تازه، فایل Firebase داخل بیلد، تطبیق package و پروژهٔ Firebase، مجوز سیستم و اتصال شبکه را بررسی کنید |
| `MismatchSenderId` یا خطای اعتبارنامهٔ FCM | Service Account اکسپو و `google-services.json` باید متعلق به یک پروژه باشند |
| `DeviceNotRegistered` | توکن دستگاه دیگر معتبر نیست؛ اشتراک غیرفعال می‌شود و ثبت دوباره از نصب معتبر لازم است |
| Web Push پیکربندی نشده | مقدار کلید عمومی، مسیر واقعی و خواندنی بودن فایل خصوصی و بارگذاری مجدد تنظیمات سرور را بررسی کنید |
| پیام چت می‌رسد ولی Push ارسال نمی‌شود | پرچم، اشتراک فعال، نشست معتبر، worker در حالت غیر eager و رکورد `NotificationDelivery` را بررسی کنید |
| اعلان روی گوشی دیده نمی‌شود | مجوز اعلان، تنظیمات کانال پشتیبانی و وضعیت پس‌زمینه را بررسی کنید؛ پذیرش Expo معادل دریافت نیست |

در حالت روشن، فرمان `retry_support_notifications` ارسال‌های pending/failed و ارسال رهاشدهٔ قدیمی را با سقف سه تلاش دوباره وارد جریان می‌کند. در حالت خاموش، ارسال انجام نمی‌دهد. متن پیام‌ها و کلیدها را در لاگ یا گزارش خطا قرار ندهید.

## ۱۰. خاموش کردن دوباره

پرچم را به `False` برگردانید و بک‌اند و workerها را دوباره اجرا کنید. در اپِ دارای این کد، گزینه‌ها و بنر اعلان پشتیبانی پنهان می‌شوند؛ ثبت و ارسال Push متوقف می‌شود. چت و شمارندهٔ خوانده‌نشده‌ها فعال می‌مانند. درخواست‌هایی که پیش از خاموش شدن به ارائه‌دهنده رسیده‌اند قابل پس گرفتن نیستند. برای پاک‌سازی صف مانده، فرمان retry را در همین حالت خاموش اجرا کنید.

فایل‌های مسئول: [settings/base.py](../backend/config/settings/base.py)، [support/views.py](../backend/apps/support/views.py)، [support/services.py](../backend/apps/support/services.py)، [support/notifications.py](../backend/apps/support/notifications.py)، [useSupportNotifications.ts](../frontend/src/notifications/useSupportNotifications.ts)، [SupportSettings.tsx](../frontend/src/components/SupportSettings.tsx)، [app.config.js](../frontend/app.config.js).

## اعتبارسنجی غیرفعال‌سازی فعلی

۱۷ آزمون بک‌اند برای حالت روشن/خاموش، حفظ چت و شمارنده، مسدود شدن ثبت فعال، امکان لغو اشتراک، ارسال نشدن به هر دو ارائه‌دهنده و رفتار retry موفق بودند. TypeScript، خروجی وب، بررسی Django و نبود migration معوق هم بررسی شدند؛ OpenAPI خطا ندارد و چهار هشدار قبلی باقی است. مرورگر واقعی تأیید کرد که گزینه‌ها در پروفایل/تنظیمات پنهان‌اند، چت پیام می‌فرستد و تعداد درخواست‌های مجوز، اشتراک مرورگر و API ثبت اعلان همگی صفر است. این بررسی، آزمون دریافت Push واقعی پس از فعال‌سازی نیست؛ مراحل بخش ۸ بعداً لازم‌اند.
