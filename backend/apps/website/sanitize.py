"""An allow-list HTML sanitizer for what the panel's editor saves.

Everything an editor writes is cleaned on save, so the public pages can print
it as-is: tags and attributes not on the lists below are dropped, `script`
and friends are removed with their content, and links may only be http(s),
mailto, tel or relative. It rebuilds the markup from a parse rather than
patching strings, so malformed input cannot slip a tag through.
"""

import html
import re
from html.parser import HTMLParser

ALLOWED_TAGS = {
    "p", "br", "h2", "h3", "h4", "strong", "em", "u", "s", "a", "ul", "ol", "li", "blockquote", "img",
    "figure", "figcaption", "table", "thead", "tbody", "tr", "th", "td", "hr", "code", "pre", "div",
    "span", "sup", "sub",
}
ALIASES = {"b": "strong", "i": "em", "strike": "s", "del": "s", "h1": "h2", "h5": "h4", "h6": "h4"}
VOID = {"br", "hr", "img"}
# Dropped together with everything inside them.
DROP_WITH_CONTENT = {"script", "style", "iframe", "object", "embed", "noscript", "template", "svg", "math", "form", "textarea", "select", "button", "head", "title"}
ALLOWED_ATTRS = {
    "a": {"href", "title", "target", "rel"},
    "img": {"src", "alt", "width", "height", "title"},
    "td": {"colspan", "rowspan"},
    "th": {"colspan", "rowspan"},
    "ol": {"start"},
    "p": {"class"}, "h2": {"class"}, "h3": {"class"}, "h4": {"class"}, "div": {"class"}, "span": {"class"},
    "figure": {"class"}, "ul": {"class"},
}
ALLOWED_CLASSES = {"callout", "cta-app", "note", "ta-center", "ta-right", "ta-left", "lead", "tbl"}
_SCHEMES = ("http://", "https://", "mailto:", "tel:")
_CTRL = re.compile(r"[\x00-\x20\x7f]+")


def safe_url(value, *, image=False):
    value = (value or "").strip()
    compact = _CTRL.sub("", value).lower()
    if not compact:
        return ""
    if compact.startswith(("/", "#", "?")) and not compact.startswith("//"):
        return value
    allowed = ("http://", "https://") if image else _SCHEMES
    if compact.startswith(allowed):
        return value
    return ""


class _Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out = []
        self.stack = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        tag = ALIASES.get(tag, tag)
        if tag in DROP_WITH_CONTENT or self.skip:
            if tag in DROP_WITH_CONTENT and tag not in VOID:
                self.skip += 1
            return
        if tag not in ALLOWED_TAGS:
            return
        clean = self._attrs(tag, attrs)
        if tag == "a" and clean.get("href") and "rel" not in clean:
            clean["rel"] = "noopener noreferrer"
        if tag == "img" and not clean.get("src"):
            return
        if tag == "a" and clean.get("target") not in (None, "_blank"):
            clean.pop("target")
        text = "".join(f' {k}="{html.escape(v, quote=True)}"' for k, v in clean.items())
        self.out.append(f"<{tag}{text}>")
        if tag not in VOID:
            self.stack.append(tag)

    def handle_startendtag(self, tag, attrs):
        tag = ALIASES.get(tag, tag)
        if tag in DROP_WITH_CONTENT:
            return
        depth = len(self.stack)
        self.handle_starttag(tag, attrs)
        if len(self.stack) > depth:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        tag = ALIASES.get(tag, tag)
        if tag in DROP_WITH_CONTENT:
            if self.skip:
                self.skip -= 1
            return
        if self.skip or tag not in ALLOWED_TAGS or tag in VOID:
            return
        if tag in self.stack:
            while self.stack:
                top = self.stack.pop()
                self.out.append(f"</{top}>")
                if top == tag:
                    break

    def handle_data(self, data):
        if not self.skip:
            self.out.append(html.escape(data, quote=False))

    def _attrs(self, tag, attrs):
        allowed = ALLOWED_ATTRS.get(tag, set())
        clean = {}
        for name, value in attrs:
            name = (name or "").lower()
            value = value or ""
            if name not in allowed:
                continue
            if name == "href":
                value = safe_url(value)
            elif name == "src":
                value = safe_url(value, image=True)
            elif name == "class":
                value = " ".join(c for c in value.split() if c in ALLOWED_CLASSES)
            elif name in ("width", "height", "colspan", "rowspan", "start"):
                value = value if value.isdigit() and len(value) <= 4 else ""
            elif name == "rel":
                value = "noopener noreferrer"
            elif name == "target":
                value = "_blank" if value == "_blank" else ""
            if value != "" or name == "alt":
                clean[name] = value
        return clean

    def result(self):
        while self.stack:
            self.out.append(f"</{self.stack.pop()}>")
        return "".join(self.out)


def clean_html(value):
    parser = _Cleaner()
    parser.feed(value or "")
    parser.close()
    return parser.result().strip()


class _Text(HTMLParser):
    BLOCK = {"p", "br", "li", "div", "h2", "h3", "h4", "tr", "blockquote", "figcaption"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in DROP_WITH_CONTENT:
            self.skip += 1
        elif tag in self.BLOCK:
            self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in DROP_WITH_CONTENT and self.skip:
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip:
            self.parts.append(data)


def plain_text(value):
    """The text of an HTML fragment, whitespace collapsed."""
    parser = _Text()
    parser.feed(value or "")
    parser.close()
    return re.sub(r"\s+", " ", "".join(parser.parts)).strip()
