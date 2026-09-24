# Python Coding Standards

> Pythonic patterns, type hints, and best practices for maintainable code.

---

## Core Principles

1. **Immutability** - Create new objects, never mutate existing ones
2. **Explicit over implicit** - Clear intent, no magic
3. **Small functions** - < 50 lines per function
4. **Type hints everywhere** - Full type coverage

---

## Naming Conventions

| Type | Style | Example |
|------|-------|---------|
| Class | PascalCase | `UserService` |
| Function | snake_case | `get_user_by_id` |
| Variable | snake_case | `user_count` |
| Constant | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| File | snake_case | `user_service.py` |
| Enum | PascalCase | `UserStatus` |

---

## Type Hints (CRITICAL)

### Always Use Type Hints

```python
# ✅ Good
def get_user(user_id: str) -> User | None:
    """Get user by ID."""
    return User.objects.filter(id=user_id).first()

def process_items(items: list[dict]) -> list[str]:
    """Process items and return results."""
    return [item["name"] for item in items]

# ❌ Bad
def get_user(user_id):
    return User.objects.filter(id=user_id).first()
```

### Advanced Type Hints

```python
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')

class Repository(Protocol):
    """Protocol for structural subtyping."""
    def find_by_id(self, id: str) -> dict | None: ...
    def save(self, entity: dict) -> dict: ...

class UserRepository:
    def find_by_id(self, id: str) -> dict | None:
        return {"id": id, "name": "Test"}
    
    def save(self, entity: dict) -> dict:
        return entity

# Union types (Python 3.10+)
def format_value(value: str | int | None) -> str:
    match value:
        case str():
            return value.upper()
        case int():
            return str(value)
        case None:
            return "empty"

# TypeVar for generics (Python 3.12+ simplified)
def first_item(items: list[T]) -> T | None:
    """Get first item from list or None if empty."""
    return items[0] if items else None
```

---

## Immutability (CRITICAL)

### Never Mutate Existing Objects

```python
# ❌ Wrong - mutates original
def add_item(items: list, item: dict) -> None:
    items.append(item)  # Mutates!

# ✅ Correct - returns new list
def add_item(items: list[dict], item: dict) -> list[dict]:
    return [*items, item]

# ✅ Or use tuple for true immutability
def add_item(items: tuple, item: dict) -> tuple:
    return (*items, item)
```

### Use Frozen Dataclasses

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class User:
    """Immutable user entity."""
    id: str
    name: str
    email: str

# This raises FrozenInstanceError
user = User("1", "John", "john@example.com")
user.name = "Jane"  # ❌ Error!
```

---

## Dataclasses as DTOs

```python
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class CreateUserRequest:
    """Request DTO for creating a user."""
    name: str
    email: str
    age: Optional[int] = None
    tags: list[str] = field(default_factory=list)

@dataclass
class UserResponse:
    """Response DTO for user data."""
    id: str
    name: str
    email: str
    created_at: str
```

---

## Function Design

### Keyword-Only Arguments

```python
# ✅ Good - explicit, hard to misuse
def create_user(*, name: str, email: str, age: int | None = None) -> User:
    return User.objects.create(name=name, email=email, age=age)

# ❌ Bad - positional args can be confusing
def create_user(name, email, age=None):
    return User.objects.create(name, email, age)

# Usage
user = create_user(name="John", email="john@example.com")
```

### Small Functions & Sub-Packaging

Functions should be small and focused:

```python
# ✅ Good - focused, testable
def validate_email(email: str) -> bool:
    """Validate email format."""
    return "@" in email and "." in email.split("@")[1]

def sanitize_name(name: str) -> str:
    """Sanitize user name."""
    return name.strip().title()

def create_user(name: str, email: str) -> User:
    """Create a new user with validation."""
    if not validate_email(email):
        raise ValueError("Invalid email")
    
    sanitized = sanitize_name(name)
    return User.objects.create(name=sanitized, email=email)
```

### Sub-Package Long Code

When a module approaches 200 lines, split into a sub-package:

```
# ❌ Bad - single 800+ line file
workflows/pipelines/email_intake.py

