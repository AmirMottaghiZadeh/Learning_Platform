"""The openfda drug profiles as portable reference-data files (see
apps.core.reference_db), for loading a database that has no pipeline file --
the production server -- with exactly what `import_openfda` wrote into this
one: ingredients, their ATC codes and their profile sections (the label text
and the fa/en summaries, as cleaned here).

Unlike the other datasets the data is split over parts of at most
`max_bytes` each (openfda.part01.db, openfda.part02.db ...), so no file
outgrows what can be uploaded in one go. Every part is a complete SQLite file
with the same tables and the usual `meta`, plus the export's id and the part's
number and count: an import refuses an incomplete set or parts of two
different exports. The ingredients and ATC codes travel in part 1, the
sections fill the parts in order.

Tables: atc_code, ingredient (pharm_classes as JSON text), ingredient_atc,
section.
"""

import hashlib
import sqlite3
import uuid
from pathlib import Path

from django.core.management.base import CommandError
from django.db import transaction
from django.db.models.functions import MD5
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from apps.core.reference_db import FORMAT, SCHEMA_VERSION, dumps, loads, rows

from .models import AtcCode, Ingredient, IngredientProfileSection

DATASET = "openfda"
PART_GLOB = f"{DATASET}.part*.db"

SCHEMA = """
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE atc_code (code TEXT PRIMARY KEY, name TEXT NOT NULL, name_fa TEXT NOT NULL);
CREATE TABLE ingredient (
    rxcui TEXT PRIMARY KEY, name TEXT NOT NULL, name_fa TEXT NOT NULL, slug TEXT NOT NULL,
    n_products INTEGER NOT NULL, n_source_records INTEGER NOT NULL, pharm_classes TEXT NOT NULL,
    source_fetched_at TEXT
);
CREATE TABLE ingredient_atc (rxcui TEXT NOT NULL, code TEXT NOT NULL);
CREATE TABLE section (
    rxcui TEXT NOT NULL, field TEXT NOT NULL, raw_text TEXT NOT NULL,
    n_contributing_products INTEGER NOT NULL, summary_fa TEXT NOT NULL, summary_en TEXT NOT NULL,
    PRIMARY KEY (rxcui, field)
);
"""

_SECTION_FIELDS = ("raw_text", "n_contributing_products", "summary_fa", "summary_en")


def part_name(number):
    return f"{DATASET}.part{number:02d}.db"


class _Parts:
    """Writes the parts one after another, each a `.partial` file until the
    whole export is done (see export)."""

    def __init__(self, out, max_bytes, export_id):
        self.out, self.max_bytes, self.export_id = out, max_bytes, export_id
        self.paths, self.counts, self.conn = [], [], None
        self.next()

    def next(self):
        if self.conn is not None:
            self.conn.commit()
            self.conn.close()
        path = self.out / (part_name(len(self.paths) + 1) + ".partial")
        path.unlink(missing_ok=True)
        self.conn = sqlite3.connect(path)
        self.conn.execute("PRAGMA journal_mode = OFF")
        self.conn.execute("PRAGMA synchronous = OFF")
        self.conn.executescript(SCHEMA)
        self.paths.append(path)
        self.counts.append({"atc_code": 0, "ingredient": 0, "ingredient_atc": 0, "section": 0})

    def size(self):
        page_count = self.conn.execute("PRAGMA page_count").fetchone()[0]
        return page_count * self.conn.execute("PRAGMA page_size").fetchone()[0]

    def close(self, exported_at):
        """Finishes every part's meta now that their number is known."""
        self.conn.commit()
        self.conn.close()
        for number, (path, counts) in enumerate(zip(self.paths, self.counts), start=1):
            conn = sqlite3.connect(path)
            meta = {
                "format": FORMAT,
                "schema_version": str(SCHEMA_VERSION),
                "dataset": DATASET,
                "exported_at": exported_at,
                "export_id": self.export_id,
                "part": str(number),
                "parts": str(len(self.paths)),
                **{f"count.{table}": str(n) for table, n in counts.items()},
            }
            conn.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())
            conn.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)
            conn.commit()
            conn.close()


