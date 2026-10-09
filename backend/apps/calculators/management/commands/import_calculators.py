"""Import the bilingual (en/fa) calculator snapshot into Postgres.

The source is a SQLite file produced by a separate translation pipeline (see
--source's default) -- a properly normalized schema (calculator / category /
tag / question / choice / question_unit / result / error_check / reference),
every user-facing column paired with a `_fa` counterpart. This command reads
it with the stdlib's own `sqlite3` module (read-only, no new dependency) and
denormalizes questions/results/error_checks back into JSON blobs on each
`Calculator` row -- see that model's docstring for why.

Idempotent and safe to re-run: categories/tags are matched on the source's
own `external_id`, calculators on `uid`.
"""

import json
import sqlite3
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.calculators.models import Calculator, CalculatorCategory, CalculatorTag

DEFAULT_SOURCE = "/home/amir/Documents/Learning Platform/backend/data/calculators_all.sqlite"


def _rows(conn, sql, params=()):
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    for row in cur:
        yield dict(zip(cols, row))


def _import_categories(conn):
    """Two passes: every row created first (so self-FK `parent` targets
    always exist already), then every `parent` wired up."""
    by_external_id = {}
    pending_parents = {}  # external_id -> parent's external_id
    for row in _rows(conn, "SELECT * FROM category"):
        cat, _ = CalculatorCategory.objects.update_or_create(
            external_id=row["external_id"],
            defaults={
                "name": row["name"] or "",
                "name_fa": row["name_fa"] or "",
                "is_main_category": bool(row["is_main_category"]),
            },
        )
        by_external_id[row["external_id"]] = cat
        if row["parent_id"] is not None:
            pending_parents[row["external_id"]] = row["parent_id"]

    # `parent_id` in the source is a local row id, not an external_id -- map
    # it through the source `category.id` -> `external_id` first.
    source_id_to_external = {
        row["id"]: row["external_id"] for row in _rows(conn, "SELECT id, external_id FROM category")
    }
    for external_id, parent_source_id in pending_parents.items():
        parent_external_id = source_id_to_external.get(parent_source_id)
        if parent_external_id is None:
            continue
        cat = by_external_id[external_id]
        cat.parent = by_external_id.get(parent_external_id)
        cat.save(update_fields=["parent"])

    return by_external_id


def _import_tags(conn):
    by_external_id = {}
    for row in _rows(conn, "SELECT * FROM tag"):
        tag, _ = CalculatorTag.objects.update_or_create(
            external_id=row["external_id"],
            defaults={"name": row["name"] or "", "name_fa": row["name_fa"] or ""},
        )
        by_external_id[row["external_id"]] = tag
    return by_external_id


def _questions_for(conn, calculator_source_id):
    questions = []
    for q in _rows(
        conn,
        "SELECT * FROM question WHERE calculator_id = ? ORDER BY position",
        (calculator_source_id,),
    ):
        choices = [
            {
                "title_primary": c["title_primary"] or "",
                "title_primary_fa": c["title_primary_fa"] or "",
                "title_secondary": c["title_secondary"],
                "title_secondary_fa": c["title_secondary_fa"],
                "answer_factor": c["answer_factor"],
            }
            for c in _rows(
                conn,
                "SELECT * FROM choice WHERE question_id = ? ORDER BY position",
                (q["id"],),
            )
        ]
        units = [
            {
                "title": u["title"] or "",
                "title_fa": u["title_fa"] or "",
                "min_value": u["min_value"],
                "max_value": u["max_value"],
                "min_value_msg": u["min_value_msg"],
                "min_value_msg_fa": u["min_value_msg_fa"],
                "max_value_msg": u["max_value_msg"],
                "max_value_msg_fa": u["max_value_msg_fa"],
                "unit_factor": u["unit_factor"],
                "initial_value": u["initial_value"],
            }
            for u in _rows(
                conn,
                "SELECT * FROM question_unit WHERE question_id = ? ORDER BY position",
                (q["id"],),
            )
        ]
        questions.append({
            "position": q["position"],
            "title": q["title"] or "",
            "title_fa": q["title_fa"] or "",
            "type": q["type"],
            "more_information": q["more_information"],
            "more_information_fa": q["more_information_fa"],
            "section_name": q["section_name"],
            "section_name_fa": q["section_name_fa"],
            "initial_value": q["initial_value"],
            "choices": choices,
            "units": units,
        })
    return questions


def _results_for(conn, calculator_source_id):
    return [
        {
            "position": r["position"],
            "title": r["title"] or "",
            "title_fa": r["title_fa"] or "",
            "title_formula": r["title_formula"],
            "sub_title": r["sub_title"],
            "sub_title_fa": r["sub_title_fa"],
            "sub_title_formula": r["sub_title_formula"],
            "formula": r["formula"],
            "condition_formula": r["condition_formula"],
            "answer": r["answer"],
            "answer_fa": r["answer_fa"],
            "type": r["type"],
        }
        for r in _rows(
            conn,
            "SELECT * FROM result WHERE calculator_id = ? ORDER BY position",
            (calculator_source_id,),
        )
    ]


