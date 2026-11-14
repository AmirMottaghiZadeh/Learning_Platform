from concurrent.futures import ThreadPoolExecutor
from threading import Event, Lock, Thread
import time
from types import SimpleNamespace
from uuid import uuid4

from django.conf import settings
from django.core.cache import caches
from django.db import close_old_connections
from django.utils import timezone
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
from . import telemetry
from .workflow import apply_event

_executor = ThreadPoolExecutor(max_workers=max(1, min(16, settings.AI_LAB_MAX_CONCURRENT_JOBS)), thread_name_prefix="reference-lab")
_instance = uuid4().hex
TTL = jobs.TTL


class AskSerializer(serializers.Serializer):
    question = serializers.CharField(min_length=3, max_length=1500)
    model = serializers.ChoiceField(choices=list(MODEL_ALIASES))
    sources = serializers.ListField(child=serializers.ChoiceField(choices=list(SOURCES)), min_length=1, max_length=1,
                                    default=lambda: ["uptodate"])
    history = serializers.ListField(child=serializers.CharField(max_length=1500), max_length=4, default=list)
    request_id = serializers.RegexField(r"^[A-Za-z0-9_.:-]{1,128}$",required=False)

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
def _run(job_id, user, payload, slot, *, durable=False):
    cache = caches["throttle"]
    key = f"ai-lab:job:{job_id}"
    initial = cache.get(key) or {}
    created = initial.get("created_at")
    queue_wait_ms = max(0, (time.time() - created) * 1000) if isinstance(created, (int, float)) else 0
    trace = telemetry.Trace(queue_wait_ms=queue_wait_ms,credit_reservation_id=job_id if durable else None)
    close_old_connections()
    stopped, state_lock = Event(), Lock()
    cancelled = Event()
    delivery_failed = False
    def journal(event):
        nonlocal delivery_failed
        if durable and not delivery_failed:
            from .events import append
            try:
                append(job_id,event)
            except ProviderError:
                # A transport outage must not discard a completed, durable
                # clinical result or replay a paid provider request.
                delivery_failed=True
    def check_cancelled():
        if durable:
            try:
                requested = cache.get(f"ai-lab:cancel:{job_id}")
            except Exception:
                from .models import SearchRun
                requested = SearchRun.objects.filter(pk=job_id,cancel_requested=True).exists()
            if cancelled.is_set() or requested:
                raise ProviderError("SEARCH_CANCELLED")
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
        for lease in [f"ai-lab:user:{user.pk}", slot]:
            if lease and cache.get(lease) == job_id:
                cache.touch(lease, jobs.LEASE)
    def progress(stage):
        check_cancelled()
        with state_lock:
            touch(stage)
    def heartbeat():
        try:
            while not stopped.wait(10):
                try:
                    with state_lock:
                        if stopped.is_set():
                            return
                        touch()
                        if durable:
                            from .models import SearchRun
                            if SearchRun.objects.filter(pk=job_id,cancel_requested=True).exists():
                                cancelled.set()
                            SearchRun.objects.filter(pk=job_id,status="running").update(heartbeat_at=timezone.now())
                except Exception:
                    return
        finally:
            from django.db import connections
            connections.close_all()
    def publish(event):
        check_cancelled()
        with state_lock:
            record = jobs.read(job_id, user.pk)
            if not record or record.get("status") != "running":
                raise ProviderError("EXPERIMENT_EXPIRED")
            findings = list(record.get("findings", []))
            seen = {finding["id"]:index for index,finding in enumerate(findings)}
            changed=[]
            for citation in event["citations"]:
                finding_id = f'{event["part_index"]}:{event["article_id"]}:{citation["source_id"]}'
                if finding_id in seen:
                    index=seen[finding_id]
                    if findings[index]["citation"]!=citation:
                        findings[index]={**findings[index],"citation":citation}
                        changed.append(findings[index])
                    continue
                if len(findings) >= jobs.MAX_FINDINGS:
                    record["findings_limited"] = True
                    break
                findings.append({"id": finding_id, "sequence": len(findings) + 1, "part_index": event["part_index"],
                    "question_fa": event["question_fa"], "article_id": event["article_id"],
                    "published_at": time.time(), "citation": citation})
                seen[finding_id]=len(findings)-1
                changed.append(findings[-1])
            if findings:
                record.setdefault("first_result_ms", max(0, round((time.time() - record["created_at"]) * 1000)))
            record.update(findings=findings, heartbeat_at=time.time(), revision=record.get("revision", 0) + 1)
            cache.set(key, record, TTL)
            if changed:
                journal({"type":"sources","findings":changed})
    def observe(event):
        with state_lock:
            record = jobs.read(job_id, user.pk)
            if not record or record.get("status") != "running":
                raise ProviderError("EXPERIMENT_EXPIRED")
            record.update(workflow=apply_event(record.get("workflow", []), event),
                          heartbeat_at=time.time(), revision=record.get("revision", 0) + 1)
            cache.set(key, record, TTL)
    def finish(values):
        result = values.get("result") or {}
        if values.get("status") == "complete":
            from apps.ai_feedback.services import save_answer
            # Durable jobs already contain the trusted final snapshot. The
            # separate feedback DB is populated by its authenticated endpoint,
            # so its connection latency cannot delay the clinical answer.
            values["feedback_available"] = bool(settings.AI_LAB_FEEDBACK_ENABLED) if durable else save_answer(job_id, user, payload["question"], result)
        parts = result.get("parts", [])
        trace.finish(values["status"], answer_complete=bool(parts) and all(
            part.get("status") == "answered" and part.get("items") for part in parts))
        if durable:
            from apps.ai_wallet.services import settle
            settle(job_id,outcome=values["status"])
        with state_lock:
            stopped.set()
            record = jobs.read(job_id, user.pk)
            if record and record.get("status") == "running":
                record={**record, **values, "metrics": trace.snapshot(), "revision": record.get("revision", 0) + 1}
                if durable:
                    from .models import SearchRun
                    from .job_store import encode
                    SearchRun.objects.filter(pk=job_id).update(status=values["status"],finished_at=timezone.now(),
                        heartbeat_at=timezone.now(),encrypted_result=encode(jobs.public(record)))
                try:
                    cache.set(key,record,TTL)
                except Exception:
                    if not durable:
                        raise
                journal({"type":"complete","job":jobs.public(record)})
    def stream_event(event):
        check_cancelled()
        if not durable:
            return
        if event["type"] in {"answer_delta","answer_reset"} and settings.AI_LAB_STREAM_ANSWER_DRAFTS:
            with state_lock:
                record=jobs.read(job_id,user.pk)
                if not record or record.get("status")!="running":
                    raise ProviderError("EXPERIMENT_EXPIRED")
                drafts=record.setdefault("answer_drafts",{})
                index=str(event["part_index"])
                drafts[index]="" if event["type"]=="answer_reset" else drafts.get(index,"")+event["text"]
                cache.set(key,record,TTL)
            journal(event)
    try:
        progress("starting")
        Thread(target=heartbeat, daemon=True, name="reference-lab-heartbeat").start()
        with trace.activate():
            kwargs={"on_event":stream_event,"check_cancelled":check_cancelled} if durable else {}
            result = answer(payload["question"], payload["model"], payload["sources"], payload["history"],
                            SimpleNamespace(user=user), progress, publish, observe,**kwargs)
            check_cancelled()
        finish({"status": "complete", "result": result})
    except ProviderError as exc:
        finish({"status": "failed", "error": {
            "code": exc.code, "provider_status": exc.status,
            "model": getattr(exc, "model", configured_models().get(payload["model"])),
        }})
    except Exception:
        finish({"status": "failed", "error": {"code": "EXPERIMENT_FAILED"}})
    finally:
        trace.finish("failed")
        telemetry.log_summary(trace)
        stopped.set()
        jobs.release(job_id, user.pk, slot)
        close_old_connections()


