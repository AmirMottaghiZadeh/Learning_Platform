"""The admin's map: modules on the rail, each with its pages in the column
beside it. A page shows only to someone its rule lets in, and lights up on
any of the views it covers (`match`, fnmatch patterns on "namespace:name").

Pages of a tool that is switched off (BILLING_CONSOLE_ENABLED and the like)
don't resolve and are left out.
"""

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Callable

from django.urls import NoReverseMatch, reverse

from . import access


@dataclass(frozen=True)
class Page:
    key: str
    label: str
    url: str  # a url name, or a path starting with "/"
    allowed: Callable
    match: tuple = ()
    badge: Callable | None = None
    external: bool = False


@dataclass(frozen=True)
class Module:
    key: str
    label: str
    icon: str
    pages: tuple = field(default_factory=tuple)


# stroke icons, 24x24, drawn with currentColor
ICONS = {
    "home": '<path d="M3 11l9-7 9 7"/><path d="M5 10v10h14V10"/>',
    "users": '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><path d="M16 4.5a3.5 3.5 0 0 1 0 7M18 14.5a6.5 6.5 0 0 1 3.5 5.5"/>',
    "sales": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "app": '<rect x="6" y="2.5" width="12" height="19" rx="3"/><path d="M10.5 18.5h3"/>',
    "site": '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    "data": '<path d="M12 3l8 3v6c0 5-3.5 8-8 9-4.5-1-8-4-8-9V6z"/><path d="M9 12l2 2 4-4"/>',
    "system": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M4.9 4.9l2.1 2.1M17 17l2.1 2.1M4.9 19.1L7 17M17 7l2.1-2.1"/>',
}


def _pending_comments(user):
    from apps.website.models import Comment

    return Comment.objects.filter(status=Comment.PENDING).count()


def _new_messages(user):
    from apps.website.models import ContactMessage

    return ContactMessage.objects.filter(status=ContactMessage.NEW).count()


def _pending_reviews(user):
    from apps.data_quality_center.models import SectionEditRequest

    return SectionEditRequest.objects.filter(status=SectionEditRequest.STATUS_PENDING).count()


def _my_changes(user):
    from apps.data_quality_center.models import SectionEditRequest

    return SectionEditRequest.objects.filter(
        requested_by=user, status=SectionEditRequest.STATUS_CHANGES_REQUESTED
    ).count()


