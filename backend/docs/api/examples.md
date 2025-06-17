# API Usage Examples

## Overview

This document provides comprehensive examples of how to interact with the Oprina API across different use cases and programming languages. All examples assume you have a running instance of the API at `http://localhost:8000`.

## Quick Start

### 1. User Registration and Authentication

#### cURL
```bash
# Register a new user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "alice@example.com",
    "password": "SecurePass123!",
    "full_name": "Alice Johnson",
    "preferred_name": "Alice",
    "work_type": "Product Manager",
    "ai_preferences": "I prefer concise responses with actionable insights"
  }'

# Login and get token
TOKEN=$(curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "alice@example.com", "password": "SecurePass123!"}' \
  | jq -r '.access_token')

echo "Token: $TOKEN"
```

#### JavaScript/TypeScript
```javascript
const API_BASE = 'http://localhost:8000/api/v1';

class OprinaAPIClient {
  constructor(baseUrl = API_BASE) {
    this.baseUrl = baseUrl;
    this.token = null;
  }

  async register(userData) {
    const response = await fetch(`${this.baseUrl}/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(userData),
    });

    const data = await response.json();
    
    if (response.ok) {
      this.token = data.access_token;
      localStorage.setItem('oprina_token', this.token);
    }
    
    return data;
  }

  async login(email, password) {
    const response = await fetch(`${this.baseUrl}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();
    
    if (response.ok) {
      this.token = data.access_token;
      localStorage.setItem('oprina_token', this.token);
    }
    
    return data;
  }

  getAuthHeaders() {
    return {
      'Authorization': `Bearer ${this.token}`,
      'Content-Type': 'application/json',
    };
  }
}

// Usage
const client = new OprinaAPIClient();

// Register
const userData = {
  email: 'alice@example.com',
  password: 'SecurePass123!',
  full_name: 'Alice Johnson',
  preferred_name: 'Alice',
  work_type: 'Product Manager',
  ai_preferences: 'I prefer concise responses with actionable insights'
};

client.register(userData)
  .then(result => console.log('Registration successful:', result))
  .catch(error => console.error('Registration failed:', error));
```

#### Python
```python
import requests
import json

class OprinaAPIClient:
    def __init__(self, base_url="http://localhost:8000/api/v1"):
        self.base_url = base_url
        self.token = None
    
    def register(self, user_data):
        response = requests.post(
            f"{self.base_url}/auth/register",
            json=user_data
        )
        
        if response.status_code == 201:
            data = response.json()
            self.token = data['access_token']
            return data
        else:
            raise Exception(f"Registration failed: {response.text}")
    
    def login(self, email, password):
        response = requests.post(
            f"{self.base_url}/auth/login",
            json={"email": email, "password": password}
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data['access_token']
            return data
        else:
            raise Exception(f"Login failed: {response.text}")
    
    def get_auth_headers(self):
        return {"Authorization": f"Bearer {self.token}"}

# Usage
client = OprinaAPIClient()

# Register
user_data = {
    "email": "alice@example.com",
    "password": "SecurePass123!",
    "full_name": "Alice Johnson",
    "preferred_name": "Alice",
    "work_type": "Product Manager",
    "ai_preferences": "I prefer concise responses with actionable insights"
}

try:
    result = client.register(user_data)
    print("Registration successful:", result)
except Exception as e:
    print("Registration failed:", e)
```

### 2. Session Management

#### Create and Manage Conversation Sessions

```javascript
// JavaScript - Session Management
class SessionManager {
  constructor(apiClient) {
    this.client = apiClient;
  }

  async createSession(title, context = '') {
    const response = await fetch(`${this.client.baseUrl}/sessions`, {
      method: 'POST',
      headers: this.client.getAuthHeaders(),
      body: JSON.stringify({ title, context }),
    });

    return response.json();
  }

  async getSessions(limit = 50, offset = 0) {
    const response = await fetch(
      `${this.client.baseUrl}/sessions?limit=${limit}&offset=${offset}`,
      {
        headers: this.client.getAuthHeaders(),
      }
    );

    return response.json();
  }

  async getSessionMessages(sessionId, limit = 100) {
    const response = await fetch(
      `${this.client.baseUrl}/sessions/${sessionId}/messages?limit=${limit}`,
      {
        headers: this.client.getAuthHeaders(),
      }
    );

    return response.json();
  }

  async endSession(sessionId) {
    const response = await fetch(
      `${this.client.baseUrl}/sessions/${sessionId}/end`,
      {
        method: 'POST',
        headers: this.client.getAuthHeaders(),
      }
    );

    return response.json();
  }
}

// Usage
const sessionManager = new SessionManager(client);

// Create a new session
sessionManager.createSession('API Integration Discussion', 'Planning API integration')
  .then(session => {
    console.log('Session created:', session);
    return sessionManager.getSessionMessages(session.session.id);
  })
  .then(messages => {
    console.log('Session messages:', messages);
  });
```

#### Python Session Example
```python
class SessionManager:
    def __init__(self, api_client):
        self.client = api_client
    
    def create_session(self, title, context=''):
        response = requests.post(
            f"{self.client.base_url}/sessions",
            json={"title": title, "context": context},
            headers=self.client.get_auth_headers()
        )
        return response.json()
    
    def get_sessions(self, limit=50, offset=0):
        response = requests.get(
            f"{self.client.base_url}/sessions",
            params={"limit": limit, "offset": offset},
            headers=self.client.get_auth_headers()
        )
        return response.json()
    
    def get_session_messages(self, session_id, limit=100):
        response = requests.get(
            f"{self.client.base_url}/sessions/{session_id}/messages",
            params={"limit": limit},
            headers=self.client.get_auth_headers()
        )
        return response.json()

# Usage
session_manager = SessionManager(client)

# Create and use session
session = session_manager.create_session("Planning Meeting", "Q1 planning discussion")
print(f"Created session: {session['session']['id']}")

sessions = session_manager.get_sessions()
print(f"Total sessions: {sessions['total']}")
```

### 3. Voice Processing

#### Voice Transcription Example

```javascript
// JavaScript - Voice Processing
class VoiceProcessor {
  constructor(apiClient) {
    this.client = apiClient;
  }

  async transcribeAudio(audioFile, language = 'en-US') {
    const formData = new FormData();
    formData.append('audio', audioFile);
    formData.append('language', language);

    const response = await fetch(`${this.client.baseUrl}/voice/transcribe`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.client.token}`,
      },
      body: formData,
    });

    return response.json();
  }

  async synthesizeSpeech(text, options = {}) {
    const payload = {
      text,
      voice: options.voice || 'en-US-Neural2-F',
      language: options.language || 'en-US',
      speaking_rate: options.speaking_rate || 1.0,
      audio_format: options.audio_format || 'mp3'
    };

    const response = await fetch(`${this.client.baseUrl}/voice/synthesize`, {
      method: 'POST',
      headers: this.client.getAuthHeaders(),
      body: JSON.stringify(payload),
    });

    return response.json();
  }

  async processVoiceMessage(sessionId, audioFile, language = 'en-US') {
    const formData = new FormData();
    formData.append('session_id', sessionId);
    formData.append('audio', audioFile);
    formData.append('language', language);

    const response = await fetch(`${this.client.baseUrl}/voice/message`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.client.token}`,
      },
      body: formData,
    });

    return response.json();
  }
}

// Usage with file input
document.getElementById('audioFile').addEventListener('change', async (event) => {
  const file = event.target.files[0];
  if (file) {
    const voiceProcessor = new VoiceProcessor(client);
    
    try {
      const transcription = await voiceProcessor.transcribeAudio(file);
      console.log('Transcription:', transcription.transcription);
      
      // Synthesize response
      const synthesis = await voiceProcessor.synthesizeSpeech(
        'Thank you for your message. How can I help you further?'
      );
      console.log('Audio URL:', synthesis.audio_url);
    } catch (error) {
      console.error('Voice processing failed:', error);
    }
  }
});
```

#### Python Voice Processing
```python
import requests

class VoiceProcessor:
    def __init__(self, api_client):
        self.client = api_client
    
    def transcribe_audio(self, audio_file_path, language='en-US'):
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio': audio_file}
            data = {'language': language}
            
            response = requests.post(
                f"{self.client.base_url}/voice/transcribe",
                files=files,
                data=data,
                headers=self.client.get_auth_headers()
            )
            
        return response.json()
    
    def synthesize_speech(self, text, voice='en-US-Neural2-F', language='en-US'):
        payload = {
            'text': text,
            'voice': voice,
            'language': language,
            'speaking_rate': 1.0,
            'audio_format': 'mp3'
        }
        
        response = requests.post(
            f"{self.client.base_url}/voice/synthesize",
            json=payload,
            headers=self.client.get_auth_headers()
        )
        
        return response.json()

# Usage
voice_processor = VoiceProcessor(client)

# Transcribe audio
transcription = voice_processor.transcribe_audio('recording.wav')
print(f"Transcription: {transcription['transcription']}")

# Synthesize speech
synthesis = voice_processor.synthesize_speech("Hello, this is a test message")
print(f"Audio URL: {synthesis['audio_url']}")
```

### 4. Google OAuth Integration

#### OAuth Flow Example

```javascript
// JavaScript - OAuth Integration
class OAuthManager {
  constructor(apiClient) {
    this.client = apiClient;
  }

  initiateGoogleLogin() {
    // Redirect to Google OAuth
    window.location.href = `${this.client.baseUrl}/oauth/google/login`;
  }

  async checkOAuthStatus() {
    const response = await fetch(`${this.client.baseUrl}/oauth/status`, {
      headers: this.client.getAuthHeaders(),
    });

    return response.json();
  }

  async connectGoogleService() {
    window.location.href = `${this.client.baseUrl}/oauth/connect/google`;
  }

  async disconnectService(service = 'google') {
    const response = await fetch(`${this.client.baseUrl}/oauth/disconnect`, {
      method: 'POST',
      headers: this.client.getAuthHeaders(),
      body: JSON.stringify({ service }),
    });

    return response.json();
  }
}

// Usage
const oauthManager = new OAuthManager(client);

// Check OAuth status
oauthManager.checkOAuthStatus()
  .then(status => {
    console.log('OAuth status:', status);
    
    if (!status.google_connected) {
      console.log('Google not connected, initiating connection...');
      oauthManager.connectGoogleService();
    }
  });
```

### 5. Avatar Integration

#### Avatar Session Management

```javascript
// JavaScript - Avatar Management
class AvatarManager {
  constructor(apiClient) {
    this.client = apiClient;
  }

  async getQuota() {
    const response = await fetch(`${this.client.baseUrl}/avatar/quota`, {
      headers: this.client.getAuthHeaders(),
    });

    return response.json();
  }

  async checkQuota(requiredMinutes) {
    const response = await fetch(`${this.client.baseUrl}/avatar/check-quota`, {
      method: 'POST',
      headers: this.client.getAuthHeaders(),
      body: JSON.stringify({ requested_minutes: requiredMinutes }),
    });

    return response.json();
  }

  async startAvatarSession(avatarId, estimatedDuration) {
    const response = await fetch(`${this.client.baseUrl}/avatar/sessions/start`, {
      method: 'POST',
      headers: this.client.getAuthHeaders(),
      body: JSON.stringify({
        avatar_id: avatarId,
        estimated_duration_minutes: estimatedDuration
      }),
    });

    return response.json();
  }

  async endAvatarSession(sessionId, actualDuration) {
    const response = await fetch(`${this.client.baseUrl}/avatar/sessions/end`, {
      method: 'POST',
      headers: this.client.getAuthHeaders(),
      body: JSON.stringify({
        session_id: sessionId,
        actual_duration_minutes: actualDuration
      }),
    });

    return response.json();
  }

  async getSessionStatus(sessionId) {
    const response = await fetch(`${this.client.baseUrl}/avatar/sessions/status`, {
      method: 'POST',
      headers: this.client.getAuthHeaders(),
      body: JSON.stringify({ session_id: sessionId }),
    });

    return response.json();
  }
}

// Usage Example
const avatarManager = new AvatarManager(client);

async function startAvatarConversation() {
  try {
    // Check quota first
    const quota = await avatarManager.getQuota();
    console.log(`Available minutes: ${quota.daily_remaining}`);

    if (quota.daily_remaining >= 10) {
      // Start avatar session
      const session = await avatarManager.startAvatarSession('avatar-123', 10);
      console.log('Avatar session started:', session);

      // Simulate some interaction time
      setTimeout(async () => {
        // End session
        const endResult = await avatarManager.endAvatarSession(session.session.id, 8);
        console.log('Avatar session ended:', endResult);
      }, 5000);
    } else {
      console.log('Insufficient quota for avatar session');
    }
  } catch (error) {
    console.error('Avatar session error:', error);
  }
}

startAvatarConversation();
```

## Complete Usage Examples

### 1. Full Conversation Flow

```javascript
// Complete conversation flow example
async function completeConversationFlow() {
  try {
    // 1. Initialize client and login
    const client = new OprinaAPIClient();
    await client.login('alice@example.com', 'SecurePass123!');

    // 2. Create a conversation session
    const sessionManager = new SessionManager(client);
    const session = await sessionManager.createSession(
      'Morning Standup',
      'Daily team sync discussion'
    );
    const sessionId = session.session.id;

    // 3. Check avatar quota
    const avatarManager = new AvatarManager(client);
    const quota = await avatarManager.getQuota();
    
    if (quota.daily_remaining >= 15) {
      // 4. Start avatar session
      const avatarSession = await avatarManager.startAvatarSession('avatar-123', 15);
      
      // 5. Process voice input (simulated)
      const voiceProcessor = new VoiceProcessor(client);
      // In real app, this would be actual audio file
      const mockAudioFile = new Blob(['mock audio data'], { type: 'audio/wav' });
      
      const voiceResult = await voiceProcessor.processVoiceMessage(
        sessionId,
        mockAudioFile
      );
      
      console.log('AI Response:', voiceResult.ai_response);
      
      // 6. End avatar session
      await avatarManager.endAvatarSession(avatarSession.session.id, 12);
    }

    // 7. Get session history
    const messages = await sessionManager.getSessionMessages(sessionId);
    console.log('Conversation history:', messages);

    // 8. End conversation session
    await sessionManager.endSession(sessionId);
    
  } catch (error) {
    console.error('Conversation flow error:', error);
  }
}
```

### 2. User Profile Management

```python
# Python - Complete user management example
def complete_user_flow():
    try:
        # Initialize client
        client = OprinaAPIClient()
        
        # Login
        client.login('alice@example.com', 'SecurePass123!')
        
        # Get current user profile
        response = requests.get(
            f"{client.base_url}/user/me",
            headers=client.get_auth_headers()
        )
        user_profile = response.json()
        print("Current profile:", user_profile)
        
        # Update profile
        update_data = {
            "work_type": "Senior Product Manager",
            "ai_preferences": "Focus on strategic insights and data-driven recommendations",
            "timezone": "America/New_York"
        }
        
        response = requests.put(
            f"{client.base_url}/user/me",
            json=update_data,
            headers=client.get_auth_headers()
        )
        
        if response.status_code == 200:
            print("Profile updated successfully")
        
        # Change password
        password_data = {
            "current_password": "SecurePass123!",
            "new_password": "NewSecurePass456!"
        }
        
        response = requests.post(
            f"{client.base_url}/user/change-password",
            json=password_data,
            headers=client.get_auth_headers()
        )
        
        if response.status_code == 200:
            print("Password changed successfully")
            
    except Exception as e:
        print(f"User management error: {e}")

complete_user_flow()
```

### 3. Error Handling Best Practices

```javascript
// Comprehensive error handling
class ErrorHandler {
  static async handleApiResponse(response) {
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      
      switch (response.status) {
        case 401:
          // Handle authentication errors
          localStorage.removeItem('oprina_token');
          window.location.href = '/login';
          throw new Error('Authentication required');
          
        case 403:
          throw new Error('Insufficient permissions');
          
        case 429:
          const retryAfter = response.headers.get('Retry-After') || 60;
          throw new Error(`Rate limit exceeded. Retry after ${retryAfter} seconds`);
          
        case 422:
          // Handle validation errors
          const validationErrors = errorData.detail || [];
          const errorMessages = validationErrors.map(err => 
            `${err.loc.join('.')}: ${err.msg}`
          );
          throw new Error(`Validation errors: ${errorMessages.join(', ')}`);
          
        case 500:
          throw new Error('Server error. Please try again later.');
          
        default:
          throw new Error(errorData.message || `HTTP ${response.status}`);
      }
    }
    
    return response.json();
  }
}

// Usage with error handling
async function safeApiCall() {
  try {
    const response = await fetch(`${client.baseUrl}/user/me`, {
      headers: client.getAuthHeaders(),
    });
    
    const data = await ErrorHandler.handleApiResponse(response);
    console.log('User data:', data);
    
  } catch (error) {
    console.error('API call failed:', error.message);
    
    // Show user-friendly error message
    showNotification('error', error.message);
  }
}
```

### 4. Real-time Health Monitoring

```javascript
// Health monitoring utility
class HealthMonitor {
  constructor(apiClient, interval = 30000) {
    this.client = apiClient;
    this.interval = interval;
    this.isMonitoring = false;
  }

  async checkHealth() {
    try {
      const response = await fetch(`${this.client.baseUrl}/health/detailed`);
      const health = await response.json();
      
      return {
        status: health.status,
        timestamp: new Date(health.timestamp),
        uptime: health.uptime_seconds,
        services: health.services
      };
    } catch (error) {
      return {
        status: 'error',
        error: error.message,
        timestamp: new Date()
      };
    }
  }

  startMonitoring(callback) {
    if (this.isMonitoring) return;
    
    this.isMonitoring = true;
    
    const monitor = async () => {
      if (!this.isMonitoring) return;
      
      const health = await this.checkHealth();
      callback(health);
      
      setTimeout(monitor, this.interval);
    };
    
    monitor();
  }

  stopMonitoring() {
    this.isMonitoring = false;
  }
}

// Usage
const monitor = new HealthMonitor(client);

monitor.startMonitoring((health) => {
  console.log('Health status:', health.status);
  
  if (health.status !== 'healthy') {
    console.warn('API health issue detected:', health);
  }
});
```

## Testing Examples

### Unit Tests with Jest

```javascript
// api-client.test.js
import { OprinaAPIClient } from './oprina-client';

describe('OprinaAPIClient', () => {
  let client;
  
  beforeEach(() => {
    client = new OprinaAPIClient('http://localhost:8000/api/v1');
    global.fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  describe('Authentication', () => {
    test('should register user successfully', async () => {
      const mockResponse = {
        message: 'User registered successfully',
        user: { id: '123', email: 'test@example.com' },
        access_token: 'mock-token'
      };

      fetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse,
      });

      const userData = {
        email: 'test@example.com',
        password: 'password123',
        full_name: 'Test User'
      };

      const result = await client.register(userData);

      expect(fetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/auth/register',
        expect.objectContaining({
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(userData),
        })
      );

      expect(result).toEqual(mockResponse);
      expect(client.token).toBe('mock-token');
    });

    test('should handle login failure', async () => {
      fetch.mockResolvedValueOnce({
        ok: false,
        status: 401,
        json: async () => ({ error: 'Invalid credentials' }),
      });

      await expect(
        client.login('wrong@email.com', 'wrongpassword')
      ).rejects.toThrow();
    });
  });
});
```

### Integration Tests

```python
# test_integration.py
import pytest
import requests
from oprina_client import OprinaAPIClient

class TestIntegration:
    @pytest.fixture
    def client(self):
        return OprinaAPIClient("http://localhost:8000/api/v1")
    
    @pytest.fixture
    def authenticated_client(self, client):
        # Setup test user
        user_data = {
            "email": "test@example.com",
            "password": "TestPass123!",
            "full_name": "Test User"
        }
        
        try:
            client.register(user_data)
        except:
            client.login(user_data["email"], user_data["password"])
        
        return client
    
    def test_complete_session_flow(self, authenticated_client):
        # Create session
        session_data = {
            "title": "Test Session",
            "context": "Integration test session"
        }
        
        response = requests.post(
            f"{authenticated_client.base_url}/sessions",
            json=session_data,
            headers=authenticated_client.get_auth_headers()
        )
        
        assert response.status_code == 201
        session = response.json()["session"]
        
        # Get session details
        response = requests.get(
            f"{authenticated_client.base_url}/sessions/{session['id']}",
            headers=authenticated_client.get_auth_headers()
        )
        
        assert response.status_code == 200
        assert response.json()["title"] == "Test Session"
        
        # End session
        response = requests.post(
            f"{authenticated_client.base_url}/sessions/{session['id']}/end",
            headers=authenticated_client.get_auth_headers()
        )
        
        assert response.status_code == 200
```

## Environment-Specific Examples

### Development Environment Setup

```bash
# .env.development
ENVIRONMENT=development
DEBUG=true
SUPABASE_URL=https://your-dev-project.supabase.co
SUPABASE_SERVICE_KEY=your-dev-service-key
GOOGLE_CLIENT_ID=your-dev-client-id
GOOGLE_CLIENT_SECRET=your-dev-client-secret
FRONTEND_URL=http://localhost:3000
```

### Production Deployment Example

```dockerfile
# Dockerfile example for production
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```yaml
# docker-compose.yml
version: '3.8'

services:
  oprina-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_SERVICE_KEY=${SUPABASE_SERVICE_KEY}
      - GOOGLE_CLIENT_ID=${GOOGLE_CLIENT_ID}
      - GOOGLE_CLIENT_SECRET=${GOOGLE_CLIENT_SECRET}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    depends_on:
      - redis
  
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

This comprehensive examples documentation covers all major use cases and provides practical code samples for integrating with the Oprina API across different programming languages and environments.
