from drf_spectacular.utils import extend_schema
from rest_framework import views
from rest_framework.response import Response
from apps.games.services import start_game
from apps.games.serializers import GameSessionSerializer
from .serializers import (
    LeagueLeaderboardEntrySerializer,
    LeagueSeasonSerializer,
    LeagueSummarySerializer,
    LeagueUserRankSerializer,
    StartLeagueSerializer,
)
from .services import get_current_season, get_leaderboard_entries, get_league_summary, get_user_league_rank, list_league_seasons


def bounded_int(value, *, default, minimum, maximum):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return min(max(parsed, minimum), maximum)


class LeagueView(views.APIView):
    @extend_schema(responses=LeagueLeaderboardEntrySerializer(many=True))
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        topic_key = request.query_params.get("topic_key") or None
        season_key = request.query_params.get("season_key") or None
        entries = get_leaderboard_entries(
            product_id=product_id,
            topic_key=topic_key,
            season_key=season_key,
        )
        return Response(LeagueLeaderboardEntrySerializer(entries, many=True).data)


class MyLeagueRankView(views.APIView):
    @extend_schema(responses=LeagueUserRankSerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        topic_key = request.query_params.get("topic_key") or None
        season_key = request.query_params.get("season_key") or None
        rank = get_user_league_rank(
            request.user,
            product_id=product_id,
            topic_key=topic_key,
            season_key=season_key,
        )
        return Response(LeagueUserRankSerializer(rank).data)


class CurrentLeagueSeasonView(views.APIView):
    @extend_schema(responses=LeagueSeasonSerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        season = get_current_season(product_id=product_id)
        return Response(LeagueSeasonSerializer(season).data)


class LeagueSeasonListView(views.APIView):
    @extend_schema(responses=LeagueSeasonSerializer(many=True))
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        limit = bounded_int(request.query_params.get("limit"), default=12, minimum=1, maximum=52)
        seasons = list_league_seasons(product_id=product_id, limit=limit)
        return Response(LeagueSeasonSerializer(seasons, many=True).data)


class LeagueSummaryView(views.APIView):
    @extend_schema(responses=LeagueSummarySerializer)
    def get(self, request):
        product_id = request.query_params.get("product_id") or "k_game"
        topic_key = request.query_params.get("topic_key") or None
        season_key = request.query_params.get("season_key") or None
        summary = get_league_summary(
            request.user,
            product_id=product_id,
            topic_key=topic_key,
            season_key=season_key,
        )
        return Response(LeagueSummarySerializer(summary).data)

class StartLeagueView(views.APIView):
    @extend_schema(request=StartLeagueSerializer, responses={201: GameSessionSerializer})
    def post(self, request):
        serializer = StartLeagueSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        session = start_game(
            request.user,
            topic_key=serializer.validated_data["topic_key"],
            mode="league",
            count=50,
            timer_seconds=serializer.validated_data["timer_seconds"],
        )
        return Response(GameSessionSerializer(session).data, status=201)
