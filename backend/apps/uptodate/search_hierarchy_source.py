"""Read-only snapshot adapter for the article-first retrieval experiment."""

from contextlib import ExitStack, closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import zlib

from .search_extraction import extract_article
from .search_hierarchy import ArticleCatalog, ArticleMetadata


class SQLiteHierarchySource:
    """Build metadata from ALL type=1 titles, then lazily load selected bodies."""

    def __init__(self, directory: Path, *, aliases=None):
        self.directory = Path(directory).resolve()
        self.aliases = aliases
        self.stack = ExitStack()

    def __enter__(self):
        try:
            paths = [self.directory / name for name in ("fts.db", "content.db")]
            self.signature = [(p.stat().st_size, p.stat().st_mtime_ns) for p in paths]
            self.snapshot_id = sha256(json.dumps(self.signature).encode()).hexdigest()
            self.titles, self.content = [self.stack.enter_context(closing(self._connect(p))) for p in paths]
            rows = self.titles.execute(
                "SELECT contentId, MIN(title) FROM fts WHERE type=1 AND contentId IS NOT NULL "
                "GROUP BY contentId ORDER BY contentId")
            self.catalog = ArticleCatalog((ArticleMetadata.from_title(str(key), title or "")
                                           for key, title in rows), aliases=self.aliases)
            self.metadata = {article.article_id: article for article in self.catalog.articles}
            return self
        except BaseException:
            self.stack.close()
            raise

    @staticmethod
    def _connect(path):
        return sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)

    def __exit__(self, *exc):
        return self.stack.__exit__(*exc)

    def check_snapshot(self):
        paths = [self.directory / name for name in ("fts.db", "content.db")]
        if [(p.stat().st_size, p.stat().st_mtime_ns) for p in paths] != self.signature:
            raise RuntimeError("Source snapshot changed during hierarchy evaluation")

    def load_article(self, article_id):
        self.check_snapshot()
        if article_id not in self.metadata:
            raise ValueError("Article is outside the independent title catalog")
        row = self.content.execute("SELECT gzip FROM content WHERE id=?", (article_id,)).fetchone()
        if row is None:
            raise ValueError("Selected article is missing from the snapshot")
        record = json.loads(zlib.decompress(row[0]))
        metadata = ArticleMetadata.from_title(article_id, record.get("title") or "")
        if metadata != self.metadata[article_id]:
            raise ValueError("Title catalog and article content disagree")
        # As in the v3 audit: monographs lacking topicText use the body fallback.
        # Its flat/unsectioned provenance is retained in the hierarchy trace.
        return extract_article(article_id, record.get("bodyHtml") or ""), record.get("outlineHtml") or ""

