import logging

from django.db import transaction
from django.db.models import Count, Q, F
from django.utils import timezone

from apps.accounts.services import active_role_keys

from .models import Conversation, Message, NotificationDelivery, PushSubscription

logger = logging.getLogger(__name__)


def can_support(user):
    if not (user.is_authenticated and user.is_active):
        return False
    from apps.website.permissions import role_of
    from apps.website.models import StaffRole

    return bool(user.is_superuser or role_of(user) in {StaffRole.SUPPORT, StaffRole.ADMIN} or set(active_role_keys(user)) & {"support_agent", "platform_admin"})


def conversations_for(user):
    return Conversation.objects.filter(user=user).annotate(unread=Count("messages", filter=Q(messages__from_staff=True, messages__id__gt=F("user_read_id"))))


@transaction.atomic
def send_message(conversation, sender, text, client_id, *, staff=False):
    conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    if (staff and not can_support(sender)) or (not staff and conversation.user_id != sender.pk):
        raise PermissionError("This conversation belongs to another account.")
    message, created = Message.objects.get_or_create(
        conversation=conversation, sender=sender, client_id=client_id,
        defaults={"text": text.strip(), "from_staff": staff},
    )
    if created:
        conversation.updated_at = timezone.now()
        conversation.status = "open"
        conversation.save(update_fields=["updated_at", "status"])
        if staff:
            subscriptions = PushSubscription.objects.filter(user=conversation.user, enabled=True, session__revoked_at__isnull=True, session__refresh_expires_at__gt=timezone.now())
            NotificationDelivery.objects.bulk_create([NotificationDelivery(message=message, subscription=sub) for sub in subscriptions], ignore_conflicts=True)
            transaction.on_commit(lambda: _queue_notification(message.pk))
    return message, created


def _queue_notification(message_id):
    from apps.core.queue import enqueue
    from .tasks import deliver_message_notifications

    try:
        enqueue(deliver_message_notifications, message_id)
    except Exception:
        # A provider outage must not turn a saved reply into an apparent send
        # failure. The retry command scans messages with pending deliveries.
        logger.exception("Could not queue support notification for message %s", message_id)


@transaction.atomic
def mark_read(conversation, through, *, staff=False):
    conversation = Conversation.objects.select_for_update().get(pk=conversation.pk)
    # Only acknowledge a message the client actually received, never messages
    # arriving between the fetch and this acknowledgement.
    value = Message.objects.filter(conversation=conversation, pk__lte=through).order_by("-pk").values_list("pk", flat=True).first() or 0
    field = "staff_read_id" if staff else "user_read_id"
    if value > getattr(conversation, field):
        setattr(conversation, field, value)
        conversation.save(update_fields=[field])
