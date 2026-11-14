"""Fixes to the text of drug profile summaries, requested by the owner on
2026-11-01. Two kinds, both on whole summaries of one field and language:

1. Side-effect categories each on a line of their own. The adverse-reactions
   summaries are bullets opening with a category -- «شایع:», «مهم و جدی:»,
   «نادر:» (Common, Important/Serious, Rare) -- which the lesson screen shows
   in bold. In about 50 drugs a category was run into the previous bullet
   after a semicolon («…سندرم سروتونین؛ نادر: تشنج…») and lost its bold.
   Only a category right after «؛» or «;» is split off: «نادر:» elsewhere is
   an adjective («نارسایی کبدی کلستاتیک نادر:» in warnings).

2. Commentary about the source text, which says nothing about the drug. The
   summaries were written from label excerpts, and where an excerpt was cut
   short or was not what its heading promised, the summary said so:
   «فقط به محتوای 600 mg بطری اشاره دارد» as azithromycin's boxed warning
   (its label's "boxed" text is only "contents per bottle 600 mg"), «این بخش
   داده‌ای درباره‌ی پتانسیل سوءمصرف ندارد…», "The available text does not
   preserve the specific mg dose for this excerpt — refer to the full
   prescribing information." A line that is nothing but such commentary is
   dropped; a commentary sentence or bracket inside a line with real content
   («… یک‌بار در روز. متن موجود دوز شروع دقیق را در این بخش حفظ نکرده است —
   به اطلاعات کامل تجویز مراجعه شود. دوز نباید …») is cut and the rest kept.
   The patterns are the ones found by reading every match in the pipeline
   file, not guesses: "pharmacy bulk package" is real content under dosage
   forms and dosing, and is dropped only when it is a boxed warning's whole
   text.
"""

import re

ZWNJ = "‌"

# -- 1. side-effect categories ------------------------------------------------

_CATEGORIES = r"(?:شایع|مهم و جدی|مهم/جدی|نادر|Common|Important/Serious|Rare)"
_RUN_IN_CATEGORY = re.compile(rf"\s*[؛;]\s*(?={_CATEGORIES}\s*[:：])")


def split_categories(text):
    """Every side-effect category after «؛»/«;» moved to a new bullet."""
    out = []
    for line in text.split("\n"):
        bullet = "- " if line.lstrip().startswith("-") else ""
        out.append(_RUN_IN_CATEGORY.sub("\n" + bullet, line))
    return "\n".join(out)


# -- 2. commentary about the source -------------------------------------------

def _fa(pattern):
    """A Persian pattern where a zero-width non-joiner may or may not be
    written between the parts of a word («داده‌ای» / «داده ای»)."""
    return pattern.replace("‌", f"[{ZWNJ} ]?")


# A whole line (after its bullet) that is only commentary.
_META_LINES = [
    re.compile(r"^only (mentions?|refers? to|lists?)\b", re.I),
    re.compile(r"^no clinical boxed warning (is )?present\.?$", re.I),
    re.compile(r"^this section contains no [^;.]*data[;,.] it (only )?describes\b", re.I),
    re.compile(_fa(r"^فقط به .{1,80}اشاره (دارد|می‌کند)\.?$")),
    re.compile(_fa(r"^این بخش داده‌ای [^؛.]*ندارد[؛،.]")),
]
# Only the whole text of a boxed warning: a heading from the package, not a
# warning. Elsewhere the same words are real content.
_META_BOXED = re.compile(_fa(r"^(pharmacy bulk package|بسته‌بندی انبوه داروخانه‌ای)\.?$"), re.I)

# Commentary inside a line: in brackets, or a sentence (to its full stop, a
# dash clause to the end of the sentence). A full stop ends a sentence only
# before a space or the end, so «0.1 mL» is never cut.
_END = r"(?:\.(?=\s|$)|$)"
_META_CLAUSES = [
    re.compile(r"\s*\((?:the available text|متن موجود)[^()]*\)", re.I),
    re.compile(rf"\s*—?\s*\bthe available text does not preserve\b.*?{_END}", re.I),
    re.compile(_fa(rf"\s*—?\s*متن موجود .*?حفظ نکرده است(?:\s*—\s*.*?مراجعه شود)?{_END}")),
]


def _drop_clauses(content):
    for pattern in _META_CLAUSES:
        content = pattern.sub("", content)
    content = re.sub(r"\s{2,}", " ", content).strip()
    content = re.sub(r"\s+([.,;:،؛])", r"\1", content)
    return content.rstrip(" —-").strip()


def drop_source_commentary(text, field):
    """`text` without lines, sentences or brackets that only comment on the
    source. Returns (text, number of cuts)."""
    kept, cuts = [], 0
    for line in text.split("\n"):
        stripped = line.strip()
        bullet = stripped.startswith("- ")
        content = stripped[2:].strip() if bullet else stripped
        if not content:
            kept.append(line)
            continue
        if any(p.search(content) for p in _META_LINES) or (field == "boxed_warning" and _META_BOXED.match(content)):
            cuts += 1
            continue
        cleaned = _drop_clauses(content)
        if cleaned != content:
            cuts += 1
            if not cleaned:
                continue
            line = ("- " if bullet else "") + cleaned
        kept.append(line)
    return "\n".join(kept), cuts


def fix_summary(text, field):
    """Both fixes; returns the text unchanged when there is nothing to do."""
    fixed = split_categories(text) if field == "adverse_reactions" else text
    fixed, _ = drop_source_commentary(fixed, field)
    return fixed
