from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(url="/data-quality/", permanent=False)),
    path("data-quality/", include("apps.data_quality_center.urls")),
    path("admin/", admin.site.urls),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="api-v1-schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="api-v1-schema"), name="api-v1-docs"),
    path("api/v1/", include("config.api_urls")),
    # Backward-compatible aliases for the migration starter.
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.learning.urls")),
    path("api/", include("apps.drugs.urls")),
    path("api/", include("apps.games.urls")),
    path("api/", include("apps.league.urls")),
    path("api/", include("apps.flashcards.urls")),
]
