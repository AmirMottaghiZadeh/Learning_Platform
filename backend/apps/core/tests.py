from django.test import SimpleTestCase

from apps.core.events import LearningEvent, NullLearningEventPublisher, build_learning_event


class LearningEventTests(SimpleTestCase):
    def test_build_learning_event_creates_platform_envelope(self):
        event = build_learning_event(
            event_type="QuestionAnswered",
            learner_id=10,
            payload={"question_id": 20},
        )

        self.assertEqual(event.event_type, "QuestionAnswered")
        self.assertEqual(event.learner_id, 10)
        self.assertEqual(event.product_id, "k_game")
        self.assertEqual(event.payload, {"question_id": 20})
        self.assertTrue(event.correlation_id)

    def test_learning_event_requires_event_type(self):
        with self.assertRaises(ValueError):
            LearningEvent(event_type="", learner_id=1, product_id="k_game")

    def test_null_publisher_matches_event_publisher_contract(self):
        event = build_learning_event(event_type="HealthChecked", learner_id=None)

        self.assertIsNone(NullLearningEventPublisher().publish(event))
