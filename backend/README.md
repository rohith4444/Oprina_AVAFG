# Backend - Oprina API

FastAPI-based backend API for the Oprina conversational AI platform with user authentication, session management, voice processing, and avatar integration.

## 🏗️ Architecture

### Clean Architecture Layers
- **API Layer** (`app/api/`) - HTTP endpoints and request/response handling
- **Core Services** (`app/core/services/`) - Business logic and orchestration
- **Data Layer** (`app/core/database/`) - Data access and repository pattern
- **External Integrations** (`app/core/integrations/`) - Third-party service connections
- **Utilities** (`app/utils/`) - Cross-cutting concerns and helpers

### Supabase Integration Architecture

**Authentication Flow:**
1. **Frontend** → **Supabase Auth** (login, register, OAuth)
2. **Supabase** → **Frontend** (JWT tokens)
3. **Frontend** → **Backend API** (requests with JWT tokens)
4. **Backend** → **Supabase** (validates JWT tokens)

**Key Components:**
- **`supabase_auth.py`** - JWT token validation and user extraction
- **`dependencies.py`** - Authentication dependencies for API endpoints
- **`user_repository.py`** - User data operations with Supabase integration
- **Supabase RLS** - Row Level Security policies for data isolation

**Database Access:**
- **Service Role Key** - Backend admin operations (bypasses RLS)
- **Anonymous Key** - Frontend operations (enforces RLS)
- **JWT Validation** - Token verification for authenticated requests

### Key Features
- ✅ **Supabase Authentication** - Direct integration with Supabase Auth (login, register, OAuth)
- ✅ **Session Management** - Chat session and message persistence
- ✅ **Voice Processing** - Google Cloud Speech-to-Text & Text-to-Speech
- ✅ **Avatar Integration** - HeyGen streaming avatar sessions
- ✅ **OAuth Support** - Google Gmail and Calendar connections via Supabase
- ✅ **Background Services** - Token refresh and maintenance
- ✅ **Agent Integration** - Vertex AI agent communication

## 📁 Folder Structure

```
backend/
├── .env                         # Local environment variables (gitignored)
├── .env.example                 # Development environment template
├── .env.production              # Production environment variables (gitignored)
├── .env.production.example      # Production environment template
├── README.md                    # This documentation
├── app/
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── api/                    # API endpoints and models
│   │   ├── endpoints/          # API route handlers
│   │   └── models/             # Request/response schemas
│   ├── core/                   # Business logic
│   │   ├── database/           # Database connections and repositories
│   │   ├── services/           # Business logic services
│   │   └── integrations/       # External service clients
│   └── utils/                  # Utilities and helpers
├── credentials/                # Google Cloud service account credentials
├── migrations/                 # Database migration scripts
└── tests/                      # Testing utilities
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Supabase project with database migrations applied
- Google Cloud project with required APIs enabled
- Deployed Oprina agent on Vertex AI

### 1. Environment Setup

#### Development Environment
```bash
cd backend
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# Database
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# AI Services
VERTEX_AI_AGENT_ID=your-deployed-agent-id
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# OAuth (for Gmail/Calendar integration)
GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-secret

# Security
ENCRYPTION_KEY=your-encryption-key-here

# Application URLs (Development)
FRONTEND_URL=http://localhost:5173
BACKEND_API_URL=http://localhost:8000
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/oauth/callback
CORS_ORIGINS=http://localhost:5173,http://localhost:3000,http://localhost:3001

# Optional: Avatar Service
HEYGEN_API_KEY=your-heygen-api-key

# Voice Services (Google Cloud)
GOOGLE_APPLICATION_CREDENTIALS=./credentials/oprina-voice.json
```

#### Production Environment
```bash
cp .env.production.example .env.production
```

Edit `.env.production` for production deployment:
```bash
# Database (same as development)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-key

# AI Services (production agent)
VERTEX_AI_AGENT_ID=your-production-agent-id
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# OAuth (production credentials)
GOOGLE_CLIENT_ID=your-production-google-client-id
GOOGLE_CLIENT_SECRET=your-production-google-secret

# Security
ENCRYPTION_KEY=your-production-encryption-key

# Production settings
ENVIRONMENT=production
DEBUG=false
HOST=0.0.0.0
PORT=8080
```

#### Google Cloud Authentication Setup

**⚠️ IMPORTANT: Choose ONE authentication method to avoid conflicts**

**Method 1: gcloud SDK (Recommended for Local Development)**
```bash
# Install gcloud SDK if not already installed
# https://cloud.google.com/sdk/docs/install

