import json
from pathlib import Path

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob, AIDataReport, AIDataSuggestion
from apps.ai_data_pipeline.reports.report_generator import build_batch_report, write_reports
from apps.ai_data_pipeline.reviewers.approval import review_suggestions

from .forms import BatchFilterForm, JobFilterForm, SuggestionEditForm, SuggestionReviewActionForm, SuggestionFilterForm
from .services import (
    build_batch_context,
    build_dashboard_context,
    build_record_context,
    filter_suggestions,
    get_model_for_table,
    health_summary_snapshot,
    report_csv_content,
)


def _staff_view(view):
    return staff_member_required(view)


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
    batch = get_object_or_404(AIDataBatch, pk=batch_id)
    health_report = None
    if batch.batch_type == constants.BATCH_TYPE_HEALTH_CHECK and batch.summary:
        health_report = {"summary": batch.summary}
    report = build_batch_report(batch, health_report=health_report)
    paths = write_reports(batch, report=report)
    batch.summary = batch.summary or report.get("summary", {})
    batch.save(update_fields=["summary"])
    messages.success(request, f"Report generated for batch {batch.id}.")
    return redirect("data_quality_center:report_detail", report_id=batch.reports.order_by("-created_at").first().id)


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
def suggestion_list(request):
    form = SuggestionFilterForm(request.GET or None)
    queryset = filter_suggestions(request.GET)
    if request.method == "POST":
        action = request.POST.get("action")
        selected_ids = _selected_ids_from_post(request)
        if not selected_ids:
            messages.warning(request, "Select at least one suggestion.")
            return redirect(request.path + ("?" + request.META.get("QUERY_STRING", "") if request.META.get("QUERY_STRING") else ""))

        reviewer_notes = request.POST.get("reviewer_notes", "").strip()
        if action == "approve":
            queryset = queryset.filter(id__in=selected_ids)
            safe_queryset = queryset.filter(risk_level=constants.RISK_SAFE)
            count = review_suggestions(
                suggestion_ids=list(safe_queryset.values_list("id", flat=True)),
                action="approve",
                reviewed_by=request.user.get_username(),
            )
            messages.success(request, f"Approved {count} safe suggestions.")
        elif action == "reject":
            count = review_suggestions(
                suggestion_ids=selected_ids,
                action="reject",
                reviewed_by=request.user.get_username(),
            )
            messages.success(request, f"Rejected {count} suggestions.")
        elif action == "mark_review":
            with transaction.atomic():
                updated = AIDataSuggestion.objects.select_for_update().filter(id__in=selected_ids).exclude(status=constants.SUGGESTION_STATUS_APPLIED)
                for suggestion in updated:
                    suggestion.status = constants.SUGGESTION_STATUS_PENDING
                    suggestion.risk_level = constants.RISK_NEEDS_REVIEW
                    suggestion.reviewed_by = request.user.get_username()
                    suggestion.reviewed_at = timezone.now()
                    if reviewer_notes:
                        suggestion.metadata = dict(suggestion.metadata or {})
                        suggestion.metadata["reviewer_notes"] = reviewer_notes
                    suggestion.save(update_fields=["status", "risk_level", "reviewed_by", "reviewed_at", "metadata", "updated_at"])
                messages.success(request, f"Marked {updated.count()} suggestions as needs review.")
        else:
            messages.warning(request, "Unsupported bulk action.")
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
        },
    )


@_staff_view
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
        if action == "edit":
            edit_form = SuggestionEditForm(request.POST)
            if edit_form.is_valid():
                suggestion.suggested_value = edit_form.cleaned_data.get("suggested_value", suggestion.suggested_value)
                suggestion.reason = edit_form.cleaned_data.get("reason", suggestion.reason)
                if edit_form.cleaned_data.get("confidence_score") is not None:
                    suggestion.confidence_score = edit_form.cleaned_data["confidence_score"]
                if edit_form.cleaned_data.get("risk_level"):
                    suggestion.risk_level = edit_form.cleaned_data["risk_level"]
                notes = edit_form.cleaned_data.get("reviewer_notes", "").strip()
                suggestion.metadata = dict(suggestion.metadata or {})
                if notes:
                    suggestion.metadata["reviewer_notes"] = notes
                suggestion.status = constants.SUGGESTION_STATUS_EDITED
                suggestion.reviewed_by = request.user.get_username()
                suggestion.reviewed_at = timezone.now()
                suggestion.save()
                messages.success(request, "Suggestion updated.")
                return redirect("data_quality_center:suggestion_detail", suggestion_id=suggestion.id)
        elif action == "approve":
            if suggestion.status != constants.SUGGESTION_STATUS_APPLIED:
                review_suggestions(suggestion_ids=[suggestion.id], action="approve", reviewed_by=request.user.get_username())
                messages.success(request, "Suggestion approved.")
                return redirect("data_quality_center:suggestion_detail", suggestion_id=suggestion.id)
        elif action == "reject":
            if suggestion.status != constants.SUGGESTION_STATUS_APPLIED:
                review_suggestions(suggestion_ids=[suggestion.id], action="reject", reviewed_by=request.user.get_username())
                messages.success(request, "Suggestion rejected.")
                return redirect("data_quality_center:suggestion_detail", suggestion_id=suggestion.id)

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
        },
    )


def reverse_record_url(suggestion):
    try:
        return f"/data-quality/records/{suggestion.table_name}/{suggestion.record_id}/"
    except Exception:
        return ""


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
    return f"""<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><title>Report {report.id}</title></head>
<body><pre>{json.dumps(report.content, ensure_ascii=False, indent=2)}</pre></body>
</html>"""
