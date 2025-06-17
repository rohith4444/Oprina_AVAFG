# Oprina API Architecture

## Overview

The Oprina API is a sophisticated FastAPI-based backend system designed to provide multi-user voice assistant capabilities with avatar integration. The system follows a clean architecture pattern with clear separation of concerns across multiple layers.

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
├─────────────────────────────────────────────────────────────────┤
│  React Frontend  │  Mobile Apps  │  Third-party Integrations    │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI │ CORS │ Authentication │ Rate Limiting │ Validation   │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      BUSINESS LOGIC LAYER                       │
├─────────────────────────────────────────────────────────────────┤
│  User Service │ Agent Service │ Voice Service │ Avatar Service  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                     DATA ACCESS LAYER                           │
├─────────────────────────────────────────────────────────────────┤
│  User Repo │ Session Repo │ Message Repo │ Token Repo │ Avatar  │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL SERVICES                             │
├─────────────────────────────────────────────────────────────────┤
│  Supabase │ Google Cloud │ HeyGen │ Vertex AI │ OAuth Providers │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. API Layer (`app/api/`)

**Purpose**: Handles HTTP requests, routing, and response formatting.

- **Endpoints**: RESTful API endpoints organized by domain
- **Models**: Request/response schemas using Pydantic
- **Dependencies**: Dependency injection for services and authentication
- **Middleware**: CORS, authentication, error handling

### 2. Core Services (`app/core/services/`)

**Purpose**: Business logic and orchestration layer.

- **UserService**: User management and profile operations
- **AgentService**: AI agent interaction and conversation management
- **VoiceService**: Speech-to-text and text-to-speech processing
- **AvatarService**: HeyGen avatar integration and quota management
- **GoogleOAuthService**: OAuth flow management and token handling
- **BackgroundTasks**: Automated maintenance and token refresh

### 3. Data Access Layer (`app/core/database/`)

**Purpose**: Data persistence and retrieval operations.

- **Repositories**: Domain-specific data access objects
- **Connection**: Database client management
- **Models**: Database entity definitions
- **Schema Validator**: Database schema validation utilities

### 4. External Integrations (`app/core/integrations/`)

**Purpose**: Third-party service integrations.

- **Speech Services**: Google Cloud Speech-to-Text/Text-to-Speech
- **Client**: HTTP client configurations for external APIs

### 5. Utilities (`app/utils/`)

**Purpose**: Cross-cutting concerns and helper functions.

- **Authentication**: JWT token management and password hashing
- **Encryption**: Data encryption utilities
- **Validation**: Input validation helpers
- **Logging**: Structured logging configuration
- **Error Handling**: Custom exceptions and error responses

## Data Flow

### Authentication Flow
```
Client → API Endpoint → JWT Validation → User Repository → Database
```

### Voice Processing Flow
```
Client → Voice Endpoint → Speech Service → Agent Service → Response
```

### OAuth Flow
```
Client → OAuth Endpoint → Google OAuth → Token Storage → User Profile
```

### Avatar Session Flow
```
Client → Avatar Endpoint → Quota Check → HeyGen API → Session Tracking
```

## Database Schema

### Core Tables

1. **users** - User accounts and profiles
2. **sessions** - Conversation sessions
3. **messages** - Chat messages and AI responses
4. **oauth_tokens** - OAuth token storage
5. **avatar_quotas** - Avatar usage tracking
6. **avatar_sessions** - Avatar session management

### Relationships

```
users (1) ←→ (many) sessions
sessions (1) ←→ (many) messages
users (1) ←→ (many) oauth_tokens
users (1) ←→ (1) avatar_quotas
avatar_quotas (1) ←→ (many) avatar_sessions
```

## Security Architecture

### Authentication & Authorization

- **JWT Tokens**: Stateless authentication with configurable expiration
- **Password Hashing**: bcrypt for secure password storage
- **OAuth Integration**: Google OAuth for third-party authentication
- **Token Refresh**: Automatic background token refresh
- **Rate Limiting**: Configurable request rate limiting

### Data Protection

- **Encryption**: AES encryption for sensitive data
- **Secure Headers**: CORS and security headers
- **Input Validation**: Comprehensive request validation
- **SQL Injection Prevention**: Parameterized queries via ORM

## Scalability Considerations

### Horizontal Scaling

- **Stateless Design**: No server-side session state
- **Database Connection Pooling**: Efficient database connections
- **Caching Strategy**: Redis integration ready
- **Load Balancing**: Multiple instance support

### Performance Optimization

- **Async Operations**: FastAPI async support
- **Connection Pooling**: Database connection optimization
- **Background Tasks**: Async background processing
- **Lazy Loading**: Efficient data fetching patterns

## Monitoring & Observability

### Health Checks

- **Basic Health**: Simple liveness probe
- **Detailed Health**: Database connectivity and service status
- **Service Dependencies**: External service health monitoring

### Logging

- **Structured Logging**: JSON formatted logs
- **Log Levels**: Configurable logging levels
- **Request Tracking**: Request ID correlation
- **Error Tracking**: Comprehensive error logging

### Metrics

- **Background Service Stats**: Token refresh and cleanup metrics
- **API Usage**: Endpoint usage tracking
- **Performance Metrics**: Response time monitoring

## Configuration Management

### Environment-Based Configuration

- **Development**: Local development settings
- **Staging**: Pre-production environment
- **Production**: Production-ready configuration

### Security Configuration

- **Secrets Management**: Environment variable based secrets
- **API Keys**: Secure API key management
- **Database Credentials**: Encrypted credential storage

## Development Patterns

### Repository Pattern

```python
class UserRepository:
    def __init__(self, db_client):
        self.db = db_client
    
    async def get_user_by_id(self, user_id: str) -> dict:
        # Data access implementation
```

### Service Pattern

```python
class UserService:
    def __init__(self, user_repository):
        self.user_repo = user_repository
    
    async def create_user(self, user_data: dict) -> dict:
        # Business logic implementation
```

### Dependency Injection

```python
def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository)
) -> UserService:
    return UserService(user_repository)
```

## Technology Stack

### Core Technologies

- **FastAPI**: Modern Python web framework
- **Pydantic**: Data validation and serialization
- **Supabase**: PostgreSQL database with real-time features
- **Python 3.9+**: Runtime environment

### External Services

- **Google Cloud**: Speech services and OAuth
- **HeyGen**: Avatar generation and management
- **Vertex AI**: AI agent capabilities

### Development Tools

- **Poetry/pip**: Dependency management
- **pytest**: Testing framework
- **Black**: Code formatting
- **mypy**: Type checking

## Deployment Architecture

### Container Strategy

- **Docker**: Containerized application
- **Multi-stage builds**: Optimized container images
- **Health checks**: Container health monitoring

### Infrastructure Requirements

- **Compute**: CPU and memory requirements
- **Storage**: Database and file storage
- **Network**: Load balancing and CDN
- **Monitoring**: Observability stack

## Future Enhancements

### Planned Features

- **Caching Layer**: Redis integration for performance
- **Message Queue**: Async task processing
- **Microservices**: Service decomposition
- **Multi-tenancy**: Organization-level isolation
- **API Versioning**: Backward compatibility support

### Scalability Improvements

- **Database Sharding**: Horizontal database scaling
- **CDN Integration**: Static asset optimization
- **Event Sourcing**: Audit trail and replay capabilities
- **CQRS Pattern**: Command-query separation
