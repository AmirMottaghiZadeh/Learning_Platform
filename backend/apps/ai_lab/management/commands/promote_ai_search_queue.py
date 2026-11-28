"""Drain the waiting smart-search queue without a Celery beat scheduler."""
from django.core.management.base import BaseCommand

from apps.ai_lab.models import SearchRun
from apps.ai_lab.runner import promote


class Command(BaseCommand):
    help = "Promote waiting smart searches onto free slots. Safe to run from cron every few seconds."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Keep promoting until interrupted.")
        parser.add_argument("--interval", type=float, default=5.0, help="Seconds between rounds with --loop.")

    def handle(self, *args, **options):
        if not options["loop"]:
            waiting = SearchRun.objects.filter(status="queued", slot="").count()
            promoted = promote()
            self.stdout.write(f"waiting={waiting} promoted={promoted}")
            return
        import time

        try:
            while True:
                promote()
                time.sleep(max(1.0, options["interval"]))
        except KeyboardInterrupt:
            pass
