from django.urls import include, path


urlpatterns = [
    path("", include("apps.core.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.drugs.urls")),
    path("", include("apps.lessons.urls")),
    path("", include("apps.progress.urls")),
    # quiz + flashcards are locked until their apps are rebuilt.
    path("", include("apps.core.quiz_maintenance_urls")),
    path("", include("apps.core.flashcards_maintenance_urls")),
]
