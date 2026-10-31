"""دارونامه: the public drug pages on the site (/drugs/ and /drugs/<slug>/).

Opened one category at a time (settings.SITE_DRUG_ATC_PREFIXES, J01 first)
and with four of a drug's sections only -- mechanism, indications, side
effects and the boxed warning. The rest of the lesson, and the flashcards
and quizzes, stay in the app, which the pages lead to. The text is the same
IngredientProfileSection summaries the app shows; nothing is written here.
"""

import re

from django.conf import settings
from django.core.cache import cache
from django.db.models import Prefetch, Q
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.html import escape
from django.utils.safestring import mark_safe

from apps.billing.templatetags.billing_extras import fa
from apps.drugs.models import AtcCategory, AtcCode, Ingredient, IngredientProfileSection
from apps.drugs.serializers import LESSON_SECTION_MAP

from . import seo, services
from .models import SiteSettings
from .views_public import _page_meta

# (section field, key, title on the page), in the order shown.
PUBLIC_SECTIONS = [
    ("boxed_warning", "boxed", "هشدار جعبه‌ای (Boxed Warning)"),
    ("clinical_pharmacology", "mechanism", "مکانیسم اثر"),
    ("indications_and_usage", "indication", "موارد مصرف"),
    ("adverse_reactions", "side", "عوارض جانبی"),
]
PUBLIC_FIELDS = [field for field, _key, _title in PUBLIC_SECTIONS]
# A section's heading on a drug's page, with the drug's name in it.
HEADINGS = {
    "boxed": "هشدار جعبه‌ای {name} (Boxed Warning)",
    "mechanism": "مکانیسم اثر {name}",
    "indication": "موارد مصرف {name}",
    "side": "عوارض جانبی {name}",
}
# What the app adds for a drug: its other lesson sections, by their app titles.
APP_SECTIONS = [(field, title_fa) for _key, field, title_fa, _en, _tone in LESSON_SECTION_MAP if field not in PUBLIC_FIELDS]

# A friendlier name than the ATC one for a category's heading.
GROUP_TITLES = {"J01": "آنتی‌بیوتیک‌ها"}

# Summaries the generator wrote when its input had nothing to say ("the input
# holds no boxed warning ...") are not content and are never shown.
NOT_CONTENT = re.compile(r"متن ورودی|ورودی ارائه")
NO_BOXED = re.compile(r"(هشدار جعبه‌ای|جعبه[ ‌]?سیاه)[^.\n]{0,30}(نیست|ندارد|وجود ندارد|نشده)")
MIN_SECTIONS = 2
# A group (an ATC category or subgroup) gets its own page from this many drugs;
# below that the page would only repeat the drug's own.
MIN_GROUP_DRUGS = 2
CATALOG_SECONDS = 600
ZWNJ = "\u200c"

# Shown first among a category's drugs on the homepage, where present.
POPULAR = [
    "amoxicillin", "azithromycin", "cefixime", "ciprofloxacin", "ceftriaxone", "cephalexin", "metronidazole",
    "doxycycline", "clarithromycin", "levofloxacin", "vancomycin", "gentamicin", "nitrofurantoin", "clindamycin",
]

FA_ORDER = "آابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهی"


def english_name(name):
    """"amoxicillin" -> "Amoxicillin"."""
    return name[:1].upper() + name[1:]


def fa_key(text):
    """Sort key in Persian alphabetical order (Unicode puts پ چ ژ گ after ی)."""
    folded = text.replace("ي", "ی").replace("ك", "ک").replace("‌", "")
    return [FA_ORDER.index(ch) if ch in FA_ORDER else 100 + ord(ch) for ch in folded]


def _usable(field, text):
    if len(text) < 20 or NOT_CONTENT.search(text):
        return False
    return not (field == "boxed_warning" and NO_BOXED.search(text))


def _in_scope():
    query = Q()
    for prefix in settings.SITE_DRUG_ATC_PREFIXES:
        query |= Q(atc_codes__code__startswith=prefix)
    return query


