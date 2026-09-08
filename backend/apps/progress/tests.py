from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.drugs.models import AtcCategory, AtcCode, Ingredient

from .models import DailyStudy, LearnerProgress, Mistake, StudyPlan
from .services import bump_mistake, record_study


def _chapter_with_drug():
    c = AtcCategory.objects.create(code="C", name_en="Cardio", name_fa="قلب", level=1)
    AtcCategory.objects.create(code="C07", name_en="Beta blockers",
                               name_fa="بتابلوکرها", level=2, parent=c)
    ing = Ingredient.objects.create(name="metoprolol", rxcui="6918", slug="metoprolol-6918")
    code, _ = AtcCode.objects.get_or_create(code="C07AB02", defaults={"name": "x"})
    ing.atc_codes.add(code)
    return ing


class ProgressServiceTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")

    def test_record_study_builds_daily_row_and_totals(self):
        record_study(self.user, minutes=15, reviews=3, xp=12)
        record_study(self.user, minutes=5, quizzes=1)

        progress = LearnerProgress.objects.get(user=self.user)
        self.assertEqual(progress.total_minutes, 20)
        self.assertEqual(progress.total_reviews, 3)
        self.assertEqual(progress.total_quizzes, 1)
        self.assertEqual(progress.xp, 12)
        self.assertEqual(DailyStudy.objects.get(user=self.user).minutes, 20)

    def test_streak_increments_only_on_consecutive_days(self):
        progress = record_study(self.user, minutes=5)
        self.assertEqual(progress.streak_days, 1)

        # same day again -> unchanged
        self.assertEqual(record_study(self.user, minutes=5).streak_days, 1)

        # simulate "yesterday was the last study day"
        LearnerProgress.objects.filter(pk=progress.pk).update(
            last_study_date=timezone.localdate() - timedelta(days=1)
        )
        self.assertEqual(record_study(self.user, minutes=5).streak_days, 2)

        # gap of two days -> reset to 1
        LearnerProgress.objects.filter(pk=progress.pk).update(
            last_study_date=timezone.localdate() - timedelta(days=3)
        )
        self.assertEqual(record_study(self.user, minutes=5).streak_days, 1)

    def test_bump_mistake_creates_then_increments_and_unresolves(self):
        m = bump_mistake(self.user, topic_key="side_effects", topic_fa="عوارض", topic_en="Side effects")
        self.assertEqual(m.count, 1)
        m.resolved = True
        m.save()

        again = bump_mistake(self.user, topic_key="side_effects", topic_fa="عوارض", topic_en="Side effects")
        self.assertEqual(again.count, 2)
        self.assertFalse(again.resolved)
        self.assertEqual(Mistake.objects.filter(user=self.user).count(), 1)


class MeApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="sara", email="s@e.com", password="x", first_name="Sara"
        )
        self.client.force_authenticate(self.user)
        self.ing = _chapter_with_drug()

    def test_dashboard_fresh_user(self):
        res = self.client.get("/api/v1/me/dashboard/")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["greeting_name"], "Sara")
        self.assertEqual(res.data["streak_days"], 0)
        self.assertEqual(res.data["next_chapter"]["code"], "C07")
        kinds = [r["kind"] for r in res.data["focus_session"]["rows"]]
        self.assertEqual(kinds, ["lesson"])  # no mistakes, no flashcards app

    def test_dashboard_includes_top_unresolved_mistake_row(self):
        bump_mistake(self.user, topic_key="dose", topic_fa="دوز", topic_en="Dosage")
        bump_mistake(self.user, topic_key="dose", topic_fa="دوز", topic_en="Dosage")  # count 2
        bump_mistake(self.user, topic_key="int", topic_fa="تداخل", topic_en="Interactions")  # count 1

        rows = self.client.get("/api/v1/me/dashboard/").data["focus_session"]["rows"]
        mistake_rows = [r for r in rows if r["kind"] == "mistake"]
        self.assertEqual(len(mistake_rows), 1)
        self.assertEqual(mistake_rows[0]["title_en"], "Questions on Dosage")

    def test_statistics_week_bars_reflect_daily_study(self):
        record_study(self.user, minutes=30)
        res = self.client.get("/api/v1/me/statistics/").data
        self.assertEqual(sum(res["week_bars"]), 30)
        self.assertEqual(len(res["week_bars"]), 7)
        self.assertEqual(res["minutes"], 30)

    def test_plan_get_then_put_validates_seven_days(self):
        self.assertEqual(self.client.get("/api/v1/me/plan/").data["days"], [False] * 7)

        ok = self.client.put(
            "/api/v1/me/plan/",
            {"days": [True, False, True, True, False, True, False], "reminders_enabled": True},
            format="json",
        )
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.data["reminders_enabled"])
        self.assertEqual(StudyPlan.objects.get(user=self.user).days[0], True)

        bad = self.client.put("/api/v1/me/plan/", {"days": [True, False]}, format="json")
        self.assertEqual(bad.status_code, 400)

    def test_mistake_list_resolve_and_restore(self):
        m = bump_mistake(self.user, topic_key="dose", topic_fa="دوز", topic_en="Dosage")

        self.assertEqual(len(self.client.get("/api/v1/me/mistakes/").data), 1)

        resolved = self.client.post(f"/api/v1/me/mistakes/{m.id}/resolve/")
        self.assertEqual(resolved.status_code, 200)
        self.assertTrue(resolved.data["resolved"])

        restored = self.client.post("/api/v1/me/mistakes/restore/")
        self.assertEqual(restored.status_code, 200)
        self.assertFalse(restored.data[0]["resolved"])

    def test_requires_authentication(self):
        self.assertEqual(APIClient().get("/api/v1/me/dashboard/").status_code, 401)
