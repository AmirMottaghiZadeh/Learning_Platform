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

The source content carries inline ad-loader calls from the page it was
scraped from (`webmd.ads2.defineAd({...});`), stripped recursively from
every section's content on the way in.
"""

import json
import re
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils.text import slugify

from apps.medscape.models import Article

DEFAULT_DISEASES_DIR = "/home/amir/Desktop/Documents/Medscape/Diseases & Conditions"
DEFAULT_GUIDELINES_DIR = "/home/amir/Desktop/Documents/Medscape/guidlines"

_AD_CALL = re.compile(r"webmd\.[\w.]+\([^)]*\)\s*;?")
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
    return _BLANK_LINES.sub("\n\n", cleaned).strip()


def _clean_sections(sections, child_key):
    cleaned = []
    for s in sections or []:
        cleaned.append({
            "heading": (s.get("heading") or "").strip(),
            "content": _clean_text(s.get("content")),
            "children": _clean_sections(s.get(child_key) or [], child_key),
        })
    return cleaned


def _specialty_label(raw):
    return raw.replace("_", " ").replace("guide ", "").strip().title()


class Command(BaseCommand):
    help = "Import the Medscape Diseases & Conditions and Guidelines snapshots."

    def add_arguments(self, parser):
        parser.add_argument("--diseases-dir", default=DEFAULT_DISEASES_DIR)
        parser.add_argument("--guidelines-dir", default=DEFAULT_GUIDELINES_DIR)
        parser.add_argument(
            "--limit", type=int, default=0,
            help="Import at most this many articles per source file (0 = all).",
        )
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **options):
        diseases_dir = Path(options["diseases_dir"])
        guidelines_dir = Path(options["guidelines_dir"])
        limit = options["limit"]
        dry_run = options["dry_run"]

        stats = {"created": 0, "updated": 0, "skipped": 0}
        with transaction.atomic():
            if diseases_dir.is_dir():
                self._import_diseases(diseases_dir, limit, stats)
            else:
                self.stderr.write(self.style.WARNING(f"Diseases dir not found: {diseases_dir}"))

            if guidelines_dir.is_dir():
                self._import_guidelines(guidelines_dir, limit, stats)
            else:
                self.stderr.write(self.style.WARNING(f"Guidelines dir not found: {guidelines_dir}"))

            if dry_run:
                transaction.set_rollback(True)

        self.stdout.write(self.style.SUCCESS(
            "import_medscape_articles %s: %d created / %d updated, %d skipped"
            % ("(dry-run)" if dry_run else "done", stats["created"], stats["updated"], stats["skipped"])
        ))

    def _import_diseases(self, root, limit, stats):
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
                    self._collect_disease(rec, by_id, stats)

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

    def _collect_disease(self, rec, by_id, stats):
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
                "sections": _clean_sections(rec.get("sections"), "children"),
                "categories": [pair],
            }
        elif pair not in entry["categories"]:
            entry["categories"].append(pair)

    def _import_guidelines(self, root, limit, stats):
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
                self._save_guideline(rec, specialty, stats)

    def _save_guideline(self, rec, specialty, stats):
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
                "sections": _clean_sections(rec.get("sections"), "subsections"),
            },
        )
        stats["created" if created else "updated"] += 1
