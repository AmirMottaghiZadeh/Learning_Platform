import re
import json
from pathlib import Path

DEFAULT_CHARACTER_MAP = {
    "ي": "ی",
    "ى": "ی",
    "ك": "ک",
    "ة": "ه",
}
DEFAULT_DIGIT_MAP = {
    "۰": "0",
    "۱": "1",
    "۲": "2",
    "۳": "3",
    "۴": "4",
    "۵": "5",
    "۶": "6",
    "۷": "7",
    "۸": "8",
    "۹": "9",
    "٠": "0",
    "١": "1",
    "٢": "2",
    "٣": "3",
    "٤": "4",
    "٥": "5",
    "٦": "6",
    "٧": "7",
    "٨": "8",
    "٩": "9",
}
RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "terminology_map.json"
RULES = {}
if RULES_PATH.exists():
    RULES = json.loads(RULES_PATH.read_text(encoding="utf-8"))
ARABIC_TO_PERSIAN = str.maketrans(RULES.get("character_normalization") or DEFAULT_CHARACTER_MAP)
DIGIT_TRANSLATION = str.maketrans(RULES.get("digit_normalization") or DEFAULT_DIGIT_MAP)
ZERO_WIDTH_CHARS = "\u200c\u200d\u200e\u200f\ufeff"
SPACE_RE = re.compile(r"\s+")
PERSIAN_RE = re.compile(r"[\u0600-\u06FF]")
LATIN_RE = re.compile(r"[A-Za-z]")
ARABIC_VARIANT_RE = re.compile(r"[يك]\b|[يك]")
MALFORMED_SPACE_BEFORE_PUNCT_RE = re.compile(r"\s+([,.;:،؛])")
MALFORMED_SPACE_AFTER_PUNCT_RE = re.compile(r"([,.;:،؛])(\S)")


def to_text(value):
    return "" if value is None else str(value)


def normalize_persian_characters(value):
    text = to_text(value)
    for char in ZERO_WIDTH_CHARS:
        text = text.replace(char, " ")
    return text.translate(ARABIC_TO_PERSIAN).translate(DIGIT_TRANSLATION)


def normalize_spacing(value):
    text = to_text(value).strip()
    text = SPACE_RE.sub(" ", text)
    text = MALFORMED_SPACE_BEFORE_PUNCT_RE.sub(r"\1", text)
    text = MALFORMED_SPACE_AFTER_PUNCT_RE.sub(r"\1 \2", text)
    return text.strip()


def normalize_text(value):
    return normalize_spacing(normalize_persian_characters(value))


def canonical_signature(value):
    text = normalize_text(value).casefold()
    return "".join(ch for ch in text if ch.isalnum() or "آ" <= ch <= "ی")


def has_persian(value):
    return bool(PERSIAN_RE.search(to_text(value)))


def has_latin(value):
    return bool(LATIN_RE.search(to_text(value)))


def has_mixed_persian_english(value):
    text = to_text(value)
    return has_persian(text) and has_latin(text)


def has_arabic_persian_inconsistency(value):
    return bool(ARABIC_VARIANT_RE.search(to_text(value)))


def has_extra_spaces(value):
    text = to_text(value)
    if not text:
        return False
    return text != text.strip() or bool(re.search(r"\s{2,}", text.strip()))


def standard_english_casing(value):
    text = normalize_text(value)
    if not text or has_persian(text):
        return text
    small_words = {"and", "or", "of", "with", "for", "in", "the"}
    words = []
    for index, word in enumerate(text.split(" ")):
        lower = word.lower()
        if index and lower in small_words:
            words.append(lower)
        elif word.isupper() and len(word) <= 4:
            words.append(word.upper())
        else:
            words.append(lower[:1].upper() + lower[1:])
    return " ".join(words)
