from django.urls import path

from .api import LegalPageView, ReleaseCheckView


urlpatterns = [
    path("app/release/", ReleaseCheckView.as_view(), name="app-release-check"),
    path("app/legal/<slug:slug>/", LegalPageView.as_view(), name="app-legal-page"),
]
