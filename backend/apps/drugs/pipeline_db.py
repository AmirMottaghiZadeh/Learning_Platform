"""Corrections written into the openfda pipeline file itself.

`import_openfda` copies the pipeline's summary columns over the app's, so a
correction made only in Postgres is undone by the next sync. One that must
hold is made in the pipeline file too, through `rewrite_summaries`: every cell
it changes is first copied, with its old text, into a backup table of that
file (`<name>_backup_<date>`, the file's own naming for its backups).
"""

import sqlite3
from datetime import date

TABLE = "ingredient_clinical_profiles"
_SUFFIXES = ("_summary_fa", "_summary_en")


def rewrite_summaries(source, transform, backup_name, dry_run=False):
    """`transform(field, lang, text, names)` over every `<field>_summary_<lang>`
    cell of the pipeline file at `source`, writing back the ones it changes;
    `names` is the ingredient's (English name, Persian name). Returns (cells
    changed, ingredients changed, backup table or None)."""
    conn = sqlite3.connect(source)
    try:
        all_columns = [row[1] for row in conn.execute(f"PRAGMA table_info({TABLE})")]
        columns = [c for c in all_columns if c.endswith(_SUFFIXES)]
        if not columns:
            raise ValueError(f"{source} has no {TABLE} with summary columns")
        # a pipeline file from before the Persian name existed has none
        name_fa = "ingredient_name_fa" if "ingredient_name_fa" in all_columns else "''"
        changes = []  # (rowid, rxcui, column, old, new)
        for column in columns:
            field, lang = column[: -len("_summary_fa")], column[-2:]
            for rowid, rxcui, name, persian_name, text in conn.execute(
                f"SELECT rowid, ingredient_rxcui, ingredient_name, {name_fa}, {column} FROM {TABLE} "
                f"WHERE {column} IS NOT NULL AND {column} != ''"
            ):
                fixed = transform(field, lang, text, (name, persian_name))
                if fixed != text:
                    changes.append((rowid, rxcui, column, text, fixed))
        ingredients = len({c[0] for c in changes})
        if dry_run or not changes:
            return len(changes), ingredients, None

        backup = f"{backup_name}_backup_{date.today():%Y_%m_%d}"
        with conn:
            conn.execute(
                f"CREATE TABLE IF NOT EXISTS {backup} "
                "(source_rowid INTEGER, ingredient_rxcui TEXT, column_name TEXT, old_value TEXT, changed_at TEXT)"
            )
            conn.executemany(
                f"INSERT INTO {backup} VALUES (?, ?, ?, ?, datetime('now'))",
                [(rowid, rxcui, column, old) for rowid, rxcui, column, old, _ in changes],
            )
            for column in columns:
                conn.executemany(
                    f"UPDATE {TABLE} SET {column} = ? WHERE rowid = ?",
                    [(new, rowid) for rowid, _, col, _, new in changes if col == column],
                )
        return len(changes), ingredients, backup
    finally:
        conn.close()
