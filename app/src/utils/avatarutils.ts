// src/utils/avatarUtils.ts
// Pure utility functions for avatar operations - no dependencies

import type {
  HeyGenAvatar,
  HeyGenVoice,
  QuotaState,
  QuotaStatus,
  SessionUsage,
  AvatarFilter,
  VoiceFilter,
  StoredQuotaData 
} from '../types/heygen';

// ============================================================================
// AVATAR UTILITY FUNCTIONS
// ============================================================================

/**
 * Filter avatars based on criteria
 */
export const filterAvatars = (
  avatars: HeyGenAvatar[],
  filter: AvatarFilter
): HeyGenAvatar[] => {
  return avatars.filter(avatar => {
    if (filter.gender && avatar.gender !== filter.gender) {
      return false;
    }
    
    if (filter.search) {
      const searchLower = filter.search.toLowerCase();
      return avatar.avatar_name.toLowerCase().includes(searchLower) ||
             avatar.avatar_id.toLowerCase().includes(searchLower);
    }
    
    return true;
  });
};

/**
 * Filter voices based on criteria
 */
export const filterVoices = (
  voices: HeyGenVoice[],
  filter: VoiceFilter
): HeyGenVoice[] => {
  return voices.filter(voice => {
    if (filter.language && voice.language !== filter.language) {
      return false;
    }
    
    if (filter.gender) {
      const voiceGender = voice.gender.toLowerCase();
      if (voiceGender !== filter.gender) {
        return false;
      }
    }
    
    if (filter.emotionSupport !== undefined && voice.emotion_support !== filter.emotionSupport) {
      return false;
    }
    
    if (filter.interactiveSupport !== undefined && voice.support_interactive_avatar !== filter.interactiveSupport) {
      return false;
    }
    
    return true;
  });
};

/**
 * Find best matching voice for an avatar
 */
export const findMatchingVoice = (
  avatar: HeyGenAvatar,
  voices: HeyGenVoice[]
): HeyGenVoice | null => {
  // First try to match gender and interactive support
  const exactMatch = voices.find(voice => 
    voice.gender.toLowerCase() === avatar.gender &&
    voice.support_interactive_avatar
  );
  
  if (exactMatch) return exactMatch;
  
  // Fallback to any interactive-supported voice
  const interactiveVoice = voices.find(voice => voice.support_interactive_avatar);
  
  return interactiveVoice || null;
};

/**
 * Get avatar display name with fallback
 */
export const getAvatarDisplayName = (avatar: HeyGenAvatar | null): string => {
  if (!avatar) return 'Unknown Avatar';
  return avatar.avatar_name || avatar.avatar_id || 'Unnamed Avatar';
};

/**
 * Check if avatar image URL is valid
 */
export const isValidAvatarImageUrl = (url: string): boolean => {
  try {
    const urlObj = new URL(url);
    return urlObj.protocol === 'https:' && urlObj.hostname.includes('heygen');
  } catch {
    return false;
  }
};

// ============================================================================
// QUOTA UTILITY FUNCTIONS
// ============================================================================

/**
 * Calculate quota status from current state
 */
export const calculateQuotaStatus = (
  quotaState: QuotaState,
  warningThreshold: number = 5
): QuotaStatus => {
  const remainingMinutes = Math.max(0, quotaState.remainingMinutes);
  const remainingSeconds = remainingMinutes * 60;
  const percentUsed = Math.min(100, (quotaState.usedMinutes / quotaState.totalMinutes) * 100);
  
  let status: QuotaStatus['status'];
  let message: string;
  
  if (quotaState.isExceeded) {
    status = 'exceeded';
    message = 'Interactive time limit reached. Using voice-only mode.';
  } else if (remainingMinutes <= 0) {
    status = 'grace';
    message = 'In grace period. Session will end soon.';
  } else if (remainingMinutes <= warningThreshold) {
    status = 'warning';
    message = `${Math.floor(remainingMinutes)} minutes of interactive time remaining.`;
  } else {
    status = 'available';
    message = `${Math.floor(remainingMinutes)} minutes of interactive time available.`;
  }
  
  return {
    available: !quotaState.isExceeded,
    remainingMinutes,
    remainingSeconds,
    percentUsed,
    status,
    message
  };
};

/**
 * Update quota state with new session usage
 */
export const updateQuotaWithUsage = (
  currentQuota: QuotaState,
  sessionUsage: SessionUsage
): QuotaState => {
  const usedMinutes = currentQuota.usedMinutes + (sessionUsage.duration / 60);
  const remainingMinutes = Math.max(0, currentQuota.totalMinutes - usedMinutes);
  
  return {
    ...currentQuota,
    usedMinutes,
    remainingMinutes,
    sessionHistory: [...currentQuota.sessionHistory, sessionUsage],
    isExceeded: usedMinutes >= currentQuota.totalMinutes
  };
};

/**
 * Check if quota should be reset
 * For account-level quota: only manual reset or account upgrade
 */
export const shouldResetQuota = (): boolean => {
  return false;
};

/**
 * Reset quota state to initial values
 */
export const resetQuotaState = (totalMinutes: number = 20): QuotaState => {
  return {
    totalMinutes,
    usedMinutes: 0,
    remainingMinutes: totalMinutes,
    lastResetDate: new Date(),
    sessionHistory: [],
    isExceeded: false,
    warningShown: false
  };
};

/**
 * Calculate total cost from session history
 */
export const calculateTotalCost = (sessions: SessionUsage[]): number => {
  return sessions.reduce((total, session) => total + session.cost, 0);
};

/**
 * Get usage statistics
 */
