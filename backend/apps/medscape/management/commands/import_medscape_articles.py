"""Import the Medscape Diseases & Conditions and Guidelines snapshots.

Diseases & Conditions: `<dir>/{medicine,pediatrics,surgery}/<specialty>.json`,
each a JSON array of articles already carrying `article_id`, `category` and
`specialty`. Guidelines: `<dir>/*.json`, each a JSON array of articles with
no id/category/specialty of their own -- category is fixed to "guideline"
and specialty comes from the source filename (there are only three: the
general guideline summaries, expert insights, and the primary-care-hacks
series).

Idempotent: diseases are matched on (kind, source_id) since article_id is
stable; guidelines have no upstream id, so they're matched on their source
URL's last path segment, which is itself a stable, globally unique slug.

Each section's body is a list of typed blocks (paragraph/list/table/image)
-- see apps.medscape.models for the shape -- copied through from the scraper
almost as-is, except:
- paragraph/list/table text is run through the same ad-loader-call stripper
  as before (`webmd.ads2.defineAd({...});`), since a handful of pages embed
  it mid-paragraph rather than as its own block.
- numbered citation markers (e.g. "[8, 6]", "[17]") are stripped from that
  same text. On the source site they're links into a References/Bibliography
  section; that section was never part of the scrape, so here they're just
  dead, unclickable clutter rather than a real citation trail.
- an image block's local `file` (content-addressed by the scraper, under
  --disease-images-dir / --guideline-images-dir) is read once and stored as
  an ArticleImage row (get_or_create on the content hash, so the same figure
  reused across articles is only ever stored once), and the block becomes
  {"type": "image", "id": <ArticleImage.pk>, "alt", "caption"} -- self-
  hosted from here on, no dependency on the source site staying up.
"""

import hashlib
import json
import mimetypes
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.medscape.models import Article, ArticleImage

DEFAULT_DISEASES_DIR = "/home/amir/Documents/Medscape/Diseases & Conditions"
DEFAULT_GUIDELINES_DIR = "/home/amir/Documents/Medscape/guidlines"
DEFAULT_DISEASE_IMAGES_DIR = "/home/amir/Documents/Medscape/emedicine_images"
DEFAULT_GUIDELINE_IMAGES_DIR = "/home/amir/Documents/Medscape/guideline_images"

_AD_CALL = re.compile(r"webmd\.[\w.]+\([^)]*\)\s*;?")
_CITATION_MARKER = re.compile(r"\s*\[\d+(?:,\s*\d+)*\]")
_BLANK_LINES = re.compile(r"\n{3,}")

GUIDELINE_SPECIALTY_BY_FILENAME = {
    "guidelines_content.json": "Guidelines",
    "Expert_insights.json": "Expert Insights",
    "Primary Care Hacks.json": "Primary Care Hacks",
}


def _clean_text(text):
    if not text:
        return ""
    cleaned = _AD_CALL.sub("", text)
    cleaned = _CITATION_MARKER.sub("", cleaned)
    return _BLANK_LINES.sub("\n\n", cleaned).strip()


class ImageResolver:
    """Reads a scraped image once per content-hash and get_or_creates its
    ArticleImage row, so the same figure referenced by many blocks (or many
    articles) is only ever read from disk / written to the DB once per run."""

    def __init__(self, images_dir: Path):
        self.images_dir = images_dir
        self._cache: dict[str, int | None] = {}

    def resolve(self, block: dict) -> dict | None:
        filename = block.get("file")
        if not filename:
            return None
        content_hash = Path(filename).stem
        if content_hash in self._cache:
            image_id = self._cache[content_hash]
        else:
            image_id = self._load(filename, content_hash, block.get("url") or block.get("src") or "")
            self._cache[content_hash] = image_id
        if image_id is None:
            return None
        return {
            "type": "image",
            "id": image_id,
            "alt": _clean_text(block.get("alt")),
            "caption": _clean_text(block.get("caption")),
        }

    def _load(self, filename: str, content_hash: str, source_url: str) -> int | None:
        existing = ArticleImage.objects.filter(content_hash=content_hash).values_list("pk", flat=True).first()
        if existing is not None:
            return existing
        path = self.images_dir / filename
        try:
            data = path.read_bytes()
        except OSError:
            return None
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        image = ArticleImage.objects.create(
            content_hash=content_hash or hashlib.sha256(data).hexdigest(),
            content_type=content_type,
            data=data,
            source_url=source_url,
        )
        return image.pk


def _clean_blocks(blocks, resolver: ImageResolver):
    cleaned = []
    for b in blocks or []:
        btype = b.get("type")
        if btype == "paragraph":
            text = _clean_text(b.get("text"))
            if text:
                cleaned.append({"type": "paragraph", "text": text})
        elif btype == "list":
            items = [_clean_text(i) for i in (b.get("items") or [])]
            items = [i for i in items if i]
            if items:
                cleaned.append({"type": "list", "ordered": bool(b.get("ordered")), "items": items})
        elif btype == "table":
            headers = [_clean_text(h) for h in b["headers"]] if b.get("headers") else None
            rows = [[_clean_text(c) for c in row] for row in (b.get("rows") or [])]
            if headers or rows:
                cleaned.append({"type": "table", "headers": headers, "rows": rows})
        elif btype == "image":
            resolved = resolver.resolve(b)
            if resolved:
                cleaned.append(resolved)
    return cleaned


def _clean_sections(sections, child_key, resolver: ImageResolver):
    cleaned = []
    for s in sections or []:
        cleaned.append({
            "heading": _clean_text(s.get("heading") or ""),
            "blocks": _clean_blocks(s.get("blocks"), resolver),
            "children": _clean_sections(s.get(child_key) or [], child_key, resolver),
        })
    return cleaned


