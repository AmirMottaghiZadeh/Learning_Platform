from datetime import timedelta
from zoneinfo import ZoneInfo

from django.db.models import Count, Sum, Q
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.utils import timezone

from .models import ActivityEvent


APP_SECTIONS = {
    "dashboard": "خانه", "lessons": "دارونامه", "lessonList": "فهرست داروها", "lessonDetail": "جزئیات دارو",
    "quiz": "آزمون", "profile": "پروفایل", "mistakes": "اشتباهات", "statistics": "آمار",
    "planning": "برنامهٔ مطالعه", "planningSetup": "تنظیم برنامه", "uptodate": "جست‌وجوی آپتودیت",
    "uptodateOutline": "فهرست مقالهٔ آپتودیت", "uptodateArticle": "خواندن آپتودیت", "lexicomp": "تداخلات دارویی",
    "downloads": "دانلودها", "settings": "تنظیمات", "plans": "خرید اشتراک", "education": "آموزش",
    "guidelines": "گایدلاین‌ها", "diseasesConditions": "بیماری‌ها و شرایط", "calculator": "ماشین‌حساب‌ها",
    "calculatorDomain": "گروه ماشین‌حساب", "calculatorDetail": "محاسبه", "medscapeOutline": "فهرست مرجع مداسکیپ",
    "medscapeArticle": "خواندن مداسکیپ", "medscapeSpecialty": "تخصص مداسکیپ", "support": "پشتیبانی",
    "devices": "دستگاه‌های من", "notifications": "اعلان‌ها", "onboarding": "آنبوردینگ",
}
SITE_SECTIONS = {
    "home": "خانه", "blog": "بلاگ", "post": "مقالهٔ بلاگ", "page": "برگه‌ها", "plans": "پلن‌ها",
    "download": "دانلود اپ", "contact": "تماس", "drugs": "دارونامهٔ عمومی", "drug": "جزئیات دارو",
    "account": "حساب کاربری", "checkout": "خرید", "login": "ورود", "announcements": "اطلاعیه‌ها",
    "category": "دستهٔ بلاگ", "tag": "برچسب بلاگ", "search": "جست‌وجوی سایت", "announcement": "جزئیات اطلاعیه",
}


def report(*, source="", days=30):
    days = min(90, max(1, days))
    since = timezone.now() - timedelta(days=days)
    qs = ActivityEvent.objects.filter(occurred_at__gte=since)
    if source in {"app", "site"}:
        qs = qs.filter(source=source)
    matrix = [[0 for _ in range(24)] for _ in range(7)]
    for cell in qs.filter(action="view").annotate(day=ExtractWeekDay("occurred_at", tzinfo=ZoneInfo("Asia/Tehran")), hour=ExtractHour("occurred_at", tzinfo=ZoneInfo("Asia/Tehran"))).values("day", "hour").annotate(total=Count("pk")):
        # Django Sunday=1; display Saturday first.
        matrix[(cell["day"] + 0) % 7][cell["hour"]] = cell["total"]
    observed = {(r["source"], r["section"]): r for r in qs.values("source", "section").annotate(views=Count("pk", filter=Q(action="view")), clicks=Count("pk", filter=Q(action="click")), seconds=Sum("duration_seconds"), users=Count("user", distinct=True))}
    sections = []
    for origin, labels in [("app", APP_SECTIONS), ("site", SITE_SECTIONS)]:
        if source and source != origin:
            continue
        for key, label in labels.items():
            value = observed.get((origin, key), {})
            sections.append({"source": origin, "key": key, "label": label, "views": value.get("views", 0), "clicks": value.get("clicks", 0), "seconds": value.get("seconds") or 0, "users": value.get("users", 0)})
    sections.sort(key=lambda row: (-row["views"], row["label"]))
    return {"days": days, "source": source, "matrix": matrix, "peak": max((max(row) for row in matrix), default=0), "sections": sections, "most": sections[:5], "least": sorted(sections, key=lambda row: (row["views"], row["label"]))[:5], "total": qs.filter(action="view").count(), "users": qs.exclude(user=None).values("user").distinct().count()}


def click_map(*, source, section, days=30, area="screen", viewport="mobile"):
    rows = ActivityEvent.objects.filter(source=source, section=section, action="click", area=area, viewport=viewport, occurred_at__gte=timezone.now() - timedelta(days=min(90, max(1, days)))).values("x", "y").annotate(total=Count("pk"))
    grid = [[0 for _ in range(12)] for _ in range(20)]
    for row in rows:
        if row["x"] is not None and row["y"] is not None:
            grid[min(19, row["y"] * 20 // 101)][min(11, row["x"] * 12 // 101)] += row["total"]
    return grid
