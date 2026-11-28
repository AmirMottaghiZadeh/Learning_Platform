"""Versioned UpToDate block extraction for search anchors and offline retrieval.

Anchors identify a block only within the exact input HTML revision. Annotating
the original start tag preserves the article markup and lets a browser resolve
the target without assuming that its DOM tree matches Python's parser tree.
This prototype requires browser/WebView validation before production use.
"""

from dataclasses import dataclass
from hashlib import sha256
from html import escape
from html.parser import HTMLParser
import re


ANCHOR_ATTRIBUTE = "data-pharmenta-search-anchor"
EXTRACTION_VERSION = "utd-blocks-v4"
_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
_EXCLUDED_IDS = frozenset({"references", "reference"})
_SKIP_TEXT = frozenset({"script", "style", "noscript"})


@dataclass(frozen=True)
class SearchBlock:
    paragraph_id: str
    kind: str
    section_id: str
    section_title: str
    text: str
    table_headers: tuple[str, ...] = ()
    table_context_status: str = ""


@dataclass(frozen=True)
class ExtractedArticle:
    content_id: str
    content_hash: str
    version: str
    html: str
    blocks: tuple[SearchBlock, ...]


class _TopicProbe(HTMLParser):
    def __init__(self):
        super().__init__()
        self.count = 0

    def handle_starttag(self, tag, attrs):
        self.count += dict(attrs).get("id") == "topicText"


class _TableProbe(HTMLParser):
    """Mark tables whose header associations cannot safely be inferred."""
    def __init__(self, body):
        super().__init__()
        self.line_offsets = [0] + [m.end() for m in re.finditer("\n", body)]
        self.stack = []
        self.unsafe = set()

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            offset = self.line_offsets[self.getpos()[0] - 1] + self.getpos()[1]
            if self.stack:
                self.unsafe.update(item["offset"] for item in self.stack)
                self.unsafe.add(offset)
            self.stack.append({"offset": offset, "header_rows": 0, "in_header_row": False})
        elif self.stack and tag == "tr":
            self.stack[-1]["in_header_row"] = False
        elif self.stack and tag in {"th", "td"}:
            attr = dict(attrs)
            if any(attr.get(name) not in (None, "1") for name in ("rowspan", "colspan")):
                self.unsafe.update(item["offset"] for item in self.stack)
            if tag == "th" and not self.stack[-1]["in_header_row"]:
                table = self.stack[-1]
                table["in_header_row"] = True
                table["header_rows"] += 1
                if table["header_rows"] > 1:
                    self.unsafe.add(table["offset"])

    def handle_endtag(self, tag):
        if tag == "table" and self.stack:
            self.stack.pop()


