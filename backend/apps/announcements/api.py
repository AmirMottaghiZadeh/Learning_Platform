"""The app's announcements: what to show this learner now, and what they did
with each (seen, button pressed, closed)."""

from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .models import AppAnnouncement


class ButtonSerializer(serializers.Serializer):
    label = serializers.CharField()
    # "url": open `url`; "app": go to `screen` (with `param`) in the app
    kind = serializers.ChoiceField(choices=["url", "app"])
    url = serializers.CharField(allow_blank=True)
    screen = serializers.CharField(allow_blank=True)
    param = serializers.CharField(allow_blank=True)


class AnnouncementSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    body = serializers.CharField()
    kind = serializers.ChoiceField(choices=[k for k, _ in AppAnnouncement.KIND_CHOICES])
    kind_label = serializers.CharField()
    button = ButtonSerializer(allow_null=True)
    dismissible = serializers.BooleanField()
    pinned = serializers.BooleanField()
    # False until the app reports it shown: an unseen one opens dimmed
    seen = serializers.BooleanField()
    starts_at = serializers.DateTimeField()
    is_test = serializers.BooleanField()


def as_item(item, receipt):
    button = None
    if item.has_button:
        button = {
            "label": item.cta_label, "kind": item.link_kind,
            "url": item.link_url if item.link_kind == AppAnnouncement.LINK_URL else "",
            "screen": item.link_screen if item.link_kind == AppAnnouncement.LINK_APP else "",
            "param": item.link_param if item.link_kind == AppAnnouncement.LINK_APP else "",
        }
    return {
        "id": item.pk, "title": item.title, "body": item.body, "kind": item.kind, "kind_label": item.get_kind_display(),
        "button": button, "dismissible": item.dismissible, "pinned": item.is_pinned,
        "seen": bool(receipt and receipt.seen_at), "starts_at": item.starts_at or item.created_at,
        "is_test": not item.is_published,
    }


class AnnouncementListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter("version_code", int, description="The installed app's version code, for notices to old versions.")],
        responses=AnnouncementSerializer(many=True),
    )
    def get(self, request):
        raw = request.query_params.get("version_code", "")
        app_code = int(raw) if raw.isdigit() else None
        rows = [as_item(item, receipt) for item, receipt in services.for_user(request.user, app_code)]
        return Response(AnnouncementSerializer(rows, many=True).data)


class EventSerializer(serializers.Serializer):
    event = serializers.ChoiceField(choices=services.EVENTS)


class AnnouncementEventView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=EventSerializer, responses={204: None})
    def post(self, request, pk):
        body = EventSerializer(data=request.data)
        body.is_valid(raise_exception=True)
        visible = {item.pk: item for item, _ in services.for_user(request.user, None)}
        # an old-version notice is hidden here (no version given) but may be on screen
        item = visible.get(pk) or get_object_or_404(AppAnnouncement, pk=pk, is_published=True)
        services.record(request.user, item, body.validated_data["event"])
        return Response(status=204)
