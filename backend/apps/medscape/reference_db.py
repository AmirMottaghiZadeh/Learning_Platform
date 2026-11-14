"""Medscape guidelines or diseases as a portable reference-data file (see
apps.core.reference_db) -- one kind per file, with the figures its articles
show stored inside it, so loading it needs nothing but the file.

Tables:
- article: one row per article, keyed by (kind, source_id) like the
  original importer; `categories` / `sections` are the stored JSON as text.
- image: content_hash, content_type, source_url, data (the image bytes).

An image block inside `sections` points at its figure by database id, and
ids differ between databases -- so in the file the block carries the
image's content hash instead ({"type": "image", "hash": ...}), and the
import swaps it back for the id the image has on the target.
"""

from datetime import date

from django.db import transaction
from django.utils import timezone

from apps.core.reference_db import dumps, expected_count, loads, record_counts, rows

from .models import Article, ArticleImage

DATASET_FOR_KIND = {Article.GUIDELINE: "guidelines", Article.DISEASE: "diseases"}

SCHEMA = """
CREATE TABLE article (
    kind TEXT NOT NULL, source_id TEXT NOT NULL, slug TEXT NOT NULL, title TEXT NOT NULL,
    meta TEXT NOT NULL, url TEXT NOT NULL, categories TEXT NOT NULL, sections TEXT NOT NULL,
    latest_update TEXT,
    PRIMARY KEY (kind, source_id)
);
CREATE TABLE image (
    content_hash TEXT PRIMARY KEY, content_type TEXT NOT NULL, source_url TEXT NOT NULL, data BLOB NOT NULL
);
"""

IMAGE_BATCH = 100


def _map_images(sections, swap):
    """A copy of the section tree with every image block passed through
    `swap(block)`, which returns the replacement block or None to drop it."""
    out = []
    for section in sections or []:
        blocks = []
        for block in section.get("blocks", []):
            if block.get("type") == "image":
                block = swap(block)
                if block is None:
                    continue
            blocks.append(block)
        out.append({**section, "blocks": blocks, "children": _map_images(section.get("children", []), swap)})
    return out


def export(conn, kind, log=print):
    """Writes every article of `kind`, and the images they show, into
    `conn`. Returns the row counts."""
    conn.executescript(SCHEMA)
    hash_of = dict(ArticleImage.objects.values_list("pk", "content_hash"))
    used, missing = set(), 0

    def to_hash(block):
        nonlocal missing
        image_hash = hash_of.get(block.get("id"))
        if image_hash is None:
            missing += 1
            return None
        used.add(block["id"])
        return {"type": "image", "hash": image_hash, "alt": block.get("alt", ""), "caption": block.get("caption", "")}

    articles = 0
    for a in Article.objects.filter(kind=kind).order_by("source_id").iterator(chunk_size=100):
        conn.execute(
            "INSERT INTO article VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                a.kind, a.source_id, a.slug, a.title, a.meta or "", a.url or "",
                dumps(a.categories), dumps(_map_images(a.sections, to_hash)),
                a.latest_update.isoformat() if a.latest_update else None,
            ),
        )
        articles += 1
    if missing:
        log(f"  {missing} image block(s) pointed at a missing image and were left out")

    ids = sorted(used)
    for start in range(0, len(ids), IMAGE_BATCH):
        chunk = ArticleImage.objects.filter(pk__in=ids[start:start + IMAGE_BATCH]).values_list(
            "content_hash", "content_type", "source_url", "data"
        )
        conn.executemany(
            "INSERT INTO image VALUES (?, ?, ?, ?)",
            [(h, ct, url or "", bytes(data)) for h, ct, url, data in chunk],
        )
    counts = {"article": articles, "image": len(ids)}
    record_counts(conn, counts)
    return counts


