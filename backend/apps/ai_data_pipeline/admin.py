from django.contrib import admin, messages
from django.db import transaction
from django.utils import timezone
from django.utils.html import format_html

from . import constants
from .models import (
    AIDataBatch,
    AIDataChangeHistory,
    AIDataJob,
    AIDataReport,
    AIDataSuggestion,
    AIDataTranslation,
)


def short_text(value, *, limit=120):
    text = str(value or "")
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def formatted_text(value):
    return format_html(
        "<div style='max-width:520px; white-space:pre-wrap; direction:auto; line-height:1.55'>{}</div>",
        value or "",
    )


def badge(value, *, color, background):
    return format_html(
        "<span style='display:inline-block; padding:2px 8px; border-radius:999px; color:{}; background:{}; font-weight:600'>{}</span>",
        color,
        background,
        value,
    )


class AIDataSuggestionInline(admin.TabularInline):
    model = AIDataSuggestion
    extra = 0
    can_delete = False
    fields = (
        "id",
        "status",
        "risk_level",
        "suggestion_type",
        "provider",
        "table_name",
        "record_id",
        "field_name",
        "confidence_score",
        "old_value_preview",
        "suggested_value_preview",
    )
    readonly_fields = fields
    show_change_link = True

    def old_value_preview(self, obj):
        return short_text(obj.old_value, limit=80)

    def suggested_value_preview(self, obj):
        return short_text(obj.suggested_value, limit=80)


class AIDataReportInline(admin.TabularInline):
    model = AIDataReport
    extra = 0
    can_delete = False
    fields = (
        "id",
        "report_type",
        "format",
        "path_display",
        "issues_found",
        "duplicate_candidates",
        "created_at",
    )
    readonly_fields = fields
    show_change_link = True

    def path_display(self, obj):
        return obj.path or "-"


class AIDataJobInline(admin.TabularInline):
    model = AIDataJob
    extra = 0
    can_delete = False
    fields = (
        "id",
        "job_type",
        "provider",
        "status",
        "progress_percent",
        "processed_records",
        "total_records",
        "suggestions_created",
        "errors_count",
        "started_at",
        "completed_at",
    )
    readonly_fields = fields
    show_change_link = True


class AIDataChangeHistoryInline(admin.TabularInline):
    model = AIDataChangeHistory
    extra = 0
    can_delete = False
    fields = ("id", "table_name", "record_id", "field_name", "applied_by", "applied_at")
    readonly_fields = fields
    show_change_link = True