export const getUsageStatistics = (quotaState: QuotaState) => {
  const totalSessions = quotaState.sessionHistory.length;
  const totalCost = calculateTotalCost(quotaState.sessionHistory);
  const averageSessionDuration = totalSessions > 0 
    ? quotaState.sessionHistory.reduce((sum, s) => sum + s.duration, 0) / totalSessions / 60
    : 0;
  
  return {
    totalSessions,
    totalCost,
    averageSessionDuration,
    usagePercent: (quotaState.usedMinutes / quotaState.totalMinutes) * 100
  };
};

// ============================================================================
// SESSION UTILITY FUNCTIONS
// ============================================================================

/**
 * Calculate session cost based on duration
 */
export const calculateSessionCost = (durationSeconds: number): number => {
  // HeyGen billing: 1 credit = 5 minutes, minimum 30 seconds = 0.1 credits
  const minimumSeconds = 30;
  const billingSeconds = Math.max(minimumSeconds, durationSeconds);
  const credits = billingSeconds / (5 * 60); // 5 minutes per credit
  return Math.round(credits * 1000) / 1000; // Round to 3 decimal places
};

/**
 * Format duration for display
 */
export const formatDuration = (seconds: number): string => {
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  
  if (remainingSeconds === 0) {
    return `${minutes}m`;
  }
  
  return `${minutes}m ${remainingSeconds}s`;
};

/**
 * Format quota time for display
 */
export const formatQuotaTime = (minutes: number): string => {
  if (minutes < 1) {
    return `${Math.round(minutes * 60)}s`;
  }
  
  const wholeMinutes = Math.floor(minutes);
  const seconds = Math.round((minutes - wholeMinutes) * 60);
  
  if (seconds === 0) {
    return `${wholeMinutes}:00`;
  }
  
  return `${wholeMinutes}:${seconds.toString().padStart(2, '0')}`;
};

// ============================================================================
// STORAGE UTILITY FUNCTIONS
// ============================================================================

/**
 * Serialize quota data for storage
 */
export const serializeQuotaData = (quotaState: QuotaState): StoredQuotaData => {
  return {
    quotaState: {
      ...quotaState,
      lastResetDate: quotaState.lastResetDate,
      sessionHistory: quotaState.sessionHistory.map(session => ({
        ...session,
        startTime: session.startTime,
        endTime: session.endTime
      }))
    },
    lastUpdated: new Date().toISOString(),
    version: '1.0.0'
  };
};

/**
 * Deserialize quota data from storage
 */
export const deserializeQuotaData = (stored: StoredQuotaData): QuotaState => {
  return {
    ...stored.quotaState,
    lastResetDate: new Date(stored.quotaState.lastResetDate),
    sessionHistory: stored.quotaState.sessionHistory.map(session => ({
      ...session,
      startTime: new Date(session.startTime),
      endTime: new Date(session.endTime)
    }))
  };
};

/**
 * Validate stored quota data
 */
export const isValidStoredQuotaData = (data: any): data is StoredQuotaData => {
  return data &&
    data.quotaState &&
    typeof data.quotaState.totalMinutes === 'number' &&
    typeof data.quotaState.usedMinutes === 'number' &&
    Array.isArray(data.quotaState.sessionHistory) &&
    typeof data.lastUpdated === 'string' &&
    typeof data.version === 'string';
};

// ============================================================================
// AUDIO UTILITY FUNCTIONS
// ============================================================================

/**
 * Get best available speech synthesis voice
 */
export const getBestAvailableVoice = (
  preferredGender?: 'male' | 'female',
  preferredLang?: string
): SpeechSynthesisVoice | null => {
  const voices = speechSynthesis.getVoices();
  
  if (voices.length === 0) return null;
  
  // First try exact match
  const exactMatch = voices.find(voice => 
    (!preferredGender || voice.name.toLowerCase().includes(preferredGender)) &&
    (!preferredLang || voice.lang.includes(preferredLang)) &&
    voice.localService
  );
  
  if (exactMatch) return exactMatch;
  
  // Fallback to any local voice
  const localVoice = voices.find(voice => voice.localService);
  
  return localVoice || voices[0];
};

/**
 * Check if Web Speech API is supported
 */
export const isSpeechSynthesisSupported = (): boolean => {
  return 'speechSynthesis' in window && 'SpeechSynthesisUtterance' in window;
};

// ============================================================================
// ERROR UTILITY FUNCTIONS
// ============================================================================

/**
 * Create standardized error object
 */
export const createHeyGenError = (
  code: string,
  message: string,
  details?: any
): Error => {
  const error = new Error(message);
  error.name = 'HeyGenError';
  (error as any).code = code;
  (error as any).details = details;
  (error as any).timestamp = new Date();
  return error;
};

/**
 * Check if error is a HeyGen-specific error
 */
export const isHeyGenError = (error: any): boolean => {
  return error && error.name === 'HeyGenError' && error.code;
};

// ============================================================================
// VALIDATION UTILITY FUNCTIONS
// ============================================================================

/**
 * Validate environment variables
 */
export const validateEnvironment = (): { valid: boolean; missing: string[] } => {
  const required = ['HEYGEN_API_KEY']; // Match your existing setup
  const missing = required.filter(key => !import.meta.env[key]);
  
  return {
    valid: missing.length === 0,
    missing
  };
};

/**
 * Sanitize user input
 */
export const sanitizeInput = (input: string): string => {
  return input.replace(/[<>]/g, '').trim();
};

/**
 * Generate unique session ID
 */
export const generateSessionId = (): string => {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
};