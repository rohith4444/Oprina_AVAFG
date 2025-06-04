// src/components/AudioFallbackTTS.tsx
// Browser TTS fallback component when HeyGen quota is exceeded

import React, { useEffect, useCallback } from 'react';
import { useAudioFallback } from '../hooks/useAudioFallback';
import type { AudioFallbackConfig } from '../types/heygen';

interface AudioFallbackTTSProps {
  text?: string;
  isActive: boolean;
  config?: Partial<AudioFallbackConfig>;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
  className?: string;
}

const AudioFallbackTTS: React.FC<AudioFallbackTTSProps> = ({
  text,
  isActive,
  config = {},
  onStart,
  onEnd,
  onError,
  className = '',
}) => {
  const {
    state,
    config: currentConfig,
    speak,
    stop,
    clearQueue,
    updateConfig,
    isSupported,
  } = useAudioFallback(config);

  // Update configuration when props change
  useEffect(() => {
    if (config && Object.keys(config).length > 0) {
      updateConfig(config);
    }
  }, [config, updateConfig]);

  // Speak text when provided and component is active
  useEffect(() => {
    if (text && text.trim() && isActive && isSupported) {
      speak(text)
        .then(() => {
          onStart?.();
        })
        .catch((error) => {
          onError?.(error.message);
        });
    }
  }, [text, isActive, isSupported, speak, onStart, onError]);

  // Handle speaking state changes
  useEffect(() => {
    if (state.isSpeaking) {
      onStart?.();
    } else {
      onEnd?.();
    }
  }, [state.isSpeaking, onStart, onEnd]);

  // Cleanup when component becomes inactive
  useEffect(() => {
    if (!isActive && state.isSpeaking) {
      stop();
      clearQueue();
    }
  }, [isActive, state.isSpeaking, stop, clearQueue]);

  // Handle errors
  useEffect(() => {
    if (state.error) {
      onError?.(state.error);
    }
  }, [state.error, onError]);

  const handleStopSpeaking = useCallback(() => {
    stop();
    clearQueue();
  }, [stop, clearQueue]);

  const handleClearQueue = useCallback(() => {
    clearQueue();
  }, [clearQueue]);

  const getVoiceInfo = () => {
    if (!state.currentVoice) return 'Default Voice';
    return state.currentVoice.name || 'Unknown Voice';
  };

  const getQueueInfo = () => {
    if (state.queue.length === 0) return null;
    if (state.queue.length === 1) return '1 item in queue';
    return `${state.queue.length} items in queue`;
  };

  // Don't render if browser doesn't support TTS
  if (!isSupported) {
    return (
      <div className={`audio-fallback-tts unsupported ${className}`}>
        <div className="tts-status">
          <span className="status-icon">❌</span>
          <span className="status-text">Browser TTS not supported</span>
        </div>
      </div>
    );
  }

  // Don't render if not active
  if (!isActive) {
    return null;
  }

  return (
    <div className={`audio-fallback-tts ${state.isSpeaking ? 'speaking' : ''} ${className}`}>
      {/* TTS Status Indicator */}
      <div className="tts-status">
        <div className="status-indicator">
          {state.isSpeaking ? (
            <>
              <div className="sound-waves">
                <div className="wave"></div>
                <div className="wave"></div>
                <div className="wave"></div>
              </div>
              <span className="status-text">Speaking...</span>
            </>
          ) : state.queue.length > 0 ? (
            <>
              <span className="status-icon">⏳</span>
              <span className="status-text">Queued</span>
            </>
          ) : (
            <>
              <span className="status-icon">🔊</span>
              <span className="status-text">TTS Ready</span>
            </>
          )}
        </div>
      </div>

      {/* TTS Controls */}
      <div className="tts-controls">
        <div className="tts-info">
          <div className="voice-info">
            <span className="label">Voice:</span>
            <span className="value">{getVoiceInfo()}</span>
          </div>
          
          <div className="config-info">
            <span className="label">Rate:</span>
            <span className="value">{currentConfig.rate.toFixed(1)}x</span>
            <span className="label">Volume:</span>
            <span className="value">{Math.round(currentConfig.volume * 100)}%</span>
          </div>

          {getQueueInfo() && (
            <div className="queue-info">
              <span className="queue-text">{getQueueInfo()}</span>
            </div>
          )}
        </div>

        <div className="tts-actions">
          {state.isSpeaking && (
            <button 
              className="tts-button stop-button"
              onClick={handleStopSpeaking}
              title="Stop speaking"
            >
              ⏹️
            </button>
          )}
          
          {state.queue.length > 0 && (
            <button 
              className="tts-button clear-button"
              onClick={handleClearQueue}
              title="Clear queue"
            >
              🗑️
            </button>
          )}
        </div>
      </div>

      {/* Error Display */}
      {state.error && (
        <div className="tts-error">
          <span className="error-icon">⚠️</span>
          <span className="error-text">{state.error}</span>
        </div>
      )}

      {/* Debug Info (development only) */}
      {process.env.NODE_ENV === 'development' && (
        <div className="tts-debug">
          <small>
            Voices: {state.availableVoices.length} | 
            Queue: {state.queue.length} | 
            Speaking: {state.isSpeaking ? 'Yes' : 'No'}
          </small>
        </div>
      )}
    </div>
  );
};

export default AudioFallbackTTS;