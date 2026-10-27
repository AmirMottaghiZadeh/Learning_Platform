import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = "Create a timestamped database backup without modifying production data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--output-dir",
            default=str(settings.BASE_DIR / "backups"),
            help="Directory where the backup file will be written.",
        )
        parser.add_argument("--name", default="", help="Optional backup file prefix.")
        parser.add_argument("--dry-run", action="store_true", help="Show the target path without writing a backup.")

    def handle(self, *args, **options):
        database = settings.DATABASES["default"]
        engine = database["ENGINE"]
        output_dir = Path(options["output_dir"])
        prefix = options["name"] or "database"
        timestamp = timezone.now().strftime("%Y%m%d-%H%M%S")

        if "postgresql" in engine:
            target = output_dir / f"{prefix}-{timestamp}.dump"
            database_url = getattr(settings, "DATABASE_URL", None)
            if not database_url:
                database_url = self._build_postgres_url(database)
            if options["dry_run"]:
                self.stdout.write(str(target))
                return
            if not shutil.which("pg_dump"):
                raise CommandError("pg_dump is required for PostgreSQL backups.")
            output_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(["pg_dump", database_url, "--format=custom", "--file", str(target)], check=True)
            self.stdout.write(self.style.SUCCESS(f"PostgreSQL backup created: {target}"))
            return

        raise CommandError(f"Unsupported database engine for backup: {engine}. Expected PostgreSQL.")

    def _build_postgres_url(self, database):
        user = database.get("USER") or ""
        password = database.get("PASSWORD") or ""
        host = database.get("HOST") or "localhost"
        port = database.get("PORT") or "5432"
        name = database.get("NAME")
        credentials = user
        if password:
            credentials = f"{user}:{password}"
        auth = f"{credentials}@" if credentials else ""
        return f"postgresql://{auth}{host}:{port}/{name}"
