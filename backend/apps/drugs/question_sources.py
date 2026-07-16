INVALID_QUESTION_VALUES = {"", "-", "ندارد", "نامشخص", "none", "unknown", "n/a"}


def clean_question_text(value):
    if isinstance(value, list):
        return " | ".join(
            item for item in (clean_question_text(item) for item in value) if item
        )
    if value is None:
        return ""
    return " ".join(str(value).replace("\u200c", " ").split()).strip()


def compact_question_text(value):
    if isinstance(value, list):
        return " | ".join(
            item for item in (compact_question_text(item) for item in value) if item
        )
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


def question_source_specs(drug):
    """Build the currently valid learning-question definitions for one drug."""
    category = getattr(drug, "category", []) or []
    classification = (
        drug.drug_classification
        or (drug.atc_categories[0] if drug.atc_categories else "")
        or (category[0] if category else "")
        or (drug.atc_subclasses[0] if drug.atc_subclasses else "")
    )
    pregnancy_values = []
    for value in (drug.pregnancy, drug.breastfeeding):
        if value and value not in pregnancy_values:
            pregnancy_values.append(value)
    pregnancy = "\n\n".join(pregnancy_values)
    generic_name = drug.generic_name or drug.name or drug.persian_name
    specs = [
        ("brandGeneric", drug.generic_name, drug.brand_name, drug.drug_classification),
        ("timing", drug.consumption_time_sorted, drug.consumption_time, drug.dosage_form),
        ("indication", drug.indication_answer, drug.indication, drug.drug_classification),
        ("sideEffects", drug.side_effects_answer, drug.side_effects, drug.drug_classification),
        ("classification", classification, classification, drug.atc_codes[0] if drug.atc_codes else ""),
        ("dosageForm", drug.dosage_form, drug.dosage_form, classification),
        ("dosing", drug.dosing_and_administration, drug.dosing_and_administration, classification),
        ("pregnancy", pregnancy, pregnancy, classification),
        ("doseAdjustment", drug.dose_adjustment, drug.dose_adjustment, classification),
    ]
    for question_type, answer, feedback, chip in specs:
        normalized_answer = (
            compact_question_text(answer)
            if question_type == "timing"
            else clean_question_text(answer)
        )
        if (
            not normalized_answer
            or normalized_answer.casefold() in INVALID_QUESTION_VALUES
        ):
            continue
        if question_type == "brandGeneric" and not clean_question_text(drug.brand_name):
            continue
        yield {
            "question_type": question_type,
            "correct_answer": normalized_answer,
            "feedback": clean_question_text(feedback),
            "chip": clean_question_text(chip),
            "subtitle": generic_name,
        }
