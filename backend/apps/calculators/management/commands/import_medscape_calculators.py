"""Import the Medscape/QxMD interactive calculator snapshot into Postgres.

The upstream is a single JSON array (one object per calculator) holding its
questions and scoring formulas. The command is idempotent -- every calculator
is matched on its source `calculator_id` -- so it is safe to re-run as the
snapshot is refreshed.

`questions` and `results` are kept close to their source shape (trimmed of
internal bookkeeping ids) rather than normalized into their own tables: the
client always reads and renders a whole calculator as one document, and the
scoring `formula` strings reference answers/results by array position, so
`questions` and `results` are each sorted by their source `position` on the
way in.
"""

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.calculators.models import Calculator

DEFAULT_SOURCE = "/home/amir/Desktop/Documents/Medscape/calculator/medical_calculators.json"


def _names(items):
    """Flatten a list of {"name": ...} dicts (categories/tags) to plain names."""
    names = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        if name:
            names.append(name)
        for sub in item.get("subcategories") or []:
            if isinstance(sub, dict) and sub.get("name"):
                names.append(sub["name"])
    return names


def _clean_questions(questions):
    cleaned = []
    for q in sorted(questions or [], key=lambda q: q.get("position") or 0):
        cleaned.append({
            "position": q.get("position"),
            "title": q.get("title") or "",
            "type": q.get("type"),
            "more_information": q.get("more_information"),
            "initial_value": q.get("initial_value"),
            "choices": [
                {
                    "title_primary": c.get("title_primary"),
                    "title_secondary": c.get("title_secondary"),
                    "answer_factor": c.get("answer_factor"),
                }
                for c in (q.get("choices") or [])
            ],
            "units": [
                {
                    "title": u.get("title"),
                    "min_value": u.get("min_value"),
                    "max_value": u.get("max_value"),
                    "min_value_msg": u.get("min_value_msg"),
                    "max_value_msg": u.get("max_value_msg"),
                    "unit_factor": u.get("unit_factor"),
                    "initial_value": u.get("initial_value"),
                }
                for u in (q.get("units") or [])
            ],
        })
    return cleaned


def _clean_results(results):
    cleaned = []
    for r in sorted(results or [], key=lambda r: r.get("position") or 0):
        cleaned.append({
            "position": r.get("position"),
            "title": r.get("title") or "",
            "title_formula": r.get("title_formula"),
            "sub_title": r.get("sub_title"),
            "sub_title_formula": r.get("sub_title_formula"),
            "formula": r.get("formula"),
            "condition_formula": r.get("condition_formula"),
            "answer": r.get("answer"),
            "answer_primary": r.get("answer_primary"),
            "answer_secondary": r.get("answer_secondary"),
            "type": r.get("type"),
        })
    return cleaned


def _clean_references(references):
    return [
        {
            "names": r.get("names"),
            "sources": r.get("sources"),
            "papers": r.get("papers"),
        }
        for r in (references or [])
    ]


class Command(BaseCommand):
    help = "Import the Medscape/QxMD interactive calculator snapshot."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=DEFAULT_SOURCE,
            help=f"Path to the calculators JSON file (default: {DEFAULT_SOURCE}).",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Import at most this many calculators (0 = all).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Read and report, but roll back all writes.",
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_file():
            raise CommandError(f"Source file not found: {source}")

        with source.open(encoding="utf-8") as f:
            records = json.load(f)
        if not isinstance(records, list):
            raise CommandError("Expected a JSON array of calculators.")

        limit = options["limit"]
        if limit > 0:
            records = records[:limit]
        dry_run = options["dry_run"]

        created = updated = skipped = 0
        with transaction.atomic():
            for rec in records:
                calculator_id = str(rec.get("calculator_id") or "").strip()
                name = (rec.get("name") or "").strip()
                if not calculator_id or not name:
                    skipped += 1
                    continue

                _, was_created = Calculator.objects.update_or_create(
                    calculator_id=calculator_id,
                    defaults={
                        "slug": Calculator.build_slug(name, calculator_id),
                        "name": name,
                        "description": (rec.get("description") or "").strip(),
                        "about": rec.get("about") or "",
                        "author": rec.get("author") or "",
                        "categories": _names(rec.get("categories")),
                        "tags": _names(rec.get("tags")),
                        "questions": _clean_questions(rec.get("questions")),
                        "results": _clean_results(rec.get("results")),
                        "references": _clean_references(rec.get("references")),
                    },
                )
                created += was_created
                updated += not was_created

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            "import_medscape_calculators %s: %d created / %d updated, %d skipped"
            % ("(dry-run)" if dry_run else "done", created, updated, skipped)
        ))
