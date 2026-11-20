"""Zero-model operational check of Redis Streams and a separate Celery worker."""
import asyncio
import time
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.ai_lab import events, job_store
from apps.ai_lab.models import SearchRun
from apps.ai_lab.tasks import enqueue_search


class Command(BaseCommand):
    help = "Check real Redis/worker transport using a pre-cancelled diagnostic job; makes no model requests."

    def handle(self, *args, **options):
        owner = None
        identifier = uuid4()
        try:
            if settings.CELERY_BROKER_URL.startswith("memory:") or not settings.AI_LAB_EVENT_REDIS_URL:
                raise CommandError("REAL_WORKER_AND_EVENT_REDIS_REQUIRED")
            events.append(identifier, {"type":"heartbeat"})
            async def check_stream():
                try:
                    rows = await events.read_async(identifier,0,block_ms=100)
                    if len(rows)!=1 or rows[0]["sequence"]!=1:
                        raise CommandError("REDIS_STREAM_CHECK_FAILED")
                finally:
                    await events._async_redis(settings.AI_LAB_EVENT_REDIS_URL).aclose()
            asyncio.run(check_stream())
            owner = get_user_model().objects.create_user("ai-worker-probe-"+uuid4().hex[:16],is_staff=True,is_superuser=True)
            # Invalid model alias is a second guard against any paid work,
            # even if a future regression ignores the pre-cancelled state.
            payload={"question":"Runtime transport probe.","model":"runtime_probe","sources":["uptodate"],"history":[]}
            run=SearchRun.objects.create(id=identifier,owner=owner,client_id="runtime-probe",payload_digest=job_store.digest(payload),
                encrypted_payload=job_store.encode(payload),status="queued",cancel_requested=True,heartbeat_at=timezone.now())
            enqueue_search(str(identifier))
            expires=time.monotonic()+15
            while time.monotonic()<expires:
                run.refresh_from_db()
                if run.status=="failed":
                    if job_store.decode(run.encrypted_result).get("error",{}).get("code")!="SEARCH_CANCELLED":
                        raise CommandError("WORKER_CANCELLATION_CHECK_FAILED")
                    self.stdout.write("Redis stream and separate Celery worker passed; model requests=0.")
                    return
                time.sleep(.2)
            raise CommandError("SEARCH_WORKER_DID_NOT_RESPOND")
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"SEARCH_RUNTIME_CHECK_FAILED type={type(exc).__name__}") from None
        finally:
            if owner is not None:
                from django.core.cache import caches
                caches["throttle"].delete(f"ai-lab:job:{identifier}")
                owner.delete()
            try:
                events._redis(settings.AI_LAB_EVENT_REDIS_URL).delete(events._key(identifier),events._key(identifier)+":sequence")
            except Exception:
                pass
