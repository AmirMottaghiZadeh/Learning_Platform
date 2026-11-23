"""Read source-owned article and graphic links as literal HTML metadata."""
from collections import deque
from dataclasses import dataclass
from html.parser import HTMLParser
import re

_VOID = frozenset("area base br col embed hr img input link meta param source track wbr".split())
_REGIONS = {"outlinerelatedgraphicslinks": "graphics", "outlinerelatedtopicslinks": "topics"}
_ID = re.compile(r"[0-9]{1,12}\Z")
_OPERATION = re.compile(r"\bdoOperation\s*\(")
_ARRAY = re.compile(r"\bcontentIds[\"']?\s*:\s*\[([^\]]{1,1500})\]")
_SINGLE = re.compile(r"\bcontentId[\"']?\s*:\s*[\"']?([0-9]{1,12})(?![0-9])")
_GRAPHIC_LABEL = re.compile(r"^(?:(?:see|view)\s+)?(?:table|fig\.?|figure|image|algorithm)\s*(?:#?\d+|[:.—–])", re.I)


def link_ids(attrs, *, graphic_section=False):
    """Return graphic ids and a singular topic id from known reference anchors."""
    operation = attrs.get("onclick") or ""
    operation = operation if _OPERATION.search(operation) else ""
    graphics = []
    if match := _ARRAY.search(operation):
        for part in match[1].split(","):
            identifier = part.strip().strip("\"'")
            if _ID.fullmatch(identifier):
                graphics.append(identifier)
    for attr in ("data-graphic", "data-graphic-id"):
        identifier = attrs.get(attr) or ""
        if _ID.fullmatch(identifier):
            graphics.append(identifier)
    found = _SINGLE.search(operation)
    topic = found[1] if found else (attrs.get("data-topicid") or attrs.get("data-topic") or "")
    topic = topic if _ID.fullmatch(topic) else ""
    if topic and (graphic_section or "graphic" in (attrs.get("class") or "").split()):
        graphics.append(topic)
        topic = ""
    return list(dict.fromkeys(graphics)), topic


@dataclass(frozen=True)
class MediaLink:
    identifier: str
    graphic: bool
    label: str
    group: str = ""
    context: str = ""


class _Links(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.frames = []
        self.recent = deque(maxlen=12)
        self.anchor = None
        self.heading = None
        self.group = ""
        self.links = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in _VOID:
            return
        region = _REGIONS.get((attrs.get("id") or "").lower(), self.frames[-1][1] if self.frames else "")
        skipped = tag in {"script", "style", "noscript", "template"} or bool(self.frames and self.frames[-1][2])
        self.frames.append((tag, region, skipped))
        if skipped:
            return
        depth = len(self.frames)
        if tag in {"p", "li"} and not region:
            self.recent.clear()
        if region == "graphics" and "relatedGraphicsHeading" in (attrs.get("class") or "").split():
            self.heading = (depth, [])
        if tag == "a":
            graphics, topic = link_ids(attrs, graphic_section=region == "graphics")
            targets = [(identifier, True) for identifier in graphics]
            if topic and region == "topics":
                targets.append((topic, False))
            elif topic and not region and "drug" not in (attrs.get("class") or "").split():
                targets.append((topic, None))
            if targets:
                context = " ".join(self.recent)[-600:] if not region else ""
                self.anchor = (depth, targets, [], self.group if region == "graphics" else "", context)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag not in _VOID:
            self.handle_endtag(tag)

    def handle_data(self, data):
        if self.frames and self.frames[-1][2]:
            return
        if self.anchor:
            self.anchor[2].append(data)
        if self.heading:
            self.heading[1].append(data)
        cleaned = " ".join(data.split())
        if cleaned:
            self.recent.append(cleaned[-600:])

    def handle_endtag(self, tag):
        for index in range(len(self.frames) - 1, -1, -1):
            if self.frames[index][0] != tag:
                continue
            depth = index + 1
            if self.anchor and self.anchor[0] >= depth:
                _, targets, parts, group, context = self.anchor
                label = " ".join("".join(parts).split()).lstrip("-–—• ")[:300]
                for identifier, graphic in targets:
                    direct_graphic = bool(_GRAPHIC_LABEL.match(label)) if graphic is None else graphic
                    self.links.append(MediaLink(identifier, direct_graphic, label, group, context))
                self.anchor = None
            if self.heading and self.heading[0] >= depth:
                self.group = " ".join("".join(self.heading[1]).split())[:120]
                self.heading = None
            del self.frames[index:]
            break


def media_links(html):
    parser = _Links()
    parser.feed(html)
    parser.close()
    return list(dict.fromkeys(parser.links))


def graphic_ids(html):
    return list(dict.fromkeys(link.identifier for link in media_links(html) if link.graphic))
