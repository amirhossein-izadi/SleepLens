# Django Patterns

> Battle-tested patterns for Django + DRF projects.

---

## Models

### One Model Per File

```python
# models/product.py
from django.db import models
import uuid

class Product(models.Model):
    # UUID v7 is sortable by creation time (native in Python 3.14+)
    id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["sku"]),
            models.Index(fields=["is_available", "-created_at"]),
        ]

    def __str__(self):
        return self.name
```

### Use TextChoices for Status Fields

```python
# models/order.py
from django.db import models

class OrderStatus(models.TextChoices):
    PENDING = "pending", "Pending"
    PROCESSING = "processing", "Processing"
    SHIPPED = "shipped", "Shipped"
    DELIVERED = "delivered", "Delivered"
    CANCELLED = "cancelled", "Cancelled"

class Order(models.Model):
    status = models.CharField(
        max_length=20,
        choices=OrderStatus.choices,
        default=OrderStatus.PENDING,
    )
```

---

## Serializers

### Separate Read/Write Serializers

```python
# api/v1/serializers/user.py
from rest_framework import serializers
from myapp.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "name", "email", "created_at"]

class UserCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()

    def validate_email(self, value):
        return value.lower().strip()

    def create(self, validated_data):
        return User.objects.create(**validated_data)
```

### Never Use `__all__`

```python
# ✅ Good
class Meta:
    fields = ["id", "name", "email", "created_at"]

# ❌ Bad
class Meta:
    fields = "__all__"
```

---

## Views & ViewSets

### Use Explicit Mixins

```python
# api/v1/views/user.py
from rest_framework import viewsets, mixins
from rest_framework.response import Response

class UserViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    queryset = User.objects.all()
    lookup_field = "id"  # Use UUID, not pk

    def get_serializer_class(self):
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def list(self, request, *args, **kwargs):
        qs = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(qs, many=True)
        return Response({"data": serializer.data})
```

### Never Expose Database PK

```python
# ✅ Good - use UUID
lookup_field = "id"  # UUID field

# ❌ Bad - exposes internal ID
lookup_field = "pk"
```

---

## URL Configuration

### Versioned API URLs

```python
# api/urls.py
from django.urls import path, include

app_name = "myapp_api"

urlpatterns = [
    path("v1/", include("myapp.api.v1.urls")),
]
```

```python
# api/v1/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from myapp.api.v1.views import UserViewSet

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="users")

app_name = "myapp_api_v1"

urlpatterns = [
    path("", include(router.urls)),
]
```

---

## Services Layer

### Explicit Service Calls — No Signals (2026 Rule)

Signals are implicit, hard to trace, and make testing painful. **Call services explicitly.**

```python
# ❌ Old way — signal fires "magically"
@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    if created:
        send_welcome_email(instance)

# ✅ 2026 way — explicit in the service/view
class UserService:
    @staticmethod
    def create_user(*, name: str, email: str) -> User:
        with transaction.atomic():
            user = User.objects.create(name=name, email=email)
            send_welcome_email(user)  # explicit, traceable, testable
            return user
```

**When signals ARE acceptable (2026 consensus):**
- Audit logging (decoupled, non-critical)
- Cache invalidation
- Third-party app integration where you can't modify the save call
- Cross-app decoupling where explicit calls would create circular dependencies

**When to NEVER use signals:**
- Business logic that must be traceable
- Sending emails/notifications on user actions
- Triggering background tasks (use Django 6.0 Tasks instead)
- Data validation or transformation

### Django 6.0+ Background Tasks (Built-in)

Django 6.0 introduced a built-in Tasks framework. Use it instead of Celery for simple background jobs.

