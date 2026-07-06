from django.db import OperationalError, connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import HealthCheckSerializer


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(responses=HealthCheckSerializer)
    def get(self, request):
        database_status = "ok"

        try:
            connection.ensure_connection()
        except OperationalError:
            database_status = "unavailable"

        overall_status = "ok" if database_status == "ok" else "degraded"

        return Response(
            {
                "status": overall_status,
                "service": "learning-platform-api",
                "version": "v1",
                "time": timezone.now().isoformat(),
                "checks": {
                    "database": database_status,
                },
            },
            status=200 if overall_status == "ok" else 503,
        )
