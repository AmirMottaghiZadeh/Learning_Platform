"""Build the UpToDate title index and search catalog before a reader asks.

Both are cached per web process and built from the whole fts table (and the
snapshot's search catalog) on first use. On a remote MySQL mirror that build
takes seconds, so the first search after a deploy used to wait for it while
every other UpToDate request queued behind the same lock. Run this at boot,
in the background, to pay that cost before anyone is waiting.
"""

from django.core.management.base import BaseCommand

from apps.uptodate import services


class Command(BaseCommand):
    help = "Warm the UpToDate search caches (title index and catalog)."

    def handle(self, *args, **options):
        if not services.is_available():
            self.stdout.write("UpToDate data is not available; nothing to warm.")
            return
        version = services.snapshot_version()
        index = services._title_index(version)
        catalog = services._search_catalog(version)
        self.stdout.write(
            f"Warmed UpToDate search: version={version or '-'} "
            f"titles={len(index.ids)} catalog_queries={len(catalog.queries)}"
        )
