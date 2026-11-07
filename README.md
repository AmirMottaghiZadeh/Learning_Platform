# فارمنتا (Pharmenta)

اپ آموزشی داروسازی: درس‌نامه‌های دارویی بر پایهٔ دادهٔ openFDA، فلش‌کارت لایتنر، آزمون، برنامهٔ مطالعه، مرجع‌های بالینی (UpToDate، Lexicomp، Medscape) با امکان دانلود آفلاین، ماشین‌حساب‌های بالینی، و فروش اشتراک. یک کد برای اندروید، iOS و وب.

- **بک‌اند:** Django REST، PostgreSQL، روی رانفلر — `backend/`
- **اپ:** Expo (React Native) + `react-native-web` — `frontend/`
- **سایت و بلاگ:** `pharmenta.ir` در همان بک‌اند

| نشانی | چیست |
|---|---|
| https://app.pharmenta.ir | وب‌اپ |
| https://pharmenta.ir | سایت و بلاگ |
| https://api.pharmenta.ir/api/v1/docs/ | مستندات زندهٔ API |

> نرم‌افزار آموزشی است، نه ابزار تصمیم‌گیری بالینی.

## شروع سریع

```bash
# بک‌اند
cd backend
python3.11 -m venv .venv && .venv/bin/pip install -r requirements.txt
cp .env.example .env                      # DATABASE_URL را تنظیم کنید
.venv/bin/python manage.py migrate
.venv/bin/python manage.py runserver 127.0.0.1:8000

# اپ (ترمینال دیگر)
cd frontend
npm ci && cp .env.example .env
npm run web                               # http://localhost:8081
```

## مستندات

همهٔ مستندات فنی در **[`docs/`](docs/README.md)** است:

- [معرفی و معماری](docs/01-overview.md)
- [راه‌اندازی محیط توسعه](docs/02-local-setup.md)
- [بک‌اند](docs/03-backend.md) و [اپ](docs/04-frontend.md)
- [قرارداد API](docs/05-api.md)
- [متغیرهای محیطی](docs/06-configuration.md)
- [داده و دستورهای ایمپورت](docs/07-data.md)
- [دیپلوی](docs/08-deployment.md)
- [نگهداری، بکاپ و عیب‌یابی](docs/09-operations.md)
- [مرجع سریع دستورها](docs/10-commands.md)
- [کنسول‌های مدیریت](docs/11-admin-consoles.md) و [سایت و پنل محتوا](docs/12-website.md)

تاریخچهٔ فازهای بازنویسی: [PHASES.md](PHASES.md).
