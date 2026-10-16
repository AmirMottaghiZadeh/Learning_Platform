"""The simple panel pages, declared as sections for the generic CRUD."""

from django.utils.html import format_html

from ..models import (
    Announcement, AppRelease, Category, ContentBlock, DownloadLink, MenuItem, Page, Redirect, Tag,
)
from . import forms
from .crud import Section, chip
from .ui import jalali_format

TAX_TABS = [("دسته‌ها", "panel:categories", "categories"), ("برچسب‌ها", "panel:tags", "tags")]
DL_TABS = [("نسخه‌ها", "panel:releases", "releases"), ("پیوندهای دانلود", "panel:links", "links")]


def _state(obj, ok="فعال", no="غیرفعال"):
    return chip(ok, "ok") if obj else chip(no, "dr")


categories = Section(
    key="categories", route="categories", model=Category, form=forms.CategoryForm, title="دسته‌ها", singular="دسته",
    perm="taxonomy.manage", active="taxonomy", search=("name",), ordering=("order", "name"),
    columns=[("نام", lambda o: o.name), ("نشانی", lambda o: format_html('<span dir="ltr">{}</span>', o.slug)),
             ("تعداد مطلب", lambda o: o.posts.count()), ("ترتیب", lambda o: o.order)],
)
tags = Section(
    key="tags", route="tags", model=Tag, form=forms.TagForm, title="برچسب‌ها", singular="برچسب",
    perm="taxonomy.manage", active="taxonomy", search=("name",), ordering=("name",),
    columns=[("نام", lambda o: o.name), ("نشانی", lambda o: format_html('<span dir="ltr">{}</span>', o.slug)), ("تعداد مطلب", lambda o: o.posts.count())],
)
pages = Section(
    key="pages", route="pages", model=Page, form=forms.PageForm, title="برگه‌ها", singular="برگه",
    perm="page.manage", active="pages", search=("title", "slug"), ordering=("title",),
    filters=[("status", "وضعیت", Page.STATUS_CHOICES, "status")],
    hint="برگه‌های متنی مثل «دربارهٔ ما» و «قوانین». برگهٔ نوع «تماس» فرم تماس را هم نشان می‌دهد.",
    columns=[("عنوان", lambda o: o.title), ("نشانی", lambda o: format_html('<a href="/{0}/" target="_blank" dir="ltr">/{0}/</a>', o.slug)),
             ("نوع", lambda o: o.get_kind_display()), ("وضعیت", lambda o: chip(o.get_status_display(), "ok" if o.status == "published" else "dr")),
             ("به‌روزرسانی", lambda o: jalali_format(o.updated_at, False))],
)
announcements = Section(
    key="announcements", route="announcements", model=Announcement, form=forms.AnnouncementForm, title="اطلاعیه‌ها", singular="اطلاعیه",
    perm="announcement.manage", active="ann", search=("title",), ordering=("-pinned", "-published_at"),
    filters=[("level", "نوع", Announcement.LEVEL_CHOICES, "level")],
    hint="اطلاعیه‌ها در صفحهٔ اصلی و بخش «اطلاعیه‌ها» نمایش داده می‌شوند. برای نوار بالای سایت به «تنظیمات › نوار اطلاعیه» بروید.",
    columns=[("عنوان", lambda o: o.title), ("نوع", lambda o: o.get_level_display()),
             ("وضعیت", lambda o: chip("منتشرشده", "ok") if o.is_live else chip("منتشر نشده" if not o.is_published else "زمان‌بندی‌شده", "sc")),
             ("سنجاق", lambda o: "✓" if o.pinned else ""), ("تاریخ", lambda o: jalali_format(o.published_at))],
)
releases = Section(
    key="releases", route="releases", model=AppRelease, form=forms.ReleaseForm, title="نسخه‌های اپ", singular="نسخه",
    perm="download.manage", active="downloads", ordering=("-released_at", "-id"), tabs=DL_TABS,
    filters=[("platform", "پلتفرم", AppRelease.PLATFORM_CHOICES, "platform")],
    columns=[("پلتفرم", lambda o: o.get_platform_display()), ("نسخه", lambda o: format_html('<span dir="ltr">{}</span>', o.version)),
             ("کانال", lambda o: o.get_channel_display()), ("آخرین", lambda o: chip("آخرین", "ok") if o.is_latest else ""),
             ("وضعیت", lambda o: _state(o.is_published, "منتشرشده", "پنهان")), ("تاریخ", lambda o: jalali_format(o.released_at, False))],
)
links = Section(
    key="links", route="download-links", model=DownloadLink, form=forms.DownloadLinkForm, title="پیوندهای دانلود", singular="پیوند",
    perm="download.manage", active="downloads", ordering=("order", "id"), tabs=DL_TABS,
    hint="دکمه‌های صفحهٔ دانلود و بخش دانلود صفحهٔ اصلی. شمارندهٔ کلیک هر دکمه اینجا دیده می‌شود.",
    columns=[("فروشگاه", lambda o: o.get_store_display()), ("متن دکمه", lambda o: o.label), ("نشانی", lambda o: format_html('<span dir="ltr">{}</span>', o.url[:50])),
             ("کلیک", lambda o: o.clicks), ("وضعیت", lambda o: _state(o.is_active))],
)
menus = Section(
    key="menus", route="menus", model=MenuItem, form=forms.MenuItemForm, title="منوها", singular="آیتم منو",
    perm="menu.manage", active="menus", ordering=("location", "order", "id"), per_page=60,
    filters=[("location", "جایگاه", MenuItem.LOCATIONS, "location")],
    hint="منوی بالای سایت و ستون‌های پایین سایت. عدد ترتیب کوچک‌تر، بالاتر نمایش داده می‌شود.",
    columns=[("جایگاه", lambda o: o.get_location_display()), ("عنوان", lambda o: o.label), ("نشانی", lambda o: format_html('<span dir="ltr">{}</span>', o.url)),
             ("ترتیب", lambda o: o.order), ("وضعیت", lambda o: _state(o.is_active))],
)
blocks = Section(
    key="blocks", route="home-blocks", model=ContentBlock, form=forms.ContentBlockForm, title="بلوک‌های صفحهٔ اصلی", singular="بلوک",
    perm="content.manage", active="home", ordering=("kind", "order", "id"), per_page=60, search=("title", "text"),
    filters=[("kind", "نوع", ContentBlock.KINDS, "kind")],
    hint="کارت‌های ویژگی، بخش‌های معرفی، مراحل، مخاطبان، آمار و پرسش‌های متداول. تیتر و دکمهٔ اصلی در «تنظیمات › صفحهٔ اصلی» است.",
    columns=[("نوع", lambda o: o.get_kind_display()), ("عنوان", lambda o: o.title), ("متن", lambda o: o.text[:60]),
             ("ترتیب", lambda o: o.order), ("وضعیت", lambda o: _state(o.is_active))],
)
redirects = Section(
    key="redirects", route="redirects", model=Redirect, form=forms.RedirectForm, title="تغییر مسیرها", singular="تغییر مسیر",
    perm="seo.manage", active="seo", search=("from_path", "to_url"), ordering=("from_path",),
    hint="وقتی نشانی یک صفحه عوض می‌شود، نشانی قدیمی را به جدید هدایت کنید تا رتبهٔ سئو حفظ شود.",
    columns=[("از", lambda o: format_html('<span dir="ltr">{}</span>', o.from_path)), ("به", lambda o: format_html('<span dir="ltr">{}</span>', o.to_url)),
             ("نوع", lambda o: "۳۰۱" if o.permanent else "۳۰۲"), ("بازدید", lambda o: o.hits), ("وضعیت", lambda o: _state(o.is_active))],
)
categories.tabs = TAX_TABS
tags.tabs = TAX_TABS

ALL = [categories, tags, pages, announcements, releases, links, menus, blocks, redirects]
