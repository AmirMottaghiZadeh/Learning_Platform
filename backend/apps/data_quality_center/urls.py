from django.urls import path

from . import views

app_name = "data_quality_center"

urlpatterns = [
    path("", views.ingredient_list, name="ingredient_list"),
    path("requests/", views.pending_requests, name="pending_requests"),
    path("requests/<int:request_id>/review/", views.review_request, name="review_request"),
    path("history/", views.edit_history, name="edit_history"),
    path("<slug:slug>/", views.ingredient_detail, name="ingredient_detail"),
    path("<slug:slug>/sections/<str:field>/edit/", views.section_edit, name="section_edit"),
]
