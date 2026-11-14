import uuid
from django.conf import settings
from django.db import models


class AISettings(models.Model):
    enabled = models.BooleanField(default=False)
    base_url = models.URLField(default="https://api.gapgpt.app/v1")
    model = models.CharField(max_length=150, blank=True)
    encrypted_api_key = models.TextField(blank=True)
    reasoning_effort = models.CharField(max_length=12, blank=True, choices=[("", "ارسال نشود"), ("none", "none"), ("low", "low"), ("medium", "medium"), ("high", "high")])
    timeout_seconds = models.PositiveSmallIntegerField(default=90)
    max_output_tokens = models.PositiveIntegerField(default=5000)
    updated_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    updated_at = models.DateTimeField(auto_now=True)


class AIPromptPreset(models.Model):
    name = models.CharField(max_length=100)
    action = models.CharField(max_length=20, choices=[("structure", "ویرایش ساختاری جملات"), ("align", "تطبیق با متن خام OpenFDA"), ("fa_to_en", "ترجمه فارسی به انگلیسی"), ("en_to_fa", "ترجمه انگلیسی به فارسی"), ("custom", "دستور اختصاصی")], default="custom")
    instruction = models.TextField()
    active = models.BooleanField(default=True)
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["order", "pk"]


class AIEditRun(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    section = models.ForeignKey("drugs.IngredientProfileSection", on_delete=models.CASCADE)
    operator = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    model = models.CharField(max_length=150)
    action = models.CharField(max_length=20)
    instruction = models.TextField()
    target = models.CharField(max_length=5)
    input_digest = models.CharField(max_length=64)
    status = models.CharField(max_length=12, default="running")
    summary_fa = models.TextField(blank=True)
    summary_en = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    usage = models.JSONField(default=dict)
    error_code = models.CharField(max_length=40, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