```python
# ✅ Django 6.0 Tasks — for simple background jobs
from django.tasks import task

@task
def send_welcome_email(user_id: str):
    user = User.objects.get(id=user_id)
    # send email...

# Enqueue the task
send_welcome_email.enqueue(user_id=str(user.id))

# ✅ Celery — for complex workflows (retries, scheduling, chains)
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def process_large_dataset(self, dataset_id: str):
    try:
        # complex processing...
    except Exception as exc:
        self.retry(exc=exc, countdown=60)
```

**When to use Django 6.0 Tasks:**
- Simple fire-and-forget background jobs
- Sending emails, notifications
- Light data processing
- No complex retry/scheduling needs

**When to use Celery:**
- Complex retry logic with exponential backoff
- Task chaining and workflows
- Periodic/scheduled tasks (celery-beat)
- Heavy data processing with progress tracking
- Distributed task execution across multiple workers

### Pure Functions with Keyword-Only Args

```python
# services/user_service.py
from django.db import transaction

class UserService:
    @staticmethod
    def create_user(*, name: str, email: str) -> User:
        """Create a new user with validation."""
        email = email.lower().strip()
        
        if User.objects.filter(email=email).exists():
            raise ValueError("Email already exists")
        
        with transaction.atomic():
            return User.objects.create(name=name, email=email)

    @staticmethod
    def get_user_by_email(*, email: str) -> User | None:
        """Get user by email."""
        return User.objects.filter(email=email.lower()).first()
```

---

## Workflows (LangGraph Patterns)

For complex AI/LLM pipelines, use LangGraph with a structured sub-package approach.

### Workflow Structure

```
apps/workflows/pipelines/<pipeline_name>/
├── __init__.py              # Exports main graph builder
├── graph.py                 # Main workflow graph definition
├── graph_builder.py         # Graph assembly (nodes + edges)
├── state.py                 # State dataclass definitions
├── nodes/                   # Individual node implementations
│   ├── __init__.py
│   ├── node_a.py
│   ├── node_b.py
│   └── node_c.py
└── edges/                   # (Optional) Edge conditions
    ├── __init__.py
    └── routing_logic.py
```

### State Management

```python
# workflows/pipelines/order_processing/state.py
from dataclasses import dataclass, field
from typing import List, Optional
from decimal import Decimal

@dataclass
class OrderState:
    """Pipeline state - evolves through processing nodes."""
    order_id: str
    items: List[dict] = field(default_factory=list)
    total_amount: Decimal = Decimal("0.00")
    discount_applied: bool = False
    inventory_checked: bool = False
    payment_processed: bool = False
    error_message: Optional[str] = None
```

### Node Pattern

```python
# workflows/pipelines/order_processing/nodes/validator.py
from .state import OrderState

def validate_inventory(state: OrderState) -> OrderState:
    """Pure function - validates stock availability."""
    unavailable_items = []
    for item in state.items:
        if not check_stock(item["sku"], item["quantity"]):
            unavailable_items.append(item["sku"])
    
    if unavailable_items:
        return OrderState(
            order_id=state.order_id,
            items=state.items,
            total_amount=state.total_amount,
            error_message=f"Out of stock: {', '.join(unavailable_items)}"
        )
    
    # Return new state with inventory checked
    return OrderState(
        order_id=state.order_id,
        items=state.items,
        total_amount=state.total_amount,
        discount_applied=state.discount_applied,
        inventory_checked=True,
        payment_processed=state.payment_processed,
    )
```

### Graph Builder

```python
# workflows/pipelines/order_processing/graph_builder.py
from langgraph.graph import StateGraph, END
from .state import OrderState
from .nodes import validate_inventory, apply_discounts, process_payment

def build_order_workflow() -> StateGraph:
    """Build and return configured order processing graph."""
    workflow = StateGraph(OrderState)
    
    # Add nodes
    workflow.add_node("validate", validate_inventory)
    workflow.add_node("discount", apply_discounts)
    workflow.add_node("payment", process_payment)
    
    # Add edges with conditional routing
    workflow.set_entry_point("validate")
    workflow.add_edge("validate", "discount")
    workflow.add_edge("discount", "payment")
    workflow.add_edge("payment", END)
    
    return workflow.compile()
```

