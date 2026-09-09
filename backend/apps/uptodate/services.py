"""Read-only access to the bundled UpToDate SQLite snapshot.

The snapshot (~2.8 GB across several .db files) is never imported into Postgres:
it is a fixed, licensed content dump and SQLite FTS5 is exactly the right tool
for searching it. This module opens the files read-only and caches one
connection per file for the process.

Layout (`settings.UPTODATE_DB_DIR`):
  fts.db      -- FTS5 table `fts(title, displayTitle, type, contentId, content)`
  content.db  -- `content(id, gzip, version)` -- gzip is zlib-compressed JSON
                 {title, bodyHtml, outlineHtml, contributors, ...}
  toc.db      -- `toc(id, title, parentId, section, contentId)` tree
  info.json   -- {version: 202607, ...}
"""

import json
import re
import sqlite3
import threading
import zlib
from functools import lru_cache
from pathlib import Path

from django.conf import settings

_LOCK = threading.Lock()
_CONNS: dict[str, sqlite3.Connection] = {}

# Only real topic articles (type 1); type 2/3 are outline/section fragments.
TOPIC_TYPE = 1


def _dir() -> Path:
    return Path(getattr(settings, "UPTODATE_DB_DIR", ""))


def is_available() -> bool:
    d = _dir()
    return bool(d) and (d / "fts.db").is_file() and (d / "content.db").is_file()


def _conn(name: str) -> sqlite3.Connection:
    with _LOCK:
        conn = _CONNS.get(name)
        if conn is None:
            path = _dir() / f"{name}.db"
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _CONNS[name] = conn
        return conn


def close_all() -> None:
    with _LOCK:
        for conn in _CONNS.values():
            conn.close()
        _CONNS.clear()
    snapshot_version.cache_clear()


@lru_cache(maxsize=1)
def snapshot_version() -> str:
    try:
        info = json.loads((_dir() / "info.json").read_text())
        return str(info.get("version", ""))
    except Exception:
        return ""


def _fts_query(raw: str) -> str:
    """Turn a user string into a safe FTS5 prefix query."""
    words = re.findall(r"[A-Za-z0-9؀-ۿ]+", raw or "")
    if not words:
        return ""
    return " ".join(f'"{w}"*' for w in words[:8])


def _section_for(content_id: str) -> str:
    """Top-level TOC ancestor title for an article, e.g. 'Cardiovascular Medicine'."""
    try:
        toc = _conn("toc")
    except sqlite3.OperationalError:
        return ""
    row = toc.execute(
        "SELECT parentId FROM toc WHERE contentId = ? LIMIT 1", (str(content_id),)
    ).fetchone()
    if not row:
        return ""
    pid, seen = row["parentId"], set()
    while pid and pid not in seen:
        seen.add(pid)
        node = toc.execute(
            "SELECT title, parentId FROM toc WHERE id = ?", (pid,)
        ).fetchone()
        if not node:
            break
        if not node["parentId"]:
            return node["title"]
        pid = node["parentId"]
    return ""


def search_topics(query: str, limit: int = 25) -> list[dict]:
    match = _fts_query(query)
    if not match:
        return []
    rows = _conn("fts").execute(
        "SELECT title, contentId FROM fts "
        "WHERE fts MATCH ? AND type = ? ORDER BY rank LIMIT ?",
        (match, TOPIC_TYPE, int(limit)),
    ).fetchall()
    version = snapshot_version()
    return [
        {
            "id": row["contentId"],
            "title": row["title"],
            "section": _section_for(row["contentId"]),
            "version": version,
        }
        for row in rows
    ]


def get_topic(content_id: str) -> dict | None:
    row = _conn("content").execute(
        "SELECT gzip, version FROM content WHERE id = ?", (str(content_id),)
    ).fetchone()
    if not row:
        return None
    try:
        doc = json.loads(zlib.decompress(row["gzip"]))
    except Exception:
        return None
    contributors = []
    for group in doc.get("contributors", []) or []:
        for person in group.get("contributors", []) or []:
            if person.get("name"):
                contributors.append(person["name"])
    return {
        "id": str(content_id),
        "title": doc.get("title", ""),
        "section": _section_for(content_id),
        "contributors": contributors,
        "outline_html": doc.get("outlineHtml", ""),
        "body_html": doc.get("bodyHtml", ""),
        "version": str(row["version"] or snapshot_version()),
    }
