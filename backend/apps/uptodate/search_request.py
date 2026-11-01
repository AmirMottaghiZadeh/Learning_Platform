"""Ground requested depth in the chosen title and its actual outline.

No model-created heading or paragraph can become a destination. Unconsumed
details are mandatory paragraph constraints, not optional ranking signals.
"""

from dataclasses import dataclass
import re
import unicodedata


_FILLER = frozenset("adjust impairment disease patient product compare information drug article title find show please about an a the of for in on with and during at to by within در از و به برای درباره مقاله عنوان اطلاعات لطفا محصول تنظیم نارسایی بیماری".split())
_ROUTES = frozenset({"iv", "im", "sc", "oral", "bolus", "infusion"})
_DETAIL_MARKERS = frozenset({"product", "brand", "strength", "محصول", "برند"})
_UNITS = {
    "milligrams": "mg", "milligram": "mg", "میلیگرم": "mg", "میلی گرم": "mg",
    "micrograms": "mcg", "microgram": "mcg", "میکروگرم": "mcg", "میکرو گرم": "mcg",
    "milliliters": "ml", "milliliter": "ml", "میلی لیتر": "ml",
    "grams": "g", "kilograms": "kg", "µg": "mcg", "μg": "mcg",
}


def measurements(text):
    """Exact written numbers/comparators with their units; no unit conversion."""
    text = unicodedata.normalize("NFKC", text).casefold().replace("\u200c", " ")
    text = ''.join(str(unicodedata.digit(c)) if c.isdecimal() else c for c in text)
    text = text.replace("٫", ".").replace("≤", "<=").replace("≥", ">=")
    for source, target in sorted(_UNITS.items(), key=lambda item: -len(item[0])):
        text = re.sub(r"(?<![^\W\d_])" + re.escape(source) + r"(?![^\W\d_])", target, text)
    pattern = r"([<>]=?\s*)?(\d+(?:\.\d+)?)\s*((?:mcg|mg|mmol|ml|kg|g|%)(?:\s*/\s*(?:kg|min|dl|l|ml|day))*)?"
    return tuple(((comparison or '').replace(' ', '') + number, re.sub(r"\s", '', unit or ''))
                 for comparison, number, unit in re.findall(pattern, text))


def route_constraints(text):
    """Preserve explicitly written routes/methods; never infer a drug's route."""
    text = unicodedata.normalize("NFKC", text).casefold().replace("‌", " ")
    patterns = {
        "iv": r"\biv\b|\bi\.v\.|\bintravenous\b|وریدی",
        "im": r"\bim\b|\bintramuscular\b|عضلانی",
        "sc": r"\bsc\b|\bsubcutaneous\b|زیر\s*جلدی",
        "oral": r"\boral\b|خوراکی",
        "bolus": r"\bbolus\b|بولوس",
        "infusion": r"\binfusion\b|انفوزیون",
    }
    return tuple(sorted(key for key, pattern in patterns.items() if re.search(pattern, text)))


def meaningful(words):
    return frozenset(word for word in words if word not in _FILLER)


@dataclass(frozen=True)
class SearchRequest:
    level: str
    article_terms: tuple[str, ...]
    section_terms: tuple[str, ...]
    paragraph_terms: tuple[str, ...]
    measurements: tuple[tuple[str, str], ...]
    routes: tuple[str, ...]
    product_requested: bool

    def trace(self):
        return {"level": self.level, "article_terms": list(self.article_terms),
                "section_terms": list(self.section_terms), "paragraph_terms": list(self.paragraph_terms),
                "measurements": [list(value) for value in self.measurements],
                "routes": list(self.routes), "product_requested": self.product_requested}


def title_satisfies(plan, article):
    from .search_hierarchy import terms
    words = meaningful(plan.query_terms)
    title_words = set(terms(article.title))
    subject_words = {word for entity in plan.entities for word in terms(entity)}
    for entity in plan.entities:
        if not set(terms(entity)).issubset(title_words) and not plan.cross_topic:
            return False
    return (words.issubset(title_words | subject_words)
            and not (set(plan.query_terms) & _DETAIL_MARKERS)
            and all(value in measurements(article.title) for value in measurements(plan.search_text)))


