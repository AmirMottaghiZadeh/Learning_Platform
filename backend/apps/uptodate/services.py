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
import bisect
import json
import re
import sqlite3
import threading
import zlib
from dataclasses import dataclass, field
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
    _title_index.cache_clear()
    _term.cache_clear()
    _infixed.cache_clear()
    _SECTIONS.clear()


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


# How much of a topic's plain-text `content` holds its header: the title,
# contributors and dates. The body starts right after "This topic last
# updated: <date>.", so a few KB covers the header plus the opening
# paragraphs the offline packages store (`snippet_source`).
SNIPPET_SOURCE_CHARS = 6000
_UPDATED_RE = re.compile(r"This topic last updated:\s*([A-Z][a-z]{2,8}\.? \d{1,2}, \d{4})\.?")
# An all-caps run-in heading ("INTRODUCTION — ") wherever it sits.
_RUN_IN_HEADING_RE = re.compile(r"\s*\b[A-Z][A-Z0-9 ,'()/&-]{2,80}\s+—\s+")
# Sentence glued to the next one where block tags were dropped: "below.)The".
_GLUED_RE = re.compile(r"(?<=[a-z0-9.)\]][.)\]])(?=[A-Z][a-z])")
_BOILERPLATE_RE = re.compile(
    r"\d{4}©.*?All Rights Reserved\.|Please read the Disclaimer at the end of this page\."
)
_GLYPHS_RE = re.compile(r"[●•▪◦■]")


def _updated_from_text(text: str) -> str:
    match = _UPDATED_RE.search(text or "")
    return match.group(1) if match else ""


def snippet_source(content: str, title: str = "") -> str:
    """The article body's opening as clean plain text, without the
    title/author header. The offline packages store this per topic (app
    builds before 1.3 cut a search-result excerpt from it)."""
    text = (content or "").replace("\xa0", " ")
    header = _UPDATED_RE.search(text)
    if header:
        text = text[header.end():]
    elif title and text.startswith(title):
        text = text[len(title):]
    text = _BOILERPLATE_RE.sub(" ", text)
    text = _GLYPHS_RE.sub(" ", text)
    text = _GLUED_RE.sub(" ", text)
    text = _RUN_IN_HEADING_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


# contentId -> title of its top-level TOC ancestor ("Cardiovascular Medicine"),
# filled in as topics are looked up; emptied with the connections.
_SECTIONS: dict[str, str] = {}
# ids per IN (...) query
_SECTION_BATCH = 500


def _toc_rows(sql_sqlite: str, sql_mysql: str, ids: list) -> list[dict]:
    """`sql_*` with "{marks}" filled in for `ids`, in batches."""
    rows = []
    for at in range(0, len(ids), _SECTION_BATCH):
        part = ids[at:at + _SECTION_BATCH]
        if _using_mysql():
            with _mysql_conn().cursor() as cur:
                cur.execute(sql_mysql.format(marks=",".join(["%s"] * len(part))), part)
                rows.extend(cur.fetchall())
        else:
            rows.extend(dict(r) for r in _sqlite_conn("toc").execute(
                sql_sqlite.format(marks=",".join(["?"] * len(part))), part
            ))
    return rows


def _lookup_sections(content_ids: list[str]) -> dict[str, str]:
    """Each topic's section, a level of the tree per query: a handful of
    queries for any number of topics."""
    parent: dict[str, object] = {}
    for row in _toc_rows(
        "SELECT contentId, parentId FROM toc WHERE contentId IN ({marks})",
        "SELECT contentId, parentId FROM toc WHERE contentId IN ({marks})",
        content_ids,
    ):
        # the first place a topic sits in the tree, as one lookup reads it
        parent.setdefault(str(row["contentId"]), row["parentId"])
    nodes: dict = {}
    wanted = {pid for pid in parent.values() if pid}
    while wanted:
        rows = _toc_rows(
            "SELECT id, title, parentId FROM toc WHERE id IN ({marks})",
            "SELECT id, title, parentId FROM toc WHERE id IN ({marks})",
            sorted(wanted, key=str),
        )
        for row in rows:
            nodes[row["id"]] = (row["title"], row["parentId"])
        wanted = {row["parentId"] for row in rows if row["parentId"] and row["parentId"] not in nodes}

    def top(pid):
        seen = set()
        while pid and pid not in seen:
            seen.add(pid)
            node = nodes.get(pid)
            if node is None:
                break
            if not node[1]:
                return node[0] or ""
            pid = node[1]
        return ""

    return {cid: top(parent.get(cid)) for cid in content_ids}


