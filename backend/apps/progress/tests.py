from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.drugs.models import AtcCategory, AtcCode, Ingredient
from apps.flashcards.models import LeitnerCard
from apps.lessons.selectors import mark_drug_read
from apps.quiz.models import QuizAnswer, QuizQuestion, QuizSession

from . import planning
from .models import DailyStudy, LearnerProgress, Mistake, StudyPlan, StudyPlanItem
from .services import bump_mistake, get_plan, record_study


def _chapter_with_drug():
    c = AtcCategory.objects.create(code="C", name_en="Cardio", name_fa="قلب", level=1)
    AtcCategory.objects.create(code="C07", name_en="Beta blockers",
                               name_fa="بتابلوکرها", level=2, parent=c)
    ing = Ingredient.objects.create(name="metoprolol", rxcui="6918", slug="metoprolol-6918")
    code, _ = AtcCode.objects.get_or_create(code="C07AB02", defaults={"name": "x"})
    ing.atc_codes.add(code)
    return ing


def _two_chapter_topic():
    """C07 (beta blockers) and C03 (diuretics), both under the 'cv-htn'
    study topic -- for plan-generation tests that need more than one chapter."""
    l1 = AtcCategory.objects.create(code="C", name_en="Cardio", name_fa="قلب", level=1)
    AtcCategory.objects.create(code="C07", name_en="Beta blockers",
                               name_fa="بتابلوکرها", level=2, parent=l1)
    AtcCategory.objects.create(code="C03", name_en="Diuretics",
                               name_fa="دیورتیک‌ها", level=2, parent=l1)
    beta = Ingredient.objects.create(name="metoprolol", rxcui="6918", slug="metoprolol-6918")
    beta_code, _ = AtcCode.objects.get_or_create(code="C07AB02", defaults={"name": "x"})
    beta.atc_codes.add(beta_code)
    diuretic = Ingredient.objects.create(name="hydrochlorothiazide", rxcui="5487", slug="hctz-5487")
    diuretic_code, _ = AtcCode.objects.get_or_create(code="C03AA03", defaults={"name": "y"})
    diuretic.atc_codes.add(diuretic_code)
    return beta, diuretic


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
        self.assertEqual(self.client.get("/api/v1/me/plan/").data["mode"], "none")

        ok = self.client.put(
            "/api/v1/me/plan/",
            {
                "mode": "none",
                "days": [True, False, True, True, False, True, False],
                "reminders_enabled": True,
                "daily_minutes": 30,
            },
            format="json",
        )
        self.assertEqual(ok.status_code, 200)
        self.assertTrue(ok.data["reminders_enabled"])
        self.assertTrue(ok.data["fits_deadline"])
        self.assertEqual(StudyPlan.objects.get(user=self.user).days[0], True)

        bad = self.client.put(
            "/api/v1/me/plan/", {"mode": "none", "days": [True, False]}, format="json"
        )
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


class TopicMasteryTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.beta, self.diuretic = _two_chapter_topic()

    def test_mastery_is_pure_completion_before_any_quiz_or_flashcards(self):
        self.assertEqual(planning.topic_mastery(self.user, "cv-htn"), 0)
        mark_drug_read(self.user, self.beta.slug)
        mark_drug_read(self.user, self.diuretic.slug)
        self.assertEqual(planning.topic_mastery(self.user, "cv-htn"), 100)

    def test_mastery_blends_in_quiz_accuracy_once_quizzed(self):
        mark_drug_read(self.user, self.beta.slug)  # 1/2 chapters -> 50% completion
        session = QuizSession.objects.create(user=self.user, category="cardio", question_count=2)
        for order, is_correct in enumerate((True, True), start=1):
            q = QuizQuestion.objects.create(
                session=session, order=order, prompt_fa="p", prompt_en="p",
                correct_index=0, subject_slug=self.beta.slug,
            )
            QuizAnswer.objects.create(question=q, selected_index=0, is_correct=is_correct)

        mastery = planning.topic_mastery(self.user, "cv-htn")
        # completion=50 (w=.3) + quiz=100 (w=.4), recall absent -> renormalised over .7
        self.assertEqual(mastery, round((50 * 0.3 + 100 * 0.4) / 0.7))

    def test_mastery_blends_in_flashcard_recall(self):
        LeitnerCard.objects.create(user=self.user, ingredient=self.beta, box=5)
        mastery = planning.topic_mastery(self.user, "cv-htn")
        # completion=0 (w=.3) + recall=100 (max box, w=.3) -> renormalised over .6
        self.assertEqual(mastery, round((0 * 0.3 + 100 * 0.3) / 0.6))


class GoalPlanGenerationTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.beta, self.diuretic = _two_chapter_topic()
        self.today = timezone.localdate()

    def _plan(self, **overrides):
        plan = get_plan(self.user)
        plan.mode = StudyPlan.MODE_GOAL
        plan.topic_keys = ["cv-htn"]
        plan.daily_minutes = overrides.pop("daily_minutes", 60)
        plan.deadline = overrides.pop("deadline", self.today + timedelta(days=7))
        plan.days = overrides.pop("days", [True] * 7)
        plan.save()
        return plan

    def test_unread_chapters_scheduled_before_quiz_and_flashcards(self):
        plan = self._plan()
        fits = planning.regenerate_items(self.user, plan)
        self.assertTrue(fits)

        items = list(StudyPlanItem.objects.filter(plan=plan).order_by("day", "order"))
        types = [i.activity_type for i in items]
        # 2 unread chapters, then one quiz + one flashcard pass for the topic
        self.assertEqual(types.count(StudyPlanItem.LESSON), 2)
        self.assertEqual(types.count(StudyPlanItem.QUIZ), 1)
        self.assertEqual(types.count(StudyPlanItem.FLASHCARDS), 1)
        self.assertEqual(items[0].activity_type, StudyPlanItem.LESSON)
        self.assertTrue(all(i.topic_key == "cv-htn" for i in items))

    def test_already_read_chapter_is_not_rescheduled(self):
        mark_drug_read(self.user, self.beta.slug)
        plan = self._plan()
        planning.regenerate_items(self.user, plan)

        lesson_codes = [
            i.atc_code for i in StudyPlanItem.objects.filter(plan=plan, activity_type=StudyPlanItem.LESSON)
        ]
        self.assertEqual(lesson_codes, ["C03"])

    def test_tight_deadline_reports_it_does_not_fit(self):
        plan = self._plan(daily_minutes=5, deadline=self.today)
        fits = planning.regenerate_items(self.user, plan)
        self.assertFalse(fits)
        # still schedules everything it can, today, rather than nothing
        self.assertTrue(StudyPlanItem.objects.filter(plan=plan, day=self.today).exists())

    def test_lesson_item_auto_completes_when_chapter_is_read_outside_the_planner(self):
        plan = self._plan()
        planning.regenerate_items(self.user, plan)
        lesson_item = StudyPlanItem.objects.get(plan=plan, atc_code="C07")
        self.assertEqual(lesson_item.status, StudyPlanItem.PENDING)

        # The learner reads the chapter's drug directly, not via the planner.
        mark_drug_read(self.user, self.beta.slug)

        synced = planning.today_items(self.user, plan)
        today_item = next(i for i in synced if i.id == lesson_item.id)
        self.assertEqual(today_item.status, StudyPlanItem.DONE)
        self.assertIsNotNone(today_item.completed_at)

    def test_replanning_keeps_completed_items_but_clears_pending_ones(self):
        plan = self._plan()
        planning.regenerate_items(self.user, plan)
        first = StudyPlanItem.objects.filter(plan=plan).order_by("day", "order").first()
        planning.complete_item(self.user, first.id)

        mark_drug_read(self.user, self.beta.slug)
        mark_drug_read(self.user, self.diuretic.slug)  # topic now fully read
        planning.regenerate_items(self.user, plan)

        self.assertTrue(StudyPlanItem.objects.filter(id=first.id, status=StudyPlanItem.DONE).exists())
        # nothing left to read -> only quiz + flashcards regenerated
        remaining = StudyPlanItem.objects.filter(plan=plan, status=StudyPlanItem.PENDING)
        self.assertEqual(remaining.filter(activity_type=StudyPlanItem.LESSON).count(), 0)


class MaintenancePlanAndApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            username="u", email="u@e.com", password="x"
        )
        self.client.force_authenticate(self.user)
        self.beta, self.diuretic = _two_chapter_topic()
        mark_drug_read(self.user, self.beta.slug)
        mark_drug_read(self.user, self.diuretic.slug)

    def _goal_plan_payload(self, **extra):
        base = {
            "mode": "goal",
            "topic_keys": ["cv-htn"],
            "daily_minutes": 60,
            "deadline": str(timezone.localdate() + timedelta(days=7)),
            "days": [True] * 7,
            "reminders_enabled": False,
        }
        base.update(extra)
        return base

    def test_put_rejects_goal_mode_without_topics_or_deadline(self):
        res = self.client.put(
            "/api/v1/me/plan/",
            self._goal_plan_payload(topic_keys=[], deadline=None),
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_put_rejects_unknown_topic_key(self):
        res = self.client.put(
            "/api/v1/me/plan/", self._goal_plan_payload(topic_keys=["not-a-real-topic"]), format="json"
        )
        self.assertEqual(res.status_code, 400)

    def test_put_goal_plan_then_today_lists_generated_items(self):
        put_res = self.client.put("/api/v1/me/plan/", self._goal_plan_payload(), format="json")
        self.assertEqual(put_res.status_code, 200)

        today = self.client.get("/api/v1/me/plan/today/").data
        self.assertEqual(today["mode"], "goal")
        kinds = {i["activity_type"] for i in today["items"]}
        self.assertEqual(kinds, {"quiz", "flashcards"})  # both chapters already read
        self.assertEqual(today["topics"][0]["key"], "cv-htn")
        self.assertEqual(today["topics"][0]["progress_pct"], 100)

    def test_maintenance_mode_surfaces_due_flashcards_and_open_mistakes(self):
        LeitnerCard.objects.create(
            user=self.user, ingredient=self.beta, due_at=timezone.now() - timedelta(hours=1)
        )
        bump_mistake(self.user, topic_key="drug_class", topic_fa="دسته", topic_en="Class")
        self.client.put(
            "/api/v1/me/plan/",
            {
                "mode": "maintenance", "topic_keys": [], "daily_minutes": 30,
                "days": [True] * 7, "reminders_enabled": False,
            },
            format="json",
        )

        kinds = {i["activity_type"] for i in self.client.get("/api/v1/me/plan/today/").data["items"]}
        self.assertIn("flashcards", kinds)
        self.assertIn("mistake_review", kinds)

    def test_complete_and_skip_item(self):
        self.client.put("/api/v1/me/plan/", self._goal_plan_payload(), format="json")
        item_id = self.client.get("/api/v1/me/plan/today/").data["items"][0]["id"]

        done = self.client.post(f"/api/v1/me/plan/items/{item_id}/complete/")
        self.assertEqual(done.status_code, 200)
        self.assertEqual(done.data["status"], "done")

        # completing an already-done item is a no-op, not an error
        again = self.client.post(f"/api/v1/me/plan/items/{item_id}/complete/")
        self.assertEqual(again.status_code, 200)

    def test_item_from_another_user_is_not_reachable(self):
        other = get_user_model().objects.create_user(username="other", email="o@e.com", password="x")
        other_plan = get_plan(other)
        other_plan.mode = StudyPlan.MODE_MAINTENANCE
        other_plan.save()
        item = StudyPlanItem.objects.create(
            plan=other_plan, day=timezone.localdate(), activity_type=StudyPlanItem.MISTAKE_REVIEW
        )
        res = self.client.post(f"/api/v1/me/plan/items/{item.id}/complete/")
        self.assertEqual(res.status_code, 404)
