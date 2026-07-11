from dataclasses import dataclass

from apps.learning.models import KnowledgeSource, LearningObject, LearningTopic

from .categories import category_payload_for_drug
from .models import DrugQuestionSource


PRODUCT_ID = "k_game"


@dataclass(frozen=True)
class LearningSyncResult:
    topics: int = 0
    learning_objects: int = 0
    knowledge_sources: int = 0


def drug_learning_object_external_id(drug) -> str:
    return drug.external_id or f"drug:{drug.id}"


def drug_question_source_external_id(source: DrugQuestionSource) -> str:
    return f"drug-question-source:{source.drug.external_id}:{source.question_type}"


def generic_drug_name(drug) -> str:
    return (
        drug.generic_name
        or drug.name
        or drug.persian_name
        or drug.brand_name
        or drug.external_id
    )


def brand_drug_name(drug) -> str:
    return (
        drug.brand_name
        or drug.name
        or drug.persian_name
        or drug.generic_name
        or drug.external_id
    )


def prompt_for_source(source: DrugQuestionSource) -> str:
    drug = source.drug
    if source.question_type == "brandGeneric":
        return f"نام ژنریک داروی تجاری {brand_drug_name(drug)} کدام است؟"
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


def sync_drug_question_source(source: DrugQuestionSource) -> KnowledgeSource:
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
                "atc_codes": drug.atc_codes,
                "extra_attributes": drug.extra_attributes,
                "domain": "pharmacology",
                **category_payload,
            },
            "is_active": True,
        },
    )

    knowledge_source, _ = KnowledgeSource.objects.update_or_create(
        product_id=PRODUCT_ID,
        external_id=drug_question_source_external_id(source),
        defaults={
            "learning_object": learning_object,
            "topic": topic,
            "source_type": source.question_type,
            "prompt": prompt_for_source(source),
            "correct_answer": source.correct_answer,
            "explanation": source.feedback,
            "metadata": {
                "legacy_model": "drugs.DrugQuestionSource",
                "legacy_id": source.id,
                "subtitle": source.subtitle,
                "chip": source.chip,
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
    return knowledge_source


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
        sync_drug_question_source(source)
        topic_ids.add(source.topic_id)
        drug_ids.add(source.drug_id)
        knowledge_source_count += 1

    return LearningSyncResult(
        topics=len(topic_ids),
        learning_objects=len(drug_ids),
        knowledge_sources=knowledge_source_count,
    )
