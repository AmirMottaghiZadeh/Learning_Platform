import json
from html import escape
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.accounts.permissions import (
    platform_permission_required,
    require_request_permission,
)
from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.appliers.apply_changes import BackupUnavailable
from apps.ai_data_pipeline.audit_service import (
    DataQualityWorkflowError,
    review_suggestion,
    rollback_applied_change,
)
from apps.ai_data_pipeline.models import AIDataBatch, AIDataChangeHistory, AIDataJob, AIDataReport, AIDataSuggestion
from apps.ai_data_pipeline.reviewers.approval import review_suggestions
from apps.ai_data_pipeline.tasks import enqueue_batch_report
from apps.core.audit import audit_trail_for, verify_audit_chain
from apps.core.models import AuditEvent
from apps.drugs.models import Drug

from .step_up import step_up_required

from .forms import (
    BatchFilterForm,
    DrugDatabaseCreateForm,
    DrugDatabaseDeleteForm,
    DrugDatabaseEditForm,
    DrugDatabaseFilterForm,
    JobFilterForm,
    RuleBasedSuggestionBatchForm,
    SuggestionEditForm,
    SuggestionReviewActionForm,
    SuggestionFilterForm,
)
from .services import (
    build_batch_context,
    build_dashboard_context,
    build_record_context,
    create_drug_from_quality_center,
    create_rule_based_suggestion_batch,
    delete_drug_from_quality_center,
    drug_deletion_summary,
    DrugDeletionBlocked,
    MedicalFieldRequiresReview,
    filter_suggestions,
    filter_drugs,
    get_model_for_table,
    health_summary_snapshot,
    apply_rule_based_suggestions,
    is_rule_based_batch,
    report_csv_content,
    update_drug_from_quality_center,
)
def _staff_view(view):
    return platform_permission_required(
        "accounts.view_data_quality_center"
    )(view)


def _paginate(request, queryset, per_page=24):
    paginator = Paginator(queryset, per_page)
    page = paginator.get_page(request.GET.get("page"))
    return page, paginator


def _selected_ids_from_post(request):
    raw_ids = request.POST.getlist("selected_ids")
    if not raw_ids and request.POST.get("selected_ids"):
        raw_ids = [chunk.strip() for chunk in request.POST.get("selected_ids", "").split(",") if chunk.strip()]
    return [item for item in raw_ids if str(item).isdigit()]


def _max_count(mapping):
    return max(mapping.values(), default=1)


def _change_reason(request):
    """The operator's written justification, required for every data change."""
    return (request.POST.get("change_reason") or "").strip()


def _report_workflow_error(request, exc):
    messages.error(request, str(exc))


def _report_refusals(request, refusals):
    """Surface per-row governance refusals instead of hiding them in a total."""
    for refusal in refusals[:5]:
        messages.warning(
            request,
            f"Suggestion #{refusal['suggestion_id']} was not changed: {refusal['error']}",
        )
    if len(refusals) > 5:
        messages.warning(request, f"{len(refusals) - 5} further suggestion(s) were refused.")


@_staff_view
def dashboard(request):
    context = build_dashboard_context()
    latest_suggestions = AIDataSuggestion.objects.select_related("batch").order_by("-created_at")[:24]
    latest_batches = AIDataBatch.objects.order_by("-created_at")[:12]
    latest_jobs = AIDataJob.objects.select_related("batch").order_by("-created_at")[:12]
    latest_reports = AIDataReport.objects.select_related("batch").order_by("-created_at")[:8]
    return render(
        request,
        "data_quality_center/dashboard.html",
        {
            **context,
            "suggestion_status_max": _max_count(context["suggestion_status_counts"]),
            "suggestion_risk_max": _max_count(context["suggestion_risk_counts"]),
            "suggestion_type_max": _max_count(context["suggestion_type_counts"]),
            "problem_table_max": max((item["total"] for item in context["problem_tables"]), default=1),
            "problem_field_max": max((item["total"] for item in context["problem_fields"]), default=1),
            "latest_suggestions": latest_suggestions,
            "latest_batches": latest_batches,
            "latest_jobs": latest_jobs,
            "latest_reports": latest_reports,
            "nav_section": "dashboard",
        },
    )


