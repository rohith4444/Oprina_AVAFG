# API Endpoints Documentation

## Base URL

```
http://localhost:8000/api/v1
```

## Overview

The Oprina API provides REST endpoints organized into the following domains:

- **Health** - System health and monitoring
- **Authentication** - User authentication and authorization  
- **Users** - User profile management
- **Sessions** - Conversation session management
- **OAuth** - Third-party authentication
- **Voice** - Speech processing services
- **Avatar** - HeyGen avatar integration

## Health Endpoints

### Simple Ping
**GET** `/health/ping`

Simple liveness probe for load balancers.

**Response:**
```json
{
  "status": "ok"
}
```

### Basic Health Check
**GET** `/health/`

Basic health status with timestamp.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

### Detailed Health Check
**GET** `/health/detailed`

Comprehensive health check including database connectivity.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "uptime_seconds": 3600.5,
  "services": {
    "database": {
      "status": "healthy",
      "connected": true,
      "test_query": "users table accessible"
    },
    "environment": {
      "status": "healthy"
    }
  }
}
```

## Authentication Endpoints

### Register User
**POST** `/auth/register`

Register a new user account.

**Request Body:**
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

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "jwt-token-string",
  "token_type": "bearer"
}
```

### Login
**POST** `/auth/login`

Authenticate user and return JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
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
**GET** `/auth/validate`

Validate JWT token and return user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
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
**POST** `/auth/logout`

Logout user (client-side token removal).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Logout successful"
}
```

### Deactivate Account
**DELETE** `/auth/deactivate`

Deactivate user account (soft delete).

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Account deactivated successfully"
}
```

## User Endpoints

### Get Current User
**GET** `/user/me`

Get current user profile information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "full_name": "John Doe",
  "preferred_name": "John",
  "work_type": "Software Developer",
  "ai_preferences": "Please provide detailed explanations",
  "avatar_url": null,
  "timezone": "UTC",
  "language": "en",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

### Update User Profile
**PUT** `/user/me`

Update current user profile.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "full_name": "John Smith",
  "preferred_name": "John",
  "work_type": "Senior Developer",
  "ai_preferences": "Focus on performance optimization",
  "timezone": "America/New_York",
  "language": "en"
}
```

**Response (200):**
```json
{
  "message": "Profile updated successfully",
  "user": {
    "id": "uuid-string",
    "email": "user@example.com",
    "full_name": "John Smith",
    "updated_at": "2024-01-15T11:00:00Z"
  }
}
```

### Change Password
**POST** `/user/change-password`

Change user password.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "current_password": "oldpassword123",
  "new_password": "newsecurepassword456"
}
```

**Response (200):**
```json
{
  "message": "Password changed successfully"
}
```

## Session Endpoints

### Create Session
**POST** `/sessions`

