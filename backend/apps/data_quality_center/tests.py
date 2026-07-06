from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.ai_data_pipeline import constants
from apps.ai_data_pipeline.models import AIDataBatch, AIDataJob, AIDataReport, AIDataSuggestion
from apps.drugs.models import Drug


class DataQualityCenterTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="reviewer",
            password="pass12345",
            is_staff=True,
            is_superuser=True,
        )
        self.batch = AIDataBatch.objects.create(
            batch_type=constants.BATCH_TYPE_SUGGESTION_GENERATION,
            status=constants.BATCH_STATUS_COMPLETED,
            config={"batch_name": "UI smoke batch"},
            created_by="tester",
        )
        self.job = AIDataJob.objects.create(
            batch=self.batch,
            job_type=constants.JOB_TYPE_FULL_RULES_REVIEW,
            provider=constants.PROVIDER_RULES,
            status=constants.JOB_STATUS_COMPLETED,
            total_records=20,
            processed_records=20,
            suggestions_created=4,
            created_by="tester",
        )
        self.report = AIDataReport.objects.create(
            batch=self.batch,
            report_type=constants.BATCH_TYPE_REPORT,
            format="json",
            content={"hello": "world"},
            summary={"total_records_scanned": 20, "issue_count": 5, "exact_duplicate_groups": 1, "near_duplicate_pairs": 2},
        )
        self.suggestion = AIDataSuggestion.objects.create(
            batch=self.batch,
            table_name=constants.DRUG_TABLE,
            record_id="1",
            field_name="generic_name",
            old_value="متفورمين  ",
            suggested_value="متفورمین",
            suggestion_type=constants.SUGGESTION_TYPE_NORMALIZATION,
            reason="Normalize spacing and Persian characters.",
            confidence_score=0.95,
            risk_level=constants.RISK_SAFE,
            provider=constants.PROVIDER_RULES,
        )
        self.drug = Drug.objects.create(
            external_id="drug-1",
            generic_name="متفورمین",
            brand_name="Glucophage",
            source_topic="Endo",
        )
        self.client.force_login(self.user)

    def test_dashboard_and_core_pages_load(self):
        urls = [
            reverse("data_quality_center:dashboard"),
            reverse("data_quality_center:batch_list"),
            reverse("data_quality_center:job_list"),
            reverse("data_quality_center:suggestion_list"),
            reverse("data_quality_center:health"),
            reverse("data_quality_center:report_list"),
            reverse("data_quality_center:batch_detail", args=[self.batch.id]),
            reverse("data_quality_center:batch_compare", args=[self.batch.id]),
            reverse("data_quality_center:suggestion_detail", args=[self.suggestion.id]),
            reverse("data_quality_center:record_inspector", args=[constants.DRUG_TABLE, self.drug.id]),
            reverse("data_quality_center:report_detail", args=[self.report.id]),
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)

    def test_suggestion_detail_edit_and_review_actions_work(self):
        response = self.client.post(
            reverse("data_quality_center:suggestion_detail", args=[self.suggestion.id]),
            {
                "action": "edit",
                "suggested_value": "متفورمین 500",
                "reason": "More precise normalization.",
                "confidence_score": "0.88",
                "risk_level": constants.RISK_SAFE,
                "reviewer_notes": "Checked manually.",
            },
        )
        self.assertEqual(response.status_code, 302)
        self.suggestion.refresh_from_db()
        self.assertEqual(self.suggestion.status, constants.SUGGESTION_STATUS_EDITED)
        self.assertEqual(self.suggestion.suggested_value, "متفورمین 500")
        self.assertEqual(self.suggestion.metadata.get("reviewer_notes"), "Checked manually.")

        response = self.client.post(
            reverse("data_quality_center:suggestion_detail", args=[self.suggestion.id]),
            {"action": "approve"},
        )
        self.assertEqual(response.status_code, 302)
        self.suggestion.refresh_from_db()
        self.assertEqual(self.suggestion.status, constants.SUGGESTION_STATUS_APPROVED)

    def test_bulk_actions_on_suggestion_list(self):
        second = AIDataSuggestion.objects.create(
            batch=self.batch,
            table_name=constants.DRUG_TABLE,
            record_id="2",
            field_name="brand_name",
            old_value="Glucophage",
            suggested_value="Glucophage XR",
            suggestion_type=constants.SUGGESTION_TYPE_TERMINOLOGY,
            reason="Terminology cleanup.",
            confidence_score=0.9,
            risk_level=constants.RISK_SAFE,
            provider=constants.PROVIDER_RULES,
        )

        response = self.client.post(
            reverse("data_quality_center:suggestion_list"),
            {"action": "approve", "selected_ids": [self.suggestion.id, second.id]},
        )
        self.assertEqual(response.status_code, 302)
        self.suggestion.refresh_from_db()
        second.refresh_from_db()
        self.assertEqual(self.suggestion.status, constants.SUGGESTION_STATUS_APPROVED)
        self.assertEqual(second.status, constants.SUGGESTION_STATUS_APPROVED)

    def test_report_download_routes_work(self):
        response = self.client.get(reverse("data_quality_center:report_download", args=[self.report.id, "json"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json; charset=utf-8")

        response = self.client.get(reverse("data_quality_center:report_download", args=[self.report.id, "csv"]))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")

    def test_batch_generate_report_creates_report(self):
        before = AIDataReport.objects.count()
        response = self.client.post(reverse("data_quality_center:batch_generate_report", args=[self.batch.id]))
        self.assertEqual(response.status_code, 302)
        self.assertGreater(AIDataReport.objects.count(), before)
