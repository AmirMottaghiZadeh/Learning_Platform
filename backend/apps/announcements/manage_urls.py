from django.urls import path

from . import manage_views as views

app_name = "app_admin"

urlpatterns = [
    path("announcements/", views.announcements, name="announcements"),
    path("announcements/new/", views.announcement, name="announcement_new"),
    path("announcements/<int:pk>/", views.announcement, name="announcement"),
    path("announcements/<int:pk>/action/", views.announcement_action, name="announcement_action"),
]
