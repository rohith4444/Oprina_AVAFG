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
   * Speak a single text string
   */
  const speakText = useCallback((text: string): Promise<void> => {
    return new Promise((resolve, reject) => {
      if (!isSupported) {
        reject(new Error('Speech synthesis not supported'));
        return;
      }

      if (!text.trim()) {
        resolve();
        return;
      }

      const utterance = new SpeechSynthesisUtterance(text);
      
      // Apply configuration
      if (config.voice) {
        utterance.voice = config.voice;
      }
      utterance.rate = config.rate;
      utterance.pitch = config.pitch;
      utterance.volume = config.volume;

      // Set up event handlers
      utterance.onstart = () => {
        currentUtterance.current = utterance;
        setState(prev => ({ ...prev, isSpeaking: true, error: null }));
      };

      utterance.onend = () => {
        currentUtterance.current = null;
        setState(prev => ({ ...prev, isSpeaking: false }));
        resolve();
      };

      utterance.onerror = (event) => {
        currentUtterance.current = null;
        setState(prev => ({ 
          ...prev, 
          isSpeaking: false, 
          error: `Speech synthesis error: ${event.error}` 
        }));
        reject(new Error(`Speech synthesis error: ${event.error}`));
      };

      // Start speaking
      speechSynthesis.speak(utterance);
    });
  }, [isSupported, config]);

  /**
   * Add text to speech queue
   */
  const speak = useCallback(async (text: string): Promise<void> => {
    if (!isSupported) {
      throw new Error('Speech synthesis not supported');
    }

    if (!text.trim()) {
      return;
    }

    // Add to queue
    setState(prev => ({
      ...prev,
      queue: [...prev.queue, text],
      error: null,
    }));

    // Start processing if not already running
    if (!isProcessingQueue.current) {
      setTimeout(() => processQueue(), 50);
    }
  }, [isSupported, processQueue]);

  /**
   * Stop current speech and clear queue
   */
  const stop = useCallback(() => {
    if (isSupported) {
      speechSynthesis.cancel();
      currentUtterance.current = null;
      isProcessingQueue.current = false;
      
      setState(prev => ({
        ...prev,
        isSpeaking: false,
        queue: [],
        error: null,
      }));
    }
  }, [isSupported]);

  /**
   * Pause current speech
   */
  const pause = useCallback(() => {
    if (isSupported && speechSynthesis.speaking) {
      speechSynthesis.pause();
    }
  }, [isSupported]);

  /**
   * Resume paused speech
   */
  const resume = useCallback(() => {
    if (isSupported && speechSynthesis.paused) {
      speechSynthesis.resume();
    }
  }, [isSupported]);

  /**
   * Clear the speech queue without stopping current utterance
   */
  const clearQueue = useCallback(() => {
    setState(prev => ({
      ...prev,
      queue: [],
    }));
  }, []);

  // ============================================================================
  // CONFIGURATION FUNCTIONS
  // ============================================================================

  /**
   * Set voice
   */
  const setVoice = useCallback((voice: SpeechSynthesisVoice | null) => {
    setConfig(prev => ({ ...prev, voice }));
    setState(prev => ({ ...prev, currentVoice: voice }));
  }, []);

  /**
   * Set speech rate
   */
  const setRate = useCallback((rate: number) => {
    const clampedRate = Math.max(0.1, Math.min(10, rate));
    setConfig(prev => ({ ...prev, rate: clampedRate }));
  }, []);

  /**
   * Set speech pitch
   */
  const setPitch = useCallback((pitch: number) => {
    const clampedPitch = Math.max(0, Math.min(2, pitch));
    setConfig(prev => ({ ...prev, pitch: clampedPitch }));
  }, []);

  /**
   * Set speech volume
   */
  const setVolume = useCallback((volume: number) => {
    const clampedVolume = Math.max(0, Math.min(1, volume));
    setConfig(prev => ({ ...prev, volume: clampedVolume }));
  }, []);

  /**
   * Update multiple config properties
   */
  const updateConfig = useCallback((newConfig: Partial<AudioFallbackConfig>) => {
    setConfig(prev => ({ ...prev, ...newConfig }));
  }, []);

  // ============================================================================
  // EFFECTS
  // ============================================================================

  /**
   * Load voices on mount and when voices change
   */
  useEffect(() => {
    if (isSupported) {
      loadVoices();
      
      // Listen for voices changed event
      const handleVoicesChanged = () => {
        loadVoices();
      };
      
      speechSynthesis.addEventListener('voiceschanged', handleVoicesChanged);
      
      return () => {
        speechSynthesis.removeEventListener('voiceschanged', handleVoicesChanged);
      };
    }
  }, [loadVoices, isSupported]);

  /**
   * Save config to storage when it changes
   */
  useEffect(() => {
    saveConfigToStorage(config);
  }, [config, saveConfigToStorage]);

  /**
   * Cleanup on unmount
   */
  useEffect(() => {
    return () => {
      stop();
    };
  }, [stop]);

  // ============================================================================
  // RETURN
  // ============================================================================

  return {
    // State
    state,
    config,
    
    // Actions
    speak,
    stop,
    pause,
    resume,
    clearQueue,
    
    // Configuration
    setVoice,
    setRate,
    setPitch,
    setVolume,
    updateConfig,
    
    // Utilities
    getAvailableVoices,
    isSupported,
  };
};

export default useAudioFallback;