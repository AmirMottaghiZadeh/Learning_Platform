"""Medscape reference articles -- Diseases & Conditions and Guidelines.

Both kinds share the exact same shape once imported: a title, an optional
`meta`/`url`, and a tree of sections (heading + content, nested up to a few
levels deep in the source). An article is always read and rendered as one
whole document, never queried into section-by-section, so the tree is kept
as a single JSON blob rather than normalized into section rows -- the same
reasoning as apps.calculators' questions/results.

`categories` gives the two-level browse taxonomy the source itself organizes
by (medicine/pediatrics/surgery -> cardiology/... for diseases; one fixed
"guideline" category -> the three source files for guidelines). It's a list,
not a single pair: about a third of disease articles are genuinely
cross-listed under more than one specialty in the source (e.g. "Cardiac
Tamponade" under both Cardiology and Clinical Procedures), so every
(category, specialty) pair an article was ever filed under is kept rather
than letting the last-processed source file silently win.

`sections` is a tree of {heading, blocks, children}: each heading's own body
is a list of typed blocks --
  {"type": "paragraph", "text": str}
  {"type": "list", "ordered": bool, "items": [str, ...]}
  {"type": "table", "headers": [str, ...] | None, "rows": [[str, ...], ...]}
  {"type": "image", "id": <ArticleImage.pk>, "alt": str, "caption": str}
-- rather than one flattened string, so a table stays a table and a figure
stays an image instead of collapsing into prose.
"""

from django.db import models


class Article(models.Model):
    DISEASE = "disease"
    GUIDELINE = "guideline"
    KIND_CHOICES = [(DISEASE, "Disease"), (GUIDELINE, "Guideline")]

    kind = models.CharField(max_length=16, choices=KIND_CHOICES)
    source_id = models.CharField(max_length=200)
    slug = models.SlugField(max_length=320, unique=True)
    title = models.CharField(max_length=500)
    meta = models.TextField(blank=True)
    url = models.URLField(blank=True, max_length=600)
    # [{"category": "medicine", "specialty": "Cardiology"}, ...]
    categories = models.JSONField(default=list)
    # [{heading, blocks: [...], children: [...]}, ...], arbitrary depth.
    sections = models.JSONField(default=list)
    # Most recent date mentioned in a "Latest Guidance Updates" (or similar)
    # section, for guidelines that have one -- about a quarter of them do.
    # None for everything else (diseases, and guidelines without a change
    # log). Lets the UI surface what's actually changed recently instead of
    # only offering alphabetical browsing.
    latest_update = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["kind"])]

    def __str__(self):
        return f"{self.title} ({self.kind})"


class ArticleImage(models.Model):
    """A figure/diagram downloaded from the source site, content-addressed by
    the sha256 the scraper already hashed it by -- the same image reused
    across many articles (logos, shared diagrams) is stored exactly once.
    """

    content_hash = models.CharField(max_length=64, unique=True)
    content_type = models.CharField(max_length=40)
    data = models.BinaryField()
    source_url = models.URLField(blank=True, max_length=600)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.content_hash
