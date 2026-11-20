from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from apps.drugs.chemistry import ChemistryError, depiction, enrich, fetch_candidate, review, version
from apps.drugs.models import ChemistryReview, Ingredient, IngredientChemistry
from apps.drugs.serializers import IngredientDetailSerializer, LessonDrugSerializer


PROPS = {"PropertyTable": {"Properties": [{"CID": 702, "MolecularFormula": "C2H6O",
    "SMILES": "CCO", "InChIKey": "LFQSCWFLJHTTHZ-UHFFFAOYSA-N", "Title": "Ethanol"}]}}


class ChemistryTests(TestCase):
    def setUp(self):
        self.ingredient = Ingredient.objects.create(name="ethanol", name_fa="اتانول", rxcui="448", slug="ethanol-448")

    def candidate(self):
        with patch("apps.drugs.chemistry._get", return_value=PROPS):
            return enrich(self.ingredient)

    def test_validated_pubchem_candidate_is_visible_without_manual_review(self):
        self.assertIsNone(IngredientDetailSerializer(self.ingredient).data["chemistry"])
        chemistry = self.candidate()
        fresh = Ingredient.objects.get(pk=self.ingredient.pk)
        self.assertEqual(LessonDrugSerializer(fresh).data["chemistry"]["molecular_formula"], "C2H6O")
        self.assertEqual(chemistry.status, "pending")
        self.assertIn("<svg", chemistry.structure_svg)
        review(self.ingredient, "approver", "approve", version(chemistry))
        data = LessonDrugSerializer(Ingredient.objects.get(pk=self.ingredient.pk)).data["chemistry"]
        self.assertEqual(LessonDrugSerializer(self.ingredient).data["name_fa"], "اتانول")
        self.assertEqual(data["molecular_formula"], "C2H6O")
        self.assertEqual(data["source_url"], "https://pubchem.ncbi.nlm.nih.gov/compound/702")
        self.assertNotIn("reviewed_by", data)
        self.assertEqual(ChemistryReview.objects.count(), 2)

    def test_formula_and_structure_must_agree(self):
        self.assertIn("<svg", depiction("F", "FH"))
        self.assertIn("<svg", depiction("CCO", "OC2H6"))
        with self.assertRaises(ChemistryError):
            depiction("[Na+]", "Na-")
        with self.assertRaises(ChemistryError):
            depiction("CCO", "C3H8O")
        with self.assertRaises(ChemistryError):
            depiction("invalid!", "C2H6O")

    def test_ambiguous_and_missing_compounds_are_never_guessed(self):
        with patch("apps.drugs.chemistry._get", return_value={"PropertyTable": {"Properties": [{"CID": 1}, {"CID": 2}]}}) as get:
            self.assertEqual(fetch_candidate("mix"), {"status": "ambiguous", "candidates": [1, 2]})
            self.assertEqual(get.call_count, 1)
        with patch("apps.drugs.chemistry._get", return_value=None):
            self.assertEqual(fetch_candidate("not a compound")["status"], "not_found")

    def test_rejection_unpublishes_and_stale_review_is_rejected(self):
        chemistry = self.candidate()
        old_version = version(chemistry)
        approved = review(self.ingredient, "boss", "approve", old_version)
        with self.assertRaises(ChemistryError):
            review(self.ingredient, "other", "reject", old_version)
        review(self.ingredient, "boss", "reject", version(approved))
        self.assertIsNone(LessonDrugSerializer(Ingredient.objects.get(pk=self.ingredient.pk)).data["chemistry"])

    def test_refresh_resets_approval_and_failure_keeps_published_data(self):
        chemistry = self.candidate()
        approved = review(self.ingredient, "boss", "approve", version(chemistry))
        with patch("apps.drugs.chemistry.fetch_candidate", side_effect=ChemistryError("unavailable")):
            with self.assertRaises(ChemistryError):
                enrich(self.ingredient)
        approved.refresh_from_db()
        self.assertEqual(approved.status, "approved")
        with patch("apps.drugs.chemistry._get", return_value=PROPS):
            refreshed = enrich(self.ingredient, cid=702, expected=version(approved))
        self.assertEqual(refreshed.status, "pending")
        self.assertIsNone(refreshed.reviewed_at)
        self.assertEqual(refreshed.reviewed_by, "")

    def test_concurrent_fetch_cannot_overwrite_review(self):
        chemistry = self.candidate()
        def fetch(*args):
            review(self.ingredient, "boss", "approve", version(chemistry))
            return {"status": "not_found", "candidates": []}
        with patch("apps.drugs.chemistry.fetch_candidate", side_effect=fetch):
            with self.assertRaises(ChemistryError):
                enrich(self.ingredient)
        self.assertEqual(IngredientChemistry.objects.get(ingredient=self.ingredient).status, "approved")

    def test_import_resumes_and_never_replaces_existing_decisions(self):
        self.candidate()
        with patch("apps.drugs.chemistry.fetch_candidate") as fetch:
            call_command("import_pubchem", stdout=StringIO())
            fetch.assert_not_called()

    def test_failed_import_exits_nonzero_and_leaves_record_retryable(self):
        with patch("apps.drugs.chemistry.fetch_candidate", side_effect=ChemistryError("unavailable")):
            with self.assertRaises(CommandError):
                call_command("import_pubchem", stdout=StringIO(), stderr=StringIO())
        self.assertFalse(IngredientChemistry.objects.exists())
        with patch("apps.drugs.chemistry._get", return_value=PROPS):
            call_command("import_pubchem", stdout=StringIO())
        self.assertEqual(IngredientChemistry.objects.get().status, "pending")

    def test_identity_change_hides_previously_approved_structure(self):
        chemistry = self.candidate()
        approved = review(self.ingredient, "boss", "approve", version(chemistry))
        Ingredient.objects.filter(pk=self.ingredient.pk).update(name="different salt")
        current = Ingredient.objects.get(pk=self.ingredient.pk)
        self.assertIsNone(LessonDrugSerializer(current).data["chemistry"])
        from apps.data_quality_center.selectors import filtered_ingredients
        self.assertIn(current, filtered_ingredients(None, {"show": "chemistry"}))
        approved.status = "pending"
        approved.save()
        with self.assertRaises(ChemistryError):
            review(current, "boss", "approve", version(approved))

    def test_network_404_is_missing_but_service_failure_is_not(self):
        from urllib.error import HTTPError
        from apps.drugs.chemistry import _get
        with patch("apps.drugs.chemistry.urlopen", side_effect=HTTPError("url", 404, "missing", {}, None)), patch("apps.drugs.chemistry.time.sleep"):
            self.assertIsNone(_get("/test"))
        with patch("apps.drugs.chemistry.urlopen", side_effect=HTTPError("url", 503, "down", {}, None)), patch("apps.drugs.chemistry.time.sleep"):
            with self.assertRaises(ChemistryError):
                _get("/test")


