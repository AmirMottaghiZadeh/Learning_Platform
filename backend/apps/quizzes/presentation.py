TIMING_CHOICES = ["با غذا", "بدون غذا", "فرقی نمی‌کند"]

QUESTION_TYPE_LABELS = {
    "timing": "زمان مصرف",
    "brandGeneric": "نام تجاری / ژنریک",
    "indication": "کاربرد",
    "sideEffects": "عوارض جانبی",
}


def choices_for_source(source_type, correct_answer, wrong_answers):
    if source_type == "timing" and canonical_timing_answer(correct_answer) in TIMING_CHOICES:
        return TIMING_CHOICES.copy()
    return unique_choices(correct_answer, wrong_answers)


def _answer_signature(value):
    text = str(value or "").strip()
    text = text.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
    text = text.replace("\u200c", "")
    return "".join(ch for ch in text.lower() if ch.isalnum() or "آ" <= ch <= "ی")


def canonical_timing_answer(value):
    signature = _answer_signature(value)
    if not signature:
        return ""
    if "بدون" in signature:
        return "بدون غذا"
    if "فرقی" in signature or "فرقي" in signature or "فرقینمیکند" in signature or "فرقیندارد" in signature:
        return "فرقی نمی‌کند"
    if "باغذا" in signature:
        return "با غذا"
    return str(value or "").strip()


def answers_match(*, question_type, selected_answer, correct_answer):
    if question_type == "timing":
        return canonical_timing_answer(selected_answer) == canonical_timing_answer(correct_answer)
    return str(selected_answer or "").strip() == str(correct_answer or "").strip()


def unique_choices(correct_answer, wrong_answers, total=4):
    unique_wrong = []
    for answer in wrong_answers:
        if not answer:
            continue
        if answer == correct_answer:
            continue
        if answer in unique_wrong:
            continue
        unique_wrong.append(answer)
    return unique_wrong[: total - 1] + [correct_answer]


def interaction_type_for(question_type, options):
    if question_type == "timing":
        return "binary" if len(options) <= 2 else "segmented"
    return "multiple_choice"


def option_layout_for(question_type):
    if question_type == "timing":
        return "compact"
    return "list"


def chip_for(question_type, metadata):
    if question_type == "timing":
        return QUESTION_TYPE_LABELS["timing"]
    return metadata.get("chip") or QUESTION_TYPE_LABELS.get(question_type, question_type)


def instruction_for(question_type):
    if question_type == "timing":
        return "زمان مصرف مناسب را انتخاب کن."
    if question_type == "brandGeneric":
        return "نام درست را انتخاب کن."
    if question_type == "indication":
        return "کاربرد اصلی را انتخاب کن."
    if question_type == "sideEffects":
        return "عوارض مرتبط را انتخاب کن."
    return "گزینه درست را انتخاب کن."