@admin.register(AIDataBatch)
class AIDataBatchAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "batch_type",
        "status",
        "batch_name_display",
        "provider_mode_summary",
        "created_by",
        "created_at",
        "completed_at",
        "total_suggestions",
        "pending_suggestions",
        "approved_suggestions",
        "rejected_suggestions",
        "applied_suggestions",
        "safe_suggestions",
        "needs_review_suggestions",
        "risky_suggestions",
        "suggestions_link",
    )
    list_filter = ("batch_type", "status", "created_by")
    search_fields = ("id", "batch_uuid", "created_by", "source_database")
    readonly_fields = (
        "batch_uuid",
        "created_at",
        "started_at",
        "completed_at",
        "batch_name_display",
        "suggestion_status_summary",
        "suggestion_type_summary",
        "suggestion_risk_summary",
        "provider_mode_summary",
        "total_suggestions",
        "pending_suggestions",
        "approved_suggestions",
        "rejected_suggestions",
        "applied_suggestions",
        "safe_suggestions",
        "needs_review_suggestions",
        "risky_suggestions",
        "suggestions_link",
        "report_summary_preview",
    )
    fieldsets = (
        ("Batch", {"fields": ("batch_uuid", "batch_type", "status", "batch_name_display", "created_by")}),
        ("Runtime", {"fields": ("source_database", "started_at", "completed_at", "created_at", "error_message")}),
        ("Scope / Config", {"fields": ("target_scope", "config")}),
        (
            "Review Summary",
            {
                "fields": (
                    "summary",
                    "suggestion_status_summary",
                    "suggestion_type_summary",
                    "suggestion_risk_summary",
                    "provider_mode_summary",
                    "total_suggestions",
                    "pending_suggestions",
                    "approved_suggestions",
                    "rejected_suggestions",
                    "applied_suggestions",
                    "safe_suggestions",
                    "needs_review_suggestions",
                    "risky_suggestions",
                    "suggestions_link",
                    "report_summary_preview",
                )
            },
        ),
    )
    inlines = (AIDataJobInline, AIDataSuggestionInline, AIDataReportInline, AIDataChangeHistoryInline)

    def suggestion_status_summary(self, obj):
        return obj.suggestion_status_counts

    def suggestion_type_summary(self, obj):
        return obj.suggestion_type_counts

    def suggestion_risk_summary(self, obj):
        return obj.suggestion_risk_counts

    def provider_mode_summary(self, obj):
        providers = obj.provider_modes
        return ", ".join(providers) if providers else "-"

    def batch_name_display(self, obj):
        return obj.config.get("batch_name") or "-"

    def suggestions_link(self, obj):
        if not obj.pk:
            return "-"
        return format_html("<a href='{}'>Open related suggestions</a>", obj.suggestions_admin_url())

    def report_summary_preview(self, obj):
        latest_report = obj.reports.order_by("-created_at").first()
        if not latest_report:
            return "-"
        return latest_report.summary or latest_report.content.get("summary", {})


