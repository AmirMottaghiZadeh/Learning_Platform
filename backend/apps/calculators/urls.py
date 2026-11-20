from django.urls import path

from .pediatric import PediatricDoseDatasetView
from .views import CalculatorCategoryListView, CalculatorDetailView, CalculatorListView

urlpatterns = [
    path("calculators/pediatric-dose/", PediatricDoseDatasetView.as_view(), name="pediatric-dose-dataset"),
    path("calculators/categories/", CalculatorCategoryListView.as_view(), name="calculator-category-list"),
    path("calculators/", CalculatorListView.as_view(), name="calculator-list"),
    path("calculators/<slug:slug>/", CalculatorDetailView.as_view(), name="calculator-detail"),
]
