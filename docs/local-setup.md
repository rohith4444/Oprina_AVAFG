# Local Development Setup Guide

Complete guide to setting up Oprina locally for development and testing with Google ADK integration.

## 📋 Prerequisites

- **Python 3.11+** - Required for backend and Oprina agent
- **Node.js 18+** - Required for frontend development
- **Git** - Version control
- **Google Cloud Account** - For Vertex AI and APIs
- **Supabase Account** - For database and authentication

---

## ⚠️ Important Notes

🔴 **Virtual Environment Required**: Keep your virtual environment active for ALL commands in this guide. Many operations will fail silently if the environment is not activated.

🔴 **Command Execution**: All commands should be run from the project root directory (`oprina_avafg/`) unless specifically noted otherwise.

---

## Step 1: Virtual Environment & Dependencies

### 1.1 Create and Activate Virtual Environment

```bash
# From project root (oprina_avafg/)
python -m venv venv

# Activate virtual environment
source venv/bin/activate   # Linux/Mac
# OR
.\venv\Scripts\activate    # Windows

# Verify activation (should show venv in prompt)
which python  # Should point to venv/bin/python
```

### 1.2 Install Python Dependencies

```bash
# Install all required dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep fastapi
pip list | grep google-cloud-aiplatform
```

**Dependencies Installed Include:**
- FastAPI, Uvicorn, Pydantic (Backend framework)
- Supabase, AsyncPG, SQLAlchemy (Database)
- Google Cloud AI Platform, Speech, Text-to-Speech (AI services)
- Python-jose, Passlib, Bcrypt (Authentication)
- Structlog, Schedule (Logging & scheduling)
- HTTPX, AIOHttp, Requests (HTTP clients)

---

## Step 2: Google Cloud SDK Setup

### 2.1 Install Google Cloud SDK

**macOS:**
```bash
brew install google-cloud-sdk
```

**Linux:**
```bash
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
```

