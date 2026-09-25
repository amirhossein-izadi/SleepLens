# Environment Configuration

> Managing environment variables, settings, and configuration across environments.

---

## File Structure

```
.env                 # Local overrides (never commit)
.env.example         # Template for developers
.env.dev             # Development overrides
.env.prod.example    # Production template
```

---

## Environment File Priority

```
.env.dev          # Highest priority in dev
.env              # Local overrides
.env.example      # Fallback
# Hardcoded defaults in settings
```

---

## Django Settings Pattern

```python
# settings/base.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "dev-secret-key")
DEBUG = os.getenv("DEBUG", "0") == "1"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB", "project"),
        "USER": os.getenv("POSTGRES_USER", "project"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD", "password"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# Redis
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# CORS
CORS_ALLOWED_ORIGINS = os.getenv(
    "CORS_ALLOWED_ORIGINS", 
    "http://localhost:8080"
).split(",")
```

---

## Settings Structure

```
project_name/
└── settings/
    ├── __init__.py      # Environment loader
    ├── base.py          # Shared settings
    ├── dev.py           # Dev overrides
    ├── test.py          # Test overrides
    └── prod.py          # Production overrides
```

```python
# settings/__init__.py
import os

env = os.getenv("DJANGO_ENV", "dev")

if env == "prod":
    from .prod import *
elif env == "test":
    from .test import *
else:
    from .dev import *
```

---

## Dev Settings

```python
# settings/dev.py
from .base import *

DEBUG = True
ALLOWED_HOSTS = ["*"]

# Dev-specific middleware
MIDDLEWARE += ["debug_toolbar.middleware.DebugToolbarMiddleware"]

# Disable password validators
AUTH_PASSWORD_VALIDATORS = []

# Log to console
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "DEBUG",
    },
}
```

---

## Production Settings

```python
# settings/prod.py
from .base import *
import os

DEBUG = False
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",")

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Static & media files
STATIC_URL = "/static/"
MEDIA_URL = "/media/"

# Logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "filename": "/var/log/project/app.log",
            "formatter": "verbose",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "INFO",
    },
}
```

---

## Environment Variables Reference

### Database
```bash
POSTGRES_DB=project
POSTGRES_USER=project
POSTGRES_PASSWORD=secret
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

### Django
```bash
DJANGO_SECRET_KEY=your-secret-key
DJANGO_ENV=dev  # dev, test, prod
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Redis
```bash
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/1
```

### CORS
```bash
CORS_ALLOWED_ORIGINS=http://localhost:8080
CORS_ALLOW_CREDENTIALS=true
```

### External Services
```bash
# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=app-password

# S3 (optional)
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=...
AWS_S3_REGION_NAME=us-east-1
```

---

## Loading Environment in Python

```python
# lib/env.py
import os
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Database
    postgres_db: str = "project"
    postgres_user: str = "project"
    postgres_password: str = "password"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    
    # Django
    django_secret_key: str = "dev-secret"
    debug: bool = False
    allowed_hosts: list[str] = ["localhost"]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

---

## Docker Environment

```yaml
# docker-compose.yml
services:
  web:
    env_file:
      - .env.dev
    environment:
      - DJANGO_ENV=dev
      - DEBUG=1
```

---

## Development vs Production Rules of Thumb

### Error Handling

| Aspect | Development | Production |
|-------|-------------|------------|
| **Stack traces** | Full verbose | JSON only |
| **Error messages** | Detailed | Generic ("Internal server error") |
| **Logging** | DEBUG level | INFO level |
| **Debug toolbar** | Enabled | Disabled |

```python
# Development - verbose errors
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": "{levelname} {module} {message}"},
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "verbose"},
    },
}

# Production - structured JSON
LOGGING = {
    "version": 1,
    "formatters": {
        "json": {"()": "structlog.stdlib.ProcessorFormatterAdapter", "processor": "json.dumps"},
    },
    "handlers": {
        "json": {"class": "logging.StreamHandler", "formatter": "json"},
    },
}
```

### Development vs Production Config

| Aspect | Development | Production |
|--------|-------------|------------|
| **DEBUG** | True | **False** (enforced) |
| **Logging** | Verbose console | JSON structured |
| **Database** | localhost:5432, CONN_MAX_AGE=0 | Connection pool, SSL required |
| **ALLOWED_HOSTS** | `*` | Specific domains |
| **Validation** | Lazy (warn) | Fail-fast |

```python
# Production safety checks
DEBUG = os.getenv("DEBUG", "0") == "1"

if not DEBUG:
    if os.getenv("DEBUG", "").lower() == "true":
        raise ImproperlyConfigured("DEBUG=True not allowed in production")
    if not os.getenv("SECRET_KEY"):
        raise ImproperlyConfigured("SECRET_KEY required in production")
    
    # Database with connection pooling
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": os.getenv("DB_HOST"),
            "CONN_MAX_AGE": 300,  # Reuse connections
            "OPTIONS": {"sslmode": "require"},
        }
    }
else:
    # Development - no pooling
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "HOST": "localhost",
            "CONN_MAX_AGE": 0,
        }
    }

# Logging
if DEBUG:
    LOGGING = {"handlers": {"console": {"formatter": "verbose"}}}
else:
    # Structured JSON logging with correlation IDs
    import structlog
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
    )
```

---

## Structured Logging Best Practices

Use `structlog` for production log management:

```python
import structlog
import logging

# Configure for production
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.JSONRenderer(),
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
)

# Usage with correlation ID
log = structlog.get_logger()
log.info(
    "request_completed",
    request_id="550e8400-e29b-41d4-a716-446655440000",
    user_id="12345",
    endpoint="/api/users",
    method="GET",
    status_code=200,
    duration_ms=42,
)
```

### Correlation ID Propagation

```python
# Extract from request header
def get_correlation_id(request) -> str:
    return request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

# Use in views
def my_view(request):
    correlation_id = get_correlation_id(request)
    structlog.contextvars.merge_contextvars(correlation_id=correlation_id)
    # All logs now include correlation_id
```

---

## Environment Variables Reference

### Required for All Environments
```bash
DJANGO_SECRET_KEY=<random-string>
DJANGO_ENV=dev|prod
DEBUG=0|1
ALLOWED_HOSTS=localhost,127.0.0.1
```

### Required for Production
```bash
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=example.com,www.example.com
SECURE_SSL_REDIRECT=1
SESSION_COOKIE_SECURE=1
CSRF_COOKIE_SECURE=1
```

### Optional - Recommended
```bash
SENTRY_DSN=<sentry-url>  # Error tracking
DATADOG_API_KEY=<key>   # APM/monitoring
```

---

## Best Practices

1. **Never commit secrets** - Use `.env` files
2. **Use `.env.example`** - Document required variables
3. **Separate environments** - dev, test, prod configs
4. **Validate early** - Fail fast on missing required vars
5. **Use pydantic** - Type-safe environment loading
6. **Enforce DEBUG=False** in production
7. **Use structured logging** - JSON with correlation IDs
8. **Connection pooling** - For production databases

---

*Related: [04_DOCKER_NGINX_SETUP.md](04_DOCKER_NGINX_SETUP.md), [06_TESTING_GUIDELINES.md](06_TESTING_GUIDELINES.md)*