from django.conf import settings
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .health import check_broker, check_cache, check_database
from .serializers import HealthCheckSerializer, ReadinessCheckSerializer


class HealthCheckView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    include_database = True

    def envelope(self, *, status, checks):
        return {
            "status": status,
            "service": "learning-platform-api",
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "release_sha": settings.RELEASE_SHA,
            "time": timezone.now().isoformat(),
            "checks": checks,
        }

    @extend_schema(responses=HealthCheckSerializer)
    def get(self, request):
        if self.include_database:
            database_status, database_latency_ms = check_database()
        else:
            database_status, database_latency_ms = "not_checked", None

        overall_status = "ok" if database_status in {"ok", "not_checked"} else "degraded"

        return Response(
            self.envelope(
                status=overall_status,
                checks={
                    "database": database_status,
                    "database_latency_ms": database_latency_ms,
                },
            ),
            status=200 if overall_status == "ok" else 503,
        )


class LivenessCheckView(HealthCheckView):
    """Process liveness only: never fails on a dependency outage."""

    include_database = False


class ReadinessCheckView(HealthCheckView):
    """Readiness across the dependencies a request actually needs.

    The database and — once Redis is configured — the shared cache are hard
    requirements: without them authentication and throttling are degraded.
    """

    @extend_schema(responses=ReadinessCheckSerializer)
    def get(self, request):
        database_status, database_latency_ms = check_database()
        cache_status, cache_latency_ms = check_cache()
        broker_status, broker_latency_ms = check_broker()

        checks = {
            "database": database_status,
            "database_latency_ms": database_latency_ms,
            "cache": cache_status,
            "cache_latency_ms": cache_latency_ms,
            "broker": broker_status,
            "broker_latency_ms": broker_latency_ms,
        }

        blocking = [database_status != "ok"]
        if settings.READINESS_REQUIRE_CACHE:
            blocking.append(cache_status != "ok")
        if settings.READINESS_REQUIRE_BROKER:
            blocking.append(broker_status != "ok")

        overall_status = "degraded" if any(blocking) else "ok"

        return Response(
            self.envelope(status=overall_status, checks=checks),
            status=200 if overall_status == "ok" else 503,
        )
