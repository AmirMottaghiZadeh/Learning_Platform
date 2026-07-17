from io import StringIO

from django.contrib.admin.sites import AdminSite
from django.contrib.auth import get_user_model
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import RequestFactory, TestCase

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.admin import AIDataSuggestionAdmin
from apps.ai_data_pipeline.analyzers.health_check import run_health_check
from apps.ai_data_pipeline.appliers.apply_changes import apply_approved_suggestions
from apps.ai_data_pipeline.models import (
    AIDataBatch,
    AIDataChangeHistory,
    AIDataJob,
    AIDataReport,
    AIDataSuggestion,
    AIDataTranslation,
)
from apps.ai_data_pipeline.providers.base import get_provider
from apps.ai_data_pipeline.reports.report_generator import build_dashboard_summary
from apps.ai_data_pipeline.reviewers.approval import review_suggestions
from apps.ai_data_pipeline.reviewers.suggestion_generator import generate_suggestions
from apps.drugs.models import Drug, DrugQuestionSource


class AIDataPipelineTests(TestCase):
    def create_batch(self, batch_type=constants.BATCH_TYPE_SUGGESTION_GENERATION):
        return AIDataBatch.objects.create(batch_type=batch_type, status=constants.BATCH_STATUS_RUNNING)

    def create_suggestion(self, **overrides):
        batch = overrides.pop("batch", None) or self.create_batch()
        defaults = {
            "batch": batch,
            "table_name": constants.DRUG_TABLE,
            "record_id": "1",
            "field_name": "generic_name",
            "old_value": "متفورمين",
            "suggested_value": "متفورمین",
            "suggestion_type": constants.SUGGESTION_TYPE_NORMALIZATION,
            "reason": "Normalize Persian characters.",
            "confidence_score": 0.95,
            "risk_level": constants.RISK_SAFE,
            "status": constants.SUGGESTION_STATUS_PENDING,
        }
        defaults.update(overrides)
        return AIDataSuggestion.objects.create(**defaults)

    def create_admin_request(self):
        request = RequestFactory().post("/admin/ai_data_pipeline/aidatasuggestion/")
        request.user = get_user_model().objects.create_user(username="admin", password="x", is_staff=True)
        request.session = {}
        request._messages = FallbackStorage(request)
        return request

    def test_health_check_detects_text_and_duplicate_issues(self):
        Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            brand_name="Glucophage",
            dosage_form="TAB 500mg",
            source_topic="Endo",
        )
        Drug.objects.create(
            external_id="drug-2",
            generic_name="متفورمین",
            brand_name="Glucophage",
            dosage_form="TAB 500mg",
            source_topic="Endo",
        )

        report = run_health_check(include_near_duplicates=False)

        issue_types = {issue["issue_type"] for issue in report["issues"]}
        self.assertIn("extra_spaces", issue_types)
        self.assertIn("arabic_persian_character_inconsistency", issue_types)
        self.assertEqual(report["summary"]["exact_duplicate_groups"], 1)

    def test_generate_suggestions_creates_pending_rows_without_modifying_drug(self):
        drug = Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            brand_name="Glucophage",
            dosage_form="TAB 500mg",
            source_topic="Endo",
        )
        batch = self.create_batch()

        summary = generate_suggestions(
            batch=batch,
            fields=["generic_name", "dosage_form"],
            include_duplicates=False,
        )
        drug.refresh_from_db()

        self.assertGreaterEqual(summary["suggestions_generated"], 1)
        self.assertEqual(drug.generic_name, "متفورمين  ")
        self.assertTrue(
            AIDataSuggestion.objects.filter(
                batch=batch,
                status=constants.SUGGESTION_STATUS_PENDING,
                table_name=constants.DRUG_TABLE,
                record_id=str(drug.id),
            ).exists()
        )

    def test_approved_normalization_suggestion_applies_with_history(self):
        drug = Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            brand_name="Glucophage",
            source_topic="Endo",
        )
        batch = self.create_batch()
        suggestion = AIDataSuggestion.objects.create(
            batch=batch,
            table_name=constants.DRUG_TABLE,
            record_id=str(drug.id),
            field_name="generic_name",
            old_value="متفورمين  ",
            suggested_value="متفورمین",
            suggestion_type=constants.SUGGESTION_TYPE_NORMALIZATION,
            reason="Normalize Persian characters and spacing.",
            confidence_score=0.95,
            risk_level=constants.RISK_SAFE,
        )

        review_suggestions(suggestion_ids=[suggestion.id], action="approve", reviewed_by="tester")
        result = apply_approved_suggestions(batch_id=batch.id, applied_by="tester", min_confidence=0.8)
        drug.refresh_from_db()
        suggestion.refresh_from_db()

        self.assertEqual(result.applied, 1)
        self.assertEqual(drug.generic_name, "متفورمین")
        self.assertEqual(suggestion.status, constants.SUGGESTION_STATUS_APPLIED)
        self.assertEqual(AIDataChangeHistory.objects.count(), 1)

    def test_translation_suggestion_stores_translation_without_changing_original(self):
        drug = Drug.objects.create(
            external_id="drug-1",
            persian_name="دیابت",
            brand_name="TestBrand",
            source_topic="Endo",
        )
        batch = self.create_batch()
        suggestion = AIDataSuggestion.objects.create(
            batch=batch,
            table_name=constants.DRUG_TABLE,
            record_id=str(drug.id),
            field_name="persian_name",
            old_value="دیابت",
            suggested_value="diabetes mellitus",
            suggestion_type=constants.SUGGESTION_TYPE_TRANSLATION,
            reason="Medical English translation.",
            confidence_score=0.9,
            risk_level=constants.RISK_SAFE,
        )

        review_suggestions(suggestion_ids=[suggestion.id], action="approve", reviewed_by="tester")
        result = apply_approved_suggestions(batch_id=batch.id, applied_by="tester", min_confidence=0.8)
        drug.refresh_from_db()

        self.assertEqual(result.applied, 1)
        self.assertEqual(drug.persian_name, "دیابت")
        translation = AIDataTranslation.objects.get(table_name=constants.DRUG_TABLE, record_id=str(drug.id))
        self.assertEqual(translation.translated_value, "diabetes mellitus")

    def test_selected_approved_suggestions_apply_only_selected_rows_and_sync_learning_sources(self):
        first_drug = Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            brand_name="Glucophage",
            source_topic="Endo",
        )
        second_drug = Drug.objects.create(
            external_id="drug-2",
            generic_name="Acetaminophen",
            brand_name="Tylenol  ",
            source_topic="Pain",
        )
        batch = self.create_batch()
        selected = self.create_suggestion(
            batch=batch,
            record_id=str(first_drug.id),
            field_name="brand_name",
            old_value="Glucophage",
            suggested_value="Glucophage XR",
        )
        unselected = self.create_suggestion(
            batch=batch,
            record_id=str(second_drug.id),
            field_name="brand_name",
            old_value="Tylenol  ",
            suggested_value="Tylenol",
        )
        review_suggestions(
            suggestion_ids=[selected.id, unselected.id],
            action="approve",
            reviewed_by="tester",
        )

        result = apply_approved_suggestions(
            batch_id=batch.id,
            suggestion_ids=[selected.id],
            applied_by="tester",
        )

        first_drug.refresh_from_db()
        second_drug.refresh_from_db()
        selected.refresh_from_db()
        unselected.refresh_from_db()
        self.assertEqual(result.applied, 1)
        self.assertEqual(first_drug.brand_name, "Glucophage XR")
        self.assertEqual(second_drug.brand_name, "Tylenol  ")
        self.assertEqual(selected.status, constants.SUGGESTION_STATUS_APPLIED)
        self.assertEqual(unselected.status, constants.SUGGESTION_STATUS_APPROVED)
        self.assertEqual(
            DrugQuestionSource.objects.get(
                drug=first_drug,
                question_type="brandGeneric",
            ).prompt,
            "نام ژنریک داروی تجاری Glucophage XR کدام است؟",
        )

    def test_admin_actions_approve_reject_and_mark_needs_review(self):
        model_admin = AIDataSuggestionAdmin(AIDataSuggestion, AdminSite())
        request = self.create_admin_request()
        first = self.create_suggestion()
        second = self.create_suggestion(record_id="2", risk_level=constants.RISK_RISKY)

        queryset = AIDataSuggestion.objects.filter(id__in=[first.id, second.id])
        model_admin.approve_selected_suggestions(request, queryset)
        first.refresh_from_db()
        second.refresh_from_db()

        self.assertEqual(first.status, constants.SUGGESTION_STATUS_APPROVED)
        self.assertEqual(second.status, constants.SUGGESTION_STATUS_APPROVED)
        self.assertEqual(first.reviewed_by, "admin")

        model_admin.reject_selected_suggestions(request, AIDataSuggestion.objects.filter(id=first.id))
        first.refresh_from_db()

        self.assertEqual(first.status, constants.SUGGESTION_STATUS_REJECTED)
        self.assertEqual(first.reviewed_by, "admin")

        applied = self.create_suggestion(record_id="3", status=constants.SUGGESTION_STATUS_APPLIED)
        model_admin.mark_selected_needs_review(
            request,
            AIDataSuggestion.objects.filter(id__in=[second.id, applied.id]),
        )
        second.refresh_from_db()
        applied.refresh_from_db()

        self.assertEqual(second.status, constants.SUGGESTION_STATUS_PENDING)
        self.assertEqual(second.risk_level, constants.RISK_NEEDS_REVIEW)
        self.assertEqual(applied.status, constants.SUGGESTION_STATUS_APPLIED)

    def test_suggestion_validation_rejects_unsafe_targets_and_values(self):
        with self.assertRaises(ValidationError):
            self.create_suggestion(confidence_score=1.5)

        with self.assertRaises(ValidationError):
            self.create_suggestion(record_id="1; DROP TABLE drugs_drug")

        with self.assertRaises(ValidationError):
            self.create_suggestion(table_name="unsafe_table", field_name="generic_name")

        with self.assertRaises(ValidationError):
            self.create_suggestion(field_name="unsafe_field")

        with self.assertRaises(ValidationError):
            self.create_suggestion(
                field_name="unsafe_field",
                suggestion_type=constants.SUGGESTION_TYPE_MEDICAL_WARNING,
            )

    def test_applied_suggestion_is_locked(self):
        suggestion = self.create_suggestion(status=constants.SUGGESTION_STATUS_APPLIED)
        suggestion.suggested_value = "Edited after apply"

        with self.assertRaises(ValidationError):
            suggestion.save()

    def test_report_summary_properties_expose_admin_counts(self):
        batch = self.create_batch(batch_type=constants.BATCH_TYPE_REPORT)
        report = AIDataReport.objects.create(
            batch=batch,
            report_type="summary",
            format="json",
            content={
                "health_report": {
                    "summary": {
                        "total_records_scanned": 10,
                        "issue_count": 4,
                        "exact_duplicate_groups": 1,
                        "near_duplicate_pairs": 2,
                    }
                },
                "suggestions": {
                    "by_type": {
                        constants.SUGGESTION_TYPE_TRANSLATION: 3,
                        constants.SUGGESTION_TYPE_NORMALIZATION: 2,
                        constants.SUGGESTION_TYPE_MEDICAL_WARNING: 1,
                    },
                    "by_risk": {constants.RISK_RISKY: 1},
                    "by_status": {constants.SUGGESTION_STATUS_PENDING: 4},
                    "approved": 2,
                    "rejected": 1,
                    "applied": 0,
                },
            },
        )

        self.assertEqual(report.total_records_scanned, 10)
        self.assertEqual(report.issues_found, 4)
        self.assertEqual(report.duplicate_candidates, 3)
        self.assertEqual(report.suggestion_counts["translation"], 3)
        self.assertEqual(report.suggestion_counts["risky"], 1)

    def test_rule_based_dry_run_does_not_persist_suggestions(self):
        Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            source_topic="Endo",
        )
        batch_count = AIDataBatch.objects.count()
        suggestion_count = AIDataSuggestion.objects.count()

        summary = generate_suggestions(
            batch=None,
            fields=["generic_name"],
            dry_run=True,
            include_duplicates=False,
            include_medical_validation=False,
        )

        self.assertGreaterEqual(summary["suggestions_generated"], 1)
        self.assertEqual(AIDataBatch.objects.count(), batch_count)
        self.assertEqual(AIDataSuggestion.objects.count(), suggestion_count)

    def test_rule_based_terminology_standardizes_dosage_and_units(self):
        drug = Drug.objects.create(
            external_id="drug-1",
            generic_name="Metformin",
            dosage_form="TAB ۵۰۰mg",
            source_topic="Endo",
        )
        batch = self.create_batch()

        generate_suggestions(
            batch=batch,
            fields=["dosage_form"],
            include_duplicates=False,
            include_medical_validation=False,
            include_normalization=False,
            include_terminology=True,
        )
        drug.refresh_from_db()

        suggestion = AIDataSuggestion.objects.get(batch=batch, suggestion_type=constants.SUGGESTION_TYPE_TERMINOLOGY)
        self.assertEqual(suggestion.status, constants.SUGGESTION_STATUS_PENDING)
        self.assertEqual(suggestion.risk_level, constants.RISK_SAFE)
        self.assertEqual(suggestion.suggested_value, "Tablet 500 mg")
        self.assertEqual(drug.dosage_form, "TAB ۵۰۰mg")

    def test_rule_based_unknown_translation_requires_review_without_inventing_text(self):
        drug = Drug.objects.create(
            external_id="drug-1",
            generic_name="TestDrug",
            indication="عبارت تخصصی ناشناخته",
            source_topic="Endo",
        )
        batch = self.create_batch()

        generate_suggestions(
            batch=batch,
            fields=["indication"],
            include_duplicates=False,
            include_medical_validation=False,
            include_normalization=False,
            include_terminology=False,
        )

        suggestion = AIDataSuggestion.objects.get(batch=batch, suggestion_type=constants.SUGGESTION_TYPE_TRANSLATION)
        self.assertEqual(suggestion.status, constants.SUGGESTION_STATUS_PENDING)
        self.assertEqual(suggestion.risk_level, constants.RISK_NEEDS_REVIEW)
        self.assertEqual(suggestion.suggested_value, "")
        self.assertTrue(suggestion.metadata["requires_manual_review"])

    def test_provider_selection_and_provider_field_are_canonical(self):
        self.assertEqual(get_provider("rules").provider_name, constants.PROVIDER_RULES)
        self.assertEqual(get_provider("local-rules").provider_name, constants.PROVIDER_RULES)
        self.assertEqual(get_provider("mock").provider_name, constants.PROVIDER_MOCK)
        drug = Drug.objects.create(
            external_id="drug-1",
            generic_name="TestDrug",
            indication="دیابت",
            source_topic="Endo",
        )
        batch = self.create_batch()

        generate_suggestions(
            batch=batch,
            fields=["indication"],
            provider=get_provider("mock"),
            include_duplicates=False,
            include_medical_validation=False,
            include_normalization=False,
            include_terminology=False,
        )
        drug.refresh_from_db()

        suggestion = AIDataSuggestion.objects.get(batch=batch, suggestion_type=constants.SUGGESTION_TYPE_TRANSLATION)
        self.assertEqual(suggestion.provider, constants.PROVIDER_MOCK)
        self.assertEqual(suggestion.status, constants.SUGGESTION_STATUS_PENDING)
        self.assertEqual(drug.indication, "دیابت")

    def test_job_status_flow_tracks_rule_generation(self):
        Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            source_topic="Endo",
        )
        batch = self.create_batch()
        job = AIDataJob.objects.create(
            batch=batch,
            job_type=constants.JOB_TYPE_FULL_RULES_REVIEW,
            provider=constants.PROVIDER_RULES,
        )

        summary = generate_suggestions(
            batch=batch,
            job=job,
            fields=["generic_name"],
            include_duplicates=False,
            include_medical_validation=False,
        )
        job.refresh_from_db()

        self.assertEqual(job.status, constants.JOB_STATUS_COMPLETED)
        self.assertEqual(job.total_records, 1)
        self.assertEqual(job.processed_records, 1)
        self.assertEqual(job.suggestions_created, summary["suggestions_generated"])

    def test_generate_suggestions_command_dry_run_does_not_save_batch(self):
        Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            source_topic="Endo",
        )
        batch_count = AIDataBatch.objects.count()
        suggestion_count = AIDataSuggestion.objects.count()
        out = StringIO()

        call_command(
            "ai_generate_suggestions",
            "--provider",
            "rules",
            "--dry-run",
            "--limit",
            "5",
            "--field",
            "generic_name",
            "--include-normalization",
            stdout=out,
        )

        self.assertIn("Dry run complete", out.getvalue())
        self.assertEqual(AIDataBatch.objects.count(), batch_count)
        self.assertEqual(AIDataSuggestion.objects.count(), suggestion_count)

    def test_generate_suggestions_command_creates_completed_job(self):
        Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمين  ",
            source_topic="Endo",
        )
        out = StringIO()

        call_command(
            "ai_generate_suggestions",
            "--provider",
            "rules",
            "--limit",
            "5",
            "--field",
            "generic_name",
            "--include-normalization",
            "--batch-name",
            "Test rules job",
            stdout=out,
        )

        job = AIDataJob.objects.get(job_type=constants.JOB_TYPE_FULL_RULES_REVIEW)
        self.assertEqual(job.provider, constants.PROVIDER_RULES)
        self.assertEqual(job.status, constants.JOB_STATUS_COMPLETED)
        self.assertGreaterEqual(job.suggestions_created, 1)
        self.assertTrue(AIDataSuggestion.objects.filter(batch=job.batch, provider=constants.PROVIDER_RULES).exists())

    def test_dashboard_summary_reports_counts(self):
        batch = self.create_batch()
        self.create_suggestion(batch=batch, risk_level=constants.RISK_SAFE)
        self.create_suggestion(
            batch=batch,
            record_id="2",
            risk_level=constants.RISK_NEEDS_REVIEW,
            status=constants.SUGGESTION_STATUS_APPROVED,
        )
        AIDataJob.objects.create(
            batch=batch,
            job_type=constants.JOB_TYPE_FULL_RULES_REVIEW,
            provider=constants.PROVIDER_RULES,
            status=constants.JOB_STATUS_COMPLETED,
            suggestions_created=2,
        )

        summary = build_dashboard_summary()

        self.assertEqual(summary["suggestions_by_status"][constants.SUGGESTION_STATUS_PENDING], 1)
        self.assertEqual(summary["suggestions_by_status"][constants.SUGGESTION_STATUS_APPROVED], 1)
        self.assertEqual(summary["suggestions_by_risk"][constants.RISK_SAFE], 1)
        self.assertEqual(summary["latest_jobs"][0]["provider"], constants.PROVIDER_RULES)
