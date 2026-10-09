from django.urls import path

from .views import CalculatorCategoryListView, CalculatorDetailView, CalculatorListView

urlpatterns = [
    path("calculators/categories/", CalculatorCategoryListView.as_view(), name="calculator-category-list"),
    path("calculators/", CalculatorListView.as_view(), name="calculator-list"),
    path("calculators/<slug:slug>/", CalculatorDetailView.as_view(), name="calculator-detail"),
]
