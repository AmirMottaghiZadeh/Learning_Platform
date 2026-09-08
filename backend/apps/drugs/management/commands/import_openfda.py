"""Import the OpenFDA ingredient clinical profiles into Postgres.

The upstream is the read-only SQLite database built by the openfda pipeline.
Only the tables the app needs are read: ``ingredient_clinical_profiles`` (one
row per ingredient, carrying every clinical field plus its fa/en summary) and
``ingredient_atc_codes`` (a fallback source of ATC / pharm-class codes).

The command is idempotent — every ingredient is matched on its RXCUI — so it is
safe to re-run as upstream summaries get filled in. ``--only-summaries`` limits
the write to the ``summary_fa`` / ``summary_en`` columns of sections that
already exist, which is the common case once the raw text is stable.
"""

import json
import sqlite3
from datetime import datetime, timezone as dt_timezone
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.drugs.models import (
    CLINICAL_FIELD_KEYS,
    AtcCode,
    Ingredient,
    IngredientProfileSection,
)


DEFAULT_SOURCE = "/home/amir/Documents/openfda/pipeline_v2/pipeline_v2.db"


def _int(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _json_list(value):
    if not value:
        return []
    try:
        parsed = json.loads(value)
    except (TypeError, ValueError):
        return []
    return parsed if isinstance(parsed, list) else []


def _parse_fetched_at(value):
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(value, fmt).replace(tzinfo=dt_timezone.utc)
        except (TypeError, ValueError):
            continue
    return None


class Command(BaseCommand):
    help = "Import OpenFDA ingredient clinical profiles from the pipeline SQLite DB."

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            default=DEFAULT_SOURCE,
            help=f"Path to the pipeline SQLite file (default: {DEFAULT_SOURCE}).",
        )
        parser.add_argument(
            "--only-summaries",
            action="store_true",
            help="Only update summary_fa / summary_en on existing sections.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=0,
            help="Import at most this many ingredients (0 = all).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Read and report, but roll back all writes.",
        )

    def handle(self, *args, **options):
        source = Path(options["source"])
        if not source.is_file():
            raise CommandError(f"Source database not found: {source}")

        only_summaries = options["only_summaries"]
        limit = options["limit"]
        dry_run = options["dry_run"]

        conn = sqlite3.connect(f"file:{source}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        try:
            atc_fallback = self._load_atc_fallback(conn)
            rows = self._iter_profiles(conn, limit)
            stats = self._import(rows, atc_fallback, only_summaries, dry_run)
        finally:
            conn.close()

        self.stdout.write(self.style.SUCCESS(
            "import_openfda %s: ingredients %d created / %d updated, "
            "sections %d written, ATC codes %d, skipped %d"
            % (
                "(dry-run)" if dry_run else "done",
                stats["ingredients_created"],
                stats["ingredients_updated"],
                stats["sections_written"],
                stats["atc_codes"],
                stats["skipped"],
            )
        ))

    # -- reading -------------------------------------------------------------

    def _load_atc_fallback(self, conn):
        """rxcui -> ({code: name}, [pharm_class, ...]) from ingredient_atc_codes."""
        fallback = {}
        try:
            cursor = conn.execute(
                "SELECT ingredient_rxcui, atc_codes_json, epc_codes_json "
                "FROM ingredient_atc_codes"
            )
        except sqlite3.OperationalError:
            return fallback
        for row in cursor:
            codes = {
                item["atc_code"]: item.get("atc_name", "")
                for item in _json_list(row["atc_codes_json"])
                if isinstance(item, dict) and item.get("atc_code")
            }
            epc = [c for c in _json_list(row["epc_codes_json"]) if isinstance(c, str)]
            fallback[str(row["ingredient_rxcui"])] = (codes, epc)
        return fallback

    def _iter_profiles(self, conn, limit):
        sql = "SELECT * FROM ingredient_clinical_profiles ORDER BY ingredient_name"
        if limit and limit > 0:
            sql += f" LIMIT {int(limit)}"
        return conn.execute(sql)

    # -- writing ----------------------------------------------------------

    def _import(self, rows, atc_fallback, only_summaries, dry_run):
        stats = {
            "ingredients_created": 0,
            "ingredients_updated": 0,
            "sections_written": 0,
            "atc_codes": 0,
            "skipped": 0,
        }
        atc_cache = {}

        with transaction.atomic():
            for row in rows:
                rxcui = str(row["ingredient_rxcui"] or "").strip()
                name = (row["ingredient_name"] or "").strip()
                if not rxcui or not name:
                    stats["skipped"] += 1
                    continue

                if only_summaries:
                    self._sync_summaries(row, stats)
                    continue

                ingredient, created = Ingredient.objects.update_or_create(
                    rxcui=rxcui,
                    defaults={
                        "name": name,
                        "slug": Ingredient.build_slug(name, rxcui),
                        "n_products": _int(row["n_products"]),
                        "n_source_records": _int(row["n_source_records"]),
                        "pharm_classes": self._pharm_classes(row, rxcui, atc_fallback),
                    },
                )
                stats["ingredients_created" if created else "ingredients_updated"] += 1

                self._set_atc(ingredient, row, rxcui, atc_fallback, atc_cache, stats)
                self._write_sections(ingredient, row, stats)

            if dry_run:
                transaction.set_rollback(True)

        stats["atc_codes"] = len(atc_cache)
        return stats

    def _pharm_classes(self, row, rxcui, atc_fallback):
        classes = [c for c in _json_list(row["pharm_class_epc"]) if isinstance(c, str)]
        if classes:
            return classes
        return atc_fallback.get(rxcui, ({}, []))[1]

    def _set_atc(self, ingredient, row, rxcui, atc_fallback, atc_cache, stats):
        pairs = {
            item["atc_code"]: item.get("atc_name", "")
            for item in _json_list(row["atc_codes"])
            if isinstance(item, dict) and item.get("atc_code")
        }
        if not pairs:
            pairs = atc_fallback.get(rxcui, ({}, []))[0]
        if not pairs:
            ingredient.atc_codes.clear()
            return

        codes = []
        for code, atc_name in pairs.items():
            obj = atc_cache.get(code)
            if obj is None:
                obj, _ = AtcCode.objects.get_or_create(
                    code=code, defaults={"name": atc_name or code}
                )
                if atc_name and obj.name != atc_name:
                    obj.name = atc_name
                    obj.save(update_fields=["name"])
                atc_cache[code] = obj
            codes.append(obj)
        ingredient.atc_codes.set(codes)

    def _write_sections(self, ingredient, row, stats):
        keys = row.keys()
        for field in CLINICAL_FIELD_KEYS:
            if field not in keys:
                continue
            IngredientProfileSection.objects.update_or_create(
                ingredient=ingredient,
                field=field,
                defaults={
                    "raw_text": (row[field] or "").strip(),
                    "n_contributing_products": _int(
                        row[f"{field}_n_contributing_products"]
                        if f"{field}_n_contributing_products" in keys
                        else 0
                    ),
                    "summary_fa": (row[f"{field}_summary_fa"] or "").strip()
                    if f"{field}_summary_fa" in keys
                    else "",
                    "summary_en": (row[f"{field}_summary_en"] or "").strip()
                    if f"{field}_summary_en" in keys
                    else "",
                },
            )
            stats["sections_written"] += 1

    def _sync_summaries(self, row, stats):
        rxcui = str(row["ingredient_rxcui"] or "").strip()
        try:
            ingredient = Ingredient.objects.get(rxcui=rxcui)
        except Ingredient.DoesNotExist:
            stats["skipped"] += 1
            return

        keys = row.keys()
        existing = {s.field: s for s in ingredient.sections.all()}
        for field, section in existing.items():
            fa_col, en_col = f"{field}_summary_fa", f"{field}_summary_en"
            fa = (row[fa_col] or "").strip() if fa_col in keys else section.summary_fa
            en = (row[en_col] or "").strip() if en_col in keys else section.summary_en
            if fa != section.summary_fa or en != section.summary_en:
                section.summary_fa = fa
                section.summary_en = en
                section.save(update_fields=["summary_fa", "summary_en", "updated_at"])
                stats["sections_written"] += 1
