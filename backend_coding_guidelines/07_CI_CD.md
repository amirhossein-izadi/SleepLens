# CI/CD Guidelines

> Continuous Integration and Deployment patterns.

---

## Git Workflow

### Branch Strategy

```
main (or master)
├── develop
│   ├── feature/user-auth
│   ├── feature/payment-api
│   └── bugfix/login-issue
└── release/v1.2.0
```

### Commit Messages

```bash
# Format
<type>(<scope>): <description>

# Types
feat:     New feature
fix:      Bug fix
docs:     Documentation
style:    Formatting
refactor: Code refactoring
test:     Tests
chore:    Maintenance

# Examples
feat(auth): add password reset functionality
fix(api): handle null response from external service
docs(readme): update installation instructions
```

---

## Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pycqa/isort
    rev: 5.13.2
    hooks:
      - id: isort
```

---

## GitHub Actions (Example)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.14'
          
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest-cov
          
      - name: Run tests
        env:
          POSTGRES_DB: test_db
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
          POSTGRES_HOST: localhost
        run: |
          pytest --cov=apps --cov-report=xml
          
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          files: ./coverage.xml
```

---

## Makefile Commands

```makefile
# Makefile
.PHONY: help install test lint format clean docker-up docker-down

help:
	@echo "Available commands:"
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run tests"
	@echo "  make lint         - Run linters"
	@echo "  make format       - Format code"
	@echo "  make docker-up    - Start Docker services"
	@echo "  make docker-down  - Stop Docker services"

install:
	pip install -r requirements.txt
	pre-commit install

test:
	pytest

lint:
	ruff check .

format:
	black .
	isort .

docker-up:
	docker-compose -f compose/dev/docker-compose.yml up -d

docker-down:
	docker-compose -f compose/dev/docker-compose.yml down

migrate:
	python manage.py makemigrations
	python manage.py migrate

superuser:
	python manage.py createsuperuser
```

---

## Deployment Pipeline

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Commit    │───▶│     CI      │───▶│   Staging   │───▶│  Production │
│             │    │  (GitHub)   │    │  (Auto)     │    │  (Manual)   │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                        │                   │                   │
                        ▼                   ▼                   ▼
                   - Run tests         - Deploy to          - Deploy to
                   - Lint              - staging server     - production
                   - Type check        - Run migrations     - Run migrations
                   - Build image       - Smoke tests        - Smoke tests
```

---

## Production Deployment

```bash
# Build and deploy
docker-compose -f compose/prod/docker-compose.yml build
docker-compose -f compose/prod/docker-compose.yml up -d

# Check status
docker-compose -f compose/prod/docker-compose.yml ps
docker-compose -f compose/prod/docker-compose.yml logs -f web

# Rollback
docker-compose -f compose/prod/docker-compose.yml up -d --rollback
```

---

## Health Checks

```yaml
# docker-compose.yml
services:
  web:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

```python
# health check endpoint
from django.http import JsonResponse
from django.db import connection

def health(request):
    # Check database
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
    
    return JsonResponse({"status": "healthy"})
```

---

## Monitoring

```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
    ports:
      - "9090:9090"

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
```

---

*Related: [06_TESTING_GUIDELINES.md](06_TESTING_GUIDELINES.md), [08_API_DESIGN.md](08_API_DESIGN.md)*