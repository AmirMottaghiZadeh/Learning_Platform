from django.urls import path

from .views import ImageDetailView, TopicDetailView, TopicSearchView

urlpatterns = [
    path("uptodate/topics/", TopicSearchView.as_view(), name="uptodate-search"),
    path("uptodate/topics/<str:content_id>/", TopicDetailView.as_view(), name="uptodate-detail"),
    path("uptodate/images/<str:image_id>/", ImageDetailView.as_view(), name="uptodate-image"),
]
