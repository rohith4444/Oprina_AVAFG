// src/hooks/useHeyGenSession.ts
// HeyGen session lifecycle management hook

import { useState, useCallback, useRef, useEffect } from 'react';
import StreamingAvatar, { 
  AvatarQuality, 
  StreamingEvents, 
  TaskType 
} from '@heygen/streaming-avatar';
import type {
  SessionConfig,
  SessionState,
  HeyGenSessionEvent 
} from '../types/heygen';
import { useQuotaManager } from './useQoutaManager';
import { createHeyGenError, generateSessionId } from '../utils/avatarutils';

// ============================================================================
// CONSTANTS
// ============================================================================

const DEFAULT_SESSION_CONFIG: SessionConfig = {
  avatarId: 'Ann_Therapist_public',
  voiceId: '',
  quality: AvatarQuality.High,
  activityIdleTimeout: 30,
  disableIdleTimeout: false,
  language: 'English',
};

// ============================================================================
// TYPES
// ============================================================================

interface UseHeyGenSessionReturn {
  // State
  sessionState: SessionState;
  isReady: boolean;
  isConnecting: boolean;
  hasError: boolean;
  
  // Session Management
  createSession: (config?: Partial<SessionConfig>) => Promise<boolean>;
  startSession: () => Promise<boolean>;
  endSession: () => Promise<void>;
  
  // Avatar Control
  speak: (text: string) => Promise<boolean>;
  
  // Configuration
  updateConfig: (newConfig: Partial<SessionConfig>) => void;
  
  // Event Handlers
  onSessionEvent: (callback: (event: HeyGenSessionEvent) => void) => () => void;
  
  // Utilities
  getSessionDuration: () => number;
  getRemainingTime: () => number;
}

// ============================================================================
// MAIN HOOK
// ============================================================================

