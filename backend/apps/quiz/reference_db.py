"""The quiz bank and the flashcard facts as a portable reference-data file
(see apps.core.reference_db): study_content.db.

Written by `export_study_content_db` from a database that already holds the
content (the laptop, after `import_study_content`), loaded on another database
-- the production server -- by `import_study_content_db`.

Drugs are matched by RxCUI, which is the same on every database, never by
local row id. Tables:

    question       one row per quiz.BankQuestion  (source_id is the study_content question id)
    flashcard_fact one row per flashcards.FlashcardFact
"""

from collections import defaultdict

from django.db import transaction

from apps.core.reference_db import dumps, expected_count, loads, record_counts, rows
from apps.drugs.models import Ingredient
from apps.flashcards.models import FlashcardFact

from .models import BankQuestion

DATASET = "study_content"

SCHEMA = """
CREATE TABLE question (
    source_id INTEGER PRIMARY KEY, rxcui TEXT NOT NULL, field TEXT NOT NULL, difficulty TEXT NOT NULL,
    prompt_fa TEXT NOT NULL, prompt_en TEXT NOT NULL, options_fa TEXT NOT NULL, options_en TEXT NOT NULL,
    correct_index INTEGER NOT NULL, explanation_fa TEXT NOT NULL, explanation_en TEXT NOT NULL
);
CREATE TABLE flashcard_fact (
    rxcui TEXT NOT NULL, section TEXT NOT NULL, lang TEXT NOT NULL, ord INTEGER NOT NULL, text TEXT NOT NULL,
    PRIMARY KEY (rxcui, section, lang, ord)
);
"""


def export(conn):
    """Writes every bank question that came from study_content and every flashcard
    fact into `conn`. Returns the row counts."""
    conn.executescript(SCHEMA)
    rxcui = dict(Ingredient.objects.values_list("id", "rxcui"))

    questions = BankQuestion.objects.filter(source_id__isnull=False).order_by("source_id")
    conn.executemany(
        "INSERT INTO question VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        [
            (
                q.source_id, rxcui[q.ingredient_id], q.field, q.difficulty, q.prompt_fa, q.prompt_en,
                dumps(q.options_fa), dumps(q.options_en), q.correct_index, q.explanation_fa, q.explanation_en,
            )
            for q in questions.iterator(chunk_size=500)
        ],
    )
    facts = FlashcardFact.objects.order_by("ingredient_id", "section", "lang", "order")
    conn.executemany(
        "INSERT INTO flashcard_fact VALUES (?,?,?,?,?)",
        [(rxcui[f.ingredient_id], f.section, f.lang, f.order, f.text) for f in facts.iterator(chunk_size=2000)],
    )
    counts = {"question": questions.count(), "flashcard_fact": facts.count()}
    record_counts(conn, counts)
    return counts


def load(conn, meta, *, prune=False, log=print):
    """Upserts the file's questions (matched on `source_id`) and replaces, for
    every (drug, section, language) in the file, that group of flashcard facts.
    With `prune`, bank questions from study_content that are not in the file,
    and fact groups of drugs/sections the file does not mention, are deleted.
    Everything runs in one transaction. Returns a summary dict."""
    summary = {}
    ingredients = dict(Ingredient.objects.values_list("rxcui", "id"))
    missing = set()
    with transaction.atomic():
        # -- questions
        existing = {q.source_id: q.pk for q in BankQuestion.objects.filter(source_id__isnull=False).only("pk", "source_id")}
        created = updated = skipped = 0
        seen = set()
        for row in rows(conn, "SELECT * FROM question ORDER BY source_id", batch=200):
            ing = ingredients.get(row["rxcui"])
            if ing is None:
                missing.add(row["rxcui"]); skipped += 1
                continue
            seen.add(row["source_id"])
            fields = dict(
                ingredient_id=ing, field=row["field"], difficulty=row["difficulty"],
                prompt_fa=row["prompt_fa"], prompt_en=row["prompt_en"],
                options_fa=loads(row["options_fa"], []), options_en=loads(row["options_en"], []),
                correct_index=row["correct_index"],
                explanation_fa=row["explanation_fa"], explanation_en=row["explanation_en"],
            )
            pk = existing.get(row["source_id"])
            if pk is None:
                BankQuestion.objects.create(source_id=row["source_id"], **fields)
                created += 1
            else:
                BankQuestion.objects.filter(pk=pk).update(**fields)
                updated += 1
        summary["question"] = (created, updated)
        if skipped:
            summary["question skipped (drug not on this database)"] = skipped
        expected = expected_count(meta, "question")
        if expected is not None and len(seen) + skipped != expected:
            raise RuntimeError(f"Read {len(seen) + skipped} questions but the file says {expected}; it may be damaged.")
        if prune:
            gone = BankQuestion.objects.filter(source_id__isnull=False).exclude(source_id__in=seen)
            summary["question pruned"] = gone.count()
            gone.delete()

        # -- flashcard facts: whole (drug, section, language) groups are replaced
        groups = defaultdict(list)
        for row in rows(conn, "SELECT * FROM flashcard_fact ORDER BY rxcui, section, lang, ord", batch=2000):
            groups[(row["rxcui"], row["section"], row["lang"])].append(row)
        total = 0
        new_facts = []
        keep = set()
        for (rx, section, lang), items in groups.items():
            ing = ingredients.get(rx)
            if ing is None:
                missing.add(rx)
                continue
            keep.add((ing, section, lang))
            FlashcardFact.objects.filter(ingredient_id=ing, section=section, lang=lang).delete()
            new_facts += [
                FlashcardFact(ingredient_id=ing, section=section, lang=lang, order=i["ord"], text=i["text"]) for i in items
            ]
            total += len(items)
        FlashcardFact.objects.bulk_create(new_facts, batch_size=1000)
        summary["flashcard_fact"] = f"{total} in {len(keep)} groups"
        expected = expected_count(meta, "flashcard_fact")
        read = sum(len(v) for v in groups.values())
        if expected is not None and read != expected:
            raise RuntimeError(f"Read {read} flashcard facts but the file says {expected}; it may be damaged.")
        if prune:
            pruned = 0
            for fact in FlashcardFact.objects.values_list("pk", "ingredient_id", "section", "lang"):
                if (fact[1], fact[2], fact[3]) not in keep:
                    FlashcardFact.objects.filter(pk=fact[0]).delete()
                    pruned += 1
            summary["flashcard_fact pruned"] = pruned
    if missing:
        log(f"  no Ingredient for rxcui: {sorted(missing)[:10]}{' ...' if len(missing) > 10 else ''}")
    return summary
