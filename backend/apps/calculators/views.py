"""Read-only clinical-calculator API. Carries no per-user state.

The list is unpaginated -- the client groups all ~500 calculators by clinical
category (a calculator can belong to several) and filters by name/category
client-side, so it always needs the full set rather than one page of it.
"""

from rest_framework import generics

from .models import Calculator
from .serializers import CalculatorDetailSerializer, CalculatorListSerializer


class CalculatorListView(generics.ListAPIView):
    serializer_class = CalculatorListSerializer
    pagination_class = None
    queryset = Calculator.objects.order_by("name")


class CalculatorDetailView(generics.RetrieveAPIView):
    serializer_class = CalculatorDetailSerializer
    lookup_field = "slug"
    queryset = Calculator.objects.all()