def _group_code(ingredient):
    """The drug's ATC code inside the open categories (its first, in order)."""
    codes = sorted(a.code for a in ingredient.atc_codes.all())
    return next((c for c in codes if any(c.startswith(p) for p in settings.SITE_DRUG_ATC_PREFIXES)), codes[0] if codes else "")


def public_sections(ingredient):
    """The sections a drug's page shows, from its prefetched `sections`."""
    by_field = {s.field: s for s in ingredient.sections.all()}
    out = []
    for field, key, title in PUBLIC_SECTIONS:
        section = by_field.get(field)
        text = (section.summary_fa or "").strip() if section else ""
        text = _drop_title(text, title)
        if _usable(field, text):
            out.append({"key": key, "title": title, "text": text, "html": summary_html(text), "updated": section.updated_at})
    return out


LABEL = re.compile(r"^([^:：\n]{2,30})[:：]\s*(.+)$")


def _drop_title(text, title):
    """A summary that opens with its own section's name ("مکانیسم اثر: ...")
    loses that label: the heading above already says it."""
    match = LABEL.match(text.split("\n", 1)[0])
    if match and match.group(1).strip() == title:
        return (match.group(2) + text[len(text.split("\n", 1)[0]):]).strip()
    return text


def summary_html(text):
    """A summary as HTML: "- " lines become a list, other lines paragraphs, and
    a short "label:" opening a line ("مکانیسم اثر:", "شایع:") is made bold.
    Everything is escaped; no markup from the data gets through."""
    out, items = [], []

    def flush():
        if items:
            out.append("<ul>" + "".join(f"<li>{item}</li>" for item in items) + "</ul>")
            items.clear()

    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        bullet = line[0] in "-•"
        if bullet:
            line = line.lstrip("-• ").strip()
        match = LABEL.match(line)
        html = f"<b>{escape(match.group(1).strip())}:</b> {escape(match.group(2))}" if match else escape(line)
        if bullet:
            items.append(html)
        else:
            flush()
            out.append(f"<p>{html}</p>")
    flush()
    return mark_safe("".join(out))


def catalog():
    """Every drug that has a page: [{slug, name, name_fa, code, updated}],
    cached -- the index, the related links, the homepage and the sitemap all
    read it."""
    key = "website:drugs:catalog:v2:" + ",".join(settings.SITE_DRUG_ATC_PREFIXES)
    data = cache.get(key)
    if data is None:
        data = _build_catalog()
        cache.set(key, data, CATALOG_SECONDS)
    return data


def _build_catalog():
    if not settings.SITE_DRUG_ATC_PREFIXES:
        return []
    sections = IngredientProfileSection.objects.filter(field__in=PUBLIC_FIELDS).only("ingredient_id", "field", "summary_fa", "updated_at")
    qs = (
        Ingredient.objects.filter(_in_scope()).distinct()
        .prefetch_related(Prefetch("sections", queryset=sections), "atc_codes")
        .only("id", "slug", "name", "name_fa")
    )
    entries = []
    for ingredient in qs:
        shown = public_sections(ingredient)
        if len(shown) < MIN_SECTIONS:
            continue
        entries.append({
            "slug": ingredient.slug,
            "name": ingredient.name,
            "name_fa": ingredient.name_fa or english_name(ingredient.name),
            "code": _group_code(ingredient),
            "updated": max(s["updated"] for s in shown),
            "uses": uses_line(next((s["text"] for s in shown if s["key"] == "indication"), "")),
        })
    entries.sort(key=lambda e: fa_key(e["name_fa"]))
    return entries


def uses_line(indication, limit=150):
    """An indication summary as one short line ("عفونت گوش، عفونت ادراری"),
    for a drug's description and for the lists on the group pages."""
    items = [line.lstrip("-• ").split(":")[-1].strip() for line in indication.splitlines() if line.strip()]
    text = "، ".join(item for item in items if item)
    return (text[:limit].rsplit(" ", 1)[0] + "…") if len(text) > limit + 5 else text


