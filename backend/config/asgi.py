import os
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.production")
application = get_asgi_application()


def create_application():
    """Uvicorn factory runs inside each worker, after Django initialization."""
    from apps.ai_lab.warmup import warm_search
    warm_search()
    return application
