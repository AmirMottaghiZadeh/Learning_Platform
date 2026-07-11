import json

from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import ValidationError

from apps.drugs.json_import import parse_json_directory, replace_drug_metadata_from_json


class Command(BaseCommand):
    help = "Validate and atomically replace K_Game drug metadata from versioned JSON documents."

    def add_arguments(self, parser):
        parser.add_argument("directory")
        parser.add_argument(
            "--validate-only",
            action="store_true",
            help="Validate and summarize the dataset without changing the database.",
        )

    def handle(self, *args, **options):
        directory = options["directory"]
        try:
            if options["validate_only"]:
                documents, skipped_rows = parse_json_directory(directory)
                drug_count = sum(len(document.drugs) for document in documents)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Valid dataset: {len(documents)} documents, "
                        f"{drug_count} drugs, {skipped_rows} skipped rows."
                    )
                )
                return

            result = replace_drug_metadata_from_json(directory)
        except (ValidationError, ValueError, TypeError, json.JSONDecodeError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Replaced K_Game metadata with {result.documents} documents, "
                f"{result.drugs} drugs and {result.question_sources} question sources; "
                f"{result.skipped_rows} rows skipped."
            )
        )
