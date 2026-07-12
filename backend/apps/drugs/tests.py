import json
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase

from apps.drugs.learning_adapter import KGameLearningAdapter
from apps.drugs.learning_sync import drug_question_source_external_id, sync_drug_question_source
from apps.drugs.models import Drug, DrugDatasetDocument, DrugQuestionSource, DrugTopic
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
            product_id="pharmexa",
            external_id=drug_question_source_external_id(source),
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


class DrugJsonImportTests(TestCase):
    def write_dataset(self, directory):
        payload = {
            "schema_version": "1.0",
            "source": {
                "file_name": "Endo.docx",
                "path": "/source/Endo.docx",
                "format": "docx",
                "size_bytes": 1234,
                "sha256": "a" * 64,
                "metadata": {
                    "creator": "Author",
                    "pages": 2,
                },
            },
            "extraction": {
                "mode": "all",
                "method": "docx_xml",
                "ocr_used": False,
                "extracted_at": "2026-07-11T10:00:00+00:00",
            },
            "content": {
                "full_text": "ignored audit content",
                "paragraphs": [],
                "sections": [],
                "tables": [
                    {
                        "index": 2,
                        "records": [
                            {
                                "_source_row": 3,
                                "نام دارو": "متفورمین\nMetformin",
                                "English Generic Name": "Metformin",
                                "Persian Generic Name": "متفورمین",
                                "نام تجاری": "Glucophage",
                                "اشکال دارویی": "Tab 500 mg",
                                "دوزینگ و دستور مصرف": "500 mg twice daily",
                                "اندیکاسیون": "دیابت نوع دو",
                                "رابطه با غذا": "همراه غذا",
                                "بارداری و شیردهی": "رده B",
                                "تنظیم دوز": "تنظیم بر اساس eGFR",
                                "عوارض": "تهوع",
                                "سایر نکات": "مانیتورینگ کلیه",
                                "atc_code": "A10BA02",
                                "class": "ALIMENTARY TRACT AND METABOLISM",
                                "sub_class": "DRUGS USED IN DIABETES",
                                "category": "Biguanides",
                                "نیمه عمر دقیقه": "390",
                            }
                        ],
                    }
                ],
            },
            "warnings": [],
            "enrichment": {
                "drug_names": {
                    "version": "1.0",
                    "method": "test",
                    "records_seen": 1,
                    "matched": 1,
                }
            },
        }
        report = {
            "files": {
                "Endo.docx.json": {
                    "issues": [],
                }
            }
        }
        Path(directory, "Endo.docx.json").write_text(
            json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        Path(directory, "drug_enrichment_report.json").write_text(
            json.dumps(report, ensure_ascii=False),
            encoding="utf-8",
        )

    def test_import_replaces_legacy_metadata_and_preserves_json_provenance(self):
        Drug.objects.create(external_id="legacy", name="Legacy")

        with TemporaryDirectory() as directory:
            self.write_dataset(directory)
            call_command("import_drug_json", directory)

        self.assertFalse(Drug.objects.filter(external_id="legacy").exists())
        self.assertEqual(DrugDatasetDocument.objects.count(), 1)
        document = DrugDatasetDocument.objects.get()
        drug = Drug.objects.get()

        self.assertEqual(document.schema_version, "1.0")
        self.assertEqual(document.source_sha256, "a" * 64)
        self.assertEqual(document.source_metadata["creator"], "Author")
        self.assertEqual(document.extraction_metadata["method"], "docx_xml")
        self.assertEqual(drug.dataset_document, document)
        self.assertEqual(drug.generic_name, "Metformin")
        self.assertEqual(drug.persian_name, "متفورمین")
        self.assertEqual(drug.consumption_time_sorted, "با غذا")
        self.assertEqual(drug.atc_codes, ["A10BA02"])
        self.assertEqual(drug.source_table, 2)
        self.assertEqual(drug.source_row, 3)
        self.assertEqual(drug.extra_attributes["نیمه عمر دقیقه"], "390")
        self.assertEqual(
            set(drug.question_sources.values_list("question_type", flat=True)),
            {
                "brandGeneric",
                "timing",
                "indication",
                "sideEffects",
                "classification",
                "dosageForm",
                "dosing",
                "pregnancy",
                "doseAdjustment",
            },
        )
        self.assertEqual(
            KnowledgeSource.objects.filter(
                product_id="pharmexa",
                learning_object__external_id=drug.external_id,
                is_active=True,
            ).count(),
            9,
        )

        with TemporaryDirectory() as directory:
            self.write_dataset(directory)
            call_command("import_drug_json", directory)

        self.assertEqual(Drug.objects.count(), 1)
        self.assertEqual(DrugDatasetDocument.objects.count(), 1)
        self.assertEqual(DrugQuestionSource.objects.count(), 9)
        self.assertEqual(KnowledgeSource.objects.filter(product_id="pharmexa").count(), 9)

    def test_validate_only_does_not_change_existing_metadata(self):
        Drug.objects.create(external_id="legacy", name="Legacy")

        with TemporaryDirectory() as directory:
            self.write_dataset(directory)
            call_command("import_drug_json", directory, validate_only=True)

        self.assertEqual(Drug.objects.count(), 1)
        self.assertTrue(Drug.objects.filter(external_id="legacy").exists())
        self.assertEqual(DrugDatasetDocument.objects.count(), 0)
