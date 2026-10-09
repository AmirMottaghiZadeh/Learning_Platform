"""Breaks one IngredientProfileSection summary into atomic "facts" -- the
same structure the lesson screen's text parser recovers (frontend:
LessonDetailScreen.tsx's parseLessonText), ported here so the question bank
draws on the same already-structured content instead of re-deriving it
differently.

A fact is one bullet item (for the bulleted clinical fields) or one sentence
(for the two paragraph fields, mechanism and pregnancy) -- small enough to
stand alone as a single quiz fact, with its label (if any) split out so a
frequency/dosage-form/population tag doesn't read as part of the sentence.
Deliberately whole-bullet, not split further on internal commas: an
adverse-reactions bullet often parenthesizes sub-symptoms ("injection site
reactions (pain, swelling)"), and a naive comma split breaks those open
unevenly -- whole bullets are safe and still plenty granular.
"""

import re

LABEL_RE = re.compile(r"^([^\d:：]{1,40}):\s+(.+)$", re.S)
BULLET_RE = re.compile(r"^-\s+(.*)$")
SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+(?=\S)")


def split_label(line: str) -> tuple[str | None, str]:
    m = LABEL_RE.match(line)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return None, line.strip()


def split_sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT_RE.split(text) if s.strip()]


def extract_facts(text: str) -> list[dict]:
    """Returns [{"label": str|None, "text": str}, ...] for one summary."""
    facts: list[dict] = []
    para_lines: list[str] = []

    def flush_paragraph():
        if not para_lines:
            return
        label, body = split_label(" ".join(para_lines))
        for sentence in split_sentences(body) or [body]:
            if sentence:
                facts.append({"label": label, "text": sentence})
        para_lines.clear()

    for raw in text.split("\n"):
        line = raw.strip()
        if not line:
            continue
        bullet = BULLET_RE.match(line)
        if bullet:
            flush_paragraph()
            label, body = split_label(bullet.group(1))
            if body:
                facts.append({"label": label, "text": body})
        else:
            para_lines.append(line)
    flush_paragraph()
    return facts
