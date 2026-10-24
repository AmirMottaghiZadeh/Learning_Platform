"""The marketing site and blog served on the public domain (pharmenta.ir).

Everything an editor changes from the panel (/panel/) lives here: posts and
pages, the media library, comments, announcements, app releases and store
links, menus, the home page blocks, newsletter subscribers, contact messages,
redirects, simple traffic counters and an activity log. Plans, prices,
orders and discount codes stay in `apps.billing`; the site only reads them.

Uploaded files are kept in the database (`Media.data`): the production
container has no persistent disk to write them to.
"""

import hashlib
import math
import re

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .sanitize import plain_text

SITE_URLCONF = "config.urls_site"


def make_slug(text, fallback="item"):
    return slugify((text or "").replace("\u200c", "-"), allow_unicode=True)[:150] or fallback


def unique_slug(model, base, *, exclude_pk=None, field="slug"):
    """`base`, or `base-2`, `base-3`... whichever the model does not hold."""
    base = make_slug(base)
    slug, n = base, 2
    qs = model.objects.all()
    if exclude_pk:
        qs = qs.exclude(pk=exclude_pk)
    while qs.filter(**{field: slug}).exists():
        slug = f"{base}-{n}"
        n += 1
    return slug


# -- settings ---------------------------------------------------------------

class SiteSettings(models.Model):
    """The single row of site-wide settings."""

    CACHE_KEY = "website:settings:v1"

    site_name = models.CharField("نام سایت", max_length=80, default="فارمنتا")
    tagline = models.CharField("شعار", max_length=160, default="آموزش داروشناسی بر پایهٔ طبقه‌بندی ATC", blank=True)
    description = models.CharField(
        "توضیح پیش‌فرض (متا)", max_length=300, blank=True,
        default="درس، فلش‌کارت و آزمون داروشناسی بر پایهٔ طبقه‌بندی جهانی ATC، با خلاصهٔ فارسی از برچسب رسمی دارو.",
    )
    default_og_image = models.ForeignKey("Media", verbose_name="تصویر پیش‌فرض اشتراک‌گذاری", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")

    # hero
    hero_title = models.CharField("تیتر صفحهٔ اصلی", max_length=160, default="داروشناسی را دسته‌به‌دسته یاد بگیرید")
    hero_highlight = models.CharField("کلمهٔ پررنگ در تیتر", max_length=60, default="دسته‌به‌دسته", blank=True)
    hero_text = models.TextField("متن زیر تیتر", default="درس، فلش‌کارت و آزمون بر پایهٔ طبقه‌بندی جهانی ATC. هر دارو در جای درست خودش، با خلاصهٔ فارسی از برچسب رسمی دارو.")
    hero_primary_label = models.CharField("دکمهٔ اصلی", max_length=40, default="دانلود اپ")
    hero_primary_url = models.CharField("نشانی دکمهٔ اصلی", max_length=300, default="/download/")
    hero_secondary_label = models.CharField("دکمهٔ دوم", max_length=40, default="استفاده از وب‌اپ", blank=True)
    hero_secondary_url = models.CharField("نشانی دکمهٔ دوم", max_length=300, default="", blank=True,
                                          help_text="خالی = نشانی وب‌اپ از تنظیمات سرور")

    # announcement bar
    bar_enabled = models.BooleanField("نوار اطلاعیه بالای سایت", default=False)
    bar_text = models.CharField("متن نوار", max_length=200, blank=True)
    bar_link_text = models.CharField("متن پیوند", max_length=60, blank=True)
    bar_url = models.CharField("نشانی پیوند", max_length=300, blank=True)

    # contact + social
    contact_email = models.EmailField("ایمیل تماس", blank=True)
    contact_phone = models.CharField("تلفن تماس", max_length=40, blank=True)
    address = models.CharField("نشانی", max_length=300, blank=True)
    telegram_url = models.URLField("تلگرام", blank=True)
    instagram_url = models.URLField("اینستاگرام", blank=True)
    linkedin_url = models.URLField("لینکدین", blank=True)
    youtube_url = models.URLField("یوتیوب", blank=True)
    x_url = models.URLField("ایکس (توییتر)", blank=True)
    footer_note = models.CharField("یادداشت پایین سایت", max_length=300, blank=True,
                                   default="فارمنتا ابزار آموزشی است و جایگزین مرجع بالینی نیست.")
    copyright_text = models.CharField("متن کپی‌رایت", max_length=120, blank=True, default="فارمنتا")

    # features
    comments_enabled = models.BooleanField("نظرات فعال باشد", default=True)
    comments_moderated = models.BooleanField("نظرات پیش از نمایش تأیید شود", default=True)
    newsletter_enabled = models.BooleanField("خبرنامه فعال باشد", default=True)
    posts_per_page = models.PositiveSmallIntegerField("تعداد مطلب در هر صفحه", default=9)
    featured_plan_slug = models.SlugField("پلن پیشنهادی (نشانی پلن)", max_length=60, blank=True,
                                          help_text="این پلن در صفحهٔ اصلی با نشان «پیشنهادی» دیده می‌شود.")

    # seo
    noindex_site = models.BooleanField("جلوگیری از ایندکس کل سایت", default=False,
                                       help_text="برای محیط آزمایشی؛ سایت در موتورهای جست‌وجو ظاهر نمی‌شود.")
    robots_extra = models.TextField("خطوط اضافه robots.txt", blank=True)
    google_verification = models.CharField("کد تأیید گوگل (Search Console)", max_length=120, blank=True)
    title_suffix = models.CharField("پسوند عنوان صفحه‌ها", max_length=60, blank=True, default="| فارمنتا")
    analytics_head = models.TextField("کد تحلیل‌گر (head)", blank=True,
                                      help_text="مثلاً کد گوگل آنالیتیکس یا متریکا؛ فقط مدیر اصلی می‌تواند تغییر دهد.")

    maintenance_mode = models.BooleanField("حالت تعمیر (سایت موقتاً بسته)", default=False)
    maintenance_text = models.CharField("پیام تعمیر", max_length=300, blank=True, default="سایت در حال به‌روزرسانی است و به‌زودی برمی‌گردد.")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیمات سایت"
        verbose_name_plural = "تنظیمات سایت"

    def __str__(self):
        return self.site_name

    @classmethod
    def get(cls):
        row = cache.get(cls.CACHE_KEY)
        if row is None:
            row, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, row, 60)
        return row

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
        cache.delete(self.CACHE_KEY)

    @property
    def app_url(self):
        return self.hero_secondary_url or settings.SITE_APP_URL

    @property
    def socials(self):
        pairs = [("telegram", "تلگرام", self.telegram_url), ("instagram", "اینستاگرام", self.instagram_url),
                 ("linkedin", "لینکدین", self.linkedin_url), ("youtube", "یوتیوب", self.youtube_url), ("x", "ایکس", self.x_url)]
        return [(k, label, url) for k, label, url in pairs if url]


