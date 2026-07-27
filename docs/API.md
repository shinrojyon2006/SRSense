# SRSense AI — API Documentation

This document describes the API endpoints provided by SRSense AI Foundation.

Auto-generated OpenAPI Interactive Documentation:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`
- **OpenAPI Schema**: `http://localhost:8000/openapi.json`
- **Postman Collection**: [`docs/SRSense_AI.postman_collection.json`](SRSense_AI.postman_collection.json)

---

## Base URL

- Development Backend: `http://localhost:8000/api`
- Production Docker Nginx: `http://localhost/api`

---

## Authentication Endpoints (`/api/auth`)

### 1. Register User
`POST /api/auth/register`

Creates a new user account and returns an access token and refresh token.

**Request Body**:
```json
{
  "name": "Jane Doe",
  "email": "jane@srsense.ai",
  "password": "Password123!",
  "password_confirmation": "Password123!",
  "role": "developer"
}
```

**Response (201 Created)**:
```json
{
  "access_token": "eyJhbGciOi...",
  "refresh_token": "d98f7...",
  "token_type": "bearer",
  "user": {
    "id": "c1f77d34-912b-4e4b-9e2e-13c54f5b5f21",
    "name": "Jane Doe",
    "email": "jane@srsense.ai",
    "role": "developer",
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

---

### 2. Login User
`POST /api/auth/login`

Authenticates credentials and returns a new access + refresh token pair.

**Request Body**:
```json
{
  "email": "jane@srsense.ai",
  "password": "Password123!"
}
```

---

### 3. Refresh Access Token (Token Rotation)
`POST /api/auth/refresh`

Revokes the old refresh token and issues a fresh token pair.

**Request Body**:
```json
{
  "refresh_token": "d98f7..."
}
```

---

### 4. Logout User
`POST /api/auth/logout`

Revokes the provided refresh token.

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "refresh_token": "d98f7..."
}
```

---

### 5. Get User Profile
`GET /api/auth/profile`

Returns current user info.

**Headers**: `Authorization: Bearer <access_token>`

---

## User Management Endpoints (`/api/users`)

### 1. Update Profile
`PUT /api/users/update`

Updates user's name or email.

**Headers**: `Authorization: Bearer <access_token>`

**Request Body**:
```json
{
  "name": "Jane Smith",
  "email": "janesmith@srsense.ai"
}
```