def spellings(name):
    """A Persian name as people type it: with the half-space and without
    ("آموکسی‌سیلین", "آموکسی سیلین", "آموکسیسیلین")."""
    out = [name]
    for variant in (name.replace(ZWNJ, " "), name.replace(ZWNJ, "")):
        if variant not in out:
            out.append(variant)
    return out


def group_pages(entries):
    """{code: [drug entries]} for the groups that have a page: each category
    (ATC level 2) and subgroup (level 4) with at least MIN_GROUP_DRUGS drugs."""
    pages = {}
    for entry in entries:
        for code in {entry["code"][:3], entry["code"][:5]}:
            if len(code) in (3, 5):
                pages.setdefault(code, []).append(entry)
    return {code: drugs for code, drugs in pages.items() if len(drugs) >= MIN_GROUP_DRUGS}


def group_url(code, pages):
    """A group's own page, or its place on the index when it has none."""
    return f"/drugs/group/{code.lower()}/" if code in pages else f"/drugs/#{code[:3].lower()}"


def _group_titles(codes):
    """Persian names for ATC codes: level 4 from AtcCode, levels 1-2 from
    AtcCategory, with the friendlier category names on top."""
    names = {c.code: (c.name_fa or c.name) for c in AtcCode.objects.filter(code__in=codes)}
    names.update({c.code: c.name_fa for c in AtcCategory.objects.filter(code__in=codes)})
    names.update({code: title for code, title in GROUP_TITLES.items() if code in codes})
    return names


def grouped(entries):
    """The catalog as categories (ATC level 2) of subgroups (level 4)."""
    l2 = sorted({e["code"][:3] for e in entries})
    l4 = sorted({e["code"][:5] for e in entries})
    names = _group_titles(l2 + l4)
    pages = group_pages(catalog())
    out = []
    for category in l2:
        subgroups = []
        for code in [c for c in l4 if c.startswith(category)]:
            drugs = [e for e in entries if e["code"][:5] == code]
            subgroups.append({"code": code, "name": names.get(code, code), "drugs": drugs, "url": pages.get(code) and group_url(code, pages)})
        out.append({
            "code": category,
            "name": names.get(category, category),
            "url": pages.get(category) and group_url(category, pages),
            "subgroups": subgroups,
            "count": sum(len(s["drugs"]) for s in subgroups),
        })
    return out


def popular(limit=12):
    """Well-known drugs with a page, for links from the homepage."""
    entries = catalog()
    by_name = {e["name"].lower(): e for e in entries}
    picked = [by_name[name] for name in POPULAR if name in by_name]
    rest = [e for e in entries if e not in picked]
    return (picked + rest)[:limit]


def drug_index(request):
    if not settings.SITE_DRUG_ATC_PREFIXES:
        raise Http404
    site = SiteSettings.get()
    entries = catalog()
    groups = grouped(entries)
    services.record_view(request, "/drugs/")
    title = "دارونامه فارسی: آموزش دارو و داروشناسی"
    description = (
        f"دارونامهٔ فارسی فارمنتا برای دانشجویان و داروسازان: مکانیسم اثر، موارد مصرف و عوارض جانبی "
        f"{fa(len(entries))} دارو به زبان ساده، بر پایهٔ برچسب رسمی دارو."
    )
    ctx = {"groups": groups, "total": len(entries), "nav": "drugs"}
    ctx.update(_page_meta(request, title=title, description=description, image=seo.OG_IMAGE_PATH, canonical="/drugs/"))
    ctx["structured_data"] = seo.page_graph(
        site,
        seo.breadcrumbs([("خانه", "/"), ("دارونامه", None)]),
        {
            "@type": "CollectionPage",
            "url": ctx["meta_canonical"],
            "name": title,
            "description": description,
            "inLanguage": "fa-IR",
            "isPartOf": {"@id": services.absolute("/#website")},
            "mainEntity": {
                "@type": "ItemList",
                "numberOfItems": len(entries),
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "url": services.absolute(f"/drugs/{e['slug']}/"), "name": e["name_fa"]}
                    for i, e in enumerate(entries, start=1)
                ],
            },
        },
    )
    return render(request, "website/drugs_index.html", ctx)


