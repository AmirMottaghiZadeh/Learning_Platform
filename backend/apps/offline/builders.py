"""Turn the local UpToDate and Lexicomp SQLite snapshots into encrypted
offline packages (see `pack`). Run on the machine that holds the snapshots,
through `manage.py build_offline_package`.

The records hold exactly what the API would answer, so the app shows the
same thing offline as online:

UpToDate
  article record (JSON)  -- `uptodate.services.article_from_row`, for every
                            content row (topics and the graphics they link)
  head record (text)     -- `uptodate.services.snippet_source` of a topic's
                            opening, which search results cut a snippet from
  image record (bytes)   -- the raw PNG/JPEG
  index (JSON)           -- topic titles/sections/dates for title search, and
                            the locator of every record above

Lexicomp
  monograph record (JSON) -- the four texts of one interaction rule
  index (JSON)            -- generics, brands, classes, the rules' keys and
                             exceptions: everything `check_interactions`
                             needs to match, kept in memory by the app
"""

import json
import sqlite3
from pathlib import Path

from apps.uptodate import services as uptodate_services

from .pack import PackWriter, pack_json, pack_text

SNIPPET_SOURCE_CHARS = uptodate_services.SNIPPET_SOURCE_CHARS


def _ro(path: Path) -> sqlite3.Connection:
    if not path.is_file():
        raise FileNotFoundError(path)
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _info_version(directory: Path) -> str:
    try:
        return str(json.loads((directory / "info.json").read_text()).get("version", ""))
    except Exception:
        return ""


def _varints(blob: bytes) -> list[int]:
    """SQLite varints, as FTS5 packs a row's per-column token counts."""
    out, i = [], 0
    while i < len(blob):
        value = 0
        for n in range(9):
            byte = blob[i]
            i += 1
            if n == 8:
                value = (value << 8) | byte
                break
            value = (value << 7) | (byte & 0x7F)
            if byte < 0x80:
                break
        out.append(value)
    return out


def _porter_terms(titles: list[str]) -> list[str]:
    """Each title as the space-separated terms FTS5's porter tokenizer
    indexes, so the app matches stemmed query prefixes against exactly
    what the server's title search matches against."""
    mem = sqlite3.connect(":memory:")
    mem.execute("CREATE VIRTUAL TABLE t USING fts5(x, tokenize=porter)")
    mem.executemany("INSERT INTO t(rowid, x) VALUES (?, ?)", [(i + 1, t) for i, t in enumerate(titles)])
    mem.execute("CREATE VIRTUAL TABLE v USING fts5vocab(t, 'instance')")
    terms: list[list[str]] = [[] for _ in titles]
    for doc, term in mem.execute("SELECT doc, term FROM v ORDER BY doc, offset"):
        terms[doc - 1].append(term)
    mem.close()
    return [" ".join(t) for t in terms]


def _top_sections(toc: sqlite3.Connection) -> dict[str, str]:
    """contentId -> title of its top-level TOC ancestor, like
    `uptodate.services._section_for`, for the whole tree at once."""
    nodes = {row["id"]: (row["title"], row["parentId"]) for row in toc.execute("SELECT id, title, parentId FROM toc")}
    memo: dict[int, str] = {}

    def top_title(start):
        chain, pid = [], start
        while pid and pid not in memo:
            node = nodes.get(pid)
            if node is None or pid in chain:
                found = ""
                break
            chain.append(pid)
            if not node[1]:
                found = node[0]
                break
            pid = node[1]
        else:
            found = memo.get(pid, "") if pid else ""
        for p in chain:
            memo[p] = found
        return found

    sections = {}
    for row in toc.execute("SELECT contentId, parentId FROM toc WHERE contentId IS NOT NULL ORDER BY rowid"):
        cid = str(row["contentId"])
        if cid not in sections:
            sections[cid] = top_title(row["parentId"])
    return sections