class LabStatusView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=dict)
    def get(self, request):
        response = Response({"enabled": settings.AI_LAB_ENABLED and allowed(request.user), "models": configured_models(),
                             "sources": SOURCES})
        if request.user.is_staff and request.query_params.get("diagnostics") == "1":
            from .release import runtime_profile
            from .evaluation import digest
            try:
                profile=runtime_profile()
                response.data["runtime"] = {"instance": _instance, "profile_digest": digest(profile),
                    "engine":profile.get("engine"),"semantic_ready":profile.get("semantic_ready"),
                    "local_lexical_pilot":profile.get("local_lexical_pilot",False),
                    "capacity": settings.AI_LAB_MAX_CONCURRENT_JOBS,
                    "max_provider_requests": settings.AI_LAB_OUTLINE_MAX_PROVIDER_REQUESTS,
                    "job_cache_backend": settings.CACHES["throttle"]["BACKEND"],
                    "answer_cache_backend": settings.CACHES["ai_lab"]["BACKEND"]}
            except Exception:
                response.data["runtime"] = {"available": False}
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
        from apps.ai_wallet.services import billing_enabled
        if settings.AI_LAB_SEARCH_ENGINE=="hybrid" or billing_enabled():
            from .runner import submit
            try:
                return submit(request,serializer.validated_data)
            except ProviderError as exc:
                raise PlatformAPIError("زیرساخت جست‌وجو در دسترس نیست.",code=exc.code,status_code=503) from None
        cache, job_id = caches["throttle"], str(uuid4())
        user_lock = f"ai-lab:user:{request.user.pk}"
        now = time.time()
        cache.set(f"ai-lab:job:{job_id}", {"user_id": request.user.pk, "status": "running", "stage": "starting",
            "revision": 0, "findings": [], "findings_limited": False, "workflow": [], "stages_seen": ["starting"],
            "pipeline": "outline-v1", "slot": None, "created_at": now, "heartbeat_at": now, "question": serializer.validated_data["question"],
            "model": serializer.validated_data["model"], "sources": serializer.validated_data["sources"]}, TTL)
        previous = jobs.active(request.user.pk)
        if previous or not cache.add(user_lock, job_id, jobs.LEASE):
            cache.delete(f"ai-lab:job:{job_id}")
            raise PlatformAPIError("جست‌وجوی قبلی هنوز در حال اجراست.", code="AI_LAB_BUSY", status_code=429,
                                   details={"job_id": previous["job_id"]} if previous else {})
        slot = None
        try:
            for n in range(max(1, min(16, settings.AI_LAB_MAX_CONCURRENT_JOBS))):
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
