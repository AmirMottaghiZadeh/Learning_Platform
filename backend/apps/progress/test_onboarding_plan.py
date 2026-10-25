from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import LearnerProfile
from apps.lessons.data.study_topics import STUDY_TOPICS
from apps.lessons.selectors import mark_drug_read
from apps.quiz.models import QuizSession

from . import planning
from .models import StudyPlan, StudyPlanItem
from .services import get_plan
from .tests import _two_chapter_topic

WEEKDAYS = [True, True, True, True, True, False, False]  # Saturday to Wednesday


def _onboarding(goal, **plan):
    body = {"study_field": "pharmacy", "study_goal": goal, "study_level": "intermediate"}
    body.update(plan)
    return body


class OnboardingPlanTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.client.force_authenticate(self.user)
        self.today = timezone.localdate()
        _two_chapter_topic()

    def post(self, body):
        return self.client.post("/api/v1/auth/onboarding/", body, format="json")

    def test_end_of_course_exam_plans_every_topic_up_to_the_exam(self):
        exam = self.today + timedelta(days=40)
        res = self.post(_onboarding("comprehensive", exam_date=str(exam), daily_minutes=30, study_days=[True] * 7))
        self.assertEqual(res.status_code, 200, res.content)
        plan = get_plan(self.user)
        self.assertEqual(plan.mode, StudyPlan.MODE_GOAL)
        self.assertEqual(plan.deadline, exam)
        self.assertEqual(len(plan.topic_keys), len(STUDY_TOPICS))
        self.assertEqual(plan.started_on, self.today)
        self.assertTrue(plan.items.filter(topic_key="cv-htn", activity_type=StudyPlanItem.LESSON).exists())

    def test_term_finals_plan_only_the_chosen_categories(self):
        exam = str(self.today + timedelta(days=20))
        res = self.post(_onboarding(
            "final", exam_date=exam, daily_minutes=45, study_days=WEEKDAYS, category_keys=["cardio-blood"],
        ))
        self.assertEqual(res.status_code, 200, res.content)
        plan = get_plan(self.user)
        expected = [t["key"] for t in STUDY_TOPICS if t["category"] == "cardio-blood"]
        self.assertEqual(plan.topic_keys, expected)
        self.assertEqual(plan.days, WEEKDAYS)
        self.assertEqual(plan.daily_minutes, 45)

        missing = self.post(_onboarding("final", exam_date=exam, daily_minutes=45, study_days=WEEKDAYS))
        self.assertEqual(missing.status_code, 400)

    def test_daily_clinical_review_is_an_open_ended_maintenance_plan(self):
        res = self.post(_onboarding("clinical", daily_minutes=10, study_days=[True] * 7))
        self.assertEqual(res.status_code, 200, res.content)
        plan = get_plan(self.user)
        self.assertEqual((plan.mode, plan.deadline, plan.daily_minutes), (StudyPlan.MODE_MAINTENANCE, None, 10))

    def test_exam_date_must_be_ahead_and_a_study_day_chosen(self):
        past = self.post(_onboarding("comprehensive", exam_date=str(self.today), daily_minutes=30, study_days=[True] * 7))
        self.assertIn("exam_date", past.json()["details"])
        no_days = self.post(_onboarding(
            "comprehensive", exam_date=str(self.today + timedelta(days=9)), daily_minutes=30, study_days=[False] * 7,
        ))
        self.assertIn("study_days", no_days.json()["details"])

    def test_answers_alone_still_save_without_a_plan(self):
        res = self.post(_onboarding("comprehensive"))
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(get_plan(self.user).mode, StudyPlan.MODE_NONE)


class PlanPaceRolloverAndWeekTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.beta, self.diuretic = _two_chapter_topic()
        self.today = timezone.localdate()

    def _plan(self, level="intermediate", minutes=60):
        LearnerProfile.objects.update_or_create(user=self.user, defaults={"study_level": level})
        self.user.refresh_from_db()
        plan = get_plan(self.user)
        plan.mode = StudyPlan.MODE_GOAL
        plan.topic_keys = ["cv-htn"]
        plan.daily_minutes = minutes
        plan.deadline = self.today + timedelta(days=14)
        plan.days = [True] * 7
        plan.started_on = self.today
        plan.save()
        planning.regenerate_items(self.user, plan)
        return plan

    def test_level_sets_the_minutes_a_chapter_is_planned_at(self):
        lessons = lambda plan: set(plan.items.filter(activity_type=StudyPlanItem.LESSON).values_list("estimated_minutes", flat=True))
        self.assertEqual(lessons(self._plan("beginner")), {14})
        self.assertEqual(lessons(self._plan("advanced")), {7})

    def test_a_missed_day_moves_its_work_onto_the_coming_days_once(self):
        plan = self._plan(minutes=20)
        yesterday = self.today - timedelta(days=1)
        plan.items.update(day=yesterday)  # nothing of "yesterday" was done
        items = planning.today_items(self.user, plan)

        self.assertTrue(items, "the missed work is laid out from today")
        self.assertTrue(plan.items.filter(day=yesterday, status=StudyPlanItem.PENDING).exists())
        plan.refresh_from_db()
        self.assertEqual(plan.rolled_over_on, self.today)
        count = plan.items.count()
        planning.today_items(self.user, plan)
        self.assertEqual(plan.items.count(), count, "a second look the same day does not lay it out again")

        week = {d["date"]: d["state"] for d in planning.week_overview(self.user, plan)}
        if yesterday in week:  # unless today is Saturday, yesterday is in this week
            plan.started_on = yesterday - timedelta(days=1)
            plan.save()
            week = {d["date"]: d["state"] for d in planning.week_overview(self.user, plan)}
            self.assertEqual(week[yesterday], "missed")
        self.assertEqual(week[self.today], "today")

    def test_a_finished_quiz_completes_its_task_and_is_not_planned_again(self):
        plan = self._plan(minutes=240)
        quiz = plan.items.get(activity_type=StudyPlanItem.QUIZ)
        QuizSession.objects.create(user=self.user, category="cv-htn", question_count=10, finished_at=timezone.now())
        items = planning.today_items(self.user, plan)
        self.assertEqual(next(i for i in items if i.id == quiz.id).status, StudyPlanItem.DONE)

        planning.regenerate_items(self.user, plan)
        self.assertEqual(plan.items.filter(activity_type=StudyPlanItem.QUIZ).count(), 1)

    def test_tasks_carry_their_titles(self):
        plan = self._plan(minutes=240)
        titles = {i.activity_type: i.title_fa for i in planning.today_items(self.user, plan)}
        self.assertTrue(titles[StudyPlanItem.LESSON].startswith("درسنامه: "))
        self.assertTrue(titles[StudyPlanItem.QUIZ].startswith("آزمون: "))

    def test_summary_counts_days_weeks_and_progress(self):
        plan = self._plan(minutes=240)
        first = plan.items.order_by("day", "order").first()
        planning.complete_item(self.user, first.id)
        summary = planning.plan_summary(plan)
        self.assertEqual(summary["days_left"], 14)
        self.assertEqual((summary["week_index"], summary["week_count"]), (1, 3))
        total = plan.items.count()
        self.assertEqual(summary["progress_pct"], round(100 / total))

    def test_a_day_with_every_task_finished_is_done(self):
        plan = self._plan(minutes=240)
        mark_drug_read(self.user, self.beta.slug)
        mark_drug_read(self.user, self.diuretic.slug)
        for item in plan.items.filter(day=self.today):
            planning.complete_item(self.user, item.id)
        week = {d["date"]: d["state"] for d in planning.week_overview(self.user, plan)}
        self.assertEqual(week[self.today], "done")


class PlanTodayApiTests(TestCase):
    def test_brief_answer_has_summary_and_week_but_no_topics(self):
        user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        client = APIClient()
        client.force_authenticate(user)
        _two_chapter_topic()
        plan = get_plan(user)
        plan.mode, plan.topic_keys, plan.days = StudyPlan.MODE_GOAL, ["cv-htn"], [True] * 7
        plan.deadline, plan.started_on = timezone.localdate() + timedelta(days=7), timezone.localdate()
        plan.save()
        planning.regenerate_items(user, plan)

        body = client.get("/api/v1/me/plan/today/", {"brief": "1"}).json()
        self.assertEqual(body["topics"], [])
        self.assertEqual(len(body["week"]), 7)
        self.assertEqual(body["summary"]["days_left"], 7)
        self.assertTrue(all(item["title_fa"] for item in body["items"]))
        self.assertEqual(len(client.get("/api/v1/me/plan/today/").json()["topics"]), 1)
