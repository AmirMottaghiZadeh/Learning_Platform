from django.urls import path

from .maintenance_urls import maintenance_response

# Served while the quiz app is locked (settings.QUIZ_API_ENABLED is False).
urlpatterns = [
    path("quiz/start/", maintenance_response),
    path("quiz/<int:pk>/answer/", maintenance_response),
    path("quiz/<int:pk>/finish/", maintenance_response),
    # legacy aliases
    path("games/", maintenance_response),
    path("games/<int:pk>/", maintenance_response),
    path("games/<int:pk>/answer/", maintenance_response),
    path("games/<int:pk>/finish/", maintenance_response),
]
