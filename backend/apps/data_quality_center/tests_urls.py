"""Root URLconf used by the DQC tests: mounts the app with its namespace.

Includes the admin so `staff_member_required`'s redirect target resolves.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("ops/data-quality/", include("apps.data_quality_center.urls")),
]
