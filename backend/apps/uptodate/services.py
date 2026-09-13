"""Read-only access to the UpToDate snapshot.

The snapshot (~2.8 GB across several files) is a fixed, licensed content
dump -- never imported into the main Postgres database. It has two possible
homes:

- Local SQLite files (`settings.UPTODATE_DB_DIR`) -- what local dev uses.
  Opened read-only, one connection cached per file.
- A remote MySQL mirror (`settings.UPTODATE_MYSQL_URL`) -- what a host with
  no local disk for a multi-GB dataset (Render) uses instead. Populated by
  `manage.py migrate_uptodate_to_mysql`, which is also the authority on the
  MySQL schema (see that command's SCHEMA constant).

Whichever is configured, this module exposes the same functions; only the
handful of functions below that actually touch a connection branch on which
backend is active. MySQL is preferred when `UPTODATE_MYSQL_URL` is set.

SQLite layout (`settings.UPTODATE_DB_DIR`):
  fts.db      -- FTS5 table `fts(title, displayTitle, type, contentId, content)`
  content.db  -- `content(id, gzip, version)` -- gzip is zlib-compressed JSON
                 {title, bodyHtml, outlineHtml, contributors, ...}
  toc.db      -- `toc(id, title, parentId, section, contentId)` tree
  images.db   -- `images(id, binary, type)` -- raw PNG/JPEG bytes for the
                 <img src="<id>"> graphics referenced from bodyHtml; optional,
                 figure/algorithm graphics answer 404 without it.
  info.json   -- {version: 202607, ...}
"""

import base64
import json
import re
import sqlite3
import threading
import zlib
from functools import lru_cache
from pathlib import Path

import dj_database_url
import pymysql
import pymysql.cursors
from django.conf import settings

_LOCK = threading.Lock()
_CONNS: dict[str, sqlite3.Connection] = {}
_MYSQL_CONN: pymysql.connections.Connection | None = None

# Only real topic articles (type 1); type 2/3 are outline/section fragments.
TOPIC_TYPE = 1


def _using_mysql() -> bool:
    return bool(getattr(settings, "UPTODATE_MYSQL_URL", ""))


def _dir() -> Path:
    return Path(getattr(settings, "UPTODATE_DB_DIR", ""))


def is_available() -> bool:
    if _using_mysql():
        return True
    d = _dir()
    return bool(d) and (d / "fts.db").is_file() and (d / "content.db").is_file()


def _sqlite_conn(name: str) -> sqlite3.Connection:
    with _LOCK:
        conn = _CONNS.get(name)
        if conn is None:
            path = _dir() / f"{name}.db"
            conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            _CONNS[name] = conn
        return conn


def mysql_config() -> dict:
    parsed = dj_database_url.parse(settings.UPTODATE_MYSQL_URL)
    return {
        "host": parsed["HOST"],
        "port": parsed["PORT"] or 3306,
        "user": parsed["USER"],
        "password": parsed["PASSWORD"],
        "database": parsed["NAME"],
        "charset": "utf8mb4",
        "cursorclass": pymysql.cursors.DictCursor,
        # The Runflare-hosted instance presents a self-signed cert -- still
        # encrypted in transit, just not verified against a CA.
        "ssl": {"ssl": {}},
        "ssl_verify_cert": False,
        "ssl_verify_identity": False,
        "connect_timeout": 10,
    }


def _mysql_conn() -> pymysql.connections.Connection:
    global _MYSQL_CONN
    with _LOCK:
        if _MYSQL_CONN is not None:
            try:
                _MYSQL_CONN.ping(reconnect=True)
                return _MYSQL_CONN
            except Exception:
                _MYSQL_CONN = None
        _MYSQL_CONN = pymysql.connect(**mysql_config())
        return _MYSQL_CONN


def close_all() -> None:
    global _MYSQL_CONN
    with _LOCK:
        for conn in _CONNS.values():
            conn.close()
        _CONNS.clear()
        if _MYSQL_CONN is not None:
            _MYSQL_CONN.close()
            _MYSQL_CONN = None
    snapshot_version.cache_clear()


