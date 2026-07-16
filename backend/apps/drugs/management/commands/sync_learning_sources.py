from django.core.management.base import BaseCommand, CommandError

from apps.drugs.learning_sync import (
    regenerate_and_sync_all_drug_question_sources,
    regenerate_and_sync_drug_question_sources,
    sync_all_drug_question_sources,
)
from apps.drugs.models import Drug


class Command(BaseCommand):
    help = "Incrementally sync Pharmexa question sources into platform learning sources."

    def add_arguments(self, parser):
        parser.add_argument(
            "--drug-id",
            type=int,
            help="Sync only the question sources for one drug.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Rebuild question and learning sources for every drug. This can take time.",
        )
        parser.add_argument(
            "--progress-every",
            type=int,
            default=100,
            help="Print progress after this many checked question sources (default: 100).",
        )

    def handle(self, *args, **options):
        progress_every = max(1, options["progress_every"])
        drug_id = options.get("drug_id")

        if options["all"] and drug_id is not None:
            raise CommandError("--all and --drug-id cannot be used together.")

        if drug_id is not None:
            drug = Drug.objects.filter(pk=drug_id).first()
            if drug is None:
                raise CommandError(f"Drug #{drug_id} was not found.")
            result = regenerate_and_sync_drug_question_sources(drug)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Drug #{drug.id} synced: {result.question_sources} question sources and "
                    f"{result.knowledge_sources} active learning sources."
                )
            )
            return

        if options["all"]:
            self.stdout.write("Rebuilding question and learning sources for every drug…")

            def report_full_rebuild(processed, total, question_sources):
                if processed == 1 or processed % progress_every == 0 or processed == total:
                    self.stdout.write(
                        f"Progress: {processed}/{total} drugs rebuilt; "
                        f"{question_sources} question sources generated."
                    )

            result = regenerate_and_sync_all_drug_question_sources(
                progress_callback=report_full_rebuild,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    "Full learning-source rebuild complete: "
                    f"{result.topics} topics, "
                    f"{result.learning_objects} learning objects, "
                    f"{result.knowledge_sources} active knowledge sources; "
                    f"{result.updated_sources} question sources generated."
                )
            )
            return

        self.stdout.write("Checking learning sources for required updates…")

        def report_progress(processed, total, updated):
            if processed == 1 or processed % progress_every == 0 or processed == total:
                self.stdout.write(
                    f"Progress: {processed}/{total} question sources checked; "
                    f"{updated} updated."
                )

        result = sync_all_drug_question_sources(
            progress_callback=report_progress,
        )
        self.stdout.write(
            self.style.SUCCESS(
                "Learning-source sync complete: "
                f"{result.topics} topics, "
                f"{result.learning_objects} learning objects, "
                f"{result.knowledge_sources} active knowledge sources; "
                f"{result.updated_sources}/{result.processed_sources} question sources updated."
            )
        )
