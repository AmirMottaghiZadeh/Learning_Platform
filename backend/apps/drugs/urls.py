from django.urls import path

from .views import AtcCodeListView, IngredientDetailView, IngredientListView

urlpatterns = [
    path("drugs/", IngredientListView.as_view(), name="drug-list"),
    path("drugs/<slug:slug>/", IngredientDetailView.as_view(), name="drug-detail"),
    path("atc/", AtcCodeListView.as_view(), name="atc-list"),
]
