from django.urls import path

from .views import (
    LearnerProgressListView,
    LearningDashboardView,
    LearningProgressSummaryView,
    LearningRecommendationView,
    LearningStatisticsView,
    WeakTopicListView,
)


urlpatterns = [
    path("me/dashboard/", LearningDashboardView.as_view()),
    path("me/progress/", LearnerProgressListView.as_view()),
    path("me/progress/summary/", LearningProgressSummaryView.as_view()),
    path("me/recommendations/", LearningRecommendationView.as_view()),
    path("me/statistics/", LearningStatisticsView.as_view()),
    path("me/weak-topics/", WeakTopicListView.as_view()),
]
