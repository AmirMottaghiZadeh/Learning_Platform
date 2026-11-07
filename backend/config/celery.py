import os

from celery import Celery
from kombu import Queue


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("pharmexa")
app.config_from_object("django.conf:settings", namespace="CELERY")


@app.on_after_configure.connect
def configure_runtime(sender, **kwargs):
    """Apply the parts of the runtime contract the namespace loader can't express.

    This runs when the Celery config is finalized, which is after Django
    settings are ready, so reading ``django.conf.settings`` here is safe even
    though ``config/__init__.py`` imports this module during settings import.
    """
    from django.conf import settings

    conf = sender.conf
    conf.result_backend = settings.CELERY_RESULT_BACKEND or None
    conf.broker_connection_retry_on_startup = True
    conf.broker_transport_options = {
        "visibility_timeout": settings.CELERY_BROKER_VISIBILITY_TIMEOUT,
        "max_retries": 3,
    }
    conf.task_default_queue = settings.CELERY_TASK_DEFAULT_QUEUE
    conf.task_queues = tuple(Queue(name) for name in settings.PLATFORM_TASK_QUEUES)
    conf.timezone = settings.TIME_ZONE
    conf.enable_utc = True

    conf.task_routes = {
        "accounts.send_password_reset_email": {"queue": "default"},
    }


app.autodiscover_tasks()
