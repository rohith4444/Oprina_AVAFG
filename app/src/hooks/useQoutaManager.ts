// src/hooks/useQuotaManager.ts
// Client-side quota management hook - tracks 20-minute account limit

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  QuotaState,
  QuotaStatus,
  QuotaConfig,
  SessionUsage,
  QuotaEvent
} from '../types/heygen';
import {
  calculateQuotaStatus,
  updateQuotaWithUsage,
  resetQuotaState,
  serializeQuotaData,
  deserializeQuotaData,
  isValidStoredQuotaData,
  calculateSessionCost,
  generateSessionId
} from '../utils/avatarutils';

// ============================================================================
// CONSTANTS
// ============================================================================

const STORAGE_KEY = 'heygen_quota_state';

const DEFAULT_CONFIG: QuotaConfig = {
  totalMinutes: 20,
  resetType: 'manual',
  warningThreshold: 5,
  gracePeriod: 30,
};

// ============================================================================
// TYPES
// ============================================================================

interface UseQuotaManagerReturn {
  // State
  quotaState: QuotaState;
  quotaStatus: QuotaStatus;
  config: QuotaConfig;
  
  // Actions
  startSession: () => string; // Returns session ID
  endSession: (sessionId: string, duration: number) => void;
  checkQuotaAvailable: () => boolean;
  getTimeRemaining: () => { minutes: number; seconds: number };
  resetQuota: () => void;
  updateConfig: (newConfig: Partial<QuotaConfig>) => void;
  
  // Events
  onQuotaEvent: (callback: (event: QuotaEvent) => void) => () => void;
  
  // Utilities
  getUsageStats: () => {
    totalSessions: number;
    totalCost: number;
    averageSessionDuration: number;
    usagePercent: number;
  };
}

interface ActiveSession {
  sessionId: string;
  startTime: Date;
}

// ============================================================================
// MAIN HOOK
// ============================================================================