# ✅ Good - sub-packaged by feature
workflows/pipelines/email_intake/
├── __init__.py           # Orchestrator (main entry point)
├── orchestrator.py       # Pipeline flow control
├── intake.py            # Intake phase logic
├── routing.py           # Routing logic
├── nodes/               # Individual processing nodes
│   ├── __init__.py
│   ├── noise_filter.py
│   ├── preprocessor.py
│   ├── storage.py
│   └── threader.py
└── state.py             # Pipeline state dataclasses
```

**Rule**: Create a sub-package when:
- File exceeds 200 lines
- Multiple related classes/functions with distinct purposes
- Clear separation of concerns exists (e.g., nodes in a pipeline)

---

## Context Managers

### For Resource Management

```python
from contextlib import contextmanager

@contextmanager
def database_transaction(db):
    """Context manager for database transactions."""
    try:
        yield
        db.commit()
    except Exception:
        db.rollback()
        raise

# Usage
with database_transaction(db):
    db.execute("INSERT INTO users ...")
```

### Class-Based

```python
class FileProcessor:
    def __init__(self, filename: str):
        self.filename = filename
        self.file = None

    def __enter__(self):
        self.file = open(self.filename, 'r')
        return self.file

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.file:
            self.file.close()
        return False
```

---

## Decorators

### Function Decorator

```python
from functools import wraps
import time

