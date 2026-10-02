"""Read-only clinical-calculator API. Carries no per-user state."""

from django.db.models import Q
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from .models import Calculator
from .serializers import CalculatorDetailSerializer, CalculatorListSerializer


class CalculatorListView(generics.ListAPIView):
    serializer_class = CalculatorListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="Match name or category (case-insensitive)."),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Calculator.objects.order_by("name")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(
                Q(name__icontains=search)
                | Q(description__icontains=search)
                | Q(categories__icontains=search)
            )
        return qs


class CalculatorDetailView(generics.RetrieveAPIView):
    serializer_class = CalculatorDetailSerializer
    lookup_field = "slug"
    queryset = Calculator.objects.all()
