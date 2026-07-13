import shutil
import subprocess
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataBatch, AIDataChangeHistory, AIDataSuggestion, AIDataTranslation


class ApplyResult:
    def __init__(self, *, applied=0, skipped=0, failed=0, backup_path=""):
        self.applied = applied
        self.skipped = skipped
        self.failed = failed
        self.backup_path = backup_path

    def as_dict(self):
        return {
            "applied": self.applied,
            "skipped": self.skipped,
            "failed": self.failed,
            "backup_path": self.backup_path,
        }


def apply_approved_suggestions(*, batch_id, applied_by="", backup_dir=None, min_confidence=0.8, include_risky=False):
    batch = AIDataBatch.objects.get(id=batch_id)
    backup_path = create_database_backup(batch_id=batch.id, backup_dir=backup_dir)
    queryset = AIDataSuggestion.objects.select_for_update().filter(
        batch=batch,
        status=constants.SUGGESTION_STATUS_APPROVED,
    ).order_by("id")

    applied = 0
    skipped = 0
    failed = 0
    with transaction.atomic():
        for suggestion in queryset:
            if suggestion.confidence_score < min_confidence:
                skipped += 1
                continue
            if suggestion.risk_level == constants.RISK_RISKY and not include_risky:
                skipped += 1
                continue
            if suggestion.suggestion_type not in constants.APPLYABLE_SUGGESTION_TYPES:
                suggestion.status = constants.SUGGESTION_STATUS_FAILED
                suggestion.metadata = {
                    **suggestion.metadata,
                    "apply_error": "Suggestion type is not auto-applicable by safety policy.",
                }
                suggestion.save(update_fields=["status", "metadata", "updated_at"])
                failed += 1
                continue
            if suggestion.suggestion_type == constants.SUGGESTION_TYPE_TRANSLATION:
                _apply_translation(suggestion, applied_by=applied_by)
            else:
                _apply_field_update(suggestion, applied_by=applied_by)
            suggestion.status = constants.SUGGESTION_STATUS_APPLIED
            suggestion.applied_at = timezone.now()
            suggestion.save(update_fields=["status", "applied_at", "updated_at"])
            applied += 1
    return ApplyResult(applied=applied, skipped=skipped, failed=failed, backup_path=backup_path)


def create_database_backup(*, batch_id, backup_dir=None):
    database = settings.DATABASES["default"]
    engine = database.get("ENGINE", "")
    backup_root = Path(backup_dir) if backup_dir else Path(settings.BASE_DIR) / "backups" / "ai_data_pipeline"
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")

    if "postgresql" in engine:
        database_url = getattr(settings, "DATABASE_URL", "")
        if not database_url:
            return ""
        if not shutil.which("pg_dump"):
            return ""
        backup_root.mkdir(parents=True, exist_ok=True)
        backup_path = backup_root / f"database.batch-{batch_id}.{timestamp}.dump"
        subprocess.run(
            ["pg_dump", database_url, "--format=custom", "--file", str(backup_path)],
            check=True,
        )
        return str(backup_path)
    return ""


def _model_for_table(table_name):
    for model in apps.get_models():
        if model._meta.db_table == table_name:
            return model
    raise ValueError(f"Unsupported table: {table_name}")


def _apply_field_update(suggestion, *, applied_by):
    allowed_fields = constants.ALLOWED_APPLY_FIELDS.get(suggestion.table_name, set())
    if suggestion.field_name not in allowed_fields:
        raise ValueError(f"Field {suggestion.table_name}.{suggestion.field_name} is not approved for automated apply.")
    model = _model_for_table(suggestion.table_name)
    instance = model.objects.select_for_update().get(pk=suggestion.record_id)
    current_value = "" if getattr(instance, suggestion.field_name) is None else str(getattr(instance, suggestion.field_name))
    if current_value != suggestion.old_value:
        raise ValueError(
            f"Current value mismatch for {suggestion.table_name}:{suggestion.record_id}:{suggestion.field_name}."
        )
    new_value = None if suggestion.metadata.get("suggested_null") else suggestion.suggested_value
    setattr(instance, suggestion.field_name, new_value)
    instance.save(update_fields=[suggestion.field_name])
    AIDataChangeHistory.objects.create(
        batch=suggestion.batch,
        suggestion=suggestion,
        table_name=suggestion.table_name,
        record_id=suggestion.record_id,
        field_name=suggestion.field_name,
        old_value=suggestion.old_value,
        new_value="" if new_value is None else str(new_value),
        reason=suggestion.reason,
        suggestion_type=suggestion.suggestion_type,
        confidence_score=suggestion.confidence_score,
        risk_level=suggestion.risk_level,
        applied_by=applied_by,
    )


def _apply_translation(suggestion, *, applied_by):
    translation, _ = AIDataTranslation.objects.update_or_create(
        table_name=suggestion.table_name,
        record_id=suggestion.record_id,
        source_field=suggestion.field_name,
        language_code="en",
        defaults={
            "batch": suggestion.batch,
            "suggestion": suggestion,
            "source_value": suggestion.old_value,
            "translated_value": suggestion.suggested_value,
            "confidence_score": suggestion.confidence_score,
        },
    )
    AIDataChangeHistory.objects.create(
        batch=suggestion.batch,
        suggestion=suggestion,
        table_name=constants.TRANSLATION_TABLE,
        record_id=str(translation.id),
        field_name="translated_value",
        old_value="",
        new_value=suggestion.suggested_value,
        reason=suggestion.reason,
        suggestion_type=suggestion.suggestion_type,
        confidence_score=suggestion.confidence_score,
        risk_level=suggestion.risk_level,
        applied_by=applied_by,
        metadata={
            "source_table": suggestion.table_name,
            "source_record_id": suggestion.record_id,
            "source_field": suggestion.field_name,
        },
    )
