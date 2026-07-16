import inspect
from datetime import timedelta

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.drugs.models import Drug, DrugQuestionSource, DrugTopic
from apps.drugs.learning_sync import sync_drug_question_sources
from apps.games.contracts import ScoringContext
from apps.games.models import GameQuestion, GameSession, Mistake, QuizReminder
from apps.games.services.answer_service import answer_question
from apps.games.services.reminder_service import create_quiz_reminder
from apps.games.services.assessment_service import evaluate_answer
from apps.games.services.scoring_service import (
    SCORING_RULE_VERSION,
    calculate_score,
    calculate_score_delta,
)
from apps.games.services.lifecycle_service import extend_current_question_timer, pause_game, resume_game
from apps.games.services.session_service import start_game
from apps.games.serializers import GameQuestionSerializer
from apps.learning.models import (
    KnowledgeSource,
    LearnerProgress,
    LearningEventRecord,
    LearningObject,
    LearningTopic,
)


class AssessmentServiceTests(SimpleTestCase):
    def test_correct_late_answer_is_correct_but_not_scored(self):
        result = evaluate_answer(
            selected_answer="A",
            correct_answer="A",
            remaining_seconds=0,
        )

        self.assertTrue(result.is_correct)
        self.assertTrue(result.time_expired)
        self.assertFalse(result.is_scored_correct)

    def test_wrong_on_time_answer_is_not_correct(self):
        result = evaluate_answer(
            selected_answer="B",
            correct_answer="A",
            remaining_seconds=12,
        )

        self.assertFalse(result.is_correct)
        self.assertFalse(result.time_expired)
        self.assertFalse(result.is_scored_correct)

    def test_timing_answer_uses_canonical_comparison(self):
        result = evaluate_answer(
            selected_answer="فرقی نمی کند",
            correct_answer="فرقی نمی‌کند",
            remaining_seconds=12,
            question_type="timing",
        )

        self.assertTrue(result.is_correct)


class ScoringRuleTests(SimpleTestCase):
    def test_correct_on_time_answer_gets_base_score_and_streak_bonus(self):
        result = calculate_score(
            ScoringContext(
                is_correct=True,
                time_expired=False,
                remaining_seconds=10,
                streak=3,
            )
        )

        self.assertEqual(result.score_delta, 16)
        self.assertEqual(result.xp_delta, 10)
        self.assertEqual(result.streak_delta, 1)
        self.assertEqual(result.bonus["streak"], 6)
        self.assertEqual(result.rule_version, SCORING_RULE_VERSION)

    def test_late_correct_answer_gets_zero_score(self):
        result = calculate_score(
            ScoringContext(
                is_correct=True,
                time_expired=True,
                remaining_seconds=0,
                streak=4,
            )
        )

        self.assertEqual(result.score_delta, 0)
        self.assertEqual(result.xp_delta, 0)
        self.assertEqual(result.streak_delta, -4)

    def test_legacy_score_delta_helper_keeps_existing_contract(self):
        self.assertEqual(calculate_score_delta(is_correct=True, streak=2), 14)
        self.assertEqual(calculate_score_delta(is_correct=False, streak=2), 0)


class GameSessionServiceBoundaryTests(SimpleTestCase):
    def test_session_service_uses_learning_adapter_not_drug_models(self):
        import apps.games.services.session_service as session_service

        source = inspect.getsource(session_service)

        self.assertNotIn("apps.drugs", source)
        self.assertNotIn("DrugQuestionSource", source)


def create_knowledge_source(index: int, *, answer: str | None = None) -> KnowledgeSource:
    topic, _ = LearningTopic.objects.get_or_create(
        product_id="pharmexa",
        key="timing",
        defaults={"label": "Timing"},
    )
    learning_object = LearningObject.objects.create(
        product_id="pharmexa",
        external_id=f"drug-{index}",
        display_name=f"Drug {index}",
        topic=topic,
    )
    return KnowledgeSource.objects.create(
        product_id="pharmexa",
        external_id=f"source-{index}",
        learning_object=learning_object,
        topic=topic,
        source_type="timing",
        prompt=f"Prompt {index}",
        correct_answer=answer or f"Answer {index}",
        explanation=f"Explanation {index}",
        metadata={"chip": "Timing", "subtitle": "Generic"},
    )


