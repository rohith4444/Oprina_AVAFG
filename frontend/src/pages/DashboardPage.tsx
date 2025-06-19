// src/pages/DashboardPage.tsx - Updated with Phase 4 Voice-Only Activity Tracking
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';
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
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(75);
  const [isMuted, setIsMuted] = useState(false);
  
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
  
  // NEW: Voice recording states
  const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingVoice, setIsProcessingVoice] = useState(false);
  const [audioChunks, setAudioChunks] = useState<Blob[]>([]);
  const [recordingError, setRecordingError] = useState<string | null>(null);
  const [audioStream, setAudioStream] = useState<MediaStream | null>(null);
  const [currentAudio, setCurrentAudio] = useState<HTMLAudioElement | null>(null);
  
  // Refs for both avatar types
  const streamingAvatarRef = useRef<HeyGenAvatarRef>(null);
  const staticAvatarRef = useRef<StaticAvatarRef>(null);

  // Add this state at the top with other states
  const [lastSwitchTime, setLastSwitchTime] = useState(0);
  const [isSwitching, setIsSwitching] = useState(false);

  // Phase 3: Quota feedback
  const [quotaMessage, setQuotaMessage] = useState<string | null>(null);

  // Phase 4: Idle timeout management (VOICE-ONLY)
  const [idleTimer, setIdleTimer] = useState<NodeJS.Timeout | null>(null);
  const [lastActivity, setLastActivity] = useState<Date>(new Date());
  const [isIdleTimeoutActive, setIsIdleTimeoutActive] = useState(false);

  // Phase 4: Enhanced error handling
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastError, setLastError] = useState<string | null>(null);

  // Phase 4: Loading states
  const [isCheckingQuota, setIsCheckingQuota] = useState(false);
  const [isSwitchingAvatar, setIsSwitchingAvatar] = useState(false);
  const [operationStatus, setOperationStatus] = useState<string | null>(null);
  
  const navigate = useNavigate();

  // Get user token for API calls
  const getUserToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token;
  };

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

  // Phase 4: Reset idle timer on VOICE activity only
  const resetIdleTimer = useCallback(() => {
    setLastActivity(new Date());
    
    // Only track idle time when using streaming avatar
    if (!useStaticAvatar) {
      // Clear existing timer
      if (idleTimer) {
        clearTimeout(idleTimer);
      }
      
      // Set new 25-second timer
      const newTimer = setTimeout(() => {
        console.log('🕒 25-second voice idle timeout - switching to static avatar');
        handleIdleTimeout();
      }, 25000); // 25 seconds
      
      setIdleTimer(newTimer);
      setIsIdleTimeoutActive(true);
      console.log('🔄 Voice activity detected - idle timer reset');
    }
  }, [useStaticAvatar, idleTimer]);

  // Phase 4: Handle idle timeout
  const handleIdleTimeout = useCallback(async () => {
    if (!useStaticAvatar) {
      console.log('🔄 Auto-switching to static avatar due to inactivity');
      
      // Switch to static avatar
      setUseStaticAvatar(true);
      setAvatarReady(false);
      setAvatarError(null);
      
      // Show user feedback
      setQuotaMessage('Switched to static avatar due to 25 seconds of voice inactivity');
      
      // Clear timer
      setIdleTimer(null);
      setIsIdleTimeoutActive(false);
    }
  }, [useStaticAvatar]);

  // NEW: Play audio response from base64 content
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
      };
      
      audio.onended = () => {
        console.log('🔇 Audio response finished playing');
        setIsSpeaking(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl); // Clean up
      };
      
      audio.onerror = (error) => {
        console.error('Audio playback error:', error);
        setIsSpeaking(false);
        setCurrentAudio(null);
        URL.revokeObjectURL(audioUrl); // Clean up
      };
      
      await audio.play();
      
    } catch (error) {
      console.error('Failed to play audio response:', error);
      setIsSpeaking(false);
      setCurrentAudio(null);
    }
  };

  // API Methods
  const createNewSession = async () => {
    if (isCreatingSession) return null;
    
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
          title: "New Conversation",
          avatar_settings: { type: "static" }
        })
      });

      if (!response.ok) {
        throw new Error('Failed to create session');
      }
      
      const newSession = await response.json();
      // Map backend response to frontend format
      const sessionForFrontend = {
        id: newSession.session_id,  // Map session_id to id
        title: newSession.title,
        created_at: newSession.created_at,
        updated_at: newSession.created_at,  // Use created_at as initial updated_at
        message_count: 0
      };

      setSessions(prev => [sessionForFrontend, ...(prev || [])]);  // Handle prev being null
      setActiveSessionId(newSession.session_id);  // Use session_id
      setMessages([]);
      
      console.log('💬 New session created:', newSession.id);
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
          const mappedSessions = data.sessions.map(session => ({
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
        const transformedMessages = data.messages.map(msg => ({
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

  // NEW: Process audio when chunks are available
  useEffect(() => {
    if (audioChunks.length > 0 && !isRecording) {
      processRecordedAudio(audioChunks);
    }
  }, [audioChunks, isRecording]);

  // NEW: Cleanup audio resources on unmount
  useEffect(() => {
    return () => {
      if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
      }
      if (currentAudio) {
        currentAudio.pause();
      }
    };
  }, [audioStream, currentAudio]);

  // Phase 3: Auto-clear quota message after 5 seconds
  useEffect(() => {
    if (quotaMessage) {
      const timer = setTimeout(() => {
        setQuotaMessage(null);
      }, 5000);
      
      return () => clearTimeout(timer);
    }
  }, [quotaMessage]);

  // Phase 4: Voice-only activity tracking (no mouse/keyboard)
  useEffect(() => {
    if (!useStaticAvatar && avatarReady) {
      // Start idle timer when streaming avatar becomes ready
      resetIdleTimer();
      
      return () => {
        // Cleanup timer when switching away from streaming
        if (idleTimer) {
          clearTimeout(idleTimer);
          console.log('🧹 Idle timer cleared - no longer using streaming avatar');
        }
      };
    } else {
      // Clear timer when not using streaming avatar
      if (idleTimer) {
        clearTimeout(idleTimer);
        setIdleTimer(null);
        setIsIdleTimeoutActive(false);
      }
    }
  }, [useStaticAvatar, avatarReady, resetIdleTimer, idleTimer]);

  // NEW: Update audio volume when volume control changes
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

  // Phase 4: Updated avatar speaking handlers with voice activity tracking
  const handleAvatarStartTalking = useCallback(() => {
    console.log('🗣️ Avatar started talking');
    setIsSpeaking(true);
    
    // Reset idle timer when avatar starts speaking
    resetIdleTimer();
    console.log('🗣️ Avatar started speaking - idle timer reset');
  }, [resetIdleTimer]);

  const handleAvatarStopTalking = useCallback(() => {
    console.log('🤐 Avatar stopped talking');
    setIsSpeaking(false);
    
    // Reset idle timer when avatar stops speaking
    resetIdleTimer();
    console.log('🗣️ Avatar stopped speaking - idle timer reset');
  }, [resetIdleTimer]);

  // NEW: Audio Recording Functions
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

  // NEW: Send voice message to API
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

  // NEW: Process recorded audio and send to API
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
      if (apiResponse.audio_response && !isMuted) {
        console.log('🔊 Playing audio response...');
        await playAudioResponse(apiResponse.audio_response.audio_content);
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

  // Phase 4: Updated voice interaction handlers with activity tracking
  const handleStartListening = useCallback(async () => {
    // Auto-create session when user starts talking if none exists
    if (!activeSessionId && !isCreatingSession) {
      console.log('🎙️ Auto-creating session for voice interaction');
      await createNewSession();
    }
    
    setIsListening(true);
    await startAudioRecording();
    
    // Reset idle timer on voice input START
    resetIdleTimer();
    console.log('🎙️ Voice input started - idle timer reset');
  }, [activeSessionId, isCreatingSession, resetIdleTimer]);

  const handleStopListening = useCallback(async () => {
    setIsListening(false);
    await stopAudioRecording();
    
    // Reset idle timer on voice input END
    resetIdleTimer();
    console.log('🎙️ Voice input ended - idle timer reset');
  }, [mediaRecorder, resetIdleTimer]);

  // Session management handlers
  const handleNewChat = useCallback(async () => {
    await createNewSession();
  }, []);

  const handleSelectSession = useCallback((sessionId: string) => {
    setActiveSessionId(sessionId);
    console.log('💬 Session selected:', sessionId);
  }, []);

  const handleDeleteSession = useCallback(async (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      await deleteSession(sessionId);
    }
  }, []);

  // Phase 4: Updated quota check with retry logic
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

  // Phase 4: Updated avatar mode toggle with enhanced UX
  const toggleAvatarMode = async () => {
    // Clear any previous messages
    setQuotaMessage(null);
    setLastError(null);
    setOperationStatus(null);
    
    try {
      setIsSwitchingAvatar(true);
      
      // If switching FROM static TO streaming, check quota first
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
        
        setOperationStatus('Quota check passed - initializing streaming avatar...');
        console.log('✅ Quota check passed - switching to streaming');
      } else {
        setOperationStatus('Switching to static avatar...');
      }
      
      // Proceed with the switch
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
    } finally {
      setIsSwitchingAvatar(false);
      setIsCheckingQuota(false);
    }
  };

  // Phase 4: Add message with voice activity tracking
  const addMessage = useCallback((sender: 'user' | 'assistant', text: string) => {
    if (!activeSessionId) return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      sender,
      text,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // Reset idle timer on text message activity
    if (sender === 'user') {
      resetIdleTimer();
      console.log('💬 User text message sent - idle timer reset');
    }
    
    console.log('💬 Message added:', sender, text);
  }, [activeSessionId, resetIdleTimer]);

  return (
    <div className="dashboard-page min-h-screen flex flex-col">
      <div className="flex flex-1">
        {/* Sidebar */}
        <Sidebar
          sessions={sessions}
          activeSessionId={activeSessionId}
          onNewChat={handleNewChat}
          onSessionSelect={handleSelectSession}
          onSessionDelete={handleDeleteSession}
        />
        
        {/* Main Content Area - 50/50 Layout */}
        <div className="main-content flex-1">
          <div className="dashboard-unified">
            
            {/* Left Side: Avatar + Controls (50%) */}
            <div className="avatar-section">
              {/* Phase 4: Enhanced Avatar Mode Toggle with Loading States */}
              {process.env.NODE_ENV === 'development' && (
                <div className="avatar-mode-toggle">
                  <div className="left-section">
                    <button 
                      className="mode-status-box"
                      onClick={toggleAvatarMode}
                      disabled={isSwitchingAvatar || isCheckingQuota}
                      style={{
                        backgroundColor: useStaticAvatar ? '#4FD1C5' : '#5B7CFF',
                        opacity: (isSwitchingAvatar || isCheckingQuota) ? 0.6 : 1
                      }}
                    >
                      {isSwitchingAvatar ? (
                        '🔄 Switching...'
                      ) : isCheckingQuota ? (
                        '🔍 Checking Quota...'
                      ) : (
                        useStaticAvatar ? 'Switch to Streaming' : 'Switch to Static'
                      )}
                    </button>
                    <span className="mode-label">
                      {useStaticAvatar ? 'Static Avatar' : 'Streaming Avatar'}
                      {isIdleTimeoutActive && !useStaticAvatar && (
                        <span style={{ color: '#f59e0b', fontSize: '10px', marginLeft: '5px' }}>
                          (Auto-switch after 25s without voice activity)
                        </span>
                      )}
                    </span>
                  </div>
                  
                  <div className="right-section">
                    <QuotaDisplay isVisible={!useStaticAvatar} />
                    {isRetrying && (
                      <span style={{ color: '#f59e0b', fontSize: '10px' }}>
                        Retrying... (Attempt {retryCount + 1})
                      </span>
                    )}
                  </div>
                  
                  {/* Enhanced feedback messages */}
                  {quotaMessage && (
                    <div className="quota-message" style={{ 
                      color: '#ef4444', 
                      fontSize: '12px', 
                      marginTop: '4px',
                      textAlign: 'center' 
                    }}>
                      {quotaMessage}
                    </div>
                  )}
                  
                  {operationStatus && (
                    <div className="operation-status" style={{ 
                      color: '#10b981', 
                      fontSize: '12px', 
                      marginTop: '4px',
                      textAlign: 'center' 
                    }}>
                      {operationStatus}
                    </div>
                  )}
                  
                  {lastError && (
                    <div className="error-message" style={{ 
                      color: '#ef4444', 
                      fontSize: '12px', 
                      marginTop: '4px',
                      textAlign: 'center' 
                    }}>
                      {lastError}
                    </div>
                  )}
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
              </div>

              {/* NEW: Recording Feedback */}
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
            <ConversationDisplay 
              messages={messages}
              activeSessionId={activeSessionId}
              isLoading={isLoadingMessages}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;