def drug_detail(request, slug):
    if not settings.SITE_DRUG_ATC_PREFIXES:
        raise Http404
    ingredient = (
        Ingredient.objects.filter(slug=slug).filter(_in_scope()).distinct()
        .prefetch_related("sections", "atc_codes").first()
    )
    if ingredient is None:
        raise Http404
    sections = public_sections(ingredient)
    if len(sections) < MIN_SECTIONS:
        raise Http404
    site = SiteSettings.get()
    services.record_view(request, request.path)

    has_summary = {s.field for s in ingredient.sections.all() if (s.summary_fa or "").strip()}
    in_app = [title for field, title in APP_SECTIONS if field in has_summary]
    code = _group_code(ingredient)
    names = _group_titles([code[:3], code[:5]])
    entries = catalog()
    pages = group_pages(entries)
    category = {"code": code[:3], "name": names.get(code[:3], code[:3]), "url": group_url(code[:3], pages)}
    subgroup = {"code": code[:5], "name": names.get(code[:5], code[:5]), "url": group_url(code[:5], pages), "has_page": code[:5] in pages}
    related = [e for e in entries if e["code"][:5] == code[:5] and e["slug"] != ingredient.slug]
    if len(related) < 4:
        related += [e for e in entries if e["code"][:3] == code[:3] and e["code"][:5] != code[:5]][: 6 - len(related)]
    name_en = english_name(ingredient.name)
    # Without a Persian name the page names the drug once, in English.
    name_fa = ingredient.name_fa or name_en
    both = f"{name_fa} ({name_en})" if ingredient.name_fa else name_en
    updated = max(s["updated"] for s in sections)
    # Headings name the drug ("عوارض جانبی آموکسی‌سیلین"): that is how the
    # question is searched, and each section then stands on its own.
    for section in sections:
        section["heading"] = HEADINGS[section["key"]].format(name=name_fa)

    # The order searches ask in: uses and side effects first.
    title = f"{both}: موارد مصرف، عوارض جانبی و مکانیسم اثر"
    uses = uses_line(next((s["text"] for s in sections if s["key"] == "indication"), ""), limit=400)
    description = f"{both} از گروه {subgroup['name']}؛ موارد مصرف، عوارض و مکانیسم اثر به فارسی. کاربرد: {uses}"
    description = (description[:150].rsplit(" ", 1)[0] + "…") if len(description) > 155 else description

    trail = [("خانه", "/"), ("دارونامه", "/drugs/")]
    if category["code"] in pages:
        trail.append((category["name"], category["url"]))
    if subgroup["has_page"]:
        trail.append((subgroup["name"], subgroup["url"]))
    trail.append((name_fa, None))
    ctx = {
        "drug": ingredient, "name_fa": name_fa, "name_en": name_en, "has_fa": bool(ingredient.name_fa), "both": both,
        "sections": sections, "in_app": in_app, "trail": trail,
        "category": category, "subgroup": subgroup, "atc_codes": sorted(a.code for a in ingredient.atc_codes.all()),
        "related": related[:8], "updated": updated, "editorial": settings.SITE_EDITORIAL_NAME, "nav": "drugs",
    }
    ctx.update(_page_meta(request, title=title, description=description, image=seo.OG_IMAGE_PATH, canonical=f"/drugs/{ingredient.slug}/", kind="article"))
    ctx["structured_data"] = seo.page_graph(
        site,
        seo.breadcrumbs(trail),
        {
            "@type": "MedicalWebPage",
            "url": ctx["meta_canonical"],
            "name": title,
            "description": description,
            "inLanguage": "fa-IR",
            "dateModified": updated.isoformat(),
            "isPartOf": {"@id": services.absolute("/#website")},
            "author": seo.editorial_team(),
            "publisher": {"@id": services.absolute("/#organization")},
            "audience": {"@type": "MedicalAudience", "audienceType": "Clinician"},
            "about": drug_entity(name_en, ingredient.name_fa, ctx["atc_codes"]),
        },
    )
    return render(request, "website/drug_detail.html", ctx)


