from django.urls import path
from .views import (
    CurrentLeagueSeasonView,
    LeagueSeasonListView,
    LeagueSummaryView,
    LeagueView,
    MyLeagueRankView,
    StartLeagueView,
)

urlpatterns = [
    path("league/", LeagueView.as_view()),
    path("league/me/", MyLeagueRankView.as_view()),
    path("league/summary/", LeagueSummaryView.as_view()),
    path("league/seasons/", LeagueSeasonListView.as_view()),
    path("league/seasons/current/", CurrentLeagueSeasonView.as_view()),
    path("league/start/", StartLeagueView.as_view()),
]
