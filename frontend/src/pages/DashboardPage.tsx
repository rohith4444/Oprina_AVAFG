/// <reference types="vite/client" />
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Sidebar from '../components/Sidebar';
import HeyGenAvatar, { HeyGenAvatarRef } from '../components/HeyGenAvatar';
import StaticAvatar, { StaticAvatarRef } from '../components/StaticAvatar';
import ConversationDisplay from '../components/ConversationDisplay';
import '../styles/DashboardPage.css';
import QuotaDisplay from '../components/QuotaDisplay';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

// Backend API URL - Update this to match your backend
const BACKEND_API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(75);
  const [isMuted, setIsMuted] = useState(false);
  
  // Check if this was a signup attempt with existing account
  const [showExistingAccountMessage, setShowExistingAccountMessage] = useState(false);
  // Check if this was a login attempt that created a new account
  const [showNewAccountMessage, setShowNewAccountMessage] = useState(false);
  
  // Session management - Updated for API integration
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isCreatingSession, setIsCreatingSession] = useState(false);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  
  // Avatar configuration - Feature flag for static vs streaming
  const [useStaticAvatar, setUseStaticAvatar] = useState(true);
  const [avatarReady, setAvatarReady] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  
  // NEW: HeyGen Session Tracking State
  const [heygenSessionId, setHeygenSessionId] = useState<string | null>(null);
  const [isSessionActive, setIsSessionActive] = useState(false);
  const [sessionStartTime, setSessionStartTime] = useState<Date | null>(null);
  const [sessionError, setSessionError] = useState<string | null>(null);
  const [quotaRefreshTrigger, setQuotaRefreshTrigger] = useState(0);
  
  // Voice recording states
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  const [isAudioPaused, setIsAudioPaused] = useState(false);
  const hasControllableAudio = currentAudio !== null;
  const showAudioControls = useStaticAvatar || hasControllableAudio; // Always show in static mode
  
  // Sidebar collapse state - Default to collapsed on login
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(true);
  
  
  // Refs for both avatar types
  const streamingAvatarRef = useRef<HeyGenAvatarRef>(null);
  const staticAvatarRef = useRef<StaticAvatarRef>(null);

  // Existing state
  const [lastSwitchTime, setLastSwitchTime] = useState(0);
  const [isSwitching, setIsSwitching] = useState(false);
  const [quotaMessage, setQuotaMessage] = useState<string | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);
  const [isCheckingQuota, setIsCheckingQuota] = useState(false);
  const [isSwitchingAvatar, setIsSwitchingAvatar] = useState(false);
  const [operationStatus, setOperationStatus] = useState<string | null>(null);
  const [isEndingSession, setIsEndingSession] = useState(false);
  const [isLockPeriodActive, setIsLockPeriodActive] = useState(false);
  const [lockCountdown, setLockCountdown] = useState(0);
  const lockTimerRef = useRef<NodeJS.Timeout | null>(null);
  
  const navigate = useNavigate();

  // Check for signup attempt with existing account OR login attempt with new account
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const isSignupAttempt = urlParams.get('signup') === 'true';
    const isLoginAttempt = urlParams.get('login') === 'true';
    
    if (user) {
      const accountCreated = new Date(user.created_at).getTime();
      const now = Date.now();
      const timeDiff = now - accountCreated;
      
      if (isSignupAttempt) {
        // Check if this account already existed (account creation date vs current time)
        // If account was created more than 5 minutes ago, it's an existing account
        if (timeDiff > 5 * 60 * 1000) {
          setShowExistingAccountMessage(true);
          
          // Auto-hide message after 8 seconds
          setTimeout(() => setShowExistingAccountMessage(false), 8000);
        }
      } else if (isLoginAttempt) {
        // Check if this was a new account creation (account created within last 5 minutes)
        if (timeDiff <= 5 * 60 * 1000) {
          setShowNewAccountMessage(true);
          
          // Auto-hide message after 8 seconds
          setTimeout(() => setShowNewAccountMessage(false), 8000);
        }
      }
      
      // Clear the parameters from URL
      if (isSignupAttempt || isLoginAttempt) {
        const newUrl = window.location.pathname;
        window.history.replaceState({}, '', newUrl);
      }
    }
  }, [user]);

  // Get user token for API calls
  const getUserToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token;
  };

  // NEW: Generate unique session ID
  const generateSessionId = (): string => {
    return `heygen_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  };

  // NEW: Trigger quota refresh
  const triggerQuotaRefresh = () => {
    setQuotaRefreshTrigger(prev => prev + 1);
    console.log('🔄 Quota refresh triggered');
  };

  // NEW: Start Avatar Session Tracking
  const startAvatarSession = async (sessionId: string): Promise<boolean> => {
    try {
      setSessionError(null);
      
      const token = await getUserToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      console.log('🚀 Starting avatar session tracking:', sessionId);

      const response = await fetch(`${BACKEND_API_URL}/api/v1/avatar/sessions/start`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          heygen_session_id: sessionId,
          avatar_name: "Ann_Therapist_public"
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(errorData.message || `Session start failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Session start failed');
      }

      // Update state
      setHeygenSessionId(sessionId);
      setIsSessionActive(true);
      setSessionStartTime(new Date());
      
      // Trigger quota refresh to show updated remaining time
      triggerQuotaRefresh();
      
      console.log('✅ Avatar session started successfully:', result);
      return true;

    } catch (error) {
      console.error('❌ Failed to start avatar session:', error);
      setSessionError(error instanceof Error ? error.message : 'Session start failed');
      return false;
    }
  };

  // UPDATED: End Avatar Session Tracking with guard
  const endAvatarSession = async (sessionId: string): Promise<boolean> => {
    // Prevent double calls
    if (isEndingSession) {
      console.log('🚫 Session end already in progress, skipping...');
      return true;
    }

    // Check if session is still active
    if (!isSessionActive || heygenSessionId !== sessionId) {
      console.log('🚫 Session not active or ID mismatch, skipping end call');
      return true;
    }

    try {
      setIsEndingSession(true); // Set guard
      setSessionError(null);
      
      const token = await getUserToken();
      if (!token) {
        console.warn('No auth token for ending session');
        return false;
      }

      console.log('🛑 Ending avatar session tracking:', sessionId);

      const response = await fetch(`${BACKEND_API_URL}/api/v1/avatar/sessions/end`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          heygen_session_id: sessionId
        })
      });

      if (!response.ok) {
        // Handle 400 errors gracefully (session already ended)
        if (response.status === 400) {
          console.log('ℹ️ Session already ended (400 status) - this is OK');
          // Clear session state even if API call failed
          setHeygenSessionId(null);
          setIsSessionActive(false);
          setSessionStartTime(null);
          return true;
        }
        
        const errorData = await response.json().catch(() => ({ message: 'Unknown error' }));
        throw new Error(errorData.message || `Session end failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (!result.success) {
        throw new Error(result.message || 'Session end failed');
      }

      // Clear session state
      setHeygenSessionId(null);
      setIsSessionActive(false);
      setSessionStartTime(null);
      
      // Trigger quota refresh to show updated remaining time
      triggerQuotaRefresh();
      
      console.log('✅ Avatar session ended successfully:', result);
      
      // Show quota update message if quota exhausted
      if (result.quota_exhausted) {
        setQuotaMessage('Avatar quota exhausted - switching to static avatar');
      }
      
      return true;

    } catch (error) {
      console.error('❌ Failed to end avatar session:', error);
      setSessionError(error instanceof Error ? error.message : 'Session end failed');
      
      // Even if API call fails, clear local state to prevent stuck state
      setHeygenSessionId(null);
      setIsSessionActive(false);
      setSessionStartTime(null);
      
      return false;
    } finally {
      setIsEndingSession(false); // Clear guard
    }
  };

  // NEW: Handle session errors
  const handleSessionError = (error: string) => {
    console.error('🚨 Session error:', error);
    setSessionError(error);
    setOperationStatus(`Session error: ${error}`);
    
    // Clear error after 5 seconds
    setTimeout(() => {
      setSessionError(null);
      if (operationStatus?.includes('Session error')) {
        setOperationStatus(null);
      }
    }, 5000);
  };

  // UPDATED: Browser cleanup with guard
  useEffect(() => {
    const handleBeforeUnload = async (event: BeforeUnloadEvent) => {
      if (isSessionActive && heygenSessionId && !isEndingSession) {
        console.log('🧹 Page unload - ending active avatar session');
        
        // Use sendBeacon for reliable cleanup on page unload
        const token = await getUserToken();
        if (token) {
          const data = JSON.stringify({
            heygen_session_id: heygenSessionId
          });
          
          const beaconSent = navigator.sendBeacon(
            `${BACKEND_API_URL}/api/v1/avatar/sessions/end`,
            new Blob([data], { type: 'application/json' })
          );
          
          console.log('📡 Beacon sent:', beaconSent);
        }
      }
    };

    window.addEventListener('beforeunload', handleBeforeUnload);
    
    return () => {
      window.removeEventListener('beforeunload', handleBeforeUnload);
      
      // Component unmount cleanup with guard
      if (isSessionActive && heygenSessionId && !isEndingSession) {
        console.log('🧹 Component unmount - ending active avatar session');
        endAvatarSession(heygenSessionId);
      }
    };
  }, [isSessionActive, heygenSessionId, isEndingSession]);

  // Phase 4: Retry logic for failed API calls
  const retryOperation = async (
    operation: () => Promise<any>, 
    maxRetries: number = 3,
    retryDelay: number = 1000
  ): Promise<any> => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        setIsRetrying(attempt > 1);
        setRetryCount(attempt - 1);
        
        const result = await operation();
        
        // Success - clear error states
        setIsRetrying(false);
        setRetryCount(0);
        setLastError(null);
        
        return result;
        
      } catch (error) {
        console.log(`Attempt ${attempt}/${maxRetries} failed:`, error);
        
        if (attempt === maxRetries) {
          // Final attempt failed
          setIsRetrying(false);
          setLastError(`Operation failed after ${maxRetries} attempts`);
          throw error;
        }
        
        // Wait before retry
        await new Promise(resolve => setTimeout(resolve, retryDelay * attempt));
      }
    }
  };

  // Play audio response from base64 content
  const playAudioResponse = async (base64Audio: string) => {
    try {
      // Stop any currently playing audio
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
      }
      
      // Convert base64 to blob
      const audioData = atob(base64Audio);
      const audioArray = new Uint8Array(audioData.length);
      for (let i = 0; i < audioData.length; i++) {
        audioArray[i] = audioData.charCodeAt(i);
      }
      const audioBlob = new Blob([audioArray], { type: 'audio/mp3' });
      
      // Create audio URL and play
      const audioUrl = URL.createObjectURL(audioBlob);
      const audio = new Audio(audioUrl);
      
      // Set volume based on UI control
      audio.volume = isMuted ? 0 : volume / 100;
      
      // Store reference to current audio
      setCurrentAudio(audio);
      
      // Handle avatar speaking states
      audio.onplay = () => {
        console.log('🔊 Audio response started playing');
        setIsSpeaking(true);
        setIsAudioPaused(false); // NEW LINE
      };

      audio.onended = () => {
        console.log('🔇 Audio response finished playing');
        setIsSpeaking(false);
        setIsAudioPaused(false); // NEW LINE
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl); // Clean up
      };
      
      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        setIsSpeaking(false);
        setIsAudioPaused(false); // NEW LINE
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl); // Clean up
      };

      audio.onpause = () => {
        if (currentAudio && currentAudio.currentTime > 0 && !currentAudio.ended) {
          setIsAudioPaused(true);
          console.log('⏸️ Audio paused');
        }
      };
            
      await audio.play();
      
    } catch (error) {
      console.error('Failed to play audio response:', error);
      setIsSpeaking(false);
      setCurrentAudio(null);
    }
  };

  // REPLACE the basic functions with these enhanced versions:

  const pauseAudioResponse = () => {
    try {
      if (currentAudio && !currentAudio.paused) {
        currentAudio.pause();
        setIsAudioPaused(true);
        console.log('⏸️ Audio paused');
      }
    } catch (error) {
      console.error('Error pausing audio:', error);
      setIsAudioPaused(false);
    }
  };

  const resumeAudioResponse = () => {
    try {
      if (currentAudio && currentAudio.paused) {
        currentAudio.play();
        setIsAudioPaused(false);
        console.log('▶️ Audio resumed');
      }
    } catch (error) {
      console.error('Error resuming audio:', error);
      setIsAudioPaused(false);
    }
  };

  const stopAudioResponse = () => {
    try {
      if (currentAudio) {
        currentAudio.pause();
        currentAudio.currentTime = 0;
        setIsSpeaking(false);
        setIsAudioPaused(false);
        setCurrentAudio(null);
        console.log('⏹️ Audio stopped');
      }
    } catch (error) {
      console.error('Error stopping audio:', error);
      // Still reset states even if error occurs
      setIsSpeaking(false);
      setIsAudioPaused(false);
      setCurrentAudio(null);
    }
  };

  const toggleAudioPause = () => {
    if (isAudioPaused) {
      resumeAudioResponse();
    } else {
      pauseAudioResponse();
    }
  };

  // API Methods
  // MODIFY the existing createNewSession function:
  const createNewSession = async () => {
    if (isCreatingSession) return;

    try {
      setIsCreatingSession(true);
      const token = await getUserToken();
      
      const response = await fetch(`${BACKEND_API_URL}/api/v1/sessions/create`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: "New Chat" // Backend will auto-update this when first message is sent
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }
      
      const newSession = await response.json();
      // Map backend response to frontend format
      const sessionForFrontend = {
        id: newSession.session_id,
        title: newSession.title, // Will be "New Chat" initially, then auto-updated
        created_at: newSession.created_at,
        updated_at: newSession.created_at,
        message_count: 0
      };

      setSessions(prev => [sessionForFrontend, ...(prev || [])]);
      setActiveSessionId(newSession.session_id);
      setMessages([]);
      
      console.log('💬 New session created:', newSession.session_id);
      return newSession;
    } catch (error) {
      console.error('Error creating session:', error);
      return null;
    } finally {
      setIsCreatingSession(false);
    }
  };

  const loadSessions = async () => {
    try {
      const token = await getUserToken();
      
      const response = await fetch(`${BACKEND_API_URL}/api/v1/sessions/list`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
          const data = await response.json();
          // Map backend format to frontend format
          const mappedSessions = data.sessions.map((session: any) =>({
            id: session.session_id,                    // Map session_id to id
            title: session.title,
            created_at: session.created_at,
            updated_at: session.last_activity_at,     // Map last_activity_at to updated_at
            message_count: session.message_count
          }));
          setSessions(mappedSessions);
        console.log('📋 Loaded sessions:', mappedSessions.length);
      }
    } catch (error) {
      console.error('Error loading sessions:', error);
    }
  };

  const loadSessionMessages = async (sessionId: string) => {
    try {
      setIsLoadingMessages(true);
      const token = await getUserToken();
      
      const response = await fetch(`${BACKEND_API_URL}/api/v1/sessions/${sessionId}/messages`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        const data = await response.json();
        
        // Transform backend format to frontend format
        const transformedMessages = data.messages.map((msg: any) => ({
          id: msg.id,
          sender: msg.role === 'user' ? 'user' : 'assistant',  // role → sender
          text: msg.content,                                   // content → text
          timestamp: new Date(msg.created_at)                  // created_at string → Date object
        }));
        
        setMessages(transformedMessages);
        console.log('📋 Loaded and transformed messages:', transformedMessages.length);
      }
    } catch (error) {
      console.error('Error loading messages:', error);
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const deleteSession = async (sessionId: string) => {
    try {
      const token = await getUserToken();
      
      const response = await fetch(`${BACKEND_API_URL}/api/v1/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });

      if (response.ok) {
        setSessions(prev => prev.filter(s => s.id !== sessionId));
        
        // If deleting active session, clear it
        if (activeSessionId === sessionId) {
          setActiveSessionId(null);
          setMessages([]);
        }
        
        console.log('🗑️ Session deleted:', sessionId);
      }
    } catch (error) {
      console.error('Error deleting session:', error);
    }
  };

  const handleSessionUpdate = (sessionId: string, newTitle: string) => {
    setSessions(prev => prev.map((s: Session) => 
      s.id === sessionId 
        ? { ...s, title: newTitle }
        : s
    ));
    console.log(`📝 Updated session ${sessionId} title to: ${newTitle}`);
  };

  // Load sessions on component mount
  useEffect(() => {
    loadSessions();
  }, []);

  // Load messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      loadSessionMessages(activeSessionId);
    } else {
      setMessages([]);
    }
  }, [activeSessionId]);

  // Process audio when chunks are available
  useEffect(() => {
    if (audioChunks.length > 0 && !isRecording) {
      processRecordedAudio(audioChunks);
    }
  }, [audioChunks, isRecording]);
 
  // Cleanup audio resources on unmount
  useEffect(() => {
    return () => {
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
      }
      if (currentAudio) {
        currentAudio.pause();
        setIsAudioPaused(false); // NEW LINE
      }
    };
  }, [audioStream, currentAudio]);

  // Auto-clear quota message after 5 seconds
  useEffect(() => {
    if (quotaMessage) {
      const timer = setTimeout(() => {
        setQuotaMessage(null);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [quotaMessage]);

  useEffect(() => {
    return () => {
      if (lockTimerRef.current) {
        clearInterval(lockTimerRef.current);
      }
    };
  }, []);

  // Update audio volume when volume control changes
  useEffect(() => {
    if (currentAudio) {
      currentAudio.volume = isMuted ? 0 : volume / 100;
    }
  }, [volume, isMuted, currentAudio]);

  // Avatar event handlers
  const handleAvatarReady = useCallback(() => {
    console.log('✅ Avatar ready');
    setAvatarReady(true);
    setAvatarError(null);
  }, []);

  const handleAvatarError = useCallback((error: string) => {
    console.error('❌ Avatar error:', error);
    setAvatarError(error);
    setAvatarReady(false);
  }, []);

  // Updated avatar speaking handlers with voice activity tracking
  const handleAvatarStartTalking = useCallback(() => {
    console.log('🗣️ Avatar started talking');
    setIsSpeaking(true);
  }, []);

  const handleAvatarStopTalking = useCallback(() => {
    console.log('🤐 Avatar stopped talking');
    setIsSpeaking(false);
 
  }, []);

  // Audio Recording Functions
  const startAudioRecording = async () => {
    try {
      setRecordingError(null);
      
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      setAudioStream(stream);
      
      // Create MediaRecorder with WebM format (preferred by backend)
      const recorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      const chunks: Blob[] = [];
      
      recorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunks.push(event.data);
        }
      };
      
      recorder.onstop = () => {
        setAudioChunks(chunks);
        // Stop all tracks to free up microphone
        stream.getTracks().forEach(track => track.stop());
        setAudioStream(null);
      };
      
      recorder.onerror = (event) => {
        console.error('Recording error:', event);
        setRecordingError('Recording failed. Please try again.');
        setIsRecording(false);
      };
      
      setMediaRecorder(recorder);
      setAudioChunks([]);
      
      // Start recording
      recorder.start();
      setIsRecording(true);
      
      console.log('🎙️ Audio recording started');
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      setRecordingError('Microphone access denied. Please allow microphone access.');
      setIsRecording(false);
    }
  };

  const stopAudioRecording = async () => {
    if (!mediaRecorder || mediaRecorder.state === 'inactive') {
      return;
    }
    
    try {
      setIsRecording(false);
      
      // Stop recording
      mediaRecorder.stop();
      
      console.log('🛑 Audio recording stopped');
      
      // Processing will happen when recorder.onstop fires
      
    } catch (error) {
      console.error('Failed to stop recording:', error);
      setRecordingError('Failed to stop recording');
    }
  };

  // Send voice message to API
  const sendVoiceMessage = async (audioBlob: Blob, sessionId: string) => {
    try {
      const token = await getUserToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      // Create FormData for multipart upload
      const formData = new FormData();
      formData.append('session_id', sessionId);
      formData.append('audio_format', 'webm');
      formData.append('include_audio_response', 'true');
      formData.append('audio_file', audioBlob, 'recording.webm');

      console.log('📤 Sending voice message to API...');

      const response = await fetch(`${BACKEND_API_URL}/api/v1/voice/message`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.text();
        
        // Handle specific "No speech detected" case
        if (response.status === 422 && errorData.includes('NO_SPEECH_DETECTED')) {
          throw new Error("I had a hard time hearing you, can you try again?");
        }
        
        // Handle other API errors
        throw new Error(`API Error: ${response.status} - ${errorData}`);
      }

      const result = await response.json();
      console.log('📨 Voice API response:', result);

      if (!result.success) {
        throw new Error(result.error || 'Voice processing failed');
      }

      return result;

    } catch (error) {
      console.error('Voice API error:', error);
      throw error;
    }
  };

  // Process recorded audio and send to API
  const processRecordedAudio = async (chunks: Blob[]) => {
    if (chunks.length === 0) {
      console.warn('No audio chunks to process');
      return;
    }
    
    if (!activeSessionId) {
      console.error('No active session for voice message');
      setRecordingError('No active session. Please start a new conversation.');
      return;
    }
    
    try {
      setIsProcessingVoice(true);
      setRecordingError(null);
      
      // Create audio blob
      const audioBlob = new Blob(chunks, { type: 'audio/webm' });
      
      // Validate audio size (must be > 0 and < 10MB)
      if (audioBlob.size === 0) {
        throw new Error('Recording is empty');
      }
      
      if (audioBlob.size > 10 * 1024 * 1024) {
        throw new Error('Recording too large (max 10MB)');
      }
      
      console.log('🎵 Processing audio blob:', audioBlob.size, 'bytes');
      
      // Send to voice API
      const apiResponse = await sendVoiceMessage(audioBlob, activeSessionId);
      
      // Add user message (transcription) to conversation
      const userMessage: Message = {
        id: apiResponse.chat_response.message_id + '_user' || Date.now().toString() + '_user',
        sender: 'user',
        text: apiResponse.transcription.text,
        timestamp: new Date(),
      };
      
      // Add assistant response to conversation
      const assistantMessage: Message = {
        id: apiResponse.chat_response.message_id || Date.now().toString() + '_assistant',
        sender: 'assistant',
        text: apiResponse.chat_response.text,
        timestamp: new Date(),
      };
      
      // Update messages in UI
      setMessages(prev => [...prev, userMessage, assistantMessage]);
      
      // Handle audio response if provided
      // Handle audio response based on avatar mode
      if (apiResponse.audio_response && !isMuted) {
        if (useStaticAvatar) {
          // Static mode: Play background audio as before
          console.log('🔊 Playing background audio (Static mode)...');
          await playAudioResponse(apiResponse.audio_response.audio_content);
        } else {
          // Streaming mode: Make avatar speak the text instead
          console.log('🗣️ Making avatar speak (Streaming mode)...');
          if (streamingAvatarRef.current && avatarReady) {
            try {
              await streamingAvatarRef.current.speak(apiResponse.chat_response.text);
              console.log('✅ Avatar speech initiated');
            } catch (speakError) {
              console.error('❌ Avatar speak failed, falling back to background audio:', speakError);
              // Fallback to background audio if avatar speak fails
              await playAudioResponse(apiResponse.audio_response.audio_content);
            }
          } else {
            console.warn('⚠️ Avatar not ready, playing background audio as fallback');
            // Fallback to background audio if avatar not ready
            await playAudioResponse(apiResponse.audio_response.audio_content);
          }
        }
      }
      
      // Clear chunks
      setAudioChunks([]);
      
      console.log('✅ Voice message processed successfully');
      
    } catch (error) {
      console.error('Voice processing error:', error);
      setRecordingError(error instanceof Error ? error.message : 'Voice processing failed');
    } finally {
      setIsProcessingVoice(false);
    }
  };

  // Updated voice interaction handlers with activity tracking
  const handleStartListening = useCallback(async () => {
    // Auto-create session when user starts talking if none exists
    if (!activeSessionId && !isCreatingSession) {
      console.log('🎙️ Auto-creating session for voice interaction');
      await createNewSession();
    }
    
    setIsListening(true);
    await startAudioRecording();
  }, [activeSessionId, isCreatingSession]);

  const handleStopListening = useCallback(async () => {
    setIsListening(false);
    await stopAudioRecording();
  }, [mediaRecorder]);

  // Session management handlers
  const handleNewChat = useCallback(async () => {
    await createNewSession();
  }, []);

  const handleSelectSession = useCallback((sessionId: string) => {

    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
    }
    setIsAudioPaused(false);
    setIsSpeaking(false);

    setActiveSessionId(sessionId);
    console.log('💬 Session selected:', sessionId);
  }, []);

  const handleDeleteSession = useCallback(async (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      await deleteSession(sessionId);
    }
  }, []);

  // Updated quota check with retry logic
  const checkQuotaBeforeSwitch = async (): Promise<boolean> => {
    try {
      const result = await retryOperation(async () => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        
        if (!token) {
          throw new Error('No auth token available');
        }

        const response = await fetch(`${BACKEND_API_URL}/api/v1/avatar/check-quota`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          throw new Error(`Quota check failed: ${response.status}`);
        }

        return await response.json();
      });

      return result.success && result.can_create_session;
      
    } catch (error) {
      console.error('Error checking quota after retries:', error);
      setQuotaMessage('Unable to check quota - please check your connection and try again');
      return false;
    }
  };

  const startLockPeriod = () => {
    setIsLockPeriodActive(true);
    setLockCountdown(10);
    
    const countdownInterval = setInterval(() => {
      setLockCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownInterval);
          setIsLockPeriodActive(false);
          setLockCountdown(0);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
    
    lockTimerRef.current = countdownInterval;
  };

  // UPDATED: Avatar mode toggle with complete session lifecycle
  const toggleAvatarMode = async () => {

    if (currentAudio) {
      currentAudio.pause();
      setCurrentAudio(null);
    }
    setIsAudioPaused(false);
    setIsSpeaking(false);
    // Clear any previous messages
    setQuotaMessage(null);
    setLastError(null);
    setOperationStatus(null);
    setSessionError(null);
    
    try {
      setIsSwitchingAvatar(true);
      
      // If switching FROM static TO streaming, check quota and start session
      if (useStaticAvatar) {
        setOperationStatus('Checking quota...');
        setIsCheckingQuota(true);
        
        console.log('🔍 Checking quota before switching to streaming...');
        
        const canCreateSession = await checkQuotaBeforeSwitch();
        
        setIsCheckingQuota(false);
        
        if (!canCreateSession) {
          // Quota exhausted - prevent switch and show message
          setQuotaMessage('Cannot switch to streaming avatar - quota exhausted. Please wait for quota to reset.');
          console.warn('🚫 Switch to streaming blocked - quota exhausted');
          return; // Don't switch
        }
        
        setOperationStatus('Quota check passed - starting session tracking...');
        console.log('✅ Quota check passed - starting session tracking');
        
        // Generate new session ID and start tracking
        const newSessionId = generateSessionId();
        const sessionStarted = await startAvatarSession(newSessionId);
        
        if (!sessionStarted) {
          setQuotaMessage('Failed to start session tracking - please try again');
          console.error('❌ Session tracking failed');
          return; // Don't switch if session tracking fails
        }
        
        setOperationStatus('Session tracking started - switching to streaming...');
        
      } else {
        // Switching FROM streaming TO static - end session first
        setOperationStatus('Ending session tracking...');
        
        if (isSessionActive && heygenSessionId) {
          console.log('🛑 Ending session before switching to static');
          await endAvatarSession(heygenSessionId);
        }
        
        setOperationStatus('Session ended - switching to static avatar...');
      }
      
      // Proceed with the UI switch
      setUseStaticAvatar(!useStaticAvatar);
      setAvatarReady(false);
      setAvatarError(null);
      
      setOperationStatus('Avatar switch completed');
      console.log('🔄 Switched to', !useStaticAvatar ? 'static' : 'streaming', 'avatar');
      
      // Clear status after 2 seconds
      setTimeout(() => {
        setOperationStatus(null);
      }, 2000);
      
    } catch (error) {
      console.error('Error during avatar switch:', error);
      setQuotaMessage('Error switching avatar - please try again');
      setLastError('Avatar switch failed');
      handleSessionError('Avatar switch failed');
    } finally {
      setIsSwitchingAvatar(false);
      setIsCheckingQuota(false);
      
      // Start 10-second lock period
      startLockPeriod();
    }
  };

  // Add message with voice activity tracking
  const addMessage = useCallback((sender: 'user' | 'assistant', text: string) => {
    if (!activeSessionId) return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      sender,
      text,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, newMessage]);

    console.log('💬 Message added:', sender, text);
  }, [activeSessionId]);

  return (
    <div className={`dashboard-page min-h-screen flex flex-col ${isSidebarCollapsed ? 'sidebar-collapsed' : ''}`}>
      <div className="flex flex-1">
        {/* Sidebar */}
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={handleNewChat}
          onSessionSelect={handleSelectSession}
          onSessionDelete={handleDeleteSession}
          onSessionUpdate={handleSessionUpdate}
          onCollapseChange={setIsSidebarCollapsed}
        />
        
        {/* Main Content Area - 50/50 Layout */}
        <div className="main-content flex-1">
          {/* Existing Account Message */}
          {showExistingAccountMessage && (
            <div style={{
              backgroundColor: '#fef3c7',
              border: '1px solid #f59e0b',
              borderRadius: '8px',
              padding: '12px 16px',
              margin: '16px',
              color: '#92400e',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>⚠️</span>
              <span>Account with {user?.email} already exists. You have been logged in instead.</span>
              <button
                onClick={() => setShowExistingAccountMessage(false)}
                style={{
                  marginLeft: 'auto',
                  background: 'none',
                  border: 'none',
                  color: '#92400e',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: '0 4px'
                }}
                aria-label="Dismiss"
              >
                ×
              </button>
            </div>
          )}

          {/* New Account Created During Login Message */}
          {showNewAccountMessage && (
            <div style={{
              backgroundColor: '#dbeafe',
              border: '1px solid #3b82f6',
              borderRadius: '8px',
              padding: '12px 16px',
              margin: '16px',
              color: '#1d4ed8',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span>ℹ️</span>
              <span>No account found for {user?.email}. A new account has been created for you.</span>
              <button
                onClick={() => setShowNewAccountMessage(false)}
                style={{
                  marginLeft: 'auto',
                  background: 'none',
                  border: 'none',
                  color: '#1d4ed8',
                  cursor: 'pointer',
                  fontSize: '16px',
                  padding: '0 4px'
                }}
                aria-label="Dismiss"
              >
                ×
              </button>
            </div>
          )}
          
          <div className="dashboard-unified">
            
            {/* NEW: Horizontal Status Box - Above everything, full width */}
            {(quotaMessage || operationStatus || lastError || sessionError || (!useStaticAvatar) || isRetrying || isLockPeriodActive) && (
              <div className="avatar-status-box">
                <div className="status-content">
                  {/* Streaming Avatar indicator */}
                  {!useStaticAvatar && (
                    <span className="status-item streaming">
                      📡 <strong>Streaming Avatar</strong>
                    </span>
                  )}
                  
                  {/* Quota information (moved from right-section) */}
                  {!useStaticAvatar && (
                    <span className="status-item quota">
                      <QuotaDisplay 
                        isVisible={true} 
                        refreshTrigger={quotaRefreshTrigger}
                        isSessionActive={isSessionActive}
                        sessionStartTime={sessionStartTime}
                      />
                    </span>
                  )}
                  
                  {/* Connection status - only show when actually connecting */}
                    {!useStaticAvatar && !avatarReady && (
                      <span className="status-item connection">
                        🔄 Connecting...
                      </span>
                    )}
                  
                  {/* Operation Status (green messages) */}
                  {operationStatus && (
                    <span className="status-item success">
                      ✅ {operationStatus}
                    </span>
                  )}
                  
                  {/* Lock messages and warnings (yellow messages) */}
                  {quotaMessage && (
                    <span className="status-item warning">
                      ⚠️ {quotaMessage}
                    </span>
                  )}
                  
                  {/* Lock period countdown */}
                  {isLockPeriodActive && (
                    <span className="status-item warning">
                      🔒 Switch locked for {lockCountdown} seconds to prevent API errors
                    </span>
                  )}
                  
                  {/* Error Messages (red messages) */}
                  {lastError && (
                    <span className="status-item error">
                      ❌ {lastError}
                    </span>
                  )}
                  
                  {/* Session Error Messages */}
                  {sessionError && (
                    <span className="status-item error">
                      🚫 Session Error: {sessionError}
                    </span>
                  )}
                  
                  {/* Retry Status */}
                  {isRetrying && (
                    <span className="status-item info">
                      🔄 Retrying... (Attempt {retryCount + 1})
                    </span>
                  )}
                </div>
              </div>
            )}
            
            {/* Wrap the existing avatar + conversation layout */}
            <div className="dashboard-content-area">
              {/* Left Side: Avatar + Controls (50%) */}
              <div className="avatar-section">
                {/* Enhanced Avatar Mode Toggle with Session Status - KEPT EXACTLY THE SAME */}
                {import.meta.env.VITE_SHOW_AVATAR_TOGGLE === 'true' && (
                  <div className="avatar-mode-toggle">
                    <div className="left-section">
                      <button 
                        className="mode-status-box"
                        onClick={toggleAvatarMode}
                        disabled={isSwitchingAvatar || isCheckingQuota || isLockPeriodActive}
                        style={{
                          backgroundColor: useStaticAvatar ? '#4FD1C5' : '#5B7CFF',
                          opacity: (isSwitchingAvatar || isCheckingQuota) ? 0.6 : 1
                        }}
                      >
                        {isSwitchingAvatar ? (
                          '🔄 Switching...'
                        ) : isCheckingQuota ? (
                          '🔍 Checking Quota...'
                        ) : isLockPeriodActive ? (
                          `🔒 Wait ${lockCountdown}s`
                        ) : (
                          useStaticAvatar ? 'Switch to Streaming' : 'Switch to Static'
                        )}
                      </button>
                      <span className="mode-label">
                        {useStaticAvatar ? 'Static Avatar' : 'Streaming Avatar'}
                        {isSessionActive && (
                          <span style={{ color: '#10b981', fontSize: '10px', marginLeft: '5px' }}>
                            (Session Active)
                          </span>
                        )}
                      </span>
                    </div>
                    
                    <div className="right-section">
                      {/* QuotaDisplay moved to status box above - keeping empty for layout */}
                    </div>
                  </div>
                )}

                {/* Avatar Container - Conditional Rendering */}
                <div className="avatar-container-wrapper">
                  {useStaticAvatar ? (
                    <StaticAvatar
                      ref={staticAvatarRef}
                      isListening={isListening}
                      isSpeaking={isSpeaking}
                      onAvatarReady={handleAvatarReady}
                      onAvatarStartTalking={handleAvatarStartTalking}
                      onAvatarStopTalking={handleAvatarStopTalking}
                    />
                  ) : (
                    <HeyGenAvatar
                      ref={streamingAvatarRef}
                      isListening={isListening}
                      isSpeaking={isSpeaking}
                      onAvatarReady={handleAvatarReady}
                      onAvatarError={handleAvatarError}
                    />
                  )}
                </div>

                {/* Voice Controls */}
                <div className="compact-voice-controls">
                  <button
                    className={`voice-button mic-button ${isListening ? 'listening' : ''}`}
                    onClick={isListening ? handleStopListening : handleStartListening}
                    disabled={!avatarReady || isCreatingSession || isProcessingVoice}
                  >
                    {isRecording ? '🔴' : '🎙️'}
                  </button>
                  
                  <div className="volume-control">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={volume}
                      onChange={(e) => setVolume(Number(e.target.value))}
                    />
                    <span>{volume}%</span>
                  </div>
                  
                  <button
                    className="mute-button"
                    onClick={() => setIsMuted(!isMuted)}
                  >
                    {isMuted ? '🔇' : '🔊'}
                  </button>

                  {/* Audio Control Buttons */}
                  {showAudioControls && (
                    <>
                      <button
                        className="audio-control-button pause-button"
                        onClick={toggleAudioPause}
                        disabled={!currentAudio || !isSpeaking}
                        aria-label={isAudioPaused ? 'Resume audio' : 'Pause audio'}
                      >
                        {isAudioPaused ? '▶️' : '⏸️'}
                      </button>
                      
                      <button
                        className="audio-control-button stop-button"
                        onClick={stopAudioResponse}
                        disabled={!currentAudio || !isSpeaking}
                        aria-label="Stop audio"
                      >
                        ⏹️
                      </button>
                    </>
                  )}
                </div>

                {/* Recording Feedback */}
                {(isRecording || isProcessingVoice || recordingError) && (
                  <div style={{ textAlign: 'center', marginTop: '1rem', fontSize: '0.875rem' }}>
                    {isRecording && (
                      <div style={{ color: '#ef4444' }}>🔴 Recording...</div>
                    )}
                    {isProcessingVoice && (
                      <div style={{ color: '#3b82f6' }}>⚡ Processing with AI...</div>
                    )}
                    {recordingError && (
                      <div style={{ color: '#ef4444' }}>❌ {recordingError}</div>
                    )}
                  </div>
                )}
              </div>

              {/* Right Side: Conversation Display (50%) */}
              <div className="conversation-section">
                <ConversationDisplay 
                  messages={messages}
                  activeSessionId={activeSessionId}
                  isLoading={isLoadingMessages}
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;