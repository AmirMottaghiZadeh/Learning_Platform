from datetime import timedelta

from django.utils import timezone

from apps.website.models import DailyStat, StaffRole, VisitorDay

from .base import SiteTestCase
from .test_panel import SITE, PanelCase, make_user

User_AGENT = "Mozilla/5.0 (X11; Linux x86_64) Chrome/120"


def visit(client, ip, path="/", agent=User_AGENT):
    return client.get(path, HTTP_X_FORWARDED_FOR=ip, HTTP_USER_AGENT=agent, **SITE)


class UniqueVisitorTests(SiteTestCase):
    def test_same_ip_counts_once_however_many_pages(self):
        for path in ("/", "/blog/", "/plans/", "/"):
            visit(self.client, "203.0.113.5", path)
        self.assertEqual(DailyStat.objects.filter(kind=DailyStat.VIEW).count(), 3)
        self.assertEqual(sum(DailyStat.objects.filter(kind=DailyStat.VIEW).values_list("count", flat=True)), 4)
        self.assertEqual(VisitorDay.objects.count(), 1)

    def test_different_ips_count_separately(self):
        visit(self.client, "203.0.113.5")
        visit(self.client, "203.0.113.6")
        self.assertEqual(VisitorDay.objects.count(), 2)

    def test_address_is_not_stored(self):
        visit(self.client, "203.0.113.5")
        row = VisitorDay.objects.get()
        self.assertNotIn("203.0.113", row.ip_hash)
        self.assertEqual(len(row.ip_hash), 32)

    def test_bots_are_not_counted(self):
        visit(self.client, "203.0.113.5", agent="Googlebot/2.1")
        self.assertEqual(VisitorDay.objects.count(), 0)

    def test_same_ip_on_a_new_day_counts_again(self):
        visit(self.client, "203.0.113.5")
        VisitorDay.objects.update(day=timezone.localdate() - timedelta(days=1))
        from django.core.cache import cache

        cache.clear()
        visit(self.client, "203.0.113.5")
        self.assertEqual(VisitorDay.objects.count(), 2)

    def test_old_rows_are_dropped(self):
        VisitorDay.objects.create(day=timezone.localdate() - timedelta(days=500), ip_hash="a" * 32)
        visit(self.client, "203.0.113.5")
        self.assertFalse(VisitorDay.objects.filter(ip_hash="a" * 32).exists())


class UniqueVisitorPanelTests(PanelCase):
    def test_stats_counts_each_ip_once_across_days(self):
        today = timezone.localdate()
        VisitorDay.objects.create(day=today, ip_hash="a" * 32)
        VisitorDay.objects.create(day=today - timedelta(days=1), ip_hash="a" * 32)
        VisitorDay.objects.create(day=today - timedelta(days=2), ip_hash="b" * 32)
        self.login(make_user("a", StaffRole.ADMIN))
        res = self.get("stats", )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context["uniques"], 2)
        self.assertEqual([r["uniques"] for r in res.context["table"]][:3], [1, 1, 1])
        self.assertContains(res, "بازدیدکنندهٔ یکتا")

    def test_dashboard_shows_uniques_and_change(self):
        today = timezone.localdate()
        VisitorDay.objects.create(day=today, ip_hash="a" * 32)
        VisitorDay.objects.create(day=today, ip_hash="b" * 32)
        VisitorDay.objects.create(day=today - timedelta(days=40), ip_hash="c" * 32)
        self.login(make_user("a", StaffRole.ADMIN))
        res = self.get("dashboard")
        self.assertEqual(res.context["uniques_total"], 2)
        self.assertEqual(res.context["uniques_delta"], 100)
