# Self-Hosting Guide

Complete guide to deploying Oprina to production using **Google Cloud Run** (backend) and **Vercel** (frontend). You can deploy anywhere, but these are proven deployment methods with excellent performance and scalability.

## 🚀 Deployment Overview

This guide covers production deployment using:
- **Google Cloud Run** - Serverless backend hosting with auto-scaling
- **Vercel** - Frontend hosting with global CDN and GitHub integration
- **Same Supabase & Vertex AI** - Database and AI agent remain the same

---

## 📋 Prerequisites

### Complete Local Setup First
**⚠️ Important**: Complete **Steps 1-8** from the [Local Development Guide](./local-setup.md) before proceeding.

This includes:
- ✅ Virtual environment and dependencies
- ✅ Google Cloud SDK authentication  
- ✅ Google Cloud Console API configuration
- ✅ Local OAuth setup (for testing)
- ✅ Environment configuration
- ✅ Agent deployment to Vertex AI
- ✅ Supabase database setup with migrations

### Additional Requirements for Production
- **Domain name** (optional but recommended)
- **GitHub repository** for your Oprina code
- **Vercel account** (free tier available)
- **Google Cloud billing enabled** (for Cloud Run)

---

## 🔄 What's Different in Production

### ✅ Same as Local Development
- Google Cloud SDK setup and authentication
- API enablement and OAuth consent screen
- Supabase database configuration
- **Vertex AI agent deployment** (exact same process)
- Environment file structure

### ❌ Skip for Production
- Local ADK testing (`adk web`)
- Local backend server (`uvicorn app.main:app`)
- Local frontend development (`npm run dev`)

### 🔄 Production-Specific Changes
- Backend deployed to **Google Cloud Run** using Docker
- Frontend deployed to **Vercel** with GitHub integration
- Environment variables configured in deployment platforms
- Custom domains and SSL certificates
- CORS and OAuth redirect URL updates

---

## Step 9: Google Cloud Run Backend Deployment

### 9.1 Prepare Docker Deployment

Your project already includes a production-ready `Dockerfile`:

```bash
# Verify Dockerfile exists
ls backend/Dockerfile

# Should contain:
# FROM python:3.11-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY backend/app/ ./app/
# EXPOSE 8080
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 9.2 Configure Production Environment

Update your `backend/.env` for production:

```bash
# =============================================================================
# 🌐 PRODUCTION CONFIGURATION
# =============================================================================

# Database (same as local)
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-supabase-anon-key
SUPABASE_SERVICE_KEY=your-supabase-service-role-key

# AI Services (same agent ID from local deployment)
VERTEX_AI_AGENT_ID=your-deployed-agent-id
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# OAuth (production credentials)
GOOGLE_CLIENT_ID=your-production-google-client-id
GOOGLE_CLIENT_SECRET=your-production-google-secret

# Security
ENCRYPTION_KEY=your-production-encryption-key

# Application URLs (Production)
FRONTEND_URL=https://your-frontend-domain.vercel.app
BACKEND_API_URL=https://your-backend-url.run.app
GOOGLE_REDIRECT_URI=https://your-backend-url.run.app/api/v1/oauth/callback
CORS_ORIGINS=https://your-frontend-domain.vercel.app,https://your-custom-domain.com

# Production Server Settings
HOST=0.0.0.0
PORT=8080
ENVIRONMENT=production

# Optional Services
HEYGEN_API_KEY=your-heygen-api-key  # If using avatars
VOICE_MAX_AUDIO_SIZE_MB=10
VOICE_DEFAULT_LANGUAGE=en-US
```

### 9.3 Deploy to Cloud Run

```bash
# Make sure you're in the backend directory
cd backend

# Build and deploy to Cloud Run
gcloud run deploy oprina-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --port 8080 \
  --memory 2Gi \
  --cpu 1 \
  --max-instances 10 \
  --set-env-vars-file .env

# Alternative: Deploy with specific image
# gcloud builds submit --tag gcr.io/your-project-id/oprina-backend
# gcloud run deploy oprina-backend --image gcr.io/your-project-id/oprina-backend --platform managed --region us-central1
```

### 9.4 Verify Backend Deployment

```bash
# Get the deployed URL
gcloud run services describe oprina-backend --platform managed --region us-central1 --format 'value(status.url)'

# Test the deployment
curl https://your-backend-url.run.app/api/v1/health/ping

# Should return:
# {"status": "healthy", "timestamp": "2025-01-21T..."}
```

**Save your Cloud Run URL** - you'll need it for frontend configuration: `https://oprina-backend-xxx-uc.a.run.app`

