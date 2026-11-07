"""Writes the quiz bank and flashcard facts out of this database into one
portable SQLite file, study_content.db, for loading into another database
(the production server) with import_study_content_db (see apps.quiz.reference_db).

    python manage.py export_study_content_db
    python manage.py export_study_content_db --out ~/pharmenta-data
"""

import time
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.core import reference_db
from apps.quiz import reference_db as study_db

DEFAULT_OUT = "/home/amir/Documents/pharmenta-reference-data"


class Command(BaseCommand):
    help = "Export the quiz question bank and flashcard facts into study_content.db."

    def add_arguments(self, parser):
        parser.add_argument("--out", default=DEFAULT_OUT, help=f"Directory to write study_content.db into (default: {DEFAULT_OUT}).")

    def handle(self, *args, **options):
        path = Path(options["out"]).expanduser() / f"{study_db.DATASET}.db"
        started = time.monotonic()
        self.stdout.write(f"{study_db.DATASET} -> {path}")
        with reference_db.writing(path, study_db.DATASET) as conn:
            counts = study_db.export(conn)
        size_mb = path.stat().st_size / 1_000_000
        summary = ", ".join(f"{n} {table}" for table, n in counts.items())
        self.stdout.write(self.style.SUCCESS(f"  {summary} · {size_mb:.1f} MB · {time.monotonic() - started:.0f}s"))
