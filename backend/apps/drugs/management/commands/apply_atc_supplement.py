"""Give unclassified ingredients their ATC classes from the curated
supplement (apps.drugs.data.atc_supplement), without a full openFDA
re-import.

Only touches ingredients that currently have no ATC code at all -- a code
the source provided is never replaced. Idempotent: a second run finds
nothing left to do. Afterwards, rebuild the question bank
(`manage.py build_question_bank`) so the newly classified drugs get
questions too; lessons pick them up immediately.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.drugs.data.atc_supplement import ATC_SUPPLEMENT
from apps.drugs.models import AtcCode, Ingredient


class Command(BaseCommand):
    help = "Assign curated RxClass ATC codes to ingredients that have none."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Report what would change, write nothing.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        unclassified = Ingredient.objects.filter(rxcui__in=ATC_SUPPLEMENT.keys(), atc_codes__isnull=True)

        updated = []
        with transaction.atomic():
            for ingredient in unclassified:
                codes = []
                for code, name in ATC_SUPPLEMENT[ingredient.rxcui][2]:
                    obj, _ = AtcCode.objects.get_or_create(code=code, defaults={"name": name})
                    codes.append(obj)
                if not dry_run:
                    ingredient.atc_codes.set(codes)
                updated.append(f"{ingredient.name} -> {', '.join(c.code for c in codes)}")
            if dry_run:
                transaction.set_rollback(True)

        for line in updated:
            self.stdout.write(f"  {line}")
        verb = "would classify" if dry_run else "classified"
        self.stdout.write(self.style.SUCCESS(f"{verb} {len(updated)} ingredients"))
