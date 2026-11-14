from django.urls import path
from .views import EventBatchView

urlpatterns = [path("activity/events/", EventBatchView.as_view(), name="activity-events")]
