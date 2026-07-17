from pathlib import Path
from decouple import config
import dj_database_url

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
    "apps.learning",
    "apps.accounts",
    "apps.drugs",
    "apps.quizzes",
    "apps.games",
    "apps.league",
    "apps.flashcards",
    "apps.ai_data_pipeline",
    "apps.data_quality_center",
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
DATABASES = {"default": dj_database_url.config(default=DATABASE_URL, conn_max_age=600)}
DATABASES["default"]["CONN_HEALTH_CHECKS"] = True
CACHE_BACKEND = config("CACHE_BACKEND", default="django.core.cache.backends.locmem.LocMemCache")
CACHE_LOCATION = config("CACHE_LOCATION", default="pharmexa-default-cache")
CACHES = {
    "default": {
        "BACKEND": CACHE_BACKEND,
        "LOCATION": CACHE_LOCATION,
    }
}
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
CORS_ALLOW_CREDENTIALS = config("CORS_ALLOW_CREDENTIALS", default=True, cast=bool)
CSRF_TRUSTED_ORIGINS = [o for o in config("CSRF_TRUSTED_ORIGINS", default="").split(",") if o]
LEARNING_PRODUCT_ADAPTER = config(
    "LEARNING_PRODUCT_ADAPTER",
    default="apps.drugs.learning_adapter.PharmexaLearningAdapter",
)
AI_DATA_PIPELINE_PROVIDER = config("AI_DATA_PIPELINE_PROVIDER", default="rules")
AUTH_TOKEN_TTL_HOURS = config("AUTH_TOKEN_TTL_HOURS", default=24, cast=int)
PASSWORD_RESET_TIMEOUT = config("PASSWORD_RESET_TIMEOUT", default=86400, cast=int)
PASSWORD_RESET_FRONTEND_URL = config("PASSWORD_RESET_FRONTEND_URL", default="http://localhost:8081")
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = config("EMAIL_HOST", default="")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = config("EMAIL_USE_TLS", default=True, cast=bool)
DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL", default="no-reply@pharmexa.local")
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "apps.accounts.authentication.ExpiringTokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "apps.core.pagination.DefaultPagination",
    "PAGE_SIZE": 20,
    "EXCEPTION_HANDLER": "apps.core.exceptions.platform_exception_handler",
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": config("DRF_ANON_THROTTLE_RATE", default="1000/hour"),
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
