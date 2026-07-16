import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

from django.core.exceptions import ValidationError
from django.db import transaction

from apps.flashcards.models import FlashcardState
from apps.games.models import GameQuestion, Mistake
from apps.learning.models import KnowledgeSource, LearningObject

from .learning_sync import regenerate_and_sync_drug_question_sources
from .models import Drug, DrugDatasetDocument, DrugQuestionSource, DrugTopic
from .services import ensure_topics


SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
REPORT_FILE_NAME = "drug_enrichment_report.json"
INVALID_VALUES = {"", "-", "ندارد", "نامشخص", "none", "unknown", "n/a"}
FIXTURE_DRUG_MODEL = "drugs.drug"
FIXTURE_DATASET_DOCUMENT_MODEL = "drugs.drugdatasetdocument"

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
    "atc_codes",
    "atc_classes",
    "atc_subclasses",
    "atc_categories",
    "category",
    "consumption_time_sorted",
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


def compact_text(value):
    if isinstance(value, list):
        return " | ".join(item for item in (compact_text(item) for item in value) if item)
    if value is None:
        return ""
    return " ".join(str(value).split()).strip()


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

    normalized = (
        text
        .replace("ي", "ی")
        .replace("ك", "ک")
        .replace(" ", "")
        .replace("\u200c", "")
        .replace("(", "")
        .replace(")", "")
        .replace("،", "")
        .replace(".", "")
        .replace("؛", "")
        .casefold()
    )

    if not normalized or normalized in INVALID_VALUES:
        return ""

    no_difference_patterns = [
        "بایا‌بدونغذا",
        "بایابدونغذا",
        "باوبدونغذا",
        "بدونتوجهبهمصرفغذا",
        "بدونتوجهبغذا",
        "بدونتوجهبهغذا",
        "ارتباطیبامصرفغذاندارد",
        "ارتباطیمصرفغذاندارد",
        "ارتباطبامصرفغذاندارد",
        "فرقیندارد",
        "فرقی‌میکند",
        "فرقی‌میکند",
        "هرزمان",
        "تفاوتیندارد",
        "تفاوتندارد",
        "تفاوتیوجودندارد",
    ]

    empty_stomach_patterns = [
        "معدهخالی",
        "ناشتا",
        "قبلغذا",
        "قبلوازغذا",
        "یکساعتقبلغذا",
        "1ساعتقبلغذا",
        "دوساعتبعدازغذا",
        "بدونغذا",
    ]
        # مواردی که "بعد غذا توصیه نشدن" هستند و نباید با غذا حساب شوند
    negative_food_patterns = [
        "بعدازیکوعدهغذایسنگینتوصیهنمیشود",
        "بعدازغذایسنگینتوصیهنمیشود",
        "اجتنابازمصرفبعدازوعدهغذایی",
    ]

    if any(p in normalized for p in negative_food_patterns):
        return None
    
    # فاصله مشخص قبل یا بعد غذا
    separated_from_food_patterns = [
        "قبلغذا",
        "یکساعتقبلغذا",
        "1ساعتقبلغذا",
        "نیمساعتقبلغذا",
        "30دقیقهقبلغذا",
        "دو ساعتبعدازغذا",
        "2ساعتبعدازغذا",
        "یکساعتبعدازغذا",
        "1ساعتبعدازغذا",
    ]

    if any(p in normalized for p in separated_from_food_patterns):
        return "بدون غذا"

    with_food_patterns = [
        "همراهغذا",
        "معدهپر",
        "وعدهغذایی",
        "بعدازغذایسبک",
        "بعدازوعدهغذایی",
    ]

    has_no_difference = any(
        p.replace("\u200c", "") in normalized
        for p in no_difference_patterns
    )

    has_empty = any(
        p in normalized
        for p in empty_stomach_patterns
    )

    has_food = any(
        p in normalized
        for p in with_food_patterns
    )

    # اگر داده شامل چند حالت متناقض باشد
    # مثل:
    # IR بدون توجه به غذا + ER با شکم خالی
    # یا با غذا + بدون غذا
    if has_no_difference:
        return "فرقی نمی‌کند"

    if has_empty and has_food:
        return "فرقی نمی‌کند"

    if has_empty:
        return "بدون غذا"

    if has_food:
        return "با غذا"

    return None


