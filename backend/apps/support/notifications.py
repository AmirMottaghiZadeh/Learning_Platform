"""Provider delivery for support replies; message contents stay in the chat."""

import base64
import json
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from .models import NotificationDelivery


def validate_web_subscription(subscription):
    if not isinstance(subscription, dict):
        raise ValueError("اشتراک اعلان وب معتبر نیست.")
    endpoint = subscription.get("endpoint", "")
    if not isinstance(endpoint, str) or len(endpoint) > 2048:
        raise ValueError("نشانی اعلان وب معتبر نیست.")
    url = urlsplit(endpoint)
    host = (url.hostname or "").lower()
    # Never let a subscription turn the application server into an arbitrary
    # HTTP client. These are browser push services, not user-supplied hosts.
    allowed = host in {"fcm.googleapis.com", "updates.push.services.mozilla.com", "web.push.apple.com"} or host.endswith(".notify.windows.com")
    try:
        valid = url.scheme == "https" and allowed and url.port in {None, 443} and not url.username and not url.password and not url.fragment
    except ValueError:
        valid = False
    if not valid:
        raise ValueError("سرویس اعلان این مرورگر پشتیبانی نمی‌شود.")
    keys = subscription.get("keys", {})
    try:
        public = base64.urlsafe_b64decode(keys["p256dh"] + "=" * (-len(keys["p256dh"]) % 4))
        auth = base64.urlsafe_b64decode(keys["auth"] + "=" * (-len(keys["auth"]) % 4))
        if len(public) != 65 or public[0] != 4 or len(auth) != 16:
            raise ValueError
    except (ValueError, KeyError, TypeError):
        raise ValueError("کلیدهای اعلان وب معتبر نیستند.")


def send_delivery(delivery_id):
    with transaction.atomic():
        delivery = NotificationDelivery.objects.select_for_update(of=("self",)).select_related("subscription__session", "subscription__user", "message__conversation").get(pk=delivery_id)
        if delivery.status in {"sent", "accepted", "sending", "skipped"} or delivery.attempts >= 3:
            return True
        if not settings.SUPPORT_PUSH_NOTIFICATIONS_ENABLED:
            delivery.status = "skipped"
            delivery.error = "notifications_disabled"
            delivery.save(update_fields=["status", "error", "updated_at"])
            return True
        subscription = delivery.subscription
        message = delivery.message
        if not subscription.enabled or not subscription.user.is_active or not subscription.session or not subscription.session.is_active or message.pk <= message.conversation.user_read_id:
            delivery.status = "skipped"
            delivery.save(update_fields=["status", "updated_at"])
            return True
        delivery.status = "sending"
        delivery.attempts += 1
        delivery.save(update_fields=["status", "attempts", "updated_at"])
    payload = {"title": "پشتیبانی فارمنتا", "body": "یک پاسخ تازه از تیم پشتیبانی دارید.", "conversation_id": str(message.conversation_id), "message_id": message.pk, "url": "/?supportThread=" + str(message.conversation_id)}
    try:
        if subscription.platform == "android":
            body = {"to": subscription.expo_token, "title": payload["title"], "body": payload["body"], "sound": "default", "channelId": "support", "data": {"conversationId": str(message.conversation_id), "messageId": message.pk, "screen": "support"}}
            headers = {"Content-Type": "application/json", "Accept": "application/json"}
            if settings.SUPPORT_EXPO_ACCESS_TOKEN:
                headers["Authorization"] = "Bearer " + settings.SUPPORT_EXPO_ACCESS_TOKEN
            request = Request("https://exp.host/--/api/v2/push/send", data=json.dumps(body).encode(), headers=headers)
            with urlopen(request, timeout=8) as response:
                result = json.load(response)
            ticket = result.get("data", {})
            if ticket.get("status") != "ok":
                code = ticket.get("details", {}).get("error", "provider_error")
                if code == "DeviceNotRegistered":
                    subscription.enabled = False
                    subscription.save(update_fields=["enabled"])
                raise ValueError(code)
            NotificationDelivery.objects.filter(pk=delivery.pk).update(status="accepted", provider_id=ticket.get("id", ""), error="", updated_at=timezone.now())
        else:
            validate_web_subscription(subscription.web_subscription)
            if not settings.SUPPORT_WEB_PUSH_PRIVATE_KEY or not settings.SUPPORT_WEB_PUSH_PUBLIC_KEY:
                raise ValueError("web_push_not_configured")
            from pywebpush import webpush

            webpush(subscription_info=subscription.web_subscription, data=json.dumps(payload), vapid_private_key=settings.SUPPORT_WEB_PUSH_PRIVATE_KEY, vapid_claims={"sub": settings.SUPPORT_WEB_PUSH_SUBJECT}, timeout=8, ttl=86400)
            NotificationDelivery.objects.filter(pk=delivery.pk).update(status="sent", error="", updated_at=timezone.now())
        return True
    except Exception as exc:
        status = getattr(getattr(exc, "response", None), "status_code", None)
        if status in {404, 410}:
            subscription.enabled = False
            subscription.save(update_fields=["enabled"])
        # Keep endpoints, tokens, keys and message contents out of the error log.
        error = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        NotificationDelivery.objects.filter(pk=delivery.pk).update(status="failed", error=error[:120], updated_at=timezone.now())
        return False
