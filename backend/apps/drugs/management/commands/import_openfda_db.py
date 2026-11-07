"""Loads the openfda parts written by export_openfda_db into this database
-- the way a server without the pipeline file gets the drug profiles:
ATC codes, ingredients and their sections are added or updated in place
(nothing is deleted), so re-running it is safe. Every part of the export
must be there.

    python manage.py import_openfda_db --source /data/openfda --dry-run
    python manage.py import_openfda_db --source /data/openfda
"""

import time

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.drugs import reference_db
from apps.drugs.management.commands.export_openfda_db import DEFAULT_OUT


class _DryRun(Exception):
    pass


class Command(BaseCommand):
    help = "Import the openfda drug profiles from the parts written by export_openfda_db."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=DEFAULT_OUT,
            help=f"Directory holding openfda.part*.db, or one part (default: {DEFAULT_OUT}).",
        )
        parser.add_argument("--dry-run", action="store_true", help="Run the whole import, then roll it back.")

    def handle(self, *args, **options):
        parts = reference_db.open_parts(options["source"])
        meta = parts[0][1]
        self.stdout.write(f"{reference_db.DATASET}: {len(parts)} parts, exported {meta.get('exported_at', '?')}")
        started = time.monotonic()
        try:
            with transaction.atomic():
                summary = reference_db.load(parts, log=self.stdout.write)
                if options["dry_run"]:
                    raise _DryRun
        except _DryRun:
            self.report(summary)
            self.stdout.write(self.style.WARNING("Dry run: everything above was rolled back."))
            return
        finally:
            for conn, _ in parts:
                conn.close()
        self.report(summary)
        self.stdout.write(self.style.SUCCESS(f"Done in {time.monotonic() - started:.0f}s."))

    def report(self, summary):
        for table, value in summary.items():
            if isinstance(value, tuple):
                value = {"added": value[0], "updated": value[1]}
            if isinstance(value, dict):
                value = ", ".join(f"{n} {label}" for label, n in value.items())
            self.stdout.write(f"  {table}: {value}")
