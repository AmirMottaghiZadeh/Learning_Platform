"""Keep original blocks intact and retain their citation IDs when grouping context."""
from functools import lru_cache
from hashlib import sha256
import re
import uuid

CHUNKER_VERSION = "clinical-blocks-v1"
TARGET_TOKENS = 500


@lru_cache(maxsize=1)
def tokenizer():
    import tiktoken
    return tiktoken.get_encoding("cl100k_base")


def token_count(text):
    return len(tokenizer().encode(text, disallowed_special=()))


def source_metadata(title, path):
    # The closest heading overrides a monograph title (pediatric monographs
    # also contain Adult dosing). Never infer age from the title alone.
    audience = "general"
    for value in [title, *path]:
        if re.search(r"\b(?:pediatric|paediatric|children|infants?|neonat|adolescen)", value, re.I):
            audience = "pediatric"
        elif re.search(r"\badults?\b", value, re.I):
            audience = "adult"
    kind = "drug" if "drug information" in title.lower() else "patient" if re.search(r"patient (?:education|information)", title, re.I) else "topic"
    return audience, kind


def article_chunks(article, paragraphs, generation_id):
    """Streaming iterator, grouping only adjacent eligible blocks in one section.

    A long original block stays intact: truncation must never remove qualifiers
    or detach a dose from its population. Oversized inputs are reported by the
    embedding manifest before any paid call.
    """
    group, size, section, ordinal = [], 0, None, 0

    def make(rows, number):
        heading = rows[0].section
        path = list(heading.heading_path)
        text = "\n\n".join(p.text for p in rows)
        embedding_input = f"{article.title}\n{' > '.join(path) or heading.heading}\n{text}"
        audience, kind = source_metadata(article.title, path)
        return {"id": uuid.uuid5(generation_id, f"{article.source_id}:{number}"),
                "generation_id": generation_id, "source_id": article.source_id,
                "content_hash": article.content_hash, "ordinal": number,
                "title": article.title, "heading": heading.heading, "heading_path": path,
                "text": text, "audience": audience, "source_kind": kind,
                "block_ids": [p.pk for p in rows], "token_count": token_count(embedding_input),
                "input_hash": sha256(embedding_input.encode()).hexdigest()}

    for paragraph in paragraphs:
        if paragraph.retrieval_number is None:
            if group:
                yield make(group, ordinal); ordinal += 1; group, size = [], 0
            section = None
            continue
        tokens = token_count(paragraph.text)
        if group and (paragraph.section_id != section or size + tokens > TARGET_TOKENS):
            yield make(group, ordinal); ordinal += 1; group, size = [], 0
        group.append(paragraph); size += tokens
        section = paragraph.section_id
    if group:
        yield make(group, ordinal)
