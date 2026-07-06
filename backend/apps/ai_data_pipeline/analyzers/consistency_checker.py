from apps.ai_data_pipeline.transformers.normalizer import (
    has_arabic_persian_inconsistency,
    has_extra_spaces,
    has_mixed_persian_english,
    normalize_text,
)


def check_text_consistency(*, table_name, record_id, field_name, value, mixed_allowed=False):
    issues = []
    if value is None:
        return issues
    text = str(value)
    if text == "":
        issues.append({
            "issue_type": "empty_string",
            "table_name": table_name,
            "record_id": record_id,
            "field_name": field_name,
            "detail": "Empty string value.",
        })
        return issues
    if has_extra_spaces(text):
        issues.append({
            "issue_type": "extra_spaces",
            "table_name": table_name,
            "record_id": record_id,
            "field_name": field_name,
            "detail": "Extra leading, trailing, or repeated whitespace detected.",
            "normalized_value": normalize_text(text),
        })
    if has_arabic_persian_inconsistency(text):
        issues.append({
            "issue_type": "arabic_persian_character_inconsistency",
            "table_name": table_name,
            "record_id": record_id,
            "field_name": field_name,
            "detail": "Arabic ي/ك variants detected; Persian ی/ک is expected for Persian text.",
            "normalized_value": normalize_text(text),
        })
    if not mixed_allowed and has_mixed_persian_english(text):
        issues.append({
            "issue_type": "mixed_persian_english",
            "table_name": table_name,
            "record_id": record_id,
            "field_name": field_name,
            "detail": "Persian and English text are mixed in a field where this is usually suspicious.",
        })
    return issues
