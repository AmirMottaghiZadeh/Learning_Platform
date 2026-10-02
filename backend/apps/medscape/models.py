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
    # [{heading, content, children: [...]}, ...], arbitrary depth.
    sections = models.JSONField(default=list)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["title"]
        indexes = [models.Index(fields=["kind"])]

    def __str__(self):
        return f"{self.title} ({self.kind})"
