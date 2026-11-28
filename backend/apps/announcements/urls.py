from django.urls import path

from . import api

urlpatterns = [
    path("announcements/", api.AnnouncementListView.as_view(), name="announcements"),
    path("announcements/<int:pk>/event/", api.AnnouncementEventView.as_view(), name="announcement-event"),
]
