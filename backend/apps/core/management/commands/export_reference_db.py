"""Writes the calculators, guidelines and diseases datasets out of this
database into self-contained SQLite files -- calculators.db, guidelines.db,
diseases.db -- for loading into another database with import_calculators_db,
import_guidelines_db and import_diseases_db (see apps.core.reference_db).

    python manage.py export_reference_db --out ~/pharmenta-data
    python manage.py export_reference_db --out ~/pharmenta-data --only diseases
"""

import time
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.calculators import reference_db as calculators_db
from apps.core import reference_db
from apps.medscape import reference_db as medscape_db
from apps.medscape.models import Article


class Command(BaseCommand):
    help = "Export calculators / guidelines / diseases into portable SQLite files."

    def add_arguments(self, parser):
        parser.add_argument("--out", default="reference-data", help="Directory to write the .db files into.")
        parser.add_argument(
            "--only",
            action="append",
            choices=reference_db.DATASETS,
            help="Export only this dataset (repeatable). Default: all three.",
        )

    def handle(self, *args, **options):
        out = Path(options["out"]).expanduser()
        for dataset in options["only"] or reference_db.DATASETS:
            path = out / f"{dataset}.db"
            started = time.monotonic()
            self.stdout.write(f"{dataset} -> {path}")
            with reference_db.writing(path, dataset) as conn:
                if dataset == "calculators":
                    counts = calculators_db.export(conn)
                else:
                    kind = Article.GUIDELINE if dataset == "guidelines" else Article.DISEASE
                    counts = medscape_db.export(conn, kind, log=self.stdout.write)
            size_mb = path.stat().st_size / 1_000_000
            summary = ", ".join(f"{n} {table}" for table, n in counts.items())
            self.stdout.write(self.style.SUCCESS(
                f"  {summary} · {size_mb:.1f} MB · {time.monotonic() - started:.0f}s"
            ))