def decompose(plan, metadata, sections, *, original):
    from .search_hierarchy import terms
    title_words = set(terms(metadata.title))
    subjects = {word for entity in plan.entities for word in terms(entity)}
    article_terms = subjects or (meaningful(plan.query_terms) & title_words)
    remaining = meaningful(plan.query_terms) - title_words - subjects
    product = bool(set(terms(original)) & _DETAIL_MARKERS or set(plan.query_terms) & _DETAIL_MARKERS)
    routes = route_constraints(plan.search_text)
    numeric = tuple(value for value in measurements(plan.search_text) if value not in measurements(metadata.title))
    product_words = set()
    for index, word in enumerate(plan.query_terms):
        if word in _DETAIL_MARKERS:
            product_words.update(meaningful(plan.query_terms[index + 1:]) - subjects)
            break
    detail = set(remaining) & (_ROUTES | product_words)
    numeric_words = {word for word in remaining if any(c.isdecimal() for c in word)}
    unit_words = {"mg", "mcg", "ml", "kg", "g", "mmol", "min", "dl", "l"} if numeric else set()
    available = remaining - _DETAIL_MARKERS - detail - numeric_words - unit_words
    section_concepts = {"dose", "kidney", "liver", "interaction", "pregnancy", "bleeding",
                        "administration", "formulation", "management", "diagnosis", "prevention"}
    core = available & section_concepts
    # Interpret the remaining qualifiers in the requested branch. A word that
    # happens to name a heading elsewhere (e.g. under liver dosing) cannot
    # redirect a request that explicitly selected kidney dosing.
    branch = [section for section in sections
              if core.issubset(terms(' '.join(section.path_titles)))]
    vocabulary = {word for section in branch for word in terms(' '.join(section.path_titles))}
    section_words = available & (vocabulary | section_concepts)
    unknown = available - section_words
    # An unknown requested heading must remain an unmatched section, rather
    # than silently turning into an article-wide paragraph search.
    if not section_words and not (detail or numeric or routes or product):
        section_words = unknown
    else:
        detail.update(unknown)
    # For a specific drug-drug interaction, both names must be present in the
    # paragraph or its inherited title/heading context.
    if len(plan.entities) > 1 and "interaction" in plan.facets:
        detail.update(subjects)
    level = "paragraph" if detail or numeric or routes or product else "section"
    if not section_words and level == "paragraph":
        # Route-only requests still select a real administration section first.
        defaults = {"administration"} if routes else ({"formulation"} if product else set())
        section_words = defaults & vocabulary
    return SearchRequest(level, tuple(sorted(article_terms)), tuple(sorted(section_words)),
                         tuple(sorted(detail)), numeric, routes, product)


def select_request_sections(request, sections, plan, *, beam):
    from .search_hierarchy import _population_matches, _useful_section, terms
    required = set(request.section_terms)
    if not required:
        return ()
    candidates = [section for section in sections if section.section_id
        and _population_matches(plan, section) and _useful_section(plan, section)
        and required.issubset(set(terms(' '.join(section.path_titles))))]
    # Prefer the heading that names the requested scope over a more specific
    # descendant. Additional, unrequested concepts are not a reason to descend.
    candidates.sort(key=lambda section: (
        len(meaningful(terms(' '.join(section.path_titles))) - required - {"adult", "pediatric"}),
        len(section.path_ids), section.section_id))
    selected = []
    for section in candidates:
        if any(section.section_id in other.path_ids or other.section_id in section.path_ids for other in selected):
            continue
        selected.append(section)
        if len(selected) == beam:
            break
    return tuple(selected)


def matches_details(request, text, context):
    from .search_hierarchy import terms
    words = terms(context + ' ' + text)
    if not set(request.paragraph_terms).issubset(words):
        return False
    if not set(request.routes).issubset(route_constraints(context + ' ' + text)):
        return False
    canonical = ' ' + ' '.join(words) + ' '
    for route in ("iv", "im", "sc", "oral"):
        if route in request.routes and "bolus" in request.routes and f' {route} bolus ' not in canonical:
            return False
    available = measurements(context + ' ' + text)
    return all(any(number == actual and (not unit or unit == actual_unit)
                   for actual, actual_unit in available) for number, unit in request.measurements)


