"""The calculators dataset as a portable reference-data file (see
apps.core.reference_db): categories, tags and calculators, each keyed by the
source snapshot's own stable ids (`external_id`, `uid`) so the import can
match rows that already exist on the target.

Tables: category, tag, calculator (JSON blobs as text, exactly as stored),
calculator_category, calculator_tag.
"""

from django.db import transaction
from django.utils import timezone

from apps.core.reference_db import dumps, expected_count, loads, record_counts, rows

from .errata import fix_questions, fix_results
from .models import Calculator, CalculatorCategory, CalculatorTag

DATASET = "calculators"

_JSON_FIELDS = ("questions", "results", "error_checks", "formula_strings_fa", "references")
_TEXT_FIELDS = (
    "calculator_id", "url", "slug", "name", "name_fa", "description", "description_fa",
    "about", "about_fa", "disclaimer_footer", "disclaimer_footer_fa",
)

SCHEMA = """
CREATE TABLE category (
    external_id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_fa TEXT NOT NULL,
    parent_external_id INTEGER, is_main_category INTEGER NOT NULL
);
CREATE TABLE tag (external_id INTEGER PRIMARY KEY, name TEXT NOT NULL, name_fa TEXT NOT NULL);
CREATE TABLE calculator (
    uid TEXT PRIMARY KEY, calculator_id TEXT NOT NULL, url TEXT NOT NULL, slug TEXT NOT NULL,
    name TEXT NOT NULL, name_fa TEXT NOT NULL, description TEXT NOT NULL, description_fa TEXT NOT NULL,
    about TEXT NOT NULL, about_fa TEXT NOT NULL,
    disclaimer_footer TEXT NOT NULL, disclaimer_footer_fa TEXT NOT NULL,
    questions TEXT NOT NULL, results TEXT NOT NULL, error_checks TEXT NOT NULL,
    formula_strings_fa TEXT NOT NULL, "references" TEXT NOT NULL
);
CREATE TABLE calculator_category (uid TEXT NOT NULL, category_external_id INTEGER NOT NULL);
CREATE TABLE calculator_tag (uid TEXT NOT NULL, tag_external_id INTEGER NOT NULL);
"""


def export(conn):
    """Writes every calculator, category and tag into `conn`. Returns the
    row counts."""
    conn.executescript(SCHEMA)
    categories = CalculatorCategory.objects.select_related("parent").order_by("external_id")
    conn.executemany(
        "INSERT INTO category VALUES (?, ?, ?, ?, ?)",
        [
            (c.external_id, c.name, c.name_fa, c.parent.external_id if c.parent else None, int(c.is_main_category))
            for c in categories
        ],
    )
    conn.executemany(
        "INSERT INTO tag VALUES (?, ?, ?)",
        [(t.external_id, t.name, t.name_fa) for t in CalculatorTag.objects.order_by("external_id")],
    )

    counts = {"category": categories.count(), "tag": CalculatorTag.objects.count(), "calculator": 0}
    links_cat, links_tag = [], []
    calculators = Calculator.objects.prefetch_related("categories", "tags").order_by("uid")
    for calc in calculators.iterator(chunk_size=100):
        conn.execute(
            "INSERT INTO calculator VALUES (%s)" % ", ".join(["?"] * (1 + len(_TEXT_FIELDS) + len(_JSON_FIELDS))),
            [calc.uid, *[getattr(calc, f) or "" for f in _TEXT_FIELDS], *[dumps(getattr(calc, f)) for f in _JSON_FIELDS]],
        )
        links_cat += [(calc.uid, c.external_id) for c in calc.categories.all()]
        links_tag += [(calc.uid, t.external_id) for t in calc.tags.all()]
        counts["calculator"] += 1
    conn.executemany("INSERT INTO calculator_category VALUES (?, ?)", links_cat)
    conn.executemany("INSERT INTO calculator_tag VALUES (?, ?)", links_tag)
    counts["calculator_category"] = len(links_cat)
    counts["calculator_tag"] = len(links_tag)
    record_counts(conn, counts)
    return counts