### 9.5 Configure Custom Domain (Optional)

```bash
# Add custom domain mapping
gcloud run domain-mappings create --service oprina-backend --domain api.yourdomain.com --region us-central1

# Update DNS records as instructed by the command output
```

---

## Step 10: Vercel Frontend Deployment

### 10.1 Push Code to GitHub

```bash
# From project root, push to GitHub
git add .
git commit -m "Production deployment ready"
git push origin main
```

### 10.2 Connect to Vercel

1. **Sign up/Login to Vercel**: [vercel.com](https://vercel.com)
2. **Import Project**: 
   - Click "New Project"
   - Import from GitHub
   - Select your Oprina repository
   - **Root Directory**: Set to `frontend/`
   - **Framework Preset**: Vite (auto-detected)

### 10.3 Configure Environment Variables

In Vercel Dashboard → Your Project → Settings → Environment Variables:

```bash
# =============================================================================
# 🌐 VERCEL PRODUCTION ENVIRONMENT
# =============================================================================

# Backend Connection (UPDATE with your Cloud Run URL)
VITE_BACKEND_URL=https://oprina-backend-xxx-uc.a.run.app

# Supabase (same as local)
VITE_SUPABASE_URL=https://your-project-id.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key

# Avatar Services (if using)
VITE_HEYGEN_API_KEY=your-heygen-api-key
VITE_HEYGEN_API_URL=https://api.heygen.com/
VITE_HEYGEN_AVATAR_ID=Ann_Therapist_public

# Production Settings
VITE_USE_STATIC_AVATAR=false
VITE_SHOW_AVATAR_TOGGLE=false
VITE_DEBUG_AVATAR_API=false
VITE_CACHE_AVATAR_IMAGES=true
```

**Environment Setting**: Set to "Production" for all variables

### 10.4 Deploy Frontend

```bash
# Vercel will automatically deploy from GitHub
# Monitor deployment at: https://vercel.com/your-username/your-project

# Manual deployment (if needed)
npx vercel --prod
```

### 10.5 Verify Frontend Deployment

Your frontend will be available at: `https://your-project.vercel.app`

Test the deployment:
1. ✅ Frontend loads correctly
2. ✅ User registration/login works
3. ✅ Backend API connection works
4. ✅ Dashboard accessible after login

---

## Step 11: Post-Deployment Configuration

### 11.1 Update Backend CORS Origins

```bash
# Update backend .env with frontend URLs
CORS_ORIGINS=https://your-project.vercel.app,https://your-custom-domain.com

# Redeploy backend with new CORS settings
gcloud run deploy oprina-backend --source . --region us-central1
```

### 11.2 Update OAuth Redirect URLs

In [Google Cloud Console](https://console.cloud.google.com/apis/credentials):

1. **Edit OAuth 2.0 Client**
2. **Authorized redirect URIs**: Add production URLs:
   ```
   https://your-project.vercel.app/auth/callback
   https://your-custom-domain.com/auth/callback
   ```
3. **Save changes**

### 11.3 Update Supabase Configuration

In Supabase Dashboard → Authentication → URL Configuration:

1. **Site URL**: `https://your-project.vercel.app`
2. **Redirect URLs**: Add:
   ```
   https://your-project.vercel.app/**
   https://your-custom-domain.com/**
   ```

### 11.4 Configure Custom Domains (Optional)

#### Vercel Custom Domain:
1. Vercel Dashboard → Your Project → Settings → Domains
2. Add your custom domain: `yourdomain.com`
3. Configure DNS records as instructed:
   ```
   Type: CNAME
   Name: www
   Value: cname.vercel-dns.com
   ```

#### Cloud Run Custom Domain:
```bash
# Configure API subdomain
gcloud run domain-mappings create --service oprina-backend --domain api.yourdomain.com --region us-central1

# Add DNS records:
# Type: CNAME
# Name: api
# Value: ghs.googlehosted.com
```

---

## Step 12: Production Testing & Verification

### 12.1 Complete Integration Test

**Frontend Testing** (`https://your-project.vercel.app`):
1. ✅ Homepage loads with proper branding
2. ✅ Sign up → Email verification → Login flow
3. ✅ Dashboard loads after authentication
4. ✅ Text-based chat features work
5. ✅ Avatar integration works (if enabled)

**Backend API Testing**:
```bash
# Health check
curl https://your-backend-url.run.app/api/v1/health/ping

# API documentation
open https://your-backend-url.run.app/docs
```

**OAuth Integration Testing**:
1. ✅ Settings → Connect Gmail → OAuth flow completes
2. ✅ Settings → Connect Calendar → OAuth flow completes  
3. ✅ Text commands work: "Check my emails"
4. ✅ Agent responds through deployed Vertex AI

### 12.2 Performance Verification

**Cloud Run Metrics**:
- Go to [Cloud Run Console](https://console.cloud.google.com/run)
- Monitor: CPU utilization, Memory usage, Request latency
- Verify auto-scaling works under load

**Vercel Analytics**:
- Vercel Dashboard → Your Project → Analytics
- Monitor: Page load times, Core Web Vitals
- Check global CDN performance

### 12.3 SSL and Security Check

```bash
# Verify SSL certificates
curl -I https://your-project.vercel.app
curl -I https://your-backend-url.run.app

# Check security headers
curl -I https://your-project.vercel.app | grep -i security
```

---

## 🔧 Production Optimization

### Performance Optimization

**Cloud Run Scaling**:
```bash
# Configure auto-scaling
gcloud run services update oprina-backend \
  --min-instances 1 \
  --max-instances 20 \
  --cpu 2 \
  --memory 4Gi \
  --region us-central1
```

**Vercel Edge Functions** (if needed):
- Move API calls to edge functions for better performance
- Configure in `vercel.json` for custom routing

### Monitoring & Logging

**Cloud Run Monitoring**:
```bash
# View logs
gcloud logs read "resource.type=cloud_run_revision" --limit 50

# Set up alerting in Cloud Monitoring
```

**Vercel Monitoring**:
- Enable Vercel Analytics for performance insights
- Set up deployment notifications

### Backup & Security

**Database Backups**:
- Supabase automatically handles backups
- Configure point-in-time recovery in Supabase settings

**Environment Security**:
- ✅ All secrets in environment variables (not code)
- ✅ HTTPS enforced on all endpoints  
- ✅ CORS properly configured
- ✅ Authentication required for sensitive endpoints

---

## 🚨 Troubleshooting Production Issues

### Common Deployment Issues

**Cloud Run Build Failures**:
```bash
# Check build logs
gcloud builds list --limit 5

# Debug specific build
gcloud builds log BUILD_ID
```

**Vercel Build Failures**:
- Check build logs in Vercel dashboard
- Verify `frontend/` directory structure
- Check Node.js version compatibility
- Ensure Vite configuration is correct

**Environment Variable Issues**:
```bash
# Verify Cloud Run environment
gcloud run services describe oprina-backend --region us-central1 --format="value(spec.template.spec.template.spec.containers[0].env)"

# Test environment loading
curl https://your-backend-url.run.app/api/v1/health/env-check
```

### OAuth/CORS Issues

**OAuth Redirect Errors**:
1. Verify redirect URLs in Google Cloud Console
2. Check Supabase redirect URL configuration  
3. Ensure HTTPS is used for all redirect URLs

**CORS Errors**:
1. Update `CORS_ORIGINS` in backend environment
2. Redeploy backend after changes
3. Clear browser cache and test

---

## 🎉 Production Deployment Complete!

### ✅ Deployment Checklist

**Infrastructure**:
- ✅ Backend deployed to Cloud Run with custom domain
- ✅ Frontend deployed to Vercel with custom domain  
- ✅ SSL certificates configured and working
- ✅ Auto-scaling configured for expected traffic

**Configuration**:
- ✅ Environment variables properly configured (including encryption key)
- ✅ CORS origins updated for production URLs
- ✅ OAuth redirect URLs updated in Google Console
- ✅ Supabase redirect URLs configured

**Testing**:
- ✅ Complete user flow tested (signup → login → chat)
- ✅ Text-based chat features working in production
- ✅ Gmail/Calendar OAuth integration tested
- ✅ Agent responses working through Vertex AI
- ✅ Performance metrics within acceptable ranges

**Security**:
- ✅ All secrets stored in environment variables
- ✅ HTTPS enforced across all services
- ✅ Authentication working properly
- ✅ Database access properly secured

### 🔗 Your Production URLs

- **Frontend**: `https://your-project.vercel.app`
- **Backend API**: `https://your-backend-url.run.app`
- **API Documentation**: `https://your-backend-url.run.app/docs`
- **Health Check**: `https://your-backend-url.run.app/api/v1/health/ping`

**🎯 Your Oprina production deployment is now live and ready for users!**