# -- media ------------------------------------------------------------------

class Media(models.Model):
    """An uploaded image or PDF, stored in the database."""

    ALLOWED = {
        "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp", "image/gif": ".gif",
        "application/pdf": ".pdf",
    }
    MAX_BYTES = 5 * 1024 * 1024

    title = models.CharField("عنوان", max_length=160, blank=True)
    alt = models.CharField("متن جایگزین", max_length=250, blank=True)
    filename = models.CharField(max_length=160)
    content_type = models.CharField(max_length=60)
    size = models.PositiveIntegerField()
    sha256 = models.CharField(max_length=64, db_index=True)
    data = models.BinaryField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "فایل"
        verbose_name_plural = "رسانه"

    def __str__(self):
        return self.title or self.filename

    @property
    def is_image(self):
        return self.content_type.startswith("image/")

    @property
    def url(self):
        return reverse("site:media", args=[self.pk, self.filename], urlconf=SITE_URLCONF)

    @staticmethod
    def sniff(raw):
        """The media type of `raw` judged by its first bytes, or ''."""
        head = bytes(raw[:16])
        if head.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if head.startswith(b"\xff\xd8\xff"):
            return "image/jpeg"
        if head[:4] == b"RIFF" and head[8:12] == b"WEBP":
            return "image/webp"
        if head[:6] in (b"GIF87a", b"GIF89a"):
            return "image/gif"
        if head.startswith(b"%PDF-"):
            return "application/pdf"
        return ""

    @classmethod
    def from_upload(cls, upload, *, user=None, title=""):
        raw = upload.read()
        if len(raw) > cls.MAX_BYTES:
            raise ValueError("حجم فایل بیشتر از ۵ مگابایت است.")
        kind = cls.sniff(raw)
        if not kind:
            raise ValueError("فقط تصویر (PNG، JPG، WebP، GIF) یا PDF قابل بارگذاری است.")
        stem = re.sub(r"[^\w\-]+", "-", (upload.name or "file").rsplit(".", 1)[0], flags=re.UNICODE).strip("-")[:80] or "file"
        name = f"{stem}{cls.ALLOWED[kind]}"
        return cls.objects.create(
            title=title or stem, filename=name, content_type=kind, size=len(raw),
            sha256=hashlib.sha256(raw).hexdigest(), data=raw, uploaded_by=user,
        )


