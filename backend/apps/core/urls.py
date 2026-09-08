from django.urls import path

from .views import HealthCheckView, LivenessCheckView, ReadinessCheckView


urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="platform-health"),
    path("live/", LivenessCheckView.as_view(), name="platform-live"),
    path("ready/", ReadinessCheckView.as_view(), name="platform-ready"),
]
