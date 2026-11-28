from django.urls import path

from .views import ChapterView, LessonDrugSearchView, LessonDrugView, LessonGroupsView

urlpatterns = [
    path("lessons/groups/", LessonGroupsView.as_view(), name="lesson-groups"),
    path("lessons/chapters/<str:atc_code>/", ChapterView.as_view(), name="lesson-chapter"),
    path("lessons/search/", LessonDrugSearchView.as_view(), name="lesson-drug-search"),
    path("lessons/drugs/<str:slug>/", LessonDrugView.as_view(), name="lesson-drug"),
]