@_staff_view
def batch_list(request):
    form = BatchFilterForm(request.GET or None)
    queryset = AIDataBatch.objects.order_by("-created_at").prefetch_related("jobs", "reports", "suggestions")
    if form.is_valid():
        q = form.cleaned_data.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(config__icontains=q) | Q(created_by__icontains=q) | Q(source_database__icontains=q))
        batch_type = form.cleaned_data.get("batch_type")
        status = form.cleaned_data.get("status")
        created_by = form.cleaned_data.get("created_by", "").strip()
        if batch_type:
            queryset = queryset.filter(batch_type=batch_type)
        if status:
            queryset = queryset.filter(status=status)
        if created_by:
            queryset = queryset.filter(created_by__icontains=created_by)
    page, paginator = _paginate(request, queryset, per_page=18)
    return render(
        request,
        "data_quality_center/batches/list.html",
        {
            "nav_section": "batches",
            "form": form,
            "page_obj": page,
            "paginator": paginator,
            "batches": page.object_list,
        },
    )


@_staff_view
def batch_detail(request, batch_id):
    batch = get_object_or_404(AIDataBatch.objects.prefetch_related("jobs", "reports", "suggestions", "change_history"), pk=batch_id)
    context = build_batch_context(batch)
    return render(
        request,
        "data_quality_center/batches/detail.html",
        {
            **context,
            "nav_section": "batches",
        },
    )


@_staff_view
@require_http_methods(["POST"])
def batch_generate_report(request, batch_id):
    require_request_permission(
        request,
        "accounts.review_data_quality_suggestion",
    )
    batch = get_object_or_404(AIDataBatch, pk=batch_id)
    # Report generation scans the whole corpus, so it runs on the queue rather
    # than holding a web worker for the duration.
    job = enqueue_batch_report(batch=batch, actor=request.user)
    latest_report = batch.reports.order_by("-created_at").first()
    if latest_report is not None:
        messages.success(
            request,
            f"Report generation queued for batch {batch.id} as job #{job.id}. "
            "The most recent report is shown until it finishes.",
        )
        return redirect("data_quality_center:report_detail", report_id=latest_report.id)

    messages.success(
        request,
        f"Report generation queued for batch {batch.id} as job #{job.id}.",
    )
    return redirect("data_quality_center:job_list")


@_staff_view
def batch_compare(request, batch_id):
    batch = get_object_or_404(AIDataBatch.objects.prefetch_related("jobs", "reports", "suggestions"), pk=batch_id)
    context = build_batch_context(batch)
    return render(
        request,
        "data_quality_center/batches/compare.html",
        {
            **context,
            "nav_section": "batches",
        },
    )


@_staff_view
def job_list(request):
    form = JobFilterForm(request.GET or None)
    queryset = AIDataJob.objects.select_related("batch").order_by("-created_at")
    if form.is_valid():
        q = form.cleaned_data.get("q", "").strip()
        if q:
            queryset = queryset.filter(Q(batch__config__icontains=q) | Q(error_message__icontains=q) | Q(created_by__icontains=q))
        job_type = form.cleaned_data.get("job_type")
        status = form.cleaned_data.get("status")
        provider = form.cleaned_data.get("provider")
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        if status:
            queryset = queryset.filter(status=status)
        if provider:
            queryset = queryset.filter(provider=provider)
    page, paginator = _paginate(request, queryset, per_page=24)
    return render(
        request,
        "data_quality_center/jobs/list.html",
        {
            "nav_section": "jobs",
            "form": form,
            "page_obj": page,
            "paginator": paginator,
            "jobs": page.object_list,
        },
    )


