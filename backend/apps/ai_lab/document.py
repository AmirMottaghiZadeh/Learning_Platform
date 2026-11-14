"""Pure source preprocessing. Safe to run in separate parser processes."""
from hashlib import sha256
from html.parser import HTMLParser
import json
import re
import zlib

from apps.uptodate.search_extraction import extract_article
from apps.uptodate.text import plain_title

FORMAT_VERSION = 1
MAX_RELATED_TOPICS = 8


class FormulationLinks(HTMLParser):
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
            if label and len(self.targets) < MAX_RELATED_TOPICS:
                self.targets.append({"id": self.current["id"], "title": label})
            self.current = None


def directory_links(identifier, body, extracted):
    if 'id="formulinkBodyPlaceholder"' not in body and "id='formulinkBodyPlaceholder'" not in body:
        return []
    parser = FormulationLinks()
    parser.feed(body)
    labels = {target["title"] for target in parser.targets}
    if any(block.section_title or (len(block.text) >= 40 and block.text not in labels) for block in extracted.blocks):
        return []
    related, seen = [], {identifier}
    for target in parser.targets:
        if target["id"] not in seen:
            related.append(target)
            seen.add(target["id"])
    return related


class Outline(HTMLParser):
    """Read literal section IDs and nesting; never execute source JavaScript."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack, self.records, self.anchor = [], {}, None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "li":
            self.stack.append({"skip": "sr-button" in (attrs.get("class") or "").split()})
        elif tag == "a" and self.stack and not self.stack[-1]["skip"]:
            identifier = re.fullmatch(r"outline-link-([A-Za-z]\d+)", attrs.get("id", ""))
            identifier = identifier.group(1) if identifier else None
            if identifier is None:
                match = re.search(r"sectionName\s*:\s*['\"]([A-Za-z]\d+)['\"]", attrs.get("onclick", ""))
                identifier = match.group(1) if match else None
            if identifier:
                self.anchor = {"id": identifier, "parts": []}

    def handle_data(self, data):
        if self.anchor is not None:
            self.anchor["parts"].append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.anchor is not None:
            heading = " ".join("".join(self.anchor["parts"]).split())
            if heading and self.stack:
                ancestors = [frame for frame in self.stack[:-1] if frame.get("id")]
                identifier = self.anchor["id"]
                record = {"source_id": identifier, "heading": heading,
                          "heading_path": [frame["heading"] for frame in ancestors] + [heading],
                          "parent_source_id": ancestors[-1]["id"] if ancestors else ""}
                self.records[identifier] = record
                self.stack[-1].update(id=identifier, heading=heading)
            self.anchor = None
        elif tag == "li" and self.stack:
            self.stack.pop()


def prepare_document(identifier, article, *, blob_hash=""):
    body = article["body_html"]
    extracted = extract_article(identifier, body)
    related = directory_links(identifier, body, extracted)
    outline = Outline()
    outline.feed(article.get("outline_html", ""))
    sections, lookup, source_lookup = [], {}, {}

    def section(source_id, heading):
        key = (source_id, heading)
        if key in lookup:
            return lookup[key]
        metadata = outline.records.get(source_id)
        path = metadata["heading_path"][:-1] + [heading] if metadata else ([heading] if heading else [])
        record = {"ordinal": len(sections), "source_id": source_id, "heading": heading,
                  "heading_path": path, "hierarchy_known": bool(metadata),
                  "parent_source_id": metadata["parent_source_id"] if metadata else "",
                  "retrieval_order": None}
        sections.append(record)
        lookup[key] = record
        if source_id:
            source_lookup.setdefault(source_id, record)
        return record

    for record in outline.records.values():
        section(record["source_id"], record["heading"])
    blocks, retrieval_number, retrieval_order, limited = [], 0, 0, False
    for ordinal, block in enumerate(extracted.blocks):
        group = section(block.section_id, block.section_title)
        reason = ("navigation" if related else "complex_table" if block.table_context_status == "complex_review"
                  else "too_short" if len(block.text) < 40 else "too_long" if len(block.text) > 6000 else "")
        number = None
        if not reason:
            retrieval_number += 1
            number = retrieval_number
            if group["retrieval_order"] is None:
                group["retrieval_order"] = retrieval_order
                retrieval_order += 1
        elif not related:
            limited = True
        blocks.append({"ordinal": ordinal, "section_ordinal": group["ordinal"], "retrieval_number": number,
                       "source_anchor": block.paragraph_id, "kind": block.kind, "text": block.text,
                       "table_headers": list(block.table_headers), "table_context_status": block.table_context_status,
                       "exclusion_reason": reason})
    for record in sections:
        parent = source_lookup.get(record.pop("parent_source_id"))
        record["parent_ordinal"] = parent["ordinal"] if parent and parent["ordinal"] < record["ordinal"] else None
    return {"source_id": identifier, "title": plain_title(article["title"]),
            "source_version": str(article.get("version", "")), "content_hash": extracted.content_hash,
            "blob_hash": blob_hash, "is_directory": bool(related), "related_topics": related,
            "raw_block_count": len(blocks), "eligible_block_count": retrieval_number,
            "eligible_section_count": retrieval_order, "filter_limited": limited,
            "sections": sections, "blocks": blocks}


def prepare_blob(item):
    identifier, blob, version = item
    data = json.loads(zlib.decompress(blob))
    if not isinstance(data, dict) or not isinstance(data.get("bodyHtml"), str):
        raise ValueError("INVALID_SOURCE_DOCUMENT")
    return prepare_document(identifier, {"title": data.get("title", ""), "body_html": data["bodyHtml"],
                            "outline_html": data.get("outlineHtml", ""), "version": str(version or "")},
                            blob_hash=sha256(blob).hexdigest())


def prepare_blob_outcome(item):
    try:
        return {"document": prepare_blob(item)}
    except Exception:
        # Source content and exception bodies must not enter build logs.
        return {"error": {"article_id": item[0], "code": "SOURCE_EXTRACTION_FAILED"}}
