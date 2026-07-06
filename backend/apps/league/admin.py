from django.contrib import admin

from .models import LeagueResult, LeagueSeason


@admin.register(LeagueSeason)
class LeagueSeasonAdmin(admin.ModelAdmin):
    list_display = ["product_id", "key", "starts_at", "ends_at", "status"]
    search_fields = ["product_id", "key"]
    list_filter = ["product_id", "status"]


@admin.register(LeagueResult)
class LeagueResultAdmin(admin.ModelAdmin):
    list_display = [
        "product_id",
        "season_key",
        "topic_key",
        "user",
        "league_rating",
        "raw_score",
        "rank_snapshot",
        "created_at",
    ]
    search_fields = ["product_id", "season_key", "topic_key", "user__username"]
    list_filter = ["product_id", "season_key", "topic_key"]
    readonly_fields = ["created_at"]