def stable_external_id(schema_version, source_sha256, table_index, source_row):
    seed = f"{schema_version}:{source_sha256}:{table_index}:{source_row}"
    return f"json-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:32]}"


def stored_timing_value(precomputed_value, fallback_value):
    if isinstance(precomputed_value, list):
        precomputed_value = next((item for item in precomputed_value if item not in (None, "")), "")
    precomputed = "" if precomputed_value is None else " ".join(str(precomputed_value).split()).strip()
    if precomputed and precomputed.casefold() not in INVALID_VALUES:
        return precomputed
    canonical = canonical_timing(fallback_value)
    return canonical or ""


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
                atc_codes = clean_list(row.get("atc_codes") or row.get("atc_code"))
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
                category = clean_list(row.get("category"))
                atc_categories = clean_list(row.get("atc_categories") or category)
                drug_classification = (
                    source_classification
                    or (category[0] if category else "")
                    or (atc_categories[0] if atc_categories else "")
                )
                food_relation = combined_values(row, "food_relation")
                consumption_time_sorted = stored_timing_value(
                    row.get("consumption_time_sorted"),
                    food_relation,
                )
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
                            "consumption_time_sorted": consumption_time_sorted,
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
                            "atc_classes": clean_list(row.get("atc_classes") or row.get("class")),
                            "atc_subclasses": clean_list(row.get("atc_subclasses") or row.get("sub_class")),
                            "atc_categories": atc_categories,
                            "category": category,
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