def drug_entity(name_en, name_fa, atc_codes):
    """What a drug's page is about, with every name it is searched by.

    A MedicalEntity, not a Drug: schema.org makes Drug a kind of Product too,
    and Google then checks the page as a product listing ("offers, review or
    aggregateRating should be specified") and reports every drug page as
    invalid."""
    entity = {
        "@type": "MedicalEntity",
        "name": name_en,
        "code": [{"@type": "MedicalCode", "codeValue": c, "codingSystem": "ATC"} for c in atc_codes],
    }
    if name_fa:
        entity["alternateName"] = spellings(name_fa)
    return entity


def drug_group(request, code):
    """A category (J01, "آنتی‌بیوتیک‌ها") or subgroup (J01CA) of the
    دارونامه: its drugs, each with what it is used for, so a search for a
    class of drugs ("داروهای سفالوسپورین") has a page that answers it."""
    if not settings.SITE_DRUG_ATC_PREFIXES:
        raise Http404
    if code != code.lower():
        return redirect("site:drug_group", code=code.lower(), permanent=True)
    code = code.upper()
    entries = catalog()
    pages = group_pages(entries)
    drugs = pages.get(code)
    if not drugs:
        raise Http404
    site = SiteSettings.get()
    services.record_view(request, request.path)

    is_category = len(code) == 3
    category_code = code[:3]
    names = _group_titles([category_code, code])
    name = names.get(code, code)
    category = {"code": category_code, "name": names.get(category_code, category_code), "url": group_url(category_code, pages)}
    if is_category:
        subgroups = grouped(drugs)[0]["subgroups"]
        siblings = []
    else:
        subgroups = []
        in_category = [e for e in entries if e["code"][:3] == category_code]
        siblings = [g for g in grouped(in_category)[0]["subgroups"] if g["code"] != code and g["url"]]

    examples = "، ".join(d["name_fa"] for d in drugs[:4])
    title = f"داروهای {name}: فهرست، موارد مصرف و عوارض"
    description = (
        f"فهرست {fa(len(drugs))} داروی {name} (ATC {code})، مانند {examples}؛ "
        f"مکانیسم اثر، موارد مصرف و عوارض جانبی هر دارو به فارسی در دارونامهٔ {site.site_name}."
    )
    description = (description[:150].rsplit(" ", 1)[0] + "…") if len(description) > 155 else description
    canonical = f"/drugs/group/{code.lower()}/"
    trail = [("خانه", "/"), ("دارونامه", "/drugs/")]
    if not is_category and category_code in pages:
        trail.append((category["name"], category["url"]))
    trail.append((name, None))

    ctx = {
        "code": code, "name": name, "drugs": drugs, "is_category": is_category, "category": category,
        "subgroups": subgroups, "siblings": siblings, "trail": trail, "nav": "drugs",
        "updated": max(d["updated"] for d in drugs),
    }
    ctx.update(_page_meta(request, title=title, description=description, image=seo.OG_IMAGE_PATH, canonical=canonical))
    ctx["structured_data"] = seo.page_graph(
        site,
        seo.breadcrumbs(trail),
        {
            "@type": "CollectionPage",
            "url": ctx["meta_canonical"],
            "name": title,
            "description": description,
            "inLanguage": "fa-IR",
            "dateModified": ctx["updated"].isoformat(),
            "isPartOf": {"@id": services.absolute("/#website")},
            "about": {"@type": "MedicalEntity", "name": name, "code": {"@type": "MedicalCode", "codeValue": code, "codingSystem": "ATC"}},
            "mainEntity": {
                "@type": "ItemList",
                "numberOfItems": len(drugs),
                "itemListElement": [
                    {"@type": "ListItem", "position": i, "url": services.absolute(f"/drugs/{d['slug']}/"), "name": d["name_fa"]}
                    for i, d in enumerate(drugs, start=1)
                ],
            },
        },
    )
    return render(request, "website/drug_group.html", ctx)
