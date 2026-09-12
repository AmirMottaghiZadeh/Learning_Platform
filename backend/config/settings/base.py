import sys
from pathlib import Path
from corsheaders.defaults import default_headers
from decouple import config
import dj_database_url

RUNNING_TESTS = "test" in sys.argv

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY = config("SECRET_KEY", default="dev-secret")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="localhost,127.0.0.1").split(",")
ENVIRONMENT = config("ENVIRONMENT", default="local")
APP_VERSION = config("APP_VERSION", default="0.1.0")
RELEASE_SHA = config("RELEASE_SHA", default="local")

INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework.authtoken",
    "drf_spectacular",

    # Local apps
    "apps.core",
    "apps.accounts",
    "apps.drugs",
    "apps.lessons",
    "apps.progress",
    # Installed so their models/migrations exist; the API is gated by
    # QUIZ_API_ENABLED / FLASHCARDS_API_ENABLED (default off -> maintenance router).
    "apps.flashcards",
    "apps.quiz",
    # Internal ops tool; its URLs mount only when DATA_QUALITY_CENTER_ENABLED.
    "apps.data_quality_center",
    # Read-only access to the bundled UpToDate SQLite snapshot (no models).
    "apps.uptodate",
]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "apps.core.logging.RequestIdMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
ROOT_URLCONF = "config.urls"
TEMPLATES = [{"BACKEND": "django.template.backends.django.DjangoTemplates", "DIRS": [], "APP_DIRS": True, "OPTIONS": {"context_processors": ["django.template.context_processors.debug", "django.template.context_processors.request", "django.contrib.auth.context_processors.auth", "django.contrib.messages.context_processors.messages"]}}]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"
DATABASE_URL = config("DATABASE_URL", default="postgresql://postgres:postgres@127.0.0.1:5432/pharmexa")
# Persistent connections in production; always 0 under the test runner, where a
# reused connection left mid-transaction by a TestCase can deadlock the TRUNCATE
# a following TransactionTestCase issues (Postgres has no lock timeout by default).
DATABASES = {
    "default": dj_database_url.config(
        default=DATABASE_URL, conn_max_age=0 if RUNNING_TESTS else 600
    )
}
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
if RUNNING_TESTS:
    # Fail a stuck query fast with a clear error instead of hanging the run.
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["options"] = "-c lock_timeout=15000 -c statement_timeout=120000"
REDIS_URL = config("REDIS_URL", default="")
CACHE_URL = config("CACHE_URL", default=REDIS_URL)
BROKER_URL = config("CELERY_BROKER_URL", default=REDIS_URL)

if CACHE_URL:
    CACHE_BACKEND = config(
        "CACHE_BACKEND",
        default="django.core.cache.backends.redis.RedisCache",
    )
    CACHE_LOCATION = config("CACHE_LOCATION", default=CACHE_URL)
else:
    CACHE_BACKEND = config(
        "CACHE_BACKEND",
        default="django.core.cache.backends.locmem.LocMemCache",
    )
    CACHE_LOCATION = config("CACHE_LOCATION", default="pharmexa-default-cache")

CACHE_KEY_PREFIX = config("CACHE_KEY_PREFIX", default=f"pharmexa:{ENVIRONMENT}")
CACHE_VERSION = config("CACHE_VERSION", default=1, cast=int)
CACHE_DEFAULT_TIMEOUT = config("CACHE_DEFAULT_TIMEOUT", default=300, cast=int)
THROTTLE_CACHE_URL = config("THROTTLE_CACHE_URL", default=CACHE_URL)

if THROTTLE_CACHE_URL:
    _throttle_cache = {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": THROTTLE_CACHE_URL,
        "KEY_PREFIX": f"{CACHE_KEY_PREFIX}:throttle",
        "VERSION": CACHE_VERSION,
    }
else:
    _throttle_cache = {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": f"{CACHE_LOCATION}-throttle",
        "KEY_PREFIX": f"{CACHE_KEY_PREFIX}:throttle",
        "VERSION": CACHE_VERSION,
    }

CACHES = {
    "default": {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": CACHE_LOCATION,
        "KEY_PREFIX": CACHE_KEY_PREFIX,
        "VERSION": CACHE_VERSION,
        "TIMEOUT": CACHE_DEFAULT_TIMEOUT,
    },
    "throttle": _throttle_cache,
}

