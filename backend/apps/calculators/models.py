"""Interactive clinical calculators, imported from a bilingual (en/fa)
Medscape/QxMD snapshot -- see apps.calculators.management.commands.import_calculators.

A calculator is always read and rendered as one self-contained document --
its questions, scoring formulas and error checks are never queried into
individually -- so they're kept as JSON blobs on a single row instead of
normalized into separate tables. Every user-facing string in those blobs
carries both an English and a Persian key (`title`/`title_fa`, etc.); a
language-agnostic one (an answer_factor, a formula string) has only the one.

The scoring formulas (inside `results`) are plain JavaScript IIFE strings
copied through unevaluated, e.g.::

    (function() { return $0 + $1 + $2; })();

`$0`, `$1`, ... refer to answers by question position (so `questions` is
always kept sorted by its source `position`); `$result0`, `$result1`, ...
refer to earlier entries in `results`, computed in order. `error_checks`
formulas work the same way, but return true when that check *fails* (the
client shows its `title`/`answer` as a validation message instead of
computing a result). The client substitutes these tokens with real values
and evaluates the formula -- see import_calculators for exactly what's kept
in each blob.

Categories and tags are real rows (`CalculatorCategory`/`CalculatorTag`),
not flattened name strings: the source snapshot's own category tree
(`parent` + `is_main_category`) is the real two-level clinical taxonomy
calculator browsing groups by, in both languages, rather than a hand-
maintained English-only reconstruction of it.
"""

from django.db import models
from django.utils.text import slugify


class CalculatorCategory(models.Model):
    """One node of the source snapshot's own category tree. A main category
    (`is_main_category=True`) has no `parent`; every other row is a subtopic
    of one. A handful of names are genuinely cross-listed under more than
    one parent across different calculators -- that's a second `category`
    row with the same name but a different `parent`, not deduplicated,
    since the source snapshot itself keeps them distinct this way."""

    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    name_fa = models.CharField(max_length=255, blank=True)
    parent = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL, related_name="children"
    )
    is_main_category = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = "calculator categories"
        ordering = ["name"]

    def __str__(self):
        return self.name


class CalculatorTag(models.Model):
    external_id = models.IntegerField(unique=True)
    name = models.CharField(max_length=255)
    name_fa = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Calculator(models.Model):
    # The source snapshot's own stable string id ("CALC-715"), its natural
    # unique key -- used for import idempotency instead of the bare numeric
    # `calculator_id` (kept too, read-only metadata from the same source).
    uid = models.CharField(max_length=20, unique=True)
    calculator_id = models.CharField(max_length=20)
    url = models.URLField(max_length=500, blank=True)

    slug = models.SlugField(max_length=280, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    name_fa = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    description_fa = models.TextField(blank=True)
    about = models.TextField(blank=True)
    about_fa = models.TextField(blank=True)
    disclaimer_footer = models.TextField(blank=True)
    disclaimer_footer_fa = models.TextField(blank=True)

    categories = models.ManyToManyField(CalculatorCategory, related_name="calculators", blank=True)
    tags = models.ManyToManyField(CalculatorTag, related_name="calculators", blank=True)

    # Each bilingual, source-shaped (not normalized -- see module docstring).
    questions = models.JSONField(default=list, blank=True)
    results = models.JSONField(default=list, blank=True)
    error_checks = models.JSONField(default=list, blank=True)
    # English text a result formula returns literally -> its Persian
    # translation (see import_calculators._formula_strings_fa).
    formula_strings_fa = models.JSONField(default=dict, blank=True)
    references = models.JSONField(default=list, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.uid})"

    @staticmethod
    def build_slug(name, calculator_id):
        """Deterministic, unique slug: the name plus the source id as a suffix."""
        base = slugify(name) or "calculator"
        return f"{base}-{calculator_id}"
