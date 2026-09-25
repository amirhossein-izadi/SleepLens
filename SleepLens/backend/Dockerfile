# syntax=docker/dockerfile:1
# Multi-stage build for the SleepLens backend (API + Celery worker).

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        "django>=5.2,<6.0" "djangorestframework>=3.15" "django-cors-headers>=4.3" \
        "djangorestframework-simplejwt>=5.3" "drf-spectacular>=0.27" "django-environ>=0.11" \
        "psycopg[binary]>=3.1" "celery[redis]>=5.3" "django-celery-beat>=2.5" \
        "django-celery-results>=2.5" "httpx>=0.26" "structlog>=24.1" "sentry-sdk>=1.40"

COPY . .

FROM base AS dev
ENV DJANGO_ENV=dev DJANGO_DEBUG=1
RUN python manage.py collectstatic --noinput || true
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod
ENV DJANGO_ENV=prod DJANGO_DEBUG=0
RUN pip install --no-cache-dir gunicorn && \
    useradd --uid 1001 --create-home appuser && chown -R appuser:appuser /app
USER appuser
RUN python manage.py collectstatic --noinput || true
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1
CMD ["gunicorn", "sleeplens.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
