# Vertex Deployment - Oprina Agent on Google Cloud

Deploy and manage Oprina AI agents on Google Vertex AI platform with comprehensive session management and testing capabilities.

## 🚀 Overview

This deployment system provides a complete solution for deploying Oprina agents to Google Vertex AI, managing user sessions, and testing deployed agents in production environments.

### Key Features
- ✅ **One-Command Deployment** - Deploy agents to Vertex AI with single command
- ✅ **Session Management** - Create and manage user chat sessions
- ✅ **Production Testing** - Send test messages to deployed agents
- ✅ **Resource Management** - List, update, and delete deployments
- ✅ **Multi-User Support** - Isolated user sessions and data
- ✅ **Comprehensive Logging** - Detailed deployment and interaction logs

## 📁 Structure

```
vertex-deployment/
├── deploy.py                   # Main deployment script
└── README.md                   # This documentation
```

## 🔧 Prerequisites

### Google Cloud Setup
- Google Cloud project with billing enabled
- Vertex AI API enabled
- Cloud Storage bucket for staging
- Authentication configured (gcloud or service account)

### Required APIs
```bash
# Enable required Google Cloud APIs
gcloud services enable aiplatform.googleapis.com
gcloud services enable storage.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### Environment Configuration
Ensure your root `.env` file contains:
```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_STAGING_BUCKET=gs://your-bucket-name

# Vertex AI Configuration
GOOGLE_GENAI_USE_VERTEXAI=1

# Google OAuth Configuration
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Security
ENCRYPTION_KEY=your-encryption-key

# Database Configuration
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key
```

## 🚀 Deployment Commands

### Deploy New Agent

```bash
# Deploy Oprina agent to Vertex AI
python -m vertex-deployment.deploy --create
```

**Expected Output:**
```
Created remote app: projects/your-project/locations/us-central1/reasoningEngines/1234567890
```

**⚠️ Important:** Save the resource ID (`1234567890`) - you'll need it for all other operations and backend configuration.

### List All Deployments

```bash
python -m vertex-deployment.deploy --list
```

**Example Output:**
```
Deployments:
- projects/your-project/locations/us-central1/reasoningEngines/1234567890
- projects/your-project/locations/us-central1/reasoningEngines/0987654321
```

### Delete Deployment

```bash
python -m vertex-deployment.deploy --delete --resource_id=1234567890
```

## 👥 Session Management

### Create User Session

```bash
python -m vertex-deployment.deploy \
  --create_session \
  --resource_id=1234567890 \
  --user_id=test_user
```

**Example Output:**
```
Created session:
  Session ID: session_abc123
  User ID: test_user

Use this session ID with --session_id when sending messages.
```

### List User Sessions

```bash
python -m vertex-deployment.deploy \
  --list_sessions \
  --resource_id=1234567890 \
  --user_id=test_user
```

**Example Output:**
```
Sessions for user 'test_user':
- Session ID: session_abc123
- Session ID: session_def456
```

### Get Session Details

```bash
python -m vertex-deployment.deploy \
  --get_session \
  --resource_id=1234567890 \
  --user_id=test_user \
  --session_id=session_abc123
```

## 💬 Testing Deployed Agent

### Send Test Message

```bash
python -m vertex-deployment.deploy \
  --send \
  --resource_id=1234567890 \
  --user_id=test_user \
  --session_id=session_abc123 \
  --message="Check my recent emails"
```

**Example Output:**
```
Sending message to session session_abc123:
Message: Check my recent emails

Response:
I'll check your recent emails for you. Let me access your Gmail...
[Agent processes the request and returns results]
```

### Common Test Scenarios

**Email Testing:**
```bash
# Check emails
--message="What are my recent emails?"

# Send email
--message="Send an email to john@example.com about our meeting tomorrow"

# Search emails
--message="Find emails from my manager about the project deadline"
```

**Calendar Testing:**
```bash
# Check calendar
--message="What's on my calendar today?"

# Create event
--message="Schedule a meeting with Sarah for tomorrow at 2 PM"

# Check availability
--message="When am I free this week for a 1-hour meeting?"
```

**Cross-Agent Workflows:**
```bash
# Meeting coordination
--message="Find emails about the quarterly review and create a calendar event"

# Email to calendar
--message="Check my emails for any deadlines and add them to my calendar"
```

## 🔧 Configuration Options

### Command Line Flags

| Flag | Description | Required | Example |
|------|-------------|----------|---------|
| `--create` | Deploy new agent | ➖ | `--create` |
| `--delete` | Delete deployment | ➖ | `--delete` |
| `--list` | List all deployments | ➖ | `--list` |
| `--create_session` | Create user session | ➖ | `--create_session` |
| `--list_sessions` | List user sessions | ➖ | `--list_sessions` |
| `--get_session` | Get session details | ➖ | `--get_session` |
| `--send` | Send test message | ➖ | `--send` |
| `--resource_id` | Agent resource ID | ⚠️ | `--resource_id=1234567890` |
| `--user_id` | User identifier | ⚠️ | `--user_id=test_user` |
| `--session_id` | Session identifier | ⚠️ | `--session_id=session_abc123` |
| `--message` | Test message | ⚠️ | `--message="Hello"` |
| `--project_id` | Override project ID | ➖ | `--project_id=my-project` |
| `--location` | Override location | ➖ | `--location=us-west1` |
| `--bucket` | Override staging bucket | ➖ | `--bucket=gs://my-bucket` |

**Legend:** ✅ Required, ⚠️ Required for specific operations, ➖ Optional