Create a new conversation session.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "title": "Project Discussion",
  "context": "Discussing API architecture"
}
```

**Response (201):**
```json
{
  "message": "Session created successfully",
  "session": {
    "id": "uuid-string",
    "title": "Project Discussion",
    "context": "Discussing API architecture",
    "status": "active",
    "created_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get User Sessions
**GET** `/sessions`

Get all sessions for the current user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of sessions to return (default: 50)
- `offset` (optional): Number of sessions to skip (default: 0)
- `status` (optional): Filter by status ("active", "ended")

**Response (200):**
```json
{
  "sessions": [
    {
      "id": "uuid-string",
      "title": "Project Discussion",
      "status": "active",
      "message_count": 5,
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T10:45:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

### Get Session Details
**GET** `/sessions/{session_id}`

Get detailed information about a specific session.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid-string",
  "title": "Project Discussion",
  "context": "Discussing API architecture",
  "status": "active",
  "message_count": 5,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:45:00Z"
}
```

### Get Session Messages
**GET** `/sessions/{session_id}/messages`

Get all messages in a session.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of messages to return (default: 100)
- `offset` (optional): Number of messages to skip (default: 0)

**Response (200):**
```json
{
  "messages": [
    {
      "id": "uuid-string",
      "session_id": "session-uuid",
      "role": "user",
      "content": "Hello, I need help with API design",
      "timestamp": "2024-01-15T10:30:00Z"
    },
    {
      "id": "uuid-string",
      "session_id": "session-uuid", 
      "role": "assistant",
      "content": "I'd be happy to help with API design. What specific aspects would you like to discuss?",
      "timestamp": "2024-01-15T10:30:15Z"
    }
  ],
  "total": 2,
  "limit": 100,
  "offset": 0
}
```

### End Session
**POST** `/sessions/{session_id}/end`

Mark a session as ended.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Session ended successfully",
  "session": {
    "id": "uuid-string",
    "status": "ended",
    "ended_at": "2024-01-15T11:00:00Z"
  }
}
```

### Delete Session
**DELETE** `/sessions/{session_id}`

Delete a session and all its messages.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "message": "Session deleted successfully"
}
```

## OAuth Endpoints

### Google OAuth Login
**GET** `/oauth/google/login`

Initiate Google OAuth flow for existing users.

**Response:** Redirects to Google OAuth consent screen

### Google OAuth Signup
**GET** `/oauth/google/signup`

Initiate Google OAuth flow for new user registration.

**Response:** Redirects to Google OAuth consent screen

### OAuth Callback
**GET** `/oauth/callback`

Handle OAuth callback from providers.

**Query Parameters:**
- `code`: Authorization code
- `state`: CSRF protection state

**Response:** Redirects to frontend with authentication status

### OAuth Status
**GET** `/oauth/status`

Check OAuth connection status.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "google_connected": true,
  "google_email": "user@gmail.com",
  "last_token_refresh": "2024-01-15T10:30:00Z",
  "token_expires_at": "2024-01-15T11:30:00Z"
}
```

### Connect OAuth Service
**GET** `/oauth/connect/{service}`

Connect to an OAuth service.

**Parameters:**
- `service`: "google" 

**Headers:** `Authorization: Bearer <token>`

**Response:** Redirects to OAuth provider

### Disconnect OAuth Service
**POST** `/oauth/disconnect`

Disconnect from an OAuth service.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "service": "google"
}
```

**Response (200):**
```json
{
  "message": "Google OAuth disconnected successfully"
}
```

## Voice Endpoints

### Process Voice Message
**POST** `/voice/message`

Process voice input and return AI response.

**Headers:** `Authorization: Bearer <token>`

**Request Body (multipart/form-data):**
```
session_id: uuid-string
audio: [audio file]
language: en-US (optional)
```

**Response (200):**
```json
{
  "message": "Voice message processed successfully",
  "transcription": "Hello, how can I help you today?",
  "ai_response": "I'm here to assist you. What would you like to know?",
  "audio_url": "https://storage.example.com/response.mp3",
  "processing_time_ms": 1250
}
```

### Transcribe Audio
**POST** `/voice/transcribe`

Convert speech to text.

**Headers:** `Authorization: Bearer <token>`

**Request Body (multipart/form-data):**
```
audio: [audio file]
language: en-US (optional)
```

**Response (200):**
```json
{
  "transcription": "Hello, how can I help you today?",
  "confidence": 0.95,
  "language_detected": "en-US",
  "processing_time_ms": 500
}
```

### Synthesize Speech
**POST** `/voice/synthesize`

Convert text to speech.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "text": "Hello, how can I help you today?",
  "voice": "en-US-Neural2-F",
  "language": "en-US",
  "speaking_rate": 1.0,
  "audio_format": "mp3"
}
```

**Response (200):**
```json
{
  "audio_url": "https://storage.example.com/synthesis.mp3",
  "audio_base64": "base64-encoded-audio-data",
  "duration_seconds": 3.5,
  "processing_time_ms": 800
}
```

## Avatar Endpoints

### Get Avatar Quota
**GET** `/avatar/quota`

Get current user's avatar usage quota.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "user_id": "uuid-string",
  "monthly_limit": 1000,
  "monthly_used": 150,
  "monthly_remaining": 850,
  "daily_limit": 50,
  "daily_used": 5,
  "daily_remaining": 45,
  "current_period_start": "2024-01-01T00:00:00Z",
  "current_period_end": "2024-01-31T23:59:59Z"
}
```

### Check Avatar Quota
**POST** `/avatar/check-quota`

Check if user has sufficient quota for avatar usage.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "requested_minutes": 5
}
```

**Response (200):**
```json
{
  "sufficient_quota": true,
  "requested_minutes": 5,
  "available_minutes": 45,
  "message": "Sufficient quota available"
}
```

### Start Avatar Session
**POST** `/avatar/sessions/start`

Start a new avatar session.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "avatar_id": "heygen-avatar-id",
  "estimated_duration_minutes": 10
}
```

