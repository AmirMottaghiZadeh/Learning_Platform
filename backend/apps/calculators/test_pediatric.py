from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from rest_framework.test import APIClient

from apps.billing import config
from apps.billing.models import Plan, PlanFeature, UsageRecord

from .models import Calculator


class PediatricDatasetTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="pediatric-test", password="x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        config.clear_cache()
        self.addCleanup(config.clear_cache)

    def test_dataset_retains_all_source_rules_and_quotes(self):
        response = self.client.get("/api/v1/calculators/pediatric-dose/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Cache-Control"], "private, no-store")
        self.assertEqual(response.data["schema_version"], 1)
        self.assertRegex(response.data["engine_sha256"], r"^[0-9a-f]{64}$")
        drugs = response.data["drugs"]
        self.assertEqual(len(drugs), 50)
        self.assertEqual(sum(len(drug["regimens"]) for drug in drugs), 233)
        for drug in drugs:
            for regimen in drug["regimens"]:
                self.assertTrue(regimen.get("quote") or regimen.get("quotes"))
                self.assertTrue(all(key in drug["products"] for key in regimen["products"]))
        cold = next(drug for drug in drugs if drug["id"] == "cold_products")
        self.assertTrue(any(p.get("verificationStatus") == "unverified" for p in cold["products"].values()))

    def test_anonymous_request_cannot_read_source_data(self):
        self.assertEqual(APIClient().get("/api/v1/calculators/pediatric-dose/").status_code, 401)

    def test_no_patient_submission_endpoint_is_exposed(self):
        response = self.client.post("/api/v1/calculators/pediatric-dose/", {"weight": 20, "age": 5})
        self.assertEqual(response.status_code, 405)

    @override_settings(BILLING_ENFORCEMENT_ENABLED=True)
    def test_calculator_plan_is_required(self):
        PlanFeature.objects.filter(plan__is_free=True, feature__key="calculators").delete()
        response = self.client.get("/api/v1/calculators/pediatric-dose/")
        self.assertEqual(response.status_code, 402)
        self.assertEqual(response.json()["code"], "PREMIUM_REQUIRED")

    @override_settings(BILLING_ENFORCEMENT_ENABLED=True)
    def test_tool_shares_calculator_quota_and_reopening_counts_once(self):
        PlanFeature.objects.filter(plan=Plan.objects.get(is_free=True), feature__key="calculators").update(limit=1, period="day")
        for _ in range(2):
            self.assertEqual(self.client.get("/api/v1/calculators/pediatric-dose/").status_code, 200)
        self.assertEqual(UsageRecord.objects.filter(user=self.user, feature_key="calculators", item_key="pediatric-dose").count(), 1)
        Calculator.objects.create(uid="other", calculator_id="other", slug="other", name="Other")
        response = self.client.get("/api/v1/calculators/other/")
        self.assertEqual(response.status_code, 402)
        self.assertEqual(response.json()["code"], "QUOTA_EXCEEDED")
