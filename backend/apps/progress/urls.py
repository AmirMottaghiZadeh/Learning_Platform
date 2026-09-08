from django.urls import path

from .views import (
    DashboardView,
    MistakeListView,
    MistakeResolveView,
    MistakeRestoreView,
    StatisticsView,
    StudyPlanView,
)

urlpatterns = [
    path("me/dashboard/", DashboardView.as_view(), name="me-dashboard"),
    path("me/statistics/", StatisticsView.as_view(), name="me-statistics"),
    path("me/mistakes/", MistakeListView.as_view(), name="me-mistakes"),
    path("me/mistakes/restore/", MistakeRestoreView.as_view(), name="me-mistakes-restore"),
    path("me/mistakes/<int:mistake_id>/resolve/", MistakeResolveView.as_view(), name="me-mistake-resolve"),
    path("me/plan/", StudyPlanView.as_view(), name="me-plan"),
]
