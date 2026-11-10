"""Read-only UpToDate access through the app's canonical tagged search."""
from dataclasses import dataclass
from html.parser import HTMLParser
import re

from apps.billing.enforcement import require_feature
from apps.uptodate import services as utd
from apps.uptodate.search_extraction import extract_article
from apps.uptodate.text import plain_title

SOURCES = {"uptodate": "UpToDate"}
PAGE_SIZE = 30  # UptodateScreen's normal search page size.
MAX_ARTICLES = 8
MAX_SECTIONS_PER_ARTICLE = 60
MAX_PASSAGES = 48


class _FormulationLinks(HTMLParser):
    """Only explicit source drug links; never execute onclick or crawl external URLs."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.targets, self.current = [], None

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs = dict(attrs)
        target = attrs.get("data-topicid", "")
        if "drug" in (attrs.get("class") or "").split() and re.fullmatch(r"\d{1,12}", target):
            self.current = {"id": target, "parts": []}

    def handle_data(self, data):
        if self.current is not None:
            self.current["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            label = " ".join("".join(self.current["parts"]).split())
            if label and len(self.targets) < MAX_ARTICLES:
                self.targets.append({"id": self.current["id"], "title": label})
            self.current = None


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


def read_sections(article_ids, request, audit):
    """Expose an outline for selection, with versioned original paragraph targets."""
    sections, passage_number = [], 0
    for article_id in article_ids[:MAX_ARTICLES]:
        require_feature(request, "uptodate", item=article_id, consume=True)
        article = utd.get_topic(article_id)
        if not article:
            continue
        extracted = extract_article(article_id, article["body_html"])
        if 'id="formulinkBodyPlaceholder"' in article["body_html"] or "id='formulinkBodyPlaceholder'" in article["body_html"]:
            links = _FormulationLinks()
            links.feed(article["body_html"])
            related, seen = [], {article_id}
            for target in links.targets:
                if target["id"] not in seen:
                    related.append(target)
                    seen.add(target["id"])
            labels = {target["title"] for target in links.targets}
            has_clinical_content = any(block.section_title or (len(block.text) >= 40 and block.text not in labels)
                                       for block in extracted.blocks)
            if related and not has_clinical_content:
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
        if len(groups) > MAX_SECTIONS_PER_ARTICLE:
            audit["limited"] = True
        for (_, heading), passages in list(groups.items())[:MAX_SECTIONS_PER_ARTICLE]:
            sections.append({"id": f"T{len(sections) + 1}", "article_id": article_id,
                "title": plain_title(article["title"]), "heading": heading,
                "preview": " ".join(p.text for p in passages[:2])[:280], "passages": passages})
    audit.update(selected_articles=len(article_ids[:MAX_ARTICLES]), candidate_sections=len(sections),
                 candidate_passages=sum(len(section["passages"]) for section in sections))
    return sections


def section_menu(sections):
    return [{k: section[k] for k in ("id", "article_id", "title", "heading", "preview")} for section in sections]


def selected_passages(sections, selected_ids, audit):
    by_id = {section["id"]: section for section in sections}
    groups = [by_id[section_id]["passages"] for section_id in selected_ids]
    # Cover each selected section before taking more from one long section.
    passages = [group[depth] for depth in range(max(map(len, groups), default=0)) for group in groups if depth < len(group)]
    if len(passages) > MAX_PASSAGES:
        audit["limited"] = True
    passages = passages[:MAX_PASSAGES]
    audit.update(selected_sections=len(groups), selected_passages=len(passages))
    return passages