def _sections_for(content_ids) -> dict[str, str]:
    """Top-level TOC ancestor title per article, e.g. 'Cardiovascular Medicine'."""
    content_ids = [str(c) for c in content_ids]
    missing = [c for c in dict.fromkeys(content_ids) if c not in _SECTIONS]
    if missing:
        try:
            _SECTIONS.update(_lookup_sections(missing))
        except sqlite3.OperationalError:
            return {c: _SECTIONS.get(c, "") for c in content_ids}
    return {c: _SECTIONS.get(c, "") for c in content_ids}


def _section_for(content_id: str) -> str:
    return _sections_for([content_id])[str(content_id)]


# ---- Title search ---------------------------------------------------------
#
# The search reads topic titles only -- never the article text. Every title
# is held in memory (one read per snapshot), so SQLite and MySQL answer
# alike, and the offline package's search (frontend
# src/offline/uptodateLocal.ts) mirrors this section line for line.

_TITLE_WORD_RE = re.compile(r"[a-z0-9]+")
_TAG_RE = re.compile(r"<[^>]*>")


def _title_words(title: str) -> list[str]:
    # some titles italicise a name: "<i>Chlamydia pneumoniae</i>"
    return _TITLE_WORD_RE.findall(_TAG_RE.sub(" ", title or "").lower())


@dataclass
class TitleIndex:
    rowids: list[int]
    ids: list[str]
    titles: list[str]
    words: list[list[str]]
    # every distinct title word, sorted, and the titles that have it
    vocab: list[str]
    postings: dict[str, list[int]]
    # each vocab word's letters (`_letters`)
    letters: list[int] = field(default_factory=list)
    # each topic's last-updated date, read from its header on first need
    updated: dict[int, str] = field(default_factory=dict)


def build_title_index(rows) -> TitleIndex:
    """`rows`: (rowid, contentId, title) of every topic article."""
    rowids, ids, titles, words = [], [], [], []
    postings: dict[str, list[int]] = {}
    seen = set()
    for rowid, content_id, title in rows:
        # one entry per topic, as in the offline package
        if str(content_id) in seen:
            continue
        seen.add(str(content_id))
        i = len(ids)
        rowids.append(rowid)
        ids.append(str(content_id))
        titles.append(title or "")
        title_words = _title_words(title)
        words.append(title_words)
        for word in dict.fromkeys(title_words):
            postings.setdefault(word, []).append(i)
    vocab = sorted(postings)
    return TitleIndex(rowids, ids, titles, words, vocab, postings, [_letters(w) for w in vocab])


def _letters(word: str) -> int:
    """The set of characters in `word`, as bits."""
    bits = 0
    for ch in word:
        bits |= 1 << (ord(ch) & 63)
    return bits


@lru_cache(maxsize=1)
def _title_index(version: str) -> TitleIndex:
    if _using_mysql():
        with _mysql_conn().cursor() as cur:
            cur.execute(
                "SELECT rowid, contentId, title FROM fts WHERE type = %s ORDER BY rowid",
                (TOPIC_TYPE,),
            )
            rows = [(r["rowid"], r["contentId"], r["title"]) for r in cur.fetchall()]
    else:
        rows = _sqlite_conn("fts").execute(
            "SELECT rowid, contentId, title FROM fts WHERE type = ? ORDER BY rowid",
            (TOPIC_TYPE,),
        ).fetchall()
    return build_title_index(rows)


def _prefixed(vocab: list[str], prefix: str) -> list[str]:
    """The title words that start with `prefix`."""
    start = bisect.bisect_left(vocab, prefix)
    end = start
    while end < len(vocab) and vocab[end].startswith(prefix):
        end += 1
    return vocab[start:end]


def _max_typos(length: int, prefix: bool) -> int:
    # a word still being typed gets fewer: its starts are many
    return 1 if length <= 4 else 2 if length <= 8 or prefix else 3


def _typo_distance(word: str, candidate: str, limit: int, prefix: bool) -> tuple[int, int] | None:
    """Edits (insert, delete, substitute, swap two neighbours) from `word` to
    `candidate` -- or, with `prefix`, to the closest start of it -- as
    (distance, length of that start); None past `limit`."""
    m = len(word)
    n = min(len(candidate), m + limit) if prefix else len(candidate)
    if n < m - limit or n > m + limit:
        return None
    over = limit + 1
    # only cells within `limit` of the diagonal can stay within `limit`
    before: list[int] | None = None
    row = [j if j <= limit else over for j in range(n + 1)]
    for i in range(1, m + 1):
        current = [over] * (n + 1)
        if i <= limit:
            current[0] = i
        low, high = max(1, i - limit), min(n, i + limit)
        letter = word[i - 1]
        for j in range(low, high + 1):
            other = candidate[j - 1]
            value = row[j - 1] + (letter != other)
            if row[j] + 1 < value:
                value = row[j] + 1
            if current[j - 1] + 1 < value:
                value = current[j - 1] + 1
            if (before is not None and j > 1 and letter == candidate[j - 2]
                    and word[i - 2] == other and before[j - 2] + 1 < value):
                value = before[j - 2] + 1
            current[j] = value if value < over else over
        if min(current[low - 1:high + 1]) > limit:
            return None
        before, row = row, current
    if not prefix:
        return (row[n], n) if row[n] <= limit else None
    # the closest start, at least as long as the word less its typos; a tie
    # goes to the longer start (the whole word, when it fits)
    best = None
    for j in range(max(1, m - limit), n + 1):
        if row[j] <= limit and (best is None or row[j] <= best[0]):
            best = (row[j], j)
    return best