### Integration with Services

```python
# apps/orders/services/processor.py
from workflows.pipelines.order_processing.graph_builder import build_order_workflow
from .state import OrderState

class OrderService:
    def process_order(self, order: Order) -> dict:
        """Process order through workflow pipeline."""
        graph = build_order_workflow()
        
        initial_state = OrderState(
            order_id=str(order.id),
            items=[{"sku": i.sku, "quantity": i.quantity} for i in order.items.all()],
            total_amount=order.total,
        )
        
        final_state = graph.invoke(initial_state)
        
        if final_state.error_message:
            return {"success": False, "error": final_state.error_message}
        
        return {"success": True, "final_total": final_state.total_amount}
```

---

## Admin

### One Admin Class Per File

```python
# admin/user.py
from django.contrib import admin
from myapp.models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name", "email")
    readonly_fields = ("created_at", "updated_at")
```

---

## OpenAPI Schemas

### Use drf-spectacular

```python
# api/v1/schemas/user.py
from drf_spectacular.utils import extend_schema
from myapp.api.v1.serializers import UserSerializer

list_users_schema = extend_schema(
    operation_id="users_list",
    summary="List users",
    tags=["Users"],
    responses={200: UserSerializer(many=True)},
)

create_user_schema = extend_schema(
    operation_id="users_create",
    summary="Create user",
    tags=["Users"],
    request=UserCreateSerializer,
    responses={201: UserSerializer},
)
```

---

## Settings Structure

```
project_name/settings/
├── __init__.py         # Environment loader
├── base.py             # Shared settings
├── dev.py              # Development overrides
└── prod.py             # Production overrides
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

```python
# settings/__init__.py
import os
env = os.getenv("DJANGO_ENV", "dev")
if env == "prod":
    from .prod import *
else:
    from .dev import *
```

---

## Testing

### Use pytest

```python
# tests/v1/test_user.py
import pytest
from django.urls import reverse

@pytest.mark.django_db
class TestUserList:
    def test_list_success(self, api_client, user):
        api_client.force_authenticate(user=user)
        url = reverse("myapp_api_v1:users-list")
        response = api_client.get(url)
        assert response.status_code == 200

    def test_list_unauthorized(self, api_client):
        url = reverse("myapp_api_v1:users-list")
        response = api_client.get(url)
        assert response.status_code == 401
```

---

## Common Patterns

### Repository Pattern

```python
class UserRepository:
    def __init__(self, model):
        self.model = model

    def find_by_id(self, id: str):
        return self.model.objects.filter(id=id).first()

    def find_all(self):
        return self.model.objects.all()

    def create(self, **kwargs):
        return self.model.objects.create(**kwargs)
```

### API Response Format

```python
from rest_framework.response import Response

def api_response(data=None, error=None, status=200):
    """Standard API response format."""
    return Response({
        "success": status < 400,
        "data": data,
        "error": error,
    })
```

---

## Django 6.0 Features (December 2025)

> Requires Python 3.14+. Django 6.0 includes async ORM, built-in background tasks, CSP support.

### Built-in Background Tasks

```python
from django.background_task import background

@background(schedule=60)  # Run after 60 seconds
def send_welcome_email(user_id: int):
    """Simple background work - for complex tasks use Celery."""
    from accounts.models import User
    user = User.objects.get(id=user_id)
    # Send email logic

# Usage
def create_user(request):
    user = User.objects.create(email=request.POST["email"])
    send_welcome_email(user.id)  # Returns immediately
    return JsonResponse({"status": "created"})
```

### Async ORM

```python
from django.http import JsonResponse
from django.core.paginator import AsyncPaginator
import asyncio

class UserListView(View):
    async def get(self, request):
        # Native async ORM methods
        users = await User.objects.filter(is_active=True).alimit(100)
        return JsonResponse({"users": list(users)})

