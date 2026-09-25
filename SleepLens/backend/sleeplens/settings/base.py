"""Base Django settings for SleepLens.

All environment variables are loaded via django-environ from ``backend/.env``.
Never hardcode secrets in this file — see ``.env.example`` for the full list.
"""

from __future__ import annotations

import sys
from datetime import timedelta
from pathlib import Path

import environ
import structlog

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------

# sleeplens/settings/base.py -> sleeplens/ -> backend/
BASE_DIR: Path = Path(__file__).resolve().parent.parent
PROJECT_ROOT: Path = BASE_DIR.parent

# Three-layer architecture: ``apps/`` and the project root are importable so that
# ``from accounts.models import User`` works without a package prefix.
APPS_DIR: Path = PROJECT_ROOT / "apps"

for _dir in [str(APPS_DIR), str(PROJECT_ROOT)]:
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

# -----------------------------------------------------------------------------
# Environment (django-environ)
# -----------------------------------------------------------------------------

env = environ.Env(
    DJANGO_DEBUG=(bool, True),
    DJANGO_SECRET_KEY=(str, ""),
    DJANGO_ALLOWED_HOSTS=(list, ["localhost", "127.0.0.1"]),
    DJANGO_LOG_LEVEL=(str, "INFO"),
    # Database
    DB_ENGINE=(str, "postgres"),
    POSTGRES_DB=(str, "sleeplens"),
    POSTGRES_USER=(str, "sleeplens"),
    POSTGRES_PASSWORD=(str, "sleeplens"),
    POSTGRES_HOST=(str, "localhost"),
    POSTGRES_PORT=(int, 5432),
    # Redis / Celery
    REDIS_URL=(str, "redis://localhost:6379/0"),
    CELERY_BROKER_URL=(str, "redis://localhost:6379/0"),
    CELERY_TASK_ALWAYS_EAGER=(bool, False),
    REDIS_ENABLED=(bool, True),
    # CORS
    CORS_ALLOWED_ORIGINS=(list, ["http://localhost:5173", "http://localhost:3000"]),
    CORS_ALLOW_CREDENTIALS=(bool, True),
    # Analysis pipeline
    ANALYSIS_WEIGHTS_DIR=(str, "analysis_weights"),
    STAGING_SYSTEM=(str, "ensemble"),
    # Assistant (local opencode agent server)
    OPENCODE_BASE_URL=(str, "http://127.0.0.1:4096"),
    OPENCODE_TIMEOUT_SECONDS=(float, 180.0),
    OPENCODE_CONNECT_TIMEOUT=(float, 3.0),
    CONFIDENCE_HIGH=(float, 0.80),
    CONFIDENCE_MEDIUM=(float, 0.60),
    MAX_UPLOAD_SIZE=(int, 500 * 1024 * 1024),
    # Monitoring
    SENTRY_DSN=(str, ""),
)

environ.Env.read_env(PROJECT_ROOT / ".env")

# -----------------------------------------------------------------------------
# Core settings
# -----------------------------------------------------------------------------

DEBUG: bool = env("DJANGO_DEBUG")

SECRET_KEY: str = env("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    if DEBUG:
        SECRET_KEY = "dev-insecure-secret-key-do-not-use-in-production"
    else:
        raise ValueError("DJANGO_SECRET_KEY environment variable must be set")

ALLOWED_HOSTS: list[str] = env("DJANGO_ALLOWED_HOSTS")

# -----------------------------------------------------------------------------
# Applications
# -----------------------------------------------------------------------------

DJANGO_APPS: list[str] = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.postgres",
]

THIRD_PARTY_APPS: list[str] = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "drf_spectacular",
    "django_celery_beat",
    "django_celery_results",
]

LOCAL_APPS: list[str] = [
    "common",
    "apps.accounts",
    "apps.patients",
    "apps.studies",
    "apps.analysis",
    "apps.reports",
    "apps.assistant",
]

INSTALLED_APPS: list[str] = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# -----------------------------------------------------------------------------
# Middleware
# -----------------------------------------------------------------------------

MIDDLEWARE: list[str] = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "common.middleware.request_logging.RequestLoggingMiddleware",
]

ROOT_URLCONF: str = "sleeplens.urls"

TEMPLATES: list[dict] = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION: str = "sleeplens.wsgi.application"
ASGI_APPLICATION: str = "sleeplens.asgi.application"

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

if env("DB_ENGINE") == "sqlite":
    # Dev fallback when Docker/Postgres is not available. Not for production.
    DATABASES: dict = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": PROJECT_ROOT / "db.sqlite3",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": env("POSTGRES_DB"),
            "USER": env("POSTGRES_USER"),
            "PASSWORD": env("POSTGRES_PASSWORD"),
            "HOST": env("POSTGRES_HOST"),
            "PORT": env.int("POSTGRES_PORT"),
            "CONN_MAX_AGE": 300,
            "CONN_HEALTH_CHECKS": True,
        }
    }

# -----------------------------------------------------------------------------
# Cache (Redis) — falls back to local memory when Redis is not in play.
# -----------------------------------------------------------------------------

