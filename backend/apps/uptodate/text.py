"""Plain labels at the API boundary; article HTML itself stays intact."""

from html import unescape
import re


_TAG = re.compile(r"</?[a-z][^>]*>", re.I)
_BREAK = re.compile(r"<br\s*/?>|</(?:p|div|li|h[1-6])\s*>", re.I)


def plain_title(value: str) -> str:
    # Decode before stripping too: imported labels can contain escaped markup.
    # Require a letter after '<', preserving clinical comparisons such as <7.
    text = value or ""
    for _ in range(4):
        clean = _TAG.sub("", _BREAK.sub(" ", unescape(text)))
        if clean == text:
            break
        text = clean
    return re.sub(r"\s+", " ", text).strip()
