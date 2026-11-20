"""Authenticated NDJSON transport. Reconnecting never starts another search."""
import asyncio
import json
import time

from asgiref.sync import sync_to_async
from django.core.handlers.asgi import ASGIRequest
from django.core.cache import caches
from django.http import StreamingHttpResponse
from django.db import transaction
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.renderers import BaseRenderer, JSONRenderer
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from apps.core.exceptions import PlatformAPIError
from . import events, jobs, job_store
from .models import SearchRun
from .provider import ProviderError
from .views import require_lab


def line(event):
    return (json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n").encode()


def owned(job_id, user_id):
    record = jobs.read(str(job_id), user_id)
    if not record:
        raise PlatformAPIError("جست‌وجو پیدا نشد.", code="NOT_FOUND", status_code=404)
    return record


def snapshot(job_id, user_id):
    # Read the sequence first. Any event racing with this snapshot is replayed
    # afterwards; source IDs and snapshots make duplicate delivery harmless.
    cursor = events.last_sequence(job_id)
    record = owned(job_id, user_id)
    return {"type": "snapshot", "sequence": cursor, "job": jobs.public(record)}


def synchronous(job_id, user_id, after):
    started = time.monotonic()
    initial = snapshot(job_id, user_id)
    if after is None or initial["job"]["status"] != "running":
        yield line(initial)
        if initial["job"]["status"] != "running":
            return
        after = initial["sequence"]
    while time.monotonic() - started < events.TTL:
        rows = events.read(job_id, after)
        if rows and rows[0]["sequence"] != after + 1:
            repaired = snapshot(job_id, user_id)
            yield line(repaired)
            after = repaired["sequence"]
            if repaired["job"]["status"] != "running":
                return
            continue
        for row in rows:
            after = row["sequence"]
            yield line(row)
            if row["type"] == "complete":
                return
        if not rows:
            repaired = snapshot(job_id, user_id)
            if repaired["job"]["status"] != "running" or repaired["sequence"] < after:
                yield line(repaired)
                return
            yield line({"type": "heartbeat", "sequence": after})


async def asynchronous(job_id, user_id, after):
    started = time.monotonic()
    read_snapshot = sync_to_async(snapshot, thread_sensitive=True)
    initial = await read_snapshot(job_id, user_id)
    if after is None or initial["job"]["status"] != "running":
        yield line(initial)
        if initial["job"]["status"] != "running":
            return
        after = initial["sequence"]
    while time.monotonic() - started < events.TTL:
        rows = await events.read_async(job_id, after)
        if rows and rows[0]["sequence"] != after + 1:
            repaired = await read_snapshot(job_id, user_id)
            yield line(repaired)
            after = repaired["sequence"]
            if repaired["job"]["status"] != "running":
                return
            continue
        for row in rows:
            after = row["sequence"]
            yield line(row)
            if row["type"] == "complete":
                return
        if not rows:
            repaired = await read_snapshot(job_id, user_id)
            if repaired["job"]["status"] != "running" or repaired["sequence"] < after:
                yield line(repaired)
                return
            yield line({"type": "heartbeat", "sequence": after})
        await asyncio.sleep(0)


class StreamView(APIView):
    permission_classes = [IsAuthenticated]

    class NDJSONRenderer(BaseRenderer):
        media_type = "application/x-ndjson"
        format = "ndjson"
        charset = "utf-8"

        def render(self, data, accepted_media_type=None, renderer_context=None):
            return line(data)

    renderer_classes = [NDJSONRenderer, JSONRenderer]

    @extend_schema(parameters=[OpenApiParameter("after_sequence",OpenApiTypes.INT,required=False)],
                   responses={(200,"application/x-ndjson"):OpenApiTypes.BINARY})
    def get(self, request, job_id):
        require_lab(request.user)
        record = owned(job_id, request.user.pk)
        if record.get("pipeline") != "hybrid-v1":
            raise PlatformAPIError("این درخواست از دریافت تدریجی پشتیبانی نمی‌کند.", code="STREAM_UNAVAILABLE", status_code=409)
        raw = request.query_params.get("after_sequence")
        if raw is not None and (not raw.isascii() or not raw.isdigit() or len(raw) > 16):
            raise PlatformAPIError("شمارهٔ رویداد معتبر نیست.", code="INVALID", status_code=400)
        try:
            events.last_sequence(job_id)
        except ProviderError as exc:
            raise PlatformAPIError("دریافت تدریجی موقتاً در دسترس نیست.", code=exc.code, status_code=503) from None
        generator = asynchronous if isinstance(request._request, ASGIRequest) else synchronous
        response = StreamingHttpResponse(generator(str(job_id), request.user.pk, int(raw) if raw is not None else None),
                                         content_type="application/x-ndjson; charset=utf-8")
        response["Cache-Control"] = "private, no-store, no-transform"
        response["X-Accel-Buffering"] = "no"
        response["Content-Encoding"] = "identity"
        return response


class CancellationSerializer(serializers.Serializer):
    cancel_requested = serializers.BooleanField()


class CancelView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=None,responses=CancellationSerializer)
    def post(self, request, job_id):
        require_lab(request.user)
        owned(job_id, request.user.pk)
        with transaction.atomic():
            run = SearchRun.objects.select_for_update().filter(pk=job_id, owner=request.user).first()
            if not run:
                raise PlatformAPIError("این درخواست قابل لغو نیست.", code="NOT_FOUND", status_code=404)
            run.cancel_requested = True
            if run.status in {"admitting", "queued"}:
                run.status = "failed"
                run.finished_at = timezone.now()
                run.encrypted_result = job_store.encode({"status": "failed", "error": {"code": "SEARCH_CANCELLED"}})
            run.save(update_fields=["cancel_requested", "status", "finished_at", "encrypted_result"])
        caches["throttle"].set(f"ai-lab:cancel:{job_id}", True, jobs.TTL)
        if run.status == "failed":
            record = job_store.snapshot(run)
            caches["throttle"].set(f"ai-lab:job:{job_id}", record, jobs.TTL)
            jobs.release(str(job_id), run.owner_id, run.slot or None)
            try:
                events.append(job_id, {"type": "complete", "job": jobs.public(record)})
            except ProviderError:
                pass
        response = Response({"cancel_requested": True})
        response["Cache-Control"] = "private, no-store"
        return response