@_staff_view
@step_up_required
def suggestion_list(request):
    form = SuggestionFilterForm(request.GET or None)
    queryset = filter_suggestions(request.GET)
    active_batch = form.cleaned_data.get("batch") if form.is_valid() else None
    rule_batch_form = RuleBasedSuggestionBatchForm()
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "generate_rule_batch":
            require_request_permission(
                request,
                "accounts.review_data_quality_suggestion",
            )
            rule_batch_form = RuleBasedSuggestionBatchForm(request.POST)
            if rule_batch_form.is_valid():
                try:
                    batch, summary = create_rule_based_suggestion_batch(
                        cleaned_data=rule_batch_form.cleaned_data,
                        created_by=request.user.get_username(),
                    )
                except Exception as exc:
                    messages.error(request, f"Could not create the rule-based review package: {exc}")
                else:
                    messages.success(
                        request,
                        f"Rule-based package #{batch.id} created with "
                        f"{summary['suggestions_generated']} pending suggestion(s). No drug data was changed.",
                    )
                    return redirect(f"{request.path}?batch={batch.id}&provider={constants.PROVIDER_RULES}")
            else:
                messages.error(request, "Correct the rule-package form and try again.")
        elif action == "apply_batch":
            require_request_permission(
                request,
                "accounts.apply_data_quality_change",
            )
            _apply_all_approved_rule_suggestions(
                request,
                request.POST.get("batch_id") or request.GET.get("batch"),
                _change_reason(request),
            )
            return redirect(request.get_full_path())
        else:
            selected_ids = _selected_ids_from_post(request)
            if not selected_ids:
                messages.warning(request, "Select at least one suggestion.")
                return redirect(request.path + ("?" + request.META.get("QUERY_STRING", "") if request.META.get("QUERY_STRING") else ""))

            reviewer_notes = request.POST.get("reviewer_notes", "").strip()
            reason = _change_reason(request) or reviewer_notes
            selected_queryset = queryset.filter(id__in=selected_ids)
            try:
                if action == "approve":
                    require_request_permission(
                        request,
                        "accounts.approve_data_quality_suggestion",
                    )
                    safe_queryset = selected_queryset.filter(provider=constants.PROVIDER_RULES)
                    count, refused = review_suggestions(
                        actor=request.user,
                        reason=reason,
                        suggestion_ids=list(safe_queryset.values_list("id", flat=True)),
                        action="approve",
                        request=request,
                        skip_refused=True,
                    )
                    messages.success(request, f"Approved {count} rule-based suggestion(s).")
                    _report_refusals(request, refused)
                elif action == "reject":
                    require_request_permission(
                        request,
                        "accounts.review_data_quality_suggestion",
                    )
                    count, refused = review_suggestions(
                        actor=request.user,
                        reason=reason,
                        suggestion_ids=list(selected_queryset.values_list("id", flat=True)),
                        action="reject",
                        request=request,
                        skip_refused=True,
                    )
                    messages.success(request, f"Rejected {count} suggestion(s).")
                    _report_refusals(request, refused)
                elif action == "mark_review":
                    require_request_permission(
                        request,
                        "accounts.review_data_quality_suggestion",
                    )
                    count, refused = review_suggestions(
                        actor=request.user,
                        reason=reason,
                        suggestion_ids=list(selected_queryset.values_list("id", flat=True)),
                        action="needs_review",
                        request=request,
                        skip_refused=True,
                    )
                    messages.success(request, f"Marked {count} suggestion(s) as needs review.")
                    _report_refusals(request, refused)
                elif action == "apply_selected":
                    require_request_permission(
                        request,
                        "accounts.apply_data_quality_change",
                    )
                    _apply_selected_rule_suggestions(request, selected_queryset, reason)
                else:
                    messages.warning(request, "Unsupported bulk action.")
            except DataQualityWorkflowError as exc:
                _report_workflow_error(request, exc)
            return redirect(request.get_full_path())

    page, paginator = _paginate(request, queryset, per_page=30)
    return render(
        request,
        "data_quality_center/suggestions/list.html",
        {
            "nav_section": "suggestions",
            "form": form,
            "page_obj": page,
            "paginator": paginator,
            "suggestions": page.object_list,
            "review_action_form": SuggestionReviewActionForm(),
            "rule_batch_form": rule_batch_form,
            "active_batch": active_batch,
            "active_batch_is_rules": bool(active_batch and is_rule_based_batch(active_batch)),
        },
    )


