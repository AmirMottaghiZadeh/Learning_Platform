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
CELERY_BROKER_URL = validate_production_broker(
    CELERY_BROKER_URL,
    task_always_eager=CELERY_TASK_ALWAYS_EAGER,
)
READINESS_REQUIRE_CACHE = config("READINESS_REQUIRE_CACHE", default=True, cast=bool)
READINESS_REQUIRE_BROKER = config("READINESS_REQUIRE_BROKER", default=True, cast=bool)
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
