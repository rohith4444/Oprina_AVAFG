// src/components/HybridAvatarManager.tsx
// Main hybrid avatar controller - orchestrates HeyGen + Fallback + Static modes

import { useState, useEffect, useCallback, useRef, forwardRef, useImperativeHandle } from 'react';
import type {
  AvatarMode,
  QuotaConfig,
  AvatarModeEvent,
  QuotaEvent,
  HeyGenSessionEvent
} from '../types/heygen';
import { useQuotaManager } from '../hooks/useQoutaManager';
import { useHeyGenSession } from '../hooks/useHeyGenSession';
import { useAudioFallback } from '../hooks/useAudioFallback';
import QuotaIndicator from './QuotaIndicator';
import ModeIndicator from './ModeIndicator';
import StaticAvatarDisplay from './StaticAvatarDisplay';
import AudioFallbackTTS from './AudioFallbackTTS';
import HeyGenAvatarComponent from './HeyGenAvatar';

// Import styles
import '../styles/HybridAvatarManager.css';

// ============================================================================
// TYPES
// ============================================================================

interface HybridAvatarManagerProps {
  selectedAvatarId?: string;
  selectedVoiceId?: string;
  quotaConfig?: Partial<QuotaConfig>;
  onModeChange?: (event: AvatarModeEvent) => void;
  onQuotaEvent?: (event: QuotaEvent) => void;
  onSessionEvent?: (event: HeyGenSessionEvent) => void;
  className?: string;
}

