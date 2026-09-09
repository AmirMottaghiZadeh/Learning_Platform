from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from . import services
from .serializers import UptodateArticleSerializer, UptodateTopicSerializer


def _require_available():
    if not services.is_available():
        raise PlatformAPIError(
            "The UpToDate reference is not available.",
            code="FEATURE_NOT_AVAILABLE",
            status_code=503,
        )


class TopicSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter("search", str, description="Clinical topic query."),
            OpenApiParameter("limit", int, description="Max results (default 25)."),
        ],
        responses=UptodateTopicSerializer(many=True),
    )
    def get(self, request):
        _require_available()
        query = request.query_params.get("search", "").strip()
        try:
            limit = min(50, max(1, int(request.query_params.get("limit", 25))))
        except ValueError:
            limit = 25
        results = services.search_topics(query, limit=limit) if query else []
        return Response(UptodateTopicSerializer(results, many=True).data)


class TopicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UptodateArticleSerializer)
    def get(self, request, content_id):
        _require_available()
        article = services.get_topic(content_id)
        if article is None:
            raise PlatformAPIError("No such topic.", code="NOT_FOUND", status_code=404)
        return Response(UptodateArticleSerializer(article).data)
