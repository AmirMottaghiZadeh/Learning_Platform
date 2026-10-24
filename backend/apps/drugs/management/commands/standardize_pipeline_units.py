"""Write the units in the openfda pipeline's Persian summaries as standard
symbols («میلی‌گرم بر کیلوگرم در روز» -> «mg/kg/day»), in the pipeline's own
SQLite file -- the source `import_openfda` reads the lessons from -- so the
next sync and anything else built from that file agree with the app (whose
sections migration drugs.0006 already converted). The old text of every cell
changed is kept in `units_fa_backup_<date>` (see apps.drugs.pipeline_db).
Idempotent: a second run finds nothing left to change. The rules are in
apps.core.units_fa.
"""

import sqlite3

from django.core.management.base import BaseCommand, CommandError

from apps.core.units_fa import standardize_units
from apps.drugs.management.commands.import_openfda import DEFAULT_SOURCE
from apps.drugs.pipeline_db import rewrite_summaries


class Command(BaseCommand):
    help = "Write the units in the pipeline SQLite's Persian summaries as standard symbols."

    def add_arguments(self, parser):
        parser.add_argument("--source", default=DEFAULT_SOURCE, help=f"Pipeline SQLite file (default: {DEFAULT_SOURCE}).")
        parser.add_argument("--dry-run", action="store_true", help="Count the changes, write nothing.")

    def handle(self, *args, **opts):
        try:
            cells, ingredients, backup = rewrite_summaries(
                opts["source"],
                lambda field, lang, text: standardize_units(text) if lang == "fa" else text,
                "units_fa",
                dry_run=opts["dry_run"],
            )
        except (sqlite3.Error, ValueError) as exc:
            raise CommandError(f"cannot rewrite {opts['source']}: {exc}") from exc
        self.stdout.write(f"{cells} summaries in {ingredients} ingredients to change")
        if backup:
            self.stdout.write(self.style.SUCCESS(f"written; old text kept in {backup}"))
