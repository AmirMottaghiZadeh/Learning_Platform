"""Side-effect categories on their own lines, and commentary about the
source text removed, in the drug profile summaries (fa and en); see
apps.drugs.profile_text.

Idempotent. `--pipeline` makes the same change in the openfda pipeline file
(the old text kept in `textfix_backup_<date>`), so the next
`import_openfda --only-summaries` does not bring the old text back.
`--show` prints every change for review.
"""

import sqlite3

from django.core.management.base import BaseCommand, CommandError

from apps.drugs.management.commands.import_openfda import DEFAULT_SOURCE
from apps.drugs.models import IngredientProfileSection
from apps.drugs.pipeline_db import rewrite_summaries
from apps.drugs.profile_text import fix_summary


class Command(BaseCommand):
    help = "Put side-effect categories on their own lines and drop commentary about the source text."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")
        parser.add_argument("--show", action="store_true", help="Print each change (old and new text).")
        parser.add_argument(
            "--pipeline",
            nargs="?",
            const=DEFAULT_SOURCE,
            help=f"Also fix the openfda pipeline SQLite file (default path: {DEFAULT_SOURCE}).",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        changed = []
        for section in IngredientProfileSection.objects.exclude(summary_fa="", summary_en="").select_related("ingredient"):
            fields = []
            for attr in ("summary_fa", "summary_en"):
                old = getattr(section, attr)
                new = fix_summary(old, section.field) if old else old
                if new != old:
                    if options["show"]:
                        self.stdout.write(f"--- {section.ingredient.name} · {section.field} · {attr}\n{old}\n+++\n{new}\n")
                    setattr(section, attr, new)
                    fields.append(attr)
            if fields:
                changed.append((section, fields))

        if not dry_run:
            for fields in ({"summary_fa"}, {"summary_en"}, {"summary_fa", "summary_en"}):
                batch = [s for s, f in changed if set(f) == fields]
                if batch:
                    IngredientProfileSection.objects.bulk_update(batch, list(fields), batch_size=500)
        emptied = sum(1 for s, _ in changed if not s.summary_fa.strip() and not s.summary_en.strip())
        self.stdout.write(self.style.SUCCESS(
            f"{'(dry-run) ' if dry_run else ''}{len(changed)} sections fixed, {emptied} now empty"
        ))

        if options["pipeline"]:
            def fixed(field, lang, text, names):
                return fix_summary(text, field)

            try:
                cells, ingredients, backup = rewrite_summaries(options["pipeline"], fixed, "textfix", dry_run=dry_run)
            except (sqlite3.Error, ValueError) as exc:
                raise CommandError(f"cannot fix {options['pipeline']}: {exc}") from exc
            self.stdout.write(self.style.SUCCESS(
                f"{'(dry-run) ' if dry_run else ''}pipeline: {cells} summaries in {ingredients} ingredients fixed"
                + (f"; old text kept in {backup}" if backup else "")
            ))