@admin.register(AIDataSuggestion)
class AIDataSuggestionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "batch",
        "status_badge",
        "risk_badge",
        "provider",
        "suggestion_type",
        "table_name",
        "record_id",
        "field_name",
        "confidence_score",
        "old_value_short",
        "suggested_value_short",
        "reviewed_by",
        "applied_at",
    )
    list_filter = ("batch", "status", "risk_level", "suggestion_type", "table_name", "field_name", "provider")
    search_fields = (
        "table_name",
        "record_id",
        "field_name",
        "old_value",
        "suggested_value",
        "reason",
    )
    actions = (
        "approve_selected_suggestions",
        "reject_selected_suggestions",
        "mark_selected_needs_review",
    )
    readonly_fields = (
        "created_at",
        "updated_at",
        "reviewed_at",
        "applied_at",
        "old_value_display",
        "suggested_value_display",
        "diff_display",
        "status_badge",
        "risk_badge",
        "is_auto_applicable",
    )
    fieldsets = (
        (
            "Target",
            {"fields": ("batch", "table_name", "record_id", "field_name", "is_auto_applicable")},
        ),
        (
            "Suggestion",
            {
                "fields": (
                    "status_badge",
                    "risk_badge",
                    "old_value_display",
                    "suggested_value_display",
                    "diff_display",
                    "old_value",
                    "suggested_value",
                    "suggestion_type",
                    "reason",
                    "confidence_score",
                    "risk_level",
                    "status",
                    "provider",
                    "metadata",
                )
            },
        ),
        (
            "Review / Apply",
            {"fields": ("reviewed_at", "reviewed_by", "applied_at", "created_at", "updated_at")},
        ),
    )

    def get_readonly_fields(self, request, obj=None):
        fields = list(super().get_readonly_fields(request, obj))
        if obj:
            fields.extend(["batch", "table_name", "record_id", "field_name", "old_value", "provider"])
        if obj and obj.status == constants.SUGGESTION_STATUS_APPLIED:
            fields.extend(
                [
                    "suggested_value",
                    "suggestion_type",
                    "reason",
                    "confidence_score",
                    "risk_level",
                    "status",
                    "provider",
                    "metadata",
                    "reviewed_by",
                ]
            )
        return tuple(dict.fromkeys(fields))

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = AIDataSuggestion.objects.filter(pk=obj.pk).values_list("status", flat=True).first()
        if previous_status == constants.SUGGESTION_STATUS_APPLIED:
            messages.error(request, "Applied suggestions are locked and cannot be edited.")
            return
        return super().save_model(request, obj, form, change)

    def old_value_short(self, obj):
        return short_text(obj.old_value, limit=70)

    def suggested_value_short(self, obj):
        return short_text(obj.suggested_value, limit=70)

    def old_value_display(self, obj):
        return formatted_text(obj.old_value)

    def suggested_value_display(self, obj):
        return formatted_text(obj.suggested_value)

    def diff_display(self, obj):
        if not obj:
            return "-"
        return obj.diff_html()

    def status_badge(self, obj):
        if not obj:
            return "-"
        colors = {
            constants.SUGGESTION_STATUS_PENDING: ("#493b13", "#fff3c4"),
            constants.SUGGESTION_STATUS_APPROVED: ("#174d2b", "#dff7e8"),
            constants.SUGGESTION_STATUS_REJECTED: ("#711d1d", "#ffe1e1"),
            constants.SUGGESTION_STATUS_EDITED: ("#46306c", "#ede4ff"),
            constants.SUGGESTION_STATUS_APPLIED: ("#1d405f", "#dcefff"),
            constants.SUGGESTION_STATUS_FAILED: ("#711d1d", "#ffe1e1"),
        }
        color, background = colors.get(obj.status, ("#222", "#eee"))
        return badge(obj.status, color=color, background=background)

    def risk_badge(self, obj):
        if not obj:
            return "-"
        colors = {
            constants.RISK_SAFE: ("#174d2b", "#dff7e8"),
            constants.RISK_NEEDS_REVIEW: ("#493b13", "#fff3c4"),
            constants.RISK_RISKY: ("#711d1d", "#ffe1e1"),
        }
        color, background = colors.get(obj.risk_level, ("#222", "#eee"))
        return badge(obj.risk_level, color=color, background=background)

    @admin.action(description="Approve selected suggestions")
    def approve_selected_suggestions(self, request, queryset):
        updated = self._review_queryset(
            queryset,
            status=constants.SUGGESTION_STATUS_APPROVED,
            reviewed_by=request.user.get_username() if request.user.is_authenticated else "admin",
            allow_statuses={
                constants.SUGGESTION_STATUS_PENDING,
                constants.SUGGESTION_STATUS_EDITED,
                constants.SUGGESTION_STATUS_REJECTED,
                constants.SUGGESTION_STATUS_FAILED,
            },
        )
        messages.success(request, f"Approved suggestions: {updated}")

    @admin.action(description="Reject selected suggestions")
    def reject_selected_suggestions(self, request, queryset):
        updated = self._review_queryset(
            queryset,
            status=constants.SUGGESTION_STATUS_REJECTED,
            reviewed_by=request.user.get_username() if request.user.is_authenticated else "admin",
            allow_statuses={
                constants.SUGGESTION_STATUS_PENDING,
                constants.SUGGESTION_STATUS_APPROVED,
                constants.SUGGESTION_STATUS_EDITED,
                constants.SUGGESTION_STATUS_FAILED,
            },
        )
        messages.success(request, f"Rejected suggestions: {updated}")

    @admin.action(description="Mark selected suggestions as needs review")
    def mark_selected_needs_review(self, request, queryset):
        now = timezone.now()
        updated = 0
        username = request.user.get_username() if request.user.is_authenticated else "admin"
        with transaction.atomic():
            for suggestion in queryset.select_for_update().exclude(status=constants.SUGGESTION_STATUS_APPLIED):
                suggestion.risk_level = constants.RISK_NEEDS_REVIEW
                suggestion.status = constants.SUGGESTION_STATUS_PENDING
                suggestion.reviewed_by = username
                suggestion.reviewed_at = now
                suggestion.save(update_fields=["risk_level", "status", "reviewed_by", "reviewed_at", "updated_at"])
                updated += 1
        messages.success(request, f"Marked as needs review: {updated}")

    def _review_queryset(self, queryset, *, status, reviewed_by, allow_statuses):
        now = timezone.now()
        updated = 0
        with transaction.atomic():
            for suggestion in queryset.select_for_update().filter(status__in=allow_statuses):
                suggestion.status = status
                suggestion.reviewed_by = reviewed_by
                suggestion.reviewed_at = now
                suggestion.save(update_fields=["status", "reviewed_by", "reviewed_at", "updated_at"])
                updated += 1
        return updated


