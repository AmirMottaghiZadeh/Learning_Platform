"""Read-side logic for the lessons taxonomy.

A *group* is an ATC L1 anatomical group; a *chapter* is an ATC L2 subgroup and
its ingredients. Everything is derived from `apps.drugs` plus the learner's
`ChapterProgress` rows.
"""

from collections import defaultdict

from apps.drugs.models import AtcCategory, Ingredient

from .models import ChapterProgress

# Which profile fields become "exam points" for a chapter, and their tone.
EXAM_POINT_FIELDS = [
    ("boxed_warning", "boxed"),
    ("contraindications", "deny"),
    ("warnings", "caution"),
]


def _l2_slug_index():
    """{ 'N02': [ingredient slugs...], ... } for every L2 that has ingredients."""
    index = defaultdict(list)
    rows = (
        Ingredient.objects.filter(atc_codes__isnull=False)
        .prefetch_related("atc_codes")
        .order_by("name")
        .distinct()
    )
    for ingredient in rows:
        l2_codes = {c.code[:3] for c in ingredient.atc_codes.all()}
        for code in l2_codes:
            index[code].append(ingredient.slug)
    return index


def lesson_groups(user):
    slug_index = _l2_slug_index()
    read_by_chapter = {
        p.atc_code: set(p.read_drug_slugs)
        for p in ChapterProgress.objects.filter(user=user)
    }
    categories = {c.code: c for c in AtcCategory.objects.all()}

    groups = []
    for l1 in sorted(
        (c for c in categories.values() if c.level == 1), key=lambda c: c.code
    ):
        subgroups = []
        for l2 in sorted(
            (c for c in categories.values() if c.level == 2 and c.code[0] == l1.code),
            key=lambda c: c.code,
        ):
            slugs = slug_index.get(l2.code, [])
            if not slugs:
                continue
            done = len(read_by_chapter.get(l2.code, set()) & set(slugs))
            subgroups.append({
                "code": l2.code,
                "name_fa": l2.name_fa,
                "name_en": l2.name_en,
                "total": len(slugs),
                "done": done,
            })
        if subgroups:
            groups.append({
                "code": l1.code,
                "name_fa": l1.name_fa,
                "name_en": l1.name_en,
                "subgroups": subgroups,
            })
    return groups


def get_chapter(user, atc_code):
    """(category, ingredients_qs, progress) or None if the code is not a chapter."""
    atc_code = (atc_code or "").upper()
    try:
        category = AtcCategory.objects.select_related("parent").get(code=atc_code, level=2)
    except AtcCategory.DoesNotExist:
        return None

    ingredients = (
        Ingredient.objects.filter(atc_codes__code__startswith=atc_code)
        .prefetch_related("atc_codes", "sections")
        .order_by("name")
        .distinct()
    )
    if not ingredients:
        return None

    progress, _ = ChapterProgress.objects.get_or_create(user=user, atc_code=atc_code)
    return category, ingredients, progress


def chapter_exam_points(ingredients):
    points = []
    for ingredient in ingredients:
        by_field = {s.field: s for s in ingredient.sections.all()}
        for field, tone in EXAM_POINT_FIELDS:
            section = by_field.get(field)
            if not section:
                continue
            fa = (section.summary_fa or "").strip()
            en = (section.summary_en or "").strip()
            if not fa and not en:
                continue
            points.append({
                "drug_name": ingredient.name,
                "drug_slug": ingredient.slug,
                "field": field,
                "tone": tone,
                "point_fa": fa,
                "point_en": en,
            })
    return points