def _apply_selected_rule_suggestions(request, selected_queryset, reason):
    if request.POST.get("apply_confirmation", "").strip() != "APPLY":
        messages.error(request, "Type APPLY to confirm applying the selected suggestions.")
        return

    selected = list(
        selected_queryset.filter(provider=constants.PROVIDER_RULES)
        .select_related("batch")
    )
    if not selected:
        messages.warning(request, "Select approved rule-based suggestions to apply.")
        return

    batch_ids = {suggestion.batch_id for suggestion in selected}
    if len(batch_ids) != 1:
        messages.error(request, "Selected suggestions must belong to one rule-based package.")
        return

    _run_apply(
        request,
        batch=selected[0].batch,
        reason=reason,
        suggestion_ids=[suggestion.id for suggestion in selected],
        label="Selected package changes",
    )


def _apply_all_approved_rule_suggestions(request, batch_id, reason):
    if request.POST.get("apply_confirmation", "").strip() != "APPLY":
        messages.error(request, "Type APPLY to confirm applying all approved suggestions in this package.")
        return
    if not str(batch_id).isdigit():
        messages.warning(request, "Filter by one rule-based package before applying all approved suggestions.")
        return
    batch = get_object_or_404(AIDataBatch, pk=batch_id)
    _run_apply(request, batch=batch, reason=reason, label=f"Package #{batch.id}")


def _run_apply(request, *, batch, reason, label, suggestion_ids=None):
    try:
        result = apply_rule_based_suggestions(
            batch=batch,
            suggestion_ids=suggestion_ids,
            actor=request.user,
            reason=reason,
            request=request,
        )
    except BackupUnavailable as exc:
        # Nothing was changed: the apply refuses to run without a way back.
        messages.error(request, f"No change was applied because a backup could not be taken: {exc}")
        return
    except (DataQualityWorkflowError, ValueError) as exc:
        messages.error(request, str(exc))
        return

    messages.success(
        request,
        f"{label} processed: {result.applied} applied, "
        f"{result.skipped} skipped, {result.failed} failed.",
    )
    if result.backup_path:
        messages.info(request, f"Backup written to {result.backup_path}.")
    for error in result.errors[:5]:
        messages.warning(
            request,
            f"Suggestion #{error['suggestion_id']}: {error['error']}",
        )


