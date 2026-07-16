import hashlib
from dataclasses import dataclass
from typing import Callable

from apps.learning.models import KnowledgeSource, LearningObject, LearningTopic

from .categories import category_for_drug, category_payload_for_drug
from .models import Drug, DrugQuestionSource, DrugTopic
from .question_sources import question_source_specs
from .services import ensure_topics, signature, split_brand_names


PRODUCT_ID = "pharmexa"
MAX_BRAND_EXTERNAL_ID_SUFFIX_LENGTH = 36


@dataclass(frozen=True)
class LearningSyncResult:
    topics: int = 0
    learning_objects: int = 0
    knowledge_sources: int = 0
    processed_sources: int = 0
    updated_sources: int = 0


@dataclass(frozen=True)
class DrugLearningSyncResult:
    question_sources: int = 0
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


def _topic_defaults(source: DrugQuestionSource) -> dict:
    return {
        "label": source.topic.label,
        "detail": source.topic.detail,
        "metadata": {
            "legacy_model": "drugs.DrugTopic",
            "legacy_id": source.topic_id,
        },
        "is_active": True,
    }


def _learning_object_defaults(source: DrugQuestionSource) -> dict:
    drug = source.drug
    category_payload = category_payload_for_drug(drug)
    return {
        "display_name": (
            drug.brand_name
            or drug.name
            or drug.persian_name
            or drug.external_id
        ),
        "subtitle": drug.generic_name or drug.drug_classification,
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
    }


def _knowledge_source_defaults(
    source: DrugQuestionSource,
    *,
    learning_object: LearningObject | None = None,
    topic: LearningTopic | None = None,
    brand_variant: str = "",
) -> dict:
    drug = source.drug
    category_payload = category_payload_for_drug(drug)
    defaults = {
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
    }
    if learning_object is not None:
        defaults["learning_object"] = learning_object
    if topic is not None:
        defaults["topic"] = topic
    return defaults


def _expected_knowledge_sources(source: DrugQuestionSource) -> dict[str, dict]:
    return {
        drug_question_source_external_id(source, brand_name=brand_variant or None): _knowledge_source_defaults(
            source,
            brand_variant=brand_variant,
        )
        for brand_variant in _brand_variants_for_source(source)
    }


def _learning_topic_matches(source: DrugQuestionSource, knowledge_source: KnowledgeSource) -> bool:
    expected = _topic_defaults(source)
    topic = knowledge_source.topic
    return (
        topic.product_id == PRODUCT_ID
        and topic.key == source.topic.key
        and topic.label == expected["label"]
        and topic.detail == expected["detail"]
        and topic.metadata == expected["metadata"]
        and topic.is_active == expected["is_active"]
    )


def _learning_object_matches(source: DrugQuestionSource, knowledge_source: KnowledgeSource) -> bool:
    expected = _learning_object_defaults(source)
    learning_object = knowledge_source.learning_object
    return (
        learning_object.product_id == PRODUCT_ID
        and learning_object.external_id == drug_learning_object_external_id(source.drug)
        and learning_object.display_name == expected["display_name"]
        and learning_object.subtitle == expected["subtitle"]
        and learning_object.metadata == expected["metadata"]
        and learning_object.is_active == expected["is_active"]
    )


def _knowledge_source_matches(source: DrugQuestionSource, knowledge_source: KnowledgeSource, expected: dict) -> bool:
    return (
        knowledge_source.source_type == expected["source_type"]
        and knowledge_source.prompt == expected["prompt"]
        and knowledge_source.correct_answer == expected["correct_answer"]
        and knowledge_source.explanation == expected["explanation"]
        and knowledge_source.metadata == expected["metadata"]
        and knowledge_source.is_active == expected["is_active"]
        and _learning_topic_matches(source, knowledge_source)
        and _learning_object_matches(source, knowledge_source)
    )


def drug_question_source_needs_sync(
    source: DrugQuestionSource,
    existing_by_base: dict[str, dict[str, KnowledgeSource]],
) -> bool:
    expected_sources = _expected_knowledge_sources(source)
    base_external_id = drug_question_source_external_id_base(source)
    existing_sources = existing_by_base.get(base_external_id, {})
    if set(existing_sources) != set(expected_sources):
        return True
    return any(
        not _knowledge_source_matches(source, existing_sources[external_id], expected)
        for external_id, expected in expected_sources.items()
    )


def sync_drug_question_sources(source: DrugQuestionSource) -> list[KnowledgeSource]:
    topic, _ = LearningTopic.objects.update_or_create(
        product_id=PRODUCT_ID,
        key=source.topic.key,
        defaults=_topic_defaults(source),
    )

    learning_object, _ = LearningObject.objects.update_or_create(
        product_id=PRODUCT_ID,
        external_id=drug_learning_object_external_id(source.drug),
        defaults=_learning_object_defaults(source),
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
            defaults=_knowledge_source_defaults(
                source,
                learning_object=learning_object,
                topic=topic,
                brand_variant=brand_variant,
            ),
        )
        synced_sources.append(knowledge_source)

    KnowledgeSource.objects.filter(
        product_id=PRODUCT_ID,
        external_id__startswith=drug_question_source_external_id_base(source),
    ).exclude(external_id__in=active_external_ids).update(is_active=False)

    return synced_sources


def sync_drug_question_source(source: DrugQuestionSource) -> KnowledgeSource:
    return sync_drug_question_sources(source)[0]


