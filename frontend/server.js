// app/server.js
import express from 'express';
import cors from 'cors';
import dotenv from 'dotenv';

// Load environment variables
dotenv.config();

const app = express();
const PORT = 3001;

// Middleware
app.use(cors({
  origin: 'http://localhost:5173', // Vite dev server
  credentials: true
}));
app.use(express.json());

// HeyGen token endpoint
app.post('/api/get-access-token', async (req, res) => {
  try {
    const HEYGEN_API_KEY = process.env.HEYGEN_API_KEY;
    
    if (!HEYGEN_API_KEY) {
      console.error('❌ HEYGEN_API_KEY not found in environment variables');
      return res.status(500).json({ 
        error: 'HeyGen API key not configured on server' 
      });
    }
    
    console.log('🔑 Creating HeyGen access token...');
    console.log('🔍 API Key exists:', !!HEYGEN_API_KEY);
    console.log('🔍 API Key length:', HEYGEN_API_KEY.length);
    console.log('🔍 API Key first 10 chars:', HEYGEN_API_KEY.substring(0, 10));
    
    // Use dynamic import for node-fetch in ES modules
    const fetch = (await import('node-fetch')).default;
    
    const response = await fetch('https://api.heygen.com/v1/streaming.create_token', {
      method: 'POST',
      headers: {
        'x-api-key': HEYGEN_API_KEY,
        'Content-Type': 'application/json'
      },
    });
    
    console.log('📡 HeyGen API response status:', response.status);
    
    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ HeyGen API Error:', response.status, errorText);
      return res.status(response.status).json({ 
        error: `HeyGen API error: ${response.status}`,
        details: errorText
      });
    }
    
    const data = await response.json();
    console.log('✅ Token created successfully');
    console.log('🎫 Token length:', data.data?.token?.length);
    
    res.json({ 
      token: data.data.token,
      success: true 
    });
    
  } catch (error) {
    console.error('❌ Server error creating token:', error);
    res.status(500).json({ 
      error: 'Failed to create access token',
      details: error.message 
    });
  }
});

// Health check endpoint
app.get('/api/health', (req, res) => {
  res.json({ 
    status: 'Server is running!', 
    timestamp: new Date().toISOString(),
    env_check: {
      heygen_api_key_exists: !!process.env.HEYGEN_API_KEY,
      node_env: process.env.NODE_ENV || 'development'
    }
  });
});

// Test endpoint to verify API key without calling HeyGen
app.get('/api/test-env', (req, res) => {
  const HEYGEN_API_KEY = process.env.HEYGEN_API_KEY;
  res.json({
    api_key_configured: !!HEYGEN_API_KEY,
    api_key_length: HEYGEN_API_KEY?.length || 0,
    api_key_preview: HEYGEN_API_KEY ? HEYGEN_API_KEY.substring(0, 10) + '...' : 'Not found'
  });
});

app.listen(PORT, () => {
  console.log(`🚀 Backend server running on http://localhost:${PORT}`);
  console.log(`📍 Health check: http://localhost:${PORT}/api/health`);
  console.log(`🧪 Environment test: http://localhost:${PORT}/api/test-env`);
  console.log(`🔑 HeyGen API Key configured:`, !!process.env.HEYGEN_API_KEY);
});

export default app;