def search_request(engine, plan, *, original, article_beam, section_beam, limit):
    from .search_hierarchy import (HIERARCHY_VERSION, PassageScope, _population_matches,
                                  _useful_section, article_sections)
    candidates = engine.catalog.select(plan, beam=article_beam)
    traces, items = [], []
    base_plan = {"entities": list(plan.entities), "facets": sorted(plan.facets), "population": plan.population,
                 "cross_topic": plan.cross_topic, "intent": plan.intent,
                 "subject_groups": [list(group) for group in plan.subject_groups]}
    level, request = "article", None

    def finish(status):
        grouped = {}
        for item in items:
            grouped.setdefault(item["article_rank"], []).append(item)
        ordered = [grouped[rank][position] for position in range(limit) for rank in sorted(grouped)
                   if position < len(grouped[rank])][:limit]
        return {"hierarchy_version": HIERARCHY_VERSION, "execution_mode": "requested_depth",
                "result_level": level,
                "plan": {**base_plan, "request": request.trace() if request else {
                    "level": level, "article_terms": [word for entity in plan.entities for word in entity.split()],
                    "section_terms": [], "paragraph_terms": [], "measurements": [], "routes": [],
                    "product_requested": False}},
                "items": ordered, "articles": traces,
                "sections": [item for item in ordered if item["kind"] == "section"],
                "paragraphs": [item for item in ordered if item["kind"] == "paragraph"], "status": status}

    if not candidates:
        return finish("no_article_candidate")
    title_candidates = [candidate for candidate in candidates if title_satisfies(plan, candidate.article)]
    if title_candidates:
        for rank, candidate in enumerate(title_candidates, 1):
            article = candidate.article
            items.append({"kind": "article", "article_id": article.article_id,
                          "title": article.title, "article_rank": rank,
                          "destination": {"article_id": article.article_id}})
            traces.append({"article_id": article.article_id, "article_rank": rank,
                "article_reason": candidate.reason, "selected_sections": [], "searched_section_ids": [],
                "fallback_reasons": [], "paragraph_count": 0, "stop_reason": "title_satisfies_request"})
        return finish("results")
    for rank, candidate in enumerate(candidates, 1):
        metadata = candidate.article
        article, outline = engine.load_article(metadata.article_id)
        if article.content_id != metadata.article_id:
            raise ValueError("Loader returned a different article")
        sections = article_sections(outline, article)
        if request is None:
            request = decompose(plan, metadata, sections, original=original)
            level = request.level
        selected = select_request_sections(request, sections, plan, beam=section_beam)
        trace = {"article_id": article.content_id, "article_rank": rank, "article_reason": candidate.reason,
            "selected_sections": [{"section_id": section.section_id, "path_ids": list(section.path_ids),
                                  "provenance": section.provenance} for section in selected],
            "searched_section_ids": [], "fallback_reasons": [], "paragraph_count": 0,
            "stop_reason": "no_matching_section"}
        traces.append(trace)
        if not selected:
            continue
        if level == "section":
            for section in selected:
                item = {"kind": "section", "article_id": article.content_id, "title": metadata.title,
                    "content_hash": article.content_hash, "extraction_version": article.version,
                    "section_id": section.section_id, "section_title": section.title,
                    "section_path": list(section.path_ids), "section_titles": list(section.path_titles),
                    "article_rank": rank, "destination": {"article_id": article.content_id,
                                                         "section_id": section.section_id}}
                items.append(item)
            trace["stop_reason"] = "requested_section_found"
            continue
        eligible_sections = {section.section_id: section for section in sections
            if _population_matches(plan, section) and _useful_section(plan, section)
            and any(parent.section_id in section.path_ids for parent in selected)}
        allowed = []
        for block in article.blocks:
            section = eligible_sections.get(block.section_id)
            if section is None:
                continue
            context = '\n'.join((metadata.title, ' > '.join(section.path_titles), ' | '.join(block.table_headers)))
            if matches_details(request, block.text, context):
                allowed.append(block.paragraph_id)
        trace["searched_section_ids"] = sorted(eligible_sections)
        trace["stop_reason"] = "no_paragraph_satisfies_details"
        if not allowed:
            continue
        scope = PassageScope(article.content_id, article.content_hash, article.version,
                             tuple(sorted(eligible_sections)), tuple(sorted(allowed)))
        found = engine.passage_search(plan, article, scope, limit)
        blocks = {block.paragraph_id: block for block in article.blocks}
        if len({hit["paragraph_id"] for hit in found}) != len(found):
            raise ValueError("Passage backend returned duplicate paragraph anchors")
        for hit in found:
            if ((hit["article_id"], hit["content_hash"], hit["extraction_version"]) !=
                    (scope.article_id, scope.content_hash, scope.extraction_version)
                    or hit["section_id"] not in eligible_sections or hit["paragraph_id"] not in allowed):
                raise ValueError("Passage backend returned a result outside the selected scope or explicit details")
            if blocks[hit["paragraph_id"]].section_id != hit["section_id"]:
                raise ValueError("Passage backend returned an unknown or misplaced paragraph")
            section = eligible_sections[hit["section_id"]]
            item = {**hit, "kind": "paragraph", "title": metadata.title, "article_rank": rank,
                    "section_path": list(section.path_ids), "section_titles": list(section.path_titles),
                    "destination": {"article_id": article.content_id, "section_id": hit["section_id"],
                                    "paragraph_id": hit["paragraph_id"]}}
            items.append(item)
        trace["paragraph_count"] = len(found)
        trace["stop_reason"] = "requested_paragraph_found" if found else "no_passage_match_in_exact_scope"
    return finish("results" if items else "no_section_match" if not any(t["selected_sections"] for t in traces)
                  else "no_paragraph_match")
