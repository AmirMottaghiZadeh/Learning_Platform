from collections import Counter
from csv import writer
from io import StringIO
from math import ceil
from uuid import uuid4

from django.apps import apps
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import Count, Q
from django.http import Http404
from django.utils import timezone

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.appliers.apply_changes import apply_approved_suggestions
from apps.ai_data_pipeline.analyzers.health_check import run_health_check
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob, AIDataReport, AIDataSuggestion, AIDataChangeHistory
from apps.ai_data_pipeline.providers.base import get_provider
from apps.ai_data_pipeline.reviewers.suggestion_generator import DEFAULT_FIELDS, generate_suggestions
from apps.drugs.learning_sync import PRODUCT_ID, regenerate_and_sync_drug_question_sources
from apps.drugs.models import Drug
from apps.learning.models import KnowledgeSource, LearningObject


DRUG_DATABASE_EDITABLE_FIELDS = (
    "name",
    "persian_name",
    "brand_name",
    "generic_name",
    "dosage_form",
    "drug_classification",
    "consumption_time",
    "consumption_time_sorted",
    "indication",
    "indication_answer",
    "side_effects",
    "side_effects_answer",
    "dosing_and_administration",
    "pregnancy",
    "breastfeeding",
    "dose_adjustment",
    "clinical_notes",
    "atc_codes",
    "atc_classes",
    "atc_subclasses",
    "atc_categories",
    "category",
    "source_topic",
    "extra_attributes",
)

DRUG_DATABASE_SEARCH_FIELDS = (
    "name",
    "persian_name",
    "brand_name",
    "generic_name",
    "indication",
    "indication_answer",
    "side_effects",
    "side_effects_answer",
    "dosage_form",
    "drug_classification",
    "consumption_time",
    "consumption_time_sorted",
    "dosing_and_administration",
    "pregnancy",
    "breastfeeding",
    "dose_adjustment",
    "clinical_notes",
    "source_topic",
)


def get_model_for_table(table_name):
    for model in apps.get_models():
        if model._meta.db_table == table_name:
            return model
    raise Http404(f"Unknown table: {table_name}")


def format_duration(started_at, completed_at=None):
    if not started_at:
        return "-"
    end = completed_at or timezone.now()
    delta = end - started_at
    total_seconds = int(delta.total_seconds())
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}h {minutes}m"
    if minutes:
        return f"{minutes}m {seconds}s"
    return f"{seconds}s"


def quality_score_from_summary(summary, suggestion_counts=None):
    suggestion_counts = suggestion_counts or {}
    total_records = summary.get("total_records_scanned", 0) or 1
    issues = summary.get("issue_count", 0)
    duplicate_hits = summary.get("exact_duplicate_groups", 0) + summary.get("near_duplicate_pairs", 0)
    risky = suggestion_counts.get(constants.RISK_RISKY, 0)
    needs_review = suggestion_counts.get(constants.RISK_NEEDS_REVIEW, 0)
    score = 100
    score -= min(45, (issues / total_records) * 100 * 1.2)
    score -= min(15, duplicate_hits * 2.5)
    score -= min(15, risky * 1.5)
    score -= min(10, needs_review * 0.5)
    return max(0, round(score, 1))


def health_summary_snapshot():
    latest_health_report = (
        AIDataReport.objects.filter(report_type=constants.BATCH_TYPE_HEALTH_CHECK, format="json")
        .order_by("-created_at")
        .first()
    )
    if latest_health_report and latest_health_report.content.get("health_report"):
        return latest_health_report.content["health_report"].get("summary", {})
    live_report = run_health_check()
    return live_report.get("summary", {})


