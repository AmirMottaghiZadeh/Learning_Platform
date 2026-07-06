import json
from collections import Counter
from html import escape
from pathlib import Path

from django.conf import settings

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob, AIDataReport, AIDataSuggestion


def build_batch_report(batch: AIDataBatch, *, health_report=None):
    suggestions = AIDataSuggestion.objects.filter(batch=batch)
    status_counts = Counter(suggestions.values_list("status", flat=True))
    type_counts = Counter(suggestions.values_list("suggestion_type", flat=True))
    risk_counts = Counter(suggestions.values_list("risk_level", flat=True))
    jobs = AIDataJob.objects.filter(batch=batch).order_by("-created_at")
    report = {
        "batch": {
            "id": batch.id,
            "uuid": str(batch.batch_uuid),
            "type": batch.batch_type,
            "status": batch.status,
            "created_at": batch.created_at.isoformat() if batch.created_at else None,
            "completed_at": batch.completed_at.isoformat() if batch.completed_at else None,
        },
        "summary": batch.summary or {},
        "suggestions": {
            "total": suggestions.count(),
            "by_status": dict(status_counts),
            "by_type": dict(type_counts),
            "by_risk": dict(risk_counts),
            "approved": status_counts.get(constants.SUGGESTION_STATUS_APPROVED, 0),
            "applied": status_counts.get(constants.SUGGESTION_STATUS_APPLIED, 0),
            "rejected": status_counts.get(constants.SUGGESTION_STATUS_REJECTED, 0),
            "risky_needing_review": suggestions.filter(risk_level=constants.RISK_RISKY).exclude(status=constants.SUGGESTION_STATUS_APPLIED).count(),
        },
        "jobs": [
            {
                "id": job.id,
                "job_type": job.job_type,
                "provider": job.provider,
                "status": job.status,
                "processed_records": job.processed_records,
                "total_records": job.total_records,
                "suggestions_created": job.suggestions_created,
                "errors_count": job.errors_count,
                "started_at": job.started_at.isoformat() if job.started_at else None,
                "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            }
            for job in jobs[:20]
        ],
        "health_report": health_report or {},
    }
    return report


def build_dashboard_summary():
    suggestions = AIDataSuggestion.objects.all()
    jobs = AIDataJob.objects.all()
    latest_health_report = (
        AIDataReport.objects
        .filter(report_type=constants.BATCH_TYPE_HEALTH_CHECK, format="json")
        .order_by("-created_at")
        .first()
    )
    return {
        "latest_batches": list(
            AIDataBatch.objects.order_by("-created_at").values(
                "id",
                "batch_type",
                "status",
                "created_at",
                "completed_at",
                "created_by",
            )[:10]
        ),
        "latest_jobs": list(
            jobs.order_by("-created_at").values(
                "id",
                "batch_id",
                "job_type",
                "provider",
                "status",
                "processed_records",
                "total_records",
                "suggestions_created",
            )[:10]
        ),
        "suggestions_by_status": dict(Counter(suggestions.values_list("status", flat=True))),
        "suggestions_by_risk": dict(Counter(suggestions.values_list("risk_level", flat=True))),
        "suggestions_by_type": dict(Counter(suggestions.values_list("suggestion_type", flat=True))),
        "latest_health_summary": (
            latest_health_report.content.get("health_report", {}).get("summary", {})
            if latest_health_report
            else {}
        ),
    }


def write_reports(batch: AIDataBatch, *, report, output_dir=None):
    output_root = Path(output_dir) if output_dir else Path(settings.BASE_DIR) / "exports" / "ai_data_pipeline"
    output_root.mkdir(parents=True, exist_ok=True)
    json_path = output_root / f"batch_{batch.id}_report.json"
    html_path = output_root / f"batch_{batch.id}_report.html"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(render_html(report), encoding="utf-8")
    AIDataReport.objects.create(
        batch=batch,
        report_type=batch.batch_type,
        format="json",
        path=str(json_path),
        content=report,
        summary=report.get("summary", {}),
    )
    AIDataReport.objects.create(
        batch=batch,
        report_type=batch.batch_type,
        format="html",
        path=str(html_path),
        content=report,
        summary=report.get("summary", {}),
    )
    return {"json": str(json_path), "html": str(html_path)}


def render_html(report):
    suggestions = report.get("suggestions", {})
    health = report.get("health_report", {}).get("summary", {})
    jobs = report.get("jobs", [])
    rows = []
    for label, value in [
        ("Batch", report.get("batch", {}).get("id")),
        ("Status", report.get("batch", {}).get("status")),
        ("Total suggestions", suggestions.get("total", 0)),
        ("Approved", suggestions.get("approved", 0)),
        ("Applied", suggestions.get("applied", 0)),
        ("Rejected", suggestions.get("rejected", 0)),
        ("Risky needing review", suggestions.get("risky_needing_review", 0)),
        ("Jobs", len(jobs)),
        ("Health issues", health.get("issue_count", 0)),
        ("Exact duplicate groups", health.get("exact_duplicate_groups", 0)),
        ("Near duplicate pairs", health.get("near_duplicate_pairs", 0)),
    ]:
        rows.append(f"<tr><th>{escape(str(label))}</th><td>{escape(str(value))}</td></tr>")
    return f"""<!doctype html>
<html lang=\"fa\" dir=\"rtl\">
<head>
  <meta charset=\"utf-8\">
  <title>AI Data Pipeline Report</title>
  <style>
    body {{ font-family: Calibri, 'B Mitra', 'B Nazanin', Arial, sans-serif; background: #f6f6f2; color: #241a2a; padding: 24px; }}
    table {{ border-collapse: collapse; width: 100%; background: #fff; direction: ltr; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e3dde8; text-align: left; }}
    th {{ width: 280px; background: #403147; color: #fff; }}
    pre {{ direction: ltr; background: #fff; padding: 16px; overflow: auto; border: 1px solid #e3dde8; }}
  </style>
</head>
<body>
  <h1>AI Data Pipeline Report</h1>
  <table>{''.join(rows)}</table>
  <h2>Raw JSON</h2>
  <pre>{escape(json.dumps(report, ensure_ascii=False, indent=2))}</pre>
</body>
</html>"""
