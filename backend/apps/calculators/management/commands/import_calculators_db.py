"""Loads calculators.db (written by export_reference_db) into this
database: categories, tags and calculators are added or updated in place,
so re-running it is safe.

    python manage.py import_calculators_db --source /data/calculators.db [--dry-run] [--prune]
"""

from apps.calculators import reference_db
from apps.core.management.reference_import import ReferenceImportCommand


class Command(ReferenceImportCommand):
    help = "Import calculators from a calculators.db reference-data file."
    dataset = "calculators"

    def load(self, conn, meta, prune):
        return reference_db.load(conn, meta, prune=prune, log=self.stdout.write)
