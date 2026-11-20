import re
from datetime import timedelta

from django.conf import settings
from django.http import FileResponse, Http404, HttpResponse, StreamingHttpResponse
from django.utils import timezone
from django.views import View
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.exceptions import PlatformAPIError

from . import services, storage
from .pack import DATASETS, PackError, build_matches_dataset
from .serializers import (
    LicenseRequestSerializer,
    LicenseSerializer,
    OfflinePackageSerializer,
    PackageUrlsRequestSerializer,
    PackageUrlsSerializer,
)


def _url_ttl() -> int:
    return int(getattr(settings, "OFFLINE_URL_TTL_SECONDS", 24 * 3600))


def _dataset(value):
    if value not in DATASETS:
        raise PlatformAPIError("No such offline package.", code="NOT_FOUND", status_code=404)
    return value


def _require_entitled(request, dataset):
    if not services.is_entitled(request.user, dataset):
        raise PlatformAPIError(
            "Offline download needs a paid plan that includes this reference.",
            code="PREMIUM_REQUIRED",
            status_code=402,
            details={"feature": services.FEATURE_FOR[dataset], "reason": "offline_paid_plan"},
        )


def _require_manifest(dataset):
    manifest = storage.latest_manifest(dataset)
    if manifest is None:
        raise PlatformAPIError(
            "This offline package has not been published yet.",
            code="FEATURE_NOT_AVAILABLE",
            status_code=503,
        )
    return manifest


class PackageListView(APIView):
    """The packages there are to download, with whether this learner may."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=OfflinePackageSerializer(many=True))
    def get(self, request):
        rows = [
            {
                "dataset": dataset,
                "entitled": services.is_entitled(request.user, dataset),
                "license_days": services.license_days(),
                "package": storage.latest_manifest(dataset),
            }
            for dataset in DATASETS
        ]
        return Response(OfflinePackageSerializer(rows, many=True).data)


class PackageUrlsView(APIView):
    """Short-lived download links for every part of a build (the latest one
    unless the app is finishing an older build it already started)."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=PackageUrlsRequestSerializer, responses=PackageUrlsSerializer)
    def post(self, request, dataset):
        dataset = _dataset(dataset)
        _require_entitled(request, dataset)
        manifest = _require_manifest(dataset)
        body = PackageUrlsRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        build = body.validated_data.get("build") or manifest["build"]
        if build != manifest["build"]:
            # An older build is only served while it is still the one
            # published: the parts of a replaced build may be gone.
            raise PlatformAPIError(
                "A newer version of this package was published.",
                code="PACKAGE_REPLACED",
                status_code=409,
                details={"build": manifest["build"]},
            )
        ttl = _url_ttl()
        urls = storage.file_urls(request, dataset, build, [f["name"] for f in manifest["files"]], ttl)
        return Response(
            PackageUrlsSerializer(
                {
                    "build": build,
                    "expires_at": (timezone.now() + timedelta(seconds=ttl)).isoformat(),
                    "files": [{**f, "url": urls[f["name"]]} for f in manifest["files"]],
                }
            ).data
        )


class LicenseView(APIView):
    """The key of a build the learner has downloaded, valid for
    OFFLINE_LICENSE_DAYS; the app renews it whenever it is online."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=LicenseRequestSerializer, responses=LicenseSerializer)
    def post(self, request, dataset):
        dataset = _dataset(dataset)
        _require_entitled(request, dataset)
        body = LicenseRequestSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        build = body.validated_data["build"]
        if not build_matches_dataset(build, dataset):
            raise PlatformAPIError("Unknown build.", code="NOT_FOUND", status_code=404)
        try:
            license = services.issue_license(build, body.validated_data.get("public_key", ""))
        except services.LicenseError as exc:
            raise PlatformAPIError(str(exc), code="VALIDATION_ERROR", status_code=400)
        except PackError:
            raise PlatformAPIError(
                "Offline packages are not configured on the server.",
                code="FEATURE_NOT_AVAILABLE",
                status_code=503,
            )
        return Response(LicenseSerializer(license).data)


_RANGE_RE = re.compile(r"^bytes=(\d+)-(\d*)$")


class PackageFileView(View):
    """Development stand-in for the bucket (OFFLINE_PACKAGES_DIR): one part
    file behind a signed, expiring token, with single-range support so
    downloads resume the way they do against S3. The token is the only
    credential, as with a presigned link."""

    def _cors(self, response):
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Headers"] = "Range"
        response["Access-Control-Expose-Headers"] = "Content-Length, Content-Range, Accept-Ranges"
        return response

    def options(self, request, token):
        return self._cors(HttpResponse(status=204))

    def get(self, request, token):
        path = storage.local_file_for_token(token, _url_ttl())
        if path is None:
            raise Http404
        size = path.stat().st_size
        match = _RANGE_RE.match(request.headers.get("Range", ""))
        if not match:
            response = FileResponse(path.open("rb"), content_type="application/octet-stream")
            response["Accept-Ranges"] = "bytes"
            return self._cors(response)
        start = int(match.group(1))
        end = min(int(match.group(2)) if match.group(2) else size - 1, size - 1)
        if start > end:
            response = HttpResponse(status=416)
            response["Content-Range"] = f"bytes */{size}"
            return self._cors(response)

        def chunks():
            with path.open("rb") as fh:
                fh.seek(start)
                left = end - start + 1
                while left > 0:
                    data = fh.read(min(1024 * 1024, left))
                    if not data:
                        break
                    left -= len(data)
                    yield data

        response = StreamingHttpResponse(chunks(), status=206, content_type="application/octet-stream")
        response["Content-Length"] = str(end - start + 1)
        response["Content-Range"] = f"bytes {start}-{end}/{size}"
        response["Accept-Ranges"] = "bytes"
        return self._cors(response)
