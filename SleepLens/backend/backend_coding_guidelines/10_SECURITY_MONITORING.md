# Security & Monitoring

> Production-ready security, structured logging, and monitoring for Django 2026.

---

## Security Checklist (MANDATORY)

Before ANY commit:
- [ ] No hardcoded secrets (API keys, passwords, tokens)
- [ ] All user inputs validated via serializers
- [ ] SQL injection prevention (Django ORM handles this)
- [ ] XSS prevention (Django templates auto-escape)
- [ ] CSRF protection enabled
- [ ] Authentication/authorization verified on every endpoint
- [ ] Rate limiting on all public endpoints
- [ ] Error messages don't leak sensitive data
- [ ] File uploads validated (type, size, content)
- [ ] API keys rotated regularly

---

## Secret Management

### Environment Variables (CRITICAL)

```python
# ✅ Good: Use django-environ or pydantic-settings
import environ
env = environ.Env()
SECRET_KEY = env("DJANGO_SECRET_KEY")
DATABASE_URL = env("DATABASE_URL")
EXTERNAL_API_KEY = env("EXTERNAL_API_KEY")

# ❌ Bad: NEVER hardcode secrets
SECRET_KEY = "my-secret-key-123"
API_KEY = "ak_live_xxxxxxxxxxxx"
```

### .env Files

```bash
# .env (NEVER commit to git)
DJANGO_SECRET_KEY=your-very-long-random-secret-key-here
DATABASE_URL=postgresql://user:pass@localhost/db
EXTERNAL_API_KEY=sk_live_...

# .env.example (commit - template only)
DJANGO_SECRET_KEY=
DATABASE_URL=
EXTERNAL_API_KEY=
```

### Cloud Secrets Managers (Production)

For production environments, use cloud-native secrets managers:

```python
# AWS Secrets Manager
import boto3
from botocore.exceptions import ClientError

def get_secret(secret_name: str) -> str:
    client = boto3.client("secretsmanager")
    try:
        response = client.get_secret_value(SecretId=secret_name)
        return response["SecretString"]
    except ClientError as e:
        raise RuntimeError(f"Failed to retrieve secret: {e}")

# Usage
SECRET_KEY = get_secret("prod/django/secret-key")
```

---

## Structured Logging (2026 Standard)

### Use structlog for structured, queryable logs

```python
# settings/base.py
import structlog

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "json": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.processors.JSONRenderer(),
        },
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "processor": structlog.dev.ConsoleRenderer(),
        },
    },
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "console"},
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "logs/app.jsonl",
            "maxBytes": 10_000_000,
            "backupCount": 5,
            "formatter": "json",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "INFO"},
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
```

### Usage in code

```python
import structlog

logger = structlog.get_logger(__name__)

# ✅ Good: structured, queryable
logger.info("meeting_processed", meeting_id=str(meeting.id), duration_seconds=45.2, transcription_chars=15000)
logger.error("transcription_failed", meeting_id=str(meeting.id), error=str(exc))

# ❌ Bad: unstructured string
logger.info(f"Meeting {meeting.id} processed in 45s")
```

---

## Request Logging Middleware

```python
# meetra/common/middleware.py
import logging
import time

import structlog

logger = structlog.get_logger(__name__)


class RequestLoggingMiddleware:
    """Log every HTTP request with method, path, status, and duration."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start = time.monotonic()
        response = self.get_response(request)
        duration_ms = (time.monotonic() - start) * 1000

        logger.info(
            "http_request",
            method=request.method,
            path=request.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 1),
            user_id=getattr(request.user, "id", None),
        )
        return response
```

---

## Health Checks

```python
# meetra/common/views.py
from django.http import JsonResponse
from django.db import connection


def health(request):
    """Health check for load balancers and monitoring."""
    checks = {}
    healthy = True

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        checks["database"] = "ok"
    except Exception:
        checks["database"] = "fail"
        healthy = False

    try:
        from django.core.cache import cache
        cache.set("_health", "ok", 10)
        checks["redis"] = "ok" if cache.get("_health") == "ok" else "fail"
    except Exception:
        checks["redis"] = "fail"
        healthy = False

    return JsonResponse(
        {"status": "healthy" if healthy else "unhealthy", "checks": checks},
        status=200 if healthy else 503,
    )
```

---

## Password & Token Encryption