# -- taxonomy and posts -------------------------------------------------------

class Category(models.Model):
    name = models.CharField("نام", max_length=80)
    slug = models.SlugField("نشانی", max_length=100, unique=True, allow_unicode=True)
    description = models.CharField("توضیح", max_length=300, blank=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=100)
    seo_title = models.CharField("عنوان سئو", max_length=160, blank=True)
    seo_description = models.CharField("توضیح سئو", max_length=300, blank=True)

    class Meta:
        ordering = ["order", "name"]
        verbose_name = "دسته"
        verbose_name_plural = "دسته‌ها"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("site:category", args=[self.slug], urlconf=SITE_URLCONF)


class Tag(models.Model):
    name = models.CharField("نام", max_length=60)
    slug = models.SlugField("نشانی", max_length=80, unique=True, allow_unicode=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "برچسب"
        verbose_name_plural = "برچسب‌ها"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("site:tag", args=[self.slug], urlconf=SITE_URLCONF)


class PostQuerySet(models.QuerySet):
    def live(self):
        """Posts readers can see: published, or scheduled and now due."""
        return self.filter(status__in=[Post.PUBLISHED, Post.SCHEDULED], published_at__lte=timezone.now())


class Post(models.Model):
    DRAFT, REVIEW, SCHEDULED, PUBLISHED, ARCHIVED = "draft", "review", "scheduled", "published", "archived"
    STATUS_CHOICES = [
        (DRAFT, "پیش‌نویس"), (REVIEW, "در بازبینی"), (SCHEDULED, "زمان‌بندی‌شده"),
        (PUBLISHED, "منتشرشده"), (ARCHIVED, "بایگانی"),
    ]

    title = models.CharField("عنوان", max_length=220)
    slug = models.SlugField("نشانی", max_length=240, unique=True, allow_unicode=True)
    excerpt = models.TextField("خلاصه", max_length=600, blank=True)
    body_html = models.TextField("متن", blank=True)
    cover = models.ForeignKey(Media, verbose_name="تصویر شاخص", null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    category = models.ForeignKey(Category, verbose_name="دسته", null=True, blank=True, on_delete=models.SET_NULL, related_name="posts")
    tags = models.ManyToManyField(Tag, verbose_name="برچسب‌ها", blank=True, related_name="posts")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="نویسنده", null=True, blank=True, on_delete=models.SET_NULL, related_name="site_posts")
    status = models.CharField("وضعیت", max_length=10, choices=STATUS_CHOICES, default=DRAFT, db_index=True)
    published_at = models.DateTimeField("زمان انتشار", null=True, blank=True, db_index=True)
    featured = models.BooleanField("ویژه (نمایش در صفحهٔ اول)", default=False)
    allow_comments = models.BooleanField("نظرات فعال", default=True)
    seo_title = models.CharField("عنوان سئو", max_length=160, blank=True)
    seo_description = models.CharField("توضیح سئو", max_length=300, blank=True)
    canonical_url = models.URLField("نشانی canonical", blank=True)
    noindex = models.BooleanField("عدم ایندکس", default=False)
    views = models.PositiveIntegerField("بازدید", default=0)
    reading_minutes = models.PositiveSmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PostQuerySet.as_manager()

    class Meta:
        ordering = ["-published_at", "-created_at"]
        indexes = [models.Index(fields=["status", "published_at"])]
        verbose_name = "مطلب"
        verbose_name_plural = "مطالب"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("site:post", args=[self.slug], urlconf=SITE_URLCONF)

    @property
    def is_live(self):
        return self.status in (self.PUBLISHED, self.SCHEDULED) and bool(self.published_at) and self.published_at <= timezone.now()

    def compute_reading_minutes(self):
        words = len(plain_text(self.body_html).split())
        return max(1, math.ceil(words / 180))

    def save(self, *args, **kwargs):
        self.reading_minutes = self.compute_reading_minutes()
        if self.status == self.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        super().save(*args, **kwargs)

    @property
    def meta_title(self):
        return self.seo_title or self.title

    @property
    def meta_description(self):
        return self.seo_description or self.excerpt or plain_text(self.body_html)[:160]


class PostRevision(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="revisions")
    title = models.CharField(max_length=220)
    excerpt = models.TextField(blank=True)
    body_html = models.TextField(blank=True)
    saved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "نسخهٔ مطلب"


class Page(models.Model):
    DRAFT, PUBLISHED = "draft", "published"
    STATUS_CHOICES = [(DRAFT, "پیش‌نویس"), (PUBLISHED, "منتشرشده")]
    KIND_DEFAULT, KIND_CONTACT = "default", "contact"
    KIND_CHOICES = [(KIND_DEFAULT, "صفحهٔ متنی"), (KIND_CONTACT, "صفحهٔ تماس (با فرم)")]

    title = models.CharField("عنوان", max_length=200)
    slug = models.SlugField("نشانی", max_length=150, unique=True, allow_unicode=True)
    kind = models.CharField("نوع", max_length=10, choices=KIND_CHOICES, default=KIND_DEFAULT)
    body_html = models.TextField("متن", blank=True)
    status = models.CharField("وضعیت", max_length=10, choices=STATUS_CHOICES, default=PUBLISHED)
    seo_title = models.CharField("عنوان سئو", max_length=160, blank=True)
    seo_description = models.CharField("توضیح سئو", max_length=300, blank=True)
    noindex = models.BooleanField("عدم ایندکس", default=False)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        verbose_name = "برگه"
        verbose_name_plural = "برگه‌ها"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("site:page", args=[self.slug], urlconf=SITE_URLCONF)

    @property
    def meta_title(self):
        return self.seo_title or self.title

    @property
    def meta_description(self):
        return self.seo_description or plain_text(self.body_html)[:160]


class Comment(models.Model):
    PENDING, APPROVED, SPAM, TRASH = "pending", "approved", "spam", "trash"
    STATUS_CHOICES = [(PENDING, "در انتظار"), (APPROVED, "تأییدشده"), (SPAM, "هرزنامه"), (TRASH, "زباله‌دان")]

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    parent = models.ForeignKey("self", null=True, blank=True, on_delete=models.CASCADE, related_name="replies")
    name = models.CharField("نام", max_length=80)
    email = models.EmailField("ایمیل", blank=True)
    body = models.TextField("متن", max_length=2000)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    is_staff_reply = models.BooleanField(default=False)
    ip_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "نظر"
        verbose_name_plural = "نظرات"

    def __str__(self):
        return f"{self.name}: {self.body[:40]}"


# -- announcements, releases, downloads ----------------------------------------

class Announcement(models.Model):
    INFO, UPDATE, MAINTENANCE, PROMO = "info", "update", "maintenance", "promo"
    LEVEL_CHOICES = [(INFO, "خبر"), (UPDATE, "به‌روزرسانی"), (MAINTENANCE, "اطلاعیهٔ فنی"), (PROMO, "تخفیف و جشنواره")]

    title = models.CharField("عنوان", max_length=200)
    slug = models.SlugField("نشانی", max_length=220, unique=True, allow_unicode=True)
    body_html = models.TextField("متن", blank=True)
    level = models.CharField("نوع", max_length=12, choices=LEVEL_CHOICES, default=INFO)
    is_published = models.BooleanField("منتشر شود", default=True)
    published_at = models.DateTimeField("زمان انتشار", default=timezone.now)
    pinned = models.BooleanField("سنجاق‌شده", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-pinned", "-published_at"]
        verbose_name = "اطلاعیه"
        verbose_name_plural = "اطلاعیه‌ها"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("site:announcement", args=[self.slug], urlconf=SITE_URLCONF)

    @property
    def is_live(self):
        return self.is_published and self.published_at <= timezone.now()

    @property
    def summary(self):
        return plain_text(self.body_html)[:180]


class AppRelease(models.Model):
    ANDROID, IOS, WEB = "android", "ios", "web"
    PLATFORM_CHOICES = [(ANDROID, "اندروید"), (IOS, "iOS"), (WEB, "وب")]
    STABLE, BETA = "stable", "beta"
    CHANNEL_CHOICES = [(STABLE, "پایدار"), (BETA, "آزمایشی")]

    platform = models.CharField("پلتفرم", max_length=10, choices=PLATFORM_CHOICES, default=ANDROID)
    version = models.CharField("نسخه", max_length=20)
    channel = models.CharField("کانال", max_length=10, choices=CHANNEL_CHOICES, default=STABLE)
    notes_html = models.TextField("تغییرات این نسخه", blank=True)
    released_at = models.DateField("تاریخ انتشار", default=timezone.localdate)
    size_mb = models.DecimalField("حجم (مگابایت)", max_digits=6, decimal_places=1, null=True, blank=True)
    min_os = models.CharField("حداقل سیستم‌عامل", max_length=40, blank=True)
    is_published = models.BooleanField("منتشر شود", default=True)
    is_latest = models.BooleanField("آخرین نسخهٔ این پلتفرم", default=False)

    class Meta:
        ordering = ["-released_at", "-id"]
        verbose_name = "نسخهٔ اپ"
        verbose_name_plural = "نسخه‌های اپ"

    def __str__(self):
        return f"{self.get_platform_display()} {self.version}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_latest:
            AppRelease.objects.filter(platform=self.platform, channel=self.channel, is_latest=True).exclude(pk=self.pk).update(is_latest=False)


class DownloadLink(models.Model):
    """A button on the download page: a store or a direct link."""

    STORES = [("play", "Google Play"), ("bazaar", "کافه‌بازار"), ("myket", "مایکت"), ("appstore", "App Store"),
              ("sibapp", "سیب‌اپ"), ("direct", "دانلود مستقیم (APK)"), ("web", "وب‌اپ")]

    store = models.CharField("فروشگاه", max_length=10, choices=STORES)
    label = models.CharField("متن دکمه", max_length=60, blank=True)
    url = models.URLField("نشانی", max_length=500)
    platform = models.CharField("پلتفرم", max_length=10, choices=AppRelease.PLATFORM_CHOICES, default=AppRelease.ANDROID)
    is_active = models.BooleanField("فعال", default=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=100)
    clicks = models.PositiveIntegerField("تعداد کلیک", default=0)

    class Meta:
        ordering = ["order", "id"]
        verbose_name = "پیوند دانلود"
        verbose_name_plural = "پیوندهای دانلود"

    def __str__(self):
        return self.label or self.get_store_display()

    @property
    def display_label(self):
        return self.label or self.get_store_display()


# -- menus, content blocks ---------------------------------------------------------

class MenuItem(models.Model):
    HEADER, FOOT_PRODUCT, FOOT_RESOURCES, FOOT_COMPANY = "header", "foot_product", "foot_resources", "foot_company"
    LOCATIONS = [(HEADER, "منوی بالا"), (FOOT_PRODUCT, "پایین سایت · محصول"), (FOOT_RESOURCES, "پایین سایت · منابع"), (FOOT_COMPANY, "پایین سایت · شرکت")]

    location = models.CharField("جایگاه", max_length=16, choices=LOCATIONS)
    label = models.CharField("عنوان", max_length=60)
    url = models.CharField("نشانی", max_length=300)
    order = models.PositiveSmallIntegerField("ترتیب", default=100)
    is_active = models.BooleanField("فعال", default=True)
    new_tab = models.BooleanField("در تب جدید", default=False)

    class Meta:
        ordering = ["location", "order", "id"]
        verbose_name = "آیتم منو"
        verbose_name_plural = "منوها"

    def __str__(self):
        return self.label


class ContentBlock(models.Model):
    """A repeated piece of the home page: a feature card, a step, a stat..."""

    FEATURE, SHOWCASE, STEP, AUDIENCE, STAT, FAQ = "feature", "showcase", "step", "audience", "stat", "faq"
    KINDS = [(FEATURE, "کارت ویژگی"), (SHOWCASE, "بخش معرفی (متن و گوشی)"), (STEP, "مرحلهٔ کار"),
             (AUDIENCE, "مخاطب"), (STAT, "عدد و آمار"), (FAQ, "پرسش متداول")]
    SCREENS = [("list", "فهرست داروها"), ("card", "فلش‌کارت"), ("quiz", "آزمون"), ("dash", "پیشرفت"), ("calc", "ماشین‌حساب")]

    kind = models.CharField("نوع", max_length=10, choices=KINDS, db_index=True)
    title = models.CharField("عنوان", max_length=160, help_text="برای آمار: عدد (مثلاً ۱٬۷۹۴)؛ برای پرسش: خود پرسش")
    text = models.TextField("متن", blank=True, help_text="برای پرسش: پاسخ؛ برای آمار: برچسب عدد")
    badge = models.CharField("نشان کوتاه", max_length=12, blank=True, help_text="مثلاً Rx یا ۱ برای کارت‌ها")
    bullets = models.TextField("نکته‌ها (هر خط یکی)", blank=True)
    screen = models.CharField("تصویر گوشی", max_length=6, choices=SCREENS, blank=True)
    order = models.PositiveSmallIntegerField("ترتیب", default=100)
    is_active = models.BooleanField("فعال", default=True)

    class Meta:
        ordering = ["kind", "order", "id"]
        verbose_name = "بلوک محتوا"
        verbose_name_plural = "بلوک‌های صفحهٔ اصلی"

    def __str__(self):
        return self.title

    @property
    def bullet_list(self):
        return [line.strip() for line in self.bullets.splitlines() if line.strip()]


# -- visitors -----------------------------------------------------------------------

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    source = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "مشترک خبرنامه"
        verbose_name_plural = "مشترکان خبرنامه"

    def __str__(self):
        return self.email


class ContactMessage(models.Model):
    NEW, READ, ANSWERED, SPAM = "new", "read", "answered", "spam"
    STATUS_CHOICES = [(NEW, "جدید"), (READ, "خوانده‌شده"), (ANSWERED, "پاسخ داده شد"), (SPAM, "هرزنامه")]

    name = models.CharField("نام", max_length=100)
    email = models.EmailField("ایمیل", blank=True)
    phone = models.CharField("تلفن", max_length=20, blank=True)
    subject = models.CharField("موضوع", max_length=160, blank=True)
    message = models.TextField("پیام", max_length=4000)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=NEW, db_index=True)
    ip_hash = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "پیام تماس"
        verbose_name_plural = "پیام‌های تماس"

    def __str__(self):
        return f"{self.name}: {self.subject or self.message[:30]}"


class Redirect(models.Model):
    from_path = models.CharField("از نشانی", max_length=300, unique=True, help_text="مثلاً /old-post/")
    to_url = models.CharField("به نشانی", max_length=500)
    permanent = models.BooleanField("دائمی (301)", default=True)
    is_active = models.BooleanField("فعال", default=True)
    hits = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["from_path"]
        verbose_name = "تغییر مسیر"
        verbose_name_plural = "تغییر مسیرها"

    def __str__(self):
        return f"{self.from_path} → {self.to_url}"


class DailyStat(models.Model):
    """Counters per day: page views, post views, downloads, newsletter sign-ups."""

    VIEW, POST, DOWNLOAD, SUBSCRIBE, CONTACT, SIGNIN = "view", "post", "download", "subscribe", "contact", "signin"

    day = models.DateField(db_index=True)
    kind = models.CharField(max_length=12)
    key = models.CharField(max_length=200, blank=True)
    count = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["day", "kind", "key"], name="website_stat_once")]

    @classmethod
    def bump(cls, kind, key="", n=1):
        day = timezone.localdate()
        updated = cls.objects.filter(day=day, kind=kind, key=key).update(count=models.F("count") + n)
        if not updated:
            try:
                cls.objects.create(day=day, kind=kind, key=key, count=n)
            except Exception:
                cls.objects.filter(day=day, kind=kind, key=key).update(count=models.F("count") + n)