**Windows:**
Download and install from [Google Cloud SDK](https://cloud.google.com/sdk/docs/install)

### 2.2 Authenticate and Configure

```bash
# Login to Google Cloud
gcloud auth login

# Set your project ID (replace with your actual project)
gcloud config set project your-project-id

# Set up application default credentials
gcloud auth application-default login

# Verify setup
gcloud config list
gcloud auth list
```

📝 **Critical**: Environment variables in `.env` will only work after this authentication setup.

---

## Step 3: Google Cloud Console Configuration

### 3.1 Enable Required APIs

Navigate to [Google Cloud Console](https://console.cloud.google.com/) and enable these APIs:

- **Vertex AI API** - For agent deployment and AI model access
- **Gmail API** - For email management features  
- **Google Calendar API** - For calendar integration
- **Cloud Storage API** - For file storage and staging
- **IAM Service Account Credentials API** - For service authentication

**Quick Links:**
- [Enable Vertex AI API](https://console.cloud.google.com/apis/library/aiplatform.googleapis.com)
- [Enable Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com)
- [Enable Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com)

### 3.2 OAuth 2.0 Configuration

#### Create OAuth Credentials:
1. Go to [Credentials Page](https://console.cloud.google.com/apis/credentials)
2. Click "Create Credentials" → "OAuth 2.0 Client IDs"
3. Choose "Desktop application"
4. Name it "Oprina Local Development"
5. Download the `credentials.json` file

#### Configure OAuth Consent Screen:
1. Go to [OAuth Consent Screen](https://console.cloud.google.com/apis/credentials/consent)
2. Choose "External" user type
3. Fill required fields:
   - App name: "Oprina Local Development"
   - User support email: Your email
   - Developer contact: Your email
4. Add scopes:
   ```
   https://www.googleapis.com/auth/gmail.readonly
   https://www.googleapis.com/auth/gmail.send
   https://www.googleapis.com/auth/gmail.modify
   https://www.googleapis.com/auth/gmail.compose
   https://www.googleapis.com/auth/calendar
   https://www.googleapis.com/auth/calendar.events
   https://www.googleapis.com/auth/calendar.readonly
   ```
5. Add test users (your Gmail account and any others you'll test with)

---

## Step 4: Local Oprina OAuth Setup

### 4.1 Place Credentials File

```bash
# Move downloaded credentials to oprina folder
cp ~/Downloads/credentials.json oprina/credentials.json

# Verify file exists
ls -la oprina/credentials.json
```

### 4.2 Setup Gmail OAuth

```bash
# Navigate to oprina directory
cd oprina

# Run Gmail setup (opens browser for OAuth)
python setup_gmail.py
```

**Expected Flow:**
1. Script opens browser automatically
2. Login with your Google account
3. Grant permissions to access Gmail
4. Browser shows "The authentication flow has completed"
5. Terminal shows: `✅ Successfully saved Gmail credentials`
6. Creates `gmail_token.pickle` file

### 4.3 Setup Calendar OAuth

```bash
# Run Calendar setup (opens browser for OAuth)
python setup_calendar.py
```

**Expected Flow:**
1. Similar browser OAuth flow for Calendar
2. Grant calendar permissions
3. Terminal shows: `✅ Successfully saved Calendar credentials`
4. Creates `calendar_token.pickle` file

**Verify OAuth Setup:**
```bash
# Check created token files
ls -la oprina/*.pickle

# Should show:
# gmail_token.pickle
# calendar_token.pickle
```

🔑 **Important**: This OAuth setup is ONLY for local agent testing. Production backend handles OAuth through the website interface.

---

## Step 5: Environment Configuration

### 5.1 Create Root Environment File

```bash
# Return to project root
cd ..

# Create .env from template
cp .env.example .env
```

### 5.2 Configure Environment Variables

Edit the `.env` file with your actual values:

```bash
# =============================================================================
# 🎯 OPRINA AGENT CONFIGURATION
# =============================================================================

# Tools Mode - Controls which tool set your agents use
OPRINA_TOOLS_MODE=local  # Use 'local' for development, 'prod' for deployment

# =============================================================================
# ☁️ GOOGLE CLOUD CONFIGURATION (REQUIRED)
# =============================================================================

# Your Google Cloud Project ID
GOOGLE_CLOUD_PROJECT=your-actual-project-id

# Vertex AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=1
GOOGLE_CLOUD_LOCATION=us-central1

# Cloud Storage Bucket (create in console if needed)
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-bucket-name

# =============================================================================
# 🗄️ DATABASE CONFIGURATION (REQUIRED)
# =============================================================================

# Supabase credentials (get from Supabase dashboard)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
```

**Where to Get Values:**
- **Google Cloud Project ID**: [Google Cloud Console](https://console.cloud.google.com/) → Project selector
- **Storage Bucket**: Create at [Cloud Storage](https://console.cloud.google.com/storage/browser)
- **Supabase URL & Keys**: [Supabase Dashboard](https://supabase.com/dashboard) → Your Project → Settings → API

### 5.3 Why Root Directory?

The `.env` file MUST be in the project root because:
- ADK commands (`adk web`, `adk run`) automatically call `load_dotenv()` from root
- Vertex deployment scripts load environment from root
- Both local testing and deployment use the same configuration

---

## Step 6: Local Agent Testing (ADK)

### 6.1 Test Agent Locally

```bash
# Make sure virtual environment is active
source venv/bin/activate  # if not already active

# Test agent locally with ADK web interface
adk web
```

**Expected Output:**
```
🔧 Gmail AGENT USING TOOLS_MODE: local
📁 Using tools_local
🔧 CALENDAR AGENT USING TOOLS_MODE: local
📁 Using tools_local
Starting ADK web interface...
Server running at: http://localhost:8080
```

🌐 **Browser Testing**: 
- Open adk web hosted url.
- Test voice commands: "Check my emails", "What's on my calendar?"
- Test email operations: "Send an email to john@example.com"
- Verify OAuth tokens work correctly

### 6.2 Troubleshooting Local Testing

**Common Issues:**
```bash
# If ADK not found
pip install google-cloud-aiplatform[adk]

# If tools not loading
echo $OPRINA_TOOLS_MODE  # Should show 'local'

# If OAuth fails
ls oprina/*.pickle  # Should show token files
```

---

## Step 7: Agent Deployment to Vertex AI

### 7.1 Switch to Production Mode

```bash
# Edit .env file and change:
OPRINA_TOOLS_MODE=prod  # Change from 'local' to 'prod'
```

**What This Changes:**
- Agents now use `oprina/tools_prod/` instead of `oprina/tools/`
- Production tools connect to database for multi-user OAuth
- No local token files needed for deployed agent

### 7.2 Deploy Agent

```bash
# Deploy agent to Vertex AI
python -m vertex-deployment.deploy --create
```

**Expected Output:**
```
Creating agent deployment...
Agent uploaded successfully
Created remote app: projects/your-project/locations/us-central1/reasoningEngines/1234567890
```

### 7.3 Management Commands

```bash
# List all deployments
python -m vertex-deployment.deploy --list

# Delete specific deployment
python -m vertex-deployment.deploy --delete --resource_id=1234567890

# Create session for testing
python -m vertex-deployment.deploy --create_session --resource_id=1234567890 --user_id=test_user

# List sessions
python -m vertex-deployment.deploy --list_sessions --resource_id=1234567890 --user_id=test_user

# Send test message
python -m vertex-deployment.deploy --send --resource_id=1234567890 --session_id=session_123 --user_id=test_user --message="Hello, test the deployed agent"
```

**Save Your Agent ID**: Copy the `resource_id` from the deployment output - you'll need it for backend configuration.

---

## Step 8: Supabase Database Setup

### 8.1 Create Supabase Project

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Click "New Project"
3. Choose organization and set project details
4. Wait for project to be ready (~2 minutes)

### 8.2 Get API Keys

1. Go to Settings → API
2. Copy these values for your `.env`:
   - **Project URL**: `SUPABASE_URL`
   - **Anon public key**: `SUPABASE_KEY`
   - **Service role key**: `SUPABASE_SERVICE_KEY`

8.3 Run Database Migrations
Navigate to your Supabase project → SQL Editor → New Query, then run the migration files:
Migration Files Location:
The database migration files are located in your project at:
backend/migrations/
├── 01_extensions.sql
├── 02_users_table.sql
├── 03_sessions_table.sql
├── 04_messages_table.sql
├── 06_avatar_qouta_table.sql
└── o7_avatar_sessions_table.sql

supabase/migrations/
└── 20240101_create_contact_tables.sql
How to Run Migrations:

Open each migration file from the backend/migrations/ and supabase/migrations/ folders
Copy the SQL content from each file
Paste into Supabase SQL Editor → New Query
Execute each migration in order:

Run in this order:

01_extensions.sql - Enables required PostgreSQL extensions
02_users_table.sql - User accounts and profiles table
03_sessions_table.sql - Chat sessions table
04_messages_table.sql - Messages and conversation history
06_avatar_qouta_table.sql - Avatar usage quota tracking
o7_avatar_sessions_table.sql - Avatar streaming sessions
20240101_create_contact_tables.sql - Contact form system tables

Quick Access:
bash# View migration files
ls backend/migrations/
ls supabase/migrations/

# Open in your editor to copy SQL content
cat backend/migrations/01_extensions.sql
cat backend/migrations/02_users_table.sql
cat backend/migrations/03_sessions_table.sql
cat backend/migrations/04_messages_table.sql
cat backend/migrations/06_avatar_qouta_table.sql
cat backend/migrations/o7_avatar_sessions_table.sql
cat supabase/migrations/20240101_create_contact_tables.sql

### 8.4 Configure Database Access

1. Go to Settings → Database → Connection string
2. Note the connection details (automatically used by Supabase client)
3. Verify tables created: Go to Table Editor and check all tables exist

---

## Step 9: Backend Setup

### 9.1 Configure Backend Environment

```bash
cd backend

# Create backend .env file
cp .env.example .env
```

Edit `backend/.env` with your values:

```bash
# =============================================================================
# 🗄️ DATABASE CONFIGURATION 
# =============================================================================
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-supabase-service-role-key

# =============================================================================
# 🤖 AI SERVICES (REQUIRED)
# =============================================================================
# Your deployed agent ID from Step 7
VERTEX_AI_AGENT_ID=1234567890  # Replace with your actual agent ID

# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# =============================================================================
# 🎙️ VOICE SERVICES (OPTIONAL)
# =============================================================================
VOICE_MAX_AUDIO_SIZE_MB=10
VOICE_MAX_TEXT_LENGTH=5000
VOICE_DEFAULT_LANGUAGE=en-US
VOICE_DEFAULT_VOICE_NAME=en-US-Neural2-F

# =============================================================================
# 🎭 AVATAR SERVICES (OPTIONAL)
# =============================================================================
HEYGEN_API_KEY=your-heygen-api-key  # Get from HeyGen if using avatars
HEYGEN_API_URL=https://api.heygen.com/

# =============================================================================
# 🔧 API CONFIGURATION
# =============================================================================
HOST=localhost
PORT=8000
API_TITLE=Oprina API
API_VERSION=1.0.0
ENVIRONMENT=development
```

### 9.2 Install Backend Dependencies
bash# Dependencies already installed in Step 1
# No need to install again - same requirements.txt file

# Verify FastAPI installation
python -c "import fastapi; print('FastAPI installed successfully')"
python -c "import supabase; print('Supabase client installed successfully')"
Note: Dependencies were already installed in Step 1 when we ran pip install -r requirements.txt from the root directory.


### 9.3 Run Backend Server
bash# Make sure you're in backend/ directory
cd backend

# Start the backend API server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
Expected Output:
INFO:     Will watch for changes in these directories: ['/path/to/backend']
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345]
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.

### 9.4 Test Backend API
bash# In another terminal, test the API
curl http://localhost:8000/api/v1/health/ping

# Should return:
{"status": "healthy", "timestamp": "2025-01-21T..."}
```

---

## Step 10: Frontend Setup

### 10.1 Install Node.js Dependencies

```bash
# Navigate to frontend directory
cd ../frontend

# Install dependencies
npm install

# Verify installation
npm list react
npm list @supabase/supabase-js
```

### 10.2 Configure Frontend Environment

```bash
# Create frontend environment file
cp .env.example .env.local
```

Edit `.env.local`:

```bash
# =============================================================================
# 🌐 FRONTEND CONFIGURATION
# =============================================================================

# Backend Connection (local development)
NEXT_PUBLIC_BACKEND_URL=http://localhost:8000/api

# Supabase Configuration (same as backend)
NEXT_PUBLIC_SUPABASE_URL=https://your-project-id.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=your-supabase-anon-key

# Application URL
NEXT_PUBLIC_URL=http://localhost:3000

# =============================================================================
# 🎭 AVATAR CONFIGURATION (OPTIONAL)
# =============================================================================

# HeyGen Configuration (if using avatars)
NEXT_PUBLIC_HEYGEN_API_KEY=your-heygen-api-key
NEXT_PUBLIC_HEYGEN_API_URL=https://api.heygen.com/
NEXT_PUBLIC_HEYGEN_AVATAR_ID=Ann_Therapist_public

# Avatar Settings
NEXT_PUBLIC_USE_STATIC_AVATAR=true
NEXT_PUBLIC_ENABLE_AVATAR_SELECTOR=false
NEXT_PUBLIC_SHOW_AVATAR_TOGGLE=true
NEXT_PUBLIC_DEBUG_AVATAR_API=true  # Enable for development debugging
```

### 10.3 Run Frontend Development Server

```bash
# Start the frontend
npm run dev
```

**Expected Output:**
```
   ▲ Next.js 14.0.0
   - Local:        http://localhost:3000
   - Network:      http://192.168.1.xxx:3000

 ✓ Ready in 2.3s
```

---

## Step 11: Complete System Testing

### 11.1 Test Full Integration

**Open your browser to: http://localhost:3000**

#### Test Authentication Flow:
1. Click "Sign Up" → Create account
2. Check email for verification link
3. Verify email and login
4. Should reach dashboard

#### Test Voice Features:
1. Grant microphone permissions
2. Click microphone button
3. Say: "Check my recent emails"
4. Verify agent responds appropriately

#### Test Email Integration:
1. Go to settings → Connect Gmail
2. Complete OAuth flow
3. Return to dashboard
4. Test: "Send an email to test@example.com saying hello"

#### Test Calendar Integration:
1. Settings → Connect Calendar
2. Complete OAuth flow
3. Test: "What's on my calendar today?"

### 11.2 Verify Component Health

```bash
# Check all services are running:

# 1. Frontend
curl http://localhost:3000  # Should return HTML

# 2. Backend API  
curl http://localhost:8000/api/v1/health/ping  # Should return JSON

# 3. Database connection
# Check Supabase dashboard → Table Editor → Verify data appears

# 4. Agent deployment
python -m vertex-deployment.deploy --list  # Should show your agent
```

---

## 🛠 Troubleshooting

### Virtual Environment Issues
```bash
# Verify environment is active
echo $VIRTUAL_ENV  # Should show path to venv

# Reactivate if needed
source venv/bin/activate
```

### Google Cloud Authentication Issues
```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Check project
gcloud config get-value project
```

### Environment Variable Issues
```bash
# Check environment loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))
print('Supabase:', os.getenv('SUPABASE_URL'))
"
```

### OAuth Token Issues
```bash
# Regenerate tokens
cd oprina
rm *.pickle
python setup_gmail.py
python setup_calendar.py
```

### Frontend Connection Issues
```bash
# Check CORS settings in backend
# Verify NEXT_PUBLIC_BACKEND_URL in .env.local
# Check browser developer console for errors
```

### Agent Deployment Issues
```bash
# Check tools mode
grep OPRINA_TOOLS_MODE .env

# Verify staging bucket exists
gsutil ls gs://your-bucket-name

# Check agent logs
python -m vertex-deployment.deploy --list  # Note resource_id
# Check Google Cloud Console → Vertex AI → Reasoning Engines
```

---

## 🎉 Success Checklist

✅ Virtual environment active and dependencies installed  
✅ Google Cloud SDK authenticated and project configured  
✅ APIs enabled in Google Cloud Console  
✅ OAuth credentials created and consent screen configured  
✅ Local OAuth tokens generated (gmail_token.pickle, calendar_token.pickle)  
✅ Environment variables configured in root .env  
✅ Local agent testing works with `adk web`  
✅ Agent successfully deployed to Vertex AI with resource ID  
✅ Supabase project created and migrations run  
✅ Backend .env configured with agent ID and Supabase credentials  
✅ Backend API running on http://localhost:8000  
✅ Frontend .env.local configured with backend URL  
✅ Frontend running on http://localhost:3000  
✅ Full authentication flow works (signup → verification → login)  
✅ Voice features work with microphone permissions  
✅ Gmail OAuth connection works through settings  
✅ Calendar OAuth connection works through settings  
✅ Agent responds to voice commands and API calls  

---

## 📚 Next Steps

- **Production Deployment**: See [Self-Hosting Guide](./self-hosting.md)
- **API Development**: Check `backend/README.md` for API documentation
- **Frontend Customization**: See `frontend/README.md` for component guide
- **Agent Development**: Review `oprina/README.md` for agent customization

**🎯 Your local development environment is now fully configured!** You can start developing features, testing voice interactions, and customizing the Oprina experience.