class GamePersistenceAlignmentTests(TestCase):
    def test_start_game_writes_generic_knowledge_source(self):
        user = User.objects.create_user(username="learner")
        for index in range(1, 5):
            create_knowledge_source(index)

        session = start_game(user, topic_key="timing", count=10)

        questions = list(session.questions.order_by("order"))
        self.assertEqual(len(questions), 10)
        self.assertTrue(all(question.knowledge_source_id for question in questions))
        self.assertTrue(all(question.source_id is None for question in questions))

    def test_start_game_can_filter_by_target_category(self):
        user = User.objects.create_user(username="learner")
        topic, _ = LearningTopic.objects.get_or_create(
            product_id="pharmexa",
            key="timing",
            defaults={"label": "Timing"},
        )
        for index in range(1, 5):
            learning_object = LearningObject.objects.create(
                product_id="pharmexa",
                external_id=f"cardio-drug-{index}",
                display_name=f"Cardio Drug {index}",
                topic=topic,
                metadata={"target_category_key": "cardiovascular"},
            )
            KnowledgeSource.objects.create(
                product_id="pharmexa",
                external_id=f"cardio-source-{index}",
                learning_object=learning_object,
                topic=topic,
                source_type="timing",
                prompt=f"Cardio prompt {index}",
                correct_answer="با غذا",
                metadata={"target_category_key": "cardiovascular"},
            )
        for index in range(1, 5):
            learning_object = LearningObject.objects.create(
                product_id="pharmexa",
                external_id=f"cns-drug-{index}",
                display_name=f"CNS Drug {index}",
                topic=topic,
                metadata={"target_category_key": "cns"},
            )
            KnowledgeSource.objects.create(
                product_id="pharmexa",
                external_id=f"cns-source-{index}",
                learning_object=learning_object,
                topic=topic,
                source_type="timing",
                prompt=f"CNS prompt {index}",
                correct_answer="بدون غذا",
                metadata={"target_category_key": "cns"},
            )

        session = start_game(
            user,
            mode="category",
            topic_key="timing",
            target_category_key="cardiovascular",
            count=10,
        )

        self.assertEqual(session.target_category_key, "cardiovascular")
        for question in session.questions.select_related("knowledge_source"):
            self.assertEqual(
                question.knowledge_source.metadata["target_category_key"],
                "cardiovascular",
            )

    def test_start_game_uses_each_brand_word_as_separate_question_source(self):
        user = User.objects.create_user(username="brand-quiz")
        brand_topic = DrugTopic.objects.create(key="brandGeneric", label="Brand")
        drug = Drug.objects.create(
            external_id="drug-brand-quiz",
            generic_name="متفورمین",
            brand_name="گلوکوفاژ گلوفورمین دیابزید متفورال",
            source_topic="Endo",
        )
        source = DrugQuestionSource.objects.create(
            topic=brand_topic,
            drug=drug,
            question_type="brandGeneric",
            prompt="legacy prompt",
            correct_answer="متفورمین",
        )
        sync_drug_question_sources(source)

        session = start_game(
            user,
            topic_key="brandGeneric",
            count=5,
        )

        prompts = {
            question.knowledge_source.prompt
            for question in session.questions.select_related("knowledge_source")
        }
        self.assertGreaterEqual(len(prompts), 1)
        self.assertTrue(prompts <= {
            "نام ژنریک داروی تجاری گلوکوفاژ کدام است؟",
            "نام ژنریک داروی تجاری گلوفورمین کدام است؟",
            "نام ژنریک داروی تجاری دیابزید کدام است؟",
            "نام ژنریک داروی تجاری متفورال کدام است؟",
        })
        self.assertFalse(any("گلوکوفاژ گلوفورمین" in prompt for prompt in prompts))

    def test_wrong_answer_creates_mistake_on_generic_knowledge_source(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now(),
        )

        answer_question(
            user,
            session,
            question_id=question.id,
            selected_answer="Wrong",
        )

        mistake = Mistake.objects.get(user=user, topic_key="timing")
        self.assertEqual(mistake.knowledge_source, knowledge_source)
        self.assertIsNone(mistake.source_id)

        progress = LearnerProgress.objects.get(learner=user, topic=knowledge_source.topic)
        self.assertEqual(progress.questions_answered, 1)
        self.assertEqual(progress.correct_answers, 0)
        self.assertEqual(progress.wrong_answers, 1)
        self.assertEqual(progress.mistake_count, 1)
        self.assertEqual(progress.mastery_state, LearnerProgress.MASTERY_SEEN)

        event_types = set(
            LearningEventRecord.objects.filter(learner=user).values_list("event_type", flat=True)
        )
        self.assertIn("QuestionAnswered", event_types)
        self.assertIn("MistakeCreated", event_types)
        self.assertNotIn("ReviewScheduled", event_types)
        self.assertIn("TopicProgressUpdated", event_types)

    def test_start_game_only_starts_first_question_timer(self):
        user = User.objects.create_user(username="learner")
        for index in range(1, 5):
            create_knowledge_source(index)

        session = start_game(user, topic_key="timing", count=10)

        questions = list(session.questions.order_by("order"))
        self.assertIsNotNone(questions[0].question_started_at)
        self.assertIsNone(questions[1].question_started_at)
        self.assertIsNone(questions[2].question_started_at)

    def test_start_game_persists_unstarted_followup_questions_without_timestamps(self):
        user = User.objects.create_user(username="learner_followup")
        for index in range(1, 5):
            create_knowledge_source(index)

        session = start_game(user, topic_key="timing", count=10)

        self.assertEqual(session.questions.filter(question_started_at__isnull=True).count(), 9)

    def test_cannot_answer_question_that_has_not_started(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
        )

        with self.assertRaisesMessage(ValueError, "Question is not active."):
            answer_question(
                user,
                session,
                question_id=question.id,
                selected_answer="Correct",
            )

    def test_answer_stores_assessment_and_scoring_snapshot(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now(),
        )

        answer = answer_question(
            user,
            session,
            question_id=question.id,
            selected_answer="Correct",
        )

        self.assertTrue(answer.is_correct)
        self.assertFalse(answer.time_expired)
        self.assertEqual(answer.score_delta, 10)
        self.assertEqual(answer.xp_delta, 10)
        self.assertEqual(answer.scoring_rule_version, SCORING_RULE_VERSION)

        progress = LearnerProgress.objects.get(learner=user, topic=knowledge_source.topic)
        self.assertEqual(progress.questions_answered, 1)
        self.assertEqual(progress.correct_answers, 1)
        self.assertEqual(progress.xp, 10)

    def test_create_quiz_reminder_persists_question_snapshot(self):
        user = User.objects.create_user(username="learner_reminder")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
            is_finished=True,
            finished_at=timezone.now(),
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now(),
        )

        reminder = create_quiz_reminder(
            user=user,
            game_session_id=session.id,
            game_question_id=question.id,
            question_type="timing",
            prompt="Prompt 1",
            correct_answer="Correct",
            selected_answer="Wrong",
            explanation="Explanation 1",
            options=["Correct", "Wrong"],
        )

        self.assertEqual(QuizReminder.objects.count(), 1)
        self.assertEqual(reminder.knowledge_source, knowledge_source)
        self.assertEqual(reminder.selected_answer, "Wrong")
        self.assertEqual(reminder.options, ["Correct", "Wrong"])

    def test_timing_question_serializer_hides_raw_dosage_chip(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="با غذا")
        knowledge_source.source_type = "timing"
        knowledge_source.metadata = {
            "chip": "Tab: 250 mg\nادم\nسنگ کلیه",
            "subtitle": "نام فارسی: تست",
        }
        knowledge_source.save(update_fields=["source_type", "metadata"])
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["با غذا", "بدون غذا", "فرقی نمی‌کند"],
            question_started_at=timezone.now(),
        )

        data = GameQuestionSerializer(question).data

        self.assertEqual(data["chip"], "")
        self.assertEqual(data["interaction_type"], "segmented")
        self.assertEqual(data["option_layout"], "compact")
        self.assertEqual(data["instruction"], "")
        self.assertNotIn("subtitle", data)
        self.assertNotIn("Tab", data["chip"])

    def test_question_serializer_exposes_timer_contract(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now(),
        )

        data = GameQuestionSerializer(question).data

        self.assertEqual(data["timer_base_seconds"], 30)
        self.assertEqual(data["timer_extension_seconds"], 0)
        self.assertEqual(data["timer_total_seconds"], 30)
        self.assertLessEqual(data["timer_remaining_seconds"], 30)
        self.assertTrue(data["timer_extension_available"])


