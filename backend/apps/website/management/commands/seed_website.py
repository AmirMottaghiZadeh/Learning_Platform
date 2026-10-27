"""Give a fresh site its starting content: settings, menus, the home page
blocks, the standard pages and the web-app download link. Idempotent -- each
group is only created while it is empty, so editors' changes are never
overwritten. `--demo` also adds sample posts, an announcement and a release,
for trying the site locally."""

from django.conf import settings
from django.core.management.base import BaseCommand
from datetime import timedelta

from django.utils import timezone

from apps.website import page_texts
from apps.website.models import (
    Announcement, AppRelease, Category, ContentBlock, DownloadLink, MenuItem, Page, Post, SiteSettings, Tag, unique_slug,
)
from apps.website.sanitize import clean_html

MENUS = {
    MenuItem.HEADER: [("ویژگی‌ها", "/#features"), ("نحوهٔ کار", "/#how"), ("پلن‌ها", "/plans/"), ("مقالات", "/blog/"), ("سؤالات متداول", "/#faq")],
    MenuItem.FOOT_PRODUCT: [("ویژگی‌ها", "/#features"), ("پلن‌ها", "/plans/"), ("دانلود اپ", "/download/"), ("اطلاعیه‌ها", "/announcements/")],
    MenuItem.FOOT_RESOURCES: [("مقالات", "/blog/"), ("سؤالات متداول", "/#faq"), ("خوراک RSS", "/rss.xml")],
    MenuItem.FOOT_COMPANY: [("دربارهٔ ما", "/about/"), ("تماس با ما", "/contact/"), ("قوانین و مقررات", "/terms/"), ("حریم خصوصی", "/privacy/")],
}

BLOCKS = [
    (ContentBlock.STAT, "۱٬۷۹۴", "ماده مؤثره", "", "", ""),
    (ContentBlock.STAT, "۵۸۰", "گروه ATC با نام فارسی", "", "", ""),
    (ContentBlock.STAT, "۵", "جعبهٔ مرور لایتنر", "", "", ""),
    (ContentBlock.STAT, "۲", "زبان: فارسی و English", "", "", ""),
    (ContentBlock.FEATURE, "درس‌های ATC", "داروها بر اساس گروه چهارحرفی دسته‌بندی شده‌اند و هر دارو در جای درست خودش است.", "۱", "", ""),
    (ContentBlock.FEATURE, "فلش‌کارت لایتنر", "مرور فاصله‌دار در پنج جعبه؛ کارت‌های سخت زودتر برمی‌گردند.", "۲", "", ""),
    (ContentBlock.FEATURE, "آزمون", "سؤال از همان داروهایی که خوانده‌اید، با پاسخ فوری.", "۳", "", ""),
    (ContentBlock.FEATURE, "ماشین‌حساب‌های بالینی", "محاسبه‌های رایج دوز و کلیرانس کنار درس‌ها.", "۴", "", ""),
    (ContentBlock.SHOWCASE, "هر دارو، زیر گروه درست خودش", "فهرست داروهای هر زیردسته با سرتیتر گروه چهارحرفی ATC. می‌دانید هر دارو کجای طبقه‌بندی است و کنار چه داروهایی قرار دارد.", "درس‌ها", "نام فارسی و انگلیسی هر دارو و گروه\nعلامت درس خوانده‌شده و پیشرفت\nجست‌وجوی فارسی و انگلیسی", "list"),
    (ContentBlock.SHOWCASE, "مرور هوشمند، فقط وقتی لازم است", "کارت‌هایی که بلدید دیرتر برمی‌گردند و کارت‌های سخت زودتر. هر روز فقط همان چیزی را مرور می‌کنید که لازم دارید.", "فلش‌کارت", "پنج جعبهٔ لایتنر\nبرنامهٔ مرور روزانه\nپیگیری اشتباهات", "card"),
    (ContentBlock.SHOWCASE, "بسنجید که واقعاً یاد گرفته‌اید", "سؤال‌ها از همان داروها و گروه‌هایی ساخته می‌شود که انتخاب کرده‌اید.", "آزمون", "انتخاب موضوع و تعداد سؤال\nپاسخ فوری و توضیح\nاشتباهات به مرور اضافه می‌شود", "quiz"),
    (ContentBlock.AUDIENCE, "دانشجوی داروسازی", "طبقه‌بندی و مکانیسم را کنار هم یاد می‌گیرد.", "Rx", "", ""),
    (ContentBlock.AUDIENCE, "دانشجوی پزشکی", "داروهای هر بیماری را یک‌جا مرور می‌کند.", "MD", "", ""),
    (ContentBlock.AUDIENCE, "پرستار و کادر درمان", "داروهای تازه را سریع مرور می‌کند.", "RN", "", ""),
    (ContentBlock.AUDIENCE, "داوطلب آزمون", "با آزمون و مرور برنامه‌ریزی‌شده آماده می‌شود.", "A+", "", ""),
    (ContentBlock.STEP, "دسته را انتخاب کنید", "از ۱۴ گروه اصلی ATC شروع کنید و تا گروه چهارحرفی پایین بروید.", "", "", ""),
    (ContentBlock.STEP, "درس را بخوانید", "خلاصهٔ فارسی از برچسب رسمی دارو؛ اندیکاسیون، عوارض و تداخل‌ها.", "", "", ""),
    (ContentBlock.STEP, "با فلش‌کارت مرور کنید", "مرور فاصله‌دار لایتنر، فقط روی چیزهایی که هنوز یاد نگرفته‌اید.", "", "", ""),
    (ContentBlock.STEP, "با آزمون بسنجید", "سؤال‌ها از همان داروهایی ساخته می‌شود که خوانده‌اید.", "", "", ""),
    (ContentBlock.FAQ, "آیا فارمنتا جایگزین مرجع بالینی است؟", "خیر. فارمنتا ابزار آموزشی است و برای تصمیم‌گیری بالینی طراحی نشده است. برای درمان بیمار همیشه به منابع و راهنمای معتبر مراجعه کنید.", "", "", ""),
    (ContentBlock.FAQ, "محتوای درس‌ها از کجا می‌آید؟", "از برچسب رسمی داروها. هر درس خلاصهٔ فارسی و انگلیسی همان بخش‌های برچسب است.", "", "", ""),
    (ContentBlock.FAQ, "روی چه دستگاه‌هایی کار می‌کند؟", "اندروید، iOS و مرورگر وب. پیشرفت شما بین دستگاه‌ها هماهنگ می‌ماند.", "", "", ""),
    (ContentBlock.FAQ, "چطور اشتراک بگیرم؟", "از همین سایت، پلن را انتخاب کنید، با شمارهٔ موبایل وارد شوید و با درگاه پرداخت بپردازید. اشتراک فوراً روی حساب شما فعال می‌شود.", "", "", ""),
    (ContentBlock.FAQ, "آیا نسخهٔ رایگان دارد؟", "بله، بخشی از درس‌ها و جست‌وجوی دارو رایگان است.", "", "", ""),
    (ContentBlock.FAQ, "برای گروه‌ها پلن دارید؟", "برای دانشکده‌ها و گروه‌های آموزشی از صفحهٔ تماس با ما پیام بدهید.", "", "", ""),
]