def build_dashboard_context():
    suggestions = AIDataSuggestion.objects.all()
    suggestion_status_counts = dict(Counter(suggestions.values_list("status", flat=True)))
    suggestion_risk_counts = dict(Counter(suggestions.values_list("risk_level", flat=True)))
    suggestion_type_counts = dict(Counter(suggestions.values_list("suggestion_type", flat=True)))
    latest_health = health_summary_snapshot()

    latest_batches = list(AIDataBatch.objects.order_by("-created_at")[:12])
    latest_jobs = list(AIDataJob.objects.order_by("-created_at")[:12])
    latest_reports = list(AIDataReport.objects.order_by("-created_at")[:8])
    problem_tables = list(
        suggestions.values("table_name")
        .annotate(total=Count("id"))
        .order_by("-total", "table_name")[:8]
    )
    problem_fields = list(
        suggestions.values("field_name")
        .annotate(total=Count("id"))
        .order_by("-total", "field_name")[:8]
    )

    health_reports = list(
        AIDataReport.objects.filter(report_type=constants.BATCH_TYPE_HEALTH_CHECK, format="json")
        .order_by("-created_at")[:8]
    )
    health_trend = []
    for report in reversed(health_reports):
        summary = report.content.get("health_report", {}).get("summary", {})
        total_records = summary.get("total_records_scanned", 0) or 1
        issue_count = summary.get("issue_count", 0)
        score = quality_score_from_summary(summary, suggestion_risk_counts)
        health_trend.append(
            {
                "label": f"H{report.id}",
                "date": report.created_at,
                "score": score,
                "issue_count": issue_count,
                "total_records": total_records,
            }
        )

    if not health_trend and latest_batches:
        for batch in reversed(latest_batches[:8]):
            summary = batch.summary or {}
            issue_count = summary.get("issue_count", 0)
            total_records = summary.get("total_records_scanned", 0) or summary.get("records_scanned", 0) or 1
            score = quality_score_from_summary(summary, suggestion_risk_counts)
            health_trend.append(
                {
                    "label": f"B{batch.id}",
                    "date": batch.created_at,
                    "score": score,
                    "issue_count": issue_count,
                    "total_records": total_records,
                }
            )

    trend_path = build_sparkline_path([point["score"] for point in health_trend])
    total_records = latest_health.get("total_records_scanned", 0)
    total_issues = latest_health.get("issue_count", 0)
    health_score = quality_score_from_summary(latest_health, suggestion_risk_counts)

    return {
        "latest_batches": latest_batches,
        "latest_jobs": latest_jobs,
        "latest_reports": latest_reports,
        "latest_health": latest_health,
        "suggestion_status_counts": suggestion_status_counts,
        "suggestion_risk_counts": suggestion_risk_counts,
        "suggestion_type_counts": suggestion_type_counts,
        "problem_tables": problem_tables,
        "problem_fields": problem_fields,
        "health_trend": health_trend,
        "trend_path": trend_path,
        "health_score": health_score,
        "total_records": total_records,
        "total_issues": total_issues,
        "pending_suggestions": suggestion_status_counts.get(constants.SUGGESTION_STATUS_PENDING, 0),
        "approved_suggestions": suggestion_status_counts.get(constants.SUGGESTION_STATUS_APPROVED, 0),
        "applied_suggestions": suggestion_status_counts.get(constants.SUGGESTION_STATUS_APPLIED, 0),
        "rejected_suggestions": suggestion_status_counts.get(constants.SUGGESTION_STATUS_REJECTED, 0),
        "needs_review_suggestions": suggestion_risk_counts.get(constants.RISK_NEEDS_REVIEW, 0),
        "risky_suggestions": suggestion_risk_counts.get(constants.RISK_RISKY, 0),
        "duplicate_candidates": latest_health.get("exact_duplicate_groups", 0) + latest_health.get("near_duplicate_pairs", 0),
        "medical_validation_warnings": latest_health.get("issue_counts", {}).get("medical_warning", 0),
        "translation_suggestions": suggestion_type_counts.get(constants.SUGGESTION_TYPE_TRANSLATION, 0),
        "normalization_suggestions": suggestion_type_counts.get(constants.SUGGESTION_TYPE_NORMALIZATION, 0),
        "terminology_suggestions": suggestion_type_counts.get(constants.SUGGESTION_TYPE_TERMINOLOGY, 0),
        "drug_record_count": Drug.objects.count(),
    }


