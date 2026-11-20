from django.core.management.base import BaseCommand, CommandError

from apps.billing import config
from apps.billing.guest import delete_guests


class Command(BaseCommand):
    help = "Delete every guest account (and its progress). Refused while guest access is on."

    def handle(self, *args, **options):
        if config.current().guest_access:
            raise CommandError("Guest access is on; switch it off in /ops/access/ first.")
        self.stdout.write(f"Deleted {delete_guests()} guest accounts.")
