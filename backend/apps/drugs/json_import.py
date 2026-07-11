import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.flashcards.models import FlashcardState
from apps.games.models import GameQuestion, Mistake
from apps.learning.models import KnowledgeSource, LearningObject

from .learning_sync import prompt_for_source, sync_all_drug_question_sources
from .models import Drug, DrugDatasetDocument, DrugQuestionSource, DrugTopic
from .services import ensure_topics


SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
REPORT_FILE_NAME = "drug_enrichment_report.json"
INVALID_VALUES = {"", "-", "ندارد", "نامشخص", "none", "unknown", "n/a"}

FIELD_ALIASES = {
    "generic_name": ("English Generic Name",),
    "persian_name": ("Persian Generic Name",),
    "source_name": ("نام دارو", "کورتیکواستروئید"),
    "brand_name": ("نام تجاری", "اسم تجاری"),
    "dosage_form": ("اشکال دارویی",),
    "dosing": (
        "دوزینگ و دستور مصرف",
        "دوزینگ ،اندیکاسیون و دستور مصرف",
        "اندیکاسیون و دوزینگ",
        "دوز و اندیکاسیون",
    ),
    "indication": (
        "اندیکاسیون",
        "دوزینگ ،اندیکاسیون و دستور مصرف",
        "اندیکاسیون و دوزینگ",
        "دوز و اندیکاسیون",
    ),
    "food_relation": ("رابطه با غذا", "فاصله با غذا"),
    "pregnancy": ("بارداری", "بارداری و شیردهی"),
    "breastfeeding": ("شیردهی", "بارداری و شیردهی"),
    "dose_adjustment": ("تنظیم دوز", "تنطیم دوز"),
    "side_effects": ("عوارض",),
    "clinical_notes": ("سایر نکات", "نکات", "توصیه و نکات"),
    "source_classification": ("دسته بندی", "دسته دارویی", "column_1"),
    "atc_code": ("atc_code",),
    "atc_class": ("class",),
    "atc_subclass": ("sub_class",),
    "atc_category": ("category",),
}

KNOWN_HEADERS = {
    "_source_row",
    *(header for aliases in FIELD_ALIASES.values() for header in aliases),
}

SOURCE_TOPICS = {
    "cns-1.docx": "cns-1",
    "cns-2.docx": "cns-2",
    "cardiovascular + dyslipidemia.docx": "cardiovascular + dyslipidemia",
    "endo.docx": "endo",
    "gi.docx": "gi",
    "respiratory.docx": "respiratory",
    "خلاصه عفونی 2.docx": "infection",
    "مسکن جدول.docx": "pain_inflammation",
}


@dataclass
class ParsedDrug:
    external_id: str
    values: dict


@dataclass
class ParsedDocument:
    values: dict
    drugs: list[ParsedDrug] = field(default_factory=list)


@dataclass
class ImportResult:
    documents: int = 0
    drugs: int = 0
    question_sources: int = 0
    skipped_rows: int = 0


def clean_text(value):
    if isinstance(value, list):
        return " | ".join(item for item in (clean_text(item) for item in value) if item)
    if value is None:
        return ""
    return " ".join(str(value).replace("\u200c", " ").split()).strip()


def clean_list(value):
    values = value if isinstance(value, list) else [value]
    cleaned = []
    for item in values:
        text = clean_text(item)
        if not text or text.casefold() in INVALID_VALUES or text in cleaned:
            continue
        cleaned.append(text)
    return cleaned


def first_value(row, field_name):
    for header in FIELD_ALIASES[field_name]:
        value = clean_text(row.get(header))
        if value and value.casefold() not in INVALID_VALUES:
            return value
    return ""


def combined_values(row, field_name):
    values = []
    for header in FIELD_ALIASES[field_name]:
        value = clean_text(row.get(header))
        if not value or value.casefold() in INVALID_VALUES or value in values:
            continue
        values.append(value)
    return "\n\n".join(values)


def classification_value(row):
    for header in FIELD_ALIASES["source_classification"]:
        value = clean_text(row.get(header))
        if not value or value.casefold() in INVALID_VALUES:
            continue
        if header == "column_1" and value.replace(".", "").isdigit():
            continue
        return value
    return ""