# Login and set application default credentials
gcloud auth login
gcloud auth application-default login
gcloud config set project your-project-id

# DO NOT set GOOGLE_APPLICATION_CREDENTIALS environment variable
# Remove or comment out this line in .env:
# GOOGLE_APPLICATION_CREDENTIALS=./credentials/oprina-voice.json
```

**Method 2: Service Account JSON (For Production/Containers)**
```bash
# Place your Google Cloud service account JSON file in:
backend/credentials/oprina-voice.json

# Set environment variable in .env:
GOOGLE_APPLICATION_CREDENTIALS=./credentials/oprina-voice.json

# DO NOT use gcloud auth application-default login
```

**🚨 Authentication Conflict Issues:**

If you have **both** methods active, you may encounter:
- `insufficient authentication scopes` errors
- `invalid credentials` errors  
- `project not found` errors
- Voice API authentication failures

**How to Fix Conflicts:**

```bash
# If you want to use gcloud SDK method:
# 1. Remove JSON file environment variable
unset GOOGLE_APPLICATION_CREDENTIALS
# 2. Comment out in .env file:
# GOOGLE_APPLICATION_CREDENTIALS=./credentials/oprina-voice.json
# 3. Ensure gcloud is logged in:
gcloud auth application-default login

# If you want to use JSON file method:
# 1. Revoke gcloud application default credentials:
gcloud auth application-default revoke
# 2. Set JSON file path in .env:
GOOGLE_APPLICATION_CREDENTIALS=./credentials/oprina-voice.json
```

**Verification:**
```bash
# Test which authentication method is active
python -c "
from google.auth import default
credentials, project = default()
print(f'Project: {project}')
print(f'Credentials type: {type(credentials)}')
"
```

### 2. Install Dependencies

```bash
# Install from project root
pip install -r requirements.txt
```

### 3. Database Setup

#### Run Database Migrations in Supabase

**Navigate to your Supabase project → SQL Editor → New Query**

Execute the migration files in order by copying and pasting each file's content:

1. **Extensions** (`migrations/01_extensions.sql`)
   - Enables required PostgreSQL extensions (UUID, etc.)

2. **Users Table** (`migrations/02_users_table.sql`)
   - Creates users table with profiles and preferences

3. **Sessions Table** (`migrations/03_sessions_table.sql`)
   - Creates chat sessions table

4. **Messages Table** (`migrations/04_messages_table.sql`)
   - Creates messages table for conversation history

5. **OAuth Columns** (`migrations/05_oauth_columns.sql`)
   - Adds OAuth token storage columns

6. **Avatar Quota Table** (`migrations/06_avatar_qouta_table.sql`)
   - Creates avatar usage tracking table

7. **Avatar Sessions Table** (`migrations/07_avatar_sessions_table.sql`)
   - Creates avatar streaming sessions table

**Quick Access:**
```bash
# View migration files
ls backend/migrations/

# Copy content and paste into Supabase SQL Editor
cat backend/migrations/01_extensions.sql
cat backend/migrations/02_users_table.sql
# ... continue for all files
```

**Verification:**
After running all migrations, verify tables exist in Supabase:
- Go to **Table Editor** in Supabase dashboard
- Confirm all tables are created: `users`, `sessions`, `messages`, `user_avatar_quotas`, `avatar_sessions`

### 4. Start Development Server

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. Verify Installation

```bash
# Test health endpoint
curl http://localhost:8000/api/v1/health/ping

# Test Supabase connection
curl http://localhost:8000/api/v1/test-supabase

# View API documentation
open http://localhost:8000/docs
```

## 🔧 Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SUPABASE_URL` | ✅ | Supabase project URL |
| `SUPABASE_ANON_KEY` | ✅ | Supabase anonymous key |
| `SUPABASE_SERVICE_KEY` | ✅ | Supabase service role key |
| `VERTEX_AI_AGENT_ID` | ✅ | Deployed agent resource ID |
| `GOOGLE_CLOUD_PROJECT` | ✅ | Google Cloud project ID |
| `GOOGLE_CLOUD_LOCATION` | ✅ | Google Cloud location (e.g., us-central1) |
| `ENCRYPTION_KEY` | ✅ | Encryption key for OAuth tokens stored in database |
| `GOOGLE_APPLICATION_CREDENTIALS` | ⚠️ | Path to service account JSON (only if not using gcloud SDK) |
| `GOOGLE_CLIENT_ID` | ⚠️ | Required for OAuth features |
| `GOOGLE_CLIENT_SECRET` | ⚠️ | Required for OAuth features |
| `HEYGEN_API_KEY` | ➖ | Optional for avatar features |
| `ENVIRONMENT` | ➖ | Environment type (development/production) |
| `DEBUG` | ➖ | Enable debug logging (true/false) |

