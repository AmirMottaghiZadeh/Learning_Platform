"""Cheap, deterministic search normalization; never rewrite source/patient facts."""
import re
import unicodedata

from apps.uptodate.search_catalog import normalize

_LETTERS = str.maketrans("يك۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "یک01234567890123456789")


def question_key(value):
    # Keep decimal points, signs and negation in private plan-cache identities.
    return re.sub(r"\s+", " ", unicodedata.normalize("NFKC", value).translate(_LETTERS)).strip()


def query_text(value):
    return normalize(question_key(value).replace("\u200c", " "))


def unique_words(value, limit=24):
    return list(dict.fromkeys(query_text(value).split()))[:limit]
