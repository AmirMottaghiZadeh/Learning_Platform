from django.core.management.base import BaseCommand

from apps.ai_data_pipeline.models import AIDataBatch
from apps.ai_data_pipeline.reports.report_generator import build_batch_report, write_reports


class Command(BaseCommand):
    help = "Generate JSON/HTML report for an AI data pipeline batch."

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", type=int, required=True)
        parser.add_argument("--output-dir", default="")

    def handle(self, *args, **options):
        batch = AIDataBatch.objects.get(id=options["batch_id"])
        report = build_batch_report(batch)
        paths = write_reports(batch, report=report, output_dir=options["output_dir"] or None)
        self.stdout.write(self.style.SUCCESS(f"Report generated for batch {batch.id}."))
        self.stdout.write(f"JSON: {paths['json']}")
        self.stdout.write(f"HTML: {paths['html']}")