def timing(func):
    """Decorator to measure execution time."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end - start:.2f}s")
        return result
    return wrapper

@timing
def slow_function():
    time.sleep(1)
```

---

## Error Handling

### Custom Exceptions

```python
class DomainError(Exception):
    """Base exception for domain errors."""
    pass

class UserNotFoundError(DomainError):
    """Raised when user is not found."""
    def __init__(self, user_id: str):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")

class ValidationError(DomainError):
    """Raised when validation fails."""
    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")
```

### Exception Groups (Python 3.11+)

```python
try:
    # Multiple operations
    pass
except* ValueError as eg:
    for exc in eg.exceptions:
        print(f"ValueError: {exc}")
except* TypeError as eg:
    for exc in eg.exceptions:
        print(f"TypeError: {exc}")
```

---

## Import Order

```python
# 1. Standard library
import os
from typing import Optional

# 2. Third-party
from django.db import models
from rest_framework import serializers

# 3. Local application
from myapp.models import User
from myapp.services import UserService
```

---

## Line Length & Formatting

- **Max line length**: 100 characters (Black default: 88)
- **Use Black** for formatting
- **Use isort** for import sorting
- **Use ruff** for linting

```bash
# Format code
black .
isort .
ruff check . --fix
```

---

## Property Decorators

```python
class User:
    def __init__(self, name: str):
        self._name = name

    @property
    def name(self) -> str:
        """Read-only property."""
        return self._name

    @property
    def email(self) -> str | None:
        return self._email

    @email.setter
    def email(self, value: str) -> None:
        if '@' not in value:
            raise ValueError("Invalid email")
        self._email = value
```

---

## Async/Await

### Use httpx for HTTP Requests (2026 Standard)

`requests` is synchronous. Use `httpx` for both sync and async HTTP with built-in retry support.

```python
# ✅ Good — async with retry and timeout
import httpx

async def fetch_data(url: str) -> dict:
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url)
        response.raise_for_status()
        return response.json()

# ✅ Good — batch concurrent requests
async def fetch_all(urls: list[str]) -> list[dict]:
    async with httpx.AsyncClient(timeout=30.0) as client:
        tasks = [client.get(url) for url in urls]
        responses = await asyncio.gather(*tasks)
        return [r.json() for r in responses]

# ❌ Bad — synchronous, no timeout, no retry
import requests
response = requests.get(url)  # blocks forever if server hangs
```

### Retry with Exponential Backoff

```python
import asyncio
import httpx

async def fetch_with_retry(url: str, max_retries: int = 3) -> dict:
    """Fetch with exponential backoff retry."""
    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as exc:
            last_error = exc
            if attempt < max_retries:
                await asyncio.sleep(2 ** attempt)  # exponential backoff
    raise RuntimeError(f"Failed after {max_retries} attempts: {last_error}")
```

### Traditional Async/Await

```python
import asyncio

async def fetch_user(user_id: str) -> dict:
    """Async function for I/O-bound operations."""
    await asyncio.sleep(0.1)
    return {"id": user_id, "name": "Alice"}

async def fetch_all_users(user_ids: list[str]) -> list[dict]:
    """Concurrent execution with asyncio.gather."""
    tasks = [fetch_user(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)

# Run async code
asyncio.run(fetch_all_users(["1", "2", "3"]))
```

---

## Modern Python 3.10+ Features

### Pattern Matching (match/case)

Python 3.10+ structural pattern matching for cleaner conditionals:

```python
# ✅ Good - Pattern matching for HTTP status codes
def handle_status(status_code: int) -> str:
    match status_code:
        case 200:
            return "Success"
        case 404:
            return "Not found"
        case 500 | 502 | 503:
            return "Server error"
        case code if 400 <= code < 500:
            return f"Client error: {code}"
        case _:
            return f"Unknown status: {status_code}"

# Pattern matching with data structures
def process_event(event: dict) -> None:
    match event:
        case {"type": "click", "x": x, "y": y}:
            print(f"Click at ({x}, {y})")
        case {"type": "keypress", "key": key}:
            print(f"Key pressed: {key}")
        case {"type": unknown}:
            print(f"Unknown event type: {unknown}")
```

### Walrus Operator (:=)

Assignment expressions for cleaner loops and conditions:

```python
# ✅ Good - Walrus operator in while loop
while (line := input()) != "quit":
    process(line)

# ✅ Good - Walrus in list comprehension
results = [y for x in data if (y := transform(x)) > 0]

# ✅ Good - Walrus with regex
import re
if (match := re.search(r"\d+", text)):
    number = match.group(0)

# ❌ Bad - Without walrus (more verbose)
line = input()
while line != "quit":
    process(line)
    line = input()
```

### pathlib (Modern File Operations)

Use `pathlib` instead of `os.path` for cleaner file handling:

```python
from pathlib import Path

# ✅ Good - pathlib
config_path = Path("config") / "settings.json"
if config_path.exists():
    content = config_path.read_text()

# Path manipulation
parent = config_path.parent          # Path("config")
stem = config_path.stem              # "settings"
suffix = config_path.suffix          # ".json"

# Directory operations
output_dir = Path("output")
output_dir.mkdir(parents=True, exist_ok=True)

# ❌ Bad - os.path
import os
config_path = os.path.join("config", "settings.json")
if os.path.exists(config_path):
    with open(config_path) as f:
        content = f.read()
```

### Exception Groups (Python 3.11+)

Handle multiple exceptions simultaneously:

```python
# ✅ Good - Exception groups for batch operations
def process_batch(items: list[dict]) -> None:
    errors = []
    for item in items:
        try:
            process_item(item)
        except ValueError as e:
            errors.append(e)
    
    if errors:
        raise ExceptionGroup("Batch processing failed", errors)

# Handling exception groups
try:
    process_batch(large_dataset)
except* ValueError as eg:
    for exc in eg.exceptions:
        logger.error(f"Validation error: {exc}")
except* ConnectionError as eg:
    for exc in eg.exceptions:
        logger.error(f"Network error: {exc}")
```

---

## Generators

```python
def read_large_file(filename: str):
    """Generator for reading large files line by line."""
    with open(filename, 'r') as f:
        for line in f:
            yield line.strip()

# Memory-efficient processing
for line in read_large_file('huge.txt'):
    process(line)

# Generator expression
squares = (x**2 for x in range(1000000))  # Lazy!
```

---

## Python 3.13/3.14 Features

> Python 3.13 (Oct 2024): Type parameter defaults, improved REPL, 2-year support window.  
> Python 3.14 (Oct 2025): t-strings, deferred annotations, pathlib copy/move, UUID v7.

### Type Parameter Defaults (3.13, PEP 696)

```python
from typing import Generic, TypeVar

T = TypeVar("T")
DefaultT = TypeVar("DefaultT", default=int)  # Default value

class Container(Generic[T, DefaultT]):
    def __init__(self, value: T, default: DefaultT = None) -> None:
        self.value = value
        self.default = default

# Type inferred automatically
str_container = Container("hello")  # DefaultT = str
int_container = Container(42)        # DefaultT = int
```

### Template Strings (3.14, PEP 750)

Safer string processing - returns Template object for pre-processing:

```python
# t-strings return Template object, not string
name = "World"
template = t"Hello {name}!"

# Access before rendering (safe for SQL/HTML)
print(template.strings)           # ("Hello ", "!")
print(template.interpolations)    # Interpolation objects
result = template.render()        # Final rendering

# Use case: Safe HTML escaping before render
for interp in template.interpolations:
    safe_value = escape_html(interp.value)
```

### Deferred Annotations (3.14, PEP 649/749)

No more `from __future__ import annotations` needed:

```python
class User:
    id: int
    name: str
    related: list[User]  # Forward refs work without quotes!

# Access at runtime (returns strings, not evaluated types)
print(User.__annotations__)
```

### UUID v6/v7/v8 (3.14) - Sortable IDs

```python
import uuid

# UUID v7 - sortable by creation time (RECOMMENDED for DB keys)
user_id = uuid.uuid7()

# UUID v6 - timestamp-ordered (legacy compatibility)
request_id = uuid.uuid6()

# UUID v4 - random (existing behavior)
random_id = uuid.uuid4()
```

### Other 3.14 Additions

```python
from pathlib import Path

# Copy/move files directly with Path
source = Path("file.txt")
source.copy(Path("backup/file.txt"))  # New in 3.14
source.move(Path("archive/file.txt")) # New in 3.14

# except without brackets (PEP 758)
try:
    result = int(value)
except ValueError, TypeError:  # No parentheses!
    pass
```

### Subinterpreters (3.13, PEP 734)

```python
from concurrent.interpreters import Run

# Run code in isolated interpreter
def isolated_task():
    import random
    return random.randint(1, 100)

result = Run(isolated_task).result()
```

---

## Python asyncio Patterns (Recommended for I/O-Bound Operations)

### Use TaskGroup Over gather()

```python
import asyncio

async def fetch_user(user_id: int) -> dict:
    await asyncio.sleep(0.05)
    return {"user_id": user_id}

async def main():
    # TaskGroup - fails fast, cancels siblings
    async with asyncio.TaskGroup() as tg:
        task1 = tg.create_task(fetch_user(1))
        task2 = tg.create_task(fetch_user(2))
    # Both complete or both cancelled

    # Results available after block
    print(task1.result())
    print(task2.result())
```

### Semaphore for Rate Limiting

```python
import asyncio

semaphore = asyncio.Semaphore(20)  # Max 20 concurrent

async def bounded_request(url: str) -> dict:
    async with semaphore:
        return await fetch(url)

async def main():
    tasks = [bounded_request(url) for url in urls]
    results = await asyncio.gather(*tasks)
```

### Timeout for External Calls

```python
import asyncio

async def fetch_with_timeout(url: str) -> dict:
    try:
        async with asyncio.timeout(5):  # 5 second timeout
            return await fetch(url)
    except asyncio.TimeoutError:
        return {"error": "timeout"}
```

### Never Block the Event Loop

```python
# BAD - blocks entire event loop
time.sleep(10)
requests.get(url)

# GOOD - async alternatives
await asyncio.sleep(10)
async with aiohttp.ClientSession() as session:
    await session.get(url)

# GOOD - run blocking code in executor
loop = asyncio.get_event_loop()
await loop.run_in_executor(executor, blocking_function, arg)
```

### asyncio.to_thread() for Blocking Code

```python
import asyncio

# Offload CPU-bound/blocking work to thread pool
result = await asyncio.to_thread(blocking_function, arg)

# Or for CPU-bound work
result = await asyncio.get_event_loop().run_in_executor(
    None,  # Uses default thread pool
    cpu_intensive_function,
    arg
)
```

---

*Related: [01_PROJECT_STRUCTURE.md](01_PROJECT_STRUCTURE.md), [03_DJANGO_PATTERNS.md](03_DJANGO_PATTERNS.md)*