from django.conf import settings
from django.contrib import admin
from django.urls import include, path, re_path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.manage.views import moved
from apps.website import views_public

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

# The admin: one sign-in and home (apps.manage), with every tool under it --
# the sales console, the site's content panel and the data-quality desk.
urlpatterns += [
    path("manage/site/", include("apps.website.panel.urls")),
    path("manage/", include("apps.manage.urls")),
    # The panel's pictures, served here too so its pages show them.
    path("media/<int:pk>/<str:name>", views_public.media, name="api-media"),
]
if settings.DATA_QUALITY_CENTER_ENABLED:
    urlpatterns.append(path("manage/data/", include("apps.data_quality_center.urls")))
if settings.BILLING_CONSOLE_ENABLED:
    urlpatterns.append(path("manage/sales/", include("apps.billing.console.urls")))

# Where the tools used to be.
urlpatterns += [
    re_path(r"^ops/data-quality/(?P<rest>.*)$", moved("data")),
    re_path(r"^ops/(?P<rest>.*)$", moved("sales")),
]