def load(conn, meta, *, prune=False, log=print):
    """Upserts the file's categories, tags and calculators (matched on
    `external_id` / `uid`) and replaces each calculator's category and tag
    links. With `prune`, rows absent from the file are deleted. Runs in one
    transaction: on any error nothing is written. Returns a summary dict."""
    summary = {}
    with transaction.atomic():
        # categories: every row first, then parents (a parent may come later)
        existing = {c.external_id: c for c in CalculatorCategory.objects.all()}
        created = updated = 0
        parents = {}
        for row in rows(conn, "SELECT * FROM category"):
            fields = {"name": row["name"], "name_fa": row["name_fa"], "is_main_category": bool(row["is_main_category"])}
            cat = existing.get(row["external_id"])
            if cat is None:
                cat = CalculatorCategory.objects.create(external_id=row["external_id"], **fields)
                existing[cat.external_id] = cat
                created += 1
            else:
                CalculatorCategory.objects.filter(pk=cat.pk).update(**fields)
                updated += 1
            parents[row["external_id"]] = row["parent_external_id"]
        for external_id, parent_external_id in parents.items():
            parent = existing.get(parent_external_id) if parent_external_id is not None else None
            CalculatorCategory.objects.filter(external_id=external_id).update(parent=parent)
        summary["category"] = (created, updated)

        tags = {t.external_id: t for t in CalculatorTag.objects.all()}
        created = updated = 0
        for row in rows(conn, "SELECT * FROM tag"):
            fields = {"name": row["name"], "name_fa": row["name_fa"]}
            if row["external_id"] in tags:
                CalculatorTag.objects.filter(external_id=row["external_id"]).update(**fields)
                updated += 1
            else:
                tags[row["external_id"]] = CalculatorTag.objects.create(external_id=row["external_id"], **fields)
                created += 1
        summary["tag"] = (created, updated)

        cat_links, tag_links = {}, {}
        for row in rows(conn, "SELECT uid, category_external_id FROM calculator_category"):
            cat_links.setdefault(row["uid"], []).append(existing[row["category_external_id"]])
        for row in rows(conn, "SELECT uid, tag_external_id FROM calculator_tag"):
            tag_links.setdefault(row["uid"], []).append(tags[row["tag_external_id"]])

        by_uid = {c.uid: c for c in Calculator.objects.only("pk", "uid", "slug")}
        slugs = {c.slug: c.uid for c in by_uid.values()}
        created = updated = skipped = 0
        seen = set()
        for row in rows(conn, 'SELECT * FROM calculator', batch=50):
            uid = row["uid"]
            seen.add(uid)
            fields = {f: row[f] for f in _TEXT_FIELDS}
            fields.update({f: loads(row[f], {} if f == "formula_strings_fa" else []) for f in _JSON_FIELDS})
            fields["results"] = fix_results(fields["calculator_id"], fields["results"])
            fields["questions"] = fix_questions(fields["calculator_id"], fields["questions"])
            holder = slugs.get(fields["slug"])
            if holder is not None and holder != uid:
                log(f"  skipped {uid}: slug '{fields['slug']}' already belongs to {holder}")
                skipped += 1
                continue
            calc = by_uid.get(uid)
            if calc is None:
                calc = Calculator.objects.create(uid=uid, **fields)
                created += 1
            else:
                Calculator.objects.filter(pk=calc.pk).update(**fields, updated_at=timezone.now())
                updated += 1
            slugs[fields["slug"]] = uid
            calc.categories.set(cat_links.get(uid, []))
            calc.tags.set(tag_links.get(uid, []))
        summary["calculator"] = (created, updated)
        if skipped:
            summary["skipped"] = skipped

        expected = expected_count(meta, "calculator")
        if expected is not None and len(seen) != expected:
            raise RuntimeError(f"Read {len(seen)} calculators but the file says {expected}; it may be damaged.")

        if prune:
            gone_calc = Calculator.objects.exclude(uid__in=seen)
            gone_cat = CalculatorCategory.objects.exclude(external_id__in=list(parents))
            file_tags = [r["external_id"] for r in rows(conn, "SELECT external_id FROM tag")]
            gone_tag = CalculatorTag.objects.exclude(external_id__in=file_tags)
            summary["pruned"] = {
                "calculator": gone_calc.count(), "category": gone_cat.count(), "tag": gone_tag.count(),
            }
            gone_calc.delete()
            gone_cat.delete()
            gone_tag.delete()
    return summary
