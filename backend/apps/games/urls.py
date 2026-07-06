from django.urls import path

from .views import (
    GameCreateView,
    GameDetailView,
    GameAnswerView,
    GameExtendTimerView,
    GameFinishView,
    GamePauseView,
    GameResumeView,
    MyMistakesView,
)

urlpatterns = [
    path("games/", GameCreateView.as_view()),
    path("games/<int:pk>/", GameDetailView.as_view()),
    path("games/<int:pk>/answer/", GameAnswerView.as_view()),
    path("games/<int:pk>/extend-timer/", GameExtendTimerView.as_view()),
    path("games/<int:pk>/pause/", GamePauseView.as_view()),
    path("games/<int:pk>/resume/", GameResumeView.as_view()),
    path("games/<int:pk>/finish/", GameFinishView.as_view()),
    path("me/mistakes/", MyMistakesView.as_view()),
]
