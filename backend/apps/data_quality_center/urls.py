from django.urls import path

from . import views

app_name = "data_quality_center"

urlpatterns = [
    path("", views.ingredient_list, name="ingredient_list"),
    path("history/", views.edit_history, name="edit_history"),
    path("<slug:slug>/", views.ingredient_detail, name="ingredient_detail"),
    path("<slug:slug>/sections/<str:field>/edit/", views.section_edit, name="section_edit"),
]
