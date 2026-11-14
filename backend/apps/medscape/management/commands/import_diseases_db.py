"""Loads diseases.db (written by export_reference_db) into this database:
disease articles are added or updated in place and their figures added
once, so re-running it is safe.

    python manage.py import_diseases_db --source /data/diseases.db [--dry-run] [--prune]
"""

from apps.core.management.reference_import import ReferenceImportCommand
from apps.medscape import reference_db
from apps.medscape.models import Article


class Command(ReferenceImportCommand):
    help = "Import Medscape diseases & conditions from a diseases.db reference-data file."
    dataset = "diseases"

    def load(self, conn, meta, prune):
        return reference_db.load(conn, meta, Article.DISEASE, prune=prune, log=self.stdout.write)
