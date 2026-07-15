import hashlib
from dataclasses import dataclass

from apps.learning.models import KnowledgeSource, LearningObject, LearningTopic

from .categories import category_for_drug, category_payload_for_drug
from .models import DrugQuestionSource
from .services import signature, split_brand_names


PRODUCT_ID = "pharmexa"
MAX_BRAND_EXTERNAL_ID_SUFFIX_LENGTH = 36


@dataclass(frozen=True)
class LearningSyncResult:
    topics: int = 0
    learning_objects: int = 0
    knowledge_sources: int = 0


def drug_learning_object_external_id(drug) -> str:
    return drug.external_id or f"drug:{drug.id}"


def drug_question_source_external_id_base(source: DrugQuestionSource) -> str:
    return f"drug-question-source:{source.drug.external_id}:{source.question_type}"


def drug_question_source_external_id(source: DrugQuestionSource, brand_name: str | None = None) -> str:
    base = drug_question_source_external_id_base(source)
    if source.question_type != "brandGeneric":
        return base

    variant = brand_name
    if variant is None:
        brand_names = split_brand_names(source.drug.brand_name)
        variant = brand_names[0] if brand_names else brand_drug_name(source.drug)
    variant_signature = bounded_external_id_suffix(variant)
    return f"{base}:{variant_signature}"


def bounded_external_id_suffix(value: str | None) -> str:
    variant_signature = signature(value) or "default"
    if len(variant_signature) <= MAX_BRAND_EXTERNAL_ID_SUFFIX_LENGTH:
        return variant_signature
    digest = hashlib.sha256(variant_signature.encode("utf-8")).hexdigest()[:14]
    prefix_length = MAX_BRAND_EXTERNAL_ID_SUFFIX_LENGTH - len(digest) - 1
    return f"{variant_signature[:prefix_length]}-{digest}"


def generic_drug_name(drug) -> str:
    return (
        drug.generic_name
        or drug.name
        or drug.persian_name
        or drug.brand_name
        or drug.external_id
    )


def brand_drug_name(drug, brand_name: str | None = None) -> str:
    if brand_name:
        return brand_name
    return (
        drug.brand_name
        or drug.name
        or drug.persian_name
        or drug.generic_name
        or drug.external_id
    )


def prompt_for_source(source: DrugQuestionSource, brand_name: str | None = None) -> str:
    drug = source.drug
    if source.question_type == "brandGeneric":
        return f"نام ژنریک داروی تجاری {brand_drug_name(drug, brand_name)} کدام است؟"
    if source.question_type == "timing":
        return f"داروی {generic_drug_name(drug)} چه زمانی نسبت به غذا مصرف می‌شود؟"
    if source.question_type == "indication":
        return f"کاربرد اصلی داروی {generic_drug_name(drug)} کدام است؟"
    if source.question_type == "sideEffects":
        return f"کدام مورد از عوارض جانبی مهم داروی {generic_drug_name(drug)} است؟"
    if source.question_type == "classification":
        return f"داروی {generic_drug_name(drug)} در کدام دسته دارویی قرار می‌گیرد؟"
    if source.question_type == "dosageForm":
        return f"اشکال دارویی {generic_drug_name(drug)} کدام است؟"
    if source.question_type == "dosing":
        return f"دوز و دستور مصرف {generic_drug_name(drug)} کدام است؟"
    if source.question_type == "pregnancy":
        return f"نکته صحیح درباره مصرف {generic_drug_name(drug)} در بارداری یا شیردهی کدام است؟"
    if source.question_type == "doseAdjustment":
        return f"تنظیم دوز {generic_drug_name(drug)} چگونه انجام می‌شود؟"
    return source.prompt


def _brand_variants_for_source(source: DrugQuestionSource) -> list[str]:
    if source.question_type != "brandGeneric":
        return [""]
    variants = split_brand_names(source.drug.brand_name)
    return variants or [brand_drug_name(source.drug)]


def brand_variant_external_ids_for_source(source: DrugQuestionSource) -> list[str]:
    return [
        drug_question_source_external_id(source, brand_name=brand_variant or None)
        for brand_variant in _brand_variants_for_source(source)
    ]


def _brand_external_id_base_from_value(external_id: str) -> str:
    parts = external_id.split(":")
    if len(parts) >= 4 and parts[0] == "drug-question-source" and parts[-2] == "brandGeneric":
        return ":".join(parts[:-1])
    return external_id


