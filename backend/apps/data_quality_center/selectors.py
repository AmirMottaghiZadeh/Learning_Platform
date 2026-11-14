"""Drug browsing with the app's clinical catalog and quality-desk filters."""

from django.db.models import Count, Exists, F, OuterRef, Q
from django.http import QueryDict

from apps.drugs.models import Ingredient, IngredientProfileSection
from apps.drugs.review import with_review_status
from apps.lessons.selectors import lesson_groups

from .models import SectionEditRequest

QUEUE_FILTERS = {
    "": "همه",
    "missing": "بدون خلاصه",
    "pending": "در انتظار تأیید",
    "changes": "نیاز به اصلاح",
    "mine": "پیش‌نویس‌های من",
    "unreviewed": "بازبینی نشده",
    "reviewed": "بازبینی شده",
    "chemistry": "بازبینی اطلاعات شیمیایی",
}
BROWSE_KEYS = ("category", "topic", "chapter", "q", "show", "page")


def drug_catalog(params):
    groups = lesson_groups()
    categories = {}
    for group in groups:
        categories.setdefault(group["category_code"], {
            "code": group["category_code"], "name_fa": group["category_name_fa"],
            "name_en": group["category_name_en"],
        })
    category = params.get("category", "")
    if category not in categories:
        category = ""
    topics = [g for g in groups if g["category_code"] == category]
    selected_topic = next((g for g in topics if g["code"] == params.get("topic")), None)
    chapters = selected_topic["subgroups"] if selected_topic else []
    chapter = params.get("chapter", "")
    if not any(c["code"] == chapter for c in chapters):
        chapter = ""
    scoped_topics = [selected_topic] if selected_topic else topics
    chapter_codes = [chapter] if chapter else list(dict.fromkeys(
        child["code"] for group in scoped_topics for child in group["subgroups"]
    ))
    return {
        "categories": list(categories.values()), "topics": topics, "chapters": chapters,
        "category": category, "topic": selected_topic["code"] if selected_topic else "",
        "chapter": chapter, "chapter_codes": chapter_codes,
    }


def browse_query(params, catalog=None):
    """Only recognized, encoded query parameters ever enter return links."""
    query = QueryDict(mutable=True)
    for key in ("category", "topic", "chapter"):
        value = catalog[key] if catalog is not None else params.get(key, "")[:80]
        if value:
            query[key] = value
    search = params.get("q", "").strip()[:255]
    if search:
        query["q"] = search
    show = params.get("show", "")
    if show in QUEUE_FILTERS and show:
        query["show"] = show
    page = params.get("page", "")
    if page.isascii() and page.isdigit() and 0 < len(page) < 8 and int(page) > 1:
        query["page"] = str(int(page))
    return query


def filtered_ingredients(user, params, chapter_codes=()):
    qs = with_review_status(Ingredient.objects.all())
    if chapter_codes:
        prefix = Q()
        for code in chapter_codes:
            prefix |= Q(atccode__code__startswith=code)
        links = Ingredient.atc_codes.through.objects.filter(ingredient_id=OuterRef("pk")).filter(prefix)
        qs = qs.filter(Exists(links))
    search = params.get("q", "")
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(name_fa__icontains=search) | Q(rxcui=search))
    show = params.get("show", "")
    if show in {"reviewed", "unreviewed"}:
        qs = qs.filter(_is_reviewed=show == "reviewed")
    elif show == "chemistry":
        stale = Q(chemistry__status="approved") & (
            ~Q(name=F("chemistry__ingredient_name")) | ~Q(rxcui=F("chemistry__ingredient_rxcui"))
        )
        qs = qs.filter(Q(chemistry__status__in=["pending", "ambiguous", "not_found"]) | stale)
    elif show == "missing":
        sections = IngredientProfileSection.objects.filter(ingredient_id=OuterRef("pk"), raw_text__gt="").filter(
            Q(summary_fa="") | Q(summary_en="")
        )
        qs = qs.filter(Exists(sections))
    elif show in {"pending", "changes", "mine"}:
        statuses = {"pending": SectionEditRequest.STATUS_PENDING,
                    "changes": SectionEditRequest.STATUS_CHANGES_REQUESTED, "mine": SectionEditRequest.STATUS_DRAFT}
        requests = SectionEditRequest.objects.filter(section__ingredient_id=OuterRef("pk"), status=statuses[show])
        if show != "pending":
            requests = requests.filter(requested_by=user)
        qs = qs.filter(Exists(requests))
    return qs.order_by("name", "pk")


def queue_rows(queryset):
    with_raw = Q(sections__raw_text__gt="")
    return queryset.annotate(
        total=Count("sections", filter=with_raw, distinct=True),
        filled=Count("sections", filter=with_raw & ~Q(sections__summary_fa="") & ~Q(sections__summary_en=""), distinct=True),
        pending=Count("sections__edit_requests", filter=Q(sections__edit_requests__status=SectionEditRequest.STATUS_PENDING), distinct=True),
        changes=Count("sections__edit_requests", filter=Q(sections__edit_requests__status=SectionEditRequest.STATUS_CHANGES_REQUESTED), distinct=True),
    )
