"""Read-only clinical-calculator API. Carries no per-user state.

The list is unpaginated -- the client groups all ~500 calculators by clinical
category (a calculator can belong to several) and filters by name/category
client-side, so it always needs the full set rather than one page of it.
"""

from rest_framework import generics

from .models import Calculator, CalculatorCategory
from .serializers import CalculatorCategorySerializer, CalculatorDetailSerializer, CalculatorListSerializer


class CalculatorCategoryListView(generics.ListAPIView):
    """The full category tree (every node, main or sub, in both languages),
    independent of which calculators currently reference each one -- the
    client builds its domain grid by joining this against each calculator's
    own (few) category ids, rather than trying to reconstruct the tree from
    whichever parents happen to also be tagged directly on some calculator
    in the current list."""

    serializer_class = CalculatorCategorySerializer
    pagination_class = None
    queryset = CalculatorCategory.objects.all()


class CalculatorListView(generics.ListAPIView):
    serializer_class = CalculatorListSerializer
    pagination_class = None
    queryset = Calculator.objects.order_by("name").prefetch_related(
        "categories", "categories__parent", "tags"
    )


class CalculatorDetailView(generics.RetrieveAPIView):
    serializer_class = CalculatorDetailSerializer
    lookup_field = "slug"
    queryset = Calculator.objects.prefetch_related("categories", "categories__parent", "tags")
