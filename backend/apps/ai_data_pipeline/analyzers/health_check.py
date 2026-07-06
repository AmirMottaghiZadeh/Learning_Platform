from collections import Counter, defaultdict

from django.db.models import Count

from apps.drugs.models import Drug, DrugQuestionSource, DrugTopic
from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.analyzers.consistency_checker import check_text_consistency
from apps.ai_data_pipeline.analyzers.duplicate_detector import detect_exact_duplicates, detect_near_duplicates
from apps.ai_data_pipeline.analyzers.medical_validator import validate_drug_record
from apps.ai_data_pipeline.transformers.normalizer import normalize_text

SCAN_MODELS = [DrugTopic, Drug, DrugQuestionSource]
MIXED_ALLOWED_FIELDS = {"dosage_form", "drug_classification", "brand_name", "feedback", "prompt"}
SUSPICIOUS_EMPTY_FIELDS = set(constants.IMPORTANT_DRUG_FIELDS)


def run_health_check(*, include_near_duplicates=True, near_duplicate_threshold=0.92):
    report = {
        "tables": [],
        "total_records_scanned": 0,
        "issues": [],
        "duplicates": {"exact": [], "near": []},
        "summary": {},
    }

    for model in SCAN_MODELS:
        table_report = analyze_model(model)
        report["tables"].append(table_report)
        report["total_records_scanned"] += table_report["record_count"]
        report["issues"].extend(table_report["issues"])

    report["duplicates"]["exact"] = detect_exact_duplicates()
    if include_near_duplicates:
        report["duplicates"]["near"] = detect_near_duplicates(threshold=near_duplicate_threshold)

    report["summary"] = summarize_report(report)
    return report


def analyze_model(model):
    table_name = model._meta.db_table
    fields = [field for field in model._meta.concrete_fields]
    text_fields = [field for field in fields if field.get_internal_type() in {"CharField", "TextField"}]
    queryset = model.objects.all()
    issues = []
    field_stats = {}

    for field in fields:
        stat = {"field_name": field.name, "null_count": 0, "empty_string_count": 0}
        if field.null:
            stat["null_count"] = queryset.filter(**{f"{field.name}__isnull": True}).count()
        if field in text_fields:
            stat["empty_string_count"] = queryset.filter(**{field.name: ""}).count()
        field_stats[field.name] = stat

    for obj in queryset:
        for field in text_fields:
            value = getattr(obj, field.name)
            mixed_allowed = field.name in MIXED_ALLOWED_FIELDS
            issues.extend(
                check_text_consistency(
                    table_name=table_name,
                    record_id=obj.pk,
                    field_name=field.name,
                    value=value,
                    mixed_allowed=mixed_allowed,
                )
            )
            if field.name in SUSPICIOUS_EMPTY_FIELDS and normalize_text(value) == "":
                issues.append({
                    "issue_type": "important_field_empty",
                    "table_name": table_name,
                    "record_id": obj.pk,
                    "field_name": field.name,
                    "detail": "Important field is empty.",
                })
        if isinstance(obj, Drug):
            issues.extend(validate_drug_record(obj))

    duplicate_values = []
    for field in text_fields:
        duplicates = (
            queryset.exclude(**{field.name: ""})
            .values(field.name)
            .annotate(count=Count("id"))
            .filter(count__gt=1)
            .order_by("-count")[:25]
        )
        duplicate_values.extend([
            {"field_name": field.name, "value": item[field.name], "count": item["count"]}
            for item in duplicates
        ])

    issue_counts = Counter(issue["issue_type"] for issue in issues)
    return {
        "table_name": table_name,
        "model": model.__name__,
        "record_count": queryset.count(),
        "column_count": len(fields),
        "columns": [field.name for field in fields],
        "field_stats": list(field_stats.values()),
        "duplicate_values": duplicate_values,
        "issue_counts": dict(issue_counts),
        "issues": issues,
    }


def summarize_report(report):
    issue_counter = Counter(issue["issue_type"] for issue in report["issues"])
    risky_counter = defaultdict(int)
    for issue in report["issues"]:
        risky_counter[issue.get("table_name", "unknown")] += 1
    return {
        "total_records_scanned": report["total_records_scanned"],
        "issue_count": len(report["issues"]),
        "issue_counts": dict(issue_counter),
        "exact_duplicate_groups": len(report["duplicates"]["exact"]),
        "near_duplicate_pairs": len(report["duplicates"]["near"]),
        "issues_by_table": dict(risky_counter),
    }
