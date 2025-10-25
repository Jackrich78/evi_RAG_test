# API Specifications

**Last Updated:** 2025-10-24
**Status:** Template - Update for your project

## Overview

*This document describes API endpoints, request/response formats, and authentication. Update when you implement your API.*

**API Type:** [REST / GraphQL / gRPC]
**Base URL:** [e.g., `https://api.example.com/v1`]
**Authentication:** [JWT / OAuth / API Keys]

## Authentication

### Obtaining Access Token

```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expiresIn": 3600
}
```

### Using Access Token

Include in Authorization header:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Endpoints

### Users

#### GET /users/:id

**Description:** Get user by ID

**Authentication:** Required

**Parameters:**
- `id` (path, required): User ID

**Response (200):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "createdAt": "2025-01-01T00:00:00Z"
}
```

**Errors:**
- 401: Unauthorized (missing/invalid token)
- 404: User not found

---

#### POST /users

**Description:** Create new user

**Authentication:** Not required (registration)

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "securepassword123"
}
```

**Response (201):**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "newuser@example.com",
  "createdAt": "2025-01-01T00:00:00Z"
}
```

**Errors:**
- 400: Invalid input (validation error)
- 409: Email already exists

---

*Add your endpoints here*

## Request Format

**Content-Type:** `application/json`

**Required Headers:**
- `Content-Type: application/json`
- `Authorization: Bearer {token}` (for authenticated endpoints)

**Optional Headers:**
- `X-Request-ID`: Unique request identifier for tracing

## Response Format

### Success Response

```json
{
  "data": { ... },
  "meta": {
    "requestId": "req_123",
    "timestamp": "2025-01-01T00:00:00Z"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid email format",
    "details": [
      {
        "field": "email",
        "message": "Must be a valid email address"
      }
    ]
  },
  "meta": {
    "requestId": "req_123",
    "timestamp": "2025-01-01T00:00:00Z"
  }
}
```

## Status Codes

- **200 OK:** Successful GET/PUT/PATCH
- **201 Created:** Successful POST
- **204 No Content:** Successful DELETE
- **400 Bad Request:** Invalid input
- **401 Unauthorized:** Missing/invalid authentication
- **403 Forbidden:** Insufficient permissions
- **404 Not Found:** Resource doesn't exist
- **409 Conflict:** Resource conflict (e.g., duplicate)
- **429 Too Many Requests:** Rate limit exceeded
- **500 Internal Server Error:** Server error

## Pagination

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)

**Response:**
```json
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8
  }
}
```

## Filtering & Sorting

**Filtering:**
```http
GET /users?role=admin&status=active
```

**Sorting:**
```http
GET /users?sort=-createdAt,email
```
*Prefix with `-` for descending order*

## Rate Limiting

**Limits:**
- Anonymous: 100 requests/hour
- Authenticated: 1000 requests/hour

**Headers:**
```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Versioning

**Current Version:** v1

**URL Format:** `/v1/endpoint`

**Deprecation Policy:** 6 months notice before removing versions

## Testing

**API Documentation:** [Swagger/OpenAPI URL]

**Postman Collection:** [Link to collection]

**Test Credentials:**
- Email: test@example.com
- Password: test123

---

**Note:** Update this document when:
- Endpoints are added, modified, or removed
- Authentication changes
- Request/response formats change
- API version changes
