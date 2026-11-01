from hashlib import sha256
import re

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError
from apps.billing.enforcement import require_feature

from . import services
from .search_extraction import extract_article
from .serializers import (
    UptodateArticleSerializer,
    UptodateImageSerializer,
    UptodateSearchResultSerializer,
)


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
            OpenApiParameter(
                "search",
                str,
                description=(
                    "Topic title query: every word must start a word of the title; a misspelt word "
                    "is corrected to the closest title word. Article text is never searched."
                ),
            ),
            OpenApiParameter("limit", int, description="Max results (default 25)."),
        ],
        responses=UptodateSearchResultSerializer(many=True),
    )
    def get(self, request):
        _require_available()
        query = request.query_params.get("search", "").strip()
        try:
            limit = min(50, max(1, int(request.query_params.get("limit", 25))))
        except ValueError:
            limit = 25
        results = services.search_topics(query, limit=limit) if query else []
        return Response(UptodateSearchResultSerializer(results, many=True).data)


class TopicDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[
        OpenApiParameter("search_content_hash", str, required=False, description="SHA-256 of the indexed original body HTML."),
        OpenApiParameter("search_anchor", str, required=False, description="Version-specific paragraph anchor."),
    ], responses=UptodateArticleSerializer)
    def get(self, request, content_id):
        content_hash = request.query_params.get("search_content_hash", "")
        anchor = request.query_params.get("search_anchor", "")
        if (content_hash or anchor) and (not re.fullmatch(r"[a-f0-9]{64}", content_hash) or
                                         not re.fullmatch(r"utd-[a-f0-9]{32}", anchor)):
            raise ValidationError("Both a valid search_content_hash and search_anchor are required.")
        _require_available()
        article = services.get_topic(content_id)
        if article is None:
            raise PlatformAPIError("No such topic.", code="NOT_FOUND", status_code=404)
        require_feature(request, "uptodate", item=content_id, consume=True)
        if content_hash:
            if sha256(article["body_html"].encode("utf-8")).hexdigest() != content_hash:
                article["search_anchor_status"] = "stale"
            else:
                try:
                    extracted = extract_article(content_id, article["body_html"])
                except ValueError:
                    article["search_anchor_status"] = "missing"
                else:
                    if any(block.paragraph_id == anchor for block in extracted.blocks):
                        article["body_html"] = extracted.html
                        article["search_anchor_status"] = "matched"
                    else:
                        article["search_anchor_status"] = "missing"
        return Response(UptodateArticleSerializer(article).data)


class ImageDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UptodateImageSerializer)
    def get(self, request, image_id):
        _require_available()
        require_feature(request, "uptodate")
        image = services.get_image(image_id)
        if image is None:
            raise PlatformAPIError("No such image.", code="NOT_FOUND", status_code=404)
        return Response(UptodateImageSerializer(image).data)