### Environment Override

You can override environment variables with command flags:
```bash
python -m vertex-deployment.deploy \
  --create \
  --project_id=different-project \
  --location=us-west1 \
  --bucket=gs://different-bucket
```

## 🔍 Deployment Process

### What Happens During Deployment

1. **Environment Loading** - Loads configuration from `.env`
2. **Agent Packaging** - Packages Oprina agent with ADK wrapper
3. **Dependency Resolution** - Installs required Python packages
4. **Cloud Upload** - Uploads agent package to staging bucket
5. **Vertex AI Creation** - Creates reasoning engine on Vertex AI
6. **Resource ID Return** - Returns unique resource ID for management

### Deployment Requirements

**Python Dependencies:**
```python
requirements = [
    "google-cloud-aiplatform[adk,agent_engines]",
]
```

**Extra Packages:**
```python
extra_packages = ["./oprina"]
```

### Deployment Configuration

```python
# ADK App Configuration
app = reasoning_engines.AdkApp(
    agent=root_agent,
    enable_tracing=True,
)

# Agent Engine Configuration
remote_app = agent_engines.create(
    agent_engine=app,
    requirements=requirements,
    extra_packages=extra_packages,
)
```

## 🚨 Troubleshooting

### Common Deployment Issues

**Missing Environment Variables**
```bash
# Check required variables
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_CLOUD_LOCATION
echo $GOOGLE_CLOUD_STAGING_BUCKET
echo $GOOGLE_GENAI_USE_VERTEXAI

# Verify authentication
gcloud auth list
gcloud config get-value project
```

**Permission Errors**
```bash
# Check IAM permissions
gcloud projects get-iam-policy $GOOGLE_CLOUD_PROJECT

# Required roles:
# - Vertex AI User
# - Storage Admin (for staging bucket)
# - Service Usage Consumer
```

**Bucket Access Issues**
```bash
# Verify bucket exists and is accessible
gsutil ls $GOOGLE_CLOUD_STAGING_BUCKET

# Check bucket permissions
gsutil iam get $GOOGLE_CLOUD_STAGING_BUCKET
```

**Agent Import Errors**
```bash
# Test agent import locally
python -c "from oprina.agent import root_agent; print(root_agent.name)"

# Verify environment variables are loaded
python -c "import os; print('Project:', os.getenv('GOOGLE_CLOUD_PROJECT'))"
```

**Database Connection Issues**
```bash
# Check Supabase configuration
echo $SUPABASE_URL
echo $SUPABASE_KEY

# Test database connection
python -c "
from supabase import create_client
import os
supabase = create_client(os.getenv('SUPABASE_URL'), os.getenv('SUPABASE_KEY'))
print('Supabase connection successful')
"
```

### Session Management Issues

**Session Creation Fails**
```bash
# Verify resource ID is correct
python -m vertex-deployment.deploy --list

# Check if agent is responding
python -m vertex-deployment.deploy --send --resource_id=ID --user_id=test --session_id=new_session --message="hello"
```

**Message Sending Fails**
```bash
# Verify session exists
python -m vertex-deployment.deploy --list_sessions --resource_id=ID --user_id=test

# Check agent logs in Google Cloud Console
# Navigate to: Vertex AI > Reasoning Engines > [Your Agent] > Logs
```

## 📊 Monitoring & Logging

### Deployment Monitoring

**Google Cloud Console:**
1. Navigate to Vertex AI > Reasoning Engines
2. Select your deployed agent
3. View metrics, logs, and health status

**Command Line Monitoring:**
```bash
# List deployments to check status
python -m vertex-deployment.deploy --list

# Test agent responsiveness
python -m vertex-deployment.deploy --send --resource_id=ID --user_id=monitor --session_id=health_check --message="ping"
```

## 🔄 Development Workflow

### Development to Production

1. **Local Development**
   ```bash
   # Test locally with ADK
   adk web  # Test locally at http://localhost:8080
   ```

2. **Production Deployment**
   ```bash
   # Deploy to Vertex AI
   python -m vertex-deployment.deploy --create
   ```

3. **Backend Configuration**
   ```bash
   # Update backend with agent ID
   VERTEX_AI_AGENT_ID=1234567890
   ```

4. **Testing Pipeline**
   ```bash
   # Automated testing
   python -m vertex-deployment.deploy --send --resource_id=ID --user_id=ci_test --session_id=automated_test --message="system check"
   ```

## 📄 Integration

### Backend Integration

The deployed agent integrates with your backend API:

```python
# Backend configuration (backend/.env)
VERTEX_AI_AGENT_ID=1234567890  # From deployment output
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1
```

### Frontend Integration

Frontend connects through backend API:

```typescript
// Frontend makes API calls to backend
// Backend communicates with deployed Vertex AI agent
const response = await fetch('/api/v1/agent/chat', {
  method: 'POST',
  body: JSON.stringify({ message: userInput })
});
```

### Required Environment Variables Summary

**Essential Variables:**
- `GOOGLE_CLOUD_PROJECT` - Your Google Cloud project ID
- `GOOGLE_CLOUD_LOCATION` - Deployment region (e.g., us-central1)
- `GOOGLE_CLOUD_STAGING_BUCKET` - Cloud Storage bucket for deployment staging
- `GOOGLE_GENAI_USE_VERTEXAI` - Enable Vertex AI (set to 1)

**Authentication:**
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `ENCRYPTION_KEY` - Security encryption key

**Database:**
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_KEY` - Supabase service role key

For local development and testing, see the [Oprina README](../oprina/README.md).