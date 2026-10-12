"""Rebuild the rule-based (no LLM) quiz question bank from the drug
flashcard facts -- up to 10 four-option questions per drug, 2 from each of
the five card sections. See apps.quiz.bank_generator for the distractor
logic.

Run build_flashcards first: this reads its FlashcardFact rows. Idempotent:
always replaces the full bank.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.flashcards.models import FlashcardFact
from apps.quiz.bank_generator import generate_bank
from apps.quiz.models import BankQuestion


class Command(BaseCommand):
    help = "Rebuild BankQuestion from the flashcard facts (run build_flashcards first; rule-based, no LLM)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Only this many ingredients (0 = all).")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"] or None
        dry_run = options["dry_run"]

        if not FlashcardFact.objects.exists():
            raise CommandError("No flashcard facts yet: run build_flashcards first.")

        questions = generate_bank(limit=limit)
        per_ingredient = len({q.ingredient_id for q in questions})
        self.stdout.write(f"generated {len(questions)} questions across {per_ingredient} ingredients")

        if dry_run:
            return

        with transaction.atomic():
            BankQuestion.objects.all().delete()
            BankQuestion.objects.bulk_create(questions, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(f"saved {len(questions)} bank questions"))
