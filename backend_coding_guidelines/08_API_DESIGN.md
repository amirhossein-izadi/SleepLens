# API Design Guidelines

> RESTful API design patterns and best practices.

---

## URL Structure

### Resource Naming

```bash
# ✅ Good - nouns, plural, lowercase
GET    /api/v1/users
GET    /api/v1/users/{id}
POST   /api/v1/users
PUT    /api/v1/users/{id}
DELETE /api/v1/users/{id}

# ❌ Bad - verbs, singular
GET    /api/v1/getUsers
GET    /api/v1/user/{id}
POST   /api/v1/createUser
```

### Nested Resources

```bash
# ✅ Good - logical hierarchy
GET /api/v1/users/{user_id}/appointments
POST /api/v1/users/{user_id}/appointments

# ❌ Bad - too deep
GET /api/v1/users/{user_id}/appointments/{appointment_id}/payments/{payment_id}
```

### Actions on Resources

```bash
# ✅ Good - RESTful actions
POST   /api/v1/users/{id}/activate
POST   /api/v1/users/{id}/deactivate
POST   /api/v1/appointments/{id}/cancel

# Alternative - query params
POST /api/v1/appointments/{id}/status?action=cancel
```

---

## HTTP Methods

| Method | Usage | Idempotent |
|--------|-------|------------|
| GET | Retrieve resources | Yes |
| POST | Create resources | No |
| PUT | Replace entire resource | Yes |
| PATCH | Partial update | No |
| DELETE | Remove resource | Yes |

---

## Response Format

### Success Response

```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "name": "John Doe",
    "email": "john@example.com"
  },
  "message": null
}
```

### List Response

```json
{
  "success": true,
  "data": [
    {"id": "1", "name": "John"},
    {"id": "2", "name": "Jane"}
  ],
  "metadata": {
    "total": 100,
    "page": 1,
    "limit": 20,
    "pages": 5
  }
}
```

### Error Response

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {"field": "email", "message": "Must contain @"}
    ]
  }
}
```

---

## Status Codes

### Success

| Code | Usage |
|------|-------|
| 200 | OK - GET, PUT, PATCH |
| 201 | Created - POST |
| 204 | No Content - DELETE |

### Client Errors

| Code | Usage |
|------|-------|
| 400 | Bad Request - validation failed |
| 401 | Unauthorized - missing/invalid auth |
| 403 | Forbidden - no permission |
| 404 | Not Found - resource doesn't exist |
| 409 | Conflict - duplicate, state conflict |
| 422 | Unprocessable - business logic error |
| 429 | Too Many Requests - rate limit |

### Server Errors

| Code | Usage |
|------|-------|
| 500 | Internal Server Error |
| 502 | Bad Gateway |
| 503 | Service Unavailable |

---

## Pagination

```bash
# Request
GET /api/v1/users?page=2&limit=20

# Response
{
  "data": [...],
  "metadata": {
    "total": 100,
    "page": 2,
    "limit": 20,
    "pages": 5
  }
}
```

### Cursor-based Pagination

```bash
# For large datasets
GET /api/v1/users?cursor=eyJpZCI6MTAwfQ&limit=20
```

---

## Filtering & Sorting

### Filtering

```bash
# Single filter
GET /api/v1/users?status=active

# Multiple filters
GET /api/v1/users?status=active&role=admin

# Range
GET /api/v1/appointments?date_from=2024-01-01&date_to=2024-01-31
```

### Sorting

```bash
# Ascending
GET /api/v1/users?sort=created_at

# Descending
GET /api/v1/users?sort=-created_at

# Multiple
GET /api/v1/users?sort=-created_at,name
```

---

## Versioning

```bash
# URL versioning (recommended)
GET /api/v1/users
GET /api/v2/users

# Header versioning
Accept: application/vnd.myapp.v1+json
```

---

## Authentication

### Bearer Token

```bash
# Request
GET /api/v1/users
Authorization: Bearer <token>

# Response 401
{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or expired token"
  }
}
```

### Rate Limiting

```bash
# Response 429
{
  "success": false,
  "error": {
    "code": "RATE_LIMITED",
    "message": "Too many requests",
    "retry_after": 60
  }
}

# Headers
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1640000000
```

---

## OpenAPI Example

```yaml
paths:
  /users:
    get:
      operationId: users_list
      summary: List users
      tags: [Users]
      parameters:
        - name: page
          in: query
          schema:
            type: integer
            default: 1
        - name: limit
          in: query
          schema:
            type: integer
            default: 20
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/UserList'
```

---

## Best Practices

1. **Use HTTPS** - Always encrypt in transit
2. **Consistent URLs** - Plural nouns, lowercase
3. **Version your API** - `/api/v1/`
4. **Use proper status codes** - Don't use 200 for errors
5. **Paginate lists** - Never return unbounded results
6. **Filter & sort** - Enable flexible queries
7. **Document everything** - OpenAPI/Swagger

---

*Related: [03_DJANGO_PATTERNS.md](03_DJANGO_PATTERNS.md), [07_CI_CD.md](07_CI_CD.md)*