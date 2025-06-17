# Authentication Documentation

## Overview

The Oprina API uses JWT (JSON Web Tokens) for authentication with support for both traditional email/password authentication and Google OAuth integration. All protected endpoints require a valid JWT token in the Authorization header.

## Authentication Methods

### 1. Email/Password Authentication

Traditional username and password authentication with JWT token issuance.

### 2. Google OAuth

OAuth 2.0 integration with Google for seamless third-party authentication.

## JWT Token Structure

### Token Format
```
Authorization: Bearer <JWT_TOKEN>
```

### Token Payload
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "exp": 1642781234,
  "iat": 1642777634,
  "sub": "user_id"
}
```

### Token Expiration
- **Default**: 24 hours (1440 minutes)
- **Configurable**: Via `ACCESS_TOKEN_EXPIRE_MINUTES` environment variable

## Authentication Endpoints

### Register New User

**Endpoint**: `POST /api/v1/auth/register`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "full_name": "John Doe",
  "preferred_name": "John",
  "work_type": "Software Developer",
  "ai_preferences": "Please provide detailed explanations"
}
```

**Response**:
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "John Doe",
    "preferred_name": "John",
    "work_type": "Software Developer",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "jwt-token-string",
  "token_type": "bearer"
}
```

### User Login

**Endpoint**: `POST /api/v1/auth/login`

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response**:
```json
{
  "message": "Login successful",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "John Doe",
    "last_login_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "jwt-token-string",
  "token_type": "bearer"
}
```

### Validate Token

**Endpoint**: `GET /api/v1/auth/validate`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "valid": true,
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true
  },
  "expires_at": "2024-01-16T10:30:00Z"
}
```

### Logout

**Endpoint**: `POST /api/v1/auth/logout`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "message": "Logout successful"
}
```

### Deactivate Account

**Endpoint**: `DELETE /api/v1/auth/deactivate`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "message": "Account deactivated successfully"
}
```

## Google OAuth Endpoints

### Initiate Google OAuth (Login)

**Endpoint**: `GET /api/v1/oauth/google/login`

**Response**: Redirects to Google OAuth consent screen

### Initiate Google OAuth (Signup)

**Endpoint**: `GET /api/v1/oauth/google/signup`

**Response**: Redirects to Google OAuth consent screen

### OAuth Callback

**Endpoint**: `GET /api/v1/oauth/callback`

**Query Parameters**:
- `code`: Authorization code from Google
- `state`: CSRF protection state parameter

**Response**: Redirects to frontend with authentication status

### Check OAuth Status

**Endpoint**: `GET /api/v1/oauth/status`

**Headers**: `Authorization: Bearer <token>`

**Response**:
```json
{
  "google_connected": true,
  "google_email": "user@gmail.com",
  "last_token_refresh": "2024-01-15T10:30:00Z",
  "token_expires_at": "2024-01-15T11:30:00Z"
}
```

### Connect OAuth Service

**Endpoint**: `GET /api/v1/oauth/connect/{service}`

**Parameters**:
- `service`: "google" or "microsoft"

**Headers**: `Authorization: Bearer <token>`

**Response**: Redirects to OAuth provider

### Disconnect OAuth Service

**Endpoint**: `POST /api/v1/oauth/disconnect`

**Headers**: `Authorization: Bearer <token>`

**Request Body**:
```json
{
  "service": "google"
}
```

**Response**:
```json
{
  "message": "Google OAuth disconnected successfully"
}
```

## Authentication Middleware

### Protected Endpoints

All endpoints requiring authentication use the `get_current_user` dependency:

```python
@router.get("/protected-endpoint")
async def protected_endpoint(
    current_user: dict = Depends(get_current_user)
):
    return {"user_id": current_user["id"]}
```

### Optional Authentication

Some endpoints support optional authentication using `get_current_user_optional`:

```python
@router.get("/optional-auth-endpoint")
async def optional_auth_endpoint(
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    if current_user:
        return {"authenticated": True, "user_id": current_user["id"]}
    return {"authenticated": False}
```

## Error Responses

### Authentication Errors

**401 Unauthorized**:
```json
{
  "error": "Authentication Error",
  "message": "Invalid authentication credentials",
  "path": "/api/v1/protected-endpoint"
}
```

**403 Forbidden**:
```json
{
  "error": "Forbidden",
  "message": "Insufficient permissions",
  "path": "/api/v1/admin-endpoint"
}
```

### Validation Errors

**400 Bad Request**:
```json
{
  "error": "Validation Error",
  "message": "Email already registered",
  "path": "/api/v1/auth/register"
}
```

**422 Unprocessable Entity**:
```json
{
  "error": "Validation Error",
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

## Security Considerations

### Password Requirements

- Minimum 8 characters
- Mix of uppercase, lowercase, numbers recommended
- bcrypt hashing with salt rounds

### JWT Security

- Tokens are stateless and cannot be revoked
- Short expiration times recommended
- Secure secret key management
- HTTPS required in production

### OAuth Security

- CSRF protection with state parameter
- Secure redirect URI validation
- Token refresh background service
- Encrypted token storage

## Client Implementation Examples

### JavaScript/TypeScript

```javascript
// Login
const login = async (email, password) => {
  const response = await fetch('/api/v1/auth/login', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ email, password }),
  });
  
  const data = await response.json();
  
  if (response.ok) {
    // Store token
    localStorage.setItem('token', data.access_token);
  }
  
  return data;
};

// Authenticated API calls
const apiCall = async (endpoint) => {
  const token = localStorage.getItem('token');
  
  const response = await fetch(endpoint, {
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json',
    },
  });
  
  return response.json();
};
```

### Python

```python
import requests

# Login
def login(email, password):
    response = requests.post(
        'http://localhost:8000/api/v1/auth/login',
        json={'email': email, 'password': password}
    )
    
    if response.status_code == 200:
        return response.json()['access_token']
    else:
        raise Exception('Login failed')

# Authenticated API calls
def api_call(endpoint, token):
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(endpoint, headers=headers)
    return response.json()
```

### cURL

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}' \
  | jq '.access_token'

# Authenticated request
curl -X GET http://localhost:8000/api/v1/user/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Background Services

### Token Refresh Service

Automatically refreshes OAuth tokens to maintain authentication:

- Runs every 30 minutes (configurable)
- Refreshes tokens expiring within 1 hour
- Logs refresh activities
- Handles refresh failures gracefully

### Token Cleanup Service

Removes expired tokens and sessions:

- Runs every 6 hours (configurable)
- Cleans up expired OAuth tokens
- Removes inactive sessions
- Maintains database performance

## Configuration

### Environment Variables

```bash
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# Google OAuth
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/callback

# Frontend URLs
FRONTEND_URL=http://localhost:3000
```

### OAuth Scopes

**Google Gmail Scopes**:
- `openid email profile`
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/gmail.modify`

**Google Calendar Scopes**:
- `openid email profile`
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/calendar.settings.readonly`