@_staff_view
@step_up_required
@require_http_methods(["GET", "POST"])
def suggestion_detail(request, suggestion_id):
    suggestion = get_object_or_404(AIDataSuggestion.objects.select_related("batch"), pk=suggestion_id)
    edit_form = SuggestionEditForm(
        initial={
            "suggested_value": suggestion.suggested_value,
            "reason": suggestion.reason,
            "confidence_score": suggestion.confidence_score,
            "risk_level": suggestion.risk_level,
            "reviewer_notes": suggestion.metadata.get("reviewer_notes", "") if suggestion.metadata else "",
        }
    )

    if request.method == "POST":
        action = request.POST.get("action")
        reason = _change_reason(request)
        try:
            if action == "edit":
                require_request_permission(
                    request,
                    "accounts.review_data_quality_suggestion",
                )
                edit_form = SuggestionEditForm(request.POST)
                if edit_form.is_valid():
                    notes = edit_form.cleaned_data.get("reviewer_notes", "").strip()
                    review_suggestion(
                        suggestion=suggestion,
                        actor=request.user,
                        action="edit",
                        reason=reason or notes,
                        edited_value=edit_form.cleaned_data.get(
                            "suggested_value", suggestion.suggested_value
                        ),
                        risk_level=edit_form.cleaned_data.get("risk_level") or None,
                        request=request,
                    )
                    messages.success(request, "Suggestion updated.")
                    return redirect("data_quality_center:suggestion_detail", suggestion_id=suggestion.id)
            elif action == "approve":
                require_request_permission(
                    request,
                    "accounts.approve_data_quality_suggestion",
                )
                review_suggestion(
                    suggestion=suggestion,
                    actor=request.user,
                    action="approve",
                    reason=reason,
                    request=request,
                )
                suggestion.refresh_from_db()
                if suggestion.is_fully_approved:
                    messages.success(request, "Suggestion approved.")
                else:
                    messages.success(
                        request,
                        "Your approval was recorded. This change is risky or medical, "
                        "so a second approver must sign off before it can be applied.",
                    )
                return redirect("data_quality_center:suggestion_detail", suggestion_id=suggestion.id)
            elif action == "apply":
                require_request_permission(
                    request,
                    "accounts.apply_data_quality_change",
                )
                if request.POST.get("apply_confirmation", "").strip() != "APPLY":
                    messages.error(request, "Type APPLY to confirm applying this approved suggestion.")
                else:
                    _run_apply(
                        request,
                        batch=suggestion.batch,
                        reason=reason,
                        suggestion_ids=[suggestion.id],
                        label="Suggestion",
                    )
                    return redirect("data_quality_center:suggestion_detail", suggestion_id=suggestion.id)
            elif action == "reject":
                require_request_permission(
                    request,
                    "accounts.review_data_quality_suggestion",
                )
                review_suggestion(
                    suggestion=suggestion,
                    actor=request.user,
                    action="reject",
                    reason=reason,
                    request=request,
                )
                messages.success(request, "Suggestion rejected.")
                return redirect("data_quality_center:suggestion_detail", suggestion_id=suggestion.id)
        except DataQualityWorkflowError as exc:
            _report_workflow_error(request, exc)

    return render(
        request,
        "data_quality_center/suggestions/detail.html",
        {
            "nav_section": "suggestions",
            "suggestion": suggestion,
            "edit_form": edit_form,
            "diff_html": suggestion.diff_html(),
            "record_url": reverse_record_url(suggestion),
            "reviewer_notes_value": (suggestion.metadata or {}).get("reviewer_notes", ""),
            "is_rule_based": suggestion.provider == constants.PROVIDER_RULES and is_rule_based_batch(suggestion.batch),
        },
    )


def reverse_record_url(suggestion):
    try:
        return f"/data-quality/records/{suggestion.table_name}/{suggestion.record_id}/"
    except Exception:
        return ""


@_staff_view
def drug_database_list(request):
    form = DrugDatabaseFilterForm(request.GET or None)
    queryset = filter_drugs(form.cleaned_data if form.is_valid() else {})
    page, paginator = _paginate(request, queryset, per_page=30)
    return render(
        request,
        "data_quality_center/database/list.html",
        {
            "nav_section": "database",
            "form": form,
            "drugs": page.object_list,
            "page_obj": page,
            "paginator": paginator,
        },
    )


@_staff_view
@step_up_required
@require_http_methods(["GET", "POST"])
def drug_database_edit(request, drug_key):
    drug = get_object_or_404(Drug, pk=drug_key)
    if request.method == "POST":
        require_request_permission(request, "accounts.manage_drug_records")
        form = DrugDatabaseEditForm(request.POST, instance=drug)
        if form.is_valid():
            try:
                updated_drug, changes = update_drug_from_quality_center(
                    drug_id=drug.drug_key,
                    cleaned_data=form.cleaned_data,
                    actor=request.user,
                    reason=_change_reason(request),
                    request=request,
                )
            except (DataQualityWorkflowError, MedicalFieldRequiresReview) as exc:
                _report_workflow_error(request, exc)
            else:
                if changes:
                    messages.success(request, f"Saved {len(changes)} database field change(s) for drug {updated_drug.pk}.")
                else:
                    messages.info(request, "No values changed.")
                return redirect("data_quality_center:drug_database_edit", drug_key=updated_drug.pk)
    else:
        form = DrugDatabaseEditForm(instance=drug)

    history = AIDataChangeHistory.objects.filter(
        table_name=constants.DRUG_TABLE,
        record_id=str(drug.pk),
    ).order_by("-applied_at")[:30]
    return render(
        request,
        "data_quality_center/database/edit.html",
        {
            "nav_section": "database",
            "drug": drug,
            "form": form,
            "history": history,
        },
    )


