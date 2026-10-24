"""Dependency probes shared by the health endpoints and ops tooling."""

import logging
import time
import uuid

from django.conf import settings
from django.core.cache import caches
from django.db import OperationalError, connection


logger = logging.getLogger(__name__)


def _timed(probe):
    started_at = time.monotonic()
    try:
        probe()
    except Exception as exc:
        return "unavailable", round((time.monotonic() - started_at) * 1000, 2), exc
    return "ok", round((time.monotonic() - started_at) * 1000, 2), None


def check_database():
    def probe():
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()

    status, latency, exc = _timed(probe)
    if isinstance(exc, OperationalError) or exc is not None:
        return "unavailable", latency
    return status, latency


def check_cache(alias="default"):
    """Round-trip a unique value so a misconfigured backend cannot pass."""
    probe_key = f"ops:readiness:{uuid.uuid4().hex}"

    def probe():
        cache = caches[alias]
        cache.set(probe_key, "1", timeout=10)
        if cache.get(probe_key) != "1":
            raise RuntimeError(f"Cache alias {alias} did not return the stored value.")
        cache.delete(probe_key)

    status, latency, _ = _timed(probe)
    return status, latency


def check_broker():
    """Open a real broker connection. ``memory://`` reports as not configured."""
    broker_url = getattr(settings, "CELERY_BROKER_URL", "") or ""
    if not broker_url or broker_url.startswith("memory://"):
        return "not_configured", None

    def probe():
        from config.celery import app as celery_app

        connection_obj = celery_app.connection(broker_url)
        try:
            connection_obj.ensure_connection(max_retries=0, timeout=2)
        finally:
            connection_obj.release()

    status, latency, _ = _timed(probe)
    return status, latency