class Command(BaseCommand):
    help = "Create the site's starting content (idempotent). --demo adds sample posts."

    def add_arguments(self, parser):
        parser.add_argument("--demo", action="store_true", help="Also add sample posts, an announcement and a release.")

    def handle(self, *args, **options):
        SiteSettings.get()
        made = []
        if not MenuItem.objects.exists():
            for location, items in MENUS.items():
                for order, (label, url) in enumerate(items):
                    MenuItem.objects.create(location=location, label=label, url=url, order=order * 10)
            made.append("menus")
        if not ContentBlock.objects.exists():
            for order, (kind, title, text, badge, bullets, screen) in enumerate(BLOCKS):
                ContentBlock.objects.create(kind=kind, title=title, text=text, badge=badge, bullets=bullets, screen=screen, order=order * 10)
            made.append("home blocks")
        if not Page.objects.exists():
            Page.objects.create(title="دربارهٔ ما", slug="about", body_html=page_texts.ABOUT, status=Page.PUBLISHED)
            Page.objects.create(title="تماس با ما", slug="contact", kind=Page.KIND_CONTACT, body_html=page_texts.CONTACT, status=Page.PUBLISHED)
            Page.objects.create(title="قوانین و مقررات", slug="terms", body_html=page_texts.TERMS.strip(), status=Page.PUBLISHED)
            Page.objects.create(title="حریم خصوصی", slug="privacy", body_html=page_texts.PRIVACY.strip(), status=Page.PUBLISHED)
            made.append("pages")
        if not DownloadLink.objects.exists():
            DownloadLink.objects.create(store="web", label="وب‌اپ", url=settings.SITE_APP_URL, platform=AppRelease.WEB, order=100)
            made.append("download link")
        if not Category.objects.exists():
            for order, name in enumerate(["آموزش", "یادگیری", "داروشناسی"]):
                Category.objects.create(name=name, slug=unique_slug(Category, name), order=order * 10)
            made.append("categories")
        if options["demo"]:
            made += self._demo()
        self.stdout.write(self.style.SUCCESS(f"seed_website: created {', '.join(made) or 'nothing (already set up)'}"))

    def _demo(self):
        made = []
        if not Post.objects.exists():
            cats = {c.name: c for c in Category.objects.all()}
            samples = [
                ("راهنمای شروع با فارمنتا؛ از ثبت‌نام تا اولین درس", "آموزش", "قدم‌به‌قدم از نصب اپ تا خواندن اولین درس و مرور آن.",
                 "<h2>ثبت‌نام</h2><p>با شمارهٔ موبایل ثبت‌نام کنید. کد تأیید پیامک می‌شود و حساب شما ساخته می‌شود.</p><h2>اولین درس</h2><p>از صفحهٔ درس‌ها یک گروه اصلی ATC انتخاب کنید و تا زیرگروه موردنظر پایین بروید. داروهای هر زیرگروه با سرتیتر گروه چهارحرفی فهرست شده‌اند.</p><h2>مرور</h2><p>بعد از خواندن هر درس، کارت‌های آن به فلش‌کارت‌های شما اضافه می‌شود.</p>"),
                ("چطور با روش لایتنر داروها را برای همیشه حفظ کنیم؟", "یادگیری", "روش لایتنر کارت‌ها را در پنج جعبه می‌چیند و هر جعبه فاصلهٔ مرور مشخصی دارد.",
                 "<h2>چرا مرور فاصله‌دار؟</h2><p>حافظه بدون مرور در چند روز اول بیشترِ مطلب را فراموش می‌کند. مرور در فاصله‌های بلندتر و بلندتر، یادگیری را ماندگار می‌کند.</p><h2>پنج جعبه</h2><p>اگر پاسخ را بلد باشید کارت یک جعبه جلو می‌رود و اگر نه به جعبهٔ اول برمی‌گردد. هر جعبه فاصلهٔ مرور بیشتری دارد.</p><div class=\"callout\"><p>در فارمنتا همین روش برای هر دارو آماده است.</p></div>"),
                ("طبقه‌بندی ATC به زبان ساده", "داروشناسی", "ATC داروها را در پنج سطح از گروه آناتومیک تا خود ماده دسته‌بندی می‌کند.",
                 "<h2>پنج سطح</h2><p>حرف اول گروه اصلی آناتومیک است (مثلاً N برای دستگاه عصبی). دو رقم بعد زیرگروه درمانی، حرف بعدی زیرگروه دارویی و حرف چهارم زیرگروه شیمیایی را نشان می‌دهد و در پایان شماره‌ای خود ماده را مشخص می‌کند.</p><h2>مثال</h2><p>کد N04BC یعنی دستگاه عصبی، داروهای ضدپارکینسون، دوپامینرژیک‌ها و آگونیست‌های دوپامین.</p>"),
            ]
            for i, (title, cat, excerpt, body) in enumerate(samples):
                post = Post.objects.create(
                    title=title, slug=unique_slug(Post, title), excerpt=excerpt, body_html=clean_html(body), category=cats.get(cat),
                    status=Post.PUBLISHED, published_at=timezone.now() - timedelta(days=3 * (len(samples) - i)), featured=(i == 1),
                )
                post.tags.add(*[Tag.objects.get_or_create(name=n, defaults={"slug": unique_slug(Tag, n)})[0] for n in ["ATC", "یادگیری"]])
            made.append("sample posts")
        if not Announcement.objects.exists():
            Announcement.objects.create(title="نسخهٔ ۱٫۲ فارمنتا منتشر شد", slug=unique_slug(Announcement, "نسخه-۱٫۲-فارمنتا-منتشر-شد"), level=Announcement.UPDATE,
                                        body_html="<p>در این نسخه فهرست داروهای هر زیردسته با گروه‌های چهارحرفی ATC و نام فارسی آن‌ها نمایش داده می‌شود.</p>", pinned=True)
            made.append("announcement")
        if not AppRelease.objects.exists():
            AppRelease.objects.create(platform=AppRelease.ANDROID, version="1.2.0", is_latest=True,
                                      notes_html="<ul><li>گروه‌بندی ATC در فهرست داروها</li><li>نام فارسی گروه‌های دارویی</li></ul>")
            made.append("release")
        return made
