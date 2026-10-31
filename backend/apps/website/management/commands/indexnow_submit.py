"""Submit the site's pages to IndexNow (Bing, Yandex, ...).

    manage.py indexnow_submit            # every page in the sitemap
    manage.py indexnow_submit --days 3   # pages changed in the last 3 days

Run once with no options after setting INDEXNOW_KEY; the container's start
script runs it with --days on each deploy, which covers drug pages refreshed
by a data import. Saving a post, page or announcement submits it by itself.
"""

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.website import indexnow
from apps.website.views_public import sitemap_entries


class Command(BaseCommand):
    help = "Submit the site's pages to IndexNow."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, help="Only pages whose last change is within this many days.")

    def handle(self, *args, days=None, **options):
        if not settings.INDEXNOW_KEY:
            self.stdout.write("indexnow_submit: INDEXNOW_KEY is not set; nothing to do.")
            return
        if not indexnow.enabled():
            self.stdout.write("indexnow_submit: the site is set to noindex; nothing submitted.")
            return
        entries = sitemap_entries()
        if days is not None:
            since = timezone.now() - timedelta(days=days)
            entries = [e for e in entries if e[1] and e[1] >= since]
        paths = [path for path, _modified, _priority in entries]
        accepted = indexnow.submit(paths)
        self.stdout.write(f"indexnow_submit: {accepted} of {len(paths)} URLs accepted.")
