from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from apps.drugs.models import Ingredient
from apps.progress.models import StudyPlan
from apps.progress.services import get_plan

from . import leitner
from .models import FlashcardFact, LeitnerCard


def _drug(name, sections=("indication", "adr_common")):
    ing = Ingredient.objects.create(name=name, name_fa=f"{name}-fa", rxcui=str(abs(hash(name)) % 10**8), slug=f"{name}-x")
    for section in sections:
        for lang in ("fa", "en"):
            FlashcardFact.objects.create(ingredient=ing, section=section, lang=lang, order=0, text=f"{section} {lang}")
    return ing


class LeitnerRulesTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.drug = _drug("amlodipine")

    def test_a_miss_enters_drawer_one_and_each_further_miss_climbs_a_drawer(self):
        card = leitner.add_miss(self.user, self.drug, "indication")
        self.assertEqual((card.box, card.lapses), (1, 1))
        self.assertGreater(card.due_at, timezone.now())  # tomorrow, not now
        for expected in (2, 3, 4, 5, 5):
            card = leitner.add_miss(self.user, self.drug, "indication")
            self.assertEqual(card.box, expected)
        self.assertEqual(LeitnerCard.objects.count(), 1)

    def test_good_steps_down_and_out_of_the_box_from_drawer_one(self):
        card = leitner.add_miss(self.user, self.drug, "indication")
        leitner.add_miss(self.user, self.drug, "indication")
        card.refresh_from_db()
        leitner.review(self.user, card, leitner.GOOD)
        self.assertEqual(card.box, 1)
        leitner.review(self.user, card, leitner.GOOD)
        self.assertEqual(card.box, 0)
        self.assertFalse(LeitnerCard.objects.in_box().exists())
        # missed again later: back in drawer 1
        self.assertEqual(leitner.add_miss(self.user, self.drug, "indication").box, 1)

    def test_forgot_climbs_and_returns_within_the_session_hard_stays(self):
        card = leitner.add_miss(self.user, self.drug, "indication")
        leitner.review(self.user, card, leitner.FORGOT)
        self.assertEqual(card.box, 2)
        self.assertLess(card.due_at, timezone.now() + timedelta(minutes=leitner.RELEARN_MINUTES + 1))
        leitner.review(self.user, card, leitner.HARD)
        self.assertEqual(card.box, 2)
        self.assertGreaterEqual(card.due_at, timezone.now() + timedelta(hours=23))

    def test_each_card_keeps_its_own_interval_and_misses_shorten_it(self):
        easy = leitner.add_miss(self.user, self.drug, "indication")
        hard = leitner.add_miss(self.user, self.drug, "adr_common")
        for _ in range(3):
            leitner.add_miss(self.user, self.drug, "adr_common")
        hard.refresh_from_db()
        easy_next = leitner.outcome(easy, leitner.HARD)["interval_days"] * easy.ease
        hard_next = leitner.outcome(hard, leitner.HARD)["interval_days"] * hard.ease
        self.assertLess(hard.ease, easy.ease)
        self.assertLess(hard_next, easy_next)

    def test_an_exam_date_caps_every_interval_at_half_the_days_left(self):
        plan = get_plan(self.user)
        plan.mode, plan.deadline = StudyPlan.MODE_GOAL, timezone.localdate() + timedelta(days=6)
        plan.save()
        card = leitner.add_miss(self.user, self.drug, "indication")
        card.interval_days = 20
        card.box = 3
        for rating in (leitner.HARD, leitner.GOOD):
            self.assertLessEqual(leitner.outcome(card, rating, leitner._exam_cap_days(self.user))["interval_days"], 3)

    def test_todays_review_is_highest_drawer_first_within_the_daily_minutes(self):
        drugs = [_drug(f"d{i}") for i in range(10)]
        past = timezone.now() - timedelta(minutes=1)
        for i, drug in enumerate(drugs):
            for section in ("indication", "adr_common"):
                LeitnerCard.objects.create(user=self.user, ingredient=drug, section=section, box=1 + i % 5, due_at=past)
        plan = get_plan(self.user)
        plan.mode, plan.daily_minutes = StudyPlan.MODE_MAINTENANCE, 5  # 5 min -> 15 cards
        plan.save()
        queue, due, budget = leitner.today_queue(self.user)
        self.assertEqual((len(queue), due, budget), (15, 20, 15))
        self.assertEqual([c.box for c in queue[:4]], [5, 5, 5, 5])
        leitner.review(self.user, queue[0], leitner.GOOD)
        self.assertEqual(len(leitner.today_queue(self.user)[0]), 14)

    def test_a_drawer_opens_with_all_its_cards_due_or_not(self):
        LeitnerCard.objects.create(user=self.user, ingredient=self.drug, section="indication", box=3,
                                   due_at=timezone.now() + timedelta(days=9))
        self.assertEqual(len(leitner.drawer_cards(self.user, 3)), 1)
        self.assertEqual(leitner.today_queue(self.user)[0], [])

    def test_a_wrong_quiz_answer_boxes_the_card_holding_that_fact(self):
        drug = _drug("warfarin", sections=("adr_common", "interaction"))
        card = leitner.add_quiz_miss(self.user, drug.slug, "adverse_effect")  # no serious card: common
        self.assertEqual(card.section, "adr_common")
        self.assertEqual(leitner.add_quiz_miss(self.user, drug.slug, "interaction").section, "interaction")
        self.assertIsNone(leitner.add_quiz_miss(self.user, drug.slug, "mechanism"))
        self.assertIsNone(leitner.add_quiz_miss(self.user, "nope", "interaction"))


