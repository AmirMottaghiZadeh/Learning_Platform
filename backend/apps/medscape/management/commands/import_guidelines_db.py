"""Loads guidelines.db (written by export_reference_db) into this
database: guideline articles are added or updated in place and their
figures added once, so re-running it is safe.

    python manage.py import_guidelines_db --source /data/guidelines.db [--dry-run] [--prune]
"""

from apps.core.management.reference_import import ReferenceImportCommand
from apps.medscape import reference_db
from apps.medscape.models import Article


class Command(ReferenceImportCommand):
    help = "Import Medscape guidelines from a guidelines.db reference-data file."
    dataset = "guidelines"

    def load(self, conn, meta, prune):
        return reference_db.load(conn, meta, Article.GUIDELINE, prune=prune, log=self.stdout.write)