def _specialty_label(raw):
    return raw.replace("_", " ").replace("guide ", "").strip().title()


class Command(BaseCommand):
    help = "Import the Medscape Diseases & Conditions and Guidelines snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--diseases-dir", default=DEFAULT_DISEASES_DIR)
        parser.add_argument("--guidelines-dir", default=DEFAULT_GUIDELINES_DIR)
        parser.add_argument("--disease-images-dir", default=DEFAULT_DISEASE_IMAGES_DIR)
        parser.add_argument("--guideline-images-dir", default=DEFAULT_GUIDELINE_IMAGES_DIR)
        parser.add_argument(
            "--limit", type=int, default=0,
            help="Import at most this many articles per source file (0 = all).",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        diseases_dir = Path(options["diseases_dir"])
        guidelines_dir = Path(options["guidelines_dir"])
        disease_images = ImageResolver(Path(options["disease_images_dir"]))
        guideline_images = ImageResolver(Path(options["guideline_images_dir"]))
        limit = options["limit"]
        dry_run = options["dry_run"]

        stats = {"created": 0, "updated": 0, "skipped": 0}
        with transaction.atomic():
            if diseases_dir.is_dir():
                self._import_diseases(diseases_dir, limit, stats, disease_images)
            else:
                self.stderr.write(self.style.WARNING(f"Diseases dir not found: {diseases_dir}"))

            if guidelines_dir.is_dir():
                self._import_guidelines(guidelines_dir, limit, stats, guideline_images)
            else:
                self.stderr.write(self.style.WARNING(f"Guidelines dir not found: {guidelines_dir}"))

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            "import_medscape_articles %s: %d created / %d updated, %d skipped"
            % ("(dry-run)" if dry_run else "done", stats["created"], stats["updated"], stats["skipped"])
        ))

    def _import_diseases(self, root, limit, stats, images: ImageResolver):
        # Collected across every file first, keyed by article_id: about a
        # third of disease articles are cross-listed under more than one
        # specialty in the source (same article_id reappearing in a
        # different specialty's file), and every pair it was filed under
        # needs to survive -- not just whichever file is processed last.
        by_id = {}
        for category_dir in sorted(root.iterdir()):
            if not category_dir.is_dir():
                continue
            for source_file in sorted(category_dir.glob("*.json")):
                try:
                    records = json.loads(source_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError) as e:
                    raise CommandError(f"Failed to read {source_file}: {e}")
                if limit > 0:
                    records = records[:limit]
                for rec in records:
                    self._collect_disease(rec, by_id, stats, images)

        for source_id, data in by_id.items():
            _, created = Article.objects.update_or_create(
                kind=Article.DISEASE,
                source_id=source_id,
                defaults={
                    "slug": f"{slugify(data['title']) or 'article'}-{source_id}",
                    "title": data["title"],
                    "meta": data["meta"],
                    "url": data["url"],
                    "sections": data["sections"],
                    "categories": data["categories"],
                },
            )
            stats["created" if created else "updated"] += 1

    def _collect_disease(self, rec, by_id, stats, images: ImageResolver):
        source_id = str(rec.get("article_id") or "").strip()
        title = (rec.get("title") or rec.get("link_text") or "").strip()
        if not source_id or not title:
            stats["skipped"] += 1
            return

        pair = {"category": rec.get("category") or "", "specialty": _specialty_label(rec.get("specialty") or "")}
        entry = by_id.get(source_id)
        if entry is None:
            by_id[source_id] = {
                "title": title,
                "meta": (rec.get("meta") or "").strip(),
                "url": rec.get("url") or "",
                "sections": _clean_sections(rec.get("sections"), "children", images),
                "categories": [pair],
            }
        elif pair not in entry["categories"]:
            entry["categories"].append(pair)

    def _import_guidelines(self, root, limit, stats, images: ImageResolver):
        for source_file in sorted(root.glob("*.json")):
            specialty = GUIDELINE_SPECIALTY_BY_FILENAME.get(source_file.name)
            if specialty is None:
                # Filenames in this snapshot carry a stray leading combining
                # mark on two of the three files -- match by suffix too.
                specialty = next(
                    (v for k, v in GUIDELINE_SPECIALTY_BY_FILENAME.items() if source_file.name.endswith(k)),
                    None,
                )
            if specialty is None:
                self.stderr.write(self.style.WARNING(f"Unrecognized guidelines file, skipping: {source_file}"))
                continue
            try:
                records = json.loads(source_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as e:
                raise CommandError(f"Failed to read {source_file}: {e}")
            if limit > 0:
                records = records[:limit]
            for rec in records:
                self._save_guideline(rec, specialty, stats, images)

    def _save_guideline(self, rec, specialty, stats, images: ImageResolver):
        url = rec.get("url") or ""
        source_id = url.rstrip("/").rsplit("/", 1)[-1] if url else ""
        title = (rec.get("article_title") or rec.get("page_title") or rec.get("link_text") or "").strip()
        if not source_id or not title:
            stats["skipped"] += 1
            return

        _, created = Article.objects.update_or_create(
            kind=Article.GUIDELINE,
            source_id=source_id,
            defaults={
                "slug": f"g-{slugify(source_id) or 'article'}",
                "categories": [{"category": "guideline", "specialty": specialty}],
                "title": title,
                "meta": "",
                "url": url,
                "sections": _clean_sections(rec.get("sections"), "subsections", images),
            },
        )
        stats["created" if created else "updated"] += 1
