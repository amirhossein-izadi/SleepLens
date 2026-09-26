# Testing Guidelines

> pytest-django testing patterns for Django 6.0+ projects.

---

## Project Structure

```
tests/
├── __init__.py
├── conftest.py              # Shared fixtures
├── pytest.ini
└── apps/
    └── accounts/
        └── v1/
            └── test_user.py

# Or inside each app
app_name/
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── v1/
        └── test_user.py
```

---

## pytest Configuration

```ini
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = project_name.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
filterwarnings = 
    ignore::DeprecationWarning
```

---

## Fixtures (conftest.py)

```python
# conftest.py
import pytest
from django.contrib.auth import get_user_model

@pytest.fixture
def user(db):
    """Create a regular user."""
    User = get_user_model()
    return User.objects.create_user(
        username="testuser",
        email="test@example.com",
        password="testpass123"
    )

@pytest.fixture
def admin_user(db):
    """Create an admin user."""
    User = get_user_model()
    return User.objects.create_superuser(
        username="admin",
        email="admin@example.com",
        password="adminpass123"
    )

@pytest.fixture
def api_client():
    """DRF API client."""
    from rest_framework.test import APIClient
    return APIClient()

@pytest.fixture
def authenticated_client(api_client, user):
    """Authenticated API client."""
    api_client.force_authenticate(user=user)
    return api_client
```

---

## Database Access

```python
import pytest
from myapp.models import User, Article

@pytest.mark.django_db
def test_create_user():
    """Basic database access test."""
    user = User.objects.create_user(username='testuser', password='testpass')
    assert User.objects.filter(username='testuser').exists()
    assert user.check_password('testpass')

@pytest.mark.django_db(transaction=True)
def test_with_transactions():
    """Test that requires real transaction support."""
    from django.db import transaction

    with transaction.atomic():
        Article.objects.create(title='Test Article')

    assert Article.objects.count() == 1

@pytest.mark.django_db(databases=['default', 'secondary'])
def test_multiple_databases():
    """Test accessing multiple configured databases."""
    User.objects.using('default').create(username='user1')
    User.objects.using('secondary').create(username='user2')

    assert User.objects.using('default').count() == 1
    assert User.objects.using('secondary').count() == 1

# Mark entire module for database access
pytestmark = pytest.mark.django_db
```

---

## Model Tests

```python
# tests/v1/test_user.py
import pytest
from django.urls import reverse
from myapp.models import User

@pytest.mark.django_db
class TestUserModel:
    def test_create_user(self):
        user = User.objects.create_user(
            username="test",
            email="test@example.com",
            password="pass123"
        )
        assert user.username == "test"
        assert user.email == "test@example.com"
        assert user.check_password("pass123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            username="admin",
            email="admin@example.com",
            password="pass123"
        )
        assert user.is_staff is True
        assert user.is_superuser is True
```

---

## API Tests

```python
# tests/v1/test_user.py
import pytest
from django.urls import reverse
from rest_framework import status

@pytest.mark.django_db
class TestUserAPI:
    def test_list_users_unauthorized(self, api_client):
        url = reverse("accounts_api_v1:users-list")
        response = api_client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_list_users_success(self, authenticated_client, user):
        url = reverse("accounts_api_v1:users-list")
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK

    def test_create_user_invalid_email(self, api_client):
        url = reverse("accounts_api_v1:users-list")
        response = api_client.post(url, {"name": "Test", "email": "invalid"})
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_json_api(self, client):
        """Test JSON API endpoint."""
        response = client.post(
            '/api/items/',
            data={'name': 'New Item', 'price': 19.99},
            content_type='application/json'
        )
        assert response.status_code == 201
        data = response.json()
        assert data['name'] == 'New Item'
```

---

## Service Tests

```python
# tests/v1/test_user_service.py
import pytest
from myapp.services import UserService

@pytest.mark.django_db
class TestUserService:
    def test_create_user_success(self):
        user = UserService.create_user(
            name="John",
            email="john@example.com"
        )
        assert user.name == "John"
        assert user.email == "john@example.com"

    def test_create_user_duplicate_email(self):
        UserService.create_user(name="John", email="john@example.com")
        
        with pytest.raises(ValueError, match="Email already exists"):
            UserService.create_user(name="Jane", email="john@example.com")
```

---

## Testing Django 6.0+ Background Tasks

