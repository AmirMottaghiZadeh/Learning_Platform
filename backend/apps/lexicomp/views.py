from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.billing.enforcement import require_feature

from . import services
from .serializers import (
    InteractionCheckRequestSerializer,
    LexicompDrugSerializer,
    LexicompInteractionSerializer,
)


def _require_available():
    if not services.is_available():
        raise PlatformAPIError(
            "The Lexicomp reference is not available.",
            code="FEATURE_NOT_AVAILABLE",
            status_code=503,
        )


class DrugSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="Drug generic or brand name."),
            OpenApiParameter("limit", int, description="Max results (default 20)."),
        ],
        responses=LexicompDrugSerializer(many=True),
    )
    def get(self, request):
        _require_available()
        query = request.query_params.get("search", "").strip()
        try:
            limit = min(50, max(1, int(request.query_params.get("limit", 20))))
        except ValueError:
            limit = 20
        results = services.search_drugs(query, limit=limit) if query else []
        return Response(LexicompDrugSerializer(results, many=True).data)


class InteractionCheckView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=InteractionCheckRequestSerializer,
        responses=LexicompInteractionSerializer(many=True),
    )
    def post(self, request):
        _require_available()
        body = InteractionCheckRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        ids = body.validated_data["generic_ids"]
        require_feature(request, "lexicomp", item=",".join(sorted(map(str, ids))), consume=True)
        results = services.check_interactions(ids)
        return Response(LexicompInteractionSerializer(results, many=True).data)
