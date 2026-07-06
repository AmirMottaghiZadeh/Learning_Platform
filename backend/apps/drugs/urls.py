from django.urls import path
from .views import TopicListView, DrugListView, TargetCategoryListView
urlpatterns = [
    path("topics/", TopicListView.as_view()),
    path("target-categories/", TargetCategoryListView.as_view()),
    path("drugs/", DrugListView.as_view()),
]