### For External Service Passwords (IMAP, SMTP, etc.)

**Always use Fernet** (AES-128-CBC + HMAC authenticated encryption) for storing credentials of external services. Never use XOR, base64, or other obfuscation — they are not encryption.

```python
from cryptography.fernet import Fernet
from django.conf import settings

# settings.ENCRYPTION_KEY must be generated once with Fernet.generate_key()
# and stored in the environment (32 url-safe base64 bytes)
fernet = Fernet(settings.ENCRYPTION_KEY.encode())

# Encrypt
encrypted = fernet.encrypt(password.encode()).decode()

# Decrypt
decrypted = fernet.decrypt(encrypted.encode()).decode()
```

**Generate a key:**
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Why Fernet:**
- Authenticated encryption (AES-128-CBC + HMAC-SHA256)
- Tamper-proof (any modification fails decryption)
- Industry standard, audited
- Works for any sensitive data at rest

### Key Management

- Never commit encryption keys
- Store in environment variables
- Rotate keys periodically
- Use different keys for different environments

---

## Rate Limiting

### DRF Throttling

```python
# settings/base.py
REST_FRAMEWORK = {
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/day",
        "ai_upload": "20/hour",
    },
}
```

---

## Error Handling

### Custom DRF Exception Handler

```python
# meetra/common/exception_handlers.py
import structlog
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = structlog.get_logger(__name__)


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        return Response(
            {
                "success": False,
                "error": {
                    "code": response.status_code,
                    "message": str(response.data) if hasattr(response, "data") else str(exc),
                },
            },
            status=response.status_code,
        )

    # Unexpected error — log full traceback
    logger.exception("unhandled_error", view=context.get("view").__class__.__name__)

    return Response(
        {
            "success": False,
            "error": {
                "code": 500,
                "message": "An unexpected error occurred. Please try again later.",
            },
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
```

---

## File Upload Security

```python
# Validate file type and size
MAX_UPLOAD_SIZE = 500 * 1024 * 1024  # 500 MB
ALLOWED_AUDIO_EXTENSIONS = {"mp3", "wav", "ogg", "m4a", "webm", "flac", "aac", "wma"}
ALLOWED_ATTACHMENT_EXTENSIONS = {"pdf", "docx", "xlsx", "xls", "pptx", "txt", "csv", "png", "jpg", "jpeg"}


def validate_audio_file(file):
    """Validate audio file type and size."""
    if file.size > MAX_UPLOAD_SIZE:
        raise serializers.ValidationError(f"File too large. Max {MAX_UPLOAD_SIZE / 1024 / 1024}MB")
    ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
    if ext not in ALLOWED_AUDIO_EXTENSIONS:
        raise serializers.ValidationError(f"Unsupported audio format: {ext}")


def validate_attachment_file(file):
    """Validate attachment file type and size."""
    if file.size > MAX_UPLOAD_SIZE:
        raise serializers.ValidationError(f"File too large. Max {MAX_UPLOAD_SIZE / 1024 / 1024}MB")
    ext = file.name.rsplit(".", 1)[-1].lower() if "." in file.name else ""
    if ext not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise serializers.ValidationError(f"Unsupported file format: {ext}")
```

---

## No Signals (2026 Rule)

Signals are implicit, hard to trace, and make testing painful. **Call services explicitly.**

```python
# ❌ Old way — signal fires "magically"
@receiver(post_save, sender=Meeting)
def meeting_created(sender, instance, created, **kwargs):
    if created:
        process_meeting_pipeline.delay(str(instance.id))

# ✅ 2026 way — explicit in the view/service
class MeetingViewSet(...):
    def create(self, request, *args, **kwargs):
        meeting = Meeting.objects.create(...)
        process_meeting_pipeline.delay(str(meeting.id))  # explicit, traceable, testable
        return Response(...)
```

Only use signals when you genuinely can't control the call site (e.g. third-party models).

---

## WebSocket Security

```python
# Always validate origin and authenticate WebSocket connections
class LiveTranscriptionConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Validate origin
        origin = self.scope.get("headers", [])
        # Authenticate if needed
        await self.accept()
```

---

*Related: [04_DOCKER_NGINX_SETUP.md](04_DOCKER_NGINX_SETUP.md), [05_ENVIRONMENT_CONFIG.md](05_ENVIRONMENT_CONFIG.md)*
