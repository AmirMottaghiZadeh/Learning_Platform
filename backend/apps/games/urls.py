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
    QuizHistoryView,
    QuizReminderDetailView,
    QuizReminderListCreateView,
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
    path("me/quiz-history/", QuizHistoryView.as_view()),
    path("me/quiz-reminders/", QuizReminderListCreateView.as_view()),
    path("me/quiz-reminders/<int:pk>/", QuizReminderDetailView.as_view()),
]