### CORS Configuration

For frontend development, CORS is configured to allow:
- `http://localhost:5173` (Vite dev server)
- `http://localhost:3000` (Alternative dev server)
- Your production domain

### Google Cloud Setup

**Choose Your Authentication Method:**

**Option A: gcloud SDK (Recommended for Local Development)**
```bash
# Install and configure gcloud SDK
gcloud auth login
gcloud auth application-default login
gcloud config set project your-project-id

# No JSON file needed - DO NOT set GOOGLE_APPLICATION_CREDENTIALS
```

**Option B: Service Account JSON (For Production/CI/CD)**
```bash
# 1. Create service account in Google Cloud Console
# 2. Grant necessary permissions (Speech API, Vertex AI)
# 3. Download JSON credentials file
# 4. Place in backend/credentials/oprina-voice.json
# 5. Set environment variable: GOOGLE_APPLICATION_CREDENTIALS=./credentials/oprina-voice.json
```

**Required Google Cloud APIs:**
- Cloud Speech-to-Text API
- Cloud Text-to-Speech API
- Vertex AI API
- Gmail API (for OAuth)
- Calendar API (for OAuth)

**⚠️ Important:** Never use both authentication methods simultaneously to avoid conflicts.

### Encryption Key Generation

For the `ENCRYPTION_KEY` environment variable, generate a secure key:

```bash
# Generate encryption key
python -c "import base64, os; print(base64.b64encode(os.urandom(32)).decode())"
```

## 📚 API Endpoints

### Authentication (Handled by Supabase)
**Note:** Authentication is handled directly by Supabase, not custom backend endpoints.

**Supabase Auth URLs:**
- `POST https://your-project.supabase.co/auth/v1/signup` - User registration
- `POST https://your-project.supabase.co/auth/v1/token?grant_type=password` - User login
- `POST https://your-project.supabase.co/auth/v1/logout` - User logout
- `GET https://your-project.supabase.co/auth/v1/user` - Get current user
- `POST https://your-project.supabase.co/auth/v1/recover` - Password recovery

**Backend Auth Integration:**
- `GET /api/v1/auth/me` - Get user profile from backend (uses Supabase token)

### User Management
- `GET /api/v1/user/me` - Get user profile
- `PUT /api/v1/user/profile` - Update user profile
- `DELETE /api/v1/user/account` - Delete user account

### Session Management
- `POST /api/v1/sessions/create` - Create chat session
- `GET /api/v1/sessions` - List user sessions
- `PUT /api/v1/sessions/{session_id}` - Update session
- `DELETE /api/v1/sessions/{session_id}` - Delete session

### Voice Processing
- `POST /api/v1/voice/speech-to-text` - Convert speech to text
- `POST /api/v1/voice/text-to-speech` - Convert text to speech

### Avatar Management
- `POST /api/v1/avatar/sessions/start` - Start avatar session
- `POST /api/v1/avatar/sessions/end` - End avatar session
- `GET /api/v1/avatar/quota` - Check usage quota

### OAuth Integration
- `GET /api/v1/oauth/connect/{service}` - Get OAuth URL
- `GET /api/v1/oauth/callback/{service}` - Handle OAuth callback
- `POST /api/v1/oauth/disconnect/{service}` - Disconnect service

### Health & Testing
- `GET /api/v1/health/ping` - Simple health check
- `GET /api/v1/health/` - Basic health with timestamp
- `GET /api/v1/health/detailed` - Comprehensive health check
- `GET /api/v1/test-supabase` - Test Supabase connection

## 🧪 Testing

### Available Test Files

**Configuration & Setup Testing:**
```bash
# Debug configuration and environment variables
python tests/debug_config.py

# Test Supabase authentication integration
python tests/test_supabase_auth.py

# Test database connectivity and audit
python tests/test_database_audit.py

# Test OAuth integration
python tests/test_oauth_integration.py
```

