from django.urls import path

from . import views
from . import user_activity

app_name = "manage"

urlpatterns = [
    path("app/devices/", user_activity.devices, name="devices"),
    path("app/devices/<uuid:session_id>/revoke/", user_activity.device_revoke, name="device_revoke"),
    path("app/usage/", user_activity.usage, name="usage"),
    path("", views.home, name="home"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("activity/", views.activity, name="activity"),
    path("search/", views.search, name="search"),
]