def export(out, max_bytes, log=print):
    """Writes this database's openfda data into parts of at most `max_bytes`
    in the directory `out`, replacing the parts of an earlier export there
    only once the new set is complete. Returns (paths, total row counts)."""
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    parts = _Parts(out, max_bytes, uuid.uuid4().hex)
    try:
        conn, counts = parts.conn, parts.counts[0]
        conn.executemany(
            "INSERT INTO atc_code VALUES (?, ?, ?)",
            [(a.code, a.name, a.name_fa or "") for a in AtcCode.objects.order_by("code")],
        )
        counts["atc_code"] = AtcCode.objects.count()
        links = []
        for i in Ingredient.objects.order_by("rxcui").prefetch_related("atc_codes").iterator(chunk_size=500):
            conn.execute(
                "INSERT INTO ingredient VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (i.rxcui, i.name, i.name_fa or "", i.slug, i.n_products, i.n_source_records,
                 dumps(i.pharm_classes or []), i.source_fetched_at.isoformat() if i.source_fetched_at else None),
            )
            links += [(i.rxcui, a.code) for a in i.atc_codes.all()]
            counts["ingredient"] += 1
        conn.executemany("INSERT INTO ingredient_atc VALUES (?, ?)", links)
        counts["ingredient_atc"] = len(links)

        sections = (
            IngredientProfileSection.objects.select_related("ingredient")
            .order_by("ingredient__rxcui", "field")
            .only("field", *_SECTION_FIELDS, "ingredient__rxcui")
        )
        for n, s in enumerate(sections.iterator(chunk_size=500), start=1):
            row = (s.ingredient.rxcui, s.field, s.raw_text or "", s.n_contributing_products,
                   s.summary_fa or "", s.summary_en or "")
            # Room for the row (its text, generously counted) or a new part.
            needed = 2 * sum(len(str(v).encode()) for v in row) + 65536
            if n % 200 == 0:
                parts.conn.commit()
            if parts.counts[-1]["section"] and parts.size() + needed > parts.max_bytes:
                log(f"  part {len(parts.paths)}: {parts.size() / 1_000_000:.0f} MB")
                parts.next()
            parts.conn.execute("INSERT INTO section VALUES (?, ?, ?, ?, ?, ?)", row)
            parts.counts[-1]["section"] += 1
        parts.close(timezone.now().isoformat())
    except BaseException:
        if parts.conn is not None:
            try:
                parts.conn.close()
            except sqlite3.Error:
                pass
        for path in parts.paths:
            path.unlink(missing_ok=True)
        raise

    for old in out.glob(PART_GLOB):
        old.unlink()
    final = []
    for path in parts.paths:
        target = path.with_name(path.name[: -len(".partial")])
        path.replace(target)
        final.append(target)
    totals = {table: sum(c[table] for c in parts.counts) for table in parts.counts[0]}
    return final, totals


def open_parts(source):
    """Opens the parts of one export -- `source` is the directory holding
    them or a single part's path -- after checking that they are openfda
    parts of this format, all of one export, and that none is missing.
    Returns [(connection, meta)] in part order."""
    source = Path(source)
    paths = sorted(source.glob(PART_GLOB)) if source.is_dir() else [source]
    if not paths or not all(p.is_file() for p in paths):
        raise CommandError(f"No {PART_GLOB} files in {source}")
    opened = []
    for path in paths:
        try:
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
        except sqlite3.DatabaseError as exc:
            raise CommandError(f"{path} is not a reference-data file ({exc}).") from exc
        if meta.get("format") != FORMAT or meta.get("dataset") != DATASET:
            raise CommandError(f"{path} is not an {DATASET} reference-data file.")
        if meta.get("schema_version") != str(SCHEMA_VERSION):
            raise CommandError(f"{path} is format version {meta.get('schema_version')}; this code reads {SCHEMA_VERSION}.")
        opened.append((conn, meta))
    ids = {meta["export_id"] for _, meta in opened}
    if len(ids) != 1:
        raise CommandError(f"{source} holds parts of {len(ids)} different exports; keep only one.")
    numbers = sorted(int(meta["part"]) for _, meta in opened)
    expected = int(opened[0][1]["parts"])
    if numbers != list(range(1, expected + 1)):
        missing = sorted(set(range(1, expected + 1)) - set(numbers))
        raise CommandError(f"This export has {expected} parts; missing: {', '.join(part_name(n) for n in missing)}.")
    return sorted(opened, key=lambda item: int(item[1]["part"]))


def _checked(conn, meta, table, sql):
    """The rows of `table`, after checking the part holds as many as it says."""
    expected = int(meta.get(f"count.{table}", "0"))
    found = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    if found != expected:
        raise CommandError(f"part {meta['part']}: {table} has {found} rows, its meta says {expected}.")
    return rows(conn, sql)


def _digest(text):
    return hashlib.md5((text or "").encode()).hexdigest()