export const useQuotaManager = (
  initialConfig: Partial<QuotaConfig> = {}
): UseQuotaManagerReturn => {
  
  // ============================================================================
  // STATE SETUP
  // ============================================================================
  
  // Configuration
  const [config, setConfig] = useState<QuotaConfig>({
    ...DEFAULT_CONFIG,
    ...initialConfig,
  });

  // Load quota state from storage
  const loadQuotaFromStorage = useCallback((): QuotaState | null => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return null;

      const parsed = JSON.parse(stored);
      if (!isValidStoredQuotaData(parsed)) {
        console.warn('Invalid stored quota data, resetting...');
        return null;
      }

      return deserializeQuotaData(parsed);
    } catch (error) {
      console.error('Failed to load quota from storage:', error);
      return null;
    }
  }, []);

  // Quota state
  const [quotaState, setQuotaState] = useState<QuotaState>(() => 
    loadQuotaFromStorage() || resetQuotaState(config.totalMinutes)
  );

  // Active sessions tracking
  const [activeSessions] = useState<Map<string, ActiveSession>>(new Map());
  
  // Event listeners
  const eventListeners = useRef<((event: QuotaEvent) => void)[]>([]);

  // ============================================================================
  // STORAGE FUNCTIONS
  // ============================================================================

  /**
   * Save quota state to localStorage
   */
  const saveQuotaToStorage = useCallback((state: QuotaState) => {
    try {
      const serialized = serializeQuotaData(state);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(serialized));
    } catch (error) {
      console.error('Failed to save quota to storage:', error);
    }
  }, []);

  // ============================================================================
  // QUOTA CALCULATIONS
  // ============================================================================

  /**
   * Calculate current quota status
   */
  const quotaStatus = calculateQuotaStatus(quotaState, config.warningThreshold);

  /**
   * Check if quota is available for new session
   */
  const checkQuotaAvailable = useCallback((): boolean => {
    return quotaStatus.available && quotaStatus.remainingMinutes > 0;
  }, [quotaStatus]);

  /**
   * Get remaining time in minutes and seconds
   */
  const getTimeRemaining = useCallback(() => {
    const totalSeconds = Math.max(0, quotaStatus.remainingSeconds);
    return {
      minutes: Math.floor(totalSeconds / 60),
      seconds: Math.round(totalSeconds % 60),
    };
  }, [quotaStatus.remainingSeconds]);

  // ============================================================================
  // SESSION MANAGEMENT
  // ============================================================================

  /**
   * Start a new session
   */
  const startSession = useCallback((): string => {
    const sessionId = generateSessionId();
    const activeSession: ActiveSession = {
      sessionId,
      startTime: new Date(),
    };

    activeSessions.set(sessionId, activeSession);
    
    console.log(`Started session: ${sessionId}`);
    return sessionId;
  }, [activeSessions]);

  /**
   * End a session and update quota
   */
  const endSession = useCallback((sessionId: string, duration: number) => {
    const activeSession = activeSessions.get(sessionId);
    if (!activeSession) {
      console.warn(`Session ${sessionId} not found in active sessions`);
      return;
    }

    // Remove from active sessions
    activeSessions.delete(sessionId);

    // Create session usage record
    const sessionUsage: SessionUsage = {
      sessionId,
      duration,
      startTime: activeSession.startTime,
      endTime: new Date(),
      cost: calculateSessionCost(duration),
    };

    // Update quota state
    setQuotaState(prevState => {
      const newState = updateQuotaWithUsage(prevState, sessionUsage);
      
      // Check for quota events
      emitQuotaEvents(prevState, newState);
      
      return newState;
    });

    console.log(`Ended session: ${sessionId}, duration: ${duration}s, cost: ${sessionUsage.cost} credits`);
  }, [activeSessions]);

  // ============================================================================
  // EVENT SYSTEM
  // ============================================================================

  /**
   * Emit quota events when state changes
   */
  const emitQuotaEvents = useCallback((
    oldState: QuotaState,
    newState: QuotaState
  ) => {
    const oldStatus = calculateQuotaStatus(oldState, config.warningThreshold);
    const newStatus = calculateQuotaStatus(newState, config.warningThreshold);

    // Quota exceeded event
    if (!oldStatus.available && newStatus.available) {
      const event: QuotaEvent = {
        type: 'quota_exceeded',
        remainingMinutes: newStatus.remainingMinutes,
        timestamp: new Date(),
      };
      eventListeners.current.forEach(listener => listener(event));
    }

    // Quota warning event
    if (
      oldStatus.status !== 'warning' && 
      newStatus.status === 'warning' &&
      !newState.warningShown
    ) {
      const event: QuotaEvent = {
        type: 'quota_warning',
        remainingMinutes: newStatus.remainingMinutes,
        timestamp: new Date(),
      };
      eventListeners.current.forEach(listener => listener(event));
      
      // Mark warning as shown
      setQuotaState(prev => ({ ...prev, warningShown: true }));
    }
  }, [config.warningThreshold]);

  /**
   * Register event listener
   */
  const onQuotaEvent = useCallback((
    callback: (event: QuotaEvent) => void
  ): (() => void) => {
    eventListeners.current.push(callback);
    
    // Return cleanup function
    return () => {
      const index = eventListeners.current.indexOf(callback);
      if (index > -1) {
        eventListeners.current.splice(index, 1);
      }
    };
  }, []);

  // ============================================================================
  // QUOTA ACTIONS
  // ============================================================================

  /**
   * Reset quota to initial state (manual reset)
   */
  const resetQuota = useCallback(() => {
    const newState = resetQuotaState(config.totalMinutes);
    setQuotaState(newState);

    // Emit reset event
    const event: QuotaEvent = {
      type: 'quota_reset',
      remainingMinutes: newState.remainingMinutes,
      timestamp: new Date(),
    };
    eventListeners.current.forEach(listener => listener(event));

    console.log('Quota reset to', config.totalMinutes, 'minutes');
  }, [config.totalMinutes]);

  /**
   * Update configuration
   */
  const updateConfig = useCallback((newConfig: Partial<QuotaConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  // ============================================================================
  // USAGE STATISTICS
  // ============================================================================

  /**
   * Get usage statistics
   */
  const getUsageStats = useCallback(() => {
    const totalSessions = quotaState.sessionHistory.length;
    const totalCost = quotaState.sessionHistory.reduce(
      (sum: number, session: SessionUsage) => sum + session.cost, 
      0
    );
    const averageSessionDuration = totalSessions > 0 
      ? quotaState.sessionHistory.reduce(
          (sum: number, session: SessionUsage) => sum + session.duration, 
          0
        ) / totalSessions / 60
      : 0;

    return {
      totalSessions,
      totalCost,
      averageSessionDuration,
      usagePercent: (quotaState.usedMinutes / quotaState.totalMinutes) * 100,
    };
  }, [quotaState]);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  /**
   * Save quota state to storage whenever it changes
   */
  useEffect(() => {
    saveQuotaToStorage(quotaState);
  }, [quotaState, saveQuotaToStorage]);

  /**
   * Cleanup active sessions on unmount
   */
  useEffect(() => {
    return () => {
      // Clean up any active sessions
      activeSessions.clear();
      eventListeners.current = [];
    };
  }, [activeSessions]);

  /**
   * Update quota state when config changes
   */
  useEffect(() => {
    if (quotaState.totalMinutes !== config.totalMinutes) {
      setQuotaState(prev => ({
        ...prev,
        totalMinutes: config.totalMinutes,
        remainingMinutes: config.totalMinutes - prev.usedMinutes,
      }));
    }
  }, [config.totalMinutes, quotaState.totalMinutes]);

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // State
    quotaState,
    quotaStatus,
    config,
    
    // Actions
    startSession,
    endSession,
    checkQuotaAvailable,
    getTimeRemaining,
    resetQuota,
    updateConfig,
    
    // Events
    onQuotaEvent,
    
    // Utilities
    getUsageStats,
  };
};

export default useQuotaManager;