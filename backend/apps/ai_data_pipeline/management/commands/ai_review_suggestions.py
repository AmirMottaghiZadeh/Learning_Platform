from django.core.management.base import BaseCommand, CommandError

from apps.ai_data_pipeline.reviewers.approval import review_suggestions


class Command(BaseCommand):
    help = "Approve, reject, or edit pending AI data suggestions."

    def add_arguments(self, parser):
        parser.add_argument("--batch-id", type=int)
        parser.add_argument("--ids", default="", help="Comma-separated suggestion ids.")
        parser.add_argument("--action", choices=["approve", "reject", "edit"], required=True)
        parser.add_argument("--reviewed-by", default="cli")
        parser.add_argument("--edited-value", default=None)
        parser.add_argument("--risk-level", choices=["safe", "needs_review", "risky"])

    def handle(self, *args, **options):
        ids = [int(item.strip()) for item in options["ids"].split(",") if item.strip()]
        if not ids and not options["batch_id"]:
            raise CommandError("Provide --ids or --batch-id.")
        count = review_suggestions(
            suggestion_ids=ids or None,
            batch_id=options["batch_id"],
            action=options["action"],
            reviewed_by=options["reviewed_by"],
            edited_value=options["edited_value"],
            risk_level=options["risk_level"],
        )
        self.stdout.write(self.style.SUCCESS(f"Reviewed suggestions: {count}"))