@_staff_view
@step_up_required
@require_http_methods(["GET", "POST"])
def drug_database_create(request):
    if request.method == "POST":
        require_request_permission(request, "accounts.manage_drug_records")
        form = DrugDatabaseCreateForm(request.POST)
        if form.is_valid():
            try:
                drug = create_drug_from_quality_center(
                    cleaned_data=form.cleaned_data,
                    actor=request.user,
                    reason=_change_reason(request),
                    request=request,
                )
            except DataQualityWorkflowError as exc:
                _report_workflow_error(request, exc)
            else:
                messages.success(request, f"Created drug {drug.pk}.")
                return redirect("data_quality_center:drug_database_edit", drug_key=drug.pk)
    else:
        form = DrugDatabaseCreateForm()
    return render(
        request,
        "data_quality_center/database/create.html",
        {
            "nav_section": "create_drug",
            "form": form,
        },
    )


@_staff_view
@step_up_required
@require_http_methods(["GET", "POST"])
def drug_database_delete(request, drug_key):
    drug = get_object_or_404(Drug, pk=drug_key)
    if request.method == "POST":
        require_request_permission(request, "accounts.manage_drug_records")
        form = DrugDatabaseDeleteForm(request.POST)
        if form.is_valid():
            try:
                summary = delete_drug_from_quality_center(
                    drug_id=drug.drug_key,
                    actor=request.user,
                    reason=_change_reason(request),
                    request=request,
                )
            except DataQualityWorkflowError as exc:
                _report_workflow_error(request, exc)
                return redirect("data_quality_center:drug_database_delete", drug_key=drug.pk)
            except DrugDeletionBlocked as exc:
                messages.error(request, str(exc))
                return redirect("data_quality_center:drug_database_edit", drug_key=drug.pk)

            messages.success(
                request,
                f"Deleted drug {drug.pk}; {summary['learning_sources']} related learning source(s) were deactivated.",
            )
            return redirect("data_quality_center:drug_database_list")
    else:
        form = DrugDatabaseDeleteForm()

    return render(
        request,
        "data_quality_center/database/delete.html",
        {
            "nav_section": "database",
            "drug": drug,
            "form": form,
            "deletion_summary": drug_deletion_summary(drug),
        },
    )


@_staff_view
def record_inspector(request, table_name, record_id):
    model = get_model_for_table(table_name)
    context = build_record_context(model, record_id)
    return render(
        request,
        "data_quality_center/records/detail.html",
        {
            **context,
            "nav_section": "records",
        },
    )


@_staff_view
def health_center(request):
    dashboard_context = build_dashboard_context()
    latest_report = (
        AIDataReport.objects.filter(report_type=constants.BATCH_TYPE_HEALTH_CHECK, format="json")
        .select_related("batch")
        .order_by("-created_at")
        .first()
    )
    summary = latest_report.content.get("health_report", {}).get("summary", {}) if latest_report else health_summary_snapshot()
    reports = AIDataReport.objects.filter(report_type=constants.BATCH_TYPE_HEALTH_CHECK).select_related("batch").order_by("-created_at")[:12]
    return render(
        request,
        "data_quality_center/health.html",
        {
            "nav_section": "health",
            "latest_report": latest_report,
            "summary": summary,
            "reports": reports,
            "trend_path": dashboard_context.get("trend_path", ""),
            "dashboard": dashboard_context,
            "issue_type_max": max(summary.get("issue_counts", {}).values(), default=1) if isinstance(summary.get("issue_counts", {}), dict) else 1,
        },
    )


@_staff_view
def report_list(request):
    queryset = AIDataReport.objects.select_related("batch").order_by("-created_at")
    batch_id = request.GET.get("batch")
    report_type = request.GET.get("report_type")
    format_name = request.GET.get("format")
    if batch_id and batch_id.isdigit():
        queryset = queryset.filter(batch_id=batch_id)
    if report_type:
        queryset = queryset.filter(report_type=report_type)
    if format_name:
        queryset = queryset.filter(format=format_name)
    page, paginator = _paginate(request, queryset, per_page=24)
    return render(
        request,
        "data_quality_center/reports/list.html",
        {
            "nav_section": "reports",
            "reports": page.object_list,
            "page_obj": page,
            "paginator": paginator,
        },
    )


