"""Drug-knowledge models.

The source of truth is the OpenFDA clinical-profile dataset: one ingredient per
RxNorm ingredient RXCUI, each carrying a dozen clinical-label fields plus a
Persian and English summary of every field.

The per-field text lives in :class:`IngredientProfileSection` rather than as wide
columns on :class:`Ingredient` so that:

* the Data Quality Center edits one field's summary at a time;
* a re-import can sync just the summaries (``import_openfda --only-summaries``)
  as they get written upstream;
* adding or dropping a clinical field needs no schema change.
"""

from django.db import models
from django.utils.text import slugify


# (key, English label) for every clinical field, in the order the lesson builder
# presents them. Defined at module scope so it can seed both the field choices
# and the ordering list without tripping over class-body comprehension scope.
CLINICAL_FIELDS = [
    ("indications_and_usage", "Indications and usage"),
    ("dosage_and_administration", "Dosage and administration"),
    # Added upstream in 2026-11 for about 900 ingredients; right under the dose.
    ("food_interactions", "Food interactions"),
    ("dosage_forms_and_strengths", "Dosage forms and strengths"),
    ("contraindications", "Contraindications"),
    ("do_not_use", "Do not use"),
    ("boxed_warning", "Boxed warning"),
    ("warnings", "Warnings"),
    ("adverse_reactions", "Adverse reactions"),
    ("drug_interactions", "Drug interactions"),
    ("pregnancy", "Pregnancy"),
    ("abuse", "Abuse"),
    ("clinical_pharmacology", "Clinical pharmacology"),
]
CLINICAL_FIELD_KEYS = [key for key, _ in CLINICAL_FIELDS]


class AtcCode(models.Model):
    """A WHO ATC classification node referenced by one or more ingredients."""

    code = models.CharField(max_length=8, unique=True)
    name = models.CharField(max_length=255)
    # Persian name, from apps.drugs.data.atc_l4_fa; blank when none is known.
    name_fa = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.name}"

    @property
    def level(self):
        """ATC level from code length: 1, 3, 4, 5 or 7 characters -> 1..5."""
        return {1: 1, 3: 2, 4: 3, 5: 4, 7: 5}.get(len(self.code), 0)


class AtcCategory(models.Model):
    """A named ATC anatomical (L1) or therapeutic (L2) group.

    The pipeline only carries L4 names, so the L1/L2 tree the lessons taxonomy
    needs is seeded from a bundled bilingual reference (`load_atc_reference`).
    """

    code = models.CharField(max_length=3, unique=True)  # "N" or "N02"
    name_en = models.CharField(max_length=200)
    name_fa = models.CharField(max_length=200)
    level = models.PositiveSmallIntegerField()  # 1 or 2
    parent = models.ForeignKey(
        "self",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="children",
    )

    class Meta:
        ordering = ["code"]
        verbose_name_plural = "ATC categories"

    def __str__(self):
        return f"{self.code} — {self.name_en}"


class Ingredient(models.Model):
    """An active ingredient, keyed by its RxNorm ingredient RXCUI."""

    rxcui = models.CharField(max_length=16, unique=True)
    name = models.CharField(max_length=255, db_index=True)
    # Persian name ("سیتالوپرام"), from the pipeline's ingredient_name_fa;
    # blank until import_openfda has filled it.
    name_fa = models.CharField(max_length=255, blank=True)
    slug = models.SlugField(max_length=280, unique=True)

    n_products = models.PositiveIntegerField(
        default=0,
        help_text="Distinct products contributing to this ingredient profile.",
    )
    n_source_records = models.PositiveIntegerField(
        default=0,
        help_text="Source label records rolled up into this profile.",
    )

    # Label-only, e.g. ["Thiazide Diuretic"]. Never queried on, so kept inline.
    pharm_classes = models.JSONField(default=list, blank=True)
    atc_codes = models.ManyToManyField(AtcCode, related_name="ingredients", blank=True)

    source_fetched_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by_username = models.CharField(max_length=150, blank=True, default="", db_default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.rxcui})"

    @staticmethod
    def build_slug(name, rxcui):
        """Deterministic, unique slug: the name plus the RXCUI as a suffix."""
        base = slugify(name) or "ingredient"
        return f"{base}-{rxcui}"

    @property
    def primary_atc(self):
        return self.atc_codes.order_by("code").first()

    @property
    def is_reviewed(self):
        if "_is_reviewed" in self.__dict__:
            return self.__dict__["_is_reviewed"]
        if not self.reviewed_at or self.updated_at > self.reviewed_at:
            return False
        return not self.sections.filter(updated_at__gt=self.reviewed_at).exists()


class IngredientChemistry(models.Model):
    """Validated PubChem chemistry, visible by default unless rejected or stale."""

    ingredient = models.OneToOneField(Ingredient, on_delete=models.CASCADE, related_name="chemistry")
    status = models.CharField(max_length=20, default="pending", choices=[
        ("pending", "نیازمند بازبینی"), ("approved", "تأیید شده"),
        ("rejected", "رد شده"), ("not_found", "یافت نشد"), ("ambiguous", "چند تطبیق"),
    ])
    pubchem_cid = models.PositiveBigIntegerField(null=True, blank=True)
    matched_name = models.CharField(max_length=255, blank=True)
    ingredient_name = models.CharField(max_length=255, blank=True, default="", db_default="")
    ingredient_rxcui = models.CharField(max_length=16, blank=True, default="", db_default="")
    molecular_formula = models.CharField(max_length=512, blank=True)
    smiles = models.TextField(blank=True)
    inchikey = models.CharField(max_length=64, blank=True)
    structure_svg = models.TextField(blank=True)
    candidates = models.JSONField(default=list, blank=True)
    fetched_at = models.DateTimeField(null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.CharField(max_length=150, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def source_url(self):
        return f"https://pubchem.ncbi.nlm.nih.gov/compound/{self.pubchem_cid}" if self.pubchem_cid else ""

    def __str__(self):
        return f"{self.ingredient.name}: {self.get_status_display()}"


class ChemistryReview(models.Model):
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE, related_name="chemistry_reviews")
    actor = models.CharField(max_length=150)
    action = models.CharField(max_length=20)
    snapshot = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)


class IngredientProfileSection(models.Model):
    """One clinical-label field for an ingredient, with its fa/en summaries."""

    FIELD_CHOICES = CLINICAL_FIELDS

    ingredient = models.ForeignKey(
        Ingredient,
        related_name="sections",
        on_delete=models.CASCADE,
    )
    field = models.CharField(max_length=40, choices=FIELD_CHOICES)

    raw_text = models.TextField(blank=True)
    n_contributing_products = models.PositiveIntegerField(default=0)
    summary_fa = models.TextField(blank=True)
    summary_en = models.TextField(blank=True)
    other_sources_fa = models.TextField(blank=True, default="", db_default="")
    other_sources_en = models.TextField(blank=True, default="", db_default="")

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["ingredient", "field"]
        constraints = [
            models.UniqueConstraint(
                fields=["ingredient", "field"],
                name="drugs_unique_ingredient_field",
            ),
        ]
        indexes = [
            models.Index(fields=["field"], name="drugs_section_field_idx"),
        ]

    def __str__(self):
        return f"{self.ingredient.name} · {self.get_field_display()}"

    @property
    def has_content(self):
        return bool((self.raw_text or "").strip())

    @property
    def has_summary(self):
        return bool((self.summary_fa or "").strip() or (self.summary_en or "").strip())
