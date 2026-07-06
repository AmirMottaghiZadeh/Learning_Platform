from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob
from apps.ai_data_pipeline.providers.base import get_provider, list_provider_names
from apps.ai_data_pipeline.reports.report_generator import build_batch_report, write_reports
from apps.ai_data_pipeline.reviewers.suggestion_generator import DEFAULT_FIELDS, generate_suggestions


class Command(BaseCommand):
    help = "Generate local rule-based suggestions only. This command never applies changes to production tables."

    def add_arguments(self, parser):
        parser.add_argument("--provider", default=getattr(settings, "AI_DATA_PIPELINE_PROVIDER", constants.PROVIDER_RULES), choices=list_provider_names())
        parser.add_argument("--limit", type=int, default=0)
        parser.add_argument("--table", default=constants.DRUG_TABLE)
        parser.add_argument("--field", action="append", default=[], help="Field to scan. Can be repeated or comma-separated.")
        parser.add_argument("--fields", default="", help="Backward-compatible comma-separated field list.")
        parser.add_argument("--risk-level", choices=[constants.RISK_SAFE, constants.RISK_NEEDS_REVIEW, constants.RISK_RISKY])
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--batch-name", default="")
        parser.add_argument("--only-safe", action="store_true")
        parser.add_argument("--include-duplicates", action="store_true")
        parser.add_argument("--include-medical-validation", action="store_true")
        parser.add_argument("--include-normalization", action="store_true")
        parser.add_argument("--include-terminology", action="store_true")
        parser.add_argument("--created-by", default="cli")
        parser.add_argument("--output-dir", default="")
        parser.add_argument("--skip-duplicates", action="store_true", help="Backward-compatible alias to disable duplicates.")

    def handle(self, *args, **options):
        if options["table"] != constants.DRUG_TABLE:
            raise CommandError(f"Unsupported table for local rules: {options['table']}")
        if options["provider"] in {constants.PROVIDER_OPENAI, constants.PROVIDER_OLLAMA}:
            raise CommandError(f"Provider '{options['provider']}' is registered as a placeholder but disabled in no-external-API mode.")

        fields = self._parse_fields(options)
        include_flags = {
            "include_normalization": options["include_normalization"],
            "include_terminology": options["include_terminology"],
            "include_medical_validation": options["include_medical_validation"],
        }
        if not any(include_flags.values()):
            include_flags = {
                "include_normalization": True,
                "include_terminology": True,
                "include_medical_validation": True,
            }
        include_duplicates = options["include_duplicates"] and not options["skip_duplicates"]

        provider = get_provider(options["provider"])
        config = {
            "provider": provider.provider_name,
            "limit": options["limit"],
            "batch_name": options["batch_name"],
            "risk_level": options["risk_level"],
            "only_safe": options["only_safe"],
            "include_duplicates": include_duplicates,
            **include_flags,
        }

        if options["dry_run"]:
            summary = generate_suggestions(
                batch=None,
                fields=fields,
                limit=options["limit"] or None,
                provider=provider,
                table=options["table"],
                risk_level=options["risk_level"],
                only_safe=options["only_safe"],
                dry_run=True,
                include_duplicates=include_duplicates,
                **include_flags,
            )
            self.stdout.write(self.style.WARNING("Dry run complete. No batch or suggestions were saved."))
            self.stdout.write(f"Records scanned: {summary['records_scanned']}")
            self.stdout.write(f"Suggestions previewed: {summary['suggestions_generated']}")
            self.stdout.write(f"By type: {summary['by_type']}")
            self.stdout.write(f"By risk: {summary['by_risk']}")
            return

        batch = AIDataBatch.objects.create(
            batch_type=constants.BATCH_TYPE_SUGGESTION_GENERATION,
            status=constants.BATCH_STATUS_RUNNING,
            source_database=str(settings.DATABASES["default"].get("NAME", "")),
            target_scope={"table": constants.DRUG_TABLE, "fields": fields},
            config=config,
            created_by=options["created_by"],
            started_at=timezone.now(),
        )
        job = AIDataJob.objects.create(
            batch=batch,
            job_type=constants.JOB_TYPE_FULL_RULES_REVIEW,
            provider=provider.provider_name,
            status=constants.JOB_STATUS_PENDING,
            parameters_json=config,
            created_by=options["created_by"],
        )
        try:
            summary = generate_suggestions(
                batch=batch,
                job=job,
                fields=fields,
                limit=options["limit"] or None,
                provider=provider,
                table=options["table"],
                risk_level=options["risk_level"],
                only_safe=options["only_safe"],
                include_duplicates=include_duplicates,
                **include_flags,
            )
            report = build_batch_report(batch)
            paths = write_reports(batch, report=report, output_dir=options["output_dir"] or None)
            self.stdout.write(self.style.SUCCESS(f"Suggestion batch {batch.id} complete."))
            if options["batch_name"]:
                self.stdout.write(f"Batch name: {options['batch_name']}")
            self.stdout.write(f"Suggestions generated: {summary['suggestions_generated']}")
            self.stdout.write(f"By type: {summary['by_type']}")
            self.stdout.write(f"By risk: {summary['by_risk']}")
            self.stdout.write(f"JSON: {paths['json']}")
            self.stdout.write(f"HTML: {paths['html']}")
        except Exception as exc:
            job.mark_failed(exc)
            batch.status = constants.BATCH_STATUS_FAILED
            batch.error_message = str(exc)
            batch.completed_at = timezone.now()
            batch.save(update_fields=["status", "error_message", "completed_at"])
            raise

    def _parse_fields(self, options):
        raw_items = []
        for item in options["field"]:
            raw_items.extend(item.split(","))
        if options["fields"]:
            raw_items.extend(options["fields"].split(","))
        fields = [item.strip() for item in raw_items if item.strip()]
        return fields or DEFAULT_FIELDS
