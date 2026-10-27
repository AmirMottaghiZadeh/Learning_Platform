from django.urls import path

from .api import ReleaseCheckView


urlpatterns = [
    path("app/release/", ReleaseCheckView.as_view(), name="app-release-check"),
]
