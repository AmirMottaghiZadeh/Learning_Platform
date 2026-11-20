from celery import shared_task
from celery.exceptions import AlwaysEagerIgnored
from django.conf import settings
import warnings


@shared_task(name="ai_lab.run_search",acks_late=True,reject_on_worker_lost=True,
             soft_time_limit=0,time_limit=0,max_retries=0)
def run_search(job_id):
    from .runner import execute
    execute(job_id)


def enqueue_search(job_id):
    """AI is always background work, even when other local tasks run eagerly."""
    from .provider import ProviderError
    if not settings.CELERY_BROKER_URL or settings.CELERY_BROKER_URL.startswith("memory:"):
        raise ProviderError("SEARCH_WORKER_NOT_CONFIGURED")
    if settings.CELERY_TASK_ALWAYS_EAGER:
        if settings.ENVIRONMENT != "local":
            raise ProviderError("SEARCH_WORKER_NOT_CONFIGURED")
        from config.celery import app
        # send_task deliberately uses the real broker. Keep email/other local
        # task behavior unchanged rather than globally turning off eager mode.
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", AlwaysEagerIgnored)
            return app.send_task(run_search.name,args=[job_id],queue="ai_search")
    return run_search.apply_async(args=[job_id],queue="ai_search")
