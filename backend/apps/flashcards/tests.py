from datetime import datetime, timezone

from django.contrib.auth.models import User
from django.test import SimpleTestCase, TestCase
from django.utils import timezone as django_timezone
from rest_framework.test import APIClient

from apps.flashcards.contracts import ReviewSchedulingContext
from apps.flashcards.models import FlashcardState
from apps.flashcards.serializers import FlashcardStateSerializer
from apps.flashcards.services import (
    REVIEW_SCHEDULE_RULE_VERSION,
    calculate_review_schedule,
    get_flashcard_deck_summary,
    get_leitner_box_counts,
    review_card,
    seed_flashcards_for_user,
)
from apps.drugs.models import Drug, DrugQuestionSource, DrugTopic
from apps.learning.models import (
    KnowledgeSource,
    LearnerProgress,
    LearningEventRecord,
    LearningObject,
    LearningTopic,
)


class ReviewSchedulingRuleTests(SimpleTestCase):
    def test_unknown_moves_one_box_forward_up_to_box_five(self):
        reviewed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = calculate_review_schedule(
            ReviewSchedulingContext(
                current_box=4,
                rating="unknown",
                reviewed_at=reviewed_at,
            )
        )

        self.assertEqual(result.next_box, 5)
        self.assertEqual(result.interval_days, 0)
        self.assertEqual(result.rule_version, REVIEW_SCHEDULE_RULE_VERSION)

    def test_known_moves_one_box_back_and_removes_box_one(self):
        reviewed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        result = calculate_review_schedule(
            ReviewSchedulingContext(
                current_box=4,
                rating="known",
                reviewed_at=reviewed_at,
            )
        )

        self.assertEqual(result.next_box, 3)
        self.assertEqual(result.interval_days, 0)

        first_box_result = calculate_review_schedule(
            ReviewSchedulingContext(
                current_box=1,
                rating="known",
                reviewed_at=reviewed_at,
            )
        )
        self.assertEqual(first_box_result.next_box, 0)
        self.assertIsNone(first_box_result.due_at)

    def test_invalid_rating_is_rejected_by_rule(self):
        reviewed_at = datetime(2026, 1, 1, tzinfo=timezone.utc)

        with self.assertRaises(ValueError):
            calculate_review_schedule(
                ReviewSchedulingContext(
                    current_box=1,
                    rating="invalid",
                    reviewed_at=reviewed_at,
                )
            )