```python
# tests/test_tasks.py
import pytest
from django.tasks import task
from myapp.tasks import send_welcome_email

@pytest.mark.django_db
def test_send_welcome_email_task(mailoutbox, user):
    """Test task logic directly (without enqueueing)."""
    send_welcome_email(user_id=str(user.id))
    
    assert len(mailoutbox) == 1
    assert user.email in mailoutbox[0].to

@pytest.mark.django_db
def test_task_enqueues_successfully(user):
    """Test that task is enqueued correctly."""
    result = send_welcome_email.enqueue(user_id=str(user.id))
    
    assert result is not None
    assert result.status == "pending"  # or "completed" depending on backend
```

---

## Testing Emails with mailoutbox Fixture

```python
@pytest.mark.django_db
def test_send_email(mailoutbox):
    """Test email sending."""
    from django.core import mail
    
    mail.send_mail(
        subject='Welcome!',
        message='Thanks for signing up.',
        from_email='noreply@example.com',
        recipient_list=['user@example.com'],
    )

    assert len(mailoutbox) == 1
    assert mailoutbox[0].subject == 'Welcome!'
    assert mailoutbox[0].to == ['user@example.com']

@pytest.mark.django_db
def test_html_email(mailoutbox):
    """Test HTML email content."""
    from django.core.mail import EmailMultiAlternatives
    
    email = EmailMultiAlternatives(
        subject='HTML Email',
        body='Plain text version',
        from_email='sender@example.com',
        to=['recipient@example.com']
    )
    email.attach_alternative('<h1>HTML Version</h1>', 'text/html')
    email.send()

    assert len(mailoutbox) == 1
    assert '<h1>HTML Version</h1>' in mailoutbox[0].alternatives[0][0]
```

---

## Django Assertion Helpers

```python
from pytest_django.asserts import (
    assertContains,
    assertNotContains,
    assertRedirects,
    assertTemplateUsed,
    assertFormError,
    assertQuerySetEqual,
    assertHTMLEqual,
    assertJSONEqual,
    assertNumQueries,
)

@pytest.mark.django_db
def test_response_assertions(client):
    response = client.get('/products/')
    assertContains(response, 'Products', status_code=200)
    assertNotContains(response, 'Error')
    assertTemplateUsed(response, 'products/list.html')

@pytest.mark.django_db
def test_queryset_equality():
    from myapp.models import Item
    Item.objects.create(name='A')
    Item.objects.create(name='B')
    assertQuerySetEqual(
        Item.objects.order_by('name'),
        ['A', 'B'],
        transform=lambda x: x.name
    )
```

---

## Settings Fixture

```python
def test_with_specific_settings(settings):
    """Test with modified settings."""
    settings.USE_TZ = True
    assert settings.USE_TZ
    # Settings automatically revert after test
```

---

## Testing Best Practices

### Test Naming

```python
# ✅ Good - descriptive
def test_create_user_with_valid_email_succeeds():
    pass

def test_list_users_returns_only_active_users():
    pass

# ❌ Bad - vague
def test_create_user():
    pass

def test_list():
    pass
```

### AAA Pattern

```python
def test_example(self):
    # Arrange
    user = User.objects.create(name="John")
    
    # Act
    result = user.get_display_name()
    
    # Assert
    assert result == "John"
```

### One Assertion Per Test (when meaningful)

```python
# ✅ Good - focused tests
def test_user_has_email():
    assert user.email == "test@example.com"

def test_user_is_active_by_default():
    assert user.is_active is True

# ❌ Bad - multiple assertions
def test_user_properties():
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.name == "John"
```

---

## Running Tests

```bash
# All tests
pytest

# Specific app
pytest apps/accounts

# With coverage
pytest --cov=apps.accounts --cov-report=html

# Specific file
pytest apps/accounts/tests/v1/test_user.py

# Verbose
pytest -v

# Stop on first failure
pytest -x
```

---

## Test Categories

| Type | Purpose | Location |
|------|---------|----------|
| Unit | Single function/class | `tests/` or `app/tests/` |
| Integration | Multiple components | `tests/integration/` |
| API | HTTP endpoints | `tests/v1/` |
| E2E | Full user flows | `e2e/` |

---

## Mocking

```python
from unittest.mock import patch, MagicMock

@pytest.mark.django_db
def test_send_welcome_email():
    with patch("myapp.services.email_service.send") as mock_send:
        UserService.create_user(name="John", email="john@example.com")
        mock_send.assert_called_once()
```

---

## Factory Pattern

```python
# tests/factories.py
import factory
from django.contrib.auth import get_user_model

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()
    
    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password = factory.PostGenerationMethodCall("set_password", "password123")

# Usage
user = UserFactory()  # Creates user
users = UserFactory.create_batch(5)  # Creates 5 users
```

---

*Related: [03_DJANGO_PATTERNS.md](03_DJANGO_PATTERNS.md), [07_CI_CD.md](07_CI_CD.md)*