from django.core.cache import cache
from django.test import TestCase


class SiteTestCase(TestCase):
    """Clears the cache around each test: SiteSettings is cached, and a
    database rollback does not undo that."""

    def setUp(self):
        super().setUp()
        cache.clear()
        self.addCleanup(cache.clear)