**Response (201):**
```json
{
  "message": "Avatar session started successfully",
  "session": {
    "id": "uuid-string",
    "avatar_id": "heygen-avatar-id",
    "status": "active",
    "estimated_duration_minutes": 10,
    "started_at": "2024-01-15T10:30:00Z"
  }
}
```

### End Avatar Session
**POST** `/avatar/sessions/end`

End an active avatar session.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "session_id": "uuid-string",
  "actual_duration_minutes": 8
}
```

**Response (200):**
```json
{
  "message": "Avatar session ended successfully",
  "session": {
    "id": "uuid-string",
    "status": "completed",
    "actual_duration_minutes": 8,
    "ended_at": "2024-01-15T10:38:00Z"
  },
  "quota_updated": true
}
```

### Get Avatar Session Status
**POST** `/avatar/sessions/status`

Get status of an avatar session.

**Headers:** `Authorization: Bearer <token>`

**Request Body:**
```json
{
  "session_id": "uuid-string"
}
```

**Response (200):**
```json
{
  "session": {
    "id": "uuid-string",
    "avatar_id": "heygen-avatar-id",
    "status": "active",
    "estimated_duration_minutes": 10,
    "elapsed_minutes": 5,
    "started_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get User Avatar Sessions
**GET** `/avatar/sessions`

Get all avatar sessions for the current user.

**Headers:** `Authorization: Bearer <token>`

**Query Parameters:**
- `limit` (optional): Number of sessions to return (default: 50)
- `offset` (optional): Number of sessions to skip (default: 0)
- `status` (optional): Filter by status ("active", "completed", "cancelled")

**Response (200):**
```json
{
  "sessions": [
    {
      "id": "uuid-string",
      "avatar_id": "heygen-avatar-id",
      "status": "completed",
      "actual_duration_minutes": 8,
      "started_at": "2024-01-15T10:30:00Z",
      "ended_at": "2024-01-15T10:38:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## Admin Endpoints

### Background Service Status
**GET** `/admin/background-status`

Get background service statistics (monitoring).

**Response (200):**
```json
{
  "enabled": true,
  "is_running": true,
  "total_refreshes": 150,
  "last_run": "2024-01-15T10:25:00Z",
  "next_run": "2024-01-15T11:00:00Z"
}
```

### Avatar Admin Cleanup
**POST** `/avatar/admin/cleanup`

Clean up expired avatar sessions (admin only).

**Headers:** `Authorization: Bearer <admin-token>`

**Response (200):**
```json
{
  "message": "Cleanup completed successfully",
  "sessions_cleaned": 5,
  "quota_records_updated": 3
}
```

## Error Responses

### Standard Error Format
```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "path": "/api/v1/endpoint"
}
```

### Common HTTP Status Codes

- **200 OK** - Successful request
- **201 Created** - Resource created successfully
- **400 Bad Request** - Invalid request data
- **401 Unauthorized** - Authentication required
- **403 Forbidden** - Insufficient permissions
- **404 Not Found** - Resource not found
- **422 Unprocessable Entity** - Validation errors
- **429 Too Many Requests** - Rate limit exceeded
- **500 Internal Server Error** - Server error

### Rate Limiting

All endpoints are subject to rate limiting:
- **Default**: 60 requests per minute per user
- **Headers**: Rate limit information included in response headers
- **429 Response**: Rate limit exceeded error with retry information

## Request/Response Examples

### Authentication Flow Example

```bash
# 1. Register user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "secure123",
    "full_name": "John Doe"
  }'

# 2. Login (get token)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "john@example.com", "password": "secure123"}' \
  | jq -r '.access_token')

# 3. Use authenticated endpoint
curl -X GET http://localhost:8000/api/v1/user/me \
  -H "Authorization: Bearer $TOKEN"
```

### Voice Processing Example

```bash
# Transcribe audio file
curl -X POST http://localhost:8000/api/v1/voice/transcribe \
  -H "Authorization: Bearer $TOKEN" \
  -F "audio=@voice_message.wav" \
  -F "language=en-US"

# Synthesize speech
curl -X POST http://localhost:8000/api/v1/voice/synthesize \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test message",
    "voice": "en-US-Neural2-F",
    "language": "en-US"
  }'
```
