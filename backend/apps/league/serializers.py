from rest_framework import serializers
from .models import LeagueResult, LeagueSeason


class LeagueSeasonSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeagueSeason
        fields = ["id", "product_id", "key", "starts_at", "ends_at", "status"]


class LeagueResultSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username")
    season = LeagueSeasonSerializer(read_only=True)

    class Meta:
        model = LeagueResult
        fields = [
            "id",
            "username",
            "product_id",
            "season",
            "season_key",
            "topic_key",
            "raw_score",
            "score_per_question",
            "time_bonus",
            "league_rating",
            "answered",
            "correct",
            "wrong",
            "percent",
            "duration_seconds",
            "rank_snapshot",
            "league_rule_version",
            "created_at",
        ]


class LeagueLeaderboardEntrySerializer(serializers.Serializer):
    rank = serializers.IntegerField()
    result = LeagueResultSerializer()


class LeagueUserRankSerializer(serializers.Serializer):
    rank = serializers.IntegerField(allow_null=True)
    result = LeagueResultSerializer(allow_null=True)
    total_participants = serializers.IntegerField()


class StartLeagueSerializer(serializers.Serializer):
    topic_key = serializers.CharField(default="timing")
    timer_seconds = serializers.IntegerField(default=30, min_value=5, max_value=120)
