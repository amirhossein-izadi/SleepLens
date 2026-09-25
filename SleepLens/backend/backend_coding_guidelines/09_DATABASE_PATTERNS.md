# Database Patterns

> Modern database selection and patterns for Django 6.0+ projects.

---

## Architecture Overview

Choose databases based on your data needs. Most projects need only PostgreSQL + Redis. Add specialized stores only when justified.

```
┌─────────────────────────────────────────────────────────────────┐
│                        Django Application                        │
├──────────────┬──────────────┬──────────────┬────────────────────┤
│  PostgreSQL  │    Redis     │   Qdrant     │      MinIO         │
│  ──────────  │  ──────────  │  ──────────  │  ──────────────    │
│  • Users     │  • Cache     │  • Vectors   │  • File uploads    │
│  • Auth      │  • Sessions  │  • Embeddings│  • Media files     │
│  • Relations │  • Broker    │  • Semantic  │  • Backups         │
│  • ACID      │  • Rate lim. │    search    │  • Static assets   │
│  • JSONB     │  • Pub/Sub   │  • Similarity│  • Large objects   │
└──────────────┴──────────────┴──────────────┴────────────────────┘
```

---

## Database Selection Guide

### PostgreSQL (Primary Database)

**Use when:**
- Relational data with foreign keys and constraints
- ACID transactions required
- Complex queries with joins
- Full-text search (built-in)
- JSON data with indexing (JSONB)
- Geospatial data (PostGIS)

**Version:** PostgreSQL 16+ (17 recommended)

```python
# settings/base.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST", "localhost"),
        "PORT": config("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,  # Connection pooling
        "CONN_HEALTH_CHECKS": True,  # Django 6.0+
    }
}
```

### Redis (Cache & Message Broker)

**Use when:**
- Caching query results and sessions
- Celery message broker
- Rate limiting
- Real-time pub/sub
- Leaderboards and counters

**Version:** Redis 7+

```python
# settings/base.py
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": config("REDIS_URL", "redis://localhost:6379/0"),
    }
}

CELERY_BROKER_URL = config("REDIS_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = config("REDIS_URL", "redis://localhost:6379/1")
```

### Qdrant (Vector Database)

**Use when:**
- Semantic search over text embeddings
- RAG (Retrieval-Augmented Generation) pipelines
- Similarity matching
- AI/ML feature storage

**Version:** Qdrant 1.7+

```python
# settings/base.py
QDRANT_CONFIG = {
    "url": config("QDRANT_URL", "http://localhost:6333"),
    "collection": config("QDRANT_COLLECTION", "embeddings"),
    "vector_size": 1536,  # text-embedding-3-small
    "distance": "Cosine",
}
```

**Why Qdrant over pgvector:**
- Better performance for large vector datasets (>1M vectors)
- Built-in filtering and payload storage
- Better HNSW index tuning
- REST and gRPC APIs

**When to use pgvector instead:**
- Small vector datasets (<100K vectors)
- Want to keep everything in PostgreSQL
- Simple similarity search without complex filtering

### MinIO (Object Storage)

**Use when:**
- File uploads and media storage
- Backup storage
- Large file serving
- S3-compatible API needed

**Why MinIO over local filesystem:**
- Horizontal scaling
- Built-in replication
- S3-compatible API
- Lifecycle management
- Better for production deployments

```python
# settings/base.py
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "endpoint_url": config("MINIO_ENDPOINT", "http://localhost:9000"),
            "access_key": config("MINIO_ACCESS_KEY"),
            "secret_key": config("MINIO_SECRET_KEY"),
            "bucket_name": config("MINIO_BUCKET", "media"),
            "region_name": "us-east-1",
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
```

### MongoDB (Document Database)

**Use when:**
- Flexible/evolving schema required
- Large documents with variable structure
- Analytics and logging data
- No complex relationships needed
- High write throughput needed

**Version:** MongoDB 7+

**When NOT to use MongoDB:**
- Need ACID transactions across collections
- Complex joins and relationships
- Strict schema validation required
- → Use PostgreSQL with JSONB instead

---

## PostgreSQL Configuration (Django 6.0+)

### Settings with Connection Pooling