def _formula_strings_fa(raw):
    """English text literal -> Persian translation, for strings a result's
    formula returns itself ("Positive", a whole clinical-implication
    sentence) -- the `answer_fa` template around them is translated, but
    the formula's own output never is, so without this map every such
    result shows English in Persian mode."""
    try:
        mapping = json.loads(raw or "{}")
    except (TypeError, ValueError):
        return {}
    if not isinstance(mapping, dict):
        return {}
    return {
        k: v for k, v in mapping.items()
        if isinstance(k, str) and isinstance(v, str) and k.strip() and v.strip()
    }


def _error_checks_for(conn, calculator_source_id):
    return [
        {
            "position": e["position"],
            "type": e["type"],
            "title": e["title"] or "",
            "title_fa": e["title_fa"] or "",
            "answer": e["answer"],
            "answer_fa": e["answer_fa"],
            "formula": e["formula"],
        }
        for e in _rows(
            conn,
            "SELECT * FROM error_check WHERE calculator_id = ? ORDER BY position",
            (calculator_source_id,),
        )
    ]


def _references_for(conn, calculator_source_id):
    return [
        {"names": r["names"], "sources": r["sources"], "papers": r["papers"]}
        for r in _rows(
            conn,
            "SELECT * FROM reference WHERE calculator_id = ? ORDER BY position",
            (calculator_source_id,),
        )
    ]


class Command(BaseCommand):
    help = "Import the bilingual (en/fa) calculator snapshot from its SQLite source."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=DEFAULT_SOURCE,
            help=f"Path to the calculators SQLite file (default: {DEFAULT_SOURCE}).",
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
        dry_run = options["dry_run"]
        limit = options["limit"]

        conn = sqlite3.connect(str(source))
        conn.row_factory = sqlite3.Row
        try:
            created = updated = skipped = 0
            with transaction.atomic():
                categories_by_external_id = _import_categories(conn)
                tags_by_external_id = _import_tags(conn)

                calc_rows = list(_rows(conn, "SELECT * FROM calculator ORDER BY id"))
                if limit > 0:
                    calc_rows = calc_rows[:limit]

                for rec in calc_rows:
                    calculator_id = str(rec["calculator_id"] or "").strip()
                    uid = (rec["uid"] or "").strip()
                    name = (rec["name"] or "").strip()
                    if not uid or not calculator_id or not name:
                        skipped += 1
                        continue

                    calculator, was_created = Calculator.objects.update_or_create(
                        uid=uid,
                        defaults={
                            "calculator_id": calculator_id,
                            "url": rec["url"] or "",
                            "slug": Calculator.build_slug(name, calculator_id),
                            "name": name,
                            "name_fa": rec["name_fa"] or "",
                            "description": (rec["description"] or "").strip(),
                            "description_fa": (rec["description_fa"] or "").strip(),
                            "about": rec["about"] or "",
                            "about_fa": rec["about_fa"] or "",
                            "disclaimer_footer": rec["disclaimer_footer"] or "",
                            "disclaimer_footer_fa": rec["disclaimer_footer_fa"] or "",
                            "questions": _questions_for(conn, rec["id"]),
                            "results": _results_for(conn, rec["id"]),
                            "error_checks": _error_checks_for(conn, rec["id"]),
                            "formula_strings_fa": _formula_strings_fa(rec["formula_strings_fa"]),
                            "references": _references_for(conn, rec["id"]),
                        },
                    )
                    created += was_created
                    updated += not was_created

                    cat_external_ids = [
                        row["category_id"]
                        for row in _rows(
                            conn,
                            "SELECT c.external_id AS category_id FROM calculator_category cc "
                            "JOIN category c ON c.id = cc.category_id WHERE cc.calculator_id = ?",
                            (rec["id"],),
                        )
                    ]
                    calculator.categories.set(
                        categories_by_external_id[cid] for cid in cat_external_ids
                        if cid in categories_by_external_id
                    )
                    tag_external_ids = [
                        row["tag_id"]
                        for row in _rows(
                            conn,
                            "SELECT t.external_id AS tag_id FROM calculator_tag ct "
                            "JOIN tag t ON t.id = ct.tag_id WHERE ct.calculator_id = ?",
                            (rec["id"],),
                        )
                    ]
                    calculator.tags.set(
                        tags_by_external_id[tid] for tid in tag_external_ids
                        if tid in tags_by_external_id
                    )

                if dry_run:
                    transaction.set_rollback(True)
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS(
            "import_calculators %s: %d created / %d updated, %d skipped, "
            "%d categories, %d tags"
            % (
                "(dry-run)" if dry_run else "done",
                created, updated, skipped,
                len(categories_by_external_id), len(tags_by_external_id),
            )
        ))