@lru_cache(maxsize=1)
def snapshot_version() -> str:
    if _using_mysql():
        try:
            with _mysql_conn().cursor() as cur:
                cur.execute("SELECT value FROM meta WHERE `key` = 'version'")
                row = cur.fetchone()
                return str(row["value"]) if row else ""
        except Exception:
            return ""
    try:
        info = json.loads((_dir() / "info.json").read_text())
        return str(info.get("version", ""))
    except Exception:
        return ""


def _search_words(raw: str) -> list[str]:
    return re.findall(r"[A-Za-z0-9؀-ۿ]+", raw or "")[:8]


def _section_for(content_id: str) -> str:
    """Top-level TOC ancestor title for an article, e.g. 'Cardiovascular Medicine'."""
    content_id = str(content_id)
    if _using_mysql():
        conn = _mysql_conn()
        with conn.cursor() as cur:
            cur.execute("SELECT parentId FROM toc WHERE contentId = %s LIMIT 1", (content_id,))
            row = cur.fetchone()
            pid, seen = (row["parentId"] if row else None), set()
            while pid and pid not in seen:
                seen.add(pid)
                cur.execute("SELECT title, parentId FROM toc WHERE id = %s", (pid,))
                node = cur.fetchone()
                if not node:
                    break
                if not node["parentId"]:
                    return node["title"]
                pid = node["parentId"]
        return ""

    try:
        toc = _sqlite_conn("toc")
    except sqlite3.OperationalError:
        return ""
    row = toc.execute(
        "SELECT parentId FROM toc WHERE contentId = ? LIMIT 1", (content_id,)
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
    words = _search_words(query)
    if not words:
        return []
    limit = int(limit)

    if _using_mysql():
        # Boolean-mode fulltext: "+word*" requires the prefix in every match,
        # the closest MySQL equivalent to FTS5's implicit-AND prefix query.
        match = " ".join(f"+{w}*" for w in words)
        with _mysql_conn().cursor() as cur:
            cur.execute(
                "SELECT title, contentId, "
                "MATCH(title, content) AGAINST (%s IN BOOLEAN MODE) AS relevance "
                "FROM fts WHERE MATCH(title, content) AGAINST (%s IN BOOLEAN MODE) "
                "AND type = %s ORDER BY relevance DESC LIMIT %s",
                (match, match, TOPIC_TYPE, limit),
            )
            rows = cur.fetchall()
    else:
        match = " ".join(f'"{w}"*' for w in words)
        rows = _sqlite_conn("fts").execute(
            "SELECT title, contentId FROM fts "
            "WHERE fts MATCH ? AND type = ? ORDER BY rank LIMIT ?",
            (match, TOPIC_TYPE, limit),
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
    content_id = str(content_id)
    if _using_mysql():
        with _mysql_conn().cursor() as cur:
            cur.execute("SELECT gzip, version FROM content WHERE id = %s", (content_id,))
            row = cur.fetchone()
    else:
        row = _sqlite_conn("content").execute(
            "SELECT gzip, version FROM content WHERE id = ?", (content_id,)
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
        "id": content_id,
        "title": doc.get("title", ""),
        "section": _section_for(content_id),
        "contributors": contributors,
        "outline_html": doc.get("outlineHtml", ""),
        "body_html": doc.get("bodyHtml", ""),
        "version": str(row["version"] or snapshot_version()),
    }


_IMAGE_TYPES = {"png", "jpeg", "gif", "webp"}


def get_image(image_id: str) -> dict | None:
    image_id = str(image_id)
    if _using_mysql():
        with _mysql_conn().cursor() as cur:
            cur.execute("SELECT `binary`, type FROM images WHERE id = %s", (image_id,))
            row = cur.fetchone()
    else:
        try:
            conn = _sqlite_conn("images")
            row = conn.execute(
                "SELECT binary, type FROM images WHERE id = ?", (image_id,)
            ).fetchone()
        except sqlite3.OperationalError:
            return None
    if not row or not row["binary"]:
        return None
    img_type = (row["type"] or "").lower()
    content_type = f"image/{img_type}" if img_type in _IMAGE_TYPES else "image/jpeg"
    return {
        "id": image_id,
        "content_type": content_type,
        "data_base64": base64.b64encode(row["binary"]).decode("ascii"),
    }