if env("REDIS_ENABLED"):
    CACHES: dict = {
        "default": {
            "BACKEND": "django.core.cache.backends.redis.RedisCache",
            "LOCATION": env("REDIS_URL"),
        }
    }
else:  # pragma: no cover - dev fallback
    CACHES = {
        "default": {
            "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        }
    }

# -----------------------------------------------------------------------------
# Authentication
# -----------------------------------------------------------------------------

AUTH_USER_MODEL: str = "accounts.User"

AUTH_PASSWORD_VALIDATORS: list[dict] = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# -----------------------------------------------------------------------------
# Internationalization
# -----------------------------------------------------------------------------

LANGUAGE_CODE: str = "en-us"
TIME_ZONE: str = "UTC"
USE_I18N: bool = True
USE_TZ: bool = True

# -----------------------------------------------------------------------------
# Static & media
# -----------------------------------------------------------------------------

STATIC_URL: str = "static/"
STATIC_ROOT: Path = BASE_DIR / "staticfiles"

MEDIA_URL: str = "media/"
MEDIA_ROOT: Path = BASE_DIR / "media"

DEFAULT_AUTO_FIELD: str = "django.db.models.BigAutoField"

# -----------------------------------------------------------------------------
# Django REST Framework
# -----------------------------------------------------------------------------

REST_FRAMEWORK: dict = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "apps.accounts.authentication.CookieJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "common.renderers.ApiRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_PAGINATION_CLASS": "common.pagination.StandardPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "common.exceptions.custom_exception_handler",
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "study_upload": "20/hour",
        "report_generation": "10/hour",
    },
}

# -----------------------------------------------------------------------------
# Simple JWT
# -----------------------------------------------------------------------------

SIMPLE_JWT: dict = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=1),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# -----------------------------------------------------------------------------
# OpenAPI
# -----------------------------------------------------------------------------

SPECTACULAR_SETTINGS: dict = {
    "TITLE": "SleepLens API",
    "DESCRIPTION": "Sleep stage classification, sleep quality index, and sleep assistant",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "COMPONENT_SPLIT_REQUEST": True,
    "TAGS": [
        {"name": "Accounts", "description": "Authentication and user profile endpoints"},
        {"name": "Studies", "description": "Study upload, listing, results and charts"},
        {"name": "Analysis", "description": "Sleep stage and quality index per study"},
    ],
}

# -----------------------------------------------------------------------------
# CORS
# -----------------------------------------------------------------------------

CORS_ALLOWED_ORIGINS: list[str] = env("CORS_ALLOWED_ORIGINS")
CORS_ALLOW_CREDENTIALS: bool = env("CORS_ALLOW_CREDENTIALS")

# -----------------------------------------------------------------------------
# Celery
# -----------------------------------------------------------------------------

CELERY_BROKER_URL: str = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND: str = "django-db"
CELERY_CACHE_BACKEND: str = "django-cache"
CELERY_ACCEPT_CONTENT: list[str] = ["json"]
CELERY_TASK_SERIALIZER: str = "json"
CELERY_RESULT_SERIALIZER: str = "json"
CELERY_TIMEZONE: str = TIME_ZONE
CELERY_TASK_TRACK_STARTED: bool = True
CELERY_TASK_TIME_LIMIT: int = 60 * 60  # one hour — a full night with SDI on CPU
CELERY_TASK_ALWAYS_EAGER: bool = env("CELERY_TASK_ALWAYS_EAGER")
CELERY_BEAT_SCHEDULER: str = "django_celery_beat.schedulers:DatabaseScheduler"

# -----------------------------------------------------------------------------
# Analysis pipeline
# -----------------------------------------------------------------------------

WEIGHTS_DIR: Path = PROJECT_ROOT / env("ANALYSIS_WEIGHTS_DIR")
STAGING_SYSTEM: str = env("STAGING_SYSTEM")
CONFIDENCE_HIGH: float = env("CONFIDENCE_HIGH")
CONFIDENCE_MEDIUM: float = env("CONFIDENCE_MEDIUM")

MAX_UPLOAD_SIZE: int = env("MAX_UPLOAD_SIZE")
ALLOWED_STUDY_EXTENSIONS: frozenset[str] = frozenset({"edf"})
ALLOWED_STUDY_CONTENT_TYPES: frozenset[str] = frozenset(
    {"application/octet-stream", "application/edf", "binary/octet-stream"}
)

# -----------------------------------------------------------------------------
# Monitoring
# -----------------------------------------------------------------------------

SENTRY_DSN: str = env("SENTRY_DSN")

# -----------------------------------------------------------------------------
# Logging (structlog)
# -----------------------------------------------------------------------------

LOGGING: dict = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.processors.JSONRenderer(),
        },
        "console": {
            "()": "structlog.stdlib.ProcessorFormatter",
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": env("DJANGO_LOG_LEVEL"),
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": env("DJANGO_LOG_LEVEL"),
            "propagate": False,
        },
        "celery": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "accounts": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "studies": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "analysis": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "httpcore": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "httpx": {"handlers": ["console"], "level": "WARNING", "propagate": False},
        "reports": {"handlers": ["console"], "level": "INFO", "propagate": False},
    },
}

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)
