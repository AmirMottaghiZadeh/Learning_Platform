from django.urls import path

from .views import HealthCheckView, LivenessCheckView


urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="platform-health"),
    path("live/", LivenessCheckView.as_view(), name="platform-live"),
    path("ready/", HealthCheckView.as_view(), name="platform-ready"),
]
