"""Read-only Medscape article API. Carries no per-user state.

Browsing is two-step by design, since there are ~3200 disease articles --
too many to ship as one flat list for client-side grouping the way
apps.calculators does for its ~500 rows. `ArticleTreeView` returns just the
small category/specialty taxonomy with counts; `ArticleListView` then
either searches by title or lists one specialty's articles on demand.
"""

import collections

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article
from .serializers import ArticleDetailSerializer, ArticleListSerializer


class ArticleTreeView(APIView):
    """The category -> specialty -> count taxonomy for one article kind."""

    @extend_schema(parameters=[OpenApiParameter("kind", str, description="'disease' or 'guideline'.")])
    def get(self, request):
        kind = request.query_params.get("kind", Article.DISEASE)
        tree = collections.defaultdict(collections.Counter)
        for categories in Article.objects.filter(kind=kind).values_list("categories", flat=True):
            for pair in categories:
                tree[pair["category"]][pair["specialty"]] += 1
        return Response([
            {
                "category": category,
                "specialties": [
                    {"name": name, "count": count} for name, count in sorted(specialties.items())
                ],
            }
            for category, specialties in sorted(tree.items())
        ])


class ArticleListView(generics.ListAPIView):
    serializer_class = ArticleListSerializer
    pagination_class = None

    @extend_schema(
        parameters=[
            OpenApiParameter("kind", str, description="'disease' or 'guideline'."),
            OpenApiParameter("search", str, description="Match title (case-insensitive)."),
            OpenApiParameter("category", str, description="Browse mode: with `specialty`."),
            OpenApiParameter("specialty", str, description="Browse mode: with `category`."),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        kind = self.request.query_params.get("kind", Article.DISEASE)
        qs = Article.objects.filter(kind=kind)

        search = self.request.query_params.get("search", "").strip()
        if search:
            return qs.filter(title__icontains=search)[:30]

        category = self.request.query_params.get("category", "").strip()
        specialty = self.request.query_params.get("specialty", "").strip()
        if category and specialty:
            return qs.filter(categories__contains=[{"category": category, "specialty": specialty}])

        # Neither a search term nor a full category+specialty pair -- there
        # is no reasonable "everything" default at this size, so ask for one.
        return Article.objects.none()


class ArticleDetailView(generics.RetrieveAPIView):
    serializer_class = ArticleDetailSerializer
    lookup_field = "slug"
    queryset = Article.objects.all()
