"""Load the quiz questions and flashcards made by the study_content pipeline.

Source: the SQLite database /home/amir/Documents/openfda/study_content/study_content.db
(opened read-only). Questions go to quiz.BankQuestion, flashcard phrases to
flashcards.FlashcardFact. The command replaces whatever those two tables hold
(wipe-and-reload, idempotent), like import_openfda.

Which rows: those whose status is in --statuses. The default is draft, verified
and approved, i.e. everything except auto_rejected, flagged and rejected, so a first
look in the app is possible before the verifier and the human review have run.

Flashcard kind -> card section:
    indication -> indication, mechanism -> mechanism, adverse_common -> adr_common,
    adverse_serious -> adr_serious, interaction -> interaction, warning -> warning,
    boxed_warning -> contra_boxed
Each phrase of a flashcard becomes one FlashcardFact per language.

Question topic -> field: the topic key itself, except contraindication -> contra_boxed.
Difficulty 1-2 -> medium, 3 -> hard.
"""
import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.drugs.models import Ingredient
from apps.flashcards.models import FlashcardFact
from apps.quiz.models import BankQuestion

DEFAULT_SOURCE = "/home/amir/Documents/openfda/study_content/study_content.db"
DEFAULT_STATUSES = "draft,verified,approved"

CARD_KIND_TO_SECTION = {
    "indication": "indication",
    "mechanism": "mechanism",
    "adverse_common": "adr_common",
    "adverse_serious": "adr_serious",
    "interaction": "interaction",
    "warning": "warning",
    "boxed_warning": "contra_boxed",
}
TOPIC_TO_FIELD = {
    "indication": "indication",
    "mechanism": "mechanism",
    "adverse_effect": "adverse_effect",
    "contraindication": "contra_boxed",
    "interaction": "interaction",
    "class_level": "class_level",
    "pregnancy": "pregnancy",
    "counseling": "counseling",
    "monitoring": "monitoring",
}


class Command(BaseCommand):
    help = "Import quiz questions and flashcards from the study_content pipeline database."

    def add_arguments(self, parser):
        parser.add_argument("--source", default=DEFAULT_SOURCE, help=f"Path to study_content.db (default: {DEFAULT_SOURCE}).")
        parser.add_argument("--statuses", default=DEFAULT_STATUSES, help="Comma list of statuses to import.")
        parser.add_argument("--dry-run", action="store_true", help="Read and report, then roll back.")

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_file():
            raise CommandError(f"Source database not found: {source}")
        statuses = [s.strip() for s in options["statuses"].split(",") if s.strip()]
        marks = ",".join("?" * len(statuses))

        conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        ingredients = {i.rxcui: i.id for i in Ingredient.objects.only("id", "rxcui")}
        missing = set()
        stats = {"questions": 0, "facts": 0, "cards": 0, "skipped_no_ingredient": 0, "skipped_bad": 0}

        try:
            with transaction.atomic():
                BankQuestion.objects.all().delete()
                FlashcardFact.objects.all().delete()

                # -- questions
                questions = []
                for q in conn.execute(f"SELECT * FROM question WHERE status IN ({marks}) ORDER BY id", statuses):
                    ing = ingredients.get(q["rxcui"])
                    if ing is None:
                        missing.add(q["rxcui"]); stats["skipped_no_ingredient"] += 1
                        continue
                    opts = list(conn.execute("SELECT * FROM question_option WHERE question_id=? ORDER BY idx", (q["id"],)))
                    field = TOPIC_TO_FIELD.get(q["topic"])
                    if len(opts) != 4 or field is None or not opts[q["correct_index"]]["is_correct"]:
                        stats["skipped_bad"] += 1
                        continue
                    questions.append(BankQuestion(
                        ingredient_id=ing, field=field,
                        prompt_fa=q["stem_fa"], prompt_en=q["stem_en"],
                        options_fa=[o["text_fa"] for o in opts], options_en=[o["text_en"] for o in opts],
                        correct_index=q["correct_index"],
                        explanation_fa=q["explanation_fa"], explanation_en=q["explanation_en"],
                        difficulty="hard" if q["difficulty"] >= 3 else "medium",
                        source_id=q["id"],
                    ))
                BankQuestion.objects.bulk_create(questions, batch_size=500)
                stats["questions"] = len(questions)

                # -- flashcards: one fact per phrase and language, in card order within a section
                facts, order = [], {}
                for c in conn.execute(f"SELECT * FROM flashcard WHERE status IN ({marks}) ORDER BY id", statuses):
                    ing = ingredients.get(c["rxcui"])
                    section = CARD_KIND_TO_SECTION.get(c["kind"])
                    if ing is None:
                        missing.add(c["rxcui"]); stats["skipped_no_ingredient"] += 1
                        continue
                    if section is None:
                        stats["skipped_bad"] += 1
                        continue
                    stats["cards"] += 1
                    for it in conn.execute("SELECT * FROM flashcard_item WHERE flashcard_id=? ORDER BY idx", (c["id"],)):
                        for lang, text in (("fa", it["text_fa"]), ("en", it["text_en"])):
                            n = order.get((ing, section, lang), 0)
                            order[(ing, section, lang)] = n + 1
                            facts.append(FlashcardFact(ingredient_id=ing, section=section, lang=lang, order=n, text=text))
                FlashcardFact.objects.bulk_create(facts, batch_size=1000)
                stats["facts"] = len(facts)

                if options["dry_run"]:
                    transaction.set_rollback(True)
        finally:
            conn.close()

        if missing:
            self.stdout.write(self.style.WARNING(f"No Ingredient for rxcui: {sorted(missing)[:10]}{' ...' if len(missing) > 10 else ''}"))
        self.stdout.write(self.style.SUCCESS(
            "import_study_content %s: %d questions, %d flashcards -> %d facts, skipped %d (no ingredient) + %d (unmapped/invalid)"
            % ("(dry-run)" if options["dry_run"] else "done", stats["questions"], stats["cards"], stats["facts"],
               stats["skipped_no_ingredient"], stats["skipped_bad"])
        ))
