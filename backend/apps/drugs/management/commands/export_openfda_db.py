"""Writes the openfda drug profiles this database holds -- what
import_openfda loaded from the pipeline file, as cleaned here -- into
portable parts of at most --max-mb each (openfda.part01.db, ...), for
loading into another database with import_openfda_db (see
apps.drugs.reference_db). The parts of an earlier export in --out are
replaced once the new set is complete.

    python manage.py export_openfda_db
    python manage.py export_openfda_db --out ~/pharmenta-data/openfda --max-mb 100
"""

import time
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.drugs import reference_db

DEFAULT_OUT = "/home/amir/Documents/pharmenta-reference-data/openfda"


class Command(BaseCommand):
    help = "Export the openfda drug profiles into portable parts of at most --max-mb each."

    def add_arguments(self, parser):
        parser.add_argument("--out", default=DEFAULT_OUT, help=f"Directory for the parts (default: {DEFAULT_OUT}).")
        parser.add_argument("--max-mb", type=int, default=200, help="Largest size of one part, in MB (default: 200).")

    def handle(self, *args, **options):
        if options["max_mb"] < 5:
            raise CommandError("--max-mb must be at least 5.")
        out = Path(options["out"]).expanduser()
        started = time.monotonic()
        self.stdout.write(f"{reference_db.DATASET} -> {out}")
        paths, counts = reference_db.export(out, options["max_mb"] * 1_000_000, log=self.stdout.write)
        for path in paths:
            self.stdout.write(f"  {path.name}: {path.stat().st_size / 1_000_000:.1f} MB")
        summary = ", ".join(f"{n} {table}" for table, n in counts.items())
        self.stdout.write(self.style.SUCCESS(f"  {summary} · {len(paths)} parts · {time.monotonic() - started:.0f}s"))