@admin.register(AIDataJob)
class AIDataJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "batch",
        "job_type",
        "provider",
        "status",
        "progress_percent",
        "processed_records",
        "total_records",
        "suggestions_created",
        "errors_count",
        "created_by",
        "started_at",
        "completed_at",
    )
    list_filter = ("job_type", "provider", "status", "created_by")
    search_fields = ("created_by", "error_message")
    readonly_fields = [field.name for field in AIDataJob._meta.fields] + ["progress_percent"]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AIDataChangeHistory)
class AIDataChangeHistoryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "batch",
        "table_name",
        "record_id",
        "field_name",
        "suggestion_type",
        "risk_level",
        "applied_by",
        "applied_at",
    )
    list_filter = ("table_name", "suggestion_type", "risk_level", "applied_by")
    search_fields = ("record_id", "field_name", "old_value", "new_value", "reason")
    readonly_fields = [field.name for field in AIDataChangeHistory._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AIDataReport)
class AIDataReportAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "batch",
        "report_type",
        "format",
        "path_display",
        "total_records_scanned",
        "issues_found",
        "duplicate_candidates",
        "translation_suggestions",
        "normalization_suggestions",
        "medical_validation_warnings",
        "risky_suggestions",
        "pending_suggestions",
        "approved_suggestions",
        "rejected_suggestions",
        "applied_suggestions",
        "created_at",
    )
    list_filter = ("report_type", "format", "batch")
    search_fields = ("path", "report_type")
    readonly_fields = (
        "batch",
        "report_type",
        "format",
        "path",
        "path_display",
        "content",
        "summary",
        "total_records_scanned",
        "issues_found",
        "duplicate_candidates",
        "translation_suggestions",
        "normalization_suggestions",
        "medical_validation_warnings",
        "risky_suggestions",
        "pending_suggestions",
        "approved_suggestions",
        "rejected_suggestions",
        "applied_suggestions",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def path_display(self, obj):
        if not obj.path:
            return "-"
        if obj.path.startswith(("http://", "https://")):
            return format_html("<a href='{}' target='_blank' rel='noopener noreferrer'>{}</a>", obj.path, obj.path)
        return obj.path

    def translation_suggestions(self, obj):
        return obj.suggestion_counts["translation"]

    def normalization_suggestions(self, obj):
        return obj.suggestion_counts["normalization"]

    def medical_validation_warnings(self, obj):
        return obj.suggestion_counts["medical_warning"]

    def risky_suggestions(self, obj):
        return obj.suggestion_counts["risky"]

    def pending_suggestions(self, obj):
        return obj.suggestion_counts["pending"]

    def approved_suggestions(self, obj):
        return obj.suggestion_counts["approved"]

    def rejected_suggestions(self, obj):
        return obj.suggestion_counts["rejected"]

    def applied_suggestions(self, obj):
        return obj.suggestion_counts["applied"]


@admin.register(AIDataTranslation)
class AIDataTranslationAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "table_name",
        "record_id",
        "source_field",
        "language_code",
        "confidence_score",
        "updated_at",
    )
    list_filter = ("table_name", "source_field", "language_code")
    search_fields = ("record_id", "source_field", "source_value", "translated_value")
    readonly_fields = ("created_at", "updated_at", "source_value_display", "translated_value_display")

    def source_value_display(self, obj):
        return formatted_text(obj.source_value)

    def translated_value_display(self, obj):
        return formatted_text(obj.translated_value)
