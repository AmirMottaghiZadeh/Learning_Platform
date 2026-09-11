"""Read-side logic for the lessons taxonomy.

A *chapter* is an ATC L2 subgroup and its ingredients — unchanged, still keyed
and progress-tracked by the real ATC code. A *group* used to be the chapter's
raw ATC L1 anatomical parent; it is now a curated clinical **study topic**
(see `data/study_topics.py`) that groups chapters by indication/organ system
instead of by chemistry, so e.g. every antihypertensive class shows up under
one "Hypertension" topic instead of being scattered across unrelated-looking
ATC codes. A chapter can appear under more than one topic.
"""

from collections import defaultdict

from apps.drugs.models import AtcCategory, Ingredient

from .data.study_topics import STUDY_TOPICS
from .models import ChapterProgress, ReadDrug

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


def read_slugs_for_user(user):
    """The set of every ingredient slug this learner has read to completion,
    across all chapters — see `models.ReadDrug` for why this is global rather
    than per chapter."""
    return set(ReadDrug.objects.filter(user=user).values_list("ingredient_slug", flat=True))


def mark_drug_read(user, slug):
    if slug:
        ReadDrug.objects.get_or_create(user=user, ingredient_slug=slug)


def _subgroup(code, category, slugs, read_slugs):
    return {
        "code": code,
        "name_fa": category.name_fa if category else code,
        "name_en": category.name_en if category else code,
        "total": len(slugs),
        "done": len(read_slugs & set(slugs)),
    }


def lesson_groups(user):
    slug_index = _l2_slug_index()
    read_slugs = read_slugs_for_user(user)
    l2_categories = {c.code: c for c in AtcCategory.objects.filter(level=2)}
    l1_categories = {c.code: c for c in AtcCategory.objects.filter(level=1)}

    groups = []
    seen_codes = set()
    for topic in STUDY_TOPICS:
        subgroups = []
        for code in topic["l2"]:
            slugs = slug_index.get(code, [])
            if not slugs:
                continue
            seen_codes.add(code)
            subgroups.append(_subgroup(code, l2_categories.get(code), slugs, read_slugs))
        if subgroups:
            groups.append({
                "code": topic["key"],
                "name_fa": topic["name_fa"],
                "name_en": topic["name_en"],
                "subgroups": subgroups,
            })

    # Safety net: a populated L2 code the curated topics don't cover yet (e.g.
    # a newly-imported ATC class) still gets a home — grouped by its ATC
    # anatomical section — so a chapter never silently disappears while the
    # topic table waits to be updated. The coverage test keeps this branch
    # unreachable for the current bundled data.
    leftover_by_l1 = defaultdict(list)
    for code, slugs in slug_index.items():
        if code not in seen_codes and slugs:
            leftover_by_l1[code[0]].append(code)
    for l1_code in sorted(leftover_by_l1):
        l1 = l1_categories.get(l1_code)
        subgroups = [
            _subgroup(code, l2_categories.get(code), slug_index[code], read_slugs)
            for code in sorted(leftover_by_l1[l1_code])
        ]
        groups.append({
            "code": f"other-{l1_code}",
            "name_fa": l1.name_fa if l1 else l1_code,
            "name_en": l1.name_en if l1 else l1_code,
            "subgroups": subgroups,
        })
    return groups


def _topic_lookup():
    """{ L2 code -> [topic dict, ...] } in `STUDY_TOPICS` order; first entry
    is the chapter's primary topic."""
    lookup = defaultdict(list)
    for topic in STUDY_TOPICS:
        for code in topic["l2"]:
            lookup[code].append(topic)
    return lookup


def topics_for_chapter(atc_code, l1_category=None):
    """All study topics a chapter belongs to, or a one-item fallback built
    from its ATC L1 anatomical parent if the topic table doesn't cover it yet
    (see the `lesson_groups` safety net above for why that can happen)."""
    matches = _topic_lookup().get(atc_code)
    if matches:
        return [{"code": t["key"], "name_fa": t["name_fa"], "name_en": t["name_en"]} for t in matches]
    if l1_category:
        return [{
            "code": f"other-{l1_category.code}",
            "name_fa": l1_category.name_fa,
            "name_en": l1_category.name_en,
        }]
    return []


def get_chapter(user, atc_code):
    """(category, ingredients_qs, progress, read_slugs_in_chapter) or None if
    the code is not a chapter. `read_slugs_in_chapter` is this learner's
    globally-read drugs (see `read_slugs_for_user`), filtered to this
    chapter's ingredients."""
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
    read_slugs = read_slugs_for_user(user) & {i.slug for i in ingredients}
    return category, ingredients, progress, read_slugs


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
