from celery import shared_task
from .models import NotificationDelivery
from .notifications import send_delivery


@shared_task(bind=True, max_retries=2, name="support.deliver_message_notifications")
def deliver_message_notifications(self, message_id):
    failed = False
    ids = list(NotificationDelivery.objects.filter(message_id=message_id, status__in=["pending", "failed"], attempts__lt=3).values_list("pk", flat=True))
    for pk in ids:
        if not send_delivery(pk):
            failed = True
    if failed:
        raise self.retry(countdown=30 * (self.request.retries + 1))
    return not failed