def ensure_brand_generic_knowledge_sources(*, target_category_key: str = "") -> int:
    queryset = (
        DrugQuestionSource.objects
        .filter(is_active=True, question_type="brandGeneric")
        .exclude(prompt="")
        .exclude(correct_answer="")
        .select_related("drug", "drug__dataset_document", "topic")
    )

    existing_by_base: dict[str, set[str]] = {}
    existing_queryset = KnowledgeSource.objects.filter(
        product_id=PRODUCT_ID,
        source_type="brandGeneric",
        is_active=True,
    )
    if target_category_key:
        existing_queryset = existing_queryset.filter(metadata__target_category_key=target_category_key)
    for external_id in existing_queryset.values_list("external_id", flat=True):
        base = _brand_external_id_base_from_value(external_id)
        existing_by_base.setdefault(base, set()).add(external_id)

    synced_count = 0
    for source in queryset.iterator():
        if target_category_key and category_for_drug(source.drug).key != target_category_key:
            continue
        base_external_id = drug_question_source_external_id_base(source)
        expected_external_ids = set(brand_variant_external_ids_for_source(source))
        if expected_external_ids == existing_by_base.get(base_external_id, set()):
            continue
        sync_drug_question_sources(source)
        synced_count += 1

    return synced_count


def sync_drug_question_sources(source: DrugQuestionSource) -> list[KnowledgeSource]:
    topic, _ = LearningTopic.objects.update_or_create(
        product_id=PRODUCT_ID,
        key=source.topic.key,
        defaults={
            "label": source.topic.label,
            "detail": source.topic.detail,
            "metadata": {
                "legacy_model": "drugs.DrugTopic",
                "legacy_id": source.topic_id,
            },
            "is_active": True,
        },
    )

    drug = source.drug
    category_payload = category_payload_for_drug(drug)
    display_name = (
        drug.brand_name
        or drug.name
        or drug.persian_name
        or drug.external_id
    )
    learning_object, _ = LearningObject.objects.update_or_create(
        product_id=PRODUCT_ID,
        external_id=drug_learning_object_external_id(drug),
        defaults={
            "display_name": display_name,
            "subtitle": drug.generic_name or drug.drug_classification,
            "topic": topic,
            "metadata": {
                "legacy_model": "drugs.Drug",
                "legacy_id": drug.id,
                "source_file": drug.source_file,
                "source_table": drug.source_table,
                "source_row": drug.source_row,
                "category": drug.category,
                "atc_codes": drug.atc_codes,
                "atc_classes": drug.atc_classes,
                "atc_subclasses": drug.atc_subclasses,
                "atc_categories": drug.atc_categories,
                "consumption_time_sorted": drug.consumption_time_sorted,
                "extra_attributes": drug.extra_attributes,
                "domain": "pharmacology",
                **category_payload,
            },
            "is_active": True,
        },
    )

    synced_sources = []
    active_external_ids = []

    for brand_variant in _brand_variants_for_source(source):
        external_id = drug_question_source_external_id(
            source,
            brand_name=brand_variant or None,
        )
        active_external_ids.append(external_id)
        knowledge_source, _ = KnowledgeSource.objects.update_or_create(
            product_id=PRODUCT_ID,
            external_id=external_id,
            defaults={
                "learning_object": learning_object,
                "topic": topic,
                "source_type": source.question_type,
                "prompt": prompt_for_source(source, brand_name=brand_variant or None),
                "correct_answer": source.correct_answer,
                "explanation": source.feedback,
                "metadata": {
                    "legacy_model": "drugs.DrugQuestionSource",
                    "legacy_id": source.id,
                    "subtitle": source.subtitle,
                    "chip": source.chip,
                    "brand_name_variant": brand_variant,
                    "dataset_schema_version": (
                        drug.dataset_document.schema_version
                        if drug.dataset_document_id
                        else ""
                    ),
                    **category_payload,
                },
                "is_active": source.is_active,
            },
        )
        synced_sources.append(knowledge_source)

    KnowledgeSource.objects.filter(
        product_id=PRODUCT_ID,
        external_id__startswith=drug_question_source_external_id_base(source),
    ).exclude(external_id__in=active_external_ids).update(is_active=False)

    return synced_sources


def sync_drug_question_source(source: DrugQuestionSource) -> KnowledgeSource:
    return sync_drug_question_sources(source)[0]


def sync_all_drug_question_sources() -> LearningSyncResult:
    topic_ids = set()
    drug_ids = set()
    knowledge_source_count = 0

    queryset = DrugQuestionSource.objects.select_related(
        "drug",
        "drug__dataset_document",
        "topic",
    ).all()
    for source in queryset.iterator():
        synced_sources = sync_drug_question_sources(source)
        topic_ids.add(source.topic_id)
        drug_ids.add(source.drug_id)
        knowledge_source_count += len(synced_sources)

    return LearningSyncResult(
        topics=len(topic_ids),
        learning_objects=len(drug_ids),
        knowledge_sources=knowledge_source_count,
    )
