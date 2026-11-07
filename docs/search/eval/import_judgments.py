#!/usr/bin/env python3
"""Copy graded rows from a judging workbook into dev-judgments.csv (IDs only).

Titles stay in the private workbook; the repository keeps query, article,
section and paragraph identifiers with the grade and who gave it ("owner" or
"assistant"). Rows already present for the same query, level, article, section
and paragraph are replaced by the newer grade. Workbooks saved by other
spreadsheet programs are first normalised with LibreOffice.

    python3 docs/search/eval/import_judgments.py \
        --source /home/amir/Documents/UpToDate --judge owner \
        --workbook /home/amir/Documents/pharmenta-search-eval/judging-dev-2026-10-31.xlsx
"""

import argparse
import csv
from pathlib import Path
import subprocess
import sys
import tempfile

from openpyxl import load_workbook

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from apps.uptodate.search_hierarchy_source import SQLiteHierarchySource  # noqa: E402

FIELDS = ["query_id", "level", "article_id", "section_id", "paragraph_id", "grade", "judge", "note", "workbook"]
LEVELS = ("article", "section", "paragraph")


def open_workbook(path):
    try:
        return load_workbook(path, data_only=True)
    except (TypeError, ValueError):
        # Some spreadsheet programs write style extensions openpyxl rejects.
        target = Path(tempfile.mkdtemp())
        subprocess.run(["soffice", "--headless", "--convert-to", "xlsx", "--outdir", str(target), str(path)],
                       check=True, capture_output=True, timeout=180)
        return load_workbook(target / path.name, data_only=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--workbook", type=Path, required=True)
    parser.add_argument("--judge", choices=("owner", "assistant"), required=True)
    parser.add_argument("--output", type=Path, default=Path(__file__).with_name("dev-judgments.csv"))
    args = parser.parse_args()
    wb = open_workbook(args.workbook)

    existing = {}
    if args.output.exists():
        for row in csv.DictReader(args.output.open(encoding="utf-8")):
            row = {"paragraph_id": "", "judge": "owner", **row}
            existing[tuple(row[f] for f in FIELDS[:5])] = row

    def keep(key, grade, note):
        old = existing.get(key)
        if old and int(old["grade"]) == int(grade) and old["note"] == (note or ""):
            return  # unchanged rows keep their original judge
        existing[key] =dict(zip(FIELDS, (*key, int(grade), args.judge, note or "", args.workbook.name)))

    skipped = []
    with SQLiteHierarchySource(args.source) as source:
        by_title = {}
        for article in source.catalog.articles:
            by_title.setdefault(article.title, []).append(article.article_id)

        def article_id(title):
            ids = by_title.get(title, [])
            if len(ids) != 1:
                raise SystemExit(f"Title does not identify one article: {title!r}")
            return ids[0]

        for query_id, _, _, _, candidate, _, _, grade, note in wb["مقاله"].iter_rows(min_row=2, values_only=True):
            if grade not in (None, ""):
                keep((query_id, "article", str(candidate), "", ""), grade, note)
        for query_id, _, title, section_id, path, grade, note in wb["بخش"].iter_rows(min_row=2, values_only=True):
            if grade in (None, ""):
                continue
            if not section_id or not path:
                # Candidates from a body-less router page carry no heading.
                skipped.append(query_id)
                continue
            keep((query_id, "section", article_id(title), str(section_id), ""), grade, note)
        if "پاراگراف" in wb.sheetnames:
            for query_id, _, title, section_id, paragraph_id, _, grade, note in wb["پاراگراف"].iter_rows(
                    min_row=2, values_only=True):
                if grade not in (None, ""):
                    keep((query_id, "paragraph", article_id(title), section_id, paragraph_id), grade, note)

    rows = sorted(existing.values(), key=lambda r: tuple(r[f] for f in FIELDS[:5]))
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    levels = {level: sum(r["level"] == level for r in rows) for level in LEVELS}
    print(f"{args.output}: {levels}; skipped rows without a heading: {sorted(set(skipped))}")


if __name__ == "__main__":
    main()
