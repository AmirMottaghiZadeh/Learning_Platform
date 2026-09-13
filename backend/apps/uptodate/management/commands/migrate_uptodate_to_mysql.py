"""One-time bulk copy of the local UpToDate SQLite snapshot into the
UPTODATE_MYSQL_URL mirror -- run this once after standing up that database,
and again any time the local snapshot is refreshed to a newer version.

Resumable and safe to re-run or interrupt: each table's progress is
checkpointed by source `rowid` in a local JSON file (--checkpoint-file), and
a batch only advances that checkpoint after MySQL confirms the commit -- so
a dropped connection mid-batch just retries that same batch, never leaves a
half-written one, and never has to re-scan rows already copied. Tables keyed
by the source's own natural id (content, toc, images, thumbs, abstracts,
search_topic, search_query_topic) additionally use INSERT IGNORE as a second
safety net against duplicates from a stale checkpoint.

Usage:
  python manage.py migrate_uptodate_to_mysql
  python manage.py migrate_uptodate_to_mysql --tables content,toc
  python manage.py migrate_uptodate_to_mysql --reset --tables fts
"""

import json
import sqlite3
import time
from pathlib import Path

import pymysql
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.uptodate.services import mysql_config

DEFAULT_CHECKPOINT_FILE = Path.home() / ".uptodate_mysql_migration_checkpoint.json"