def canonical_timing(value):
    text = clean_text(value)
    normalized = text.replace("ي", "ی").replace("ك", "ک").replace(" ", "").casefold()
    if not normalized or normalized in INVALID_VALUES:
        return ""
    if any(marker in normalized for marker in ("معدهخالی", "ناشتا", "قبلغذا", "بدونغذا")):
        return "بدون غذا"
    if any(marker in normalized for marker in ("فرقین", "تفاوتین", "هرزمان")):
        return "فرقی نمی‌کند"
    if any(marker in normalized for marker in ("باغذا", "همراهغذا", "بعدازغذا")):
        return "با غذا"
    return text


def stable_external_id(schema_version, source_sha256, table_index, source_row):
    seed = f"{schema_version}:{source_sha256}:{table_index}:{source_row}"
    return f"json-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:32]}"


def load_skipped_rows(directory):
    report_path = directory / REPORT_FILE_NAME
    if not report_path.exists():
        return set()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    skipped = set()
    for file_name, details in report.get("files", {}).items():
        for issue in details.get("issues", []):
            skipped.add((file_name, issue.get("table_index"), issue.get("source_row")))
    return skipped


def parse_json_directory(directory):
    directory = Path(directory).expanduser().resolve()
    if not directory.is_dir():
        raise ValidationError(f"JSON directory does not exist: {directory}")

    skipped_rows = load_skipped_rows(directory)
    documents = []
    seen_external_ids = set()
    json_paths = sorted(path for path in directory.glob("*.json") if path.name != REPORT_FILE_NAME)
    if not json_paths:
        raise ValidationError(f"No dataset JSON files found in {directory}")

    for path in json_paths:
        payload = json.loads(path.read_text(encoding="utf-8"))
        schema_version = clean_text(payload.get("schema_version"))
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise ValidationError(f"{path.name}: unsupported schema_version {schema_version!r}")

        source = payload.get("source")
        extraction = payload.get("extraction")
        content = payload.get("content")
        if not isinstance(source, dict) or not isinstance(extraction, dict) or not isinstance(content, dict):
            raise ValidationError(f"{path.name}: source, extraction and content must be objects")

        source_file = clean_text(source.get("file_name"))
        source_sha256 = clean_text(source.get("sha256"))
        if not source_file or len(source_sha256) != 64:
            raise ValidationError(f"{path.name}: source file name and SHA-256 are required")

        document = ParsedDocument(
            values={
                "schema_version": schema_version,
                "source_file": source_file,
                "source_path": clean_text(source.get("path")),
                "source_format": clean_text(source.get("format")),
                "source_size_bytes": source.get("size_bytes") or 0,
                "source_sha256": source_sha256,
                "source_metadata": source.get("metadata") or {},
                "extraction_metadata": extraction,
                "warnings": payload.get("warnings") or [],
                "enrichment_metadata": payload.get("enrichment") or {},
            }
        )

        for table in content.get("tables") or []:
            table_index = int(table.get("index") or 0)
            for row in table.get("records") or []:
                source_row = int(row.get("_source_row") or 0)
                if (path.name, table_index, source_row) in skipped_rows:
                    continue

                generic_name = first_value(row, "generic_name")
                persian_name = first_value(row, "persian_name")
                source_name = first_value(row, "source_name")
                atc_codes = clean_list(row.get("atc_code"))
                if not generic_name and not persian_name and not atc_codes:
                    raise ValidationError(
                        f"{path.name}: table {table_index}, row {source_row} has no validated drug identity"
                    )

                external_id = stable_external_id(
                    schema_version,
                    source_sha256,
                    table_index,
                    source_row,
                )
                if external_id in seen_external_ids:
                    raise ValidationError(f"Duplicate stable drug ID: {external_id}")
                seen_external_ids.add(external_id)

                source_topic = SOURCE_TOPICS.get(source_file.casefold(), Path(source_file).stem.casefold())
                source_classification = classification_value(row)
                atc_categories = clean_list(row.get("category"))
                drug_classification = source_classification or (atc_categories[0] if atc_categories else "")
                food_relation = combined_values(row, "food_relation")
                extra_attributes = {
                    key: value
                    for key, value in row.items()
                    if key not in KNOWN_HEADERS and value not in (None, "", [], {})
                }

                document.drugs.append(
                    ParsedDrug(
                        external_id=external_id,
                        values={
                            "name": generic_name or source_name,
                            "persian_name": persian_name,
                            "brand_name": combined_values(row, "brand_name"),
                            "generic_name": generic_name or source_name,
                            "dosage_form": combined_values(row, "dosage_form"),
                            "drug_classification": drug_classification,
                            "consumption_time": food_relation,
                            "consumption_time_sorted": canonical_timing(food_relation),
                            "indication": combined_values(row, "indication"),
                            "indication_answer": combined_values(row, "indication"),
                            "side_effects": combined_values(row, "side_effects"),
                            "side_effects_answer": combined_values(row, "side_effects"),
                            "dosing_and_administration": combined_values(row, "dosing"),
                            "pregnancy": combined_values(row, "pregnancy"),
                            "breastfeeding": combined_values(row, "breastfeeding"),
                            "dose_adjustment": combined_values(row, "dose_adjustment"),
                            "clinical_notes": combined_values(row, "clinical_notes"),
                            "atc_codes": atc_codes,
                            "atc_classes": clean_list(row.get("class")),
                            "atc_subclasses": clean_list(row.get("sub_class")),
                            "atc_categories": atc_categories,
                            "source_topic": source_topic,
                            "source_file": source_file,
                            "source_table": table_index,
                            "source_row": source_row,
                            "extra_attributes": extra_attributes,
                            "raw": row,
                        },
                    )
                )
        documents.append(document)

    return documents, len(skipped_rows)


