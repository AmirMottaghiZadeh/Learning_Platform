import random
from .categories import TARGET_CATEGORIES, TARGET_CATEGORY_BY_KEY, category_for_drug
from .models import DrugQuestionSource, DrugTopic

INVALID_ANSWERS = {"", "-", "ندارد", "نامشخص"}

TOPIC_DEFS = {
    "timing": {"label": "با غذا / بی غذا", "detail": "زمان مصرف دارو نسبت به غذا"},
    "brandGeneric": {"label": "نام تجاری / ژنریک", "detail": "تطبیق Brand name با Generic name"},
    "indication": {"label": "اندیکاسیون", "detail": "کاربرد یا مورد مصرف دارو"},
    "sideEffects": {"label": "عوارض جانبی", "detail": "Side effects مهم دارو"},
    "classification": {"label": "دسته‌بندی", "detail": "کلاس و رده ATC دارو"},
    "dosageForm": {"label": "اشکال دارویی", "detail": "فرم‌ها و قدرت‌های دارویی"},
    "dosing": {"label": "دوزینگ", "detail": "دوز و دستور مصرف"},
    "pregnancy": {"label": "بارداری و شیردهی", "detail": "اطلاعات مصرف در بارداری و شیردهی"},
    "doseAdjustment": {"label": "تنظیم دوز", "detail": "تنظیم دوز کلیوی، کبدی و بالینی"},
}

def ensure_topics():
    for key, item in TOPIC_DEFS.items():
        DrugTopic.objects.update_or_create(key=key, defaults=item)

def normalize_option(value):
    return " ".join(str(value or "").split()).strip()

def signature(value):
    text = normalize_option(value).replace("ي", "ی").replace("ى", "ی").replace("ك", "ک").lower()
    return "".join(ch for ch in text if ch.isalnum() or "آ" <= ch <= "ی")

def option_pool(topic_key):
    seen, options = set(), []
    qs = DrugQuestionSource.objects.filter(question_type=topic_key, is_active=True).values_list("correct_answer", flat=True)
    for answer in qs:
        sig = signature(answer)
        if not sig or normalize_option(answer) in INVALID_ANSWERS or sig in seen:
            continue
        seen.add(sig)
        options.append(answer)
    return options

def build_options(question_source):
    correct = question_source.correct_answer
    correct_sig = signature(correct)
    candidates = option_pool(question_source.question_type)
    random.shuffle(candidates)
    distractors = []
    seen = {correct_sig}
    for option in candidates:
        sig = signature(option)
        if not sig or sig in seen:
            continue
        seen.add(sig)
        distractors.append(option)
        if len(distractors) == 3:
            break
    options = [correct] + distractors
    random.shuffle(options)
    return options


def generic_drug_signature(drug):
    value = (
        drug.generic_name
        or drug.name
        or drug.persian_name
    )
    return signature(value)


def list_target_categories(product_id="k_game", source_type=""):
    if product_id != "k_game":
        return []

    sources = (
        DrugQuestionSource.objects
        .filter(is_active=True)
        .select_related("drug")
    )
    if source_type:
        sources = sources.filter(question_type=source_type)

    generic_by_category = {}
    for source in sources:
        key = category_for_drug(source.drug).key
        generic_sig = generic_drug_signature(source.drug)
        if not generic_sig:
            continue
        generic_by_category.setdefault(key, set()).add(generic_sig)

    counts = {
        key: len(generic_signatures)
        for key, generic_signatures in generic_by_category.items()
    }

    categories = []
    for category in TARGET_CATEGORIES:
        count = counts.get(category.key, 0)
        if count:
            categories.append(
                {
                    "key": category.key,
                    "label": TARGET_CATEGORY_BY_KEY[category.key].label,
                    "count": count,
                }
            )
    return categories