export const useHeyGenSession = (
  initialConfig: Partial<SessionConfig> = {}
): UseHeyGenSessionReturn => {
  
  // ============================================================================
  // STATE SETUP
  // ============================================================================
  
  const [config, setConfig] = useState<SessionConfig>({
    ...DEFAULT_SESSION_CONFIG,
    ...initialConfig,
  });

  const [sessionState, setSessionState] = useState<SessionState>({
    status: 'idle',
    sessionId: null,
    sessionInfo: null,
    error: null,
    createdAt: null,
    lastActivity: null,
  });

  // Internal references
  const streamingAvatar = useRef<StreamingAvatar | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const eventListeners = useRef<((event: HeyGenSessionEvent) => void)[]>([]);
  const currentSessionId = useRef<string | null>(null);

  // Quota management
  const {
    checkQuotaAvailable,
    startSession: startQuotaSession,
    endSession: endQuotaSession,
  } = useQuotaManager();

  // ============================================================================
  // COMPUTED STATE
  // ============================================================================

  const isReady = sessionState.status === 'ready';
  const isConnecting = sessionState.status === 'creating' || sessionState.status === 'connecting';
  const hasError = sessionState.status === 'error';

  // ============================================================================
  // EVENT SYSTEM
  // ============================================================================

  /**
   * Emit session event to listeners
   */
  const emitSessionEvent = useCallback((
    type: HeyGenSessionEvent['type'],
    data?: any
  ) => {
    const event: HeyGenSessionEvent = {
      type,
      sessionId: sessionState.sessionId || 'unknown',
      timestamp: new Date(),
      data,
    };
    
    eventListeners.current.forEach(listener => listener(event));
  }, [sessionState.sessionId]);

  /**
   * Register event listener
   */
  const onSessionEvent = useCallback((
    callback: (event: HeyGenSessionEvent) => void
  ): (() => void) => {
    eventListeners.current.push(callback);
    
    return () => {
      const index = eventListeners.current.indexOf(callback);
      if (index > -1) {
        eventListeners.current.splice(index, 1);
      }
    };
  }, []);

  // ============================================================================
  // SESSION MANAGEMENT
  // ============================================================================

  /**
   * Get session token from backend
   */
  const getSessionToken = useCallback(async (): Promise<string> => {
    try {
      const response = await fetch('http://localhost:3001/api/get-access-token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `Backend error: ${response.status}`);
      }

      const data = await response.json();
      return data.token;
    } catch (error) {
      console.error('❌ Error getting session token:', error);
      throw error;
    }
  }, []);

  /**
   * Setup StreamingAvatar event handlers
   */
  const setupAvatarEvents = useCallback((avatar: StreamingAvatar) => {
    // Stream ready
    avatar.on(StreamingEvents.STREAM_READY, (event) => {
      console.log('🎥 Stream ready');
      if (event && event.detail && videoRef.current) {
        const stream = event.detail;
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(console.error);
      }
      
      setSessionState(prev => ({
        ...prev,
        status: 'ready',
        lastActivity: new Date(),
      }));
      
      emitSessionEvent('session_ready');
    });

    // Avatar start talking
    avatar.on(StreamingEvents.AVATAR_START_TALKING, () => {
      console.log('🗣️ Avatar started talking');
      setSessionState(prev => ({
        ...prev,
        lastActivity: new Date(),
      }));
    });

    // Avatar stop talking
    avatar.on(StreamingEvents.AVATAR_STOP_TALKING, () => {
      console.log('🤐 Avatar stopped talking');
      setSessionState(prev => ({
        ...prev,
        lastActivity: new Date(),
      }));
    });

    // Stream disconnected
    avatar.on(StreamingEvents.STREAM_DISCONNECTED, () => {
      console.log('❌ Stream disconnected');
      setSessionState(prev => ({
        ...prev,
        status: 'error',
        error: 'Stream disconnected',
      }));
      
      emitSessionEvent('session_error', { error: 'Stream disconnected' });
    });

    }, [emitSessionEvent]);

  /**
   * Create new HeyGen session
   */
  const createSession = useCallback(async (
    configOverrides: Partial<SessionConfig> = {}
  ): Promise<boolean> => {
    try {
      // Check quota availability
      if (!checkQuotaAvailable()) {
        throw createHeyGenError(
          'QUOTA_ERROR',
          'HeyGen quota exceeded. Cannot create new session.'
        );
      }

      setSessionState(prev => ({
        ...prev,
        status: 'creating',
        error: null,
      }));

      const sessionConfig = { ...config, ...configOverrides };
      const sessionId = generateSessionId();
      currentSessionId.current = sessionId;

      // Start quota tracking
      startQuotaSession();

      // Get session token
      const token = await getSessionToken();

      // Create StreamingAvatar instance
      const avatar = new StreamingAvatar({ token });
      
      // Setup event handlers
      setupAvatarEvents(avatar);

      // Create avatar session
      setSessionState(prev => ({
        ...prev,
        status: 'connecting',
      }));

      const sessionInfo = await avatar.createStartAvatar({
        quality: sessionConfig.quality,
        avatarName: sessionConfig.avatarId,
        // Note: Voice configuration might cause errors in some setups
        // voice: { voice_id: sessionConfig.voiceId },
      });

      // Store references
      streamingAvatar.current = avatar;
      
      setSessionState(prev => ({
        ...prev,
        sessionId,
        sessionInfo,
        createdAt: new Date(),
        lastActivity: new Date(),
      }));

      emitSessionEvent('session_created', { sessionInfo });

      console.log('✅ Session created successfully:', sessionId);
      return true;

    } catch (error) {
      console.error('❌ Failed to create session:', error);
      
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      setSessionState(prev => ({
        ...prev,
        status: 'error',
        error: errorMessage,
      }));
      
      emitSessionEvent('session_error', { error: errorMessage });
      
      // End quota session on failure
      if (currentSessionId.current) {
        endQuotaSession(currentSessionId.current, 0);
        currentSessionId.current = null;
      }
      
      return false;
    }
  }, [
    config,
    checkQuotaAvailable,
    startQuotaSession,
    endQuotaSession,
    getSessionToken,
    setupAvatarEvents,
    emitSessionEvent
  ]);

  /**
   * Start existing session (if needed)
   */
  const startSession = useCallback(async (): Promise<boolean> => {
    if (!streamingAvatar.current || !sessionState.sessionInfo) {
      console.warn('⚠️ No session to start');
      return false;
    }

    try {
      // Session is automatically started when created
      // This method is here for consistency with API design
      console.log('✅ Session is already started');
      return true;
    } catch (error) {
      console.error('❌ Failed to start session:', error);
      return false;
    }
  }, [sessionState.sessionInfo]);

  /**
   * Get current session duration in seconds
   */
  const getSessionDuration = useCallback((): number => {
    if (!sessionState.createdAt) return 0;
    return Math.floor((Date.now() - sessionState.createdAt.getTime()) / 1000);
  }, [sessionState.createdAt]);

  /**
   * End current session and cleanup
   */
  const endSession = useCallback(async (): Promise<void> => {
    try {
      const duration = getSessionDuration();
      
      // Stop avatar
      if (streamingAvatar.current) {
        await streamingAvatar.current.stopAvatar();
        streamingAvatar.current = null;
      }

      // Clear video
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }

      // End quota tracking
      if (currentSessionId.current) {
        endQuotaSession(currentSessionId.current, duration);
        currentSessionId.current = null;
      }

      setSessionState(prev => ({
        ...prev,
        status: 'idle',
        sessionId: null,
        sessionInfo: null,
        error: null,
        createdAt: null,
        lastActivity: null,
      }));

      emitSessionEvent('session_ended', { duration });

      console.log(`✅ Session ended. Duration: ${Math.round(duration)}s`);

    } catch (error) {
      console.error('❌ Error ending session:', error);
      
      // Force cleanup even if error occurs
      streamingAvatar.current = null;
      if (videoRef.current) {
        videoRef.current.srcObject = null;
      }
      
      if (currentSessionId.current) {
        endQuotaSession(currentSessionId.current, getSessionDuration());
        currentSessionId.current = null;
      }
      
      setSessionState(prev => ({
        ...prev,
        status: 'idle',
        sessionId: null,
        sessionInfo: null,
        createdAt: null,
        lastActivity: null,
      }));
    }
  }, [getSessionDuration, endQuotaSession, emitSessionEvent]);

  // ============================================================================
  // AVATAR CONTROL
  // ============================================================================

  /**
   * Make avatar speak text
   */
  const speak = useCallback(async (text: string): Promise<boolean> => {
    if (!streamingAvatar.current || !isReady) {
      console.warn('⚠️ Avatar not ready for speaking');
      return false;
    }

    if (!text.trim()) {
      console.warn('⚠️ Empty text provided');
      return false;
    }

    try {
      await streamingAvatar.current.speak({
        text: text.trim(),
        task_type: TaskType.REPEAT,
      });

      setSessionState(prev => ({
        ...prev,
        lastActivity: new Date(),
      }));

      console.log('🗣️ Speaking:', text.substring(0, 50) + '...');
      return true;

    } catch (error) {
      console.error('❌ Failed to make avatar speak:', error);
      
      setSessionState(prev => ({
        ...prev,
        error: 'Failed to make avatar speak',
      }));
      
      return false;
    }
  }, [isReady]);

  // ============================================================================
  // CONFIGURATION
  // ============================================================================

  /**
   * Update session configuration
   */
  const updateConfig = useCallback((newConfig: Partial<SessionConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  // ============================================================================
  // UTILITIES
  // ============================================================================

  /**
   * Get remaining session time (if applicable)
   */
  const getRemainingTime = useCallback((): number => {
    // For now, return unlimited time
    // This could be enhanced to respect session limits
    return Infinity;
  }, []);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      if (streamingAvatar.current) {
        endSession();
      }
    };
  }, [endSession]);

  /**
   * Auto-cleanup on long idle sessions
   */
  useEffect(() => {
    if (!sessionState.lastActivity || !isReady) return;

    const idleTimeout = config.activityIdleTimeout * 1000;
    if (config.disableIdleTimeout || idleTimeout <= 0) return;

    const timer = setTimeout(() => {
      const timeSinceActivity = Date.now() - sessionState.lastActivity!.getTime();
      if (timeSinceActivity >= idleTimeout) {
        console.log('⏰ Session idle timeout reached, ending session');
        endSession();
      }
    }, idleTimeout);

    return () => clearTimeout(timer);
  }, [
    sessionState.lastActivity,
    isReady,
    config.activityIdleTimeout,
    config.disableIdleTimeout,
    endSession
  ]);

  // ============================================================================
  // REF EXPOSURE (for video element)
  // ============================================================================

  // Expose video ref for parent components
  useEffect(() => {
    // This could be enhanced to expose video ref if needed
    // For now, event handlers manage video stream
  }, []);

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // State
    sessionState,
    isReady,
    isConnecting,
    hasError,
    
    // Session Management
    createSession,
    startSession,
    endSession,
    
    // Avatar Control
    speak,
    
    // Configuration
    updateConfig,
    
    // Event Handlers
    onSessionEvent,
    
    // Utilities
    getSessionDuration,
    getRemainingTime,
  };
};

export default useHeyGenSession;