def question_source_specs(drug):
    classification = (
        drug.drug_classification
        or (drug.atc_categories[0] if drug.atc_categories else "")
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
        if not clean_text(answer) or clean_text(answer).casefold() in INVALID_VALUES:
            continue
        if question_type == "brandGeneric" and not clean_text(drug.brand_name):
            continue
        yield {
            "question_type": question_type,
            "correct_answer": clean_text(answer),
            "feedback": clean_text(feedback),
            "chip": clean_text(chip),
            "subtitle": generic_name,
        }


@transaction.atomic
def replace_drug_metadata_from_json(directory):
    documents, skipped_rows = parse_json_directory(directory)

    GameQuestion.objects.filter(source__isnull=False).update(source=None)
    Mistake.objects.filter(source__isnull=False).update(source=None)
    FlashcardState.objects.filter(source__isnull=False).update(source=None)
    DrugQuestionSource.objects.all().delete()
    Drug.objects.all().delete()
    DrugDatasetDocument.objects.all().delete()
    KnowledgeSource.objects.filter(product_id="k_game").update(is_active=False)
    LearningObject.objects.filter(product_id="k_game").update(is_active=False)

    ensure_topics()
    topics = {topic.key: topic for topic in DrugTopic.objects.all()}
    result = ImportResult(documents=len(documents), skipped_rows=skipped_rows)

    for parsed_document in documents:
        document = DrugDatasetDocument.objects.create(**parsed_document.values)
        for parsed_drug in parsed_document.drugs:
            drug = Drug.objects.create(
                dataset_document=document,
                external_id=parsed_drug.external_id,
                **parsed_drug.values,
            )
            result.drugs += 1
            for spec in question_source_specs(drug):
                topic = topics[spec["question_type"]]
                source = DrugQuestionSource.objects.create(
                    topic=topic,
                    drug=drug,
                    prompt="",
                    **spec,
                )
                source.prompt = prompt_for_source(source)
                source.save(update_fields=["prompt"])
                result.question_sources += 1

    sync_all_drug_question_sources()
    KnowledgeSource.objects.filter(
        product_id="k_game",
        is_active=False,
        game_questions__isnull=True,
        mistakes__isnull=True,
        flashcard_states__isnull=True,
    ).delete()
    LearningObject.objects.filter(
        product_id="k_game",
        is_active=False,
        knowledge_sources__isnull=True,
    ).delete()
    return result