```python
# settings/base.py
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": config("POSTGRES_DB"),
        "USER": config("POSTGRES_USER"),
        "PASSWORD": config("POSTGRES_PASSWORD"),
        "HOST": config("POSTGRES_HOST", "localhost"),
        "PORT": config("POSTGRES_PORT", "5432"),
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,  # Django 6.0+
        "OPTIONS": {
            "pool": {
                "min_size": 2,
                "max_size": 4,
                "timeout": 10,
            }
        },
    }
}
```

### Environment Variables

```bash
# .env
POSTGRES_DB=project
POSTGRES_USER=project
POSTGRES_PASSWORD=strong-random-password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
```

---

## Query Optimization

### PostgreSQL (Django ORM)

```python
# ✅ Good: Select only needed columns
users = User.objects.filter(is_active=True).values(
    "id", "first_name", "email"
)

# ✅ Good: Use select_related for ForeignKey
appointments = Appointment.objects.select_related(
    "patient", "doctor"
).all()

# ✅ Good: Use prefetch_related for ManyToMany
doctor = Doctor.objects.prefetch_related("specialties").get(id=doctor_id)

# ✅ Good: Use Django 6.0+ StringAgg (now cross-database)
from django.db.models import StringAgg

tags = Post.objects.annotate(
    tag_list=StringAgg("tags__name", delimiter=", ")
)

# ❌ Bad: N+1 query problem
for appointment in appointments:
    print(appointment.patient.first_name)  # Each iteration = 1 query
```

---

## Indexing Strategy

### PostgreSQL Indexes

```python
class Meta:
    indexes = [
        # Single column
        models.Index(fields=["email"]),
        
        # Composite index (equality first, then range)
        models.Index(fields=["status", "-created_at"]),
        
        # Partial index (PostgreSQL)
        models.Index(
            fields=["created_at"],
            condition=models.Q(status="active"),
        ),
    ]
```

---

## Transactions

### PostgreSQL (Django)

```python
from django.db import transaction

@transaction.atomic
def create_appointment_with_notification(patient_id, doctor_id, time_slot):
    appointment = Appointment.objects.create(
        patient_id=patient_id,
        doctor_id=doctor_id,
        time_slot=time_slot
    )
    send_notification(patient_id, doctor_id)
    return appointment
```

---

## Best Practices

### 1. Use UUIDs for Public IDs

```python
# ✅ Good: UUID v7 (sortable by creation time, native in Python 3.14+)
id = models.UUIDField(primary_key=True, default=uuid.uuid7, editable=False)

# ⚠️ Acceptable: UUID v4 (random, not sortable)
id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

# ❌ Bad: Auto-increment ID exposed in URLs
id = models.AutoField(primary_key=True)
```

### 2. Use Django 6.0+ BigAutoField (Default)

```python
# Django 6.0+ defaults to BigAutoField
# Only override if you have a specific reason
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
```

### 3. Connection Pooling

```python
# settings/base.py
DATABASES = {
    "default": {
        # ... other settings ...
        "CONN_MAX_AGE": 60,  # Keep connections alive for 60s
        "CONN_HEALTH_CHECKS": True,  # Django 6.0+
    }
}

# For production, use PgBouncer
# DATABASES["default"]["OPTIONS"] = {"sslmode": "require"}
```

### 4. Use PostgreSQL JSONB for Flexible Data

```python
from django.db import models
from django.contrib.postgres.fields import JSONField

class Report(models.Model):
    metadata = JSONField(default=dict)
    
    # Query JSONB fields
    # Report.objects.filter(metadata__has_key="status")
    # Report.objects.filter(metadata__status="completed")
```

---

## Docker Compose Database Services

```yaml
# compose/dev/docker-compose.yml
services:
  db:
    image: postgres:17-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-project}
      POSTGRES_USER: ${POSTGRES_USER:-project}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-strong-db-password}
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    command: ["redis-server", "--appendonly", "yes"]
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 5s
      retries: 10

  # Optional: Qdrant for vector search
  qdrant:
    image: qdrant/qdrant:v1.12
    volumes:
      - qdrant_data:/qdrant/storage
    ports:
      - "6333:6333"

  # Optional: MinIO for object storage
  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_ACCESS_KEY:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_SECRET_KEY:-minioadmin}
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"
      - "9001:9001"

volumes:
  pgdata:
  redis_data:
  qdrant_data:
  minio_data:
```

---

*Related: [03_DJANGO_PATTERNS.md](03_DJANGO_PATTERNS.md), [04_DOCKER_NGINX_SETUP.md](04_DOCKER_NGINX_SETUP.md)*
