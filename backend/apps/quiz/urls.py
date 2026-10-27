from django.urls import path

from .views import (
    QuizAnswerView,
    QuizFinishView,
    QuizOverviewView,
    QuizPreviewView,
    QuizReviewMistakesView,
    QuizStartView,
)

urlpatterns = [
    path("quiz/overview/", QuizOverviewView.as_view(), name="quiz-overview"),
    path("quiz/preview/", QuizPreviewView.as_view(), name="quiz-preview"),
    path("quiz/start/", QuizStartView.as_view(), name="quiz-start"),
    path("quiz/<int:session_id>/answer/", QuizAnswerView.as_view(), name="quiz-answer"),
    path("quiz/<int:session_id>/finish/", QuizFinishView.as_view(), name="quiz-finish"),
    path(
        "quiz/<int:session_id>/review-mistakes/",
        QuizReviewMistakesView.as_view(),
        name="quiz-review-mistakes",
    ),
]
