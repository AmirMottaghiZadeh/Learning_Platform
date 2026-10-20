from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.billing import config as billing_config
from apps.billing.models import PlanFeature, UsageRecord
from apps.drugs.models import AtcCategory, AtcCode, Ingredient, IngredientProfileSection
from apps.progress.models import LearnerProgress, Mistake

from .bank_selectors import sample_bank_questions
from .models import BankQuestion, QuizSession


def _seed_atc_world():
    """Enough drugs across several ATC L2 groups, each with its own questions,
    to build a 5-question bank-backed quiz for one class."""
    classes = {
        "C07": "Beta blockers", "C03": "Diuretics", "C09": "ACE inhibitors",
        "C08": "Calcium channel blockers", "C10": "Statins",
    }
    for code, name in classes.items():
        AtcCategory.objects.get_or_create(
            code=code, defaults={"name_en": name, "name_fa": name, "level": 2}
        )
    bank = []
    for i, code in enumerate(list(classes) * 3):
        ing = Ingredient.objects.create(name=f"drug{i}", rxcui=str(1000 + i), slug=f"drug{i}-{1000+i}")
        atc, _ = AtcCode.objects.get_or_create(code=f"{code}AA{i:02d}", defaults={"name": "x"})
        ing.atc_codes.add(atc)
        for j in range(2):
            options = [f"کاربرد شمارهٔ {i}-{j}-{k}" for k in range(4)]
            bank.append(BankQuestion(
                ingredient=ing, field="indication", prompt_fa=f"کدام مورد از موارد مصرف «drug{i}» است؟ ({j})",
                options_fa=options, correct_index=(i + j) % 4,
            ))
    BankQuestion.objects.bulk_create(bank)