export interface HybridAvatarManagerRef {
  speak: (text: string) => Promise<boolean>;
  getCurrentMode: () => AvatarMode;
  getQuotaStatus: () => any;
  resetQuota: () => void;
  switchToMode: (mode: AvatarMode) => Promise<void>;
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

const HybridAvatarManager = forwardRef<HybridAvatarManagerRef, HybridAvatarManagerProps>(({
  selectedAvatarId = 'Ann_Therapist_public',
  selectedVoiceId = '',
  quotaConfig = {},
  onModeChange,
  onQuotaEvent,
  onSessionEvent,
  className = '',
}, ref) => {
  
  // ============================================================================
  // STATE MANAGEMENT
  // ============================================================================
  
  const [currentMode, setCurrentMode] = useState<AvatarMode>('static');
  const [error, setError] = useState<string | null>(null);
  const [currentSpeechText, setCurrentSpeechText] = useState<string>('');

  // Refs for managing speech
  const lastSpokenText = useRef<string>('');
  const isManualModeSwitch = useRef<boolean>(false);

  // ============================================================================
  // HOOKS INTEGRATION
  // ============================================================================

  // Quota management
  const {
    quotaStatus,
    checkQuotaAvailable,
    onQuotaEvent: onQuotaEventHook,
    resetQuota,
  } = useQuotaManager(quotaConfig);

  // HeyGen session management
  const {
    isReady: isHeyGenReady,
    isConnecting: isHeyGenConnecting,
    createSession,
    endSession,
    speak: heygenSpeak,
    onSessionEvent: onSessionEventHook,
  } = useHeyGenSession({
    avatarId: selectedAvatarId,
    voiceId: selectedVoiceId,
  });

  // Audio fallback management
  const {
    speak: fallbackSpeak,
  } = useAudioFallback();

  // ============================================================================
  // EVENT HANDLERS
  // ============================================================================

  // Handle quota events
  useEffect(() => {
    const cleanup = onQuotaEventHook((event: QuotaEvent) => {
      console.log('📊 Quota event:', event.type);
      
      if (event.type === 'quota_exceeded' && currentMode === 'interactive') {
        console.log('⚠️ Quota exceeded, switching to fallback mode');
        switchToFallbackMode('Quota exceeded');
      }
      
      onQuotaEvent?.(event);
    });
    
    return cleanup;
  }, [onQuotaEventHook, currentMode, onQuotaEvent]);

  // Handle session events
  useEffect(() => {
    const cleanup = onSessionEventHook((event: HeyGenSessionEvent) => {
      console.log('🎭 Session event:', event.type);
      
      if (event.type === 'session_ready' && currentMode !== 'interactive') {
        switchToInteractiveMode();
      } else if (event.type === 'session_error') {
        switchToFallbackMode('Session error');
      }
      
      onSessionEvent?.(event);
    });
    
    return cleanup;
  }, [onSessionEventHook, currentMode, onSessionEvent]);

  // ============================================================================
  // MODE MANAGEMENT
  // ============================================================================

  const emitModeChange = useCallback((fromMode: AvatarMode, toMode: AvatarMode, reason: string) => {
    const event: AvatarModeEvent = {
      type: 'mode_changed',
      fromMode,
      toMode,
      reason,
      timestamp: new Date(),
    };
    
    console.log(`🔄 Mode change: ${fromMode} → ${toMode} (${reason})`);
    onModeChange?.(event);
  }, [onModeChange]);

  const switchToInteractiveMode = useCallback(async () => {
    if (currentMode === 'interactive') return;
    
    const previousMode = currentMode;
    setCurrentMode('interactive');
    emitModeChange(previousMode, 'interactive', 'HeyGen session ready');
  }, [currentMode, emitModeChange]);

  const switchToFallbackMode = useCallback((reason: string) => {
    if (currentMode === 'fallback') return;
    
    const previousMode = currentMode;
    setCurrentMode('fallback');
    emitModeChange(previousMode, 'fallback', reason);
  }, [currentMode, emitModeChange]);

  const switchToStaticMode = useCallback((reason: string) => {
    if (currentMode === 'static') return;
    
    const previousMode = currentMode;
    setCurrentMode('static');
    emitModeChange(previousMode, 'static', reason);
  }, [currentMode, emitModeChange]);

  const switchToMode = useCallback(async (mode: AvatarMode): Promise<void> => {
    isManualModeSwitch.current = true;
    
    try {
      if (mode === 'interactive') {
        if (!checkQuotaAvailable()) {
          throw new Error('Cannot switch to interactive mode: quota exceeded');
        }
        
        if (!isHeyGenReady) {
          setCurrentMode('connecting');
          const success = await createSession();
          if (!success) {
            throw new Error('Failed to create HeyGen session');
          }
        } else {
          await switchToInteractiveMode();
        }
      } else if (mode === 'fallback') {
        if (isHeyGenReady) {
          await endSession();
        }
        switchToFallbackMode('Manual switch');
      } else if (mode === 'static') {
        if (isHeyGenReady) {
          await endSession();
        }
        switchToStaticMode('Manual switch');
      }
    } catch (error) {
      console.error('❌ Failed to switch mode:', error);
      setError(error instanceof Error ? error.message : 'Mode switch failed');
    } finally {
      isManualModeSwitch.current = false;
    }
  }, [checkQuotaAvailable, isHeyGenReady, createSession, endSession, switchToInteractiveMode, switchToFallbackMode, switchToStaticMode]);

  // ============================================================================
  // SPEECH MANAGEMENT
  // ============================================================================

  const speak = useCallback(async (text: string): Promise<boolean> => {
    if (!text.trim()) return false;
    
    // Avoid repeating the same text
    if (text === lastSpokenText.current) {
      console.log('🔄 Skipping duplicate text:', text.substring(0, 50));
      return true;
    }
    
    lastSpokenText.current = text;
    setCurrentSpeechText(text);
    
    try {
      if (currentMode === 'interactive' && isHeyGenReady) {
        console.log('🎥 Speaking via HeyGen:', text.substring(0, 50));
        return await heygenSpeak(text);
      } else {
        console.log('🔊 Speaking via fallback TTS:', text.substring(0, 50));
        await fallbackSpeak(text);
        return true;
      }
    } catch (error) {
      console.error('❌ Speech failed:', error);
      
      // Fallback to TTS if HeyGen fails
      if (currentMode === 'interactive') {
        console.log('🔄 Falling back to TTS due to HeyGen error');
        switchToFallbackMode('HeyGen speech failed');
        await fallbackSpeak(text);
        return true;
      }
      
      return false;
    } finally {
      setCurrentSpeechText('');
    }
  }, [currentMode, isHeyGenReady, heygenSpeak, fallbackSpeak, switchToFallbackMode]);

  // ============================================================================
  // AUTO MODE MANAGEMENT
  // ============================================================================

  useEffect(() => {
    // Auto-determine initial mode based on quota
    if (!isManualModeSwitch.current) {
      if (checkQuotaAvailable()) {
        // Don't auto-start interactive mode, wait for user interaction
        switchToStaticMode('Initial state');
      } else {
        switchToFallbackMode('Quota not available');
      }
    }
  }, [checkQuotaAvailable, switchToStaticMode, switchToFallbackMode]);

  // ============================================================================
  // REF EXPOSURE
  // ============================================================================

  useImperativeHandle(ref, () => ({
    speak,
    getCurrentMode: () => currentMode,
    getQuotaStatus: () => quotaStatus,
    resetQuota,
    switchToMode,
  }), [speak, currentMode, quotaStatus, resetQuota, switchToMode]);

  // ============================================================================
  // RENDER HELPERS
  // ============================================================================

  const renderStatusIndicators = () => (
    <div className="status-indicators">
      <ModeIndicator 
        mode={currentMode}
        isConnecting={isHeyGenConnecting || currentMode === 'connecting'}
      />
      <QuotaIndicator quotaStatus={quotaStatus} />
    </div>
  );

  const renderAvatarContent = () => {
    if (currentMode === 'interactive' && isHeyGenReady) {
      return (
            <HeyGenAvatarComponent
                isListening={false}
                isSpeaking={!!currentSpeechText}
                onAvatarReady={() => console.log('🎉 HeyGen avatar ready')}
                onAvatarError={(error: string) => {
                console.error('❌ HeyGen avatar error:', error);
                switchToFallbackMode('HeyGen avatar error');
                }}
                onAvatarStartTalking={() => console.log('🗣️ HeyGen started talking')}
                onAvatarStopTalking={() => console.log('🤐 HeyGen stopped talking')}
            />
            );
    }

    return (
            <StaticAvatarDisplay
                avatar={null}  // or remove this prop if it's optional
                isLoading={isHeyGenConnecting || currentMode === 'connecting'}
                error={error}
                quotaStatus={quotaStatus}
            />
            );
  };

  const renderFallbackTTS = () => {
    if (currentMode === 'fallback') {
      return (
        <AudioFallbackTTS
          text={currentSpeechText}
          isActive={currentMode === 'fallback'}
          onStart={() => console.log('🔊 Fallback TTS started')}
          onEnd={() => console.log('🔇 Fallback TTS ended')}
          onError={(error) => console.error('❌ Fallback TTS error:', error)}
          className="fallback-tts-overlay"
        />
      );
    }
    return null;
  };

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className={`hybrid-avatar-manager ${className}`}>
      {/* Status Indicators Row */}
      {renderStatusIndicators()}

      {/* Avatar Container */}
      <div className="avatar-container-wrapper">
        {renderAvatarContent()}
        {renderFallbackTTS()}
      </div>

      {/* Debug Info (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="debug-info">
          <small>
            Mode: {currentMode} | 
            HeyGen: {isHeyGenReady ? 'Ready' : 'Not Ready'} | 
            Quota: {Math.round(quotaStatus.remainingMinutes)}min | 
          </small>
        </div>
      )}
    </div>
  );
});

HybridAvatarManager.displayName = 'HybridAvatarManager';

export default HybridAvatarManager;