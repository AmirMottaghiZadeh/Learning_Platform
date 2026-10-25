"""The urlconf for the site's own domains (see apps.website.middleware)."""

from django.urls import include, path, re_path

from apps.billing.views import payment_callback, payment_result
from apps.manage.views import moved

handler404 = "apps.website.views_public.not_found"

urlpatterns = [
    # The panel and the sales console live in the admin now (MANAGE_PUBLIC_URL).
    re_path(r"^panel/(?P<rest>.*)$", moved("site", base="MANAGE_PUBLIC_URL")),
    re_path(r"^ops/(?P<rest>.*)$", moved("sales", base="MANAGE_PUBLIC_URL")),
    path("pay/callback/", payment_callback, name="billing-callback"),
    path("pay/callback/<slug:kind>/", payment_callback, name="billing-callback-gateway"),
    path("pay/result/<str:token>/", payment_result, name="billing-result"),
    path("", include("apps.website.urls_public")),
]
