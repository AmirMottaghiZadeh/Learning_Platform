from django.urls import include, path


urlpatterns = [
    path("", include("apps.core.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.learning.urls")),
    path("", include("apps.drugs.urls")),
    path("", include("apps.games.urls")),
    path("", include("apps.league.urls")),
    path("", include("apps.flashcards.urls")),
]
