import uuid
from difflib import SequenceMatcher
from html import escape

from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from . import constants


class AIDataBatch(models.Model):
    BATCH_TYPE_CHOICES = [
        (constants.BATCH_TYPE_HEALTH_CHECK, "Health check"),
        (constants.BATCH_TYPE_SUGGESTION_GENERATION, "Suggestion generation"),
        (constants.BATCH_TYPE_APPLY, "Apply"),
        (constants.BATCH_TYPE_REPORT, "Report"),
    ]
    STATUS_CHOICES = [
        (constants.BATCH_STATUS_CREATED, "Created"),
        (constants.BATCH_STATUS_RUNNING, "Running"),
        (constants.BATCH_STATUS_COMPLETED, "Completed"),
        (constants.BATCH_STATUS_FAILED, "Failed"),
    ]

    batch_uuid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    batch_type = models.CharField(max_length=40, choices=BATCH_TYPE_CHOICES)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=constants.BATCH_STATUS_CREATED)
    source_database = models.CharField(max_length=500, blank=True)
    target_scope = models.JSONField(default=dict, blank=True)
    config = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    created_by = models.CharField(max_length=150, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_data_batches"
        indexes = [
            models.Index(fields=["batch_type", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.batch_type}:{self.id}:{self.status}"

    @property
    def suggestion_status_counts(self):
        counts = {}
        for status in self.suggestions.values_list("status", flat=True):
            counts[status] = counts.get(status, 0) + 1
        return counts

    @property
    def suggestion_type_counts(self):
        counts = {}
        for suggestion_type in self.suggestions.values_list("suggestion_type", flat=True):
            counts[suggestion_type] = counts.get(suggestion_type, 0) + 1
        return counts

    @property
    def suggestion_risk_counts(self):
        counts = {}
        for risk_level in self.suggestions.values_list("risk_level", flat=True):
            counts[risk_level] = counts.get(risk_level, 0) + 1
        return counts

    @property
    def provider_modes(self):
        suggestion_providers = {provider for provider in self.suggestions.values_list("provider", flat=True) if provider}
        job_providers = {provider for provider in self.jobs.values_list("provider", flat=True) if provider}
        return sorted(suggestion_providers | job_providers)

    @property
    def batch_name(self):
        return self.config.get("batch_name") or ""

    @property
    def total_suggestions(self):
        return self.suggestions.count()

    @property
    def pending_suggestions(self):
        return self.suggestion_status_counts.get(constants.SUGGESTION_STATUS_PENDING, 0)

    @property
    def approved_suggestions(self):
        return self.suggestion_status_counts.get(constants.SUGGESTION_STATUS_APPROVED, 0)

    @property
    def rejected_suggestions(self):
        return self.suggestion_status_counts.get(constants.SUGGESTION_STATUS_REJECTED, 0)

    @property
    def applied_suggestions(self):
        return self.suggestion_status_counts.get(constants.SUGGESTION_STATUS_APPLIED, 0)

    @property
    def safe_suggestions(self):
        return self.suggestion_risk_counts.get(constants.RISK_SAFE, 0)

    @property
    def needs_review_suggestions(self):
        return self.suggestion_risk_counts.get(constants.RISK_NEEDS_REVIEW, 0)

    @property
    def risky_suggestions(self):
        return self.suggestion_risk_counts.get(constants.RISK_RISKY, 0)

    def suggestions_admin_url(self):
        url = reverse("admin:ai_data_pipeline_aidatasuggestion_changelist")
        return f"{url}?batch__id__exact={self.id}"


class AIDataJob(models.Model):
    JOB_TYPE_CHOICES = [
        (constants.JOB_TYPE_HEALTH_CHECK, "Health check"),
        (constants.JOB_TYPE_NORMALIZATION, "Normalization"),
        (constants.JOB_TYPE_TERMINOLOGY_CHECK, "Terminology check"),
        (constants.JOB_TYPE_DUPLICATE_DETECTION, "Duplicate detection"),
        (constants.JOB_TYPE_MEDICAL_VALIDATION, "Medical validation"),
        (constants.JOB_TYPE_TRANSLATION, "Translation"),
        (constants.JOB_TYPE_FULL_RULES_REVIEW, "Full rules review"),
    ]
    STATUS_CHOICES = [
        (constants.JOB_STATUS_PENDING, "Pending"),
        (constants.JOB_STATUS_RUNNING, "Running"),
        (constants.JOB_STATUS_COMPLETED, "Completed"),
        (constants.JOB_STATUS_FAILED, "Failed"),
        (constants.JOB_STATUS_CANCELLED, "Cancelled"),
    ]

    batch = models.ForeignKey(AIDataBatch, on_delete=models.CASCADE, related_name="jobs")
    job_type = models.CharField(max_length=80, choices=JOB_TYPE_CHOICES)
    provider = models.CharField(max_length=80, default=constants.PROVIDER_RULES)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=constants.JOB_STATUS_PENDING)
    parameters_json = models.JSONField(default=dict, blank=True)
    total_records = models.PositiveIntegerField(default=0)
    processed_records = models.PositiveIntegerField(default=0)
    suggestions_created = models.PositiveIntegerField(default=0)
    errors_count = models.PositiveIntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.CharField(max_length=150, blank=True)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_data_jobs"
        indexes = [
            models.Index(fields=["batch", "status"]),
            models.Index(fields=["job_type", "provider"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.job_type}:{self.id}:{self.status}"

    @property
    def progress_percent(self):
        if not self.total_records:
            return 0
        return round((self.processed_records / self.total_records) * 100, 1)

    def mark_running(self):
        self.status = constants.JOB_STATUS_RUNNING
        self.started_at = timezone.now()
        self.save(update_fields=["status", "started_at", "updated_at"])

    def mark_completed(self, *, processed_records=None, suggestions_created=None):
        self.status = constants.JOB_STATUS_COMPLETED
        if processed_records is not None:
            self.processed_records = processed_records
        if suggestions_created is not None:
            self.suggestions_created = suggestions_created
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "processed_records", "suggestions_created", "completed_at", "updated_at"])

    def mark_failed(self, error_message):
        self.status = constants.JOB_STATUS_FAILED
        self.errors_count = self.errors_count + 1
        self.error_message = str(error_message)
        self.completed_at = timezone.now()
        self.save(update_fields=["status", "errors_count", "error_message", "completed_at", "updated_at"])

    def clean(self):
        errors = {}
        self.provider = constants.PROVIDER_ALIASES.get(self.provider, self.provider)
        if self.provider not in constants.PROVIDER_CHOICES:
            errors["provider"] = "Unsupported provider."
        if self.processed_records > self.total_records and self.total_records:
            errors["processed_records"] = "Processed records cannot exceed total records."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AIDataSuggestion(models.Model):
    STATUS_CHOICES = [
        (constants.SUGGESTION_STATUS_PENDING, "Pending"),
        (constants.SUGGESTION_STATUS_APPROVED, "Approved"),
        (constants.SUGGESTION_STATUS_REJECTED, "Rejected"),
        (constants.SUGGESTION_STATUS_EDITED, "Edited"),
        (constants.SUGGESTION_STATUS_APPLIED, "Applied"),
        (constants.SUGGESTION_STATUS_FAILED, "Failed"),
    ]
    RISK_CHOICES = [
        (constants.RISK_SAFE, "Safe"),
        (constants.RISK_NEEDS_REVIEW, "Needs review"),
        (constants.RISK_RISKY, "Risky"),
    ]

    batch = models.ForeignKey(AIDataBatch, on_delete=models.CASCADE, related_name="suggestions")
    table_name = models.CharField(max_length=160)
    record_id = models.CharField(max_length=80)
    field_name = models.CharField(max_length=160)
    old_value = models.TextField(blank=True)
    suggested_value = models.TextField(blank=True)
    suggestion_type = models.CharField(max_length=80)
    reason = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=40, choices=RISK_CHOICES, default=constants.RISK_NEEDS_REVIEW)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default=constants.SUGGESTION_STATUS_PENDING)
    provider = models.CharField(max_length=80, default=constants.PROVIDER_RULES)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=150, blank=True)
    applied_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_data_suggestions"
        indexes = [
            models.Index(fields=["batch", "status"]),
            models.Index(fields=["table_name", "record_id"]),
            models.Index(fields=["suggestion_type", "risk_level"]),
        ]

    def __str__(self):
        return f"{self.table_name}:{self.record_id}:{self.field_name}:{self.status}"

    @property
    def is_locked(self):
        return self.status == constants.SUGGESTION_STATUS_APPLIED or self.applied_at is not None

    @property
    def is_auto_applicable(self):
        return (
            self.suggestion_type in constants.APPLYABLE_SUGGESTION_TYPES
            and self.table_name in constants.ALLOWED_APPLY_FIELDS
            and self.field_name in constants.ALLOWED_APPLY_FIELDS.get(self.table_name, set())
        )

    @property
    def text_diff(self):
        old_value = self.old_value or ""
        suggested_value = self.suggested_value or ""
        matcher = SequenceMatcher(None, old_value, suggested_value)
        old_parts = []
        new_parts = []
        for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
            old_chunk = old_value[old_start:old_end]
            new_chunk = suggested_value[new_start:new_end]
            if tag == "equal":
                old_parts.append(old_chunk)
                new_parts.append(new_chunk)
            elif tag == "delete":
                old_parts.append(f"[-{old_chunk}-]")
            elif tag == "insert":
                new_parts.append(f"[+{new_chunk}+]")
            elif tag == "replace":
                old_parts.append(f"[-{old_chunk}-]")
                new_parts.append(f"[+{new_chunk}+]")
        return {"old": "".join(old_parts), "new": "".join(new_parts)}

    def diff_html(self):
        old_html, new_html = self._highlighted_diff_html()
        return format_html(
            "<div style='display:grid; grid-template-columns:1fr 1fr; gap:12px; direction:auto'>"
            "<div><strong>Old</strong><pre style='white-space:pre-wrap; background:#fff3f3; padding:10px'>{}</pre></div>"
            "<div><strong>Suggested</strong><pre style='white-space:pre-wrap; background:#f1fff4; padding:10px'>{}</pre></div>"
            "</div>",
            mark_safe(old_html),
            mark_safe(new_html),
        )

    def _highlighted_diff_html(self):
        old_value = self.old_value or ""
        suggested_value = self.suggested_value or ""
        matcher = SequenceMatcher(None, old_value, suggested_value)
        old_parts = []
        new_parts = []
        for tag, old_start, old_end, new_start, new_end in matcher.get_opcodes():
            old_chunk = escape(old_value[old_start:old_end])
            new_chunk = escape(suggested_value[new_start:new_end])
            if tag == "equal":
                old_parts.append(old_chunk)
                new_parts.append(new_chunk)
            elif tag == "delete":
                old_parts.append(f"<span style='background:#ffd9d9; text-decoration:line-through'>{old_chunk}</span>")
            elif tag == "insert":
                new_parts.append(f"<span style='background:#cfffda'>{new_chunk}</span>")
            elif tag == "replace":
                old_parts.append(f"<span style='background:#ffd9d9; text-decoration:line-through'>{old_chunk}</span>")
                new_parts.append(f"<span style='background:#cfffda'>{new_chunk}</span>")
        return "".join(old_parts), "".join(new_parts)

    def clean(self):
        errors = {}
        self.provider = constants.PROVIDER_ALIASES.get(self.provider, self.provider)
        if not 0 <= float(self.confidence_score) <= 1:
            errors["confidence_score"] = "Confidence score must be between 0 and 1."

        if self.record_id and not str(self.record_id).isdigit():
            errors["record_id"] = "Record id must be a numeric primary key."

        if self.provider not in constants.PROVIDER_CHOICES:
            errors["provider"] = "Unsupported provider."

        allowed_fields = constants.ALLOWED_APPLY_FIELDS.get(self.table_name)
        non_field_suggestion = self.field_name == "__record__"
        if self.table_name not in constants.ALLOWED_REVIEW_TABLES:
            errors["table_name"] = "Unsupported table name."
        elif self.suggestion_type in constants.APPLYABLE_SUGGESTION_TYPES:
            if not allowed_fields:
                errors["table_name"] = "This table is not allowed for automatic apply."
            elif non_field_suggestion:
                errors["field_name"] = "Record-level suggestions cannot be automatically applied."
            elif self.field_name not in allowed_fields:
                errors["field_name"] = "This field is not allowed for automatic apply."
        elif allowed_fields and not non_field_suggestion and self.field_name not in allowed_fields:
            errors["field_name"] = "Unsupported field name."

        if self.pk:
            previous = AIDataSuggestion.objects.filter(pk=self.pk).first()
            if previous and previous.status == constants.SUGGESTION_STATUS_APPLIED and (
                previous.table_name != self.table_name
                or previous.record_id != self.record_id
                or previous.field_name != self.field_name
                or previous.old_value != self.old_value
                or previous.suggested_value != self.suggested_value
                or previous.status != self.status
            ):
                raise ValidationError("Applied suggestions are locked and cannot be edited.")

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AIDataChangeHistory(models.Model):
    batch = models.ForeignKey(AIDataBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="change_history")
    suggestion = models.ForeignKey(AIDataSuggestion, on_delete=models.SET_NULL, null=True, blank=True, related_name="change_history")
    table_name = models.CharField(max_length=160)
    record_id = models.CharField(max_length=80)
    field_name = models.CharField(max_length=160)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    reason = models.TextField(blank=True)
    suggestion_type = models.CharField(max_length=80, blank=True)
    confidence_score = models.FloatField(default=0.0)
    risk_level = models.CharField(max_length=40, blank=True)
    applied_by = models.CharField(max_length=150, blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    rollback_batch_id = models.CharField(max_length=80, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "ai_data_change_history"
        indexes = [
            models.Index(fields=["batch", "applied_at"]),
            models.Index(fields=["table_name", "record_id"]),
        ]

    def clean(self):
        errors = {}
        if self.record_id and not str(self.record_id).isdigit():
            errors["record_id"] = "Record id must be a numeric primary key."
        if self.table_name not in {constants.TRANSLATION_TABLE, *constants.ALLOWED_APPLY_FIELDS.keys()}:
            errors["table_name"] = "Unsupported table name."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class AIDataReport(models.Model):
    batch = models.ForeignKey(AIDataBatch, on_delete=models.CASCADE, related_name="reports")
    report_type = models.CharField(max_length=80)
    format = models.CharField(max_length=20, default="json")
    path = models.CharField(max_length=500, blank=True)
    content = models.JSONField(default=dict, blank=True)
    summary = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "ai_data_reports"
        indexes = [
            models.Index(fields=["batch", "report_type"]),
            models.Index(fields=["created_at"]),
        ]

    @property
    def total_records_scanned(self):
        return self.summary.get("total_records_scanned") or self.content.get("health_report", {}).get("summary", {}).get("total_records_scanned", 0)

    @property
    def issues_found(self):
        return self.summary.get("issue_count") or self.content.get("health_report", {}).get("summary", {}).get("issue_count", 0)

    @property
    def duplicate_candidates(self):
        health_summary = self.content.get("health_report", {}).get("summary", {}) or self.summary
        return (
            health_summary.get("exact_duplicate_groups", 0)
            + health_summary.get("near_duplicate_pairs", 0)
        )

    @property
    def suggestion_counts(self):
        suggestions = self.content.get("suggestions", {})
        return {
            "translation": suggestions.get("by_type", {}).get(constants.SUGGESTION_TYPE_TRANSLATION, 0),
            "normalization": suggestions.get("by_type", {}).get(constants.SUGGESTION_TYPE_NORMALIZATION, 0),
            "medical_warning": suggestions.get("by_type", {}).get(constants.SUGGESTION_TYPE_MEDICAL_WARNING, 0),
            "risky": suggestions.get("by_risk", {}).get(constants.RISK_RISKY, 0),
            "pending": suggestions.get("by_status", {}).get(constants.SUGGESTION_STATUS_PENDING, 0),
            "approved": suggestions.get("approved", 0),
            "rejected": suggestions.get("rejected", 0),
            "applied": suggestions.get("applied", 0),
        }


class AIDataTranslation(models.Model):
    batch = models.ForeignKey(AIDataBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="translations")
    suggestion = models.ForeignKey(AIDataSuggestion, on_delete=models.SET_NULL, null=True, blank=True, related_name="translations")
    table_name = models.CharField(max_length=160)
    record_id = models.CharField(max_length=80)
    source_field = models.CharField(max_length=160)
    source_value = models.TextField(blank=True)
    language_code = models.CharField(max_length=20, default="en")
    translated_value = models.TextField(blank=True)
    confidence_score = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "ai_data_translations"
        constraints = [
            models.UniqueConstraint(
                fields=["table_name", "record_id", "source_field", "language_code"],
                name="unique_ai_translation_target",
            )
        ]
        indexes = [
            models.Index(fields=["table_name", "record_id"]),
            models.Index(fields=["language_code"]),
        ]

    def clean(self):
        errors = {}
        if self.record_id and not str(self.record_id).isdigit():
            errors["record_id"] = "Record id must be a numeric primary key."
        if self.table_name not in constants.ALLOWED_APPLY_FIELDS:
            errors["table_name"] = "Unsupported source table for translation."
        if self.source_field not in constants.ALLOWED_APPLY_FIELDS.get(self.table_name, set()):
            errors["source_field"] = "Unsupported source field for translation."
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)
