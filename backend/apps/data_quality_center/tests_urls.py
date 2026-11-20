"""Root URLconf used by the DQC tests: mounts the app with its namespace,
the admin shell around it (apps.manage, which signs people in), and
Django's admin so `staff_member_required`'s redirect target resolves.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("manage/data/", include("apps.data_quality_center.urls")),
    path("manage/", include("apps.manage.urls")),
]