@_staff_view
def report_detail(request, report_id):
    report = get_object_or_404(AIDataReport.objects.select_related("batch"), pk=report_id)
    return render(
        request,
        "data_quality_center/reports/detail.html",
        {
            "nav_section": "reports",
            "report": report,
            "raw_content": json.dumps(report.content, ensure_ascii=False, indent=2),
        },
    )


@_staff_view
def report_download(request, report_id, format):
    report = get_object_or_404(AIDataReport.objects.select_related("batch"), pk=report_id)
    format = format.lower()
    if format == "json":
        payload = json.dumps(report.content, ensure_ascii=False, indent=2)
        return HttpResponse(payload, content_type="application/json; charset=utf-8")
    if format == "csv":
        return HttpResponse(report_csv_content(report), content_type="text/csv; charset=utf-8")
    if format == "html":
        if report.path and Path(report.path).exists():
            return HttpResponse(Path(report.path).read_text(encoding="utf-8"), content_type="text/html; charset=utf-8")
        return HttpResponse(build_minimal_report_html(report), content_type="text/html; charset=utf-8")
    raise Http404("Unsupported report format.")


def build_minimal_report_html(report):
    # Report content is operator-supplied data. It is escaped before being
    # embedded, so a crafted value cannot execute in a reviewer's browser.
    payload = escape(json.dumps(report.content, ensure_ascii=False, indent=2))
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'">
<title>Report {report.id}</title>
</head>
<body><pre>{payload}</pre></body>
</html>"""


@_staff_view
def audit_trail(request):
    """Read-only view of the append-only audit log, with chain verification."""
    require_request_permission(request, "accounts.view_security_audit")

    queryset = AuditEvent.objects.select_related("actor", "reverts_event")
    entity_type = request.GET.get("entity_type", "").strip()
    entity_id = request.GET.get("entity_id", "").strip()
    action = request.GET.get("action", "").strip()
    if entity_type:
        queryset = queryset.filter(entity_type=entity_type)
    if entity_id:
        queryset = queryset.filter(entity_id=entity_id)
    if action:
        queryset = queryset.filter(action=action)

    page, paginator = _paginate(request, queryset, per_page=40)
    return render(
        request,
        "data_quality_center/audit/list.html",
        {
            "nav_section": "audit",
            "events": page.object_list,
            "page_obj": page,
            "paginator": paginator,
            "verification": verify_audit_chain(limit=settings.DATA_QUALITY_AUDIT_VERIFY_LIMIT),
            "action_choices": AuditEvent.ACTION_CHOICES,
            "filters": {
                "entity_type": entity_type,
                "entity_id": entity_id,
                "action": action,
            },
        },
    )


@_staff_view
@step_up_required
@require_http_methods(["GET", "POST"])
def change_rollback(request, history_id):
    """Undo one applied change by appending a reverting audit event."""
    history = get_object_or_404(
        AIDataChangeHistory.objects.select_related("suggestion", "audit_event", "rolled_back_by_user"),
        pk=history_id,
    )

    if request.method == "POST":
        require_request_permission(request, "accounts.apply_data_quality_change")
        if request.POST.get("rollback_confirmation", "").strip() != "ROLLBACK":
            messages.error(request, "Type ROLLBACK to confirm undoing this change.")
        else:
            try:
                event = rollback_applied_change(
                    history=history,
                    actor=request.user,
                    reason=_change_reason(request),
                    request=request,
                )
            except DataQualityWorkflowError as exc:
                _report_workflow_error(request, exc)
            else:
                messages.success(
                    request,
                    f"Change #{history.id} was rolled back and recorded as audit event #{event.sequence}.",
                )
                return redirect(
                    "data_quality_center:record_inspector",
                    table_name=history.table_name,
                    record_id=history.record_id,
                )

    return render(
        request,
        "data_quality_center/records/rollback.html",
        {
            "nav_section": "records",
            "history": history,
            "trail": audit_trail_for(history.table_name, history.record_id)[:20],
        },
    )
