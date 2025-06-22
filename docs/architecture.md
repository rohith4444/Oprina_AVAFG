# Oprina Platform - Architecture Documentation

## System Overview

Oprina is a multi-agent conversational AI avatar assistant platform built on a modern microservices architecture that leverages Google Cloud's Agent Development Kit (ADK) for intelligent agent orchestration. The system combines frontend user interfaces, backend APIs, AI agent systems, and external service integrations to deliver a seamless voice-first productivity experience.

## Architecture Layers

### 1. **Frontend Layer (User Interface)**
- **Technology**: React 18 + TypeScript, Vite, Tailwind CSS
- **Components**: 
  - Avatar interaction interface (HeyGen streaming + Static fallback)
  - Voice controls and speech recognition
  - Session management and conversation display
  - Authentication and user profile management
  - Settings and OAuth connection management
- **Deployment**: Static hosting (Vercel/Netlify) with CDN distribution

### 2. **Backend API Layer (Business Logic)**
- **Technology**: FastAPI + Python
- **Services**:
  - User management and profile operations
  - Session and message persistence
  - Voice processing coordination
  - Avatar session management and quota tracking
  - OAuth token management and refresh
- **Deployment**: Google Cloud Run (containerized)

### 3. **Agent Intelligence Layer (Core AI)**
- **Technology**: Google Agent Development Kit (ADK)
- **Agent Architecture**:
  - **Root Agent**: Central orchestrator and conversation manager
  - **Email Agent**: Gmail operations specialist (read, send, organize, analyze)
  - **Calendar Agent**: Google Calendar management specialist
- **Deployment**: Google Vertex AI (agent_engines)

### 4. **Database & Authentication Layer**
- **Technology**: Supabase (PostgreSQL + Auth)
- **Components**:
  - User authentication and session management
  - Application data storage (users, sessions, messages)
  - Contact system with edge functions
  - Row Level Security (RLS) for data isolation

### 5. **External Service Integration Layer**
- **Google Cloud Services**:
  - Speech-to-Text API
  - Text-to-Speech API
  - Gmail API (via OAuth)
  - Google Calendar API (via OAuth)
- **Third-Party Services**:
  - HeyGen API (streaming avatars)
  - Resend API (email notifications)

## Component Interaction Flow

### **User Interaction Flow**
```
1. User speaks to avatar → Frontend captures audio
2. Frontend sends audio → Backend API
3. Backend processes voice → Google Speech-to-Text API
4. Text sent to → Deployed ADK Agents (Vertex AI)
5. Agents process request → Use appropriate tools (Gmail/Calendar APIs)
6. Response generated → Backend API
7. Text-to-speech conversion → Google TTS API
8. Avatar response → Frontend (HeyGen streaming or static)
9. User sees/hears response → Conversation continues
```

### **Authentication Flow**
```
1. User authenticates → Supabase Auth (email/password or Google OAuth)
2. Supabase returns → JWT token to frontend
3. Frontend includes token → All backend API requests
4. Backend validates token → Supabase token verification
5. User context extracted → For personalized agent interactions
```

### **Multi-Agent Orchestration**
```
1. User request received → Root Agent (ADK)
2. Root Agent analyzes intent → Routes to specialized agent
3. Email Agent OR Calendar Agent → Executes specific operations
4. Cross-agent workflows → Data passing between agents
5. Response coordination → Root Agent consolidates results
6. Final response → Back to user through backend/frontend
```

### **OAuth Integration Flow**
```
1. User initiates connection → Frontend OAuth flow
2. Google OAuth consent → User grants permissions
3. OAuth callback → Backend receives authorization code
4. Token exchange → Google OAuth tokens stored (encrypted)
5. Background refresh → Automated token renewal
6. Agent tool usage → Authenticated API calls to Gmail/Calendar
```

## Data Architecture

### **Frontend State Management**
- **React Context**: Authentication state and user profile
- **Local State**: Component-specific data (avatar status, voice controls)
- **Session Storage**: Temporary conversation data
- **Environment Variables**: API endpoints and configuration

