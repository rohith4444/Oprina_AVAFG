// src/pages/DashboardPage.tsx - Updated with Session API Integration & Audio Recording
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
  
  const navigate = useNavigate();

  // Get user token for API calls
  const getUserToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token;
  };

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

  const handleAvatarStartTalking = useCallback(() => {
    console.log('🗣️ Avatar started talking');
    setIsSpeaking(true);
  }, []);

  const handleAvatarStopTalking = useCallback(() => {
    console.log('🤐 Avatar stopped talking');
    setIsSpeaking(false);
  }, []);

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

  // UPDATED: Voice interaction handlers
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
    setActiveSessionId(sessionId);
    console.log('💬 Session selected:', sessionId);
  }, []);

  const handleDeleteSession = useCallback(async (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      await deleteSession(sessionId);
    }
  }, []);

  // Avatar mode toggle (for testing/development)
  const toggleAvatarMode = () => {
    setUseStaticAvatar(!useStaticAvatar);
    setAvatarReady(false);
    setAvatarError(null);
    console.log('🔄 Switched to', !useStaticAvatar ? 'static' : 'streaming', 'avatar');
  };

  // Add message to active session (for manual text interactions)
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
              {/* Avatar Mode Toggle (Development Only) */}
              {/* Avatar Mode Toggle with Quota Display */}
              {process.env.NODE_ENV === 'development' && (
                <div className="avatar-mode-toggle">
                  <div className="left-section">
                    <button 
                        className="mode-status-box"
                        onClick={toggleAvatarMode}
                        style={{
                          backgroundColor: useStaticAvatar ? '#4FD1C5' : '#5B7CFF'
                        }}
                      >
                        {useStaticAvatar ? 'Switch to Streaming' : 'Switch to Static'}
                      </button>
                      <span className="mode-label">
                        {useStaticAvatar ? 'Static Avatar' : 'Streaming Avatar'}
                      </span>
                  </div>
                  
                  <div className="right-section">
                    <QuotaDisplay isVisible={!useStaticAvatar} />
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