class FlashcardPersistenceAlignmentTests(TestCase):
    def test_serializer_reads_generic_knowledge_source_without_legacy_source(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
            explanation="Explanation",
        )
        state = FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            box=1,
        )

        data = FlashcardStateSerializer(state).data

        self.assertEqual(data["prompt"], "Prompt")
        self.assertEqual(data["correct_answer"], "Answer")
        self.assertNotIn("feedback", data)

    def test_review_card_records_schedule_snapshot_and_progress_event(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
            explanation="Explanation",
        )
        state = FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            box=1,
            review_state=FlashcardState.REVIEW_STATE_LEARNING,
            due_at=django_timezone.now(),
        )

        review = review_card(state, "unknown")
        state.refresh_from_db()

        self.assertEqual(review.box_before, 1)
        self.assertEqual(review.box_after, 2)
        self.assertEqual(review.interval_days, 0)
        self.assertEqual(review.rule_version, REVIEW_SCHEDULE_RULE_VERSION)
        self.assertEqual(state.review_count, 1)
        self.assertEqual(state.review_state, FlashcardState.REVIEW_STATE_REVIEW)
        self.assertEqual(state.schedule_rule_version, REVIEW_SCHEDULE_RULE_VERSION)
        self.assertEqual(state.lapse_count, 1)
        self.assertIsNone(state.due_at)

        progress = LearnerProgress.objects.get(learner=user, topic=topic)
        self.assertEqual(progress.review_count, 1)

        event_types = set(
            LearningEventRecord.objects.filter(learner=user).values_list("event_type", flat=True)
        )
        self.assertIn("ReviewCompleted", event_types)
        self.assertIn("TopicProgressUpdated", event_types)

    def test_seed_flashcards_creates_new_cards_outside_due_queue(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
        )
        KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-2",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt 2",
            correct_answer="Answer 2",
        )

        result = seed_flashcards_for_user(user=user, product_id="pharmexa", count=1)

        self.assertEqual(result.created_count, 2)
        states = FlashcardState.objects.filter(user=user).order_by("id")
        self.assertEqual(states.count(), 2)
        self.assertTrue(all(state.box == 0 for state in states))
        self.assertTrue(
            all(state.review_state == FlashcardState.REVIEW_STATE_NEW for state in states)
        )
        self.assertTrue(all(state.due_at is None for state in states))

    def test_leitner_box_counts_include_only_active_boxes(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
        )
        FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            box=2,
            review_state=FlashcardState.REVIEW_STATE_REVIEW,
            due_at=django_timezone.now(),
        )

        counts = get_leitner_box_counts(user=user, product_id="pharmexa")

        self.assertEqual(counts["new"], 0)
        self.assertEqual(counts["total"], 1)
        self.assertEqual(counts["boxes"][1]["box"], 2)
        self.assertEqual(counts["boxes"][1]["count"], 1)

    def test_flashcard_api_uses_category_deck_independent_of_quiz_mistakes(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        cardio_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="cardio-drug-1",
            display_name="Cardio Drug",
            topic=topic,
            metadata={"target_category_key": "cardiovascular"},
        )
        cns_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="cns-drug-1",
            display_name="CNS Drug",
            topic=topic,
            metadata={"target_category_key": "cns"},
        )
        KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="cardio-source-1",
            learning_object=cardio_object,
            topic=topic,
            source_type="timing",
            prompt="Cardio prompt",
            correct_answer="با غذا",
            metadata={"target_category_key": "cardiovascular", "target_category_label": "Cardio"},
        )
        KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="cardio-source-1b",
            learning_object=cardio_object,
            topic=topic,
            source_type="timing",
            prompt="Second cardio prompt",
            correct_answer="بدون غذا",
            metadata={"target_category_key": "cardiovascular", "target_category_label": "Cardio"},
        )
        KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="cardio-source-2",
            learning_object=cardio_object,
            topic=topic,
            source_type="indication",
            prompt="Cardio indication prompt",
            correct_answer="Indication",
            metadata={"target_category_key": "cardiovascular", "target_category_label": "Cardio"},
        )
        KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="cns-source-1",
            learning_object=cns_object,
            topic=topic,
            source_type="timing",
            prompt="CNS prompt",
            correct_answer="بدون غذا",
            metadata={"target_category_key": "cns", "target_category_label": "CNS"},
        )
        client = APIClient()
        client.force_authenticate(user=user)

        seed_response = client.post(
            "/api/v1/flashcards/seed/",
            {
                "product_id": "pharmexa",
                "target_category_key": "cardiovascular",
                "source_type": "timing",
            },
            format="json",
        )
        self.assertEqual(seed_response.status_code, 200)
        self.assertEqual(seed_response.data["created_count"], 2)

        list_response = client.get(
            "/api/v1/flashcards/?product_id=pharmexa&mode=new&target_category_key=cardiovascular&source_type=timing"
        )
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(list_response.data["count"], 2)
        self.assertEqual(
            list_response.data["results"][0]["target_category_key"],
            "cardiovascular",
        )

        box_response = client.get(
            "/api/v1/flashcards/boxes/?product_id=pharmexa&target_category_key=cardiovascular&source_type=timing"
        )
        self.assertEqual(box_response.status_code, 200)
        self.assertEqual(box_response.data["new"], 0)
        self.assertEqual(box_response.data["total"], 0)

        review_response = client.post(
            f"/api/v1/flashcards/{list_response.data['results'][0]['id']}/review/",
            {"rating": "unknown"},
            format="json",
        )
        self.assertEqual(review_response.status_code, 200)
        self.assertEqual(review_response.data["box"], 1)

        due_after_review = client.get(
            "/api/v1/flashcards/?product_id=pharmexa&mode=new&target_category_key=cardiovascular&source_type=timing"
        )
        self.assertEqual(due_after_review.status_code, 200)
        self.assertEqual(due_after_review.data["count"], 1)

        box_after_review = client.get(
            "/api/v1/flashcards/?product_id=pharmexa&mode=leitner&target_category_key=cns&source_type=indication"
        )
        self.assertEqual(box_after_review.status_code, 200)
        self.assertEqual(box_after_review.data["count"], 1)
        self.assertEqual(box_after_review.data["results"][0]["box"], 1)
        self.assertEqual(box_after_review.data["results"][0]["source_type"], "timing")

    def test_leitner_api_can_filter_by_selected_box(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        first_source = KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Box 1 prompt",
            correct_answer="Answer 1",
        )
        second_source = KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-2",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Box 3 prompt",
            correct_answer="Answer 3",
        )
        FlashcardState.objects.create(
            user=user,
            knowledge_source=first_source,
            box=1,
            review_state=FlashcardState.REVIEW_STATE_REVIEW,
        )
        FlashcardState.objects.create(
            user=user,
            knowledge_source=second_source,
            box=3,
            review_state=FlashcardState.REVIEW_STATE_REVIEW,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/flashcards/?product_id=pharmexa&mode=leitner&box=3")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["box"], 3)

    def test_flashcard_api_returns_requested_batch_size(self):
        user = User.objects.create_user(username="batch-learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="batch-drug",
            display_name="Batch Drug",
            topic=topic,
        )
        for index in range(25):
            source = KnowledgeSource.objects.create(
                product_id="pharmexa",
                external_id=f"batch-source-{index}",
                learning_object=learning_object,
                topic=topic,
                source_type="timing",
                prompt=f"Batch prompt {index}",
                correct_answer=f"Batch answer {index}",
            )
            FlashcardState.objects.create(
                user=user,
                knowledge_source=source,
                box=0,
                review_state=FlashcardState.REVIEW_STATE_NEW,
            )

        client = APIClient()
        client.force_authenticate(user=user)

        first_batch = client.get("/api/v1/flashcards/?product_id=pharmexa&mode=new&page_size=20")
        self.assertEqual(first_batch.status_code, 200)
        self.assertEqual(first_batch.data["count"], 25)
        self.assertEqual(len(first_batch.data["results"]), 20)
        last_first_batch_id = first_batch.data["results"][-1]["id"]
        second_batch = client.get(
            f"/api/v1/flashcards/?product_id=pharmexa&mode=new&page_size=20&after_id={last_first_batch_id}"
        )
        self.assertEqual(second_batch.status_code, 200)
        self.assertEqual(len(second_batch.data["results"]), 5)
        self.assertGreater(second_batch.data["results"][0]["id"], last_first_batch_id)

    def test_flashcard_deck_summary_reports_full_selected_deck(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
            metadata={"target_category_key": "cardiovascular"},
        )
        for index in range(3):
            KnowledgeSource.objects.create(
                product_id="pharmexa",
                external_id=f"source-{index}",
                learning_object=learning_object,
                topic=topic,
                source_type="timing",
                prompt=f"Prompt {index}",
                correct_answer=f"Answer {index}",
                metadata={"target_category_key": "cardiovascular"},
            )

        before_seed = get_flashcard_deck_summary(
            user=user,
            product_id="pharmexa",
            target_category_key="cardiovascular",
            source_type="timing",
        )
        self.assertEqual(before_seed["eligible_sources"], 3)
        self.assertEqual(before_seed["unscheduled_sources"], 3)

        seed_flashcards_for_user(
            user=user,
            product_id="pharmexa",
            target_category_key="cardiovascular",
            source_type="timing",
        )
        after_seed = get_flashcard_deck_summary(
            user=user,
            product_id="pharmexa",
            target_category_key="cardiovascular",
            source_type="timing",
        )

        self.assertEqual(after_seed["eligible_sources"], 3)
        self.assertEqual(after_seed["scheduled_cards"], 3)
        self.assertEqual(after_seed["unscheduled_sources"], 0)
        self.assertEqual(after_seed["new_cards"], 3)
        self.assertEqual(after_seed["due_cards"], 0)

        client = APIClient()
        client.force_authenticate(user=user)
        response = client.get(
            "/api/v1/flashcards/decks/?product_id=pharmexa&target_category_key=cardiovascular&source_type=timing"
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["eligible_sources"], 3)
        self.assertEqual(response.data["scheduled_cards"], 3)
        self.assertEqual(response.data["new_cards"], 3)

    def test_brand_flashcard_seed_uses_each_brand_word_as_separate_card(self):
        user = User.objects.create_user(username="brand-learner")
        brand_topic = DrugTopic.objects.create(key="brandGeneric", label="Brand")
        drug = Drug.objects.create(
            external_id="drug-brand-flashcard",
            generic_name="متفورمین",
            brand_name="گلوکوفاژ گلوفورمین دیابزید متفورال",
            source_topic="Endo",
        )
        DrugQuestionSource.objects.create(
            topic=brand_topic,
            drug=drug,
            question_type="brandGeneric",
            prompt="legacy prompt",
            correct_answer="متفورمین",
        )

        result = seed_flashcards_for_user(
            user=user,
            product_id="pharmexa",
            source_type="brandGeneric",
        )

        self.assertEqual(result.created_count, 0)
        self.assertEqual(FlashcardState.objects.filter(user=user).count(), 0)

        from apps.drugs.learning_sync import sync_drug_question_sources

        sync_drug_question_sources(DrugQuestionSource.objects.get(drug=drug))
        result = seed_flashcards_for_user(
            user=user,
            product_id="pharmexa",
            source_type="brandGeneric",
        )

        self.assertEqual(result.created_count, 4)
        states = FlashcardState.objects.filter(user=user).select_related("knowledge_source")
        prompts = {state.knowledge_source.prompt for state in states}
        self.assertEqual(
            prompts,
            {
                "نام ژنریک داروی تجاری گلوکوفاژ کدام است؟",
                "نام ژنریک داروی تجاری گلوفورمین کدام است؟",
                "نام ژنریک داروی تجاری دیابزید کدام است؟",
                "نام ژنریک داروی تجاری متفورال کدام است؟",
            },
        )
        self.assertTrue(all(state.knowledge_source.correct_answer == "متفورمین" for state in states))

    def test_known_new_card_completes_without_entering_leitner(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
        )
        state = FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            box=0,
            review_state=FlashcardState.REVIEW_STATE_NEW,
            due_at=None,
        )

        review_card(state, "known")
        state.refresh_from_db()

        self.assertEqual(state.box, 0)
        self.assertEqual(state.review_state, FlashcardState.REVIEW_STATE_SUSPENDED)
        self.assertIsNone(state.due_at)
        self.assertEqual(get_leitner_box_counts(user=user, product_id="pharmexa")["total"], 0)

    def test_known_box_one_card_leaves_global_leitner_queue(self):
        user = User.objects.create_user(username="learner")
        topic = LearningTopic.objects.create(product_id="pharmexa", key="timing", label="Timing")
        learning_object = LearningObject.objects.create(
            product_id="pharmexa",
            external_id="drug-1",
            display_name="Drug 1",
            topic=topic,
        )
        knowledge_source = KnowledgeSource.objects.create(
            product_id="pharmexa",
            external_id="source-1",
            learning_object=learning_object,
            topic=topic,
            source_type="timing",
            prompt="Prompt",
            correct_answer="Answer",
        )
        state = FlashcardState.objects.create(
            user=user,
            knowledge_source=knowledge_source,
            box=1,
            review_state=FlashcardState.REVIEW_STATE_LEARNING,
        )

        review_card(state, "known")
        state.refresh_from_db()

        self.assertEqual(state.box, 0)
        self.assertEqual(state.review_state, FlashcardState.REVIEW_STATE_SUSPENDED)
        self.assertEqual(get_leitner_box_counts(user=user, product_id="pharmexa")["total"], 0)
