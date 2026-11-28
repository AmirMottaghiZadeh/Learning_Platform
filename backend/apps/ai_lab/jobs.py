"""Temporary job ownership, recovery and bounded worker leases."""
import time
from uuid import UUID

from django.conf import settings
from django.core.cache import caches
from .provider import MODEL_ALIASES

TTL = 900
LEASE = 660
STALE_AFTER = 45
MAX_AGE = 600
MAX_FINDINGS = 48


def release(job_id, user_id, slot=None):
    cache = caches["throttle"]
    for key in [f"ai-lab:user:{user_id}", *([slot] if slot else [f"ai-lab:slot:{n}" for n in range(max(1, min(settings.AI_LAB_MAX_CONCURRENT_SLOTS, settings.AI_LAB_MAX_CONCURRENT_JOBS)))])]:
        try:
            if cache.get(key) == job_id:
                cache.delete(key)
        except Exception:
            return  # Leases expire; never discard a durable final answer.


def read(job_id, user_id, *, verify_sql=True):
    cache = caches["throttle"]
    key = f"ai-lab:job:{job_id}"
    try:
        record = cache.get(key)
    except Exception:
        record = None
    if record is None:
        try:
            UUID(str(job_id))
        except ValueError:
            return None
        from .models import SearchRun
        from .job_store import snapshot
        run=SearchRun.objects.filter(pk=job_id,owner_id=user_id).first()
        if run:
            record=snapshot(run)
            try:
                cache.set(key,record,TTL)
            except Exception:
                pass
    if not record or record.get("user_id") != user_id:
        return None
    queued = record.get("stage") == "queued"
    if verify_sql and (record.get("pipeline") == "hybrid-v1" or record.get("history_saved")) and record.get("status") == "running":
        # Redis can return an older value after an outage. SQL terminal state
        # wins, and a healthy worker's persisted heartbeat prevents false expiry.
        from .models import SearchRun
        from .job_store import snapshot
        run = SearchRun.objects.filter(pk=job_id, owner_id=user_id).first()
        queued = bool(run and run.status in {"admitting", "queued"})
        if run and run.status not in {"admitting", "queued", "running"}:
            record = snapshot(run)
            try:
                cache.set(key, record, TTL)
            except Exception:
                pass
        elif run and run.heartbeat_at:
            record["heartbeat_at"] = max(record.get("heartbeat_at", 0), run.heartbeat_at.timestamp())
    if record.get("status") == "running":
        now = time.time()
        heartbeat, created = record.get("heartbeat_at"), record.get("created_at")
        expired = (now - created > settings.AI_LAB_QUEUE_MAX_WAIT_SECONDS if queued and created
                   else not heartbeat or now - heartbeat > STALE_AFTER)
        if (not created or expired
                or (record.get("pipeline") not in {"outline-v1","hybrid-v1"} and now - created > min(MAX_AGE, settings.AI_LAB_TOTAL_TIMEOUT_SECONDS + 5))
                or record.get("model") not in MODEL_ALIASES or record.get("sources") != ["uptodate"]):
            record = {**record, "status": "failed", "error": {"code": "EXPERIMENT_EXPIRED"}}
            cache.set(key, record, TTL)
            if record.get("pipeline") in {"hybrid-v1", "outline-v1"}:
                from .models import SearchRun
                from .job_store import encode
                from django.utils import timezone
                SearchRun.objects.filter(pk=job_id,owner_id=user_id,status__in=["admitting","queued","running"]).update(
                    status="failed",finished_at=timezone.now(),encrypted_result=encode(public(record)))
            release(str(job_id), user_id)
    if record.get("status") == "running" and record.get("slot") == "" and record.get("stage") == "queued":
        # A search waiting for capacity: tell the reader where it stands, so
        # the app can show "third in line, about 40s" instead of a blank spin.
        record = {**record, **queued_numbers(str(job_id), record.get("created_at"))}
    return record


def queued_numbers(job_id, created_at):
    cache = caches["throttle"]
    key = f"ai-lab:qpos:{job_id}"
    try:
        cached = cache.get(key)
    except Exception:
        cached = None
    if isinstance(cached, dict):
        return cached
    from datetime import datetime, timezone as dt_timezone
    from .models import SearchRun
    try:
        created = datetime.fromtimestamp(float(created_at), tz=dt_timezone.utc)
        position = SearchRun.objects.filter(status="queued", slot="", created_at__lt=created).count() + 1
    except (TypeError, ValueError, OverflowError):
        position = 1
    capacity = max(1, min(settings.AI_LAB_MAX_CONCURRENT_SLOTS, settings.AI_LAB_MAX_CONCURRENT_JOBS))
    numbers = {"queue_position": position,
               "eta_seconds": -(-position // capacity) * settings.AI_LAB_QUEUE_ETA_SECONDS}
    try:
        cache.set(key, numbers, 3)
    except Exception:
        pass
    return numbers


def active(user_id):
    cache = caches["throttle"]
    try:
        job_id = cache.get(f"ai-lab:user:{user_id}")
    except Exception:
        job_id = None
    record = read(job_id, user_id) if job_id else None
    if record and record.get("status") == "running":
        return {"job_id": job_id, **{k: record[k] for k in ("question", "model", "sources")}, **public(record)}
    if job_id:
        release(job_id, user_id)

    from .models import SearchRun
    run = SearchRun.objects.filter(owner_id=user_id, status__in=["admitting", "queued", "running"]).first()
    if not run:
        return None
    job_id = str(run.pk)
    record = read(job_id, user_id)
    if not record or record.get("status") != "running":
        return None
    try:
        cache.add(f"ai-lab:user:{user_id}", job_id, LEASE)
    except Exception:
        pass
    return {"job_id": job_id, **{k: record[k] for k in ("question", "model", "sources")}, **public(record)}


def public(record, after_revision=None):
    keys = {"status", "stage", "result", "error", "revision", "findings", "findings_limited", "first_result_ms", "workflow", "stages_seen", "metrics", "feedback_available", "answer_drafts", "queue_position", "eta_seconds"}
    if record.get("status") == "running" and after_revision is not None and str(record.get("revision")) == after_revision:
        keys -= {"findings", "findings_limited", "workflow", "stages_seen"}
    return {"cancellable": record.get("pipeline") == "hybrid-v1", **{k: v for k, v in record.items() if k in keys}}
