from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.drugs.models import Ingredient, IngredientProfileSection
from apps.progress.models import LearnerProgress

from .models import LeitnerCard
from .services import due_card_count


def _rich_ingredient(name, rxcui):
    ing = Ingredient.objects.create(name=name, rxcui=rxcui, slug=f"{name}-{rxcui}")
    for field in ("clinical_pharmacology", "dosage_and_administration", "warnings"):
        IngredientProfileSection.objects.create(
            ingredient=ing, field=field, raw_text="x",
            summary_fa=f"{field} fa", summary_en=f"{field} en",
        )
    return ing


@override_settings(ROOT_URLCONF="apps.flashcards.urls")
class FlashcardApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.client.force_authenticate(self.user)
        self.a = _rich_ingredient("losartan", "52175")
        self.b = _rich_ingredient("metoprolol", "6918")
        # an ingredient with too little content -> never seeded
        Ingredient.objects.create(name="thin", rxcui="1", slug="thin-1")

    def test_seed_then_due_then_boxes(self):
        seeded = self.client.post("/flashcards/seed/")
        self.assertEqual(seeded.status_code, 201)
        self.assertEqual(seeded.data["created"], 2)  # only the two rich ones

        due = self.client.get("/flashcards/")
        self.assertEqual(due.status_code, 200)
        self.assertEqual(len(due.data), 2)
        card = due.data[0]
        self.assertIn("\n", card["back_fa"])  # multiple sections joined
        self.assertEqual(card["box"], 1)

        boxes = self.client.get("/flashcards/boxes/").data
        self.assertEqual(len(boxes), 5)
        self.assertEqual(boxes[0]["count"], 2)
        self.assertEqual(boxes[0]["due"], 2)

    def test_seed_is_idempotent(self):
        self.client.post("/flashcards/seed/")
        again = self.client.post("/flashcards/seed/")
        self.assertEqual(again.status_code, 200)
        self.assertEqual(again.data["created"], 0)
        self.assertEqual(LeitnerCard.objects.filter(user=self.user).count(), 2)

    def test_easy_review_promotes_box_reschedules_and_awards_xp(self):
        self.client.post("/flashcards/seed/")
        card = LeitnerCard.objects.filter(user=self.user).first()

        res = self.client.post(f"/flashcards/{card.id}/review/", {"rating": "easy"}, format="json")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["box"], 2)

        card.refresh_from_db()
        self.assertEqual(card.box, 2)
        self.assertGreater(card.due_at, timezone.now())  # pushed into the future
        self.assertEqual(due_card_count(self.user), 1)   # the other card still due

        self.assertEqual(LearnerProgress.objects.get(user=self.user).total_reviews, 1)
        self.assertGreater(LearnerProgress.objects.get(user=self.user).xp, 0)

    def test_hard_review_keeps_card_in_box_one_and_due(self):
        self.client.post("/flashcards/seed/")
        card = LeitnerCard.objects.filter(user=self.user).first()
        self.client.post(f"/flashcards/{card.id}/review/", {"rating": "easy"}, format="json")
        self.client.post(f"/flashcards/{card.id}/review/", {"rating": "hard"}, format="json")
        card.refresh_from_db()
        self.assertEqual(card.box, 1)

    def test_review_of_another_users_card_is_404(self):
        other = get_user_model().objects.create_user(username="o", email="o@e.com", password="x")
        card = LeitnerCard.objects.create(user=other, ingredient=self.a)
        res = self.client.post(f"/flashcards/{card.id}/review/", {"rating": "easy"}, format="json")
        self.assertEqual(res.status_code, 404)


@override_settings(ROOT_URLCONF="apps.core.flashcards_maintenance_urls")
class FlashcardLockedTests(TestCase):
    def test_locked_routes_answer_503_for_get_and_post(self):
        client = APIClient()
        self.assertEqual(client.get("/flashcards/").status_code, 503)
        self.assertEqual(client.post("/flashcards/seed/").status_code, 503)