def load(conn, meta, kind, *, prune=False, log=print):
    """Adds the file's images the target doesn't have yet (matched on
    content hash), then upserts its articles (matched on kind + source_id)
    with their image blocks pointing at the target's image ids. With
    `prune`, articles of this kind absent from the file are deleted. One
    transaction: on any error nothing is written. Returns a summary dict."""
    summary = {}
    with transaction.atomic():
        # -- images --------------------------------------------------------------
        added = 0
        cur = conn.execute("SELECT content_hash, content_type, source_url, data FROM image")
        while True:
            batch = cur.fetchmany(IMAGE_BATCH)
            if not batch:
                break
            have = set(
                ArticleImage.objects.filter(content_hash__in=[r[0] for r in batch]).values_list("content_hash", flat=True)
            )
            new = [
                ArticleImage(content_hash=h, content_type=ct, source_url=url, data=bytes(data))
                for h, ct, url, data in batch
                if h not in have
            ]
            ArticleImage.objects.bulk_create(new)
            added += len(new)
        file_hashes = [r[0] for r in conn.execute("SELECT content_hash FROM image")]
        id_of = {}
        for start in range(0, len(file_hashes), 1000):
            id_of.update(
                ArticleImage.objects.filter(content_hash__in=file_hashes[start:start + 1000]).values_list("content_hash", "pk")
            )
        summary["image"] = {"added": added, "already present": len(file_hashes) - added}

        expected = expected_count(meta, "image")
        if expected is not None and len(file_hashes) != expected:
            raise RuntimeError(f"Read {len(file_hashes)} images but the file says {expected}; it may be damaged.")

        dropped = 0

        def to_id(block):
            nonlocal dropped
            image_id = id_of.get(block.get("hash"))
            if image_id is None:
                dropped += 1
                return None
            return {"type": "image", "id": image_id, "alt": block.get("alt", ""), "caption": block.get("caption", "")}

        # -- articles ------------------------------------------------------------
        existing = dict(Article.objects.filter(kind=kind).values_list("source_id", "pk"))
        slug_owner = {slug: (k, sid) for slug, k, sid in Article.objects.values_list("slug", "kind", "source_id")}
        created = updated = skipped = 0
        seen = set()
        pending = []
        for row in rows(conn, "SELECT * FROM article WHERE kind = ?", (kind,), batch=50):
            seen.add(row["source_id"])
            fields = {
                "slug": row["slug"],
                "title": row["title"],
                "meta": row["meta"],
                "url": row["url"],
                "categories": loads(row["categories"], []),
                "sections": _map_images(loads(row["sections"], []), to_id),
                "latest_update": date.fromisoformat(row["latest_update"]) if row["latest_update"] else None,
            }
            owner = slug_owner.get(row["slug"])
            if owner is not None and owner != (kind, row["source_id"]):
                log(f"  skipped {row['source_id']}: slug '{row['slug']}' already belongs to {owner[0]} {owner[1]}")
                skipped += 1
                continue
            slug_owner[row["slug"]] = (kind, row["source_id"])
            pk = existing.get(row["source_id"])
            if pk is None:
                pending.append(Article(kind=kind, source_id=row["source_id"], **fields))
                created += 1
                if len(pending) >= 100:
                    Article.objects.bulk_create(pending)
                    pending = []
            else:
                Article.objects.filter(pk=pk).update(**fields, updated_at=timezone.now())
                updated += 1
        Article.objects.bulk_create(pending)
        summary["article"] = (created, updated)
        if skipped:
            summary["skipped"] = skipped
        if dropped:
            summary["image_blocks_without_image"] = dropped

        expected = expected_count(meta, "article")
        if expected is not None and len(seen) != expected:
            raise RuntimeError(f"Read {len(seen)} articles but the file says {expected}; it may be damaged.")

        if prune:
            gone = Article.objects.filter(kind=kind).exclude(source_id__in=seen)
            summary["pruned"] = {"article": gone.count()}
            gone.delete()
    return summary
