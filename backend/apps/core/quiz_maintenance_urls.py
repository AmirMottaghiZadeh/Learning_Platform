from django.urls import path

from .maintenance_urls import maintenance_response


urlpatterns = [
    path("games/", maintenance_response),
    path("games/<int:pk>/", maintenance_response),
    path("games/<int:pk>/answer/", maintenance_response),
    path("games/<int:pk>/extend-timer/", maintenance_response),
    path("games/<int:pk>/pause/", maintenance_response),
    path("games/<int:pk>/resume/", maintenance_response),
    path("games/<int:pk>/finish/", maintenance_response),
    path("me/mistakes/", maintenance_response),
    path("me/quiz-history/", maintenance_response),
    path("me/quiz-reminders/", maintenance_response),
    path("me/quiz-reminders/<int:pk>/", maintenance_response),
]
