from hashlib import sha256
import re

from django.http import HttpResponse

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
    UptodateSearchPageSerializer,
    UptodateSearchResultSerializer,
)


def _require_available():
    if not services.is_available():
        raise PlatformAPIError(
            "The UpToDate reference is not available.",
            code="FEATURE_NOT_AVAILABLE",
            status_code=503,
        )


def _int_param(request, name, default, low, high):
    try:
        return min(high, max(low, int(request.query_params.get(name, default))))
    except ValueError:
        return default


class TopicSearchView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "search",
                str,
                description=(
                    "Snapshot concepts, aliases and curated topic associations, with title matching "
                    "and typo correction as fallback. Article body text is never searched."
                ),
            ),
            OpenApiParameter("limit", int, description="Max results (default 25, at most 100)."),
            OpenApiParameter("offset", int, description="Results to skip (paged=1 only)."),
            OpenApiParameter("section", str, description="Only this section's topics (paged=1 only)."),
            OpenApiParameter(
                "paged",
                int,
                description=(
                    "1: answer {total, all, sections, terms, corrected, suggestions, results}; "
                    "otherwise the first page alone, as a list (app builds up to 0.1.x)."
                ),
            ),
        ],
        responses=UptodateSearchResultSerializer(many=True),
    )
    def get(self, request):
        _require_available()
        query = request.query_params.get("search", "").strip()
        limit = _int_param(request, "limit", 25, 1, 100)
        if request.query_params.get("paged") != "1":
            results = services.search_topics(query, limit=min(limit, 50)) if query else []
            return Response(UptodateSearchResultSerializer(results, many=True).data)
        offset = _int_param(request, "offset", 0, 0, 100_000)
        section = request.query_params.get("section", "").strip()[:200]
        page = services.search_page(query, limit=limit, offset=offset, section=section) if query else {
            "total": 0, "all": 0, "sections": [], "terms": [], "corrected": "", "results": [],
        }
        return Response(UptodateSearchPageSerializer(page).data)


class SearchMetadataView(APIView):
    """Encrypted search-only upgrade for an installed older offline package."""

    permission_classes = [IsAuthenticated]

    @extend_schema(parameters=[OpenApiParameter("build", str), OpenApiParameter("version", str)],
                   responses={(200, "application/octet-stream"): bytes})
    def get(self, request):
        from apps.offline import services as offline_services
        from apps.offline.pack import PackError, build_matches_dataset, derive_key, seal

        build = request.query_params.get("build", "")
        if not build_matches_dataset(build, "uptodate"):
            raise ValidationError("A valid UpToDate package build is required.")
        if not offline_services.is_entitled(request.user, "uptodate"):
            raise PlatformAPIError("Offline access requires a paid plan.", code="PREMIUM_REQUIRED", status_code=402)
        _require_available()
        version = services.snapshot_version()
        if request.query_params.get("version", "") != version or not build.startswith(f"uptodate-{version or 'v'}-"):
            raise PlatformAPIError("The installed snapshot has a different version.", code="PACKAGE_REPLACED", status_code=409)
        if not services._search_catalog(version).queries:
            raise PlatformAPIError("The snapshot search catalog is unavailable.", code="FEATURE_NOT_AVAILABLE", status_code=503)
        try:
            payload = seal(derive_key(build), services.search_metadata_record(version))
        except PackError:
            raise PlatformAPIError("Offline keys are not configured.", code="FEATURE_NOT_AVAILABLE", status_code=503)
        response = HttpResponse(payload, content_type="application/octet-stream")
        response["Cache-Control"] = "private, no-store"
        return response


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