def build_uptodate(source_dir, out_dir, part_bytes, log=print) -> dict:
    src = Path(source_dir)
    version = _info_version(src)
    fts, content = _ro(src / "fts.db"), _ro(src / "content.db")
    toc_path, images_path = src / "toc.db", src / "images.db"
    sections = _top_sections(_ro(toc_path)) if toc_path.is_file() else {}
    writer = PackWriter(out_dir, "uptodate", version, part_bytes)
    log(f"build {writer.build}")

    section_names: list[str] = []
    section_no: dict[str, int] = {}

    def section_index(name):
        if name not in section_no:
            section_no[name] = len(section_names)
            section_names.append(name)
        return section_no[name]

    # Articles: every content row, so graphics opened from inside an article
    # are there too.
    article_ids, article_locs = [], []
    total = content.execute("SELECT count(*) FROM content").fetchone()[0]
    for n, row in enumerate(content.execute("SELECT id, gzip, version FROM content ORDER BY rowid"), 1):
        cid = str(row["id"])
        article = uptodate_services.article_from_row(cid, row["gzip"], row["version"] or version, sections.get(cid, ""))
        if article is None:
            continue
        article_ids.append(cid)
        article_locs.extend(writer.add(pack_json(article)))
        if n % 5000 == 0 or n == total:
            log(f"articles {n}/{total}")

    # Searchable topics (type 1) with the text their snippet is cut from, and
    # each row's token count, which FTS5's bm25 ranks by (shorter first) --
    # so the app can order title matches the way the server does.
    sizes = {row["id"]: sum(_varints(row["sz"])) for row in fts.execute("SELECT id, sz FROM fts_docsize")}
    topic_ids, titles, topic_sections, updated, head_locs, lengths = [], [], [], [], [], []
    seen = set()
    rows = fts.execute(
        "SELECT rowid, title, contentId, substr(content, 1, ?) AS head FROM fts WHERE type = ? ORDER BY rowid",
        (SNIPPET_SOURCE_CHARS, uptodate_services.TOPIC_TYPE),
    )
    for row in rows:
        cid = str(row["contentId"])
        if cid in seen:
            continue
        seen.add(cid)
        head = row["head"] or ""
        topic_ids.append(cid)
        titles.append(row["title"] or "")
        lengths.append(sizes.get(row["rowid"], 0))
        topic_sections.append(section_index(sections.get(cid, "")))
        updated.append(uptodate_services._updated_from_text(head.replace("\xa0", " ")))
        head_locs.extend(writer.add(pack_text(uptodate_services.snippet_source(head, row["title"] or ""))))
    log(f"topics {len(topic_ids)}")

    image_ids, image_types, image_locs = [], [], []
    if images_path.is_file():
        images = _ro(images_path)
        total = images.execute("SELECT count(*) FROM images").fetchone()[0]
        for n, row in enumerate(images.execute("SELECT id, binary, type FROM images ORDER BY rowid"), 1):
            if not row["binary"]:
                continue
            image_ids.append(str(row["id"]))
            image_types.append((row["type"] or "").lower())
            image_locs.extend(writer.add(bytes(row["binary"])))
            if n % 5000 == 0 or n == total:
                log(f"images {n}/{total}")

    return writer.finish({
        "dataset": "uptodate",
        "version": version,
        "sections": section_names,
        "topics": {
            "ids": topic_ids,
            "titles": titles,
            "sections": topic_sections,
            "updated": updated,
            "heads": head_locs,
            "terms": _porter_terms(titles),
            "lengths": lengths,
        },
        # bm25's corpus figures: every row, not only topics
        "rows": len(sizes),
        "avg_length": (sum(sizes.values()) / len(sizes)) if sizes else 0,
        "articles": {"ids": article_ids, "locs": article_locs},
        "images": {"ids": image_ids, "types": image_types, "locs": image_locs},
    })


def build_lexicomp(source_dir, out_dir, part_bytes, log=print) -> dict:
    src = Path(source_dir)
    db = _ro(src / "interact.db")
    version = _info_version(src)
    writer = PackWriter(out_dir, "lexicomp", version, part_bytes)
    log(f"build {writer.build}")

    monographs = []
    for row in db.execute("SELECT * FROM monograph ORDER BY id"):
        texts = {k: row[k] or "" for k in ("summary", "management", "discussion", "footnotes")}
        monographs.append([
            row["id"], row["object_id"], row["precipitant_id"], row["severity_id"], row["reliability_id"],
            *writer.add(pack_json(texts)),
        ])
    log(f"monographs {len(monographs)}")

    return writer.finish({
        "dataset": "lexicomp",
        "version": version,
        "generics": [[r["id"], r["name"]] for r in db.execute("SELECT id, name FROM generic ORDER BY id")],
        "brands": [[r["id"], r["generic_id"], r["name"]] for r in db.execute("SELECT id, generic_id, name FROM brand ORDER BY id")],
        "xref": [[r["category_id"], r["generic_id"]] for r in db.execute("SELECT category_id, generic_id FROM category_generic_xref")],
        "severity": {str(r["id"]): r["severity"] for r in db.execute("SELECT id, severity FROM severity")},
        "reliability": {str(r["id"]): r["reliability"] for r in db.execute("SELECT id, reliability FROM reliability")},
        "monographs": monographs,
        "exceptions": [
            [r["monograph_id"], r["category_id"], r["generic_id"]]
            for r in db.execute("SELECT monograph_id, category_id, generic_id FROM monograph_generic_exception_xref")
        ],
    })


BUILDERS = {"uptodate": build_uptodate, "lexicomp": build_lexicomp}
