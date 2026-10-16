"""The urlconf for the site's own domains (see apps.website.middleware)."""

from django.conf import settings
from django.urls import include, path

from apps.billing.views import payment_callback

handler404 = "apps.website.views_public.not_found"

urlpatterns = [
    path("panel/", include("apps.website.panel.urls")),
    path("pay/callback/", payment_callback, name="billing-callback"),
]
if settings.BILLING_CONSOLE_ENABLED:
    urlpatterns.append(path("ops/", include("apps.billing.console.urls")))
urlpatterns.append(path("", include("apps.website.urls_public")))