# Background processing (Celery + Redis). Broker stays optional for local
# development, but production settings enforce a real broker.
CELERY_BROKER_URL = BROKER_URL or "memory://"
CELERY_RESULT_BACKEND = config("CELERY_RESULT_BACKEND", default="")
CELERY_TASK_ALWAYS_EAGER = config(
    "CELERY_TASK_ALWAYS_EAGER",
    default=not bool(BROKER_URL),
    cast=bool,
)
CELERY_TASK_EAGER_PROPAGATES = config(
    "CELERY_TASK_EAGER_PROPAGATES",
    default=False,
    cast=bool,
)
CELERY_TASK_DEFAULT_QUEUE = "default"
# Declared outside the CELERY_ namespace: Celery expects ``task_queues`` to hold
# kombu Queue objects, which config/celery.py builds from these names.
PLATFORM_TASK_QUEUES = ("default", "events", "maintenance")
CELERY_TASK_ACKS_LATE = True
CELERY_TASK_REJECT_ON_WORKER_LOST = True
CELERY_WORKER_PREFETCH_MULTIPLIER = config(
    "CELERY_WORKER_PREFETCH_MULTIPLIER",
    default=1,
    cast=int,
)
CELERY_WORKER_MAX_TASKS_PER_CHILD = config(
    "CELERY_WORKER_MAX_TASKS_PER_CHILD",
    default=500,
    cast=int,
)
CELERY_TASK_SOFT_TIME_LIMIT = config("CELERY_TASK_SOFT_TIME_LIMIT", default=120, cast=int)
CELERY_TASK_TIME_LIMIT = config("CELERY_TASK_TIME_LIMIT", default=180, cast=int)
CELERY_BROKER_VISIBILITY_TIMEOUT = config(
    "CELERY_BROKER_VISIBILITY_TIMEOUT",
    default=CELERY_TASK_TIME_LIMIT * 4,
    cast=int,
)
CELERY_TASK_MAX_RETRIES = config("CELERY_TASK_MAX_RETRIES", default=5, cast=int)
CELERY_TASK_RETRY_BACKOFF_SECONDS = config(
    "CELERY_TASK_RETRY_BACKOFF_SECONDS",
    default=5,
    cast=int,
)
CELERY_TASK_RETRY_BACKOFF_MAX_SECONDS = config(
    "CELERY_TASK_RETRY_BACKOFF_MAX_SECONDS",
    default=600,
    cast=int,
)

READINESS_REQUIRE_CACHE = config("READINESS_REQUIRE_CACHE", default=bool(CACHE_URL), cast=bool)
READINESS_REQUIRE_BROKER = config("READINESS_REQUIRE_BROKER", default=False, cast=bool)

ASYNC_EMAIL_ENABLED = config("ASYNC_EMAIL_ENABLED", default=True, cast=bool)

# Throttle scopes that must never silently open when the shared counter store
# is unavailable. Abuse protection for these scopes fails closed.
THROTTLE_FAIL_CLOSED_SCOPES = [
    scope
    for scope in config(
        "THROTTLE_FAIL_CLOSED_SCOPES",
        default=(
            "auth_login,"
            "auth_register,"
            "auth_password_reset_request,"
            "auth_password_reset_confirm"
        ),
    ).split(",")
    if scope.strip()
]
LANGUAGE_CODE = "fa-ir"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
CORS_ALLOWED_ORIGINS = [o for o in config("CORS_ALLOWED_ORIGINS", default="").split(",") if o]
CORS_ALLOW_HEADERS = (*default_headers, "idempotency-key")
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=False, cast=bool)
CSRF_TRUSTED_ORIGINS = [o for o in config("CSRF_TRUSTED_ORIGINS", default="").split(",") if o]
AUTH_ACCESS_TOKEN_TTL_MINUTES = config(
    "AUTH_ACCESS_TOKEN_TTL_MINUTES",
    default=15,
    cast=int,
)
AUTH_REFRESH_TOKEN_TTL_DAYS = config(
    "AUTH_REFRESH_TOKEN_TTL_DAYS",
    default=30,
    cast=int,
)
AUTH_MAX_ACTIVE_SESSIONS = config(
    "AUTH_MAX_ACTIVE_SESSIONS",
    default=10,
    cast=int,
)
AUTH_STEP_UP_TTL_MINUTES = config(
    "AUTH_STEP_UP_TTL_MINUTES",
    default=10,
    cast=int,
)
PASSWORD_RESET_TIMEOUT = config("PASSWORD_RESET_TIMEOUT", default=86400, cast=int)
PASSWORD_RESET_FRONTEND_URL = config("PASSWORD_RESET_FRONTEND_URL", default="http://localhost:8081")
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@pharmexa.local")
# Data Quality Center governance
DATA_QUALITY_MIN_REASON_LENGTH = config(
    "DATA_QUALITY_MIN_REASON_LENGTH",
    default=12,
    cast=int,
)
# A change that cannot be undone from a backup must not be applied at all.
DATA_QUALITY_REQUIRE_BACKUP = config(
    "DATA_QUALITY_REQUIRE_BACKUP",
    default=True,
    cast=bool,
)
DATA_QUALITY_BACKUP_DIR = config("DATA_QUALITY_BACKUP_DIR", default="")
DATA_QUALITY_STEP_UP_TTL_MINUTES = config(
    "DATA_QUALITY_STEP_UP_TTL_MINUTES",
    default=10,
    cast=int,
)
DATA_QUALITY_STEP_UP_SESSION_KEY = "data_quality_step_up_at"
# Verifying the whole chain on every page load would not scale; the console
# checks the most recent window and the scheduled job checks everything.
DATA_QUALITY_AUDIT_VERIFY_LIMIT = config(
    "DATA_QUALITY_AUDIT_VERIFY_LIMIT",
    default=500,
    cast=int,
)

