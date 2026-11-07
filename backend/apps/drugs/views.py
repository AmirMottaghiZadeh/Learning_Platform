"""Read-only drug-knowledge API.

Everything here is served from apps.drugs and carries no per-user state. The
learner-facing lesson taxonomy (ATC groups -> chapters -> progress) is built on
top of this in a later phase.
"""

from django.db.models import Count
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics

from .models import AtcCode, Ingredient
from .serializers import (
    AtcCodeSerializer,
    IngredientDetailSerializer,
    IngredientListSerializer,
)


class IngredientListView(generics.ListAPIView):
    serializer_class = IngredientListSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="Match name or RXCUI (prefix, case-insensitive)."),
            OpenApiParameter("atc", str, description="Filter by ATC code prefix, e.g. C09 or C09CA."),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = Ingredient.objects.prefetch_related("atc_codes").order_by("name")
        search = self.request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(name__istartswith=search) | qs.filter(rxcui=search)
            qs = qs.distinct()
        atc = self.request.query_params.get("atc", "").strip().upper()
        if atc:
            qs = qs.filter(atc_codes__code__startswith=atc).distinct()
        return qs


class IngredientDetailView(generics.RetrieveAPIView):
    serializer_class = IngredientDetailSerializer
    lookup_field = "slug"

    def get_queryset(self):
        return Ingredient.objects.prefetch_related("atc_codes", "sections")


class AtcCodeListView(generics.ListAPIView):
    serializer_class = AtcCodeSerializer
    pagination_class = None

    @extend_schema(
        parameters=[
            OpenApiParameter("prefix", str, description="Only codes starting with this prefix."),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        qs = AtcCode.objects.annotate(
            ingredient_count=Count("ingredients", distinct=True)
        ).order_by("code")
        prefix = self.request.query_params.get("prefix", "").strip().upper()
        if prefix:
            qs = qs.filter(code__startswith=prefix)
        return qs
