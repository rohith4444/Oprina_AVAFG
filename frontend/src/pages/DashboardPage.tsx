// src/pages/DashboardPage.tsx - Updated with Session API Integration
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import HeyGenAvatar, { HeyGenAvatarRef } from '../components/HeyGenAvatar';
import StaticAvatar, { StaticAvatarRef } from '../components/StaticAvatar';
import ConversationDisplay from '../components/ConversationDisplay';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/DashboardPage.css';

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

declare global {
  interface Window {
    SpeechRecognition: any;
    webkitSpeechRecognition: any;
  }
}

// Backend API URL - Update this to match your backend
const BACKEND_API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

const DashboardPage: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(75);
  const [isMuted, setIsMuted] = useState(false);
  const [recognition, setRecognition] = useState<InstanceType<typeof window.SpeechRecognition> | null>(null);
  
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
  
  // Refs for both avatar types
  const streamingAvatarRef = useRef<HeyGenAvatarRef>(null);
  const staticAvatarRef = useRef<StaticAvatarRef>(null);
  
  const navigate = useNavigate();

  // Get user token for API calls
  const getUserToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token;
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
        setMessages(data.messages);  // Extract messages from response
        console.log('💬 Loaded messages for session:', sessionId, data.messages.length);
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

  // Voice interaction handlers
  const handleStartListening = useCallback(async () => {
    // Auto-create session when user starts talking if none exists
    if (!activeSessionId && !isCreatingSession) {
      console.log('🎙️ Auto-creating session for voice interaction');
      await createNewSession();
    }
    
    setIsListening(true);
    console.log('🎙️ Started listening');
    
    // TODO: Add actual voice recognition logic here
    // This would integrate with speech-to-text and send to session API
  }, [activeSessionId, isCreatingSession]);

  const handleStopListening = useCallback(() => {
    setIsListening(false);
    console.log('🛑 Stopped listening');
    
    // TODO: Add logic to process voice input and send to API
  }, []);

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

  // Add message to active session (for voice interactions)
  const addMessage = useCallback((sender: 'user' | 'assistant', text: string) => {
    if (!activeSessionId) return;
    
    const newMessage: Message = {
      id: Date.now().toString(),
      sender,
      text,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, newMessage]);
    
    // TODO: Send message to session API here
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
              {process.env.NODE_ENV === 'development' && (
                <div style={{ marginBottom: '1rem', textAlign: 'center' }}>
                  <button 
                    onClick={toggleAvatarMode}
                    style={{ 
                      padding: '0.5rem 1rem', 
                      fontSize: '0.75rem',
                      backgroundColor: useStaticAvatar ? '#4FD1C5' : '#5B7CFF',
                      color: 'white',
                      border: 'none',
                      borderRadius: '0.25rem',
                      cursor: 'pointer'
                    }}
                  >
                    {useStaticAvatar ? 'Static Avatar' : 'Streaming Avatar'}
                  </button>
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
                  disabled={!avatarReady || isCreatingSession}
                >
                  🎙️
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

      <MinimalFooter />
    </div>
  );
};

export default DashboardPage;