def _nearest(word: str, index: TitleIndex) -> str | None:
    """The title word -- or a word's start, for a word still being typed --
    closest to a misspelt `word`."""
    # a short word is only compared to whole words: its starts are too many
    prefix = len(word) >= 5
    whole_limit, prefix_limit = _max_typos(len(word), False), _max_typos(len(word), prefix)
    mine = _letters(word)
    best_key, best = None, None
    for candidate, theirs in zip(index.vocab, index.letters):
        # each of the word's letters the candidate lacks costs an edit, and
        # so does each of the candidate's the word lacks: a quick lower bound
        lacking = (mine & ~theirs).bit_count()
        if lacking > whole_limit:
            continue
        found = None
        if max(lacking, (theirs & ~mine).bit_count()) <= whole_limit:
            found = _typo_distance(word, candidate, whole_limit, False)
        if prefix and lacking <= prefix_limit:
            start = _typo_distance(word, candidate, prefix_limit, True)
            if start and (found is None or start[0] < found[0]):
                found = start
        if found is None:
            continue
        distance, length = found
        whole = length == len(candidate)
        # fewest typos, then a whole word, then the word most titles share
        key = (distance, not whole, -len(index.postings[candidate]), candidate)
        if best_key is None or key < best_key:
            best_key, best = key, candidate[:length]
    return best


# A word this long is also found inside title words: "kalemia" finds
# "hyperkalemia", "tension" "hypertension". Shorter ones would find too much.
MIN_INFIX = 4


@lru_cache(maxsize=4096)
def _infixed(term: str, version: str) -> tuple[str, ...]:
    """The title words that have `term` inside them, not at their start."""
    if len(term) < MIN_INFIX:
        return ()
    return tuple(w for w in _title_index(version).vocab if term in w and not w.startswith(term))


@lru_cache(maxsize=4096)
def _term(word: str, version: str) -> tuple[str, str, bool]:
    """How one query word is matched: the start (or, from MIN_INFIX letters,
    a part) of title words it must be, the whole word it stands for, and
    whether that is a spelling correction."""
    whole = word.lower()
    index = _title_index(version)
    if len(whole) < 3 or _prefixed(index.vocab, whole) or _infixed(whole, version):
        # a plural also finds the singular ("infections" -> "infection")
        singular = whole[:-1]
        if len(whole) >= 6 and whole.endswith("s") and _is_word(index.vocab, singular):
            return singular, whole, False
        return whole, whole, False
    nearest = _nearest(whole, index)
    return (nearest, nearest, True) if nearest else (whole, whole, False)


def _is_word(vocab: list[str], word: str) -> bool:
    i = bisect.bisect_left(vocab, word)
    return i < len(vocab) and vocab[i] == word


# Words that say little about what a topic is about: a title made of the
# query and these is the general topic ("Overview of hypertension in
# adults"), ahead of the narrower ones ("Hypertension in athletes").
_GENERAL_WORDS = frozenset(
    "a an and the of in on for to with by or at from its "
    "overview introduction adult adults child children".split()
)
# Topics that serve another reader or only list links: after the reviews.
_SECONDARY_STARTS = (["patient", "education"], ["society", "guideline"])


def _rank(index: TitleIndex, i: int, matched: list[tuple[str, str, bool]]) -> tuple:
    words = index.words[i]
    terms = [term for term, _, _ in matched]
    starts = [p for p, word in enumerate(words) if any(word.startswith(t) for t in terms)]
    # a term found only inside words ("tension" in "hypertension")
    inside = sum(1 for t in terms if not any(word.startswith(t) for word in words))
    whole = sum(1 for term, word, _ in matched if term in words or word in words)
    secondary = words[:2] in _SECONDARY_STARTS
    overview = "overview" in words
    extra = sum(1 for word in words if word not in _GENERAL_WORDS and not any(t in word for t in terms))
    exact = words == [word for _, word, _ in matched]
    # the title that is the query; then every word at a word's start, whole
    # words over starts; reviews before patient pages and link lists; an
    # overview first; the general topic (fewest other words) before the
    # narrow; the word early in the title; shorter titles
    return (not exact, inside, -whole, secondary, not overview, extra, min(starts, default=len(words)),
            len(words), index.titles[i].lower(), i)


