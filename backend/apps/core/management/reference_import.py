"""What import_calculators_db, import_guidelines_db and import_diseases_db
share: the options, the dry run, and the report."""

import time

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core import reference_db


class _DryRun(Exception):
    pass


class ReferenceImportCommand(BaseCommand):
    dataset = ""

    def add_arguments(self, parser):
        parser.add_argument("--source", required=True, help=f"Path to {self.dataset}.db (from export_reference_db).")
        parser.add_argument(
            "--prune",
            action="store_true",
            help="Also delete rows of this dataset that are not in the file.",
        )
        parser.add_argument("--dry-run", action="store_true", help="Run the whole import, then roll it back.")

    def load(self, conn, meta, prune):
        raise NotImplementedError

    def handle(self, *args, **options):
        conn, meta = reference_db.open_for_import(options["source"], self.dataset)
        self.stdout.write(f"{self.dataset}: file exported {meta.get('exported_at', '?')}")
        started = time.monotonic()
        try:
            with transaction.atomic():
                summary = self.load(conn, meta, options["prune"])
                if options["dry_run"]:
                    raise _DryRun
        except _DryRun:
            self.report(summary)
            self.stdout.write(self.style.WARNING("Dry run: everything above was rolled back."))
            return
        finally:
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
