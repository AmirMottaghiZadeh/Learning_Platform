from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.core.queue import enqueue
from apps.support.models import NotificationDelivery
from apps.support.tasks import deliver_message_notifications


class Command(BaseCommand):
    help = "Retry pending/failed support notifications; no message text or tokens are printed."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        # Recover worker crashes after claiming a delivery, but never steal an
        # in-flight request (the provider timeout is eight seconds).
        NotificationDelivery.objects.filter(status="sending", updated_at__lt=timezone.now() - timedelta(minutes=5)).update(status="failed")
        ids = list(NotificationDelivery.objects.filter(status__in=["pending", "failed"], attempts__lt=3).order_by("message_id").values_list("message_id", flat=True).distinct()[:max(1, min(1000, options["limit"]))])
        for pk in ids:
            enqueue(deliver_message_notifications, pk)
        self.stdout.write(f"Queued {len(ids)} message(s) for notification delivery.")