@override_settings(ROOT_URLCONF="apps.quiz.urls")
class QuizApiTests(TestCase):
    def setUp(self):
        _seed_atc_world()
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.client.force_authenticate(self.user)

    def _start(self, category="cardio", atc_code="C07", count=5):
        res = self.client.post(
            "/quiz/start/",
            {"category": category, "atc_code": atc_code, "count": count},
            format="json",
        )
        self.assertEqual(res.status_code, 201, res.data)
        return res.data

    def test_start_returns_questions_without_the_answer_key(self):
        data = self._start()
        self.assertEqual(len(data["questions"]), 5)
        q = data["questions"][0]
        self.assertEqual(len(q["options_fa"]), 4)
        self.assertNotIn("correct_index", q)

    def test_start_preserves_long_bank_prompts_in_both_languages(self):
        prompt_fa = "شرح بالینی طولانی سؤال آزمون. " * 30
        prompt_en = "A long clinical scenario for the quiz question. " * 30
        BankQuestion.objects.update(prompt_fa=prompt_fa, prompt_en=prompt_en)

        data = self._start()

        for question in data["questions"]:
            self.assertEqual(question["prompt_fa"], prompt_fa)
            self.assertEqual(question["prompt_en"], prompt_en)

    def test_drug_quiz_preserves_long_persian_prompt_as_english_fallback(self):
        prompt = "شرح بالینی طولانی سؤال آزمون. " * 30
        BankQuestion.objects.filter(ingredient__slug="drug0-1000").update(
            prompt_fa=prompt, prompt_en=""
        )

        response = self.client.post(
            "/quiz/start/", {"ingredient_slug": "drug0-1000"}, format="json"
        )

        self.assertEqual(response.status_code, 201, response.data)
        for question in response.data["questions"]:
            self.assertEqual(question["prompt_fa"], prompt)
            self.assertEqual(question["prompt_en"], prompt)

    def test_review_mistakes_preserves_long_prompts(self):
        prompt_fa = "شرح بالینی طولانی سؤال آزمون. " * 30
        prompt_en = "A long clinical scenario for the quiz question. " * 30
        BankQuestion.objects.update(prompt_fa=prompt_fa, prompt_en=prompt_en)
        data = self._start()
        session = QuizSession.objects.get(pk=data["id"])
        question = session.questions.first()
        answer = self.client.post(
            f"/quiz/{session.id}/answer/",
            {"question_id": question.id, "selected_index": (question.correct_index + 1) % 4},
            format="json",
        )
        self.assertEqual(answer.status_code, 200, answer.data)
        finish = self.client.post(f"/quiz/{session.id}/finish/")
        self.assertEqual(finish.status_code, 200, finish.data)

        response = self.client.post(f"/quiz/{session.id}/review-mistakes/")

        self.assertEqual(response.status_code, 201, response.data)
        self.assertEqual(len(response.data["questions"]), 1)
        self.assertEqual(response.data["questions"][0]["prompt_fa"], prompt_fa)
        self.assertEqual(response.data["questions"][0]["prompt_en"], prompt_en)

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

    def test_bank_sampling_makes_four_option_questions(self):
        questions = sample_bank_questions("", "C07", 5)
        self.assertEqual(len(questions), 5)
        for q in questions:
            self.assertEqual(len(q.options_fa), 4)
            self.assertIn(q.correct_index, range(4))

    def test_unknown_topic_without_atc_code_is_rejected(self):
        res = self.client.post(
            "/quiz/start/",
            {"category": "not-a-real-topic", "count": 5},
            format="json",
        )
        self.assertEqual(res.status_code, 400)

    def test_questions_carry_their_source_field(self):
        data = self._start()
        for q in data["questions"]:
            self.assertEqual(q["field"], "indication")
            self.assertEqual(q["field_label_fa"], "اندیکاسیون")
            self.assertEqual(q["field_tone"], "info")
            self.assertTrue(q["subject_slug"])

    def test_answer_returns_extra_context_from_sibling_facts(self):
        data = self._start()
        session = QuizSession.objects.get(pk=data["id"])
        q0 = session.questions.first()
        res = self.client.post(
            f"/quiz/{session.id}/answer/",
            {"question_id": q0.id, "selected_index": q0.correct_index},
            format="json",
        )
        # each drug gets 2 indication questions, so the other one is the
        # sibling fact
        self.assertGreater(len(res.data["extra_context"]), 0)
        for text in res.data["extra_context"]:
            self.assertNotEqual(text, q0.options_fa[q0.correct_index])

    def test_finish_reports_field_breakdown_and_previous_best(self):
        data = self._start(count=5)
        session = QuizSession.objects.get(pk=data["id"])
        questions = list(session.questions.all())
        for q in questions:
            self.client.post(
                f"/quiz/{session.id}/answer/",
                {"question_id": q.id, "selected_index": q.correct_index},
                format="json",
            )
        result = self.client.post(f"/quiz/{session.id}/finish/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["by_field"], [{
            "field": "indication",
            "label_fa": "اندیکاسیون",
            "tone": "info",
            "correct": 5,
            "total": 5,
        }])
        self.assertEqual(result.data["missed"], [])
        self.assertIsNone(result.data["previous_best_pct"])  # first attempt at this topic

        # a second, worse attempt at the same topic should see the first's
        # score as its "previous best"
        data2 = self._start(count=5)
        session2 = QuizSession.objects.get(pk=data2["id"])
        for q in session2.questions.all():
            wrong = (q.correct_index + 1) % 4
            self.client.post(
                f"/quiz/{session2.id}/answer/",
                {"question_id": q.id, "selected_index": wrong},
                format="json",
            )
        result2 = self.client.post(f"/quiz/{session2.id}/finish/")
        self.assertEqual(result2.data["previous_best_pct"], 100)
        self.assertEqual(len(result2.data["missed"]), 5)

    def test_review_mistakes_builds_a_session_of_just_the_missed_ones(self):
        data = self._start(count=5)
        session = QuizSession.objects.get(pk=data["id"])
        questions = list(session.questions.all())
        for i, q in enumerate(questions):
            selected = q.correct_index if i == 0 else (q.correct_index + 1) % 4
            self.client.post(
                f"/quiz/{session.id}/answer/",
                {"question_id": q.id, "selected_index": selected},
                format="json",
            )
        self.client.post(f"/quiz/{session.id}/finish/")

        res = self.client.post(f"/quiz/{session.id}/review-mistakes/")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["question_count"], 4)
        self.assertEqual(len(res.data["questions"]), 4)

    def test_review_mistakes_with_nothing_missed_is_rejected(self):
        data = self._start(count=5)
        session = QuizSession.objects.get(pk=data["id"])
        for q in session.questions.all():
            self.client.post(
                f"/quiz/{session.id}/answer/",
                {"question_id": q.id, "selected_index": q.correct_index},
                format="json",
            )
        self.client.post(f"/quiz/{session.id}/finish/")
        res = self.client.post(f"/quiz/{session.id}/review-mistakes/")
        self.assertEqual(res.status_code, 422)

    def test_overview_reports_mastery_after_a_finished_quiz(self):
        before = self.client.get("/quiz/overview/")
        self.assertEqual(before.data["total_quizzes"], 0)
        self.assertEqual(before.data["mastery"], {})

        data = self._start(category="my-topic", count=5)
        session = QuizSession.objects.get(pk=data["id"])
        for q in session.questions.all():
            self.client.post(
                f"/quiz/{session.id}/answer/",
                {"question_id": q.id, "selected_index": q.correct_index},
                format="json",
            )
        self.client.post(f"/quiz/{session.id}/finish/")

        after = self.client.get("/quiz/overview/")
        self.assertEqual(after.data["total_quizzes"], 1)
        self.assertEqual(after.data["avg_score_pct"], 100)
        self.assertEqual(after.data["mastery"], {"my-topic": 100})

    def test_start_with_ingredient_slug_returns_only_that_drugs_questions(self):
        drug0 = Ingredient.objects.get(slug="drug0-1000")
        res = self.client.post("/quiz/start/", {"ingredient_slug": drug0.slug}, format="json")
        self.assertEqual(res.status_code, 201, res.data)
        data = res.data
        self.assertEqual(data["category"], "drug")
        self.assertGreater(len(data["questions"]), 0)
        for q in data["questions"]:
            self.assertEqual(q["subject_slug"], drug0.slug)

    def test_unknown_ingredient_slug_is_rejected(self):
        res = self.client.post("/quiz/start/", {"ingredient_slug": "not-a-real-drug-999"}, format="json")
        self.assertEqual(res.status_code, 422)

    def test_drug_self_test_does_not_pollute_topic_mastery(self):
        drug0 = Ingredient.objects.get(slug="drug0-1000")
        res = self.client.post("/quiz/start/", {"ingredient_slug": drug0.slug}, format="json")
        session = QuizSession.objects.get(pk=res.data["id"])
        for q in session.questions.all():
            self.client.post(
                f"/quiz/{session.id}/answer/",
                {"question_id": q.id, "selected_index": q.correct_index},
                format="json",
            )
        self.client.post(f"/quiz/{session.id}/finish/")

        overview = self.client.get("/quiz/overview/")
        self.assertEqual(overview.data["total_quizzes"], 1)
        self.assertEqual(overview.data["mastery"], {})

    def test_preview_tabulates_by_field_for_the_selection(self):
        res = self.client.get("/quiz/preview/", {"category": "", "atc_code": "C07", "count": 5})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["available"], 5)
        self.assertEqual(res.data["by_field"], [{
            "field": "indication",
            "label_fa": "اندیکاسیون",
            "tone": "info",
            "count": 5,
        }])


