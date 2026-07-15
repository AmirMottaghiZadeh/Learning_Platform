import random
import re

from apps.learning.models import KnowledgeSource

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


def is_valid_correct_answer(value):
    normalized = normalize_option(value)
    return normalized not in INVALID_ANSWERS and bool(signature(normalized))


def split_brand_names(value):
    normalized = str(value or "").replace("\u200c", " ")
    parts = re.split(r"[\s/\\+،,؛;|\n\r\t]+", normalized)
    brands = []
    seen = set()
    for part in parts:
        item = normalize_option(part)
        item_signature = signature(item)
        if not item or not item_signature or item_signature in seen:
            continue
        seen.add(item_signature)
        brands.append(item)
    return brands

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


def list_target_categories(product_id="pharmexa", source_type=""):
    if product_id != "pharmexa":
        return []

    if source_type == "brandGeneric":
        from .learning_sync import ensure_brand_generic_knowledge_sources

        ensure_brand_generic_knowledge_sources()

    synced_sources = (
        KnowledgeSource.objects
        .filter(product_id=product_id, is_active=True)
        .exclude(prompt="")
        .exclude(correct_answer="")
    )
    if source_type:
        synced_sources = synced_sources.filter(source_type=source_type)
    if synced_sources.exists():
        counts = {}
        for source in synced_sources.iterator():
            if not is_valid_correct_answer(source.correct_answer):
                continue
            key = source.metadata.get("target_category_key", "")
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1

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

    sources = (
        DrugQuestionSource.objects
        .filter(is_active=True)
        .select_related("drug")
    )
    if source_type:
        sources = sources.filter(question_type=source_type)

    counts = {}
    for source in sources:
        key = category_for_drug(source.drug).key
        if source.question_type == "brandGeneric":
            brand_count = len(split_brand_names(source.drug.brand_name))
            if not brand_count or not generic_drug_signature(source.drug) or not is_valid_correct_answer(source.correct_answer):
                continue
            counts[key] = counts.get(key, 0) + brand_count
            continue
        if not is_valid_correct_answer(source.correct_answer):
            continue
        counts[key] = counts.get(key, 0) + 1

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
