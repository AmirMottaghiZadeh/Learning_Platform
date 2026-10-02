from django.urls import path

from .views import CalculatorDetailView, CalculatorListView

urlpatterns = [
    path("calculators/", CalculatorListView.as_view(), name="calculator-list"),
    path("calculators/<slug:slug>/", CalculatorDetailView.as_view(), name="calculator-detail"),
]
