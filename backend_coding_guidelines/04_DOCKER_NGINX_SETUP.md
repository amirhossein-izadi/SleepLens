# Docker & Nginx Setup

> Production-ready Docker and Nginx configuration for Django 6.0+ projects.

---

## Project Structure

```
compose/
├── dev/
│   ├── docker-compose.yml
│   └── nginx.conf
└── prod/
    ├── docker-compose.yml
    └── nginx.conf

deploy/
├── entrypoint.sh
├── celery-entrypoint.sh
└── gunicorn.conf.py

nginx/
└── default.conf

Dockerfile
```

---

## Dockerfile (2026 Best Practices)

```dockerfile
# Use Python 3.14+ (Django 6.0+ requirement)
FROM python:3.14-slim as base

# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Development stage
FROM base as dev
ENV DEBUG=1

# Production stage
FROM base as prod
ENV DEBUG=0

# Final stage
FROM prod as final
WORKDIR /app

# Copy application
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Run as non-root user (security)
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup appuser
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

---

## Docker Compose (Development)

```yaml
# compose/dev/docker-compose.yml
services:
  db:
    image: postgres:17-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-project}
      POSTGRES_USER: ${POSTGRES_USER:-project}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  web:
    build:
      context: ../..
      target: dev
    restart: unless-stopped
    working_dir: /app
    env_file:
      - ../../.env.dev
    command: ["bash", "/app/deploy/entrypoint.sh"]
    volumes:
      - ../..:/app
      - static_volume:/srv/static
      - media_volume:/srv/media
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    ports:
      - "8000:8000"

  nginx:
    image: nginx:1.27-alpine
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      - static_volume:/srv/static:ro
      - media_volume:/srv/media:ro
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - web

  worker:
    build:
      context: ../..
      target: dev
    restart: unless-stopped
    env_file:
      - ../../.env.dev
    command: ["celery", "-A", "project", "worker", "-l", "info"]
    volumes:
      - ../..:/app
    depends_on:
      - redis
      - db

volumes:
  pgdata:
  redis_data:
  static_volume:
  media_volume:
```

---

## Nginx Configuration

```nginx
# compose/dev/nginx.conf
upstream web {
    server web:8000;
}

server {
    listen 80;
    server_name localhost;

    client_max_body_size 100M;

    # Static files
    location /static/ {
        alias /srv/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /srv/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API proxy
    location / {
        proxy_pass http://web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # WebSocket support (Django Channels)
    location /ws/ {
        proxy_pass http://web;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

---

## Production Nginx

```nginx
# compose/prod/nginx.conf
upstream web {
    server web:8000;
}

server {
    listen 80;
    server_name example.com www.example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com www.example.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;

    client_max_body_size 100M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Static files
    location /static/ {
        alias /srv/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /srv/media/;
        expires 7d;
        add_header Cache-Control "public";
    }

    # API
    location / {
        proxy_pass http://web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # WebSocket support
    location /ws/ {
        proxy_pass http://web;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }
}
```

---

## Entrypoint Script

```bash
#!/bin/bash
# deploy/entrypoint.sh

set -e

# Wait for database
echo "Waiting for database..."
python manage.py wait_for_db --timeout 60

# Run migrations
echo "Running migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if needed
if [ "$CREATE_SUPERUSER" = "true" ]; then
    echo "Creating superuser..."
    python manage.py createsuperuser --noinput || true
fi

# Start server
echo "Starting server..."
exec "$@"
```

---

## Environment Files

### .env.example

```bash
# Database
POSTGRES_DB=project
POSTGRES_USER=project
POSTGRES_PASSWORD=change_me_in_production

# Redis
REDIS_URL=redis://redis:6379/0

# Django
DJANGO_SECRET_KEY=change_me_in_production
DJANGO_ENV=dev
DEBUG=1
ALLOWED_HOSTS=localhost,127.0.0.1

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:8080
```

### .env.prod.example

```bash
# Database
POSTGRES_DB=project
POSTGRES_USER=project
POSTGRES_PASSWORD=strong_random_password

# Redis
REDIS_URL=redis://redis:6379/0

# Django
DJANGO_SECRET_KEY=very_long_random_secret_key
DJANGO_ENV=prod
DEBUG=0
ALLOWED_HOSTS=example.com,www.example.com

# Security
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
```

---

## Common Commands

```bash
# Development
docker-compose -f compose/dev/docker-compose.yml up -d
docker-compose -f compose/dev/docker-compose.yml logs -f web

# Production
docker-compose -f compose/prod/docker-compose.yml up -d --build

# Run tests in container
docker-compose -f compose/dev/docker-compose.yml exec web pytest

# Database shell
docker-compose -f compose/dev/docker-compose.yml exec db psql -U project
```

---

*Related: [05_ENVIRONMENT_CONFIG.md](05_ENVIRONMENT_CONFIG.md), [01_PROJECT_STRUCTURE.md](01_PROJECT_STRUCTURE.md)*