def parse_fixture_file(path):
    path = Path(path).expanduser().resolve()
    if not path.is_file():
        raise ValidationError(f"Fixture JSON file does not exist: {path}")

    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list):
        raise ValidationError(f"{path.name}: expected a Django fixture JSON array")

    documents_by_pk = {}
    document_order = []
    seen_external_ids = set()

    for item in payload:
        if not isinstance(item, dict):
            raise ValidationError(f"{path.name}: fixture entries must be objects")
        if item.get("model") != FIXTURE_DATASET_DOCUMENT_MODEL:
            continue

        fields = item.get("fields") or {}
        document_pk = item.get("pk")
        source_file = clean_text(fields.get("source_file"))
        source_sha256 = clean_text(fields.get("source_sha256"))
        if document_pk in (None, "") or not source_file or len(source_sha256) != 64:
            raise ValidationError(
                f"{path.name}: invalid drugs.drugdatasetdocument entry {document_pk!r}"
            )

        documents_by_pk[document_pk] = ParsedDocument(
            values={
                "schema_version": clean_text(fields.get("schema_version")),
                "source_file": source_file,
                "source_path": clean_text(fields.get("source_path")),
                "source_format": clean_text(fields.get("source_format")),
                "source_size_bytes": fields.get("source_size_bytes") or 0,
                "source_sha256": source_sha256,
                "source_metadata": fields.get("source_metadata") or {},
                "extraction_metadata": fields.get("extraction_metadata") or {},
                "warnings": fields.get("warnings") or [],
                "enrichment_metadata": fields.get("enrichment_metadata") or {},
            }
        )
        document_order.append(document_pk)

    if not documents_by_pk:
        raise ValidationError(f"{path.name}: no drugs.drugdatasetdocument entries found")

    for item in payload:
        if item.get("model") != FIXTURE_DRUG_MODEL:
            continue

        fields = item.get("fields") or {}
        dataset_document_pk = fields.get("dataset_document")
        if dataset_document_pk not in documents_by_pk:
            raise ValidationError(
                f"{path.name}: drug {item.get('pk')!r} references unknown dataset document {dataset_document_pk!r}"
            )

        external_id = clean_text(fields.get("external_id"))
        if not external_id:
            raise ValidationError(f"{path.name}: drug {item.get('pk')!r} is missing external_id")
        if external_id in seen_external_ids:
            raise ValidationError(f"{path.name}: duplicate drug external_id {external_id!r}")
        seen_external_ids.add(external_id)

        raw = fields.get("raw") if isinstance(fields.get("raw"), dict) else {}
        category = clean_list(fields.get("category") or raw.get("category"))
        atc_categories = clean_list(fields.get("atc_categories") or category)
        drug_classification = (
            clean_text(fields.get("drug_classification"))
            or (category[0] if category else "")
            or (atc_categories[0] if atc_categories else "")
        )

        documents_by_pk[dataset_document_pk].drugs.append(
            ParsedDrug(
                external_id=external_id,
                values={
                    "name": clean_text(fields.get("name")),
                    "persian_name": clean_text(fields.get("persian_name")),
                    "brand_name": clean_text(fields.get("brand_name")),
                    "generic_name": clean_text(fields.get("generic_name")),
                    "dosage_form": clean_text(fields.get("dosage_form")),
                    "drug_classification": drug_classification,
                    "consumption_time": clean_text(fields.get("consumption_time")),
                    "consumption_time_sorted": stored_timing_value(
                        fields.get("consumption_time_sorted") or raw.get("consumption_time_sorted"),
                        fields.get("consumption_time"),
                    ),
                    "indication": clean_text(fields.get("indication")),
                    "indication_answer": clean_text(fields.get("indication_answer")),
                    "side_effects": clean_text(fields.get("side_effects")),
                    "side_effects_answer": clean_text(fields.get("side_effects_answer")),
                    "dosing_and_administration": clean_text(fields.get("dosing_and_administration")),
                    "pregnancy": clean_text(fields.get("pregnancy")),
                    "breastfeeding": clean_text(fields.get("breastfeeding")),
                    "dose_adjustment": clean_text(fields.get("dose_adjustment")),
                    "clinical_notes": clean_text(fields.get("clinical_notes")),
                    "atc_codes": clean_list(fields.get("atc_codes")),
                    "atc_classes": clean_list(fields.get("atc_classes")),
                    "atc_subclasses": clean_list(fields.get("atc_subclasses")),
                    "atc_categories": atc_categories,
                    "category": category,
                    "source_topic": clean_text(fields.get("source_topic")),
                    "source_file": clean_text(fields.get("source_file"))
                    or documents_by_pk[dataset_document_pk].values["source_file"],
                    "source_table": int(fields.get("source_table") or 0),
                    "source_row": int(fields.get("source_row") or 0),
                    "extra_attributes": (
                        fields.get("extra_attributes")
                        if isinstance(fields.get("extra_attributes"), dict)
                        else {}
                    ),
                    "raw": raw,
                },
            )
        )

    return [documents_by_pk[pk] for pk in document_order], 0


def parse_json_source(source):
    source = Path(source).expanduser().resolve()
    if source.is_dir():
        return parse_json_directory(source)
    if source.is_file():
        return parse_fixture_file(source)
    raise ValidationError(f"JSON source does not exist: {source}")


@transaction.atomic
def replace_drug_metadata_from_json(source):
    documents, skipped_rows = parse_json_source(source)

    GameQuestion.objects.filter(source__isnull=False).update(source=None)
    Mistake.objects.filter(source__isnull=False).update(source=None)
    FlashcardState.objects.filter(source__isnull=False).update(source=None)
    DrugQuestionSource.objects.all().delete()
    Drug.objects.all().delete()
    DrugDatasetDocument.objects.all().delete()
    KnowledgeSource.objects.filter(product_id="pharmexa").update(is_active=False)
    LearningObject.objects.filter(product_id="pharmexa").update(is_active=False)

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
            result.question_sources += regenerate_and_sync_drug_question_sources(
                drug,
                topics=topics,
            ).question_sources
    KnowledgeSource.objects.filter(
        product_id="pharmexa",
        is_active=False,
        game_questions__isnull=True,
        mistakes__isnull=True,
        flashcard_states__isnull=True,
    ).delete()
    LearningObject.objects.filter(
        product_id="pharmexa",
        is_active=False,
        knowledge_sources__isnull=True,
    ).delete()
    return result
