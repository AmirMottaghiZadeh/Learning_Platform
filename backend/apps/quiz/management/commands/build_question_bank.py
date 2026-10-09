"""Rebuild the rule-based (no LLM) quiz question bank from the drug
clinical-profile summaries -- see apps.quiz.bank_generator for the actual
fact-extraction and distractor logic.

Idempotent: always replaces the full bank, so it's safe to re-run after the
source summaries change (e.g. after clean_profile_boilerplate).
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.quiz.bank_generator import generate_bank
from apps.quiz.models import BankQuestion


class Command(BaseCommand):
    help = "Rebuild BankQuestion from drug clinical-profile summaries (rule-based, no LLM)."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0, help="Only this many ingredients (0 = all).")
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        limit = options["limit"] or None
        dry_run = options["dry_run"]

        questions = generate_bank(limit=limit)
        per_ingredient = len({q.ingredient_id for q in questions})
        self.stdout.write(f"generated {len(questions)} questions across {per_ingredient} ingredients")

        if dry_run:
            return

        with transaction.atomic():
            BankQuestion.objects.all().delete()
            BankQuestion.objects.bulk_create(questions, batch_size=1000)

        self.stdout.write(self.style.SUCCESS(f"saved {len(questions)} bank questions"))