def build_sparkline_path(values, width=240, height=70, padding=6):
    if not values:
        return ""
    if len(values) == 1:
        x = width / 2
        y = height / 2
        return f"M {x:.1f} {y:.1f}"
    min_value = min(values)
    max_value = max(values)
    spread = max(max_value - min_value, 1)
    step_x = (width - padding * 2) / (len(values) - 1)
    points = []
    for index, value in enumerate(values):
        x = padding + index * step_x
        normalized = (value - min_value) / spread
        y = height - padding - (normalized * (height - padding * 2))
        points.append(f"{x:.1f},{y:.1f}")
    return "M " + " L ".join(points)


def build_batch_context(batch):
    previous_batch = (
        AIDataBatch.objects.filter(batch_type=batch.batch_type, created_at__lt=batch.created_at)
        .order_by("-created_at")
        .first()
    )
    reports = list(batch.reports.order_by("-created_at"))
    jobs = list(batch.jobs.order_by("-created_at"))
    suggestions = list(batch.suggestions.order_by("-created_at"))
    stats = {
        "total": batch.total_suggestions,
        "pending": batch.pending_suggestions,
        "approved": batch.approved_suggestions,
        "rejected": batch.rejected_suggestions,
        "applied": batch.applied_suggestions,
        "safe": batch.safe_suggestions,
        "needs_review": batch.needs_review_suggestions,
        "risky": batch.risky_suggestions,
    }
    comparison = {}
    if previous_batch:
        comparison = {
            "previous_batch": previous_batch,
            "delta_total": stats["total"] - previous_batch.total_suggestions,
            "delta_pending": stats["pending"] - previous_batch.pending_suggestions,
            "delta_applied": stats["applied"] - previous_batch.applied_suggestions,
            "delta_risky": stats["risky"] - previous_batch.risky_suggestions,
        }
    return {
        "batch": batch,
        "previous_batch": previous_batch,
        "comparison": comparison,
        "reports": reports,
        "jobs": jobs,
        "suggestions": suggestions,
        "stats": stats,
    }


def filter_suggestions(params):
    queryset = AIDataSuggestion.objects.select_related("batch").order_by("-created_at")
    q = params.get("q", "").strip()
    batch_id = params.get("batch") or params.get("batch_id")
    provider = params.get("provider", "").strip()
    status = params.get("status", "").strip()
    risk_level = params.get("risk_level", "").strip()
    suggestion_type = params.get("suggestion_type", "").strip()
    table_name = params.get("table_name", "").strip()
    field_name = params.get("field_name", "").strip()
    sort = params.get("sort") or "-created_at"

    if q:
        queryset = queryset.filter(
            Q(old_value__icontains=q)
            | Q(suggested_value__icontains=q)
            | Q(reason__icontains=q)
            | Q(record_id__icontains=q)
        )
    if batch_id:
        queryset = queryset.filter(batch_id=batch_id)
    if provider:
        queryset = queryset.filter(provider=provider)
    if status:
        queryset = queryset.filter(status=status)
    if risk_level:
        queryset = queryset.filter(risk_level=risk_level)
    if suggestion_type:
        queryset = queryset.filter(suggestion_type=suggestion_type)
    if table_name:
        queryset = queryset.filter(table_name__icontains=table_name)
    if field_name:
        queryset = queryset.filter(field_name__icontains=field_name)

    if sort in {"created_at", "-created_at", "confidence_score", "-confidence_score"}:
        queryset = queryset.order_by(sort)
    return queryset


