"""Regenerate search_lexicon/drugs_fa.csv from the project's Persian drug names."""

import csv
from pathlib import Path

from django.core.management.base import BaseCommand

from apps.uptodate.search_concepts import LEXICON_DIR, build_drug_lexicon

DEFAULT_PIPELINE = "/home/amir/Documents/openfda/pipeline_v2/pipeline_v2.db"
DEFAULT_SNAPSHOT = "/home/amir/Documents/UpToDate"
FIELDS = ["fa", "en", "key", "article_id", "method", "status"]


class Command(BaseCommand):
    help = "Map pipeline_v2 Persian ingredient names to UpToDate drug concepts (search_lexicon/drugs_fa.csv)."

    def add_arguments(self, parser):
        parser.add_argument("--pipeline", default=DEFAULT_PIPELINE, help="pipeline_v2.db with ingredient_name_fa")
        parser.add_argument("--source", default=DEFAULT_SNAPSHOT, help="UpToDate snapshot directory (search.db)")

    def handle(self, *args, **options):
        rows = build_drug_lexicon(options["pipeline"], options["source"])
        target = Path(LEXICON_DIR) / "drugs_fa.csv"
        # Keep reviewer decisions: a row marked reviewed survives regeneration.
        reviewed = {}
        if target.exists():
            with target.open(encoding="utf-8") as handle:
                reviewed = {row["en"]: row for row in csv.DictReader(handle) if row["status"] == "reviewed"}
        rows = [reviewed.get(row["en"], row) for row in rows]
        with target.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(rows)
        counts = {status: sum(row["status"] == status for row in rows)
                  for status in ("project", "needs_review", "reviewed", "unmatched")}
        self.stdout.write(self.style.SUCCESS(f"Wrote {len(rows)} drug names to {target}: {counts}"))