### **Backend Data Flow**
- **Request Processing**: FastAPI endpoints with dependency injection
- **Session Management**: Conversation persistence and retrieval
- **Authentication**: JWT token validation and user context
- **External API Coordination**: Google Cloud services and third-party APIs

### **Database Schema**
- **Users**: Profile data, preferences, OAuth tokens
- **Sessions**: Conversation threads and metadata
- **Messages**: Individual conversation messages
- **Avatar Sessions**: Usage tracking and quota management
- **Contact System**: Support case management (Supabase functions)

### **Agent Data Context**
- **Tool Context**: Session state management across agent interactions
- **Cross-Agent Communication**: Data passing between Email and Calendar agents
- **Persistent Memory**: Conversation history and user preferences
- **Real-Time Processing**: Streaming responses and voice synthesis

## Deployment Architecture

### **Development Environment**
```
Local Development:
- Frontend: Vite dev server (localhost:5173)
- Backend: uvicorn dev server (localhost:8000)
- Agents: ADK web interface (localhost:8080)
- Database: Supabase cloud instance
- Authentication: Local gcloud SDK or service account JSON
```

### **Production Environment**
```
Production Deployment:
- Frontend: Vercel/Netlify (static hosting + CDN)
- Backend: Google Cloud Run (containerized, auto-scaling)
- Agents: Google Vertex AI (agent_engines, managed hosting)
- Database: Supabase cloud (production instance)
- Authentication: Service account keys and environment variables
```

## Security Architecture

### **Authentication & Authorization**
- **Frontend**: Supabase Auth integration with JWT tokens
- **Backend**: JWT token validation for all protected endpoints
- **Database**: Row Level Security (RLS) for user data isolation
- **External APIs**: OAuth 2.0 with encrypted token storage

### **Data Protection**
- **Encryption**: OAuth tokens encrypted at rest
- **HTTPS/TLS**: All communications encrypted in transit
- **CORS**: Properly configured cross-origin policies
- **Rate Limiting**: API rate limiting and quota management

### **Privacy Considerations**
- **Minimal Data Storage**: Email content processed in memory only
- **User Consent**: Clear OAuth permission requests
- **Data Isolation**: Session-based user data separation
- **Audit Logging**: Tool execution logging for debugging

## Technology Integration Points

### **Google Cloud Ecosystem**
- **Vertex AI**: Agent hosting and management
- **Speech APIs**: Voice processing pipeline
- **Cloud Run**: Backend service deployment
- **OAuth APIs**: Gmail and Calendar integration
- **IAM**: Identity and access management

### **Supabase Integration**
- **Authentication**: User management and session handling
- **Database**: PostgreSQL with real-time features
- **Edge Functions**: Serverless functions for contact system
- **Storage**: File and media storage (if needed)

### **External Service APIs**
- **HeyGen**: Avatar generation and streaming
- **Resend**: Email notification service
- **Gmail API**: Email operations and management
- **Calendar API**: Calendar events and scheduling

## Scalability Considerations

### **Horizontal Scaling**
- **Frontend**: CDN distribution and static hosting
- **Backend**: Cloud Run auto-scaling based on traffic
- **Agents**: Vertex AI managed scaling for agent workloads
- **Database**: Supabase connection pooling and read replicas

### **Performance Optimization**
- **Caching**: Avatar session caching and voice processing optimization
- **Async Processing**: Non-blocking voice and agent operations
- **Batch Operations**: Efficient multi-agent workflows
- **Resource Management**: Avatar quota tracking and optimization

## Monitoring & Observability

### **Application Monitoring**
- **Frontend**: Error tracking and user analytics
- **Backend**: API performance and error monitoring
- **Agents**: Vertex AI agent execution logging
- **Database**: Supabase query performance monitoring

### **Infrastructure Monitoring**
- **Cloud Run**: Service health and resource utilization
- **Vertex AI**: Agent deployment status and performance
- **External APIs**: Rate limit tracking and error monitoring
- **Network**: Latency and connectivity monitoring

---

This architecture documentation provides the foundation for creating comprehensive visual diagrams showing the technology interactions, data flows, and deployment strategies used in the Oprina platform.