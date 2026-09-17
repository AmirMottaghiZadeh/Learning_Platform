from .base import *
from decouple import config
from config.security import (
    validate_production_broker,
    validate_production_cache,
    validate_production_secret_key,
)

DEBUG = False

SECRET_KEY = validate_production_secret_key(SECRET_KEY)
CACHES = validate_production_cache(CACHES)

# Deliberate opt-out for single-container deployments with no message broker
# available (e.g. a PaaS that only allows one app + one database). The operator
# accepts that background jobs run synchronously inside the web request. A
# Postgres-backed shared cache (CACHE_BACKEND=django.core.cache.backends.db.
# DatabaseCache) still satisfies validate_production_cache, so throttling and
# caching keep working across Gunicorn workers.
CELERY_RUN_TASKS_IN_REQUEST = config("CELERY_RUN_TASKS_IN_REQUEST", default=False, cast=bool)
if CELERY_RUN_TASKS_IN_REQUEST:
    CELERY_TASK_ALWAYS_EAGER = True
    CELERY_TASK_EAGER_PROPAGATES = True
else:
    CELERY_BROKER_URL = validate_production_broker(
        CELERY_BROKER_URL,
        task_always_eager=CELERY_TASK_ALWAYS_EAGER,
    )

READINESS_REQUIRE_CACHE = config("READINESS_REQUIRE_CACHE", default=True, cast=bool)
READINESS_REQUIRE_BROKER = config(
    "READINESS_REQUIRE_BROKER",
    default=not CELERY_RUN_TASKS_IN_REQUEST,
    cast=bool,
)
QUIZ_API_ENABLED = config("QUIZ_API_ENABLED", default=False, cast=bool)
FLASHCARDS_API_ENABLED = config("FLASHCARDS_API_ENABLED", default=False, cast=bool)
DATA_QUALITY_CENTER_ENABLED = config("DATA_QUALITY_CENTER_ENABLED", default=False, cast=bool)

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SECURE_HSTS_SECONDS = config("SECURE_HSTS_SECONDS", default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=True, cast=bool)
SECURE_HSTS_PRELOAD = config("SECURE_HSTS_PRELOAD", default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "same-origin"
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = False
X_FRAME_OPTIONS = "DENY"

LOGGING["handlers"]["console"]["formatter"] = "json"

STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# DRF's default renderers include BrowsableAPIRenderer, which content
# negotiation picks whenever a client's Accept header prefers HTML over JSON
# -- i.e. every time a browser is pointed at an endpoint directly, as opposed
# to a real client (the app, curl, an uptime-checker) that asks for JSON.
# That HTML page pulls in DRF's own static assets (bootstrap.min.css, ...),
# which CompressedManifestStaticFilesStorage above requires to already be in
# its hashed manifest -- collectstatic doesn't reliably put them there, so
# rendering the page 500s with "Missing staticfiles manifest entry". This is
# a pure JSON API with no use for the browsable HTML view in production
# anyway, so the simplest fix is to never offer it there; local dev (using
# base.py's defaults) keeps it for convenience.
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = ["rest_framework.renderers.JSONRenderer"]
