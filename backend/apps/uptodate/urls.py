from django.urls import path

from .views import TopicDetailView, TopicSearchView

urlpatterns = [
    path("uptodate/topics/", TopicSearchView.as_view(), name="uptodate-search"),
    path("uptodate/topics/<str:content_id>/", TopicDetailView.as_view(), name="uptodate-detail"),
]