def load(parts, log=print):
    """Adds or updates the parts' ATC codes, ingredients (matched on RxCUI)
    and profile sections (on ingredient and field), and sets each of the
    file's ingredients' ATC codes to the file's. Nothing is deleted: an
    ingredient carries the quiz questions and flashcards made from it. Only
    rows that differ are written, and the sections are compared by digest,
    so a target across a slow link is not read in full. One transaction: on
    any error nothing is written. Returns a summary dict."""
    summary = {}
    first_conn, first_meta = parts[0]
    with transaction.atomic():
        codes = {a.code: a for a in AtcCode.objects.all()}
        created = updated = 0
        for row in _checked(first_conn, first_meta, "atc_code", "SELECT * FROM atc_code"):
            fields = {"name": row["name"], "name_fa": row["name_fa"]}
            code = codes.get(row["code"])
            if code is None:
                codes[row["code"]] = AtcCode.objects.create(code=row["code"], **fields)
                created += 1
            elif (code.name, code.name_fa) != (fields["name"], fields["name_fa"]):
                AtcCode.objects.filter(pk=code.pk).update(**fields)
                updated += 1
        summary["atc_code"] = (created, updated)

        by_rxcui = {i.rxcui: i for i in Ingredient.objects.all()}
        slugs = {i.slug: i.rxcui for i in by_rxcui.values()}
        in_file = set()
        created = updated = skipped = 0
        for row in _checked(first_conn, first_meta, "ingredient", "SELECT * FROM ingredient"):
            fields = {
                "slug": row["slug"],
                "name": row["name"],
                "name_fa": row["name_fa"],
                "n_products": row["n_products"],
                "n_source_records": row["n_source_records"],
                "pharm_classes": loads(row["pharm_classes"], []),
                "source_fetched_at": parse_datetime(row["source_fetched_at"]) if row["source_fetched_at"] else None,
            }
            holder = slugs.get(row["slug"])
            if holder is not None and holder != row["rxcui"]:
                log(f"  skipped {row['rxcui']}: slug '{row['slug']}' already belongs to {holder}")
                skipped += 1
                continue
            in_file.add(row["rxcui"])
            ingredient = by_rxcui.get(row["rxcui"])
            if ingredient is None:
                by_rxcui[row["rxcui"]] = Ingredient.objects.create(rxcui=row["rxcui"], **fields)
                slugs[row["slug"]] = row["rxcui"]
                created += 1
            elif any(getattr(ingredient, f) != v for f, v in fields.items()):
                Ingredient.objects.filter(pk=ingredient.pk).update(**fields, updated_at=timezone.now())
                updated += 1
        summary["ingredient"] = {"added": created, "updated": updated, "skipped": skipped}

        # Each of the file's ingredients gets exactly the file's ATC codes.
        Link = Ingredient.atc_codes.through
        wanted = set()
        for row in _checked(first_conn, first_meta, "ingredient_atc", "SELECT * FROM ingredient_atc"):
            if row["rxcui"] in in_file:
                wanted.add((by_rxcui[row["rxcui"]].pk, codes[row["code"]].pk))
        ids = [by_rxcui[r].pk for r in in_file]
        have = {
            (link.ingredient_id, link.atccode_id): link.pk
            for link in Link.objects.filter(ingredient_id__in=ids).only("pk", "ingredient_id", "atccode_id")
        }
        Link.objects.filter(pk__in=[pk for pair, pk in have.items() if pair not in wanted]).delete()
        Link.objects.bulk_create([Link(ingredient_id=i, atccode_id=a) for i, a in wanted - have.keys()], batch_size=500)
        summary["ingredient_atc"] = {
            "added": len(wanted - have.keys()),
            "removed": len(have.keys() - wanted),
            "kept": len(wanted & have.keys()),
        }

        existing = {
            (s["ingredient_id"], s["field"]): s
            for s in IngredientProfileSection.objects.annotate(
                raw_md5=MD5("raw_text"), fa_md5=MD5("summary_fa"), en_md5=MD5("summary_en")
            ).values("pk", "ingredient_id", "field", "n_contributing_products", "raw_md5", "fa_md5", "en_md5")
        }
        to_create, to_update, unchanged = [], [], 0
        updated = 0
        for conn, meta in parts:
            for row in _checked(conn, meta, "section", "SELECT * FROM section"):
                ingredient = by_rxcui.get(row["rxcui"]) if row["rxcui"] in in_file else None
                if ingredient is None:
                    continue  # its ingredient was skipped above
                values = {f: row[f] for f in _SECTION_FIELDS}
                have_row = existing.get((ingredient.pk, row["field"]))
                if have_row is None:
                    to_create.append(IngredientProfileSection(ingredient=ingredient, field=row["field"], **values))
                elif (
                    have_row["n_contributing_products"] != row["n_contributing_products"]
                    or have_row["raw_md5"] != _digest(row["raw_text"])
                    or have_row["fa_md5"] != _digest(row["summary_fa"])
                    or have_row["en_md5"] != _digest(row["summary_en"])
                ):
                    to_update.append(IngredientProfileSection(pk=have_row["pk"], updated_at=timezone.now(), **values))
                else:
                    unchanged += 1
                if len(to_update) >= 200:
                    IngredientProfileSection.objects.bulk_update(to_update, [*_SECTION_FIELDS, "updated_at"])
                    updated += len(to_update)
                    to_update = []
        if to_update:
            IngredientProfileSection.objects.bulk_update(to_update, [*_SECTION_FIELDS, "updated_at"])
            updated += len(to_update)
        IngredientProfileSection.objects.bulk_create(to_create, batch_size=200)
        summary["section"] = {"added": len(to_create), "updated": updated, "unchanged": unchanged}
    return summary
