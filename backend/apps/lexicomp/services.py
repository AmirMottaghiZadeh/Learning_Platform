"""Read-only access to the bundled Lexicomp drug-interactions snapshot.

Same shape as `apps.uptodate.services`: a fixed, licensed reference dump,
opened read-only straight out of its SQLite file rather than imported into
Postgres. Layout (`settings.LEXICOMP_DB_DIR/interact.db`):

  generic(id, global_id, name, combination)      -- active ingredients
  brand(id, generic_id, name)                    -- trade names
  category(id, name)                             -- drug classes
  category_generic_xref(category_id, generic_id) -- a generic's classes,
                                                     including a "class of
                                                     one" matching its own id
  monograph(id, object_id, precipitant_id, severity_id, reliability_id,
            summary, management, discussion, footnotes, ...)
                                                  -- one interaction rule
                                                     between two *categories*
                                                     (object_id/precipitant_id
                                                     are category ids, not
                                                     generic ids)
  severity(id, severity), reliability(id, reliability)
  monograph_generic_exception_xref(monograph_id, category_id, generic_id)
                                                  -- "this rule doesn't apply
                                                     when the drug filling
                                                     that category-role is
                                                     specifically this one"

A pair of drugs interacts if any category either belongs to is the
object/precipitant of a monograph the other's categories fill the other role
of -- see `check_interactions`.
"""

import sqlite3
import threading
from pathlib import Path

from django.conf import settings

_LOCK = threading.Lock()
_CONN: sqlite3.Connection | None = None

# Lower sorts first -- unrecognised/"N/A" severities fall to the end.
SEVERITY_RANK = {"major": 0, "moderate": 1, "minor": 2}


def _dir() -> Path:
    return Path(getattr(settings, "LEXICOMP_DB_DIR", ""))


def is_available() -> bool:
    d = _dir()
    return bool(d) and (d / "interact.db").is_file()


def _conn() -> sqlite3.Connection:
    global _CONN
    with _LOCK:
        if _CONN is None:
            path = _dir() / "interact.db"
            _CONN = sqlite3.connect(f"file:{path}?mode=ro", uri=True, check_same_thread=False)
            _CONN.row_factory = sqlite3.Row
        return _CONN


def close_all() -> None:
    global _CONN
    with _LOCK:
        if _CONN is not None:
            _CONN.close()
            _CONN = None


def search_drugs(query: str, limit: int = 20) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return []
    contains = f"%{query}%"
    starts_with = f"{query}%"
    # SQLite requires an ORDER BY expression on a compound (UNION) query to
    # be a bare result-column reference, not an arbitrary expression -- so
    # the ranking/limit has to happen in an outer SELECT over the union
    # rather than tacked onto it directly.
    rows = _conn().execute(
        "SELECT * FROM ("
        "  SELECT id, name, id AS generic_id, 'generic' AS kind FROM generic WHERE name LIKE ? "
        "  UNION ALL "
        "  SELECT id, name, generic_id, 'brand' AS kind FROM brand WHERE name LIKE ? "
        ") "
        "ORDER BY (CASE WHEN name LIKE ? THEN 0 ELSE 1 END), length(name) "
        "LIMIT ?",
        (contains, contains, starts_with, int(limit)),
    ).fetchall()
    return [
        {"id": row["id"], "name": row["name"], "generic_id": row["generic_id"], "kind": row["kind"]}
        for row in rows
    ]


def _categories_for_generics(conn, generic_ids: list[int]) -> dict[int, set[int]]:
    placeholders = ",".join("?" for _ in generic_ids)
    rows = conn.execute(
        f"SELECT generic_id, category_id FROM category_generic_xref WHERE generic_id IN ({placeholders})",
        generic_ids,
    ).fetchall()
    result: dict[int, set[int]] = {gid: set() for gid in generic_ids}
    for row in rows:
        result[row["generic_id"]].add(row["category_id"])
    return result


def _names_for_generics(conn, generic_ids: list[int]) -> dict[int, str]:
    placeholders = ",".join("?" for _ in generic_ids)
    rows = conn.execute(
        f"SELECT id, name FROM generic WHERE id IN ({placeholders})", generic_ids
    ).fetchall()
    return {row["id"]: row["name"] for row in rows}