# Schema for the mirror database. Created with IF NOT EXISTS every run, so
# this file is the one place the MySQL schema is defined -- nothing to set
# up by hand on a fresh database first. `meta` holds the snapshot version
# (there's no info.json equivalent to query once the data lives in MySQL).
SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (
    `key` VARCHAR(32) PRIMARY KEY,
    value VARCHAR(64)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS fts (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    title TEXT,
    displayTitle TEXT,
    type TINYINT,
    contentId VARCHAR(32),
    content LONGTEXT,
    KEY ix_fts_type (type),
    KEY ix_fts_contentId (contentId),
    FULLTEXT KEY ft_fts_search (title, content)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS content (
    id VARCHAR(32) PRIMARY KEY,
    gzip LONGBLOB,
    version VARCHAR(16)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS toc (
    id INT PRIMARY KEY,
    title TEXT,
    parentId INT,
    section TEXT,
    contentId VARCHAR(32),
    KEY ix_toc_parentId (parentId),
    KEY ix_toc_contentId (contentId)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS images (
    id VARCHAR(32) PRIMARY KEY,
    `binary` LONGBLOB,
    type VARCHAR(10)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS thumbs (
    id VARCHAR(32) PRIMARY KEY,
    `binary` LONGBLOB,
    type VARCHAR(10),
    text TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS abstracts (
    id VARCHAR(32) PRIMARY KEY,
    gzip LONGBLOB
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS search_topic (
    id INT PRIMARY KEY,
    title TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS search_query (
    rowid INT PRIMARY KEY AUTO_INCREMENT,
    id INT,
    word VARCHAR(255),
    weight INT,
    KEY ix_search_query_id (id),
    KEY ix_search_query_word (word)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS search_query_topic (
    id INT PRIMARY KEY,
    x_topic_hits TEXT,
    a_topic_hits TEXT,
    p_topic_hits TEXT,
    i_topic_hits TEXT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
"""

# name -> (source .db file stem, source table, columns in source-order,
# MySQL insert statement, batch size). Column order must match the insert's
# placeholder order. `rowid` is SQLite's implicit per-row id, present on
# every table here (including the FTS5 virtual table) -- the chunking cursor.
TABLES = {
    "content": (
        "content", "content", ["id", "gzip", "version"],
        "INSERT IGNORE INTO content (id, gzip, version) VALUES (%s,%s,%s)", 500,
    ),
    "toc": (
        "toc", "toc", ["id", "title", "parentId", "section", "contentId"],
        "INSERT IGNORE INTO toc (id, title, parentId, section, contentId) VALUES (%s,%s,%s,%s,%s)", 1000,
    ),
    "fts": (
        "fts", "fts", ["title", "displayTitle", "type", "contentId", "content"],
        "INSERT INTO fts (title, displayTitle, type, contentId, content) VALUES (%s,%s,%s,%s,%s)", 500,
    ),
    "images": (
        "images", "images", ["id", "binary", "type"],
        "INSERT IGNORE INTO images (id, `binary`, type) VALUES (%s,%s,%s)", 300,
    ),
    "thumbs": (
        "thumbs", "thumbs", ["id", "binary", "type", "text"],
        "INSERT IGNORE INTO thumbs (id, `binary`, type, text) VALUES (%s,%s,%s,%s)", 2000,
    ),
    "abstracts": (
        "abstracts", "abstracts", ["id", "gzip"],
        "INSERT IGNORE INTO abstracts (id, gzip) VALUES (%s,%s)", 300,
    ),
    "search_topic": (
        "search", "topic", ["id", "title"],
        "INSERT IGNORE INTO search_topic (id, title) VALUES (%s,%s)", 1000,
    ),
    "search_query": (
        "search", "query", ["id", "word", "weight"],
        "INSERT INTO search_query (id, word, weight) VALUES (%s,%s,%s)", 1000,
    ),
    "search_query_topic": (
        "search", "query_topic",
        ["id", "x_topic_hits", "a_topic_hits", "p_topic_hits", "i_topic_hits"],
        "INSERT IGNORE INTO search_query_topic (id, x_topic_hits, a_topic_hits, p_topic_hits, i_topic_hits) "
        "VALUES (%s,%s,%s,%s,%s)", 500,
    ),
}


class Command(BaseCommand):
    help = "Copy the local UpToDate SQLite snapshot into the UPTODATE_MYSQL_URL mirror."

    def add_arguments(self, parser):
        parser.add_argument(
            "--tables", default=",".join(TABLES),
            help=f"Comma-separated subset of: {', '.join(TABLES)}",
        )
        parser.add_argument(
            "--checkpoint-file", default=str(DEFAULT_CHECKPOINT_FILE),
            help="Where per-table progress (last source rowid copied) is tracked.",
        )
        parser.add_argument(
            "--reset", action="store_true",
            help="Ignore and clear any existing checkpoint for the selected tables "
            "(does not delete rows already in MySQL -- INSERT IGNORE handles overlap "
            "for naturally-keyed tables; fts/search_query are not naturally keyed, "
            "so only reset those if you have also truncated them).",
        )

    def handle(self, *args, **options):
        if not settings.UPTODATE_MYSQL_URL:
            raise CommandError("UPTODATE_MYSQL_URL is not set.")
        source_dir = Path(settings.UPTODATE_DB_DIR)
        if not source_dir.is_dir():
            raise CommandError(f"UPTODATE_DB_DIR does not exist: {source_dir}")

        names = [n.strip() for n in options["tables"].split(",") if n.strip()]
        unknown = [n for n in names if n not in TABLES]
        if unknown:
            raise CommandError(f"Unknown table(s): {', '.join(unknown)}")

        checkpoint_path = Path(options["checkpoint_file"])
        if options["reset"]:
            self._update_checkpoint(checkpoint_path, {name: None for name in names})

        mysql_conn = pymysql.connect(**mysql_config(), autocommit=False)
        try:
            self._ensure_schema(mysql_conn)
            for name in names:
                self._migrate_table(source_dir, mysql_conn, name, checkpoint_path)
            if "content" in names or "toc" in names:
                self._write_meta_version(source_dir, mysql_conn)
        finally:
            mysql_conn.close()

        self.stdout.write(self.style.SUCCESS("Done."))

    def _ensure_schema(self, mysql_conn):
        with mysql_conn.cursor() as cur:
            for statement in [s.strip() for s in SCHEMA.split(";") if s.strip()]:
                cur.execute(statement)
        mysql_conn.commit()

    # -- checkpointing --------------------------------------------------
    #
    # Read-merge-write on every save, keyed by table name: two of this
    # command's invocations can (and, in practice, do) run concurrently
    # against disjoint table lists sharing one checkpoint file. An in-memory
    # dict loaded once per process and blindly re-serialized on every save
    # (the original approach) forgets whatever the *other* process wrote to
    # its own keys in the meantime, and each save silently reverts them.

    def _load_checkpoint(self, path: Path) -> dict:
        if path.is_file():
            return json.loads(path.read_text())
        return {}

    def _update_checkpoint(self, path: Path, updates: dict) -> None:
        current = self._load_checkpoint(path)
        for name, rowid in updates.items():
            if rowid is None:
                current.pop(name, None)
            else:
                current[name] = rowid
        path.write_text(json.dumps(current))

    # -- per-table copy ---------------------------------------------------

    def _migrate_table(self, source_dir, mysql_conn, name, checkpoint_path):
        db_stem, table, columns, insert_sql, batch_size = TABLES[name]
        source_path = source_dir / f"{db_stem}.db"
        if not source_path.is_file():
            self.stdout.write(self.style.WARNING(f"[{name}] {source_path} not found, skipping."))
            return

        sqlite_conn = sqlite3.connect(f"file:{source_path}?mode=ro", uri=True)
        sqlite_conn.row_factory = sqlite3.Row
        total = sqlite_conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0]
        after = self._load_checkpoint(checkpoint_path).get(name, 0)
        column_list = ", ".join(columns)
        copied_before = sqlite_conn.execute(
            f"SELECT count(*) FROM {table} WHERE rowid <= ?", (after,)
        ).fetchone()[0]

        self.stdout.write(f"[{name}] {copied_before}/{total} already copied, resuming from rowid {after}.")
        start = time.monotonic()
        while True:
            rows = sqlite_conn.execute(
                f"SELECT rowid, {column_list} FROM {table} WHERE rowid > ? ORDER BY rowid LIMIT ?",
                (after, batch_size),
            ).fetchall()
            if not rows:
                break
            values = [tuple(r[c] for c in columns) for r in rows]
            self._insert_with_retry(mysql_conn, insert_sql, values)
            # Positional, not row["rowid"]: for a table whose declared PK is
            # already an INTEGER PRIMARY KEY (a rowid alias), sqlite3.Row
            # reports that alias's *storage* column name for both it and the
            # explicit `rowid` selected alongside it, so a name lookup can
            # silently resolve to the wrong one of the two identical values.
            after = rows[-1][0]
            self._update_checkpoint(checkpoint_path, {name: after})
            copied_before += len(rows)
            elapsed = time.monotonic() - start
            self.stdout.write(
                f"[{name}] {copied_before}/{total} ({100 * copied_before // max(total, 1)}%) "
                f"-- {elapsed:.0f}s elapsed"
            )
        sqlite_conn.close()
        self.stdout.write(self.style.SUCCESS(f"[{name}] complete: {copied_before}/{total}."))

    def _insert_with_retry(self, mysql_conn, insert_sql, values, max_attempts=5):
        for attempt in range(1, max_attempts + 1):
            try:
                with mysql_conn.cursor() as cur:
                    cur.executemany(insert_sql, values)
                mysql_conn.commit()
                return
            except (pymysql.err.OperationalError, pymysql.err.InterfaceError) as exc:
                if attempt == max_attempts:
                    raise
                self.stdout.write(self.style.WARNING(
                    f"MySQL error ({exc}), reconnecting -- attempt {attempt}/{max_attempts}."
                ))
                time.sleep(min(2 ** attempt, 30))
                try:
                    mysql_conn.close()
                except Exception:
                    pass
                mysql_conn.connect()

    def _write_meta_version(self, source_dir, mysql_conn):
        info_path = source_dir / "info.json"
        if not info_path.is_file():
            return
        version = str(json.loads(info_path.read_text()).get("version", ""))
        if not version:
            return
        with mysql_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO meta (`key`, value) VALUES ('version', %s) "
                "ON DUPLICATE KEY UPDATE value = VALUES(value)",
                (version,),
            )
        mysql_conn.commit()
        self.stdout.write(self.style.SUCCESS(f"meta.version = {version}"))
