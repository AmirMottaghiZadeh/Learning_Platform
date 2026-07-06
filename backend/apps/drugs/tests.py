from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from apps.drugs.learning_adapter import KGameLearningAdapter
from apps.drugs.learning_sync import drug_question_source_external_id, sync_drug_question_source
from apps.drugs.models import Drug, DrugQuestionSource, DrugTopic
from apps.drugs.services import list_target_categories
from apps.learning.models import KnowledgeSource
from apps.quizzes.contracts import QuestionGenerationContext


class KGameLearningAdapterTests(TestCase):
    def test_maps_drug_question_source_to_platform_knowledge_source(self):
        topic = DrugTopic.objects.create(
            key="timing",
            label="Timing",
            detail="Food timing",
        )
        drug = Drug.objects.create(
            external_id="drug-1",
            name="Metformin",
            generic_name="Metformin",
            brand_name="Glucophage",
            source_topic="Endo",
        )
        source = DrugQuestionSource.objects.create(
            topic=topic,
            drug=drug,
            question_type="timing",
            prompt="When should Metformin be taken?",
            correct_answer="with food",
            feedback="Take with food.",
        )

        sources = KGameLearningAdapter().list_knowledge_sources(
            QuestionGenerationContext(topic_key="timing")
        )

        self.assertEqual(len(sources), 1)
        knowledge_source = KnowledgeSource.objects.get(
            product_id="k_game",
            external_id=drug_question_source_external_id(source.id),
        )
        self.assertEqual(sources[0].id, knowledge_source.id)
        self.assertEqual(sources[0].source_type, "timing")
        self.assertEqual(sources[0].topic.key, "timing")
        self.assertEqual(sources[0].learning_object.display_name, "Glucophage")
        self.assertEqual(sources[0].correct_answer, "with food")
        self.assertEqual(sources[0].metadata["target_category_key"], "endocrine")

    def test_sync_uses_brand_only_for_brand_questions_and_generic_elsewhere(self):
        brand_topic = DrugTopic.objects.create(
            key="brandGeneric",
            label="Brand",
        )
        indication_topic = DrugTopic.objects.create(
            key="indication",
            label="Indication",
        )
        side_effect_topic = DrugTopic.objects.create(
            key="sideEffects",
            label="Side effects",
        )
        drug = Drug.objects.create(
            external_id="drug-2",
            name="FallbackName",
            generic_name="آتورواستاتین",
            brand_name="Lipitor",
        )
        brand_source = DrugQuestionSource.objects.create(
            topic=brand_topic,
            drug=drug,
            question_type="brandGeneric",
            prompt="legacy brand prompt",
            correct_answer="آتورواستاتین",
        )
        indication_source = DrugQuestionSource.objects.create(
            topic=indication_topic,
            drug=drug,
            question_type="indication",
            prompt="legacy indication prompt",
            correct_answer="هایپرلیپیدمی",
        )
        side_effect_source = DrugQuestionSource.objects.create(
            topic=side_effect_topic,
            drug=drug,
            question_type="sideEffects",
            prompt="legacy side effect prompt",
            correct_answer="میالژی",
        )

        brand_knowledge = sync_drug_question_source(brand_source)
        indication_knowledge = sync_drug_question_source(indication_source)
        side_effect_knowledge = sync_drug_question_source(side_effect_source)

        self.assertIn("Lipitor", brand_knowledge.prompt)
        self.assertNotIn("آتورواستاتین", brand_knowledge.prompt)
        self.assertIn("آتورواستاتین", indication_knowledge.prompt)
        self.assertNotIn("Lipitor", indication_knowledge.prompt)
        self.assertIn("آتورواستاتین", side_effect_knowledge.prompt)
        self.assertNotIn("Lipitor", side_effect_knowledge.prompt)

    def test_target_category_counts_unique_generic_names_not_brands_or_sources(self):
        brand_topic = DrugTopic.objects.create(key="brandGeneric", label="Brand")
        timing_topic = DrugTopic.objects.create(key="timing", label="Timing")
        first_brand = Drug.objects.create(
            external_id="brand-1",
            brand_name="Brand A",
            generic_name="متفورمین",
            source_topic="Endo",
        )
        second_brand = Drug.objects.create(
            external_id="brand-2",
            brand_name="Brand B",
            generic_name="متفورمین",
            source_topic="Endo",
        )
        other_generic = Drug.objects.create(
            external_id="brand-3",
            brand_name="Brand C",
            generic_name="گلی کلازید",
            source_topic="Endo",
        )
        brand_only = Drug.objects.create(
            external_id="brand-4",
            brand_name="Brand D",
            source_topic="Endo",
        )
        DrugQuestionSource.objects.create(
            topic=brand_topic,
            drug=first_brand,
            question_type="brandGeneric",
            prompt="Brand A?",
            correct_answer="متفورمین",
        )
        DrugQuestionSource.objects.create(
            topic=brand_topic,
            drug=second_brand,
            question_type="brandGeneric",
            prompt="Brand B?",
            correct_answer="متفورمین",
        )
        DrugQuestionSource.objects.create(
            topic=brand_topic,
            drug=other_generic,
            question_type="brandGeneric",
            prompt="Brand C?",
            correct_answer="گلی کلازید",
        )
        DrugQuestionSource.objects.create(
            topic=timing_topic,
            drug=first_brand,
            question_type="timing",
            prompt="Timing?",
            correct_answer="با غذا",
        )
        DrugQuestionSource.objects.create(
            topic=brand_topic,
            drug=brand_only,
            question_type="brandGeneric",
            prompt="Brand D?",
            correct_answer="نامشخص",
        )

        all_counts = {
            item["key"]: item["count"]
            for item in list_target_categories()
        }
        brand_counts = {
            item["key"]: item["count"]
            for item in list_target_categories(source_type="brandGeneric")
        }
        timing_counts = {
            item["key"]: item["count"]
            for item in list_target_categories(source_type="timing")
        }

        self.assertEqual(all_counts["endocrine"], 2)
        self.assertEqual(brand_counts["endocrine"], 2)
        self.assertEqual(timing_counts["endocrine"], 1)

    def test_export_drug_audit_command_writes_visible_report_files(self):
        topic = DrugTopic.objects.create(key="timing", label="Timing")
        drug = Drug.objects.create(
            external_id="drug-audit-1",
            name="Metformin",
            generic_name="Metformin",
            brand_name="Glucophage",
            source_topic="Endo",
            consumption_time_sorted="با غذا",
        )
        DrugQuestionSource.objects.create(
            topic=topic,
            drug=drug,
            question_type="timing",
            prompt="Timing?",
            correct_answer="با غذا",
        )

        with TemporaryDirectory() as temp_dir:
            call_command("export_drug_audit", output_dir=temp_dir)
            output_dir = Path(temp_dir)

            self.assertTrue((output_dir / "drug_audit.html").exists())
            self.assertTrue((output_dir / "category_summary.csv").exists())
            self.assertTrue((output_dir / "drug_records.csv").exists())
            records = (output_dir / "drug_records.csv").read_text(encoding="utf-8-sig")

        self.assertIn("endocrine", records)
        self.assertIn("Metformin", records)
        self.assertIn("Glucophage", records)
