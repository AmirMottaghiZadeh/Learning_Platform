from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.drugs.models import AtcCategory, AtcCode, Ingredient
from apps.progress.models import LearnerProgress, Mistake

from .generator import generate_questions
from .models import QuizSession


def _seed_atc_world():
    """Enough drugs across several ATC L2 groups to build a 5-question quiz."""
    classes = {
        "C07": "Beta blockers", "C03": "Diuretics", "C09": "ACE inhibitors",
        "C08": "Calcium channel blockers", "C10": "Statins",
    }
    for code, name in classes.items():
        AtcCategory.objects.get_or_create(
            code=code, defaults={"name_en": name, "name_fa": name, "level": 2}
        )
    for i, code in enumerate(list(classes) * 3):
        ing = Ingredient.objects.create(name=f"drug{i}", rxcui=str(1000 + i), slug=f"drug{i}-{1000+i}")
        atc, _ = AtcCode.objects.get_or_create(code=f"{code}AA{i:02d}", defaults={"name": "x"})
        ing.atc_codes.add(atc)


@override_settings(ROOT_URLCONF="apps.quiz.urls")
class QuizApiTests(TestCase):
    def setUp(self):
        _seed_atc_world()
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.client.force_authenticate(self.user)

    def _start(self, category="cardio", count=5):
        res = self.client.post("/quiz/start/", {"category": category, "count": count}, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        return res.data

    def test_start_returns_questions_without_the_answer_key(self):
        data = self._start()
        self.assertEqual(len(data["questions"]), 5)
        q = data["questions"][0]
        self.assertEqual(len(q["options_fa"]), 4)
        self.assertNotIn("correct_index", q)

    def test_answer_is_scored_server_side(self):
        data = self._start()
        session = QuizSession.objects.get(pk=data["id"])
        q0 = session.questions.first()

        res = self.client.post(
            f"/quiz/{session.id}/answer/",
            {"question_id": q0.id, "selected_index": q0.correct_index},
            format="json",
        )
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.data["correct"])
        self.assertEqual(res.data["correct_index"], q0.correct_index)

    def test_answering_twice_is_rejected(self):
        data = self._start()
        session = QuizSession.objects.get(pk=data["id"])
        q0 = session.questions.first()
        payload = {"question_id": q0.id, "selected_index": 0}
        self.client.post(f"/quiz/{session.id}/answer/", payload, format="json")
        again = self.client.post(f"/quiz/{session.id}/answer/", payload, format="json")
        self.assertEqual(again.status_code, 409)

    def test_finish_scores_awards_xp_and_records_mistakes(self):
        data = self._start()
        session = QuizSession.objects.get(pk=data["id"])
        questions = list(session.questions.all())
        # answer the first correctly, the rest wrong
        self.client.post(
            f"/quiz/{session.id}/answer/",
            {"question_id": questions[0].id, "selected_index": questions[0].correct_index},
            format="json",
        )
        for q in questions[1:]:
            wrong = (q.correct_index + 1) % 4
            self.client.post(
                f"/quiz/{session.id}/answer/",
                {"question_id": q.id, "selected_index": wrong},
                format="json",
            )

        result = self.client.post(f"/quiz/{session.id}/finish/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["score"], 1)
        self.assertEqual(result.data["total"], 5)
        self.assertEqual(result.data["mistakes_added"], 4)

        progress = LearnerProgress.objects.get(user=self.user)
        self.assertEqual(progress.total_quizzes, 1)
        self.assertEqual(progress.quiz_correct, 1)
        self.assertGreater(progress.xp, 0)
        self.assertTrue(Mistake.objects.filter(user=self.user, topic_key="drug_class").exists())

    def test_answer_after_finish_is_rejected(self):
        data = self._start()
        session = QuizSession.objects.get(pk=data["id"])
        self.client.post(f"/quiz/{session.id}/finish/")
        q0 = session.questions.first()
        res = self.client.post(
            f"/quiz/{session.id}/answer/",
            {"question_id": q0.id, "selected_index": 0},
            format="json",
        )
        self.assertEqual(res.status_code, 409)

    def test_generator_makes_four_option_questions(self):
        questions = generate_questions("cardio", 5)
        self.assertEqual(len(questions), 5)
        for q in questions:
            self.assertEqual(len(q["options_en"]), 4)
            self.assertIn(q["correct_index"], range(4))


@override_settings(ROOT_URLCONF="apps.core.quiz_maintenance_urls")
class QuizLockedTests(TestCase):
    def test_locked_start_answers_503(self):
        self.assertEqual(APIClient().post("/quiz/start/").status_code, 503)
