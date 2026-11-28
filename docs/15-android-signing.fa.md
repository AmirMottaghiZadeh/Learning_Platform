# ساخت و نگهداری کلید امضای اندروید

این راهنما روش ساخت keystore با EAS و ذخیرهٔ نسخهٔ پشتیبان آن داخل پروژه را توضیح می‌دهد. در تنظیم فعلی، بیلدها از کلید مدیریت‌شده روی Expo استفاده می‌کنند و فایل‌های محلی وارد Git یا آرشیو سورس EAS نمی‌شوند.

## ساخت کلید و اولین بیلد

از ریشهٔ پروژه اجرا کنید:

```bash
cd frontend
eas build --platform android --profile production
```

اگر برای بستهٔ `com.pharmenta.learning` هنوز کلید انتشار ندارید، به سؤال زیر پاسخ `yes` بدهید:

```text
Generate a new Android Keystore? › yes
```

EAS کلید را می‌سازد و روی سرورهای Expo نگه می‌دارد. پروفایل `production` در این پروژه خروجی APK می‌سازد.

اگر به این سؤال `no` بدهید، EAS مسیر فایل keystore موجود را می‌خواهد. اگر کلیدی ندارید، با `Ctrl+C` خارج شوید، دستور بیلد را دوباره اجرا کنید و این بار `yes` بدهید.

اگر قبلاً نسخه‌ای با همین نام بسته منتشر کرده‌اید، همان کلید انتشار قبلی را استفاده کنید تا نسخهٔ جدید روی نصب قبلی قابل به‌روزرسانی باشد.

## دانلود کلید داخل پروژه

پس از ساخته‌شدن کلید، داخل `frontend/` اجرا کنید:

```bash
eas credentials --platform android
```

گزینه‌های زیر را به‌ترتیب انتخاب کنید:

1. پروفایل `production`
2. `credentials.json: Upload/Download credentials between EAS servers and your local json`
3. `Download credentials from EAS to credentials.json`

اگر مسیر دیگری در `credentials.json` تعریف نشده باشد، نسخهٔ فعلی CLI این فایل‌ها را می‌سازد؛ مسیرها نسبت به ریشهٔ مخزن هستند:

```text
frontend/
├── credentials/
│   └── android/
│       └── keystore.jks
└── credentials.json
```

`keystore.jks` کلید امضا است. `credentials.json` مسیر کلید، رمز keystore، alias و در صورت وجود رمز key را نگه می‌دارد. برای بازیابی کلید، هر دو فایل را نگه دارید؛ مقدار رمزها را در مستندات ننویسید.

این دانلود را یک بار پس از ساخت کلید انجام دهید. `eas build` به‌تنهایی نسخهٔ محلی کلید را ذخیره نمی‌کند.

## جلوگیری از ورود به Git و آرشیو سورس

قواعد زیر از قبل در `.gitignore` و `.easignore` ریشهٔ پروژه قرار دارند:

```gitignore
*.jks
*.keystore
credentials.json
frontend/credentials/
play-service-account*.json
```

وجود قواعد در هر دو فایل لازم است، چون با وجود `.easignore`، EAS برای ساخت آرشیو سورس از آن به‌جای فایل‌های `.gitignore` استفاده می‌کند.

از ریشهٔ پروژه می‌توانید نادیده‌گرفتن فایل‌ها در Git را بررسی کنید:

```bash
git check-ignore -v frontend/credentials/android/keystore.jks frontend/credentials.json
```

باید برای هر دو مسیر، قاعدهٔ متناظر در `.gitignore` نمایش داده شود.

## بیلدهای بعدی و پشتیبان‌گیری

داخل `frontend/` همان دستور قبلی را اجرا کنید:

```bash
eas build --platform android --profile production
```

تنظیم فعلی `frontend/eas.json` از منبع پیش‌فرض `remote` استفاده می‌کند؛ بنابراین بیلدهای بعدی از همان کلید روی Expo استفاده می‌کنند. دانلود `credentials.json` این تنظیم را تغییر نمی‌دهد. فایل‌های داخل پروژه پشتیبان همان کلید هستند و نیازی به تغییر `credentialsSource` نیست.

یک نسخهٔ پشتیبان جدا از هر دو فایل، در مدیر رمز یا دیسک رمزگذاری‌شده، نگه دارید؛ فایل‌های نادیده‌گرفته‌شده با clone کردن مخزن بازیابی نمی‌شوند. محل نگهداری پشتیبان را بدون درج رمزها در [راهنمای عملیات](09-operations.md#رازها-و-چیزهایی-که-باید-امن-نگه-داشته-شوند) ثبت کنید.

## منابع

- [ساخت اولین بیلد در Expo](https://docs.expo.dev/build/setup/)
- [دانلود و همگام‌سازی credentials](https://docs.expo.dev/app-signing/syncing-credentials/)
- [منبع local و remote برای credentials](https://docs.expo.dev/app-signing/local-credentials/)
- [قواعد .easignore](https://docs.expo.dev/build-reference/easignore/)
- [راهنمای دیپلوی پروژه](08-deployment.md#کلید-امضا)