def create_rule_based_suggestion_batch(*, cleaned_data, created_by):
    """Create a local rules review package without changing drug records."""
    provider = get_provider(constants.PROVIDER_RULES)
    config = {
        "provider": provider.provider_name,
        "generation_mode": "rule_based",
        "batch_name": cleaned_data.get("batch_name", "").strip(),
        "limit": cleaned_data["max_suggestions"],
        "include_normalization": cleaned_data["include_normalization"],
        "include_terminology": cleaned_data["include_terminology"],
        "include_medical_validation": cleaned_data["include_medical_validation"],
        "include_duplicates": cleaned_data["include_duplicates"],
        "include_translations": cleaned_data["include_translations"],
    }
    batch = AIDataBatch.objects.create(
        batch_type=constants.BATCH_TYPE_SUGGESTION_GENERATION,
        status=constants.BATCH_STATUS_RUNNING,
        source_database=str(settings.DATABASES["default"].get("NAME", "")),
        target_scope={"table": constants.DRUG_TABLE, "fields": list(DEFAULT_FIELDS)},
        config=config,
        created_by=created_by,
        started_at=timezone.now(),
    )
    job = AIDataJob.objects.create(
        batch=batch,
        job_type=constants.JOB_TYPE_FULL_RULES_REVIEW,
        provider=provider.provider_name,
        status=constants.JOB_STATUS_PENDING,
        parameters_json=config,
        created_by=created_by,
    )
    try:
        summary = generate_suggestions(
            batch=batch,
            job=job,
            fields=DEFAULT_FIELDS,
            limit=config["limit"],
            provider=provider,
            table=constants.DRUG_TABLE,
            include_normalization=config["include_normalization"],
            include_terminology=config["include_terminology"],
            include_medical_validation=config["include_medical_validation"],
            include_duplicates=config["include_duplicates"],
            include_translations=config["include_translations"],
        )
    except Exception as exc:
        job.mark_failed(exc)
        batch.status = constants.BATCH_STATUS_FAILED
        batch.error_message = str(exc)
        batch.completed_at = timezone.now()
        batch.save(update_fields=["status", "error_message", "completed_at"])
        raise
    return batch, summary


def is_rule_based_batch(batch):
    return (
        batch.config.get("provider") == constants.PROVIDER_RULES
        or batch.jobs.filter(provider=constants.PROVIDER_RULES).exists()
        or batch.suggestions.filter(provider=constants.PROVIDER_RULES).exists()
    )


def apply_rule_based_suggestions(*, batch, suggestion_ids=None, applied_by=""):
    """Apply only confirmed, approved, safe rule-based suggestions in a package."""
    if not is_rule_based_batch(batch):
        raise ValueError("Only rule-based review packages can be applied from this workspace.")
    return apply_approved_suggestions(
        batch_id=batch.id,
        suggestion_ids=suggestion_ids,
        applied_by=applied_by,
        min_confidence=0.8,
        include_risky=False,
    )


def filter_drugs(params):
    queryset = Drug.objects.select_related("dataset_document")
    q = params.get("q", "").strip()
    search_field = params.get("search_field", "all").strip()
    sort = params.get("sort") or "generic_name"

    if q:
        if search_field in DRUG_DATABASE_SEARCH_FIELDS:
            queryset = queryset.filter(**{f"{search_field}__icontains": q})
        else:
            matches = Q()
            for field_name in DRUG_DATABASE_SEARCH_FIELDS:
                matches |= Q(**{f"{field_name}__icontains": q})
            queryset = queryset.filter(matches)

    if sort in {"generic_name", "brand_name", "-updated_at", "-created_at"}:
        queryset = queryset.order_by(sort, "id")
    else:
        queryset = queryset.order_by("generic_name", "id")
    return queryset


def _history_value(value):
    if isinstance(value, (dict, list)):
        import json

        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return "" if value is None else str(value)


