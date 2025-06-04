// src/hooks/useAudioFallback.ts
// Browser TTS fallback when HeyGen quota is exceeded

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  AudioFallbackConfig,
  AudioFallbackState
} from '../types/heygen';
import {
  getBestAvailableVoice,
  isSpeechSynthesisSupported
} from '../utils/avatarutils';

// ============================================================================
// CONSTANTS
// ============================================================================

const DEFAULT_CONFIG: AudioFallbackConfig = {
  voice: null,
  rate: 1.0,
  pitch: 1.0,
  volume: 0.8,
};

const STORAGE_KEY = 'heygen_audio_fallback_config';

// ============================================================================
// TYPES
// ============================================================================

interface UseAudioFallbackReturn {
  // State
  state: AudioFallbackState;
  config: AudioFallbackConfig;
  
  // Actions
  speak: (text: string) => Promise<void>;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  clearQueue: () => void;
  
  // Configuration
  setVoice: (voice: SpeechSynthesisVoice | null) => void;
  setRate: (rate: number) => void;
  setPitch: (pitch: number) => void;
  setVolume: (volume: number) => void;
  updateConfig: (newConfig: Partial<AudioFallbackConfig>) => void;
  
  // Utilities
  getAvailableVoices: () => SpeechSynthesisVoice[];
  isSupported: boolean;
}

// ============================================================================
// MAIN HOOK
// ============================================================================

export const useAudioFallback = (
  initialConfig: Partial<AudioFallbackConfig> = {}
): UseAudioFallbackReturn => {
  // Check if browser supports Speech Synthesis
  const isSupported = isSpeechSynthesisSupported();

  // Configuration state
  const [config, setConfig] = useState<AudioFallbackConfig>(() => {
    const stored = loadConfigFromStorage();
    return {
      ...DEFAULT_CONFIG,
      ...stored,
      ...initialConfig,
    };
  });

  // Audio state
  const [state, setState] = useState<AudioFallbackState>({
    isSupported,
    availableVoices: [],
    currentVoice: null,
    isSpeaking: false,
    queue: [],
    error: null,
  });

  // References for current utterance and queue management
  const currentUtterance = useRef<SpeechSynthesisUtterance | null>(null);
  const isProcessingQueue = useRef(false);

  // ============================================================================
  // STORAGE FUNCTIONS
  // ============================================================================

  /**
   * Load configuration from localStorage
   */
  function loadConfigFromStorage(): Partial<AudioFallbackConfig> {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (!stored) return {};

      const parsed = JSON.parse(stored);
      // Don't restore voice object (it becomes invalid), just settings
      return {
        rate: parsed.rate,
        pitch: parsed.pitch,
        volume: parsed.volume,
      };
    } catch (error) {
      console.error('Failed to load audio config from storage:', error);
      return {};
    }
  }

  /**
   * Save configuration to localStorage
   */
  const saveConfigToStorage = useCallback((newConfig: AudioFallbackConfig) => {
    try {
      // Only save serializable properties
      const toSave = {
        rate: newConfig.rate,
        pitch: newConfig.pitch,
        volume: newConfig.volume,
        voiceName: newConfig.voice?.name || null,
      };
      localStorage.setItem(STORAGE_KEY, JSON.stringify(toSave));
    } catch (error) {
      console.error('Failed to save audio config to storage:', error);
    }
  }, []);

  // ============================================================================
  // VOICE MANAGEMENT
  // ============================================================================

  /**
   * Load available voices and set default
   */
  const loadVoices = useCallback(() => {
    if (!isSupported) return;

    const voices = speechSynthesis.getVoices();
    
    setState(prev => ({
      ...prev,
      availableVoices: voices,
      error: voices.length === 0 ? 'No voices available' : null,
    }));

    // Set default voice if none selected
    if (!config.voice && voices.length > 0) {
      const bestVoice = getBestAvailableVoice('female', 'en');
      if (bestVoice) {
        setConfig(prev => ({ ...prev, voice: bestVoice }));
        setState(prev => ({ ...prev, currentVoice: bestVoice }));
      }
    }
  }, [isSupported, config.voice]);

  /**
   * Get available voices
   */
  const getAvailableVoices = useCallback((): SpeechSynthesisVoice[] => {
    return state.availableVoices;
  }, [state.availableVoices]);

  // ============================================================================
  // SPEECH FUNCTIONS
  // ============================================================================

  /**
   * Process the speech queue
   */
  const processQueue = useCallback(async () => {
    if (!isSupported || isProcessingQueue.current || state.queue.length === 0) {
      return;
    }

    isProcessingQueue.current = true;
    setState(prev => ({ ...prev, isSpeaking: true }));

    const text = state.queue[0];
    
    try {
      await speakText(text);
    } catch (error) {
      console.error('Speech synthesis error:', error);
      setState(prev => ({
        ...prev,
        error: error instanceof Error ? error.message : 'Speech synthesis failed'
      }));
    }

    // Remove processed text from queue
    setState(prev => ({
      ...prev,
      queue: prev.queue.slice(1),
    }));

    isProcessingQueue.current = false;

    // Continue processing if queue has more items
    setState(prev => {
      if (prev.queue.length > 0) {
        // Schedule next item
        setTimeout(() => processQueue(), 100);
        return prev;
      } else {
        return { ...prev, isSpeaking: false };
      }
    });
  }, [isSupported, state.queue]);

  /**
   * Speak