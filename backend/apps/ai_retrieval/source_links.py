"""Source-bound paragraph links, parsed as data; never execute source JavaScript."""
from html.parser import HTMLParser
import json
import re

from django.conf import settings
from django.core.cache import caches
from django.utils.crypto import salted_hmac, constant_time_compare

from apps.ai_lab.provider import ProviderError
from apps.uptodate import services
from apps.uptodate.search_extraction import ANCHOR_ATTRIBUTE, EXTRACTION_VERSION, extract_article

VERSION = 2
MAX_LINKS = 8192
MAX_BYTES = 1500000
VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
SECTION = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,159}\Z")
IDENTIFIER = re.compile(r"[0-9]{1,12}\Z")


def target(attrs):
    operation = attrs.get("onclick", "")
    if not re.search(r"\bdoOperation\s*\(", operation):
        operation = ""
    graphic = re.search(r"[\"']?contentIds[\"']?\s*:\s*\[\s*[\"']([0-9]{1,12})[\"']", operation)
    if graphic:
        return {"kind": "graphic", "target_id": graphic[1]}
    article = attrs.get("data-topicid", "") or attrs.get("data-topic", "")
    match = re.search(r"\bcontentId[\"']?\s*:\s*[\"']([0-9]{1,12})[\"']", operation)
    if match:
        article = match[1]
    section = ""
    match = re.search(r"\bsectionName[\"']?\s*:\s*[\"']([A-Za-z][A-Za-z0-9_-]{0,159})[\"']", operation)
    if match:
        section = match[1]
    href = attrs.get("href", "")
    if not section and href.startswith("#") and SECTION.fullmatch(href[1:]):
        section = href[1:]
    if IDENTIFIER.fullmatch(article):
        return {"kind": "article", "target_id": article, "section_id": section,
                "drug": "drug" in (attrs.get("class") or "").split()}
    if section:
        return {"kind": "section", "section_id": section}
    return None


class ParagraphLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack = []
        self.current = None
        self.links = {}
        self.count = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        skip = tag in {"script", "style", "noscript"} or any(row[2] for row in self.stack)
        anchor = attrs.get(ANCHOR_ATTRIBUTE, "")
        if tag not in VOID:
            self.stack.append((tag, anchor, skip))
        if tag == "a" and not skip and self.count < MAX_LINKS:
            owner = next((row[1] for row in reversed(self.stack) if row[1]), "")
            link = target(attrs)
            self.current = {"owner": owner, "target": link, "parts": []} if owner and link else None

    def handle_data(self, text):
        if self.current is not None and not any(row[2] for row in self.stack):
            self.current["parts"].append(text)

    def handle_endtag(self, tag):
        if tag == "a" and self.current is not None:
            label = " ".join("".join(self.current["parts"]).split())[:240]
            item = {**self.current["target"], "label": label}
            rows = self.links.setdefault(self.current["owner"], [])
            if item not in rows and label:
                rows.append(item)
                self.count += 1
            self.current = None
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in VOID:
            self.handle_endtag(tag)


def _signature(key, value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True)
    if len(raw.encode()) > MAX_BYTES:
        raise ValueError("Link metadata exceeds cache budget")
    return salted_hmac("reference-paragraph-links", key + raw, algorithm="sha256").hexdigest()


def load(article):
    """Cached only for the exact original article/hash and parser version."""
    key = f"source-links:{VERSION}:{EXTRACTION_VERSION}:{article.source_id}:{article.content_hash}"
    cache = caches["ai_lab"]
    try:
        saved = cache.get(key)
        if isinstance(saved, dict) and isinstance(saved.get("links"), dict):
            if constant_time_compare(saved.get("signature", ""), _signature(key, saved["links"])):
                return saved["links"]
    except Exception:
        pass
    raw = services.get_topic(article.source_id, include_memberships=False)
    if raw is None:
        raise ProviderError("REFERENCE_INDEX_STALE")
    extracted = extract_article(article.source_id, raw["body_html"])
    if extracted.content_hash != article.content_hash:
        raise ProviderError("REFERENCE_INDEX_STALE")
    parser = ParagraphLinks()
    parser.feed(extracted.html)
    parser.close()
    try:
        saved = {"links": parser.links, "signature": _signature(key, parser.links)}
        cache.set(key, saved, settings.AI_LAB_SOURCE_LINK_CACHE_TTL_SECONDS)
    except Exception:
        pass
    return parser.links