### Run All Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Individual Test Commands
```bash
# Test configuration setup
python tests/debug_config.py

# Test Supabase connection and auth
python tests/test_supabase_auth.py

# Audit database setup and tables
python tests/test_database_audit.py

# Test Google OAuth integration
python tests/test_oauth_integration.py
```

### Health Checks
```bash
# Test API health
curl http://localhost:8000/api/v1/health/ping

# Detailed health with service status
curl http://localhost:8000/api/v1/health/detailed

# Test Supabase connection
curl http://localhost:8000/api/v1/test-supabase
```

## 🚨 Troubleshooting

### Common Issues

**Database Connection Failed**
```bash
# Check Supabase credentials
python -c "from app.config import get_settings; print(get_settings().SUPABASE_URL)"

# Test database connection
curl http://localhost:8000/api/v1/test-supabase

# Test detailed health
curl http://localhost:8000/api/v1/health/detailed
```

**Supabase Authentication Issues**
```bash
# Test Supabase auth integration
python tests/test_supabase_auth.py

# Check Supabase project settings
# Verify Row Level Security (RLS) policies
# Ensure service role key has proper permissions
```

**Google Cloud Authentication Conflicts**
```bash
# Check if you have both authentication methods active
echo $GOOGLE_APPLICATION_CREDENTIALS  # Should be empty if using gcloud SDK
gcloud auth application-default print-access-token  # Should work if using gcloud SDK

# Common conflict symptoms:
# - "insufficient authentication scopes" 
# - "invalid credentials"
# - Voice API failures despite correct setup

# Fix: Choose ONE method
# Method 1 - Use gcloud SDK (remove JSON):
unset GOOGLE_APPLICATION_CREDENTIALS
# Comment out GOOGLE_APPLICATION_CREDENTIALS in .env
gcloud auth application-default login

# Method 2 - Use JSON file (revoke gcloud):
gcloud auth application-default revoke
# Set GOOGLE_APPLICATION_CREDENTIALS in .env
```

**Import Errors**
```bash
# Ensure you're in the backend directory
cd backend
export PYTHONPATH=$PWD:$PYTHONPATH
uvicorn app.main:app --reload

# Check Python path and imports
python -c "import app.main; print('Import successful')"
```

**OAuth Integration Issues**
```bash
# Test OAuth setup
python tests/test_oauth_integration.py

# Verify Google OAuth credentials in .env
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET

# Check redirect URIs in Google Cloud Console
# Ensure frontend URL matches CORS settings
```

**Agent Integration Issues**
```bash
# Confirm VERTEX_AI_AGENT_ID matches deployed agent
echo $VERTEX_AI_AGENT_ID

# Check Google Cloud project and location settings
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_CLOUD_LOCATION

# Verify agent deployment status
python -m vertex-deployment.deploy --list
```

**Environment Configuration Issues**
```bash
# Debug all configuration
python tests/debug_config.py

# Check environment file loading
python -c "
from app.config import get_settings
settings = get_settings()
print(f'Environment: {settings.ENVIRONMENT}')
print(f'Debug mode: {settings.DEBUG}')
"
```

### Logging

Logs are available in:
- Console output (development)
- `logs/` directory (if configured)
- JSON format (production)

Set log level with `DEBUG=true` in environment.

## 🏭 Production Deployment

### Docker Build
```bash
docker build -t oprina-backend .
docker run -p 8080:8080 --env-file .env oprina-backend
```

### Google Cloud Run
```bash
gcloud run deploy oprina-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --set-env-vars-file .env
```

### Health Monitoring
The API provides health endpoints for monitoring:
- `/api/v1/health/ping` - Simple alive check
- `/api/v1/health/` - Basic health with timestamp
- `/api/v1/health/detailed` - Comprehensive health with service status

## 🤝 Development

### Adding New Endpoints

1. **Create endpoint file** in `app/api/endpoints/`
2. **Add request/response models** in `app/api/models/`
3. **Add business logic** in `app/core/services/`
4. **Add data access** in `app/core/database/repositories/`
5. **Register router** in `app/main.py`

### Database Changes
- Add migration files to `migrations/`
- Update repository classes
- Add corresponding service methods
- Update API endpoints as needed
 
For support, check the [troubleshooting guide](../docs/local-setup.md) or create an issue in the project repository.