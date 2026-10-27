from django.urls import path

from .views import (
    DashboardView,
    MistakeListView,
    MistakeResolveView,
    MistakeRestoreView,
    PlanItemCompleteView,
    PlanItemSkipView,
    PlanTodayView,
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
    path("me/plan/today/", PlanTodayView.as_view(), name="me-plan-today"),
    path("me/plan/items/<int:item_id>/complete/", PlanItemCompleteView.as_view(), name="me-plan-item-complete"),
    path("me/plan/items/<int:item_id>/skip/", PlanItemSkipView.as_view(), name="me-plan-item-skip"),
]
