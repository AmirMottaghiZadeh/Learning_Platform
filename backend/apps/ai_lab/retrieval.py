"""Read-only UpToDate access through the app's canonical tagged search."""
from dataclasses import dataclass
import re

from apps.billing.enforcement import require_feature
from apps.uptodate import services as utd
from apps.uptodate.search_extraction import extract_article
from apps.uptodate.text import plain_title
from .telemetry import operation
from .document import FormulationLinks as _FormulationLinks, directory_links
from . import reference_index
from . import lexical

SOURCES = {"uptodate": "UpToDate"}
PAGE_SIZE = 30  # UptodateScreen's normal search page size.
MAX_ARTICLES = 8
MAX_SECTIONS_PER_ARTICLE = 60
MAX_PASSAGES = 48


def prioritize_topics(articles, lookup_kind="topic", audience="general"):
    """AI-only stable priorities inside the canonical tagged result set."""
    if lookup_kind != "drug":
        return articles
    def rank(article):
        title = article["title"].lower()
        drug = "drug information" in title
        pediatric = bool(re.search(r"\b(pediatric|paediatric|children|infants?)\b", title))
        patient = bool(re.search(r"\bpatient\b", title))
        if audience == "pediatric" and drug and pediatric:
            return 0
        if drug and not pediatric and not patient:
            return 1 if audience == "pediatric" else 0
        if patient:
            return 2 if audience == "pediatric" else 1
        if re.search(r"\badults?\b", title) and not pediatric:
            return 4 if audience == "pediatric" else 2
        return 3
    return sorted(articles, key=rank)


@dataclass
class Passage:
    id: str
    article_id: str
    title: str
    section: str
    text: str
    target: dict
    content_hash: str
    heading_path: tuple = ()
    context: tuple = ()
    ordinal: int | None = None
    media: tuple = ()


def search_articles(queries, request, audit):
    require_feature(request, "uptodate")
    if not utd.is_available():
        from .provider import ProviderError
        raise ProviderError("SOURCE_UNAVAILABLE")
    results, seen = [], set()
    searches = audit.setdefault("searches", [])
    for query in dict.fromkeys(queries):
        # Keep qualifiers and the exact normal search/catalog ranking.
        page = utd.search_page(query, limit=PAGE_SIZE, offset=0, section="")
        searches.append({"query": query, "total": page["total"], "terms": page.get("terms", []),
                         "corrected": page.get("corrected", "")})
        if page["total"] > len(page["results"]):
            audit["limited"] = True
        for hit in page["results"]:
            if hit["id"] not in seen:
                seen.add(hit["id"])
                results.append({k: hit[k] for k in ("id", "title", "sections") if k in hit})
    audit.update(search_engine="uptodate.search_page", searches=searches, candidate_articles=len(results))
    return results


def read_sections(article_ids, request, audit, *, context=None):
    """Expose an outline for selection, with versioned original paragraph targets."""
    sections, passage_number = [], 0
    for article_id in article_ids[:MAX_ARTICLES]:
        section_offset = max((int(section["id"][1:]) for section in sections), default=0) if context else len(sections)
        require_feature(request, "uptodate", item=article_id, consume=True)
        with operation("index_read"):
            prepared = reference_index.read_sections(article_id, section_offset, passage_number, audit, context=context)
        if prepared is not None:
            prepared_sections, eligible_count = prepared
            sections.extend(prepared_sections)
            passage_number += eligible_count
            continue
        with operation("source_read"):
            article = utd.get_topic(article_id)
        if not article:
            continue
        with operation("extraction"):
            extracted = extract_article(article_id, article["body_html"])
        related = directory_links(article_id, article["body_html"], extracted)
        if related:
            audit["related_topics"] = related
            continue
        groups = {}
        for block in extracted.blocks:
            if block.table_context_status == "complex_review" or not 40 <= len(block.text) <= 6000:
                audit["limited"] = True
                continue
            section = (block.section_id, block.section_title)
            passage_number += 1
            groups.setdefault(section, []).append(Passage(
                id=f"P{passage_number}", article_id=article_id, title=plain_title(article["title"]),
                section=block.section_title, text=block.text, content_hash=extracted.content_hash,
                target={"screen": "uptodateArticle", "params": {"id": article_id,
                    "title": plain_title(article["title"]), "sectionId": block.section_id,
                    "searchAnchor": block.paragraph_id, "searchContentHash": extracted.content_hash}},
            ))
        if len(groups) > MAX_SECTIONS_PER_ARTICLE and context is None:
            audit["limited"] = True
        article_sections = []
        visible_groups = list(groups.items()) if context is not None else list(groups.items())[:MAX_SECTIONS_PER_ARTICLE]
        for (_, heading), passages in visible_groups:
            article_sections.append({"id": f"T{section_offset + len(article_sections) + 1}", "article_id": article_id,
                "title": plain_title(article["title"]), "heading": heading,
                "preview": " ".join(p.text for p in passages[:2])[:280], "passages": passages})
        if context is not None:
            with operation("lexical_retrieval"):
                article_sections = lexical.rank_memory_sections(article_sections, context, audit)
        sections.extend(article_sections)
    audit.update(selected_articles=len(article_ids[:MAX_ARTICLES]), candidate_sections=len(sections),
                 candidate_passages=sum(len(section["passages"]) for section in sections))
    return sections


def section_menu(sections):
    return [{k: section[k] for k in ("id", "article_id", "title", "heading", "preview")} for section in sections]


def selected_passages(sections, selected_ids, audit, *, context=None):
    if context is not None:
        return lexical.bounded_passages(sections, selected_ids, audit)
    by_id = {section["id"]: section for section in sections}
    groups = [by_id[section_id]["passages"] for section_id in selected_ids]
    # Cover each selected section before taking more from one long section.
    passages = [group[depth] for depth in range(max(map(len, groups), default=0)) for group in groups if depth < len(group)]
    if len(passages) > MAX_PASSAGES:
        audit["limited"] = True
    passages = passages[:MAX_PASSAGES]
    audit.update(selected_sections=len(groups), selected_passages=len(passages))
    return passages
