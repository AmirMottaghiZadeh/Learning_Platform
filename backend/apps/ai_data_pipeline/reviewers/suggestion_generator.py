from django.utils import timezone

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.analyzers.duplicate_detector import detect_exact_duplicates, detect_near_duplicates
from apps.ai_data_pipeline.analyzers.medical_validator import validate_drug_record
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob, AIDataSuggestion
from apps.ai_data_pipeline.providers.base import get_provider
from apps.ai_data_pipeline.transformers.normalizer import normalize_text, standard_english_casing
from apps.ai_data_pipeline.transformers.terminology_checker import check_terminology
from apps.drugs.models import Drug


DEFAULT_FIELDS = [
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
]


def generate_suggestions(
    *,
    batch: AIDataBatch = None,
    fields=None,
    limit=None,
    provider=None,
    job: AIDataJob = None,
    table=constants.DRUG_TABLE,
    risk_level=None,
    only_safe=False,
    dry_run=False,
    include_duplicates=True,
    include_medical_validation=True,
    include_normalization=True,
    include_terminology=True,
    include_translations=True,
):
    if table != constants.DRUG_TABLE:
        raise ValueError(f"Unsupported suggestion table for local rules: {table}")
    if not dry_run and batch is None:
        raise ValueError("batch is required when dry_run is false.")

    provider = provider or get_provider()
    provider_name = provider.provider_name
    fields = fields or DEFAULT_FIELDS
    created = []
    scanned = 0
    if job is not None:
        job.total_records = Drug.objects.count()
        job.status = constants.JOB_STATUS_RUNNING
        job.started_at = job.started_at or timezone.now()
        job.save(update_fields=["total_records", "status", "started_at", "updated_at"])

    for drug in Drug.objects.all().order_by("id"):
        scanned += 1
        for field_name in fields:
            if not hasattr(drug, field_name):
                continue
            value = getattr(drug, field_name)
            payloads = []
            if include_normalization:
                payloads.extend(_normalization_payloads(batch, drug, field_name, value, provider_name=provider_name))
                payloads.extend(_empty_string_payloads(batch, drug, field_name, value, provider_name=provider_name))
            if include_terminology:
                payloads.extend(_terminology_payloads(batch, drug, field_name, value, provider_name=provider_name))
            if include_translations and field_name in constants.TRANSLATABLE_FIELDS:
                payloads.extend(_translation_payloads(batch, drug, field_name, value, provider=provider))
            if _emit_payloads(payloads, created, limit=limit, risk_level=risk_level, only_safe=only_safe, dry_run=dry_run):
                return _finish_batch(batch, created, scanned, dry_run=dry_run, job=job)

        if include_medical_validation:
            payloads = [_medical_warning_payload(batch, drug, issue, provider_name=provider_name) for issue in validate_drug_record(drug)]
            if _emit_payloads(payloads, created, limit=limit, risk_level=risk_level, only_safe=only_safe, dry_run=dry_run):
                return _finish_batch(batch, created, scanned, dry_run=dry_run, job=job)

        if job is not None:
            job.processed_records = scanned
            job.suggestions_created = len(created)
            job.save(update_fields=["processed_records", "suggestions_created", "updated_at"])

    if include_duplicates:
        duplicate_payloads = _duplicate_payloads(batch, limit=limit, already_created=len(created), provider_name=provider_name)
        _emit_payloads(duplicate_payloads, created, limit=limit, risk_level=risk_level, only_safe=only_safe, dry_run=dry_run)

    return _finish_batch(batch, created, scanned, dry_run=dry_run, job=job)


def _emit_payloads(payloads, created, *, limit=None, risk_level=None, only_safe=False, dry_run=False):
    for payload in payloads:
        if not payload:
            continue
        payload_risk = payload["risk_level"]
        if only_safe and payload_risk != constants.RISK_SAFE:
            continue
        if risk_level and payload_risk != risk_level:
            continue
        if limit and len(created) >= limit:
            return True
        created.append(payload if dry_run else AIDataSuggestion.objects.create(**payload))
        if limit and len(created) >= limit:
            return True
    return False


def _normalization_payloads(batch, drug, field_name, value, *, provider_name):
    old_value = "" if value is None else str(value)
    if not old_value:
        return []

    normalized = normalize_text(old_value)
    if old_value == normalized:
        cased = standard_english_casing(old_value)
        if cased != old_value and field_name in {"name", "generic_name", "brand_name"}:
            normalized = cased
        else:
            return []

    return [_payload(
        batch=batch,
        drug=drug,
        field_name=field_name,
        old_value=old_value,
        suggested_value=normalized,
        suggestion_type=constants.SUGGESTION_TYPE_NORMALIZATION,
        reason="Normalize whitespace, punctuation spacing, English casing, digits, or Arabic/Persian character variants.",
        confidence_score=0.95,
        risk_level=constants.RISK_SAFE,
        provider=provider_name,
    )]


def _empty_string_payloads(batch, drug, field_name, value, *, provider_name):
    if value not in ("", None):
        return []
    try:
        model_field = drug._meta.get_field(field_name)
    except Exception:
        return []
    if not getattr(model_field, "null", False):
        return []
    return [_payload(
        batch=batch,
        drug=drug,
        field_name=field_name,
        old_value="",
        suggested_value="",
        suggestion_type=constants.SUGGESTION_TYPE_STANDARDIZATION,
        reason="Empty string detected on a nullable field. Suggest storing NULL instead of an empty string.",
        confidence_score=0.9,
        risk_level=constants.RISK_SAFE,
        provider=provider_name,
        metadata={"suggested_null": True},
    )]


