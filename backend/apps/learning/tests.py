from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.flashcards.models import FlashcardState
from apps.learning.models import (
    KnowledgeSource,
    LearnerProgress,
    LearningEventRecord,
    LearningObject,
    LearningTopic,
)


class LearningProgressAPITests(TestCase):
    def test_progress_summary_returns_dashboard_metrics(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="k_game", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="k_game",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="k_game",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
        )
        LearnerProgress.objects.create(
            learner=user,
            product_id="k_game",
            topic=topic,
            questions_answered=4,
            correct_answers=3,
            wrong_answers=1,
            xp=30,
            review_count=2,
            mistake_count=1,
            mastery_state=LearnerProgress.MASTERY_REVIEWING,
        )
        FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            due_at=timezone.now(),
            review_state=FlashcardState.REVIEW_STATE_LEARNING,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/me/progress/summary/?product_id=k_game")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["questions_answered"], 4)
        self.assertEqual(response.data["correct_answers"], 3)
        self.assertEqual(response.data["accuracy_percent"], 75)
        self.assertEqual(response.data["xp"], 30)
        self.assertEqual(response.data["review_count"], 2)
        self.assertEqual(response.data["due_flashcards"], 1)
        self.assertEqual(response.data["weak_topics"][0]["topic_key"], "timing")
        self.assertEqual(response.data["weak_topics"][0]["due_flashcards"], 1)

    def test_dashboard_returns_recommendations_and_league_summary(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="k_game", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="k_game",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="k_game",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
        )
        LearnerProgress.objects.create(
            learner=user,
            product_id="k_game",
            topic=topic,
            questions_answered=4,
            correct_answers=3,
            wrong_answers=1,
            xp=30,
            mistake_count=1,
        )
        FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            due_at=timezone.now(),
            review_state=FlashcardState.REVIEW_STATE_LEARNING,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/me/dashboard/?product_id=k_game")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_id"], "k_game")
        self.assertEqual(response.data["summary"]["due_flashcards"], 1)
        self.assertEqual(response.data["recommendations"][0]["action"], "review_flashcards")
        self.assertIn("season_key", response.data["league"])

    def test_statistics_returns_daily_activity_from_learning_events(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="k_game", key="timing", label="Timing")
        LearnerProgress.objects.create(
            learner=user,
            product_id="k_game",
            topic=topic,
            questions_answered=1,
            correct_answers=1,
            xp=10,
        )
        LearningEventRecord.objects.create(
            event_type="QuestionAnswered",
            learner=user,
            product_id="k_game",
            occurred_at=timezone.now(),
            payload={"xp_delta": 10},
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/me/statistics/?product_id=k_game&days=14")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["days"], 14)
        self.assertEqual(response.data["summary"]["questions_answered"], 1)
        self.assertEqual(response.data["topics"][0]["topic_key"], "timing")
        self.assertEqual(response.data["daily_activity"][-1]["questions_answered"], 1)
        self.assertEqual(response.data["daily_activity"][-1]["xp"], 10)

    def test_weak_topics_endpoint_returns_actionable_topic_signals(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="k_game", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="k_game",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="k_game",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
        )
        LearnerProgress.objects.create(
            learner=user,
            product_id="k_game",
            topic=topic,
            questions_answered=10,
            correct_answers=4,
            wrong_answers=6,
            xp=40,
            review_count=2,
            mistake_count=3,
            mastery_state=LearnerProgress.MASTERY_REVIEWING,
        )
        FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            due_at=timezone.now(),
            review_state=FlashcardState.REVIEW_STATE_LEARNING,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/me/weak-topics/?product_id=k_game")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["topic_key"], "timing")
        self.assertEqual(response.data[0]["wrong_answers"], 6)
        self.assertEqual(response.data[0]["due_flashcards"], 1)
