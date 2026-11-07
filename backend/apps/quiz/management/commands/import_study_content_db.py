"""Loads study_content.db (written by export_study_content_db) into this
database: bank questions are added or updated in place (matched on their
study_content id), and each drug's flashcard facts are replaced per section and
language, so re-running it is safe. Meant for the server.

    python manage.py import_study_content_db --source /data/study_content.db [--dry-run] [--prune]
"""

from apps.core.management.reference_import import ReferenceImportCommand
from apps.quiz import reference_db as study_db


class Command(ReferenceImportCommand):
    help = "Import quiz questions and flashcard facts from a study_content.db reference-data file."
    dataset = study_db.DATASET

    def load(self, conn, meta, prune):
        return study_db.load(conn, meta, prune=prune, log=self.stdout.write)
