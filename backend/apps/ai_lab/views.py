from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock, Thread
import time
from types import SimpleNamespace
from uuid import uuid4

from django.conf import settings
from django.core.cache import caches
from django.db import close_old_connections
from django.views.decorators.debug import sensitive_post_parameters, sensitive_variables
from django.utils.decorators import method_decorator
from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from apps.core.exceptions import PlatformAPIError
from .access import allowed
from .provider import MODEL_ALIASES, ProviderError, configured_models
from .retrieval import SOURCES
from .services import answer
from . import jobs
from .workflow import apply_event

_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="reference-lab")
TTL = jobs.TTL


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=1500)
    model = serializers.ChoiceField(choices=list(MODEL_ALIASES))
    sources = serializers.ListField(child=serializers.ChoiceField(choices=list(SOURCES)), min_length=1, max_length=1,
                                    default=lambda: ["uptodate"])
    history = serializers.ListField(child=serializers.CharField(max_length=1500), max_length=4, default=list)

    def validate_sources(self, value):
        return list(dict.fromkeys(value))

    def validate_question(self, value):
        import re
        if re.search(r"sk-[A-Za-z0-9_-]{16,}", value):
            raise serializers.ValidationError("کلید API را در گفت‌وگو وارد نکنید.")
        return value

    def validate_history(self, value):
        for question in value:
            self.validate_question(question)
        return value


def require_lab(user):
    if not settings.AI_LAB_ENABLED or not allowed(user):
        raise PlatformAPIError("سرچ هوشمند برای حساب شما فعال نیست.", code="AI_LAB_DISABLED", status_code=403)


@sensitive_variables()
def _run(job_id, user, payload, slot):
    cache = caches["throttle"]
    key = f"ai-lab:job:{job_id}"
    close_old_connections()
    stopped, state_lock = Event(), Lock()
    def touch(stage=None):
        record = jobs.read(job_id, user.pk)
        if not record or record.get("status") != "running":
            raise ProviderError("EXPERIMENT_EXPIRED")
        record["heartbeat_at"] = time.time()
        if stage and record.get("stage") != stage:
            record["stage"] = stage
            seen = record.setdefault("stages_seen", [])
            if stage not in seen:
                seen.append(stage)
            record["revision"] = record.get("revision", 0) + 1
        cache.set(key, record, TTL)
    def progress(stage):
        with state_lock:
            touch(stage)
    def heartbeat():
        while not stopped.wait(10):
            try:
                with state_lock:
                    if stopped.is_set():
                        return
                    touch()
            except Exception:
                return
    def publish(event):
        with state_lock:
            record = jobs.read(job_id, user.pk)
            if not record or record.get("status") != "running":
                raise ProviderError("EXPERIMENT_EXPIRED")
            findings = list(record.get("findings", []))
            seen = {finding["id"] for finding in findings}
            for citation in event["citations"]:
                finding_id = f'{event["part_index"]}:{event["article_id"]}:{citation["source_id"]}'
                if finding_id in seen:
                    continue
                if len(findings) >= jobs.MAX_FINDINGS:
                    record["findings_limited"] = True
                    break
                findings.append({"id": finding_id, "sequence": len(findings) + 1, "part_index": event["part_index"],
                    "question_fa": event["question_fa"], "article_id": event["article_id"],
                    "published_at": time.time(), "citation": citation})
                seen.add(finding_id)
            if findings:
                record.setdefault("first_result_ms", max(0, round((time.time() - record["created_at"]) * 1000)))
            record.update(findings=findings, heartbeat_at=time.time(), revision=record.get("revision", 0) + 1)
            cache.set(key, record, TTL)
    def observe(event):
        with state_lock:
            record = jobs.read(job_id, user.pk)
            if not record or record.get("status") != "running":
                raise ProviderError("EXPERIMENT_EXPIRED")
            record.update(workflow=apply_event(record.get("workflow", []), event),
                          heartbeat_at=time.time(), revision=record.get("revision", 0) + 1)
            cache.set(key, record, TTL)
    def finish(values):
        with state_lock:
            stopped.set()
            record = jobs.read(job_id, user.pk)
            if record and record.get("status") == "running":
                cache.set(key, {**record, **values, "revision": record.get("revision", 0) + 1}, TTL)
    try:
        progress("starting")
        Thread(target=heartbeat, daemon=True, name="reference-lab-heartbeat").start()
        result = answer(payload["question"], payload["model"], payload["sources"], payload["history"],
                        SimpleNamespace(user=user), progress, publish, observe)
        finish({"status": "complete", "result": result})
    except ProviderError as exc:
        finish({"status": "failed", "error": {
            "code": exc.code, "provider_status": exc.status,
            "model": getattr(exc, "model", configured_models().get(payload["model"])),
        }})
    except Exception:
        finish({"status": "failed", "error": {"code": "EXPERIMENT_FAILED"}})
    finally:
        stopped.set()
        jobs.release(job_id, user.pk, slot)
        close_old_connections()


class LabStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=dict)
    def get(self, request):
        response = Response({"enabled": settings.AI_LAB_ENABLED and allowed(request.user), "models": configured_models(),
                             "sources": SOURCES})
        response["Cache-Control"] = "private, no-store"
        return response


class ActiveView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=dict)
    def get(self, request):
        require_lab(request.user)
        response = Response({"active_job": jobs.active(request.user.pk)})
        response["Cache-Control"] = "private, no-store"
        return response


@method_decorator(sensitive_post_parameters(), name="dispatch")
class AskView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(request=AskSerializer, responses={202: dict})
    def post(self, request):
        require_lab(request.user)
        serializer = AskSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        cache, job_id = caches["throttle"], str(uuid4())
        user_lock = f"ai-lab:user:{request.user.pk}"
        now = time.time()
        cache.set(f"ai-lab:job:{job_id}", {"user_id": request.user.pk, "status": "running", "stage": "starting",
            "revision": 0, "findings": [], "findings_limited": False, "workflow": [], "stages_seen": ["starting"],
            "created_at": now, "heartbeat_at": now, "question": serializer.validated_data["question"],
            "model": serializer.validated_data["model"], "sources": serializer.validated_data["sources"]}, TTL)
        previous = jobs.active(request.user.pk)
        if previous or not cache.add(user_lock, job_id, jobs.LEASE):
            cache.delete(f"ai-lab:job:{job_id}")
            raise PlatformAPIError("جست‌وجوی قبلی هنوز در حال اجراست.", code="AI_LAB_BUSY", status_code=429,
                                   details={"job_id": previous["job_id"]} if previous else {})
        slot = None
        try:
            for n in range(2):
                candidate = f"ai-lab:slot:{n}"
                owner = cache.get(candidate)
                if owner:
                    record = cache.get(f"ai-lab:job:{owner}")
                    if record:
                        jobs.read(owner, record["user_id"])
                    if not record or record.get("status") != "running":
                        if cache.get(candidate) == owner:
                            cache.delete(candidate)
                if cache.add(candidate, job_id, jobs.LEASE):
                    slot = candidate
                    break
            if slot is None:
                raise PlatformAPIError("ظرفیت جست‌وجوی هم‌زمان پر است؛ کمی بعد تلاش کنید.", code="AI_LAB_BUSY", status_code=429)
            from django.utils import timezone
            quota = f"ai-lab:budget:{request.user.pk}:{timezone.now():%Y%m%d%H}"
            cache.add(quota, 0, 3700)
            if cache.incr(quota) > 20:
                raise PlatformAPIError("سقف ۲۰ جست‌وجو در ساعت پر شده است.", code="AI_LAB_LIMIT", status_code=429)
            _executor.submit(_run, job_id, request.user, serializer.validated_data, slot)
        except Exception:
            cache.delete(f"ai-lab:job:{job_id}")
            cache.delete(user_lock)
            if slot:
                cache.delete(slot)
            raise
        response = Response({"job_id": job_id}, status=202)
        response["Cache-Control"] = "private, no-store"
        return response


class ResultView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=dict)
    def get(self, request, job_id):
        require_lab(request.user)
        record = jobs.read(str(job_id), request.user.pk)
        if not record:
            raise PlatformAPIError("جست‌وجو پیدا نشد یا منقضی شده است.", code="NOT_FOUND", status_code=404)
        response = Response(jobs.public(record, request.query_params.get("after_revision")))
        response["Cache-Control"] = "private, no-store"
        return response
