// src/services/heygenService.ts
// HeyGen API integration service - handles all API calls

import type {
  HeyGenAvatar,
  HeyGenVoice,
  HeyGenApiResponse,
  FetchAvatarsResponse,
  FetchVoicesResponse,
  CreateSessionResponse,
  SessionInfo,
  SessionConfig,
  SessionHealthResponse
} from '../types/heygen';
import { createHeyGenError, isHeyGenError } from '../utils/avatarutils';

// ============================================================================
// CONFIGURATION
// ============================================================================

const API_CONFIG = {
  baseUrl: import.meta.env.VITE_HEYGEN_API_URL || 'https://api.heygen.com',
  apiKey: import.meta.env.HEYGEN_API_KEY,
  defaultAvatar: import.meta.env.VITE_HEYGEN_AVATAR_ID || 'Ann_Therapist_public',
  timeout: 10000, // 10 seconds
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Create authenticated headers for HeyGen API
 */
const createHeaders = (): HeadersInit => {
  if (!API_CONFIG.apiKey) {
    throw createHeyGenError(
      'CONFIG_ERROR',
      'HeyGen API key not found in environment variables'
    );
  }

  return {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-Api-Key': API_CONFIG.apiKey,
  };
};

/**
 * Make authenticated request to HeyGen API
 */
const makeRequest = async <T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> => {
  const url = `${API_CONFIG.baseUrl}${endpoint}`;
  const headers = createHeaders();

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), API_CONFIG.timeout);

    const response = await fetch(url, {
      ...options,
      headers: { ...headers, ...options.headers },
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorText = await response.text();
      let errorMessage = `HTTP ${response.status}: ${response.statusText}`;
      
      try {
        const errorJson = JSON.parse(errorText);
        errorMessage = errorJson.message || errorMessage;
      } catch {
        // Use default error message if JSON parsing fails
      }

      throw createHeyGenError(
        'API_ERROR',
        errorMessage,
        { status: response.status, response: errorText }
      );
    }

    const data = await response.json();
    return data;
  } catch (error) {
    if (error instanceof DOMException && error.name === 'AbortError') {
      throw createHeyGenError('TIMEOUT_ERROR', 'Request timed out');
    }

    if (isHeyGenError(error)) {
      throw error;
    }

    throw createHeyGenError(
      'NETWORK_ERROR',
      `Network request failed: ${error instanceof Error ? error.message : 'Unknown error'}`,
      error
    );
  }
};

// ============================================================================
// AVATAR MANAGEMENT
// ============================================================================

/**
 * Fetch all available avatars from HeyGen
 */
export const fetchAvailableAvatars = async (): Promise<FetchAvatarsResponse> => {
  try {
    const response = await makeRequest<HeyGenApiResponse<{ avatars: HeyGenAvatar[] }>>(
      '/v2/avatars'
    );

    if (response.error) {
      throw createHeyGenError('API_ERROR', response.error);
    }

    return {
      avatars: response.data.avatars || [],
      total: response.data.avatars?.length || 0,
    };
  } catch (error) {
    console.error('Failed to fetch avatars:', error);
    throw error;
  }
};

/**
 * Get specific avatar by ID
 */
export const getAvatarById = async (avatarId: string): Promise<HeyGenAvatar | null> => {
  try {
    const { avatars } = await fetchAvailableAvatars();
    return avatars.find(avatar => avatar.avatar_id === avatarId) || null;
  } catch (error) {
    console.error(`Failed to get avatar ${avatarId}:`, error);
    return null;
  }
};

/**
 * Fetch all available voices from HeyGen
 */
export const fetchAvailableVoices = async (): Promise<FetchVoicesResponse> => {
  try {
    const response = await makeRequest<HeyGenApiResponse<{ voices: HeyGenVoice[] }>>(
      '/v2/voices'
    );

    if (response.error) {
      throw createHeyGenError('API_ERROR', response.error);
    }

    // Filter to only include voices that support interactive avatars
    const interactiveVoices = response.data.voices?.filter(
      voice => voice.support_interactive_avatar
    ) || [];

    return {
      voices: interactiveVoices,
      total: interactiveVoices.length,
    };
  } catch (error) {
    console.error('Failed to fetch voices:', error);
    throw error;
  }
};

// ============================================================================
// SESSION MANAGEMENT
// ============================================================================

/**
 * Create a new HeyGen streaming session
 */
