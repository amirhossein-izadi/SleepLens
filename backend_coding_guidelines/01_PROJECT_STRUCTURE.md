# Project Structure Guidelines

> Opinionated folder structure for maintainable, scalable Python/Django 6.0+ projects.

---

## Core Philosophy

**Many small files > Few large files**
- High cohesion, low coupling
- 200 lines target, 300 max per file (context-dependent: 205 lines with single well-defined purpose is fine; 195 lines with multiple unrelated concerns should split)
- Organize by feature/domain, not by type
- One model per file, one admin per file
- Sub-package design, keep related small files with a same function

---

## Django 6.0+ Project Structure

```
project_root/
├── project_name/           # Django project config
│   ├── settings/
│   │   ├── __init__.py     # Environment loader
│   │   ├── base.py         # Shared settings
│   │   ├── dev.py          # Development overrides
│   │   └── prod.py         # Production overrides
│   ├── urls.py
│   ├── wsgi.py
│   ├── asgi.py             # Required for WebSockets/Channels
│   └── celery.py
├── apps/                   # Django applications (registered via APPS_DIR)
│   ├── accounts/
│   ├── appointments/
│   └── your_app/
├── lib/                    # Shared libraries/submodules Pure Python (NO Django deps)
├── infrastructure/         # External service adapters (NO Django deps in core)
├── common/                 # Shared Django utilities (middleware, health checks)
├── docs/                   # Project documentation
├── compose/                # Docker compose (dev/prod)
├── deploy/                 # Deployment configs
├── nginx/                  # Nginx configs
├── scripts/                # Utility scripts (delete after use)
├── tests/                  # Integration/E2E tests
├── manage.py
├── requirements.txt
├── pyproject.toml          # Modern Python project config
├── Makefile
├── Dockerfile
├── .env.example
├── .env.dev
├── .env.prod.example
├── .gitignore
├── .pre-commit-config.yaml
└── pytest.ini
```

### Django Apps Directory Setup

The `apps/` directory is registered in Python path to allow loose coupling:

```python
# project_name/settings/base.py
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
APPS_DIR = BASE_DIR.parent / "apps"

if str(APPS_DIR) not in sys.path:
    sys.path.insert(0, str(APPS_DIR))
```

This allows apps to be placed in `apps/` folder (same level as project folder) rather than inside the project.

---

## lib/ - Pure Python Layer

**NO Django dependencies allowed. Use only Python standard library.**

```
lib/
├── __init__.py
├── contracts/              # Dataclasses for data exchange
│   ├── __init__.py
│   ├── normalized_message.py
│   └── sync_session.py
├── base/                   # Base classes and interfaces
│   └── __init__.py
└── constants/              # Project-level constants
    └── __init__.py
```

**Usage**: Data contracts, pure business logic, utilities that don't need Django.

```python
# lib/contracts/message.py
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class NormalizedMessage:
    """Pure data contract - no Django imports."""
    message_id: str
    sender: str
    subject: str
    body: str
    received_at: datetime
```

---

## infrastructure/ - External Service Adapters

**NO Django dependencies in core adapter code.**

```
infrastructure/
├── __init__.py
├── email/                  # Email protocols
│   ├── __init__.py
│   ├── base_adapter.py     # Abstract interface
│   ├── imap/
│   │   ├── __init__.py
│   │   ├── adapter.py      # IMAP4_SSL implementation
│   │   └── config.py       # IMAPConfig dataclass
│   └── smtp/
├── llm/                    # LLM clients
│   ├── __init__.py
│   ├── client.py           # OpenAI/LangChain wrapper
│   └── config.py
├── databases/              # (Optional: MongoDB, Qdrant adapters)
│   └── __init__.py
└── storage/                # (Optional: MinIO/S3 adapters)
    └── __init__.py
```

**Key Rules**:
- Adapters implement abstract interfaces from `base_adapter.py`
- Use dataclasses for configuration (not Django models)
- Return/accept `lib/contracts/` dataclasses, not Django models
- External I/O only: email, LLM, databases, storage

```python
# infrastructure/email/base_adapter.py
from abc import ABC, abstractmethod
from typing import List
from lib.contracts import NormalizedMessage

class EmailAdapter(ABC):
    """Abstract interface - no Django deps."""
    
    @abstractmethod
    def connect(self) -> None: ...
    
    @abstractmethod
    def fetch_unseen(self) -> List[NormalizedMessage]: ...
```

---

## common/ - Shared Django Utilities

**Django-specific shared code that doesn't belong to any single app.**

