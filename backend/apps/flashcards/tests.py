from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.drugs.models import Ingredient, IngredientProfileSection
from apps.lessons.selectors import mark_drug_read
from apps.progress.models import LearnerProgress

from .models import FlashcardFact, LeitnerCard
from .services import due_card_count, seed_deck


_SECTION_OF_FIELD = {"indications_and_usage": "indication", "dosage_forms_and_strengths": "dosage_forms"}


def _refresh_facts():
    """Card facts for the test drugs, written straight from their summaries
    (the cards' content now arrives from outside, not from a generator here):
    the bullets of the two fields that map onto a card section."""
    FlashcardFact.objects.all().delete()
    rows = []
    for sec in IngredientProfileSection.objects.filter(field__in=_SECTION_OF_FIELD):
        for lang, text in (("fa", sec.summary_fa), ("en", sec.summary_en)):
            facts = [line.lstrip("- ").strip() for line in text.splitlines() if line.strip()]
            for order, fact in enumerate(facts):
                rows.append(FlashcardFact(
                    ingredient_id=sec.ingredient_id, section=_SECTION_OF_FIELD[sec.field], lang=lang, order=order, text=fact,
                ))
    FlashcardFact.objects.bulk_create(rows)


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
        # the other old card is still due; the Leitner box (sections) is empty
        self.assertEqual(LeitnerCard.objects.filter(user=self.user, section="", due_at__lte=timezone.now()).count(), 1)
        self.assertEqual(due_card_count(self.user), 0)

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


@override_settings(ROOT_URLCONF="apps.flashcards.urls")
class TopicDeckTests(TestCase):
    def setUp(self):
        from apps.drugs.models import AtcCode

        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="d", email="d@e.com", password="x")
        self.client.force_authenticate(self.user)
        for name, rxcui, code in (
            ("lisinopril", "29046", "C09AA03"),   # hypertension + heart failure
            ("amlodipine", "17767", "C08CA01"),   # hypertension + angina
            ("atorvastatin", "83367", "C10AA05"),  # lipids, last cardio topic with cards
            ("metformin", "6809", "A10BA02"),      # diabetes, next category
        ):
            ing = _rich_ingredient(name, rxcui)
            ing.atc_codes.add(AtcCode.objects.create(code=code, name=name))
        bare = Ingredient.objects.create(name="nofacts", rxcui="9", slug="nofacts-9")
        bare.atc_codes.add(AtcCode.objects.create(code="C08CA02", name="x"))

    def _answer(self, topic, slug, rating="easy", section=None):
        body = {"drug_slug": slug, "rating": rating}
        if section:
            body["section"] = section
        return self.client.post(f"/flashcards/decks/{topic}/answer/", body, format="json")

    def test_overview_lists_only_topics_with_cards_in_taxonomy_order(self):
        data = self.client.get("/flashcards/decks/").data
        self.assertEqual([c["key"] for c in data["categories"]], ["cardio-blood", "endocrine-metabolic"])
        cardio = data["categories"][0]["topics"]
        self.assertEqual([t["key"] for t in cardio], ["cv-htn", "cv-hf", "cv-angina", "cv-lipid"])
        # two drugs with two card sections each; the drug without facts is no card
        self.assertEqual(cardio[0]["total"], 4)
        self.assertEqual((cardio[0]["position"], cardio[0]["finished"]), (0, False))

    def test_deck_is_in_chapter_order_one_section_per_card(self):
        deck = self.client.get("/flashcards/decks/cv-htn/").data
        # chapters in the topic's own order: C08 (amlodipine) before C09;
        # each drug's sections in card order
        self.assertEqual(
            [(c["drug_slug"], c["section"]) for c in deck["cards"]],
            [("amlodipine-17767", "indication"), ("amlodipine-17767", "dosage_forms"),
             ("lisinopril-29046", "indication"), ("lisinopril-29046", "dosage_forms")],
        )
        self.assertEqual(deck["category_key"], "cardio-blood")
        first_card = deck["cards"][0]
        self.assertEqual([b["field"] for b in first_card["back_fields_fa"]], ["indication"])
        self.assertEqual(first_card["section_label_fa"], "اندیکاسیون")

    def test_deck_advances_one_card_at_a_time_and_only_misses_go_in_the_box(self):
        for i, (slug, section, rating) in enumerate([
            ("amlodipine-17767", "indication", "easy"),
            ("amlodipine-17767", "dosage_forms", "hard"),
            ("lisinopril-29046", "indication", "easy"),
        ]):
            res = self._answer("cv-htn", slug, rating, section).data
            self.assertEqual(res["position"], i + 1)
        done = self._answer("cv-htn", "lisinopril-29046", "easy", "dosage_forms").data
        self.assertEqual((done["position"], done["known"], done["hard"], done["finished"]), (4, 3, 1, True))
        self.assertEqual(done["next_topic"]["key"], "cv-hf")
        # only the card not known went in the Leitner box, in drawer 1
        card = LeitnerCard.objects.get(user=self.user)
        self.assertEqual((card.ingredient.slug, card.section, card.box), ("amlodipine-17767", "dosage_forms", 1))

        overview = self.client.get("/flashcards/decks/").data
        self.assertEqual(overview["topics_finished"], 1)
        self.assertEqual(overview["cards_reviewed"], 4)

    def test_an_old_app_answer_without_a_section_rates_the_current_card(self):
        res = self._answer("cv-htn", "amlodipine-17767", "hard").data
        self.assertEqual(res["position"], 1)
        self.assertEqual(LeitnerCard.objects.get(user=self.user).section, "indication")

    def test_reviewing_out_of_order_does_not_move_the_deck(self):
        res = self._answer("cv-htn", "lisinopril-29046", section="dosage_forms")
        self.assertEqual(res.data["position"], 0)
        self.assertFalse(LeitnerCard.objects.filter(user=self.user).exists())

    def test_next_topic_crosses_into_the_next_category(self):
        self._answer("cv-lipid", "atorvastatin-83367", section="indication")
        done = self._answer("cv-lipid", "atorvastatin-83367", section="dosage_forms").data
        self.assertTrue(done["finished"])
        self.assertEqual(done["next_topic"]["key"], "endo-diabetes")
        self.assertEqual(done["next_topic"]["category_key"], "endocrine-metabolic")

    def test_restart_clears_the_pass(self):
        self._answer("cv-htn", "amlodipine-17767")
        res = self.client.post("/flashcards/decks/cv-htn/restart/")
        self.assertEqual((res.data["position"], res.data["known"]), (0, 0))
        self.assertEqual(self.client.get("/flashcards/decks/cv-htn/").data["position"], 0)

    def test_unknown_topic_and_foreign_drug_are_rejected(self):
        self.assertEqual(self.client.get("/flashcards/decks/not-a-topic/").status_code, 404)
        self.assertEqual(self._answer("cv-htn", "metformin-6809").status_code, 422)