class GameLifecycleAPITests(TestCase):
    def test_pause_and_resume_endpoints_update_session_status(self):
        user = User.objects.create_user(username="learner")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=0,
            timer_seconds=30,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        pause_response = client.post(f"/api/v1/games/{session.id}/pause/")
        self.assertEqual(pause_response.status_code, 200)
        self.assertEqual(pause_response.data["game"]["status"], GameSession.STATUS_PAUSED)

        resume_response = client.post(f"/api/v1/games/{session.id}/resume/")
        self.assertEqual(resume_response.status_code, 200)
        self.assertEqual(resume_response.data["game"]["status"], GameSession.STATUS_ACTIVE)

    def test_answer_endpoint_returns_platform_error_when_game_is_paused(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            status=GameSession.STATUS_PAUSED,
            total_questions=1,
            timer_seconds=30,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now(),
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(
            f"/api/v1/games/{session.id}/answer/",
            {"question_id": question.id, "selected_answer": "Correct"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["code"], "INVALID_GAME_STATE")
        self.assertEqual(response.data["message"], "Game is paused.")

    def test_late_correct_answer_is_not_scored_but_is_marked_correct_and_expired(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=5,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now() - timedelta(seconds=10),
        )

        answer = answer_question(
            user,
            session,
            question_id=question.id,
            selected_answer="Correct",
        )

        self.assertTrue(answer.is_correct)
        self.assertTrue(answer.time_expired)
        self.assertEqual(answer.score_delta, 0)
        self.assertEqual(answer.xp_delta, 0)

    def test_timer_extension_allows_one_extra_thirty_second_window(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now() - timedelta(seconds=40),
        )

        extend_current_question_timer(session)
        answer = answer_question(
            user,
            session,
            question_id=question.id,
            selected_answer="Correct",
        )

        self.assertTrue(answer.is_correct)
        self.assertFalse(answer.time_expired)
        self.assertEqual(answer.xp_delta, 10)

    def test_timer_extension_endpoint_rejects_second_extension(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=30,
        )
        GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now(),
        )
        client = APIClient()
        client.force_authenticate(user=user)

        first_response = client.post(f"/api/v1/games/{session.id}/extend-timer/")
        second_response = client.post(f"/api/v1/games/{session.id}/extend-timer/")

        self.assertEqual(first_response.status_code, 200)
        self.assertEqual(first_response.data["game"]["current_question"]["timer_total_seconds"], 60)
        self.assertFalse(first_response.data["game"]["current_question"]["timer_extension_available"])
        self.assertEqual(second_response.status_code, 400)
        self.assertEqual(second_response.data["code"], "INVALID_TIMER_EXTENSION")

    def test_pause_resume_freezes_current_question_timer(self):
        user = User.objects.create_user(username="learner")
        knowledge_source = create_knowledge_source(1, answer="Correct")
        session = GameSession.objects.create(
            user=user,
            topic_key="timing",
            mode="random",
            total_questions=1,
            timer_seconds=10,
        )
        question = GameQuestion.objects.create(
            session=session,
            knowledge_source=knowledge_source,
            order=0,
            options=["Correct", "Wrong"],
            question_started_at=timezone.now() - timedelta(seconds=8),
        )

        pause_game(session)
        session.refresh_from_db()
        session.paused_at = timezone.now() - timedelta(seconds=5)
        session.save(update_fields=["paused_at"])

        resume_game(session)
        question.refresh_from_db()
        session.refresh_from_db()

        self.assertEqual(session.status, GameSession.STATUS_ACTIVE)
        self.assertGreaterEqual(question.paused_seconds, 4)
        self.assertGreaterEqual(session.total_paused_seconds, 4)

        answer = answer_question(
            user,
            session,
            question_id=question.id,
            selected_answer="Correct",
        )
        self.assertFalse(answer.time_expired)
