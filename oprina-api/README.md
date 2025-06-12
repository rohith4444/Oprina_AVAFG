# Oprina API - Phase 1

**Deployed Agent Wrapper Foundation**

A FastAPI-based wrapper for the Oprina multimodal voice assistant, providing API access to the deployed Vertex AI agent with complete user session management.

## 🚀 Overview

Phase 1 of the Oprina API provides:
- **Multi-user session management** with proper isolation
- **Agent communication** with streaming support  
- **Database integration** with Supabase
- **Authentication system** (simplified for Phase 1)
- **Production-ready architecture** with error handling and logging

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI App   │────│   Chat Service   │────│  Agent Service  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────│ User Service     │             │
                        └──────────────────┘             │
                                 │                       │
                        ┌──────────────────┐    ┌─────────────────┐
                        │  Supabase DB     │    │  Vertex AI      │
                        │  - Users         │    │  - Agent        │
                        │  - Sessions      │    │  - Sessions     │
                        │  - Messages      │    └─────────────────┘
                        └──────────────────┘
```

## 📋 Features

### 🔐 Authentication
- Simple token-based auth (Phase 1)
- User registration and login
- Session validation
- User profile management

### 💬 Chat Management
- Create chat sessions
- Send messages with streaming responses
- Get conversation history
- Session statistics and management

### 🗄️ Data Management
- Multi-user session isolation
- Message persistence
- Session state tracking
- User preferences

### 🔍 Monitoring
- Health check endpoints
- Session statistics
- Error tracking and logging

## 🛠️ Setup

### Prerequisites
- Python 3.9+
- Supabase account and project
- Google Cloud project with Vertex AI enabled
- Deployed Oprina agent on Vertex AI

### Installation

1. **Clone and navigate to API directory:**
   ```bash
   cd oprina-api
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements/development.txt
   ```

4. **Configure environment:**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database:**
   ```bash
   python scripts/setup_database.py
   ```

### Configuration

Required environment variables:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key

# Vertex AI
VERTEX_AI_PROJECT_ID=your-project-id
VERTEX_AI_LOCATION=us-central1
VERTEX_AI_AGENT_ID=your-agent-id

# Application
SECRET_KEY=your-secret-key
DEBUG=True  # For development
```

## 🚀 Running the API

### Development
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 📖 API Documentation

Once running, visit:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /api/v1/auth/register` - Register/login user
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/me` - Update user profile

#### Chat
- `POST /api/v1/chat/sessions` - Create chat session
- `POST /api/v1/chat/sessions/{id}/messages` - Send message
- `POST /api/v1/chat/sessions/{id}/stream` - Stream message
- `GET /api/v1/chat/sessions/{id}/history` - Get chat history

#### Sessions
- `GET /api/v1/sessions/` - List user sessions
- `GET /api/v1/sessions/{id}` - Get session details
- `DELETE /api/v1/sessions/{id}` - Delete session

#### Health
- `GET /api/v1/health/` - Basic health check
- `GET /api/v1/health/detailed` - Detailed health with dependencies

## 🔧 Usage Examples

### Register User
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "display_name": "User"}'
```

### Create Chat Session
```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions" \
  -H "Authorization: Bearer user_[USER_ID]" \
  -H "Content-Type: application/json"
```

### Send Message
```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions/[SESSION_ID]/messages" \
  -H "Authorization: Bearer user_[USER_ID]" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello Oprina!", "message_type": "text"}'
```

### Stream Message
```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions/[SESSION_ID]/stream" \
  -H "Authorization: Bearer user_[USER_ID]" \
  -H "Content-Type: application/json" \
  -d '{"message": "Tell me about your capabilities", "message_type": "text"}' \
  --no-buffer
```

## 📊 Database Schema

### Users Table
```sql
CREATE TABLE users (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  email TEXT UNIQUE NOT NULL,
  display_name TEXT,
  avatar_url TEXT,
  preferences JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW(),
  last_login_at TIMESTAMP
);
```

### Sessions Table
```sql
CREATE TABLE sessions (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  user_id UUID REFERENCES users(id),
  session_type TEXT DEFAULT 'chat',
  status TEXT DEFAULT 'active',
  vertex_session_id TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  last_activity_at TIMESTAMP DEFAULT NOW()
);
```

### Messages Table
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  session_id UUID REFERENCES sessions(id),
  user_id UUID REFERENCES users(id),
  role TEXT NOT NULL,
  content TEXT NOT NULL,
  message_type TEXT DEFAULT 'text',
  metadata JSONB DEFAULT '{}',
  created_at TIMESTAMP DEFAULT NOW()
);
```

## 🔍 Error Handling

The API implements comprehensive error handling:

- **400 Bad Request** - Invalid input or request format
- **401 Unauthorized** - Missing or invalid authentication
- **403 Forbidden** - Access denied to resource
- **404 Not Found** - Resource doesn't exist
- **500 Internal Server Error** - Server-side errors

All errors return structured JSON responses:
```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

## 📝 Logging

Structured logging with multiple levels:
- **INFO** - Normal operations
- **WARNING** - Potential issues
- **ERROR** - Error conditions
- **DEBUG** - Detailed debugging (development only)

Log format includes:
- Timestamp
- Request ID
- User ID (when available)
- Endpoint
- Response time
- Error details

## 🧪 Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_chat_service.py
```

## 🚀 Deployment

### Docker
```bash
# Build image
docker build -t oprina-api .

# Run container
docker run -p 8000:8000 --env-file .env oprina-api
```

### Google Cloud Run
```bash
# Deploy to Cloud Run
gcloud run deploy oprina-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## 🛣️ Next Steps (Phase 1.5)

The next phase will add:
- **HeyGen Avatar Integration** - Streaming avatar sessions
- **Session Management** - Avatar session lifecycle
- **Enhanced Security** - JWT tokens and rate limiting
- **Voice Processing** - Audio input/output handling

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📜 License

This project is part of the Oprina ecosystem. See LICENSE file for details.

## 🆘 Support

For issues and questions:
- Create GitHub issue
- Contact development team
- Check API documentation at `/docs`

---

**Oprina API Phase 1** - Deployed Agent Wrapper Foundation  
Built with ❤️ for seamless AI assistant integration
