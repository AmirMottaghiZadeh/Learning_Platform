from django.urls import path

from .views import ArticleDetailView, ArticleImageDetailView, ArticleListView, ArticleTreeView

urlpatterns = [
    path("medscape/tree/", ArticleTreeView.as_view(), name="medscape-tree"),
    path("medscape/articles/", ArticleListView.as_view(), name="medscape-article-list"),
    path("medscape/articles/<slug:slug>/", ArticleDetailView.as_view(), name="medscape-article-detail"),
    path("medscape/images/<int:image_id>/", ArticleImageDetailView.as_view(), name="medscape-image-detail"),
]
