import uuid

from django.conf import settings
from django.db import models
from django.utils import timezone


class Conversation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="support_conversations")
    kind = models.CharField(max_length=12, default="general")
    subject = models.CharField(max_length=120, default="پشتیبانی فارمنتا")
    status = models.CharField(max_length=12, choices=[("open", "باز"), ("closed", "بسته")], default="open")
    user_read_id = models.PositiveBigIntegerField(default=0)
    staff_read_id = models.PositiveBigIntegerField(default=0)
    updated_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["user"], condition=models.Q(kind="general"), name="support_one_general_conversation")]


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    from_staff = models.BooleanField(default=False)
    client_id = models.UUIDField(default=uuid.uuid4)
    text = models.TextField(max_length=4000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]
        constraints = [models.UniqueConstraint(fields=["conversation", "sender", "client_id"], name="support_message_idempotency")]
        indexes = [models.Index(fields=["conversation", "from_staff", "id"], name="support_unread_index")]


class PushSubscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    session = models.ForeignKey("accounts.UserSession", on_delete=models.CASCADE, null=True)
    device_id = models.CharField(max_length=64)
    platform = models.CharField(max_length=12, choices=[("android", "Android"), ("web", "Web")])
    expo_token = models.CharField(max_length=255, blank=True)
    web_subscription = models.JSONField(default=dict, blank=True)
    enabled = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["user", "device_id"], name="support_push_user_device")]


class NotificationDelivery(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    subscription = models.ForeignKey(PushSubscription, on_delete=models.CASCADE)
    status = models.CharField(max_length=16, default="pending")
    attempts = models.PositiveSmallIntegerField(default=0)
    error = models.CharField(max_length=255, blank=True)
    provider_id = models.CharField(max_length=128, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["message", "subscription"], name="support_push_delivery_unique")]
