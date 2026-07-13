from django.db import models


class DrugDatasetDocument(models.Model):
    schema_version = models.CharField(max_length=20)
    source_file = models.CharField(max_length=255)
    source_path = models.TextField(blank=True)
    source_format = models.CharField(max_length=40, blank=True)
    source_size_bytes = models.PositiveBigIntegerField(default=0)
    source_sha256 = models.CharField(max_length=64, unique=True)
    source_metadata = models.JSONField(default=dict, blank=True)
    extraction_metadata = models.JSONField(default=dict, blank=True)
    warnings = models.JSONField(default=list, blank=True)
    enrichment_metadata = models.JSONField(default=dict, blank=True)
    imported_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["source_file"]),
            models.Index(fields=["schema_version"]),
        ]

    def __str__(self):
        return self.source_file


class DrugTopic(models.Model):
    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=120)
    detail = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.label

class Drug(models.Model):
    dataset_document = models.ForeignKey(
        DrugDatasetDocument,
        on_delete=models.CASCADE,
        related_name="drugs",
        null=True,
        blank=True,
    )
    external_id = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=255, blank=True)
    persian_name = models.CharField(max_length=255, blank=True)
    brand_name = models.TextField(blank=True)
    generic_name = models.TextField(blank=True)
    dosage_form = models.TextField(blank=True)
    drug_classification = models.TextField(blank=True)
    consumption_time = models.TextField(blank=True)
    consumption_time_sorted = models.TextField(blank=True)
    indication = models.TextField(blank=True)
    indication_answer = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    side_effects_answer = models.TextField(blank=True)
    dosing_and_administration = models.TextField(blank=True)
    pregnancy = models.TextField(blank=True)
    breastfeeding = models.TextField(blank=True)
    dose_adjustment = models.TextField(blank=True)
    clinical_notes = models.TextField(blank=True)
    atc_codes = models.JSONField(default=list, blank=True)
    atc_classes = models.JSONField(default=list, blank=True)
    atc_subclasses = models.JSONField(default=list, blank=True)
    atc_categories = models.JSONField(default=list, blank=True)
    category = models.JSONField(default=list, blank=True)
    source_topic = models.CharField(max_length=255, blank=True)
    source_file = models.CharField(max_length=255, blank=True)
    source_table = models.PositiveIntegerField(default=0)
    source_row = models.PositiveIntegerField(default=0)
    extra_attributes = models.JSONField(default=dict, blank=True)
    raw = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["source_file", "source_table", "source_row"]),
        ]

    def __str__(self):
        return self.brand_name or self.name or self.external_id

class DrugQuestionSource(models.Model):
    TOPIC_CHOICES = [
        ("timing", "با غذا / بی غذا"),
        ("brandGeneric", "نام تجاری / ژنریک"),
        ("indication", "اندیکاسیون"),
        ("sideEffects", "عوارض جانبی"),
        ("classification", "دسته‌بندی"),
        ("dosageForm", "اشکال دارویی"),
        ("dosing", "دوزینگ و دستور مصرف"),
        ("pregnancy", "بارداری و شیردهی"),
        ("doseAdjustment", "تنظیم دوز"),
    ]
    topic = models.ForeignKey(DrugTopic, on_delete=models.CASCADE, related_name="question_sources")
    drug = models.ForeignKey(Drug, on_delete=models.CASCADE, related_name="question_sources")
    question_type = models.CharField(max_length=50, choices=TOPIC_CHOICES)
    prompt = models.TextField()
    subtitle = models.TextField(blank=True)
    chip = models.TextField(blank=True)
    correct_answer = models.TextField()
    feedback = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = [("topic", "drug", "question_type", "correct_answer")]
        indexes = [models.Index(fields=["question_type", "is_active"])]
