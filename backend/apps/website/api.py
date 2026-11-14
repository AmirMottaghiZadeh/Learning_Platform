"""What the site's data serves to the app: whether an installed app should
update (frontend UpdatePrompt), from the releases entered in the panel
(/panel/releases/) with «پیشنهاد به‌روزرسانی در اپ»; and the terms and the
privacy page, shown in the app's sign-up screen."""

import re

from django.conf import settings
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.urls import reverse
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SITE_URLCONF, AppRelease, Page, version_code
from .sanitize import plain_text

_BLOCK_END = re.compile(r"<br\s*/?>|</(?:p|li|h[1-6]|div|blockquote)>", re.I)


def note_lines(html):
    """A release's notes as plain lines: one per paragraph or list item."""
    return [line for line in (plain_text(chunk) for chunk in _BLOCK_END.split(html or "")) if line]


class ReleaseQuerySerializer(serializers.Serializer):
    platform = serializers.ChoiceField(choices=[AppRelease.ANDROID, AppRelease.IOS])
    version_code = serializers.IntegerField(min_value=0)


class LatestReleaseSerializer(serializers.Serializer):
    version = serializers.CharField()
    version_code = serializers.IntegerField()
    notes = serializers.ListField(child=serializers.CharField())
    released_at = serializers.DateField()
    download_url = serializers.URLField()


class ReleaseCheckSerializer(serializers.Serializer):
    update = serializers.ChoiceField(choices=["none", "optional", "required"])
    latest = LatestReleaseSerializer(allow_null=True)


class ReleaseCheckView(APIView):
    """For the app of `version_code` (frontend/src/utils/appVersion) on
    `platform`: "required" below the strictest minimum supported version of
    the notified releases, "optional" below the newest of them, else
    "none". The update button leads to the site's download page, which has
    every store's link. Public, so the app can ask before anyone signs in."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        parameters=[
            OpenApiParameter("platform", str, enum=[AppRelease.ANDROID, AppRelease.IOS]),
            OpenApiParameter("version_code", int),
        ],
        responses=ReleaseCheckSerializer,
    )
    def get(self, request):
        query = ReleaseQuerySerializer(data=request.query_params)
        query.is_valid(raise_exception=True)
        installed = query.validated_data["version_code"]

        notified = []
        for release in AppRelease.objects.filter(
            platform=query.validated_data["platform"], channel=AppRelease.STABLE, is_published=True, notify_in_app=True,
        ):
            # The panel form only lets SemVer through; skip anything older.
            try:
                code = version_code(release.version)
                minimum = version_code(release.min_supported_version) if release.min_supported_version else 0
            except ValueError:
                continue
            notified.append((code, minimum, release))
        if not notified:
            return Response({"update": "none", "latest": None})

        code, _, latest = max(notified, key=lambda n: n[0])
        minimum = max(n[1] for n in notified)
        if installed >= code:
            update = "none"
        elif installed < minimum:
            update = "required"
        else:
            update = "optional"
        return Response({
            "update": update,
            "latest": {
                "version": latest.version,
                "version_code": code,
                "notes": note_lines(latest.notes_html),
                "released_at": latest.released_at,
                "download_url": settings.SITE_PUBLIC_URL.rstrip("/") + reverse("site:download", urlconf=SITE_URLCONF),
            },
        })


# The pages a sign-up accepts. Their text is the site's (edited in the panel),
# so the app and the site never show two versions.
LEGAL_PAGES = ("terms", "privacy")


class LegalPageSerializer(serializers.Serializer):
    title = serializers.CharField()
    body_html = serializers.CharField()
    updated_at = serializers.DateTimeField()


class LegalPageView(APIView):
    """The terms or the privacy page, published, for the sign-up screen.
    Public: it is read before anyone has an account."""

    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=LegalPageSerializer)
    def get(self, request, slug):
        if slug not in LEGAL_PAGES:
            raise Http404
        page = get_object_or_404(Page, slug=slug, status=Page.PUBLISHED)
        return Response(LegalPageSerializer(page).data)
