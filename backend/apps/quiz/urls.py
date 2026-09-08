from django.urls import path

from .views import QuizAnswerView, QuizFinishView, QuizStartView

urlpatterns = [
    path("quiz/start/", QuizStartView.as_view(), name="quiz-start"),
    path("quiz/<int:session_id>/answer/", QuizAnswerView.as_view(), name="quiz-answer"),
    path("quiz/<int:session_id>/finish/", QuizFinishView.as_view(), name="quiz-finish"),
]
