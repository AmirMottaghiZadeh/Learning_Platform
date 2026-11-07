"""Upgrade an existing MySQL mirror without needing the SQLite snapshot."""

import pymysql
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.uptodate.mysql_schema import ensure_title_search_index
from apps.uptodate.services import mysql_config


class Command(BaseCommand):
    help = "Ensure title-only UpToDate search has a MySQL FULLTEXT index (no-op for SQLite)."

    def handle(self, *args, **options):
        if not settings.UPTODATE_MYSQL_URL:
            self.stdout.write("UpToDate uses SQLite; no MySQL search index needed.")
            return

        self.stdout.write("Checking UpToDate title search index...")
        connection = pymysql.connect(**mysql_config(), autocommit=True)
        try:
            created = ensure_title_search_index(connection)
        finally:
            connection.close()
        message = "Created UpToDate title search index." if created else "UpToDate title search index already exists."
        self.stdout.write(self.style.SUCCESS(message))
