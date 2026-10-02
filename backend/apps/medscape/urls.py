from django.urls import path

from .views import ArticleDetailView, ArticleListView, ArticleTreeView

urlpatterns = [
    path("medscape/tree/", ArticleTreeView.as_view(), name="medscape-tree"),
    path("medscape/articles/", ArticleListView.as_view(), name="medscape-article-list"),
    path("medscape/articles/<slug:slug>/", ArticleDetailView.as_view(), name="medscape-article-detail"),
]
