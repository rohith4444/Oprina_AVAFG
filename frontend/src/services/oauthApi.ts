/**
 * OAuth API service for connecting to backend OAuth endpoints
 */

import { supabase } from '../supabaseClient';

// Configuration
const BACKEND_URL = 'http://localhost:8000'; // Your backend URL
const API_BASE = `${BACKEND_URL}/api/v1`;

// Types
export interface ConnectionStatus {
  gmail: {
    connected: boolean;
    email?: string;
  };
  calendar: {
    connected: boolean;
    email?: string;
  };
}

export interface OAuthApiError {
  message: string;
  detail?: string;
}

/**
 * Get authenticated headers with Supabase token
 */
async function getAuthHeaders() {
  const { data: { session } } = await supabase.auth.getSession();
  
  if (!session?.access_token) {
    throw new Error('No authentication token available');
  }
  
  return {
    'Authorization': `Bearer ${session.access_token}`,
    'Content-Type': 'application/json',
  };
}

/**
 * Handle API errors consistently
 */
function handleApiError(error: any): never {
  console.error('OAuth API Error:', error);
  
  if (error.message === 'No authentication token available') {
    throw new Error('Please log in to connect services');
  }
  
  if (error.response?.data?.detail) {
    throw new Error(error.response.data.detail);
  }
  
  if (error.message) {
    throw new Error(error.message);
  }
  
  throw new Error('An unexpected error occurred');
}

/**
 * Get connection status for all services
 */
export async function getConnectionStatus(): Promise<ConnectionStatus> {
  try {
    const headers = await getAuthHeaders();
    
    const response = await fetch(`${API_BASE}/oauth/status`, {
      method: 'GET',
      headers,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('✅ Connection status retrieved:', data);
    
    return data;
  } catch (error) {
    console.error('❌ Failed to get connection status:', error);
    handleApiError(error);
  }
}

/**
 * Connect to Gmail
 */
export async function connectGmail(): Promise<void> {
  try {
    const headers = await getAuthHeaders();
    
    console.log('🔄 Getting Gmail OAuth URL...');
    
    // Step 1: Get OAuth URL from backend (with authentication)
    const response = await fetch(`${API_BASE}/oauth/connect/gmail`, {
      method: 'GET',
      headers,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('✅ OAuth URL received:', data);
    
    // Step 2: Redirect browser to Google OAuth
    if (data.auth_url) {
      window.location.href = data.auth_url;
    } else {
      throw new Error('No OAuth URL received from backend');
    }
    
  } catch (error) {
    console.error('❌ Failed to initiate Gmail connection:', error);
    handleApiError(error);
  }
}

/**
 * Connect to Google Calendar
 */
export async function connectCalendar(): Promise<void> {
  try {
    const headers = await getAuthHeaders();
    
    console.log('🔄 Getting Calendar OAuth URL...');
    
    // Step 1: Get OAuth URL from backend (with authentication)
    const response = await fetch(`${API_BASE}/oauth/connect/calendar`, {
      method: 'GET',
      headers,
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log('✅ OAuth URL received:', data);
    
    // Step 2: Redirect browser to Google OAuth
    if (data.auth_url) {
      window.location.href = data.auth_url;
    } else {
      throw new Error('No OAuth URL received from backend');
    }
    
  } catch (error) {
    console.error('❌ Failed to initiate Calendar connection:', error);
    handleApiError(error);
  }
}

/**
 * Disconnect a service
 */
export async function disconnectService(service: 'gmail' | 'calendar'): Promise<void> {
  try {
    const headers = await getAuthHeaders();
    
    console.log(`🔄 Disconnecting ${service}...`);
    
    const response = await fetch(`${API_BASE}/oauth/disconnect`, {
      method: 'POST',
      headers,
      body: JSON.stringify({ service }),
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    console.log(`✅ ${service} disconnected successfully:`, data);
    
  } catch (error) {
    console.error(`❌ Failed to disconnect ${service}:`, error);
    handleApiError(error);
  }
}

/**
 * Check if user is authenticated (helper function)
 */
export async function isAuthenticated(): Promise<boolean> {
  try {
    const { data: { session } } = await supabase.auth.getSession();
    return !!session?.access_token;
  } catch {
    return false;
  }
}