from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(url="/api/v1/docs/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="api-v1-schema"),
    path("api/v1/docs/", SpectacularSwaggerView.as_view(url_name="api-v1-schema"), name="api-v1-docs"),
    path("api/v1/", include("config.api_urls")),
    # Backward-compatible unversioned aliases.
    path("api/auth/", include("apps.accounts.urls")),
    path("api/", include("apps.drugs.urls")),
    path("api/", include("apps.lessons.urls")),
    path("api/", include("apps.progress.urls")),
    path("api/", include("apps.uptodate.urls")),
]

if settings.QUIZ_API_ENABLED:
    urlpatterns.append(path("api/", include("apps.quiz.urls")))
else:
    urlpatterns.append(path("api/", include("apps.core.quiz_maintenance_urls")))

if settings.FLASHCARDS_API_ENABLED:
    urlpatterns.append(path("api/", include("apps.flashcards.urls")))
else:
    urlpatterns.append(path("api/", include("apps.core.flashcards_maintenance_urls")))

if settings.DATA_QUALITY_CENTER_ENABLED:
    urlpatterns.append(
        path("ops/data-quality/", include("apps.data_quality_center.urls"))
    )