def regenerate_and_sync_drug_question_sources(
    drug,
    *,
    topics: dict[str, DrugTopic] | None = None,
) -> DrugLearningSyncResult:
    """Regenerate the question definitions and learning sources for one drug."""
    if topics is None:
        ensure_topics()
        topics = {topic.key: topic for topic in DrugTopic.objects.all()}

    existing_sources = list(
        DrugQuestionSource.objects.filter(drug=drug)
        .select_related("topic")
        .order_by("id")
    )
    sources_by_type: dict[str, list[DrugQuestionSource]] = {}
    for source in existing_sources:
        sources_by_type.setdefault(source.question_type, []).append(source)

    selected_sources = []
    for spec in question_source_specs(drug):
        candidates = sources_by_type.get(spec["question_type"], [])
        source = next(
            (
                candidate
                for candidate in candidates
                if candidate.correct_answer == spec["correct_answer"]
            ),
            candidates[0] if candidates else None,
        )
        if source is None:
            source = DrugQuestionSource(
                drug=drug,
                topic=topics[spec["question_type"]],
                question_type=spec["question_type"],
            )

        source.topic = topics[spec["question_type"]]
        source.question_type = spec["question_type"]
        source.correct_answer = spec["correct_answer"]
        source.feedback = spec["feedback"]
        source.chip = spec["chip"]
        source.subtitle = spec["subtitle"]
        source.is_active = True
        source.prompt = prompt_for_source(source)
        source.save()
        selected_sources.append(source)

    selected_source_ids = {source.id for source in selected_sources}
    selected_question_types = {source.question_type for source in selected_sources}
    for source in existing_sources:
        if source.id in selected_source_ids or not source.is_active:
            continue
        source.is_active = False
        source.save(update_fields=["is_active"])
        KnowledgeSource.objects.filter(
            product_id=PRODUCT_ID,
            external_id__startswith=drug_question_source_external_id_base(source),
        ).update(is_active=False)

    for source in existing_sources:
        if source.question_type in selected_question_types:
            continue
        KnowledgeSource.objects.filter(
            product_id=PRODUCT_ID,
            external_id__startswith=drug_question_source_external_id_base(source),
        ).update(is_active=False)

    knowledge_source_count = sum(
        len(sync_drug_question_sources(source))
        for source in selected_sources
    )
    return DrugLearningSyncResult(
        question_sources=len(selected_sources),
        knowledge_sources=knowledge_source_count,
    )


def regenerate_and_sync_all_drug_question_sources(
    *,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> LearningSyncResult:
    """Rebuild question and learning sources for every drug. Use only when requested."""
    ensure_topics()
    topics = {topic.key: topic for topic in DrugTopic.objects.all()}
    total_drugs = Drug.objects.count()
    processed_drugs = 0
    question_source_count = 0
    knowledge_source_count = 0

    for drug in Drug.objects.iterator(chunk_size=100):
        processed_drugs += 1
        result = regenerate_and_sync_drug_question_sources(drug, topics=topics)
        question_source_count += result.question_sources
        knowledge_source_count += result.knowledge_sources
        if progress_callback:
            progress_callback(
                processed_drugs,
                total_drugs,
                question_source_count,
            )

    return LearningSyncResult(
        topics=LearningTopic.objects.filter(product_id=PRODUCT_ID, is_active=True).count(),
        learning_objects=LearningObject.objects.filter(product_id=PRODUCT_ID, is_active=True).count(),
        knowledge_sources=KnowledgeSource.objects.filter(product_id=PRODUCT_ID, is_active=True).count(),
        processed_sources=processed_drugs,
        updated_sources=question_source_count,
    )


def sync_all_drug_question_sources(
    *,
    drug_id: int | None = None,
    progress_callback: Callable[[int, int, int], None] | None = None,
) -> LearningSyncResult:
    queryset = DrugQuestionSource.objects.select_related(
        "drug",
        "drug__dataset_document",
        "topic",
    )
    if drug_id is not None:
        queryset = queryset.filter(drug_id=drug_id)

    total_sources = queryset.count()
    existing_by_base: dict[str, dict[str, KnowledgeSource]] = {}
    existing_queryset = (
        KnowledgeSource.objects.filter(
            product_id=PRODUCT_ID,
            external_id__startswith="drug-question-source:",
        )
        .select_related("learning_object", "topic")
    )
    for knowledge_source in existing_queryset:
        base_external_id = _brand_external_id_base_from_value(knowledge_source.external_id)
        existing_by_base.setdefault(base_external_id, {})[knowledge_source.external_id] = knowledge_source

    processed_sources = 0
    updated_sources = 0
    for source in queryset.iterator(chunk_size=200):
        processed_sources += 1
        if drug_question_source_needs_sync(source, existing_by_base):
            synced_sources = sync_drug_question_sources(source)
            updated_sources += 1
            base_external_id = drug_question_source_external_id_base(source)
            existing_by_base[base_external_id] = {
                knowledge_source.external_id: knowledge_source
                for knowledge_source in synced_sources
            }
        if progress_callback:
            progress_callback(processed_sources, total_sources, updated_sources)

    return LearningSyncResult(
        topics=LearningTopic.objects.filter(product_id=PRODUCT_ID, is_active=True).count(),
        learning_objects=LearningObject.objects.filter(product_id=PRODUCT_ID, is_active=True).count(),
        knowledge_sources=KnowledgeSource.objects.filter(product_id=PRODUCT_ID, is_active=True).count(),
        processed_sources=processed_sources,
        updated_sources=updated_sources,
    )
