import re
import json
from functools import lru_cache
from pathlib import Path

from .normalizer import normalize_text

TOKEN_RE = re.compile(r"\b[A-Za-zµ]+\b|[آ-ی]+")
RULES_PATH = Path(__file__).resolve().parents[1] / "rules" / "terminology_map.json"


@lru_cache(maxsize=1)
def load_terminology_map():
    if not RULES_PATH.exists():
        return {}
    return json.loads(RULES_PATH.read_text(encoding="utf-8"))


def _map(name):
    return load_terminology_map().get(name, {})


def _unit_re():
    units = sorted(_map("units"), key=len, reverse=True)
    if not units:
        return None
    escaped = "|".join(re.escape(unit) for unit in units)
    return re.compile(rf"(?P<num>\d+(?:\.\d+)?)\s*(?P<unit>{escaped})\b|(?P<percent_num>\d+(?:\.\d+)?)\s*(?P<percent_unit>%)", re.I)


def normalize_dosage_form(value):
    text = normalize_text(value)
    if not text:
        return text, []

    changes = []
    dosage_form_map = _map("dosage_forms")
    unit_map = _map("units")

    def replace_token(match):
        token = match.group(0)
        mapped = dosage_form_map.get(token.casefold()) or dosage_form_map.get(token)
        if mapped:
            changes.append({"from": token, "to": mapped, "type": "dosage_form"})
            return mapped
        return token

    text = TOKEN_RE.sub(replace_token, text)

    def replace_unit(match):
        unit = match.group("unit") or match.group("percent_unit")
        number = match.group("num") or match.group("percent_num")
        mapped = unit_map.get(unit.casefold()) or unit_map.get(unit) or unit
        replacement = f"{number} {mapped}"
        if mapped != unit or replacement != match.group(0):
            changes.append({"from": unit, "to": mapped, "type": "unit"})
        return replacement

    unit_re = _unit_re()
    if unit_re:
        text = unit_re.sub(replace_unit, text)
    return normalize_text(text), changes


def normalize_common_terms(value):
    text = normalize_text(value)
    if not text:
        return text, []
    aliases = _map("drug_term_aliases")
    timing_values = _map("timing_values")
    changes = []

    exact = aliases.get(text.casefold()) or aliases.get(text)
    if exact and exact != text:
        changes.append({"from": text, "to": exact, "type": "drug_term_alias"})
        return exact, changes

    timing = timing_values.get(text)
    if timing and timing != text:
        changes.append({"from": text, "to": timing, "type": "timing"})
        return timing, changes

    return text, changes


def check_terminology(value, *, field_name=""):
    if field_name == "dosage_form":
        normalized, changes = normalize_dosage_form(value)
    else:
        normalized, changes = normalize_common_terms(value)
    return {
        "normalized": normalized,
        "changes": changes,
        "has_changes": bool(changes) and normalized != normalize_text(value),
    }
