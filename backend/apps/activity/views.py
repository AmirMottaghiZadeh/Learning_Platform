from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from .models import ActivityEvent
from .serializers import EventBatchSerializer, ActivityReceiptSerializer
import hashlib
import json
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST


class EventBatchView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_scope = "sustained"

    @extend_schema(request=EventBatchSerializer, responses={202: ActivityReceiptSerializer})
    def post(self, request):
        data = EventBatchSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        ActivityEvent.objects.bulk_create([
            ActivityEvent(user=request.user, source="app", visitor=str(request.auth.pk), **row)
            for row in data.validated_data["events"]
        ], ignore_conflicts=True)
        return Response({"accepted": len(data.validated_data["events"])}, status=202)


@require_POST
def site_clicks(request):
    from apps.website.services import throttle
    from .serializers import SiteClickBatchSerializer

    if len(request.body) > 12000:
        return JsonResponse({"error": "event_batch_too_large"}, status=400)
    if not throttle(request, "activity_clicks", 120, 60):
        return JsonResponse({"error": "rate_limited"}, status=429)
    try:
        payload = json.loads(request.body)
    except (ValueError, UnicodeDecodeError):
        return JsonResponse({"error": "invalid_json"}, status=400)
    data = SiteClickBatchSerializer(data=payload)
    if not data.is_valid():
        return JsonResponse({"error": "invalid_events"}, status=400)
    device = getattr(request, "browser_device_id", "")
    visitor = hashlib.sha256((settings.SECRET_KEY + device).encode()).hexdigest()
    ActivityEvent.objects.bulk_create([ActivityEvent(user=request.user if request.user.is_authenticated else None, source="site", visitor=visitor, **row) for row in data.validated_data["events"]], ignore_conflicts=True)
    return JsonResponse({"accepted": len(data.validated_data["events"])}, status=202)
