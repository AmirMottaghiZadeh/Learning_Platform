import inspect

from django.test import SimpleTestCase

from apps.learning.contracts import (
    KnowledgeSourceRef,
    LearningObjectRef,
    LearningTopicRef,
)
from apps.quizzes.contracts import GeneratedQuestion, QuestionGenerationContext
from apps.quizzes.generators.base import make_choices
from apps.quizzes.services import QuizGenerator
from apps.quizzes.presentation import TIMING_CHOICES


class FakeLearningAdapter:
    product_id = "fake_product"

    def __init__(self):
        self.sources = [
            KnowledgeSourceRef(
                id=index,
                source_type="definition",
                prompt=f"Prompt {index}",
                correct_answer=f"Answer {index}",
                topic=LearningTopicRef(key="letters", label="Letters"),
                learning_object=LearningObjectRef(id=index, display_name=f"Object {index}"),
            )
            for index in range(1, 6)
        ]

    def list_knowledge_sources(self, context):
        return self.sources

    def get_source_instance(self, knowledge_source_id):
        return {"id": knowledge_source_id}


class FakeTimingAdapter:
    product_id = "fake_product"

    def __init__(self):
        topic = LearningTopicRef(key="timing", label="Timing")
        self.sources = [
            KnowledgeSourceRef(
                id=index,
                source_type="timing",
                prompt=f"Timing prompt {index}",
                correct_answer=answer,
                topic=topic,
                learning_object=LearningObjectRef(id=index, display_name=f"Drug {index}"),
            )
            for index, answer in enumerate(
                ["با غذا", "با غذا", "فرقی نمی‌کند", "فرقی نمی‌کند", "بدون غذا"],
                start=1,
            )
        ]

    def list_knowledge_sources(self, context):
        return self.sources

    def get_source_instance(self, knowledge_source_id):
        return {"id": knowledge_source_id}


class QuestionGenerationContractTests(SimpleTestCase):
    def test_generated_question_exposes_platform_assessment_shape(self):
        question = GeneratedQuestion(
            question_type="timing",
            text="When should this be taken?",
            choices=["with food", "without food"],
            correct_answer="with food",
            knowledge_source_id=1,
            explanation="Food timing source",
            difficulty="easy",
        )

        self.assertEqual(question.question_type, "timing")
        self.assertEqual(question.correct_answer, "with food")
        self.assertEqual(question.knowledge_source_id, 1)
        self.assertEqual(question.source_id, 1)
        self.assertEqual(question.explanation, "Food timing source")

    def test_generation_context_captures_extension_inputs(self):
        context = QuestionGenerationContext(
            question_count=5,
            topic_key="timing",
            target_category_key="cardiovascular",
            difficulty_target="easy",
            learner_id=7,
        )

        self.assertEqual(context.question_count, 5)
        self.assertEqual(context.topic_key, "timing")
        self.assertEqual(context.target_category_key, "cardiovascular")
        self.assertEqual(context.difficulty_target, "easy")
        self.assertEqual(context.learner_id, 7)

    def test_make_choices_removes_duplicates_and_keeps_correct_answer(self):
        choices = make_choices("A", ["A", "B", "B", "", "C"], total=4)

        self.assertIn("A", choices)
        self.assertEqual(len(choices), len(set(choices)))
        self.assertLessEqual(len(choices), 3)

    def test_timing_questions_use_canonical_timing_choices(self):
        questions = QuizGenerator(adapter=FakeTimingAdapter()).generate(
            context=QuestionGenerationContext(question_count=5, topic_key="timing")
        )

        for question in questions:
            self.assertEqual(question.question_type, "timing")
            self.assertEqual(question.choices, TIMING_CHOICES)
            self.assertIn(question.correct_answer, TIMING_CHOICES)

    def test_quiz_generator_uses_learning_adapter_contract(self):
        questions = QuizGenerator(adapter=FakeLearningAdapter()).generate(
            context=QuestionGenerationContext(question_count=3)
        )

        self.assertEqual(len(questions), 3)
        self.assertTrue(all(question.knowledge_source_id for question in questions))
        self.assertTrue(all(question.correct_answer in question.choices for question in questions))

    def test_quiz_generator_service_has_no_drug_dependency(self):
        import apps.quizzes.services as quiz_services

        source = inspect.getsource(quiz_services)

        self.assertNotIn("apps.drugs", source)
        self.assertNotIn("DrugQuestionSource", source)
