"""Durable admission and at-most-once worker start for paid searches."""
import re
import time
from uuid import uuid4
from django.conf import settings
from django.core.cache import caches
from django.db import IntegrityError, transaction, close_old_connections
from django.utils import timezone
from rest_framework.response import Response
from apps.core.exceptions import PlatformAPIError
from . import events, jobs, job_store
from .models import SearchRun
from .provider import ProviderError


def submit(request, payload):
    client_id=request.data.get("request_id") or str(uuid4())
    if not isinstance(client_id,str) or not re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}",client_id):
        raise PlatformAPIError("شناسهٔ درخواست معتبر نیست.",code="INVALID",status_code=400)
    digest=job_store.digest(payload)
    previous=SearchRun.objects.filter(owner=request.user,client_id=client_id).first()
    if previous:
        if previous.payload_digest!=digest:
            raise PlatformAPIError("شناسهٔ درخواست قبلاً برای سؤال دیگری استفاده شده است.",code="IDEMPOTENCY_CONFLICT",status_code=409)
        response=Response({"job_id":str(previous.pk)},status=202)
        response["Cache-Control"]="private, no-store"
        return response
    live=jobs.active(request.user.pk)
    if live:
        raise PlatformAPIError("جست‌وجوی قبلی هنوز در حال اجراست.",code="AI_LAB_BUSY",status_code=429,details={"job_id":live["job_id"]})
    from apps.ai_wallet.services import get_wallet,reconcile
    # Persist recovery of terminal usage before admission's transaction can
    # reject a depleted account and roll back the new SearchRun.
    reconcile(get_wallet(request.user))
    # Fail before admission if the event backend cannot serve this deployment.
    events.last_sequence(uuid4())
    try:
        with transaction.atomic():
            run=SearchRun.objects.create(owner=request.user,client_id=client_id,payload_digest=digest,
                                        encrypted_payload=job_store.encode(payload),heartbeat_at=timezone.now())
            from apps.ai_wallet.services import start_search
            start_search(request.user,run.pk)
    except IntegrityError:
        previous=SearchRun.objects.filter(owner=request.user,client_id=client_id).first()
        if previous and previous.payload_digest==digest:
            return Response({"job_id":str(previous.pk)},status=202)
        raise PlatformAPIError("جست‌وجوی دیگری در حال پذیرش است.",code="AI_LAB_BUSY",status_code=429) from None
    cache,job_id=caches["throttle"],str(run.pk)
    user_lock=f"ai-lab:user:{request.user.pk}"
    try:
        if not cache.add(user_lock,job_id,jobs.LEASE):
            raise PlatformAPIError("جست‌وجوی قبلی هنوز در حال اجراست.",code="AI_LAB_BUSY",status_code=429)
        slot=None
        for n in range(max(1,min(16,settings.AI_LAB_MAX_CONCURRENT_JOBS))):
            candidate=f"ai-lab:slot:{n}"
            persisted=SearchRun.objects.filter(slot=candidate,status__in=["admitting","queued","running"]).exclude(pk=run.pk).first()
            if persisted:
                alive=jobs.read(str(persisted.pk),persisted.owner_id)
                if alive and alive.get("status")=="running":
                    continue
            owner=cache.get(candidate)
            if owner:
                record=cache.get(f"ai-lab:job:{owner}")
                if record:
                    jobs.read(owner,record["user_id"])
                if not record or record.get("status")!="running":
                    if cache.get(candidate)==owner:
                        cache.delete(candidate)
            if cache.add(candidate,job_id,jobs.LEASE):
                slot=candidate;break
        if not slot:
            raise PlatformAPIError("ظرفیت جست‌وجوی هم‌زمان پر است.",code="AI_LAB_BUSY",status_code=429)
        run.slot=slot
        quota=f"ai-lab:budget:{request.user.pk}:{timezone.now():%Y%m%d%H}"
        cache.add(quota,0,3700)
        if cache.incr(quota)>20:
            raise PlatformAPIError("سقف جست‌وجوی ساعتی پر شده است.",code="AI_LAB_LIMIT",status_code=429)
        run.status="queued"
        try:
            with transaction.atomic():
                run.save(update_fields=["slot","status"])
        except IntegrityError:
            raise PlatformAPIError("ظرفیت جست‌وجوی هم‌زمان پر است.",code="AI_LAB_BUSY",status_code=429) from None
        record=job_store.snapshot(run)
        cache.set(f"ai-lab:job:{job_id}",record,jobs.TTL)
        events.append(job_id,{"type":"snapshot","job":jobs.public(record)})
        if settings.AI_LAB_EXECUTOR=="celery":
            from .tasks import enqueue_search
            enqueue_search(job_id)
        elif settings.AI_LAB_EXECUTOR=="thread" and settings.ENVIRONMENT=="local":
            from .views import _executor
            _executor.submit(execute,job_id)
        else:
            raise ProviderError("SEARCH_WORKER_NOT_CONFIGURED")
    except Exception:
        # A broker acknowledgement can be lost after a worker started. Never
        # overwrite that running job or create an automatic second paid run.
        changed=SearchRun.objects.filter(pk=run.pk,status__in=["admitting","queued"]).update(status="failed",
            finished_at=timezone.now(),encrypted_result=job_store.encode({"status":"failed","error":{"code":"SEARCH_ADMISSION_FAILED"}}))
        if changed:
            from apps.ai_wallet.services import settle
            settle(run.pk,outcome="admission_failed")
            cache.delete(f"ai-lab:job:{job_id}")
            jobs.release(job_id,request.user.pk,run.slot or None)
            raise
    response=Response({"job_id":job_id},status=202)
    response["Cache-Control"]="private, no-store"
    return response


def execute(job_id):
    close_old_connections()
    try:
        with transaction.atomic():
            run=SearchRun.objects.select_for_update().select_related("owner").get(pk=job_id)
            if run.status!="queued" or run.started_at is not None:
                return  # Duplicate queue delivery never repeats paid work.
            if run.cancel_requested:
                raise ProviderError("SEARCH_CANCELLED")
            run.status="running";run.started_at=timezone.now();run.heartbeat_at=run.started_at
            run.save(update_fields=["status","started_at","heartbeat_at"])
        from .views import _run, require_lab
        require_lab(run.owner)
        _run(str(run.pk),run.owner,job_store.decode(run.encrypted_payload),run.slot,durable=True)
    except Exception as exc:
        code=getattr(exc,"code","EXPERIMENT_FAILED")
        if not isinstance(code,str) or not re.fullmatch(r"[A-Z_]{1,64}",code):code="EXPERIMENT_FAILED"
        values={"status":"failed","error":{"code":code}}
        run=SearchRun.objects.filter(pk=job_id).first()
        if run and run.status in {"queued","running"}:
            from apps.ai_wallet.services import settle
            settle(run.pk,outcome="failed")
            run.status="failed";run.finished_at=timezone.now();run.encrypted_result=job_store.encode(values)
            run.save(update_fields=["status","finished_at","encrypted_result"])
            record=job_store.snapshot(run)
            caches["throttle"].set(f"ai-lab:job:{job_id}",record,jobs.TTL)
            try:events.append(job_id,{"type":"complete","job":jobs.public(record)})
            except ProviderError:pass
            jobs.release(str(job_id),run.owner_id,run.slot or None)
    finally:
        close_old_connections()
