// src/types/heygen.ts
// Complete TypeScript definitions for HeyGen hybrid avatar implementation

import { AvatarQuality } from '@heygen/streaming-avatar';

// ============================================================================
// CORE HEYGEN API TYPES
// ============================================================================

export interface HeyGenAvatar {
  avatar_id: string;
  avatar_name: string;
  gender: 'male' | 'female' | 'unknown';
  preview_image_url: string;
  preview_video_url: string;
}

export interface HeyGenVoice {
  voice_id: string;
  language: string;
  gender: 'male' | 'female' | 'Male' | 'Female';
  name: string;
  preview_audio: string;
  support_pause: boolean;
  emotion_support: boolean;
  support_interactive_avatar: boolean;
}

export interface HeyGenApiResponse<T> {
  error: string | null;
  data: T;
  message?: string;
}

// ============================================================================
// SESSION MANAGEMENT TYPES
// ============================================================================

export interface SessionConfig {
  avatarId: string;
  voiceId: string;
  quality: AvatarQuality;
  activityIdleTimeout: number; // seconds
  disableIdleTimeout?: boolean;
  language?: string;
}

export interface SessionInfo {
  session_id: string;
  access_token: string;
  url: string;
  is_paid: boolean;
  session_duration_limit: number;
}

export type SessionStatus = 
  | 'idle'           // No session active
  | 'creating'       // Session being created
  | 'connecting'     // WebRTC connection establishing
  | 'ready'          // Session ready for interaction
  | 'speaking'       // Avatar is currently speaking
  | 'error'          // Session error occurred
  | 'cleanup';       // Session being destroyed

export interface SessionState {
  status: SessionStatus;
  sessionId: string | null;
  sessionInfo: SessionInfo | null;
  error: string | null;
  createdAt: Date | null;
  lastActivity: Date | null;
}

// ============================================================================
// AVATAR MODE TYPES
// ============================================================================

export type AvatarMode = 
  | 'static'         // Displaying static preview image
  | 'connecting'     // Creating/connecting to HeyGen session
  | 'interactive'    // Live HeyGen avatar active
  | 'fallback';      // Browser TTS fallback mode

export interface AvatarState {
  mode: AvatarMode;
  currentAvatar: HeyGenAvatar | null;
  currentVoice: HeyGenVoice | null;
  isListening: boolean;
  isSpeaking: boolean;
  error: string | null;
}

// ============================================================================
// QUOTA MANAGEMENT TYPES
// ============================================================================

export interface QuotaConfig {
  totalMinutes: number;        // Total quota for entire account (e.g., 20 minutes)
  resetType: 'manual' | 'upgrade';  // Manual reset or account upgrade only
  warningThreshold: number;    // Minutes remaining to show warning
  gracePeriod: number;         // Seconds allowed over limit for conversation completion
}

export interface QuotaState {
  totalMinutes: number;
  usedMinutes: number;
  remainingMinutes: number;
  lastResetDate: Date;
  sessionHistory: SessionUsage[];
  isExceeded: boolean;
  warningShown: boolean;
}

export interface SessionUsage {
  sessionId: string;
  duration: number;           // in seconds
  startTime: Date;
  endTime: Date;
  cost: number;              // in credits
}

export interface QuotaStatus {
  available: boolean;
  remainingMinutes: number;
  remainingSeconds: number;
  percentUsed: number;
  status: 'available' | 'warning' | 'exceeded' | 'grace';
  message: string;
}

// ============================================================================
// AUDIO FALLBACK TYPES
// ============================================================================

export interface AudioFallbackConfig {
  voice: SpeechSynthesisVoice | null;
  rate: number;              // 0.1 to 10
  pitch: number;             // 0 to 2
  volume: number;            // 0 to 1
}

export interface AudioFallbackState {
  isSupported: boolean;
  availableVoices: SpeechSynthesisVoice[];
  currentVoice: SpeechSynthesisVoice | null;
  isSpeaking: boolean;
  queue: string[];
  error: string | null;
}

// ============================================================================
// EVENT TYPES
// ============================================================================

export interface HeyGenSessionEvent {
  type: 'session_created' | 'session_ready' | 'session_error' | 'session_ended';
  sessionId: string;
  timestamp: Date;
  data?: any;
}

export interface QuotaEvent {
  type: 'quota_warning' | 'quota_exceeded' | 'quota_reset';
  remainingMinutes: number;
  timestamp: Date;
}

export interface AvatarModeEvent {
  type: 'mode_changed';
  fromMode: AvatarMode;
  toMode: AvatarMode;
  reason: string;
  timestamp: Date;
}

