"""Portable reference-data files: one self-contained SQLite file per dataset
(calculators, guidelines, diseases), exported from a database that already
holds the data (`manage.py export_reference_db`) and loaded into another --
typically the production server -- with that dataset's own import command
(`import_calculators_db`, `import_guidelines_db`, `import_diseases_db`).

Every file carries a `meta` table naming its dataset, format version and row
counts, so an import refuses a file meant for another dataset or written in
a format it doesn't know, and can check that it read every row.
"""

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path

from django.core.management.base import CommandError
from django.utils import timezone

FORMAT = "pharmenta-reference"
# Bump when a file's tables change shape; imports refuse other versions.
SCHEMA_VERSION = 1

DATASETS = ("calculators", "guidelines", "diseases")


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def loads(text, default):
    if text is None or text == "":
        return default
    return json.loads(text)


@contextmanager
def writing(path: Path, dataset: str):
    """Opens a fresh SQLite file to write `dataset` into. The data goes into
    a temporary file renamed over `path` only once complete, so a failed or
    interrupted export never leaves a file that looks finished."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".partial")
    tmp.unlink(missing_ok=True)
    conn = sqlite3.connect(tmp)
    conn.execute("PRAGMA journal_mode = OFF")
    conn.execute("PRAGMA synchronous = OFF")
    conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    conn.executemany(
        "INSERT INTO meta VALUES (?, ?)",
        [
            ("format", FORMAT),
            ("schema_version", str(SCHEMA_VERSION)),
            ("dataset", dataset),
            ("exported_at", timezone.now().isoformat()),
        ],
    )
    try:
        yield conn
        conn.commit()
        conn.execute("PRAGMA user_version = %d" % SCHEMA_VERSION)
        conn.close()
        tmp.replace(path)
    except BaseException:
        conn.close()
        tmp.unlink(missing_ok=True)
        raise


def record_counts(conn, counts: dict):
    conn.executemany(
        "INSERT INTO meta VALUES (?, ?)",
        [(f"count.{table}", str(n)) for table, n in counts.items()],
    )


def open_for_import(path, dataset: str):
    """Opens an exported file read-only after checking it really is a
    `dataset` file of the format version this code reads. Returns the
    connection and the file's meta as a dict."""
    path = Path(path)
    if not path.is_file():
        raise CommandError(f"File not found: {path}")
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        meta = dict(conn.execute("SELECT key, value FROM meta").fetchall())
    except sqlite3.DatabaseError as exc:
        raise CommandError(f"{path} is not a reference-data file ({exc}).") from exc
    if meta.get("format") != FORMAT:
        raise CommandError(f"{path} is not a reference-data file.")
    if meta.get("dataset") != dataset:
        raise CommandError(f"{path} holds '{meta.get('dataset')}', not '{dataset}'.")
    if meta.get("schema_version") != str(SCHEMA_VERSION):
        raise CommandError(
            f"{path} is format version {meta.get('schema_version')}; this code reads version {SCHEMA_VERSION}."
        )
    return conn, meta


def expected_count(meta: dict, table: str):
    value = meta.get(f"count.{table}")
    return int(value) if value is not None else None


def rows(conn, sql, params=(), batch=200):
    """Rows of a query as dicts, fetched a batch at a time."""
    cur = conn.execute(sql, params)
    cols = [d[0] for d in cur.description]
    while True:
        chunk = cur.fetchmany(batch)
        if not chunk:
            return
        for row in chunk:
            yield dict(zip(cols, row))
