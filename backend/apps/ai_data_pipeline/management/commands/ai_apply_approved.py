from django.core.management.base import BaseCommand

from apps.ai_data_pipeline.appliers.apply_changes import apply_approved_suggestions


class Command(BaseCommand):
    help = "Apply approved suggestions with transaction, backup, and audit history."

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", type=int, required=True)
        parser.add_argument("--applied-by", default="cli")
        parser.add_argument("--backup-dir", default="")
        parser.add_argument("--min-confidence", type=float, default=0.8)
        parser.add_argument("--include-risky", action="store_true")

    def handle(self, *args, **options):
        result = apply_approved_suggestions(
            batch_id=options["batch_id"],
            applied_by=options["applied_by"],
            backup_dir=options["backup_dir"] or None,
            min_confidence=options["min_confidence"],
            include_risky=options["include_risky"],
        )
        self.stdout.write(self.style.SUCCESS(
            f"Applied={result.applied}, skipped={result.skipped}, failed={result.failed}"
        ))
        if result.backup_path:
            self.stdout.write(f"Backup: {result.backup_path}")