// ============================================================================
// COMPONENT PROPS TYPES
// ============================================================================

export interface StaticAvatarDisplayProps {
  avatar: HeyGenAvatar | null;
  isLoading: boolean;
  error: string | null;
  quotaStatus: QuotaStatus;
  className?: string;
}

export interface QuotaIndicatorProps {
  quotaStatus: QuotaStatus;
  showDetails?: boolean;
  position?: 'top' | 'bottom' | 'overlay';
  className?: string;
}

export interface AudioFallbackProps {
  text: string;
  config: AudioFallbackConfig;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
}

export interface HybridAvatarManagerProps {
  selectedAvatarId?: string;
  selectedVoiceId?: string;
  quotaConfig?: Partial<QuotaConfig>;
  onModeChange?: (event: AvatarModeEvent) => void;
  onQuotaEvent?: (event: QuotaEvent) => void;
  onSessionEvent?: (event: HeyGenSessionEvent) => void;
  className?: string;
}

// ============================================================================
// SERVICE RESPONSE TYPES
// ============================================================================

export interface FetchAvatarsResponse {
  avatars: HeyGenAvatar[];
  total: number;
}

export interface FetchVoicesResponse {
  voices: HeyGenVoice[];
  total: number;
}

export interface CreateSessionResponse {
  success: boolean;
  sessionInfo: SessionInfo | null;
  error: string | null;
}

export interface SessionHealthResponse {
  sessionId: string;
  isActive: boolean;
  duration: number;
  lastActivity: Date;
  cost: number;
}

// ============================================================================
// ERROR TYPES
// ============================================================================

export interface HeyGenError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
}

export type HeyGenErrorType = 
  | 'API_ERROR'
  | 'SESSION_ERROR'
  | 'QUOTA_ERROR'
  | 'NETWORK_ERROR'
  | 'CONFIG_ERROR'
  | 'TIMEOUT_ERROR';

// ============================================================================
// STORAGE TYPES
// ============================================================================

export interface StoredQuotaData {
  quotaState: QuotaState;
  lastUpdated: string; // ISO string
  version: string;
}

export interface StoredAvatarPreferences {
  selectedAvatarId: string | null;
  selectedVoiceId: string | null;
  audioConfig: AudioFallbackConfig;
  quotaConfig: QuotaConfig;
}

// ============================================================================
// UTILITY TYPES
// ============================================================================

export type AvatarFilter = {
  gender?: 'male' | 'female';
  search?: string;
  supportsPause?: boolean;
  emotionSupport?: boolean;
};

export type VoiceFilter = {
  language?: string;
  gender?: 'male' | 'female';
  emotionSupport?: boolean;
  interactiveSupport?: boolean;
};

// ============================================================================
// RE-EXPORT HEYGEN SDK TYPES
// ============================================================================

export { StreamingEvents, AvatarQuality } from '@heygen/streaming-avatar';

// ============================================================================
// CONSTANTS
// ============================================================================

export const DEFAULT_QUOTA_CONFIG: QuotaConfig = {
  totalMinutes: 20,
  resetType: 'manual',  // Only manual reset or account upgrade
  warningThreshold: 5,
  gracePeriod: 30
};

export const DEFAULT_SESSION_CONFIG: Partial<SessionConfig> = {
  quality: AvatarQuality.Low,
  activityIdleTimeout: 30,  // Match HeyGen's minimum billing period
  disableIdleTimeout: false,
  language: 'English'
};

export const DEFAULT_AUDIO_CONFIG: AudioFallbackConfig = {
  voice: null, // Will be set to best available voice
  rate: 1.0,
  pitch: 1.0,
  volume: 0.8
};

// ============================================================================
// TYPE GUARDS
// ============================================================================

export const isHeyGenAvatar = (obj: any): obj is HeyGenAvatar => {
  return obj && 
    typeof obj.avatar_id === 'string' &&
    typeof obj.avatar_name === 'string' &&
    typeof obj.preview_image_url === 'string';
};

export const isSessionInfo = (obj: any): obj is SessionInfo => {
  return obj &&
    typeof obj.session_id === 'string' &&
    typeof obj.access_token === 'string';
};

export const isQuotaExceeded = (quota: QuotaState): boolean => {
  return quota.usedMinutes >= quota.totalMinutes;
};

export const isQuotaWarning = (quota: QuotaState, threshold: number): boolean => {
  return quota.remainingMinutes <= threshold && quota.remainingMinutes > 0;
};