def update_drug_from_quality_center(*, drug_id, cleaned_data, edited_by):
    """Persist an approved manual edit and record each changed field for audit."""
    with transaction.atomic():
        drug = Drug.objects.select_for_update().get(pk=drug_id)
        changes = []
        for field_name in DRUG_DATABASE_EDITABLE_FIELDS:
            new_value = cleaned_data[field_name]
            old_value = getattr(drug, field_name)
            if old_value != new_value:
                changes.append((field_name, old_value, new_value))
                setattr(drug, field_name, new_value)

        if not changes:
            return drug, []

        drug.save(update_fields=[*(field_name for field_name, _, _ in changes), "updated_at"])
        regenerate_and_sync_drug_question_sources(drug)
        for field_name, old_value, new_value in changes:
            AIDataChangeHistory.objects.create(
                table_name=constants.DRUG_TABLE,
                record_id=str(drug.id),
                field_name=field_name,
                old_value=_history_value(old_value),
                new_value=_history_value(new_value),
                reason="Manual database update in Data Quality Center.",
                suggestion_type="manual_edit",
                applied_by=edited_by,
                metadata={
                    "change_source": "data_quality_center",
                    "manual_edit": True,
                },
            )
    return drug, changes


def create_drug_from_quality_center(*, cleaned_data, created_by):
    """Create an admin-entered drug with server-generated identifiers and audit history."""
    with transaction.atomic():
        drug = Drug.objects.create(
            external_id=f"drug-{uuid4().hex}",
            raw={"created_via": "data_quality_center"},
            **{
                field_name: cleaned_data[field_name]
                for field_name in DRUG_DATABASE_EDITABLE_FIELDS
            },
        )
        regenerate_and_sync_drug_question_sources(drug)
        AIDataChangeHistory.objects.create(
            table_name=constants.DRUG_TABLE,
            record_id=str(drug.id),
            field_name="__record__",
            old_value="",
            new_value=f"Created drug #{drug.id} ({drug.external_id}).",
            reason="Manual drug creation in Data Quality Center.",
            suggestion_type="manual_create",
            applied_by=created_by,
            metadata={
                "change_source": "data_quality_center",
                "manual_create": True,
                "external_id": drug.external_id,
                "initial_values": {
                    field_name: _history_value(cleaned_data[field_name])
                    for field_name in DRUG_DATABASE_EDITABLE_FIELDS
                },
            },
        )
    return drug


class DrugDeletionBlocked(ValueError):
    """Raised when a historical legacy session still protects a drug question source."""


def drug_deletion_summary(drug):
    learning_objects = LearningObject.objects.filter(
        product_id=PRODUCT_ID,
        external_id=drug.external_id,
    )
    learning_object_ids = list(learning_objects.values_list("id", flat=True))
    return {
        "question_sources": drug.question_sources.count(),
        "learning_objects": len(learning_object_ids),
        "learning_sources": KnowledgeSource.objects.filter(
            learning_object_id__in=learning_object_ids,
        ).count(),
    }