# quiz + flashcards ship built but locked: the maintenance routers answer their
# paths with a 503 envelope until these are switched on deliberately.
QUIZ_API_ENABLED = config("QUIZ_API_ENABLED", default=False, cast=bool)
FLASHCARDS_API_ENABLED = config("FLASHCARDS_API_ENABLED", default=False, cast=bool)
DATA_QUALITY_CENTER_ENABLED = config("DATA_QUALITY_CENTER_ENABLED", default=False, cast=bool)

# Directory holding the UpToDate snapshot (fts.db, content.db, toc.db, info.json).
# The /uptodate/ endpoints answer 503 when the files are not present.
UPTODATE_DB_DIR = config(
    "UPTODATE_DB_DIR",
    default="/home/amir/Documents/UpToDate",
)

# EmailOrUsernameBackend first: the product only shows/asks for "email" (see
# apps.accounts.backends for why the derived `username` field alone isn't
# enough), but ModelBackend stays listed so anything that genuinely
# authenticates by the real username (e.g. the Django admin) keeps working.
AUTHENTICATION_BACKENDS = [
    "apps.accounts.backends.EmailOrUsernameBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        # Django's default threshold (max_similarity=0.7) rejects passwords
        # that merely share a lot of characters with the username/email/name
        # -- in practice that caught plenty of genuinely fine passwords.
        # Raised so only a password that's essentially the same string as one
        # of those attributes (a near-exact match, not just "similar") is
        # rejected.
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
        "OPTIONS": {"max_similarity": 0.95},
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.SessionTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.core.exceptions.platform_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "apps.core.throttling.DistributedAnonRateThrottle",
        "apps.core.throttling.DistributedScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": config("DRF_ANON_THROTTLE_RATE", default="1000/hour"),
        "burst": config("DRF_BURST_THROTTLE_RATE", default="120/min"),
        "sustained": config("DRF_SUSTAINED_THROTTLE_RATE", default="5000/day"),
        "auth_login": config("DRF_AUTH_LOGIN_THROTTLE_RATE", default="5/min"),
        "auth_register": config("DRF_AUTH_REGISTER_THROTTLE_RATE", default="5/hour"),
        "auth_password_reset_request": config(
            "DRF_AUTH_PASSWORD_RESET_REQUEST_THROTTLE_RATE",
            default="3/hour",
        ),
        "auth_password_reset_confirm": config(
            "DRF_AUTH_PASSWORD_RESET_CONFIRM_THROTTLE_RATE",
            default="5/hour",
        ),
    },
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Learning Platform API",
    "DESCRIPTION": "Versioned API contract for the reusable Learning Platform and Pharmexa reference implementation.",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": r"/api/v1",
    "PREPROCESSING_HOOKS": [
        "apps.core.schema.filter_versioned_api_paths",
    ],
}

LOG_LEVEL = config("LOG_LEVEL", default="INFO")
LOG_FORMAT = config("LOG_FORMAT", default="plain")
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_context": {
            "()": "apps.core.logging.RequestContextFilter",
        },
    },
    "formatters": {
        "structured": {
            "format": "%(asctime)s %(levelname)s request_id=%(request_id)s %(name)s %(message)s",
        },
        "json": {
            "()": "apps.core.logging.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json" if LOG_FORMAT == "json" else "structured",
            "filters": ["request_context"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "WARNING",
            "propagate": False,
        },
        "apps": {
            "handlers": ["console"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