@override_settings(ROOT_URLCONF="apps.data_quality_center.tests_urls")
class ChemistryConsoleTests(ChemistryTests):
    def setUp(self):
        super().setUp()
        User = get_user_model()
        self.editor = User.objects.create_user("chemist", is_staff=True)
        self.approver = User.objects.create_user("boss", is_staff=True, is_superuser=True)
        self.url = reverse("data_quality_center:chemistry", args=[self.ingredient.slug])

    def test_console_permissions_preview_and_approval(self):
        self.assertEqual(self.client.get(self.url).status_code, 302)
        candidate = self.candidate()
        self.client.force_login(self.editor)
        response = self.client.get(self.url)
        self.assertContains(response, "C2H6O")
        self.assertContains(response, "data:image/svg+xml;base64,")
        payload = {"action": "approve", "version": version(candidate)}
        self.assertEqual(self.client.post(self.url, payload).status_code, 403)
        self.client.force_login(self.approver)
        self.assertEqual(self.client.post(self.url, payload).status_code, 302)
        self.assertEqual(IngredientChemistry.objects.get(ingredient=self.ingredient).status, "approved")

    def test_csrf_and_whole_drug_review_do_not_approve_chemistry(self):
        self.candidate()
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.force_login(self.approver)
        self.assertEqual(csrf_client.post(self.url, {"action": "approve"}).status_code, 403)
        from django.utils import timezone
        self.ingredient.reviewed_at = timezone.now()
        self.ingredient.save()
        self.assertIsNotNone(LessonDrugSerializer(Ingredient.objects.get(pk=self.ingredient.pk)).data["chemistry"])
        self.assertEqual(IngredientChemistry.objects.get(ingredient=self.ingredient).status, "pending")

    def test_unresolved_and_incomplete_candidates_remain_hidden(self):
        chemistry = self.candidate()
        for status in ("ambiguous", "not_found", "rejected"):
            chemistry.status = status
            chemistry.save()
            self.assertIsNone(LessonDrugSerializer(Ingredient.objects.get(pk=self.ingredient.pk)).data["chemistry"])
        chemistry.status = "pending"
        chemistry.structure_svg = ""
        chemistry.save()
        self.assertIsNone(LessonDrugSerializer(Ingredient.objects.get(pk=self.ingredient.pk)).data["chemistry"])

    def test_invalid_cid_and_stale_forms_do_not_call_pubchem(self):
        self.client.force_login(self.editor)
        with patch("apps.drugs.chemistry.fetch_candidate") as fetch:
            self.client.post(self.url, {"action": "fetch", "version": "missing", "cid": "https://example.com"})
            self.client.post(self.url, {"action": "fetch", "version": "stale"})
            fetch.assert_not_called()