```
common/
├── __init__.py
├── middleware/             # Django middleware
│   ├── __init__.py
│   └── request_logging.py  # structlog middleware
├── health/                 # Health check endpoints
│   ├── __init__.py
│   └── checks.py
├── exceptions/             # Custom exception handlers
│   └── __init__.py
└── constants/              # Shared constants
    └── __init__.py
```

---

## Django App Structure

```
app_name/
├── __init__.py
├── apps.py
├── constants.py            # App-level constants
├── tasks/                  # Django 6.0+ / Celery background tasks (folder, not file)
│   ├── __init__.py
│   ├── process_meeting.py
│   └── send_notifications.py
├── models/                 # ONE MODEL PER FILE
│   ├── __init__.py
│   ├── user.py
│   ├── profile.py
│   └── relations.py
├── admin/                  # ONE ADMIN PER FILE
│   ├── __init__.py
│   ├── user.py
│   └── profile.py
├── api/
│   ├── __init__.py
│   ├── urls.py             # Version router
│   └── v1/
│       ├── __init__.py
│       ├── urls.py
│       ├── views/
│       │   ├── __init__.py
│       │   └── user.py
│       ├── serializers/
│       │   ├── __init__.py
│       │   └── user.py
│       └── schemas/
│           ├── __init__.py
│           └── user.py
├── services/               # Business logic (explicit calls, no signals)
│   ├── __init__.py
│   ├── user_service.py
│   └── utils.py
├── utils/                  # App-specific utilities
│   ├── __init__.py
│   ├── choices.py
│   └── validation.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── v1/
│       └── test_user.py
└── migrations/
    ├── __init__.py
    └── 0001_initial.py
```

## URL Mapping Pattern

### Root URL Configuration

```python
# project_name/urls.py
from django.urls import include, path

api_urlpatterns = [
    path("api/accounts/", include("accounts.api.urls")),
    path("api/reports/", include("reports.api.urls")),
    path("api/appointments/", include("appointments.api.urls")),
    # Add new apps here
]

urlpatterns = [
    path("project/", include(base_urlpatterns + api_urlpatterns)),
]
```

### App URL Configuration

```python
# apps/accounts/api/urls.py
from django.urls import path
from rest_framework.routers import DefaultRouter

app_name = "accounts_api"

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")
router.register(r"patients", PatientViewSet, basename="patients")

urlpatterns = router.urls
```

---

## Why This Structure Works

| Layer | Purpose | Dependencies | Benefit |
|-------|---------|--------------|---------|
| `lib/` | Pure Python contracts & utilities | Python stdlib only | Testable without Django, reusable |
| `infrastructure/` | External service adapters | Vendor SDKs only | Clean boundaries, swappable implementations |
| `common/` | Shared Django utilities | Django | Cross-cutting concerns (logging, health) |
| `apps/*/models/` | Data layer | Django ORM | One file per model = easy navigation |
| `apps/*/admin/` | Admin interface | Django | Isolated admin logic |
| `apps/*/api/v1/` | REST API | DRF | Versioned, clean separation |
| `apps/*/services/` | Business logic | Django ORM | Reusable, testable, explicit calls |
| `apps/*/utils/` | App-specific helpers | Django | Localized utilities |
| `apps/*/tests/` | Test suite | pytest | Organized by version |

---

## File Naming Conventions

```
# Models
user.py           # Single model
profile.py        # Single model
relations.py      # M2M through models

# Services
user_service.py   # User-related business logic
booking.py        # Booking operations

# Views/Serializers
user.py           # User viewset + serializer
appointment.py    # Appointment viewset + serializer
```

---

## Import Patterns

```python
# models/__init__.py
from .user import User
from .profile import Profile

__all__ = ["User", "Profile"]

# services/__init__.py
from .user_service import UserService

__all__ = ["UserService"]
```

---

## When to Create New Files

| Signal | Action |
|--------|--------|
| File > 200 lines | Split by feature |
| Multiple classes same purpose | Separate files |
| Reusable utility | Create `utils/` module |
| Business logic in views | Move to `services/` |
| Repeated code | Extract to shared module |

---

## Anti-Patterns to Avoid

```
❌ models.py                     # All models in one file
❌ views.py                      # All views in one file  
❌ utils.py                       # Mixed utilities
❌ admin.py                      # Root-level admin
❌ api/urls.py                    # All URLs in one file
❌ 3000-line files               # Impossible to navigate - sub-package instead
❌ signals.py                     # Implicit logic (use explicit service calls)
❌ infrastructure/*.py            # Long adapter files - use sub-packages
❌ lib/ importing django        # lib/ must be Django-free
❌ infrastructure/ importing models  # Use dataclasses for data exchange
```

---

*Related: [02_PYTHON_CODING_STANDARDS.md](02_PYTHON_CODING_STANDARDS.md)*