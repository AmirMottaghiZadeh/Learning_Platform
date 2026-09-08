from django.core.exceptions import ImproperlyConfigured


MINIMUM_PRODUCTION_SECRET_LENGTH = 50
MINIMUM_PRODUCTION_SECRET_UNIQUE_CHARACTERS = 12
WEAK_SECRET_MARKERS = (
    "change-me",
    "changeme",
    "dev-secret",
    "docker-build",
    "docker-local",
    "local-secret",
    "password",
    "secret-key",
)


def validate_production_secret_key(secret_key):
    value = str(secret_key or "")
    normalized = value.strip().lower()

    if value != value.strip():
        raise ImproperlyConfigured("SECRET_KEY must not contain leading or trailing whitespace.")
    if len(value) < MINIMUM_PRODUCTION_SECRET_LENGTH:
        raise ImproperlyConfigured(
            f"SECRET_KEY must contain at least {MINIMUM_PRODUCTION_SECRET_LENGTH} characters."
        )
    if len(set(value)) < MINIMUM_PRODUCTION_SECRET_UNIQUE_CHARACTERS:
        raise ImproperlyConfigured("SECRET_KEY does not contain enough character diversity.")
    if normalized.isdigit() or any(marker in normalized for marker in WEAK_SECRET_MARKERS):
        raise ImproperlyConfigured("SECRET_KEY contains a known weak or placeholder value.")

    return value


LOCAL_CACHE_BACKENDS = (
    "django.core.cache.backends.locmem.LocMemCache",
    "django.core.cache.backends.dummy.DummyCache",
)


def validate_production_cache(caches):
    """Reject per-process caches in production.

    With a per-process cache each Gunicorn worker keeps its own rate-limit
    counters, so the effective login throttle is multiplied by the worker count
    and disappears entirely on horizontal scale-out.
    """
    for alias in ("default", "throttle"):
        backend = (caches.get(alias) or {}).get("BACKEND", "")
        if backend in LOCAL_CACHE_BACKENDS:
            raise ImproperlyConfigured(
                f"Cache alias '{alias}' uses the per-process backend '{backend}'. "
                "Production requires a shared cache; set REDIS_URL."
            )
    return caches


def validate_production_broker(broker_url, *, task_always_eager):
    """Reject an implicit in-request task runner in production."""
    value = str(broker_url or "")
    if task_always_eager:
        raise ImproperlyConfigured(
            "CELERY_TASK_ALWAYS_EAGER must be False in production; background work "
            "may not run inside the request."
        )
    if not value or value.startswith("memory://"):
        raise ImproperlyConfigured(
            "A real Celery broker is required in production; set REDIS_URL or "
            "CELERY_BROKER_URL."
        )
    return value
