TIMING_CHOICES = ["با غذا", "بدون غذا", "فرقی نمی‌کند"]

QUESTION_TYPE_LABELS = {
    "timing": "زمان مصرف",
    "brandGeneric": "نام تجاری / ژنریک",
    "indication": "کاربرد",
    "sideEffects": "عوارض جانبی",
    "classification": "دسته‌بندی",
    "dosageForm": "اشکال دارویی",
    "dosing": "دوزینگ",
    "pregnancy": "بارداری و شیردهی",
    "doseAdjustment": "تنظیم دوز",
}


def choices_for_source(source_type, correct_answer, wrong_answers, correct_answer_position=None):
    if source_type == "timing" and canonical_timing_answer(correct_answer) in TIMING_CHOICES:
        return place_correct_answer(
            TIMING_CHOICES,
            canonical_timing_answer(correct_answer),
            correct_answer_position,
        )
    return unique_choices(correct_answer, wrong_answers, correct_answer_position=correct_answer_position)


def option_count_for_source(source_type, correct_answer, total=4):
    if source_type == "timing" and canonical_timing_answer(correct_answer) in TIMING_CHOICES:
        return len(TIMING_CHOICES)
    return total


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


def place_correct_answer(choices, correct_answer, correct_answer_position=None):
    wrong_choices = []
    for choice in choices:
        if not choice:
            continue
        if choice == correct_answer:
            continue
        if choice in wrong_choices:
            continue
        wrong_choices.append(choice)
    position = bounded_correct_answer_position(correct_answer_position, len(wrong_choices) + 1)
    return wrong_choices[:position] + [correct_answer] + wrong_choices[position:]


def bounded_correct_answer_position(position, option_count):
    if option_count <= 1:
        return 0
    if position is None:
        return option_count - 1
    return max(0, min(option_count - 1, int(position)))


def unique_choices(correct_answer, wrong_answers, total=4, correct_answer_position=None):
    unique_wrong = []
    for answer in wrong_answers:
        if not answer:
            continue
        if answer == correct_answer:
            continue
        if answer in unique_wrong:
            continue
        unique_wrong.append(answer)
    return place_correct_answer(
        unique_wrong[: total - 1],
        correct_answer,
        correct_answer_position,
    )


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
        return ""
    if question_type == "brandGeneric":
        return "نام درست را انتخاب کن."
    if question_type == "indication":
        return "کاربرد اصلی را انتخاب کن."
    if question_type == "sideEffects":
        return "عوارض مرتبط را انتخاب کن."
    if question_type == "classification":
        return "دسته دارویی درست را انتخاب کن."
    if question_type == "dosageForm":
        return "شکل دارویی درست را انتخاب کن."
    if question_type == "dosing":
        return "دستور مصرف درست را انتخاب کن."
    if question_type == "pregnancy":
        return "گزینه صحیح بارداری یا شیردهی را انتخاب کن."
    if question_type == "doseAdjustment":
        return "گزینه صحیح تنظیم دوز را انتخاب کن."
    return "گزینه درست را انتخاب کن."
