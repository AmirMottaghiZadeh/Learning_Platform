from django.conf import settings
from django.urls import include, path


urlpatterns = [
    path("", include("apps.core.urls")),
    path("auth/", include("apps.accounts.urls")),
    path("", include("apps.drugs.urls")),
    path("", include("apps.lessons.urls")),
    path("", include("apps.progress.urls")),
]

if settings.QUIZ_API_ENABLED:
    urlpatterns.append(path("", include("apps.quiz.urls")))
else:
    urlpatterns.append(path("", include("apps.core.quiz_maintenance_urls")))

if settings.FLASHCARDS_API_ENABLED:
    urlpatterns.append(path("", include("apps.flashcards.urls")))
else:
    urlpatterns.append(path("", include("apps.core.flashcards_maintenance_urls")))
