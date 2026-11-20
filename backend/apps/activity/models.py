import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class ActivityEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    visitor = models.CharField(max_length=64, blank=True)
    source = models.CharField(max_length=8, choices=[("site", "سایت"), ("app", "اپ")])
    section = models.CharField(max_length=64)
    action = models.CharField(max_length=16, choices=[("view", "بازدید"), ("engagement", "زمان فعال"), ("click", "کلیک / لمس")])
    x = models.PositiveSmallIntegerField(null=True, blank=True)
    y = models.PositiveSmallIntegerField(null=True, blank=True)
    area = models.CharField(max_length=12, default="screen", choices=[("screen", "صفحه"), ("article", "متن مقاله")])
    viewport = models.CharField(max_length=12, default="mobile", choices=[("mobile", "موبایل"), ("tablet", "تبلت"), ("desktop", "دسکتاپ")])
    duration_seconds = models.PositiveSmallIntegerField(default=0)
    occurred_at = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [models.Index(fields=["source", "occurred_at"], name="activity_source_time"), models.Index(fields=["section", "occurred_at"], name="activity_section_time")]
        ordering = ["-occurred_at"]