def _updated_dates(index: TitleIndex, positions: list[int]) -> None:
    """Fill in the topics' last-updated dates, from their header text."""
    missing = [index.rowids[i] for i in positions if index.rowids[i] not in index.updated]
    if not missing:
        return
    marks = ",".join(["%s" if _using_mysql() else "?"] * len(missing))
    if _using_mysql():
        with _mysql_conn().cursor() as cur:
            cur.execute(
                f"SELECT rowid, LEFT(content, %s) AS head FROM fts WHERE rowid IN ({marks})",
                (SNIPPET_SOURCE_CHARS, *missing),
            )
            rows = cur.fetchall()
    else:
        rows = _sqlite_conn("fts").execute(
            f"SELECT rowid, substr(content, 1, ?) AS head FROM fts WHERE rowid IN ({marks})",
            (SNIPPET_SOURCE_CHARS, *missing),
        ).fetchall()
    for row in rows:
        index.updated[row["rowid"]] = _updated_from_text((row["head"] or "").replace("\xa0", " "))


def search_page(query: str, limit: int = 25, offset: int = 0, section: str = "") -> dict:
    """Every topic article whose title has every query word -- at the start
    of a title word, or inside one (from MIN_INFIX letters), a misspelt word
    corrected to the closest title word -- best first, one page of them.
    Only titles are searched. `section` keeps only that section's topics
    (`total` counts those); `all` and `sections` count every match, and per
    section, whatever `section` is."""
    empty = {"total": 0, "all": 0, "sections": [], "terms": [], "corrected": "", "results": []}
    words = _search_words(query)
    if not words:
        return empty
    limit, offset = max(0, int(limit)), max(0, int(offset))
    version = snapshot_version()
    index = _title_index(version)

    matched = [_term(word, version) for word in words]
    terms = list(dict.fromkeys(term for term, _, _ in matched))
    corrected = " ".join(word for _, word, _ in matched) if any(fix for _, _, fix in matched) else ""

    found: set[int] | None = None
    for term in terms:
        having = set()
        for word in _prefixed(index.vocab, term):
            having.update(index.postings[word])
        for word in _infixed(term, version):
            having.update(index.postings[word])
        found = having if found is None else found & having
        if not found:
            return {**empty, "terms": terms, "corrected": corrected}
    ranked = sorted(found, key=lambda i: _rank(index, i, matched))

    sections = _sections_for(index.ids[i] for i in ranked)
    counts: dict[str, int] = {}
    for i in ranked:
        name = sections[index.ids[i]]
        if name:
            counts[name] = counts.get(name, 0) + 1
    every = len(ranked)
    if section:
        ranked = [i for i in ranked if sections[index.ids[i]] == section]
    page = ranked[offset:offset + limit]

    _updated_dates(index, page)
    return {
        "total": len(ranked),
        "all": every,
        "sections": [{"name": name, "count": count} for name, count in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))],
        "terms": terms,
        "corrected": corrected,
        "results": [
            {
                "id": index.ids[i],
                "title": index.titles[i],
                "section": sections[index.ids[i]],
                "version": version,
                "snippet": "",
                "updated": index.updated.get(index.rowids[i], ""),
                "terms": terms,
                "corrected": corrected,
            }
            for i in page
        ],
    }


def search_topics(query: str, limit: int = 25) -> list[dict]:
    """The first `limit` results of `search_page`: what app builds up to
    0.1.x read."""
    return search_page(query, limit=limit)["results"]


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
    return article_from_row(content_id, row["gzip"], row["version"], _section_for(content_id))


def article_from_row(content_id: str, blob: bytes, version, section: str) -> dict | None:
    """One `content` row as the API's article shape; the offline packages
    build their article records with this too."""
    try:
        doc = json.loads(zlib.decompress(blob))
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
        "section": section,
        "contributors": contributors,
        "outline_html": doc.get("outlineHtml", ""),
        "body_html": doc.get("bodyHtml", ""),
        "version": str(version or snapshot_version()),
        "updated": _updated_from_html(doc.get("bodyHtml", "")),
    }


def _updated_from_html(body_html: str) -> str:
    # The date sits in the header, well inside the first few KB.
    head = re.sub(r"<[^>]+>", " ", (body_html or "")[:8000])
    head = re.sub(r"(&nbsp;|\xa0|\s)+", " ", head)
    return _updated_from_text(head)


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
