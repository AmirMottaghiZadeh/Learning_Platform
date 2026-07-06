from django.db import models

class DrugTopic(models.Model):
    key = models.CharField(max_length=50, unique=True)
    label = models.CharField(max_length=120)
    detail = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return self.label

class Drug(models.Model):
    external_id = models.CharField(max_length=80, unique=True)
    name = models.CharField(max_length=255, blank=True)
    persian_name = models.CharField(max_length=255, blank=True)
    brand_name = models.TextField(blank=True)
    generic_name = models.TextField(blank=True)
    dosage_form = models.TextField(blank=True)
    drug_classification = models.TextField(blank=True)
    consumption_time = models.TextField(blank=True)
    consumption_time_sorted = models.CharField(max_length=80, blank=True)
    indication = models.TextField(blank=True)
    indication_answer = models.TextField(blank=True)
    side_effects = models.TextField(blank=True)
    side_effects_answer = models.TextField(blank=True)
    source_topic = models.CharField(max_length=255, blank=True)
    source_file = models.CharField(max_length=255, blank=True)
    raw = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.brand_name or self.name or self.external_id

class DrugQuestionSource(models.Model):
    TOPIC_CHOICES = [
        ("timing", "با غذا / بی غذا"),
        ("brandGeneric", "نام تجاری / ژنریک"),
        ("indication", "اندیکاسیون"),
        ("sideEffects", "عوارض جانبی"),
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
