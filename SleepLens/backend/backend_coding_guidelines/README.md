# Coding Guidelines

> Production-ready coding guidelines for Python/Django 6.0+ projects with modern best practices.

---

## Quick Start

Copy this folder to your new project:

```bash
cp -r /path/to/coding_guidelines ./my_new_project/
```

---

## Files Overview

| # | File | Purpose |
|---|------|---------|
| 01 | [01_PROJECT_STRUCTURE.md](01_PROJECT_STRUCTURE.md) | Folder structure, file organization |
| 02 | [02_PYTHON_CODING_STANDARDS.md](02_PYTHON_CODING_STANDARDS.md) | Python patterns, type hints, immutability |
| 03 | [03_DJANGO_PATTERNS.md](03_DJANGO_PATTERNS.md) | Django/DRF specific patterns |
| 04 | [04_DOCKER_NGINX_SETUP.md](04_DOCKER_NGINX_SETUP.md) | Docker, Nginx, docker-compose |
| 05 | [05_ENVIRONMENT_CONFIG.md](05_ENVIRONMENT_CONFIG.md) | Environment variables, settings |
| 06 | [06_TESTING_GUIDELINES.md](06_TESTING_GUIDELINES.md) | pytest, fixtures, testing patterns |
| 07 | [07_CI_CD.md](07_CI_CD.md) | GitHub Actions, deployment |
| 08 | [08_API_DESIGN.md](08_API_DESIGN.md) | REST API design, versioning |
| 09 | [09_DATABASE_PATTERNS.md](09_DATABASE_PATTERNS.md) | PostgreSQL + MongoDB dual DB |
| 10 | [10_SECURITY_MONITORING.md](10_SECURITY_MONITORING.md) | Security, logging, health checks |
| 11 | [11_GIT_WORKFLOW.md](11_GIT_WORKFLOW.md) | Branch strategy, commit messages |
| 12 | [12_PROJECT_CLEANUP.md](12_PROJECT_CLEANUP.md) | LLM artifacts, cleanup procedures |

---

## Core Principles

### 1. Many Small Files
- 200 lines per file target (not a hard limit — context decides)
- One model per file
- One service per file
- One viewset per file

### 2. Immutability
- Never mutate existing objects
- Create new objects instead
- Use frozen dataclasses for value objects

### 3. Type Hints Everywhere
- All functions have type hints
- Use Protocol for structural typing
- Union types (Python 3.10+)

### 4. Explicit Over Implicit
- No magic
- Clear naming
- Document complex logic

---

## Project Architecture

```
project_name/                 # Django project config
├── settings/
│   ├── base.py              # Shared settings
│   ├── dev.py               # Dev overrides
│   └── prod.py              # Production
├── common/                   # Shared utilities
└── ...

apps/                         # Django applications
├── accounts/
├── appointments/
├── reports/                  # Uses MongoDB
├── chatbot/
└── ...

lib/                          # Shared libraries
├── auth/                     # Custom authentication
└── base/                     # Base functionality

compose/                      # Docker compose
├── dev/
│   ├── docker-compose.yml
│   └── nginx.conf
└── prod/
```

---

## Database Architecture

Choose databases based on your data needs:

| Database | Use Case | When to Use |
|----------|----------|-------------|
| **PostgreSQL** | Primary relational data | ACID transactions, complex queries, JSONB |
| **Redis** | Cache, sessions, message broker | High-speed operations, pub/sub |
| **MongoDB** | Flexible schemas, analytics | Variable document structures, high write throughput |
| **Qdrant** | Vector search, embeddings | Semantic search, similarity matching |
| **MinIO/S3** | Object storage | File uploads, backups, large assets |

See [09_DATABASE_PATTERNS.md](09_DATABASE_PATTERNS.md) for configuration details.

---

## Quick Commands

```bash
# Setup
make install          # Install deps + pre-commit
make docker-up        # Start services

# Development
make test             # Run tests
make test-app APP=accounts
make lint             # Lint code
make format           # Format code
make migrate          # Run migrations
make mm APP=accounts  # Make migrations for app

# Deployment
docker-compose -f compose/prod/docker-compose.yml up -d --build

# Cleanup
make hooks-run        # Run pre-commit
rm -rf __pycache__/   # Clean cache
```

---

## Tools & Versions

- **Python**: 3.10+ (3.12 recommended for latest features)
- **Django**: 6.0+ (or 5.x with forward compatibility)
- **Package Manager**: uv (required) - see [UV Setup](#uv-setup)
- **Formatter**: Ruff (replaces Black)
- **Linter**: Ruff
- **Import Sorter**: Ruff (built-in)
- **Type Checking**: mypy or pyright
- **Testing**: pytest

### UV Setup (Required)

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Install dependencies (from pyproject.toml)
uv pip install -e .

# Add new dependency
uv add django-cors-headers

# Sync with lockfile
uv pip sync uv.lock
```

### Python 3.10+ Features
- Pattern matching (`match`/`case`)
- Union types with `|` syntax
- Parameter specification variables
- Exception groups (3.11+)

### Python 3.14+ Features
- Improved f-string parsing
- Type parameter syntax (PEP 695)
- `override` decorator

---

## Security Checklist (MANDATORY)

Before any commit:
- [ ] No hardcoded secrets
- [ ] All user inputs validated
- [ ] CSRF protection enabled
- [ ] Rate limiting on endpoints
- [ ] Error messages don't leak data

See [10_SECURITY_MONITORING.md](10_SECURITY_MONITORING.md).

---

## Git Workflow

```
main ──────────────────────────────► Production
  │
  └── develop ─────────────────────► Integration
       │
       ├── feature/feature-name
       ├── bugfix/issue-description
       └── hotfix/production-issue
```

- **Never commit migrations** (handled by .gitignore)
- **Never commit .env files**
- **Always run pre-commit** before push

See [11_GIT_WORKFLOW.md](11_GIT_WORKFLOW.md).

---

## Project Cleanup

LLMs generate artifacts. Regular cleanup prevents clutter:

```bash
# Find LLM artifacts
ls -la *.md

# Find unused scripts
grep -r "script_name" apps/ lib/ || echo "UNUSED"

# Delete after review
rm AI_GATEWAY_DIAGNOSTIC_REPORT.md
rm scripts/unused_script.py
```

See [12_PROJECT_CLEANUP.md](12_PROJECT_CLEANUP.md).

---

## Based On

- Django project structure best practices
- Python best practices (PEP 8, PEP 484 type hints)
- Django/DRF conventions
- Industry security standards (OWASP, CWE)
- Modern async patterns (httpx, asyncio)
- Clean architecture principles (layered design)

## Guideline Philosophy

These guidelines represent a **combination** of:
1. **Industry SOTA** - Modern Python/Django patterns (3.10+, Django 6)
2. **Proven patterns** - Battle-tested from real projects
3. **Forward compatibility** - Ready for upcoming features

**Guidelines are living documents** - evolve them as your project grows and new best practices emerge.

---

*Adjust these guidelines to fit your project's specific needs.*