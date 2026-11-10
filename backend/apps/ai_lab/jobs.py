"""Temporary job ownership, recovery and bounded worker leases."""
import time

from django.core.cache import caches
from .provider import MODEL_ALIASES

TTL = 900
LEASE = 660
STALE_AFTER = 45
MAX_AGE = 600
MAX_FINDINGS = 48


def release(job_id, user_id, slot=None):
    cache = caches["throttle"]
    for key in [f"ai-lab:user:{user_id}", *([slot] if slot else [f"ai-lab:slot:{n}" for n in range(2)])]:
        if cache.get(key) == job_id:
            cache.delete(key)


def read(job_id, user_id):
    cache = caches["throttle"]
    key = f"ai-lab:job:{job_id}"
    record = cache.get(key)
    if not record or record.get("user_id") != user_id:
        return None
    if record.get("status") == "running":
        now = time.time()
        heartbeat, created = record.get("heartbeat_at"), record.get("created_at")
        if (not heartbeat or not created or now - heartbeat > STALE_AFTER or now - created > MAX_AGE
                or record.get("model") not in MODEL_ALIASES or record.get("sources") != ["uptodate"]):
            record = {**record, "status": "failed", "error": {"code": "EXPERIMENT_EXPIRED"}}
            cache.set(key, record, TTL)
            release(str(job_id), user_id)
    return record


def active(user_id):
    cache = caches["throttle"]
    job_id = cache.get(f"ai-lab:user:{user_id}")
    if not job_id:
        return None
    record = read(job_id, user_id)
    if not record or record.get("status") != "running":
        release(job_id, user_id)
        return None
    return {"job_id": job_id, **{k: record[k] for k in ("question", "model", "sources")}, **public(record)}


def public(record, after_revision=None):
    keys = {"status", "stage", "result", "error", "revision", "findings", "findings_limited", "first_result_ms", "workflow", "stages_seen"}
    if record.get("status") == "running" and after_revision is not None and str(record.get("revision")) == after_revision:
        keys -= {"findings", "findings_limited", "workflow", "stages_seen"}
    return {k: v for k, v in record.items() if k in keys}
