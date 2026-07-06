from django.urls import path
from .views import CurrentLeagueSeasonView, LeagueView, MyLeagueRankView, StartLeagueView

urlpatterns = [
    path("league/", LeagueView.as_view()),
    path("league/me/", MyLeagueRankView.as_view()),
    path("league/seasons/current/", CurrentLeagueSeasonView.as_view()),
    path("league/start/", StartLeagueView.as_view()),
]
