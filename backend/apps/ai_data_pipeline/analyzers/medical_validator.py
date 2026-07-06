import re

from apps.drugs.services import generic_drug_signature
from apps.ai_data_pipeline.transformers.normalizer import normalize_text

DOSAGE_NUMBER_WITHOUT_UNIT_RE = re.compile(r"\b\d+(?:\.\d+)?\b(?!\s*(mg|mcg|µg|g|ml|mL|IU|%))", re.I)
KNOWN_TIMING_VALUES = {"با غذا", "بدون غذا", "فرقی نمی‌کند", "فرقی نمی کند"}
INVALID_MARKERS = {"", "-", "ندارد", "نامشخص", "none", "unknown", "n/a"}


def validate_drug_record(drug):
    issues = []
    generic_signature = generic_drug_signature(drug)
    if not generic_signature:
        issues.append(_issue(drug, "generic_name", "incomplete_generic_signature", "No usable generic/name/persian identity was detected."))

    if normalize_text(drug.consumption_time_sorted) and normalize_text(drug.consumption_time_sorted) not in KNOWN_TIMING_VALUES:
        issues.append(_issue(drug, "consumption_time_sorted", "invalid_timing_value", "Timing value is outside the allowed canonical set."))

    dosage = normalize_text(drug.dosage_form)
    if dosage and DOSAGE_NUMBER_WITHOUT_UNIT_RE.search(dosage):
        issues.append(_issue(drug, "dosage_form", "malformed_dosage_text", "Dosage text contains numbers that may be missing units."))

    if _invalid(drug.generic_name) and _invalid(drug.name) and _invalid(drug.persian_name):
        issues.append(_issue(drug, "generic_name", "unclear_drug_name", "Drug identity fields are empty or marked as unknown."))

    if drug.brand_name and drug.generic_name and normalize_text(drug.brand_name).casefold() == normalize_text(drug.generic_name).casefold():
        issues.append(_issue(drug, "brand_name", "brand_generic_same_value", "Brand and generic names are identical; verify source data."))

    return issues


def _invalid(value):
    return normalize_text(value).casefold() in INVALID_MARKERS


def _issue(drug, field_name, issue_type, detail):
    return {
        "issue_type": issue_type,
        "table_name": drug._meta.db_table,
        "record_id": drug.id,
        "field_name": field_name,
        "detail": detail,
        "value": str(getattr(drug, field_name, "") or ""),
    }