@override_settings(ROOT_URLCONF="apps.flashcards.urls")
class LeitnerApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(username="u", email="u@e.com", password="x")
        self.client.force_authenticate(self.user)
        self.drug = _drug("amlodipine")
        self.card = leitner.add_miss(self.user, self.drug, "indication")
        LeitnerCard.objects.filter(pk=self.card.pk).update(due_at=timezone.now() - timedelta(minutes=1))

    def test_overview_counts_every_drawer_and_todays_review(self):
        data = self.client.get("/flashcards/leitner/").data
        self.assertEqual([d["box"] for d in data["drawers"]], [1, 2, 3, 4, 5])
        self.assertEqual(data["drawers"][0], {"box": 1, "count": 1, "due": 1})
        self.assertEqual((data["total"], data["due"], data["today"]), (1, 1, 1))
        first = data["preview"][0]
        self.assertEqual((first["front_fa"], first["section"], first["section_label_fa"]), ("amlodipine-fa", "indication", "اندیکاسیون"))
        self.assertEqual(first["outcomes"]["good"]["box"], 0)  # drawer 1: good takes it out

    def test_review_moves_the_card_and_answers_it_as_it_now_is(self):
        res = self.client.post(f"/flashcards/leitner/cards/{self.card.id}/review/", {"rating": "forgot"}, format="json")
        self.assertEqual(res.status_code, 200, res.content)
        self.assertEqual(res.data["box"], 2)
        self.assertEqual(len(self.client.get("/flashcards/leitner/cards/", {"box": 2}).data), 1)
        self.assertEqual(self.client.get("/flashcards/leitner/cards/", {"box": 9}).status_code, 400)

    def test_a_card_out_of_the_box_or_someone_elses_is_not_found(self):
        self.client.post(f"/flashcards/leitner/cards/{self.card.id}/review/", {"rating": "good"}, format="json")
        again = self.client.post(f"/flashcards/leitner/cards/{self.card.id}/review/", {"rating": "good"}, format="json")
        self.assertEqual(again.status_code, 404)
        other = get_user_model().objects.create_user(username="o", email="o@e.com", password="x")
        theirs = leitner.add_miss(other, self.drug, "adr_common")
        res = self.client.post(f"/flashcards/leitner/cards/{theirs.id}/review/", {"rating": "good"}, format="json")
        self.assertEqual(res.status_code, 404)

    def test_the_old_box_endpoints_never_see_the_new_cards(self):
        self.assertEqual(self.client.get("/flashcards/").data, [])
        self.assertEqual(sum(b["count"] for b in self.client.get("/flashcards/boxes/").data), 0)