def _terminology_payloads(batch, drug, field_name, value, *, provider_name):
    old_value = "" if value is None else str(value)
    if not old_value:
        return []
    result = check_terminology(old_value, field_name=field_name)
    if not result["has_changes"]:
        return []
    return [_payload(
        batch=batch,
        drug=drug,
        field_name=field_name,
        old_value=old_value,
        suggested_value=result["normalized"],
        suggestion_type=constants.SUGGESTION_TYPE_TERMINOLOGY,
        reason="Standardize terminology with the configured local rules map.",
        confidence_score=0.9,
        risk_level=constants.RISK_SAFE,
        provider=provider_name,
        metadata={"changes": result["changes"]},
    )]


def _translation_payloads(batch, drug, field_name, value, *, provider):
    old_value = "" if value is None else str(value)
    result = provider.suggest_translation(old_value, field_name=field_name)
    if not result:
        return []
    return [_payload(
        batch=batch,
        drug=drug,
        field_name=field_name,
        old_value=old_value,
        suggested_value=result.get("translated_value", ""),
        suggestion_type=constants.SUGGESTION_TYPE_TRANSLATION,
        reason=result.get("reason", "Rule-based English translation suggestion."),
        confidence_score=result.get("confidence_score", 0.0),
        risk_level=result.get("risk_level", constants.RISK_NEEDS_REVIEW),
        provider=provider.provider_name,
        metadata={**result.get("metadata", {}), "translation_target": "ai_data_translations"},
    )]


def _medical_warning_payload(batch, drug, issue, *, provider_name):
    return _payload(
        batch=batch,
        drug=drug,
        field_name=issue["field_name"],
        old_value=issue.get("value", str(getattr(drug, issue["field_name"], "") or "")),
        suggested_value=issue.get("value", ""),
        suggestion_type=constants.SUGGESTION_TYPE_MEDICAL_WARNING,
        reason=issue["detail"],
        confidence_score=0.65,
        risk_level=constants.RISK_NEEDS_REVIEW,
        provider=provider_name,
        metadata=issue,
    )


def _duplicate_payloads(batch, *, limit=None, already_created=0, provider_name):
    payloads = []
    for duplicate in detect_exact_duplicates():
        keeper_id = duplicate["record_ids"][0]
        for duplicate_id in duplicate["record_ids"][1:]:
            payloads.append({
                "batch": batch,
                "table_name": constants.DRUG_TABLE,
                "record_id": str(duplicate_id),
                "field_name": "__record__",
                "old_value": str(duplicate_id),
                "suggested_value": f"merge_with:{keeper_id}",
                "suggestion_type": constants.SUGGESTION_TYPE_MERGE,
                "reason": "Exact duplicate candidate detected. Manual merge review required; no automatic deletion is performed.",
                "confidence_score": 0.9,
                "risk_level": constants.RISK_RISKY,
                "status": constants.SUGGESTION_STATUS_PENDING,
                "provider": provider_name,
                "metadata": duplicate,
            })
            if limit and already_created + len(payloads) >= limit:
                return payloads
    for duplicate in detect_near_duplicates(max_pairs=50):
        payloads.append({
            "batch": batch,
            "table_name": constants.DRUG_TABLE,
            "record_id": str(duplicate["right_id"]),
            "field_name": "__record__",
            "old_value": duplicate["right_value"],
            "suggested_value": f"review_near_duplicate_with:{duplicate['left_id']}",
            "suggestion_type": constants.SUGGESTION_TYPE_DUPLICATE,
            "reason": "Near duplicate candidate detected. Manual review required; no automatic deletion is performed.",
            "confidence_score": duplicate["score"],
            "risk_level": constants.RISK_NEEDS_REVIEW,
            "status": constants.SUGGESTION_STATUS_PENDING,
            "provider": provider_name,
            "metadata": duplicate,
        })
        if limit and already_created + len(payloads) >= limit:
            return payloads
    return payloads


def _payload(
    *,
    batch,
    drug,
    field_name,
    old_value,
    suggested_value,
    suggestion_type,
    reason,
    confidence_score,
    risk_level,
    provider,
    metadata=None,
):
    return {
        "batch": batch,
        "table_name": constants.DRUG_TABLE,
        "record_id": str(drug.id),
        "field_name": field_name,
        "old_value": old_value,
        "suggested_value": suggested_value,
        "suggestion_type": suggestion_type,
        "reason": reason,
        "confidence_score": confidence_score,
        "risk_level": risk_level,
        "status": constants.SUGGESTION_STATUS_PENDING,
        "provider": provider,
        "metadata": metadata or {},
    }


def _finish_batch(batch, suggestions, scanned, *, dry_run=False, job=None):
    summary = {
        "records_scanned": scanned,
        "suggestions_generated": len(suggestions),
        "dry_run": dry_run,
        "by_type": {},
        "by_risk": {},
    }
    for suggestion in suggestions:
        suggestion_type = _suggestion_value(suggestion, "suggestion_type")
        risk_level = _suggestion_value(suggestion, "risk_level")
        summary["by_type"][suggestion_type] = summary["by_type"].get(suggestion_type, 0) + 1
        summary["by_risk"][risk_level] = summary["by_risk"].get(risk_level, 0) + 1
    if batch is not None and not dry_run:
        batch.summary = summary
        batch.status = constants.BATCH_STATUS_COMPLETED
        batch.completed_at = timezone.now()
        batch.save(update_fields=["summary", "status", "completed_at"])
    if job is not None:
        job.mark_completed(processed_records=scanned, suggestions_created=len(suggestions))
    return summary


def _suggestion_value(suggestion, name):
    if isinstance(suggestion, dict):
        return suggestion.get(name)
    return getattr(suggestion, name)
