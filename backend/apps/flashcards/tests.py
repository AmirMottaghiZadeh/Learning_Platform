from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.drugs.models import Ingredient, IngredientProfileSection
from apps.lessons.selectors import mark_drug_read
from apps.progress.models import LearnerProgress

from .card_facts import adr_facts, build_fact_rows, facts_for_ingredient
from .models import FlashcardFact, LeitnerCard
from .services import due_card_count, seed_deck


def _refresh_facts():
    """What build_flashcards does: rebuild every drug's card facts."""
    FlashcardFact.objects.all().delete()
    FlashcardFact.objects.bulk_create(build_fact_rows()[0])


def _rich_ingredient(name, rxcui, n_products=0):
    ing = Ingredient.objects.create(name=name, rxcui=rxcui, slug=f"{name}-{rxcui}", n_products=n_products)
    for field, fa, en in (
        ("indications_and_usage", f"- درمان فشار خون بالا با {name}", f"- Hypertension, treated with {name}"),
        ("dosage_forms_and_strengths", f"- قرص خوراکی ۵۰ میلی‌گرم {name}", f"- Oral tablet 50 mg of {name}"),
        ("clinical_pharmacology", "مکانیسم اثر دارو", "Mechanism of action"),
    ):
        IngredientProfileSection.objects.create(
            ingredient=ing, field=field, raw_text="x", summary_fa=fa, summary_en=en,
        )
    _refresh_facts()
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
        self.assertEqual([b["field"] for b in card["back_fields_fa"]], ["indication", "dosage_forms"])
        first = card["back_fields_fa"][0]
        self.assertEqual((first["label"], first["tone"]), ("اندیکاسیون", "info"))
        self.assertEqual(len(first["items"]), 1)
        self.assertEqual(card["back_fields_en"][1]["label"], "Dosage forms")
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

    def test_seed_needs_two_card_sections(self):
        # One card section (indication), plus summaries in fields that never
        # go on a card (warnings, mechanism), plus a raw-only one: not enough.
        one = Ingredient.objects.create(name="sparse", rxcui="77", slug="sparse-77", n_products=99)
        IngredientProfileSection.objects.create(
            ingredient=one, field="indications_and_usage", summary_fa="- درمان عفونت‌های ادراری ساده"
        )
        IngredientProfileSection.objects.create(ingredient=one, field="warnings", summary_fa="- هشدار مهم کبدی")
        IngredientProfileSection.objects.create(ingredient=one, field="clinical_pharmacology", summary_fa="مکانیسم")
        IngredientProfileSection.objects.create(ingredient=one, field="adverse_reactions", raw_text="only raw")
        _refresh_facts()

        seed_deck(self.user)
        self.assertFalse(LeitnerCard.objects.filter(user=self.user, ingredient=one).exists())

    def test_seed_query_count_does_not_grow_with_the_catalogue(self):
        for i in range(15):
            _rich_ingredient(f"extra{i}", f"8{i:03d}")
        with self.assertNumQueries(5):
            seed_deck(self.user)
        self.assertEqual(LeitnerCard.objects.filter(user=self.user).count(), 17)

    def test_seed_prioritizes_drugs_the_learner_has_actually_read(self):
        # losartan/metoprolol (setUp) both outrank atenolol by product count,
        # so a limit-of-one seed would normally pick one of them -- marking
        # atenolol as read in Lessons should make it jump the queue instead.
        self.a.n_products = 100
        self.a.save(update_fields=["n_products"])
        self.b.n_products = 100
        self.b.save(update_fields=["n_products"])
        atenolol = _rich_ingredient("atenolol", "2599", n_products=0)
        mark_drug_read(self.user, atenolol.slug)

        result = seed_deck(self.user, limit=1)
        self.assertEqual(result["created"], 1)
        card = LeitnerCard.objects.get(user=self.user)
        self.assertEqual(card.ingredient_id, atenolol.id)

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


class CardFactExtractionTests(TestCase):
    def test_adr_groups_by_heading_and_by_label(self):
        summary = "\n".join([
            "عوارض شایع:",
            "- سردرد خفیف و گذرا در شروع درمان",
            "- تهوع و ناراحتی گوارشی",
            "عوارض مهم و جدی:",
            "- واکنش‌های پوستی شدید: موارد نادر سندرم استیونس-جانسون",
            "نادر:",
            "- ریزش موی برگشت‌پذیر در مصرف طولانی",
            "- شایع: خواب‌آلودگی در روزهای اول مصرف",
            "- جدی: آنژیوادم که نیاز به قطع فوری دارد",
        ])
        facts = adr_facts(summary)
        self.assertEqual(facts["adr_common"], [
            "سردرد خفیف و گذرا در شروع درمان",
            "تهوع و ناراحتی گوارشی",
            "خواب‌آلودگی در روزهای اول مصرف",
        ])
        # a label that names a thing ("severe skin reactions") stays on the
        # fact; the rare group is left out; a "serious" bullet label is a group
        self.assertEqual(facts["adr_serious"], [
            "واکنش‌های پوستی شدید: موارد نادر سندرم استیونس-جانسون",
            "آنژیوادم که نیاز به قطع فوری دارد",
        ])

    def test_an_organ_system_heading_keeps_the_current_group(self):
        summary = "عوارض شایع:\nقلبی:\n- تپش قلب در دوزهای بالا"
        self.assertEqual(adr_facts(summary)["adr_common"], ["تپش قلب در دوزهای بالا"])

    def test_ungrouped_adverse_reactions_are_not_guessed(self):
        self.assertEqual(adr_facts("- سرگیجه هنگام برخاستن"), {"adr_common": [], "adr_serious": []})

    def test_contra_boxed_puts_the_boxed_warning_first(self):
        facts = facts_for_ingredient({
            "contraindications": "- حساسیت شناخته‌شده به دارو",
            "boxed_warning": "- خطر مرگ جنین در بارداری",
        })
        self.assertEqual(facts["contra_boxed"], ["خطر مرگ جنین در بارداری", "حساسیت شناخته‌شده به دارو"])

    def test_build_flashcards_command_replaces_all_facts(self):
        from io import StringIO

        from django.core.management import call_command

        _rich_ingredient("losartan", "52175")
        out = StringIO()
        call_command("build_flashcards", stdout=out)
        self.assertIn("saved 4 flashcard facts", out.getvalue())  # 2 sections x fa/en
        call_command("build_flashcards", stdout=StringIO())
        self.assertEqual(FlashcardFact.objects.count(), 4)
