from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from apps.games.models import GameSession
from apps.league.models import LeagueResult
from apps.league.services import get_current_season


class LeagueAPITests(TestCase):
    def create_result(self, user, *, raw_score, league_rating, topic_key="timing"):
        season = get_current_season(product_id="k_game")
        session = GameSession.objects.create(
            user=user,
            topic_key=topic_key,
            mode="league",
            status=GameSession.STATUS_FINISHED,
            total_questions=50,
            timer_seconds=30,
            score=raw_score,
            correct_count=raw_score // 10,
            finished_at=timezone.now(),
            is_finished=True,
        )
        return LeagueResult.objects.create(
            user=user,
            session=session,
            product_id="k_game",
            season=season,
            season_key=season.key,
            topic_key=topic_key,
            raw_score=raw_score,
            score_per_question=Decimal(raw_score) / Decimal("50"),
            league_rating=Decimal(league_rating),
            answered=50,
            correct=raw_score // 10,
            wrong=50 - (raw_score // 10),
            percent=raw_score // 10,
            duration_seconds=60,
        )

    def test_leaderboard_uses_best_result_per_user(self):
        first = User.objects.create_user(username="first")
        second = User.objects.create_user(username="second")
        self.create_result(first, raw_score=100, league_rating="2.00")
        self.create_result(first, raw_score=220, league_rating="4.40")
        self.create_result(second, raw_score=180, league_rating="3.60")
        client = APIClient()
        client.force_authenticate(user=first)

        response = client.get("/api/v1/league/?product_id=k_game&topic_key=timing")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["rank"], 1)
        self.assertEqual(response.data[0]["result"]["username"], "first")
        self.assertEqual(response.data[0]["result"]["raw_score"], 220)
        self.assertEqual(response.data[1]["rank"], 2)
        self.assertEqual(response.data[1]["result"]["username"], "second")

    def test_my_rank_returns_current_user_rank(self):
        first = User.objects.create_user(username="first")
        second = User.objects.create_user(username="second")
        self.create_result(first, raw_score=220, league_rating="4.40")
        self.create_result(second, raw_score=180, league_rating="3.60")
        client = APIClient()
        client.force_authenticate(user=second)

        response = client.get("/api/v1/league/me/?product_id=k_game&topic_key=timing")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["rank"], 2)
        self.assertEqual(response.data["total_participants"], 2)
        self.assertEqual(response.data["result"]["username"], "second")

    def test_current_season_endpoint_returns_weekly_season(self):
        user = User.objects.create_user(username="learner")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/league/seasons/current/?product_id=k_game")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["product_id"], "k_game")
        self.assertIn("W", response.data["key"])

    def test_season_list_endpoint_returns_recent_seasons(self):
        user = User.objects.create_user(username="learner")
        get_current_season(product_id="k_game")
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get("/api/v1/league/seasons/?product_id=k_game")

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product_id"], "k_game")

    def test_league_summary_returns_season_rank_and_leaderboard(self):
        first = User.objects.create_user(username="first")
        second = User.objects.create_user(username="second")
        self.create_result(first, raw_score=220, league_rating="4.40")
        self.create_result(second, raw_score=180, league_rating="3.60")
        client = APIClient()
        client.force_authenticate(user=second)

        response = client.get("/api/v1/league/summary/?product_id=k_game&topic_key=timing")

        self.assertEqual(response.status_code, 200)
        self.assertIn("season", response.data)
        self.assertEqual(response.data["my_rank"]["rank"], 2)
        self.assertEqual(response.data["total_participants"], 2)
        self.assertEqual(response.data["leaderboard"][0]["result"]["username"], "first")