MODULES = (
    Module("home", "خانه", ICONS["home"], (
        Page("today", "امروز", "manage:home", access.anyone, ("manage:home",)),
    )),
    Module("users", "کاربران", ICONS["users"], (
        Page("users", "همهٔ کاربران", "console:users", access.is_super,
             ("console:users", "console:users_export", "console:user", "console:user_*", "console:entitlement_*")),
    )),
    Module("sales", "فروش", ICONS["sales"], (
        Page("sales", "گزارش فروش", "console:sales", access.is_super, ("console:sales",)),
        Page("orders", "سفارش‌ها", "panel:orders", access.site("orders.view"), ("panel:orders",)),
        Page("subscriptions", "اشتراک‌ها", "panel:subscriptions", access.site("orders.view"), ("panel:subscriptions",)),
        Page("plans", "پلن‌ها و محصول‌ها", "console:plans", access.is_super, ("console:plans", "console:plan_*")),
        Page("site_plans", "پلن‌ها", "panel:plans", lambda u: not access.is_super(u) and access.site("orders.view")(u), ("panel:plans",)),
        Page("features", "امکانات و سقف‌ها", "console:features", access.is_super, ("console:features", "console:feature_*")),
        Page("discounts", "کدهای تخفیف", "console:discounts", access.is_super, ("console:discount*",)),
        Page("gateway", "درگاه پرداخت", "console:gateway", access.is_super, ("console:gateway*",)),
    )),
    Module("app", "اپ", ICONS["app"], (
        Page("releases", "نسخه‌ها و دانلود", "panel:releases", access.site("download.manage"), ("panel:releases*", "panel:links*")),
        Page("access", "دسترسی مهمان", "console:access", access.is_super, ("console:access",)),
    )),
    Module("site", "سایت", ICONS["site"], (
        Page("overview", "نمای کلی", "panel:dashboard", access.site("dashboard.view"), ("panel:dashboard",)),
        Page("posts", "مطالب", "panel:posts", access.site("post.create"), ("panel:posts", "panel:post_*", "panel:revision_*")),
        Page("pages", "برگه‌ها", "panel:pages", access.site("page.manage"), ("panel:pages*",)),
        Page("taxonomy", "دسته‌ها و برچسب‌ها", "panel:categories", access.site("taxonomy.manage"), ("panel:categories*", "panel:tags*")),
        Page("media", "رسانه", "panel:media", access.site("media.upload"), ("panel:media*",)),
        Page("comments", "نظرات", "panel:comments", access.site("comment.moderate"), ("panel:comment*",), _pending_comments),
        Page("contact", "پیام‌های تماس", "panel:contact", access.site("contact.view"), ("panel:contact*",), _new_messages),
        Page("subscribers", "خبرنامه", "panel:subscribers", access.site("subscriber.view"), ("panel:subscriber*",)),
        Page("announcements", "اطلاعیه‌های سایت", "panel:announcements", access.site("announcement.manage"), ("panel:announcements*",)),
        Page("blocks", "صفحهٔ اصلی", "panel:blocks", access.site("content.manage"), ("panel:blocks*",)),
        Page("menus", "منوها", "panel:menus", access.site("menu.manage"), ("panel:menus*",)),
        Page("seo", "سئو و تغییر مسیر", "panel:seo", access.site("seo.manage"), ("panel:seo", "panel:redirects*")),
        Page("stats", "آمار سایت", "panel:stats", access.site("dashboard.view"), ("panel:stats",)),
    )),
    Module("data", "کیفیت داده", ICONS["data"], (
        Page("queue", "صف ویرایش", "data_quality_center:queue", access.is_operator,
             ("data_quality_center:queue", "data_quality_center:workspace", "data_quality_center:save_draft",
              "data_quality_center:submit", "data_quality_center:withdraw", "data_quality_center:discard")),
        Page("mine", "درخواست‌های من", "data_quality_center:mine", access.is_operator, ("data_quality_center:mine",), _my_changes),
        Page("review", "میز بازبینی", "data_quality_center:review", lambda u: access.is_operator(u) and access.is_super(u),
             ("data_quality_center:review*",), _pending_reviews),
        Page("history", "سابقه و ممیزی", "data_quality_center:history", access.is_operator,
             ("data_quality_center:history", "data_quality_center:revert")),
    )),
    Module("system", "سیستم", ICONS["system"], (
        Page("activity", "گزارش فعالیت", "manage:activity", lambda u: access.is_super(u) or access.site_admin(u),
             ("manage:activity", "panel:activity", "console:audit")),
        Page("staff", "مدیران و نقش‌ها", "panel:staff", access.site_admin, ("panel:staff*",)),
        Page("settings", "تنظیمات سایت", "panel:settings", access.site_admin, ("panel:settings",)),
        Page("django", "ادمین Django", "/admin/", lambda u: access.is_super(u), (), None, True),
    )),
)

# Things to do, offered on the home column and in the command bar.
ACTIONS = (
    ("مطلب تازه برای بلاگ", "panel:post_new", access.site("post.create")),
    ("کد تخفیف تازه", "console:discounts", access.is_super),
    ("پلن تازه", "console:plan_new", access.is_super),
    ("دادن دسترسی به کاربر", "console:users", access.is_super),
)


def _resolve(url):
    if url.startswith("/"):
        return url
    try:
        return reverse(url)
    except NoReverseMatch:
        return None


def _matches(page, view_name):
    return bool(view_name) and any(fnmatch(view_name, p) for p in page.match)


def build(request):
    """The rail, the current module's pages and everything the command bar
    can jump to, for this user on this page."""
    user = request.user
    match = getattr(request, "resolver_match", None)
    view_name = match.view_name if match else ""
    modules, current, current_page, jump = [], None, None, []
    for module in MODULES:
        pages = []
        for page in module.pages:
            if not page.allowed(user):
                continue
            url = _resolve(page.url)
            if url is None:
                continue
            on = _matches(page, view_name)
            badge = page.badge(user) if page.badge else 0
            entry = {"key": page.key, "label": page.label, "url": url, "on": on, "badge": badge, "external": page.external}
            pages.append(entry)
            if on and current_page is None:
                current_page = entry
            if not page.external:
                jump.append({"label": page.label, "group": module.label, "url": url})
        if not pages:
            continue
        entry = {
            "key": module.key, "label": module.label, "icon": module.icon, "pages": pages,
            "url": pages[0]["url"], "badge": sum(p["badge"] for p in pages), "on": any(p["on"] for p in pages),
        }
        modules.append(entry)
        if entry["on"] and current is None:
            current = entry
    if current is None and modules:
        current = modules[0]
        current["on"] = True
    actions = []
    for label, url_name, allowed in ACTIONS:
        url = _resolve(url_name) if allowed(user) else None
        if url:
            actions.append({"label": label, "url": url})
            jump.append({"label": label, "group": "کار", "url": url})
    guest_url = _resolve("console:access") if access.is_super(user) else None
    return {"modules": modules, "module": current, "page": current_page, "actions": actions, "jump": jump,
            "guest_url": guest_url}