class VisitorDay(models.Model):
    """One distinct visitor (by IP) on one day, for the unique-visitor counts.

    Only a keyed hash of the address is kept -- the address itself is never
    stored -- so the same visitor is recognisable across days (needed to count
    distinct visitors over a week or a month) without the table identifying
    anyone."""

    day = models.DateField()
    ip_hash = models.CharField(max_length=32)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["day", "ip_hash"], name="website_visitor_once")]
        indexes = [models.Index(fields=["ip_hash"], name="website_visitor_ip")]

    def __str__(self):
        return f"{self.day} {self.ip_hash[:8]}"


# -- staff ----------------------------------------------------------------------------

class StaffRole(models.Model):
    ADMIN, EDITOR, AUTHOR, SUPPORT = "admin", "editor", "author", "support"
    ROLE_CHOICES = [(ADMIN, "مدیر"), (EDITOR, "سردبیر"), (AUTHOR, "نویسنده"), (SUPPORT, "پشتیبان")]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="site_role")
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=AUTHOR)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نقش پنل"
        verbose_name_plural = "نقش‌های پنل"

    def __str__(self):
        return f"{self.user} · {self.get_role_display()}"


class ActivityLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    user_label = models.CharField(max_length=120, blank=True)
    action = models.CharField(max_length=40)
    object_type = models.CharField(max_length=40, blank=True)
    object_repr = models.CharField(max_length=200, blank=True)
    detail = models.CharField(max_length=300, blank=True)
    ip = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "رویداد پنل"
        verbose_name_plural = "رویدادهای پنل"