def delete_drug_from_quality_center(*, drug_id, deleted_by):
    """Delete a drug record while retaining inactive learning history references."""
    from apps.games.models import GameQuestion

    with transaction.atomic():
        drug = Drug.objects.select_for_update().get(pk=drug_id)
        legacy_question_count = GameQuestion.objects.filter(source__drug_id=drug.id).count()
        if legacy_question_count:
            raise DrugDeletionBlocked(
                "This drug is referenced by "
                f"{legacy_question_count} legacy quiz question(s) and cannot be deleted safely."
            )

        summary = drug_deletion_summary(drug)
        record_id = str(drug.id)
        display_name = drug.brand_name or drug.generic_name or drug.name or drug.persian_name or drug.external_id
        snapshot = {
            "id": drug.id,
            "external_id": drug.external_id,
            "dataset_document_id": drug.dataset_document_id,
            **{
                field_name: getattr(drug, field_name)
                for field_name in DRUG_DATABASE_EDITABLE_FIELDS
            },
        }
        learning_object_ids = list(
            LearningObject.objects.filter(
                product_id=PRODUCT_ID,
                external_id=drug.external_id,
            ).values_list("id", flat=True)
        )

        # Existing game questions use KnowledgeSource with PROTECT. Keep those references
        # for historical sessions, but make the sources unavailable to future quizzes/cards.
        KnowledgeSource.objects.filter(learning_object_id__in=learning_object_ids).update(is_active=False)
        LearningObject.objects.filter(id__in=learning_object_ids).update(is_active=False)
        drug.delete()

        AIDataChangeHistory.objects.create(
            table_name=constants.DRUG_TABLE,
            record_id=record_id,
            field_name="__record__",
            old_value=_history_value(display_name),
            new_value=f"Deleted drug #{record_id}.",
            reason="Manual drug deletion in Data Quality Center.",
            suggestion_type="manual_delete",
            applied_by=deleted_by,
            metadata={
                "change_source": "data_quality_center",
                "manual_delete": True,
                "deactivated_learning_sources": summary["learning_sources"],
                "deactivated_learning_objects": summary["learning_objects"],
                "deleted_question_sources": summary["question_sources"],
                "deleted_record_snapshot": snapshot,
            },
        )
    return summary


def build_record_context(model, record_id):
    try:
        record = model.objects.get(pk=record_id)
    except ObjectDoesNotExist as exc:
        raise Http404(str(exc)) from exc

    fields = []
    for field in model._meta.concrete_fields:
        fields.append({
            "name": field.name,
            "verbose_name": field.verbose_name.title(),
            "value": getattr(record, field.name),
        })

    table_name = model._meta.db_table
    suggestions = AIDataSuggestion.objects.filter(table_name=table_name, record_id=str(record_id)).order_by("-created_at")
    history = AIDataChangeHistory.objects.filter(table_name=table_name, record_id=str(record_id)).order_by("-applied_at")
    warnings = [suggestion for suggestion in suggestions if suggestion.suggestion_type == constants.SUGGESTION_TYPE_MEDICAL_WARNING]
    translations = [suggestion for suggestion in suggestions if suggestion.suggestion_type == constants.SUGGESTION_TYPE_TRANSLATION]
    terminology = [suggestion for suggestion in suggestions if suggestion.suggestion_type == constants.SUGGESTION_TYPE_TERMINOLOGY]
    duplicates = []
    if table_name == "drugs_drug":
        duplicates = _duplicate_candidates_for_drug(record)

    quality_score = 100
    quality_score -= min(50, len(warnings) * 7)
    quality_score -= min(20, len(terminology) * 2)
    quality_score -= min(20, len(translations) * 1.5)
    quality_score -= min(20, len(history) * 0.7)
    quality_score = max(0, round(quality_score, 1))

    return {
        "record": record,
        "table_name": table_name,
        "fields": fields,
        "suggestions": suggestions,
        "history": history,
        "warnings": warnings,
        "translations": translations,
        "terminology": terminology,
        "duplicates": duplicates,
        "quality_score": quality_score,
    }


def _duplicate_candidates_for_drug(record):
    from apps.drugs.models import Drug
    from apps.drugs.services import generic_drug_signature

    exact = []
    near = []
    signature = generic_drug_signature(record)
    if signature:
        for drug in Drug.objects.exclude(pk=record.pk).iterator():
            if generic_drug_signature(drug) == signature:
                exact.append(drug)
    return {"exact": exact[:10], "near": near[:10]}


def report_csv_content(report):
    buffer = StringIO()
    csv_writer = writer(buffer)
    csv_writer.writerow(["section", "key", "value"])
    for key, value in sorted((report.summary or {}).items()):
        csv_writer.writerow(["summary", key, value])
    suggestions = report.content.get("suggestions", {})
    for key, value in sorted(suggestions.items()):
        csv_writer.writerow(["suggestions", key, value])
    return buffer.getvalue()