class _Extractor(HTMLParser):
    def __init__(self, content_id, body, has_topic, unsafe_tables):
        super().__init__(convert_charrefs=True)
        self.content_id = str(content_id)
        self.body = body
        self.content_hash = sha256(body.encode("utf-8")).hexdigest()
        self.stack = []
        self.active = None
        self.heading = None
        self.section_id = ""
        self.section_title = ""
        self.blocks = []
        self.insertions = []
        self.has_topic = has_topic
        self.tables = []
        self.unsafe_tables = unsafe_tables
        self.line_offsets = [0]
        for match in re.finditer("\n", body):
            self.line_offsets.append(match.end())

    def _offset(self):
        line, col = self.getpos()
        return self.line_offsets[line - 1] + col

    def _inside_excluded(self):
        return any(item[1] for item in self.stack)

    def _drug_section(self):
        return next((item for item in reversed(self.stack) if item[2]), None)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if ANCHOR_ATTRIBUTE in attrs:
            raise ValueError("Input HTML already contains the reserved search anchor attribute")
        excluded = (self._inside_excluded() or tag in _SKIP_TEXT or
                    (attrs.get("id") or "").lower() in _EXCLUDED_IDS)
        eligible = (not excluded and (not self.has_topic or attrs.get("id") == "topicText" or
                                      any(item[4] for item in self.stack)))
        if tag == "table" and eligible:
            self.tables.append({"headers": (), "unsafe": self._offset() in self.unsafe_tables})
        classes = set((attrs.get("class") or "").split())
        is_heading = tag == "p" and "headingAnchor" in classes
        if eligible and is_heading and self.active is None:
            self.heading = {"tag": "p", "id": attrs.get("id") or "", "parts": [],
                            "offset": self._offset(), "label": [], "tail": [],
                            "label_depth": None, "label_closed": False}
        elif eligible and tag == "h2" and self._drug_section() and self.active is None:
            self.heading = {"tag": "h2", "id": "", "parts": [], "label_depth": None}
        elif eligible and self.active is None and self.heading is None and tag in {"p", "li", "tr"}:
            # Nested p/li/tr belong to the enclosing block, not separate hits.
            self.active = {"tag": tag, "offset": self._offset(), "parts": [], "depth": 1,
                           "cells": [], "cell": None, "header_row": False}
        elif eligible and self.active is not None and tag == self.active["tag"]:
            self.active["depth"] += 1
        elif eligible and self.active is not None and tag in {"br", "td", "th"}:
            self.active["parts"].append(" ")
            if self.active["tag"] == "tr" and tag in {"td", "th"}:
                self.active["cell"] = []
                self.active["header_row"] |= tag == "th"
        if (eligible and self.heading is not None and self.heading["tag"] == "p"
                and tag == "span" and any(re.fullmatch(r"h[1-6]", name) for name in classes)
                and self.heading["label_depth"] is None):
            # A headingAnchor paragraph may contain both a short heading span
            # and clinical prose. The span supplies metadata; the whole
            # paragraph remains an anchored block when prose follows it.
            self.heading["label_depth"] = len(self.stack)
        if tag not in _VOID:
            section = attrs.get("id") or ""
            if tag != "div" or not re.fullmatch(r"F\d+", section):
                section = ""
            self.stack.append([tag, excluded, section, "", attrs.get("id") == "topicText"])

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self._inside_excluded():
            return
        if self.heading is not None:
            self.heading["parts"].append(data)
            if self.heading.get("label_closed"):
                self.heading["tail"].append(data)
            elif self.heading["label_depth"] is not None:
                self.heading["label"].append(data)
        elif self.active is not None:
            self.active["parts"].append(data)
            if self.active["cell"] is not None:
                self.active["cell"].append(data)

    def handle_endtag(self, tag):
        closing = next((item for item in reversed(self.stack) if item[0] == tag), None)
        if closing is not None and closing[1]:
            for i in range(len(self.stack) - 1, -1, -1):
                if self.stack[i][0] == tag:
                    del self.stack[i:]
                    break
            return
        if self.active is not None and tag in {"td", "th"} and self.active["cell"] is not None:
            self.active["cells"].append(" ".join("".join(self.active["cell"]).split()))
            self.active["cell"] = None
        if (self.heading is not None and self.heading["label_depth"] is not None
                and tag == "span" and len(self.stack) - 1 == self.heading["label_depth"]):
            self.heading["label_closed"] = True
        if self.heading is not None and tag == self.heading["tag"]:
            heading = self.heading
            title_parts = heading["label"] if heading["label_depth"] is not None else heading["parts"]
            title = " ".join("".join(title_parts).split())
            drug_section = self._drug_section()
            if tag == "h2" and drug_section:
                drug_section[3] = title
            else:
                self.section_id = self.heading["id"]
                self.section_title = title
            self.heading = None
            tail = " ".join("".join(heading.get("tail", ())).split()).strip(" —–")
            if tag == "p" and tail:
                self.active = {"tag": "p", "offset": heading["offset"],
                               "parts": heading["parts"], "depth": 1,
                               "cells": [], "cell": None, "header_row": False}
        if self.active is not None and tag == self.active["tag"]:
            self.active["depth"] -= 1
        if self.active is not None and tag == self.active["tag"] and self.active["depth"] == 0:
            text = " ".join("".join(self.active["parts"]).split())
            if text:
                ordinal = len(self.blocks)
                anchor = "utd-" + sha256(
                    f"{EXTRACTION_VERSION}\0{self.content_id}\0{self.content_hash}\0{ordinal}".encode("utf-8")
                ).hexdigest()[:32]
                offset = self.active["offset"]
                # HTMLParser supplies the exact start tag, including spelling.
                opening = self.body[offset:self.body.find(">", offset) + 1]
                match = re.match(r"<\s*[^\s/>]+", opening)
                if not match:
                    raise ValueError("Unable to annotate block start tag")
                self.insertions.append((offset + match.end(), f' {ANCHOR_ATTRIBUTE}="{escape(anchor, quote=True)}"'))
                drug_section = self._drug_section()
                section_id = drug_section[2] if drug_section else self.section_id
                section_title = drug_section[3] if drug_section else self.section_title
                table = self.tables[-1] if self.tables and self.active["tag"] == "tr" else None
                headers = table["headers"] if table and not table["unsafe"] else ()
                if self.tables and self.active["tag"] == "tr" and self.active["header_row"]:
                    self.tables[-1]["headers"] = tuple(self.active["cells"])
                    headers = ()
                status = ("complex_review" if table["unsafe"] else "simple") if table else ""
                self.blocks.append(SearchBlock(anchor, self.active["tag"], section_id, section_title, text, headers, status))
            self.active = None
        if tag == "table" and self.tables and not self._inside_excluded():
            self.tables.pop()
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                del self.stack[i:]
                break

    def result(self):
        pieces = []
        previous = 0
        for offset, value in self.insertions:
            pieces.extend((self.body[previous:offset], value))
            previous = offset
        pieces.append(self.body[previous:])
        html = "".join(pieces)
        return ExtractedArticle(self.content_id, self.content_hash, EXTRACTION_VERSION, html, tuple(self.blocks))


def extract_article(content_id: str, body_html: str, *, require_topic: bool = False) -> ExtractedArticle:
    if not isinstance(body_html, str):
        raise TypeError("body_html must be a string")
    probe = _TopicProbe()
    probe.feed(body_html)
    if probe.count > 1:
        raise ValueError("Input HTML has duplicate topicText containers")
    if require_topic and probe.count != 1:
        raise ValueError("Input HTML has no topicText container")
    tables = _TableProbe(body_html)
    tables.feed(body_html)
    tables.close()
    parser = _Extractor(content_id, body_html, bool(probe.count), tables.unsafe)
    parser.feed(body_html)
    parser.close()
    return parser.result()
