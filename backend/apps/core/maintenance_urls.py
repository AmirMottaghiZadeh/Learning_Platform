from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def maintenance_response(request, *args, **kwargs):
    """Stable 503 for a feature that is built but switched off."""
    return JsonResponse(
        {
            "code": "FEATURE_NOT_AVAILABLE",
            "message": "This feature is not available yet.",
            "details": {},
        },
        status=503,
    )
