import time

from django.conf import settings
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
    include_database = True

    @extend_schema(responses=HealthCheckSerializer)
    def get(self, request):
        database_status = "ok"
        database_latency_ms = None

        if self.include_database:
            started_at = time.monotonic()
            try:
                connection.ensure_connection()
                with connection.cursor() as cursor:
                    cursor.execute("SELECT 1")
                    cursor.fetchone()
                database_latency_ms = round((time.monotonic() - started_at) * 1000, 2)
            except OperationalError:
                database_status = "unavailable"
                database_latency_ms = round((time.monotonic() - started_at) * 1000, 2)
        else:
            database_status = "not_checked"

        overall_status = "ok" if database_status in {"ok", "not_checked"} else "degraded"

        return Response(
            {
                "status": overall_status,
                "service": "learning-platform-api",
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
                "release_sha": settings.RELEASE_SHA,
                "time": timezone.now().isoformat(),
                "checks": {
                    "database": database_status,
                    "database_latency_ms": database_latency_ms,
                },
            },
            status=200 if overall_status == "ok" else 503,
        )


class LivenessCheckView(HealthCheckView):
    include_database = False