def _exceptions_for_monographs(conn, monograph_ids: list[int]) -> dict[int, list[dict]]:
    if not monograph_ids:
        return {}
    placeholders = ",".join("?" for _ in monograph_ids)
    rows = conn.execute(
        f"SELECT monograph_id, category_id, generic_id FROM monograph_generic_exception_xref "
        f"WHERE monograph_id IN ({placeholders})",
        monograph_ids,
    ).fetchall()
    by_monograph: dict[int, list[dict]] = {}
    for row in rows:
        by_monograph.setdefault(row["monograph_id"], []).append(row)
    return by_monograph


def _severity_and_reliability(conn) -> tuple[dict[int, str], dict[int, str]]:
    severities = {r["id"]: r["severity"] for r in conn.execute("SELECT id, severity FROM severity")}
    reliabilities = {
        r["id"]: r["reliability"] for r in conn.execute("SELECT id, reliability FROM reliability")
    }
    return severities, reliabilities


def check_interactions(generic_ids: list[int]) -> list[dict]:
    """Every applicable interaction between any two of the given generics.

    A monograph matches a pair (a, b) when one's categories contain its
    object_id and the other's contain its precipitant_id (either
    assignment). It's then dropped only if *every* valid assignment is
    blocked by a generic-specific exception for that exact role -- a
    monograph with two valid role assignments where just one is excepted
    still surfaces, using the assignment that isn't.
    """
    ids = sorted({int(g) for g in generic_ids})
    if len(ids) < 2:
        return []

    conn = _conn()
    cats = _categories_for_generics(conn, ids)
    names = _names_for_generics(conn, ids)
    severities, reliabilities = _severity_and_reliability(conn)

    matches: dict[tuple, sqlite3.Row] = {}
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            cats_a, cats_b = cats[a], cats[b]
            if not cats_a or not cats_b:
                continue
            ph_a = ",".join("?" for _ in cats_a)
            ph_b = ",".join("?" for _ in cats_b)
            rows = conn.execute(
                f"SELECT * FROM monograph WHERE "
                f"(object_id IN ({ph_a}) AND precipitant_id IN ({ph_b})) "
                f"OR (object_id IN ({ph_b}) AND precipitant_id IN ({ph_a}))",
                [*cats_a, *cats_b, *cats_b, *cats_a],
            ).fetchall()
            for row in rows:
                matches[(row["id"], a, b)] = row

    exceptions = _exceptions_for_monographs(conn, [row["id"] for row in matches.values()])

    results = []
    for (monograph_id, a, b), row in matches.items():
        cats_a, cats_b = cats[a], cats[b]
        candidates = []
        if row["object_id"] in cats_a and row["precipitant_id"] in cats_b:
            candidates.append((a, b))
        if row["object_id"] in cats_b and row["precipitant_id"] in cats_a:
            candidates.append((b, a))

        excepted = exceptions.get(monograph_id, [])
        excepted_object = {e["generic_id"] for e in excepted if e["category_id"] == row["object_id"]}
        excepted_precipitant = {
            e["generic_id"] for e in excepted if e["category_id"] == row["precipitant_id"]
        }
        valid = [
            (obj, prec)
            for obj, prec in candidates
            if obj not in excepted_object and prec not in excepted_precipitant
        ]
        if not valid:
            continue
        object_drug, precipitant_drug = valid[0]

        results.append({
            "monograph_id": monograph_id,
            "drug_ids": [a, b],
            "object_generic_id": object_drug,
            "object_name": names.get(object_drug, ""),
            "precipitant_generic_id": precipitant_drug,
            "precipitant_name": names.get(precipitant_drug, ""),
            "severity": severities.get(row["severity_id"], "N/A"),
            "reliability": reliabilities.get(row["reliability_id"], ""),
            "summary": row["summary"] or "",
            "management": row["management"] or "",
            "discussion": row["discussion"] or "",
            "footnotes": row["footnotes"] or "",
        })

    results.sort(key=lambda r: SEVERITY_RANK.get(r["severity"].lower(), 99))
    return results
