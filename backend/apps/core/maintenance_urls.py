from django.http import JsonResponse
def maintenance_response(request, *args, **kwargs):
    return JsonResponse(
        {
            "code": "FEATURE_TEMPORARILY_DISABLED",
            "message": "This feature is temporarily disabled during the phase 0 release freeze.",
            "details": {},
        },
        status=503,
    )