export const createSession = async (config: SessionConfig): Promise<CreateSessionResponse> => {
  try {
    // Step 1: Create session token
    const tokenResponse = await makeRequest<{ data: { token: string } }>(
      '/v1/streaming.create_token',
      { method: 'POST' }
    );

    if (!tokenResponse.data?.token) {
      throw createHeyGenError('API_ERROR', 'Failed to create session token');
    }

    // Step 2: Create streaming session
    const sessionPayload = {
      quality: config.quality,
      avatar_name: config.avatarId,
      voice: {
        voice_id: config.voiceId,
      },
      activityIdleTimeout: config.activityIdleTimeout,
      disableIdleTimeout: config.disableIdleTimeout || false,
    };

    const sessionResponse = await makeRequest<HeyGenApiResponse<SessionInfo>>(
      '/v1/streaming.new',
      {
        method: 'POST',
        body: JSON.stringify(sessionPayload),
      }
    );

    if (sessionResponse.error) {
      throw createHeyGenError('SESSION_ERROR', sessionResponse.error);
    }

    return {
      success: true,
      sessionInfo: sessionResponse.data,
      error: null,
    };
  } catch (error) {
    console.error('Failed to create session:', error);
    
    return {
      success: false,
      sessionInfo: null,
      error: error instanceof Error ? error.message : 'Unknown error occurred',
    };
  }
};

/**
 * Start an existing session
 */
export const startSession = async (sessionId: string): Promise<boolean> => {
  try {
    const response = await makeRequest<HeyGenApiResponse<any>>(
      '/v1/streaming.start',
      {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId }),
      }
    );

    return !response.error;
  } catch (error) {
    console.error('Failed to start session:', error);
    return false;
  }
};

/**
 * Stop and cleanup a session
 */
export const stopSession = async (sessionId: string): Promise<boolean> => {
  try {
    const response = await makeRequest<HeyGenApiResponse<any>>(
      '/v1/streaming.stop',
      {
        method: 'POST',
        body: JSON.stringify({ session_id: sessionId }),
      }
    );

    return !response.error;
  } catch (error) {
    console.error('Failed to stop session:', error);
    return false;
  }
};

/**
 * Send a speaking task to the avatar
 */
export const sendSpeakingTask = async (
  sessionId: string,
  text: string,
  taskType: 'talk' | 'repeat' = 'repeat'
): Promise<boolean> => {
  try {
    const response = await makeRequest<HeyGenApiResponse<any>>(
      '/v1/streaming.task',
      {
        method: 'POST',
        body: JSON.stringify({
          session_id: sessionId,
          text: text,
          task_type: taskType,
        }),
      }
    );

    return !response.error;
  } catch (error) {
    console.error('Failed to send speaking task:', error);
    return false;
  }
};

/**
 * Get current session status and health
 */
export const getSessionHealth = async (sessionId: string): Promise<SessionHealthResponse | null> => {
  try {
    // Note: This endpoint might not exist in HeyGen API
    // This is a placeholder for session monitoring functionality
    const response = await makeRequest<HeyGenApiResponse<any>>(
      `/v1/streaming.status?session_id=${sessionId}`
    );

    if (response.error) {
      return null;
    }

    return {
      sessionId,
      isActive: true,
      duration: 0, // Would be calculated from session data
      lastActivity: new Date(),
      cost: 0, // Would be calculated from duration
    };
  } catch (error) {
    console.error('Failed to get session health:', error);
    return null;
  }
};

/**
 * List all active sessions (for debugging/monitoring)
 */
export const listActiveSessions = async (): Promise<string[]> => {
  try {
    const response = await makeRequest<HeyGenApiResponse<{ sessions: any[] }>>(
      '/v1/streaming.list'
    );

    if (response.error || !response.data.sessions) {
      return [];
    }

    return response.data.sessions.map(session => session.session_id);
  } catch (error) {
    console.error('Failed to list sessions:', error);
    return [];
  }
};

// ============================================================================
// UTILITY FUNCTIONS
// ============================================================================

/**
 * Test API connection and credentials
 */
export const testApiConnection = async (): Promise<boolean> => {
  try {
    // Try to fetch avatars as a connection test
    await fetchAvailableAvatars();
    return true;
  } catch (error) {
    console.error('API connection test failed:', error);
    return false;
  }
};

/**
 * Get API configuration for debugging
 */
export const getApiConfig = () => ({
  baseUrl: API_CONFIG.baseUrl,
  hasApiKey: !!API_CONFIG.apiKey,
  defaultAvatar: API_CONFIG.defaultAvatar,
  timeout: API_CONFIG.timeout,
});

/**
 * Validate API configuration
 */
export const validateApiConfig = (): { valid: boolean; errors: string[] } => {
  const errors: string[] = [];

  if (!API_CONFIG.apiKey) {
    errors.push('HEYGEN_API_KEY environment variable is required');
  }

  if (!API_CONFIG.baseUrl) {
    errors.push('VITE_HEYGEN_API_URL environment variable is required');
  }

  if (!API_CONFIG.defaultAvatar) {
    errors.push('VITE_HEYGEN_AVATAR_ID environment variable is required');
  }

  return {
    valid: errors.length === 0,
    errors,
  };
};

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  // Avatar management
  fetchAvailableAvatars,
  getAvatarById,
  fetchAvailableVoices,
  
  // Session management
  createSession,
  startSession,
  stopSession,
  sendSpeakingTask,
  getSessionHealth,
  listActiveSessions,
  
  // Utilities
  testApiConnection,
  getApiConfig,
  validateApiConfig,
};