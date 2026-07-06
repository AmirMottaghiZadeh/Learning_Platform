from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.analyzers.health_check import run_health_check
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob
from apps.ai_data_pipeline.reports.report_generator import build_batch_report, write_reports


class Command(BaseCommand):
    help = "Run AI data pipeline health check without modifying production data."

    def add_arguments(self, parser):
        parser.add_argument("--output-dir", default="")
        parser.add_argument("--created-by", default="cli")
        parser.add_argument("--no-near-duplicates", action="store_true")
        parser.add_argument("--near-threshold", type=float, default=0.92)

    def handle(self, *args, **options):
        batch = AIDataBatch.objects.create(
            batch_type=constants.BATCH_TYPE_HEALTH_CHECK,
            status=constants.BATCH_STATUS_RUNNING,
            source_database=str(settings.DATABASES["default"].get("NAME", "")),
            config={
                "include_near_duplicates": not options["no_near_duplicates"],
                "near_threshold": options["near_threshold"],
            },
            created_by=options["created_by"],
            started_at=timezone.now(),
        )
        job = AIDataJob.objects.create(
            batch=batch,
            job_type=constants.JOB_TYPE_HEALTH_CHECK,
            provider=constants.PROVIDER_RULES,
            status=constants.JOB_STATUS_RUNNING,
            parameters_json=batch.config,
            created_by=options["created_by"],
            started_at=timezone.now(),
        )
        try:
            health_report = run_health_check(
                include_near_duplicates=not options["no_near_duplicates"],
                near_duplicate_threshold=options["near_threshold"],
            )
            batch.summary = health_report["summary"]
            batch.status = constants.BATCH_STATUS_COMPLETED
            batch.completed_at = timezone.now()
            batch.save(update_fields=["summary", "status", "completed_at"])
            job.total_records = health_report["summary"].get("total_records_scanned", 0)
            job.mark_completed(
                processed_records=job.total_records,
                suggestions_created=0,
            )
            report = build_batch_report(batch, health_report=health_report)
            paths = write_reports(batch, report=report, output_dir=options["output_dir"] or None)
            self.stdout.write(self.style.SUCCESS(f"Health batch {batch.id} complete."))
            self.stdout.write(f"JSON: {paths['json']}")
            self.stdout.write(f"HTML: {paths['html']}")
        except Exception as exc:
            job.mark_failed(exc)
            batch.status = constants.BATCH_STATUS_FAILED
            batch.error_message = str(exc)
            batch.completed_at = timezone.now()
            batch.save(update_fields=["status", "error_message", "completed_at"])
            raise