@override_settings(ROOT_URLCONF="apps.quiz.urls", BILLING_ENFORCEMENT_ENABLED=True)
class QuizAccessTests(TestCase):
    def setUp(self):
        billing_config.clear_cache()
        self.addCleanup(billing_config.clear_cache)
        _seed_atc_world()
        self.user = get_user_model().objects.create_user(username="quiz-access", password="x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _start_question(self):
        response = self.client.post(
            "/quiz/start/", {"ingredient_slug": "drug0-1000"}, format="json"
        )
        self.assertEqual(response.status_code, 201, response.data)
        return QuizSession.objects.get(pk=response.data["id"]).questions.first()

    def _answer(self, question):
        return self.client.post(
            f"/quiz/{question.session_id}/answer/",
            {"question_id": question.pk, "selected_index": question.correct_index},
            format="json",
        )

    def test_answer_with_billing_enforced_and_unlimited_access_succeeds(self):
        response = self._answer(self._start_question())
        self.assertEqual(response.status_code, 200, response.data)
        self.assertTrue(response.data["correct"])

    def test_answer_with_remaining_quota_succeeds_and_counts_question_once(self):
        PlanFeature.objects.filter(plan__is_free=True, feature__key="quiz").update(
            limit=1, period="day"
        )
        question = self._start_question()

        response = self._answer(question)

        self.assertEqual(response.status_code, 200, response.data)
        self.assertEqual(
            UsageRecord.objects.get(user=self.user, feature_key="quiz").item_key,
            str(question.bank_question_id),
        )

    def test_exhausted_quota_returns_402_without_recording_an_answer(self):
        PlanFeature.objects.filter(plan__is_free=True, feature__key="quiz").update(
            limit=0, period="day"
        )
        question = self._start_question()

        response = self._answer(question)

        self.assertEqual(response.status_code, 402, response.data)
        self.assertEqual(response.data["code"], "QUOTA_EXCEEDED")
        self.assertEqual(response.data["details"]["feature"], "quiz")
        self.assertFalse(hasattr(question, "answer"))
        self.assertFalse(UsageRecord.objects.filter(user=self.user).exists())

    def test_missing_plan_access_returns_402_on_start(self):
        PlanFeature.objects.filter(plan__is_free=True, feature__key="quiz").delete()

        response = self.client.post(
            "/quiz/start/", {"ingredient_slug": "drug0-1000"}, format="json"
        )

        self.assertEqual(response.status_code, 402, response.data)
        self.assertEqual(response.data["code"], "PREMIUM_REQUIRED")
        self.assertFalse(QuizSession.objects.filter(user=self.user).exists())

    def test_unauthenticated_answer_returns_401_instead_of_402(self):
        question = self._start_question()
        self.client.force_authenticate(user=None)

        response = self._answer(question)

        self.assertEqual(response.status_code, 401, response.data)
        self.assertEqual(response.data["code"], "NOT_AUTHENTICATED")


@override_settings(ROOT_URLCONF="apps.core.quiz_maintenance_urls")
class QuizLockedTests(TestCase):
    def test_locked_start_answers_503(self):
        self.assertEqual(APIClient().post("/quiz/start/").status_code, 503)
