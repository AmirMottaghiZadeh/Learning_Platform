"""Interactive clinical calculators, imported from the Medscape/QxMD snapshot.

A calculator is always read and rendered as one self-contained document --
its questions and scoring formulas are never queried into individually -- so
they're kept as JSON blobs on a single row instead of normalized into
separate tables.

The scoring formulas (inside `results`) are plain JavaScript IIFE strings
copied through unevaluated, e.g.::

    (function() { return $0 + $1 + $2; })();

`$0`, `$1`, ... refer to answers by question position (so `questions` is
always kept sorted by its source `position`); `$result0`, `$result1`, ...
refer to earlier entries in `results`, computed in order. The client
substitutes these tokens with real values and evaluates the formula --
see import_medscape_calculators for exactly what's kept in each blob.
"""

from django.db import models
from django.utils.text import slugify


class Calculator(models.Model):
    calculator_id = models.CharField(max_length=20, unique=True)
    slug = models.SlugField(max_length=280, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)
    about = models.TextField(blank=True)
    author = models.TextField(blank=True)

    # Label-only -- never queried into individually, just searched/displayed.
    categories = models.JSONField(default=list, blank=True)
    tags = models.JSONField(default=list, blank=True)
    questions = models.JSONField(default=list, blank=True)
    results = models.JSONField(default=list, blank=True)
    references = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.calculator_id})"

    @staticmethod
    def build_slug(name, calculator_id):
        """Deterministic, unique slug: the name plus the source id as a suffix."""
        base = slugify(name) or "calculator"
        return f"{base}-{calculator_id}"
