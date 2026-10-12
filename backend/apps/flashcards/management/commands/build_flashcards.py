"""Rebuild every drug's flashcard facts (FlashcardFact) from its clinical-profile
summaries -- see apps.flashcards.card_facts for what goes in each of the five
sections.

Idempotent: always replaces all facts, so it's safe to re-run after the
summaries change. Run build_question_bank after it: the quiz bank is built
from these facts.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.flashcards.card_facts import build_fact_rows
from apps.flashcards.models import FlashcardFact
from apps.flashcards.sections import SECTION_META


class Command(BaseCommand):
    help = "Rebuild FlashcardFact from drug clinical-profile summaries (run before build_question_bank)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Only this many ingredients (0 = all).")
        parser.add_argument("--dry-run", action="store_true", help="Report, but write nothing.")

    def handle(self, *args, **options):
        rows, stats = build_fact_rows(limit=options["limit"] or None)

        self.stdout.write(f"{stats['drugs']} drugs with Persian card facts")
        for key, count in stats["by_section"].items():
            self.stdout.write(f"  {SECTION_META[key]['en']:<36} {count} facts")

        if options["dry_run"]:
            self.stdout.write("dry run: nothing written")
            return

        with transaction.atomic():
            FlashcardFact.objects.all().delete()
            FlashcardFact.objects.bulk_create(rows, batch_size=2000)

        self.stdout.write(self.style.SUCCESS(f"saved {len(rows)} flashcard facts"))
