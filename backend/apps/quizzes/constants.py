from django.db import models


class QuestionType(models.TextChoices):
    BRAND_GENERIC = "brandGeneric", "Brand → Generic"
    GENERIC_BRAND = "genericBrand", "Generic → Brand"
    INDICATION = "indication", "Indication"
    SIDE_EFFECTS = "sideEffects", "Side Effects"
    TIMING = "timing", "Food Timing"
    CLASSIFICATION = "classification", "Classification"
    DOSAGE_FORM = "dosageForm", "Dosage Form"
    DOSING = "dosing", "Dosing"
    PREGNANCY = "pregnancy", "Pregnancy"
    DOSE_ADJUSTMENT = "doseAdjustment", "Dose Adjustment"


TIMING_CHOICES = [
    "با غذا",
    "بدون غذا",
    "فرقی نمی‌کند",
    "وضعیت ثابت",
]