from django.urls import path

from .views import ImageDetailView, SearchMetadataView, TopicDetailView, TopicSearchView, TopicPdfView, TopicMediaView

urlpatterns = [
    path("uptodate/search-metadata/", SearchMetadataView.as_view(), name="uptodate-search-metadata"),
    path("uptodate/topics/", TopicSearchView.as_view(), name="uptodate-search"),
    path("uptodate/topics/<str:content_id>/", TopicDetailView.as_view(), name="uptodate-detail"),
    path("uptodate/topics/<str:content_id>/pdf/", TopicPdfView.as_view(), name="uptodate-pdf"),
    path("uptodate/topics/<str:content_id>/media/<str:media_key>/", TopicMediaView.as_view(), name="uptodate-media"),
    path("uptodate/images/<str:image_id>/", ImageDetailView.as_view(), name="uptodate-image"),
]
