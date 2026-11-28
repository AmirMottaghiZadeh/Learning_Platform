"""Automatic checks on a proposed summary, plus the word diff shown to the
operator while editing and to the reviewer before approving.

Checks only ever warn -- they point a human at something to look at; the
reviewer decides. Each result is `{"key", "level": "ok" | "warn", "label"}`
with a Persian label ready to show.
"""

import difflib
import re

from django.utils.html import escape

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩٫", "01234567890123456789.")
_NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
_THOUSANDS_RE = re.compile(r"(?<=\d)[,٬](?=\d{3}\b)")
_TOKEN_RE = re.compile(r"\s+|[^\s]+")

# A summary longer than this share of its source is no longer a summary.
MAX_LENGTH_RATIO = 1.0


def _numbers(text: str) -> list[str]:
    normalized = _THOUSANDS_RE.sub("", (text or "").translate(_DIGITS))
    return _NUMBER_RE.findall(normalized)


def _canonical(number: str) -> str:
    # "5.0" and "5" are the same dose.
    return number.rstrip("0").rstrip(".") if "." in number else number


def numbers_missing_from_source(raw_text: str, *summaries: str) -> list[str]:
    source = {_canonical(n) for n in _numbers(raw_text)}
    missing = []
    for summary in summaries:
        for number in _numbers(summary):
            canonical = _canonical(number)
            if canonical not in source and canonical not in missing:
                missing.append(canonical)
    return missing


def run_checks(raw_text: str, before_fa: str, after_fa: str, before_en: str, after_en: str) -> list[dict]:
    results = []
    raw = (raw_text or "").strip()
    fa = (after_fa or "").strip()
    en = (after_en or "").strip()

    if raw and (fa or en):
        missing = numbers_missing_from_source(raw, fa, en)
        if missing:
            shown = "، ".join(missing[:4]) + ("…" if len(missing) > 4 else "")
            results.append({"key": "numbers", "level": "warn", "label": f"عدد در متن منبع نیست: {shown}"})
        elif _numbers(fa) or _numbers(en):
            results.append({"key": "numbers", "level": "ok", "label": "اعداد با منبع می‌خواند"})

    if raw and not fa:
        results.append({"key": "empty_fa", "level": "warn", "label": "خلاصهٔ فارسی خالی است"})
    if raw and not en:
        results.append({"key": "empty_en", "level": "warn", "label": "خلاصهٔ انگلیسی خالی است"})

    fa_changed = fa != (before_fa or "").strip()
    en_changed = en != (before_en or "").strip()
    if fa and en:
        if fa_changed and not en_changed and (before_en or "").strip():
            results.append({"key": "sync", "level": "warn", "label": "فقط نسخهٔ فارسی تغییر کرده"})
        elif en_changed and not fa_changed and (before_fa or "").strip():
            results.append({"key": "sync", "level": "warn", "label": "فقط نسخهٔ انگلیسی تغییر کرده"})
        else:
            results.append({"key": "sync", "level": "ok", "label": "فارسی و انگلیسی هم‌گام"})

    if raw and en:
        ratio = len(en) / max(1, len(raw))
        if ratio > MAX_LENGTH_RATIO:
            results.append({"key": "length", "level": "warn", "label": "خلاصه از متن منبع بلندتر است"})
        else:
            results.append({"key": "length", "level": "ok", "label": f"طول خلاصه {round(ratio * 100)}٪ منبع"})

    return results


def warning_count(results: list[dict]) -> int:
    return sum(1 for r in results if r.get("level") == "warn")


def word_diff(before: str, after: str) -> tuple[str, int, int]:
    """HTML of `after` with removed words struck through (<del>) and added
    ones marked (<ins>), plus the counts of words added and removed."""
    a = _TOKEN_RE.findall(before or "")
    b = _TOKEN_RE.findall(after or "")
    parts, added, removed = [], 0, 0
    for op, i1, i2, j1, j2 in difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes():
        if op == "equal":
            parts.append(escape("".join(a[i1:i2])))
            continue
        if op in ("delete", "replace"):
            old = "".join(a[i1:i2])
            removed += sum(1 for t in a[i1:i2] if t.strip())
            if old.strip():
                parts.append(f"<del>{escape(old)}</del>")
        if op in ("insert", "replace"):
            new = "".join(b[j1:j2])
            added += sum(1 for t in b[j1:j2] if t.strip())
            if new.strip():
                parts.append(f"<ins>{escape(new)}</ins>")
            else:
                parts.append(escape(new))
    return "".join(parts), added, removed