async def dashboard(request):
    # Parallel queries with gather
    stats, users, orders = await asyncio.gather(
        Stats.objects.aget_latest(),
        User.objects.acount(),
        Order.objects.filter(status="pending").acount()
    )
    return JsonResponse({"stats": stats, "users": users, "orders": orders})

# Async pagination
async def paginated_users(request):
    paginator = AsyncPaginator(User.objects.all(), per_page=20)
    page = await paginator.apage(int(request.GET.get("page", 1)))
    return JsonResponse({
        "users": list(page.object_list),
        "has_next": page.has_next(),
    })
```

### Security Features

```python
# settings/prod.py
# Content Security Policy
MIDDLEWARE += ["django.middleware.csp.CSPMiddleware"]
CSP_DEFAULT_SRC = ["'self'"]
CSP_SCRIPT_SRC = ["'self'", "https://analytics.example.com"]
CSP_REPORT_ONLY = True  # Start with report-only mode

# BigAutoField default for new projects
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

### Model Enhancements

```python
from django.db import models
from django.db.models import StringAgg

class Order(models.Model):
    total = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(paid__lte=models.F("total")),
                name="paid_cannot_exceed_total",
            )
        ]

# StringAgg now cross-database (was PostgreSQL-only)
@property
def tag_list(self):
    return StringAgg("tags__name", delimiter=", ")
```

### Other Features

- **Template partials**: `{% partialdef name %}...{% endpartialdef %}`
- **Email policy**: `email.message(policy=email.policy.SMTP)`
- **PBKDF2**: 1.2M iterations (was ~600K) - automatic security upgrade

---

## Django Async Best Practices

### When to Use Async

| Scenario | Use |
|----------|-----|
| Simple CRUD | Sync views |
| Multiple API calls | Async views |
| WebSockets | Async views |
| Parallel DB queries | Async with `gather()` |
| CPU-intensive | Sync (or Celery) |

### Async View Pattern

```python
class APIView(View):
    async def get(self, request):
        result = await self.fetch_data()  # Always await async calls
        return JsonResponse(result)

    async def fetch_data(self):
        async with aiohttp.ClientSession() as session:
            return await (await session.get(url)).json()

# BAD: Never call sync ORM in async view
def bad_view(request):
    user = User.objects.first()  # Blocks!

# GOOD: Use async ORM
async def good_view(request):
    user = await User.objects.afirst()  # Native async
```

---

## Celery Best Practices

### Beat Schedule in Separate File

```python
# apps/emails/beat_schedule.py
beat_schedule = {
    "poll-all-integrations": {
        "task": "emails.tasks.poll_all_active_integrations",
        "schedule": 60.0,  # Every 60 seconds
    },
}
```

```python
# settings/base.py
from apps.emails.beat_schedule import beat_schedule

CELERY_BEAT_SCHEDULE = beat_schedule
```

### Task Patterns

```python
# tasks.py
import structlog  # Use structlog, not logging
from celery import shared_task

logger = structlog.get_logger(__name__)

@shared_task(bind=True, max_retries=3)
def process_data(self, *, item_id: str) -> dict:
    """Process data with retry logic."""
    try:
        result = process_item(item_id)
        logger.info("item_processed", item_id=item_id, success=True)
        return {"success": True, "data": result}
    except RetryableError as e:
        logger.warning("retry_attempt", item_id=item_id, attempt=self.request.retries)
        raise self.retry(countdown=60, exc=e)
    except Exception as e:
        logger.error("processing_failed", item_id=item_id, error=str(e))
        return {"success": False, "error": str(e)}
```

---

*Related: [02_PYTHON_CODING_STANDARDS.md](02_PYTHON_CODING_STANDARDS.md), [04_DOCKER_NGINX_SETUP.md](04_DOCKER_NGINX_SETUP.md)*
