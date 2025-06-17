// src/pages/DashboardPage.tsx - Updated Integration
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
  
interface Conversation {
  id: string;
  messages: Message[];
  timestamp: Date;
}

const DashboardPage: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [volume, setVolume] = useState(75);
  const [isMuted, setIsMuted] = useState(false);
  const [recognition, setRecognition] = useState<InstanceType<typeof window.SpeechRecognition> | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  
  // Avatar configuration - Feature flag for static vs streaming
  const [useStaticAvatar, setUseStaticAvatar] = useState(true); // Toggle this to switch modes
  const [avatarReady, setAvatarReady] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  
  // Refs for both avatar types
  const streamingAvatarRef = useRef<HeyGenAvatarRef>(null);
  const staticAvatarRef = useRef<StaticAvatarRef>(null);
  
  const navigate = useNavigate();

  const activeMessages = conversations.find(c => c.id === activeConversationId)?.messages || [];

  // Initialize with a default conversation
  useEffect(() => {
    if (conversations.length === 0) {
      const defaultConversation: Conversation = {
        id: Date.now().toString(),
        messages: [],
        timestamp: new Date(),
      };
      setConversations([defaultConversation]);
      setActiveConversationId(defaultConversation.id);
    }
  }, [conversations.length]);

  const addMessage = useCallback((sender: 'user' | 'assistant', text: string) => {
    setConversations(prev => {
      return prev.map(conv =>
        conv.id === activeConversationId
          ? {
              ...conv,
              messages: [...conv.messages, {
                id: Date.now().toString(),
                sender,
                text,
                timestamp: new Date()
              }]
            }
          : conv
      );
    });

    // Make avatar speak (works for both static and streaming)
    if (sender === 'assistant' && avatarReady) {
      console.log('🗣️ Making avatar speak:', text);
      
      if (useStaticAvatar && staticAvatarRef.current) {
        staticAvatarRef.current.speak(text);
      } else if (!useStaticAvatar && streamingAvatarRef.current) {
        streamingAvatarRef.current.speak(text);
      }
    }
  }, [activeConversationId, avatarReady, useStaticAvatar]);

  useEffect(() => {
    // Handle Gmail OAuth callback
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.substring(1));
    const gmailToken = params.get('access_token');
    if (gmailToken) {
      localStorage.setItem('gmail_token', gmailToken);
      localStorage.setItem('gmail_connected', 'true');
      window.history.replaceState(null, '', window.location.pathname);
    }

    // Restore user session
    const restoreSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      const user = session?.user;

      if (user) {
        localStorage.setItem('user', JSON.stringify({
          uid: user.id,
          email: user.email,
        }));
      } else {
        navigate('/login');
        return;
      }
    };

    restoreSession();

    // Set up speech recognition
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';

      recognitionInstance.onresult = (event: SpeechRecognitionEvent) => {
        const transcript = event.results[0][0].transcript;
        console.log('🎤 Speech recognized:', transcript);
        
        // Add user message
        addMessage('user', transcript);
        
        // Generate response after a brief delay
        setTimeout(() => {
          const response = generateDummyResponse(transcript);
          addMessage('assistant', response);
        }, 1000);
      };

      recognitionInstance.onerror = (event: SpeechRecognitionErrorEvent) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
      };

      recognitionInstance.onend = () => {
        console.log('🎤 Speech recognition ended');
        setIsListening(false);
      };

      setRecognition(recognitionInstance);
    }
  }, [navigate, addMessage]);

  // Enhanced dummy response generator
  const generateDummyResponse = (transcript: string): string => {
    const lowerCommand = transcript.toLowerCase();
    
    if (lowerCommand.includes('email') || lowerCommand.includes('gmail')) {
      return "I found 3 new emails in your inbox. You have one urgent message from your manager about tomorrow's meeting, and two newsletter updates. The urgent email is about the quarterly review preparation. Would you like me to read the full content?";
    } else if (lowerCommand.includes('calendar') || lowerCommand.includes('schedule')) {
      return "I've checked your calendar for today and the rest of the week. You have a team meeting at 2 PM today with the development team, and a client call scheduled for tomorrow at 10 AM with the marketing team. Your Thursday is completely free if you'd like to schedule something new.";
    } else if (lowerCommand.includes('summary') || lowerCommand.includes('summarize')) {
      return "Here's your daily summary: You have 5 new emails including 2 requiring immediate attention, 2 calendar events today including the important team meeting, and 3 pending tasks on your to-do list. Your highest priority item is reviewing the project proposal before the 2 PM meeting starts.";
    } else if (lowerCommand.includes('hello') || lowerCommand.includes('hi')) {
      return "Hello! I'm your Oprina voice assistant. I'm here to help you manage your emails, calendar, and daily tasks efficiently. You can ask me to check your emails, review your schedule, or summarize your day. What would you like me to help you with?";
    } else if (lowerCommand.includes('test') || lowerCommand.includes('testing')) {
      return "This is a test of my speech capabilities. I can speak any text you send to me with perfect lip synchronization. The avatar technology uses advanced AI to match my mouth movements with the spoken words in real-time.";
    } else {
      return `I understand you said: "${transcript}". I'm your intelligent voice assistant powered by advanced AI technology. I can help you with email management, calendar scheduling, task organization, and much more. Try asking me to check your emails or review your calendar!`;
    }
  };

  const handleStartListening = useCallback(() => {
    if (recognition && !isListening && avatarReady) {
      console.log('🎤 Starting speech recognition...');
      recognition.start();
      setIsListening(true);
    } else if (!avatarReady) {
      console.warn('⚠️ Avatar not ready yet, please wait...');
    }
  }, [recognition, isListening, avatarReady]);

  const handleStopListening = useCallback(() => {
    if (recognition && isListening) {
      console.log('🎤 Stopping speech recognition...');
      recognition.stop();
      setIsListening(false);
    }
  }, [recognition, isListening]);

  const handleVolumeChange = useCallback((newVolume: number) => {
    setVolume(newVolume);
    setIsMuted(newVolume === 0);
    console.log('🔊 Volume changed to:', newVolume);
  }, []);

  const handleVolumeIncrement = useCallback(() => {
    const newVolume = Math.min(100, volume + 10);
    handleVolumeChange(newVolume);
  }, [volume, handleVolumeChange]);

  const handleVolumeDecrement = useCallback(() => {
    const newVolume = Math.max(0, volume - 10);
    handleVolumeChange(newVolume);
  }, [volume, handleVolumeChange]);

  // Unified avatar event handlers (work for both static and streaming)
  const handleAvatarReady = useCallback(() => {
    console.log('🎉 Avatar is ready for interaction!');
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

  // Conversation management for sidebar
  const handleNewChat = () => {
    const newId = Date.now().toString();
    const newConversation: Conversation = {
      id: newId,
      messages: [],
      timestamp: new Date(),
    };
    setConversations(prev => [newConversation, ...prev]);
    setActiveConversationId(newId);
    console.log('💬 New conversation created:', newId);
  };

  const handleSelectChat = (id: string) => {
    setActiveConversationId(id);
    console.log('💬 Conversation selected:', id);
  };

  // Avatar mode toggle (for testing/development)
  const toggleAvatarMode = () => {
    setUseStaticAvatar(!useStaticAvatar);
    setAvatarReady(false);
    setAvatarError(null);
    console.log('🔄 Switched to', !useStaticAvatar ? 'static' : 'streaming', 'avatar');
  };

  return (
    <div className="dashboard-page min-h-screen flex flex-col">
      <div className="flex flex-1">
        {/* Sidebar */}
        <Sidebar
          conversations={conversations}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
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
                    onAvatarError={handleAvatarError}
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
                    onAvatarStartTalking={handleAvatarStartTalking}
                    onAvatarStopTalking={handleAvatarStopTalking}
                  />
                )}
              </div>

              {/* Error Display */}
              {avatarError && (
                <div className="avatar-error-message">
                  <p>⚠️ Avatar connection issue</p>
                  <small>{avatarError}</small>
                </div>
              )}

              {/* Clean Voice Controls */}
              <div className="compact-voice-controls">
                {/* Microphone Button */}
                <button 
                  className={`btn voice-button mic-button ${isListening ? 'active' : ''}`}
                  onClick={isListening ? handleStopListening : handleStartListening}
                  disabled={!avatarReady}
                  title={isListening ? 'Stop listening' : 'Start listening'}
                >
                  {isListening ? '🎙️' : '🎤'}
                </button>

                {/* Volume Control */}
                <div className="volume-control">
                  <button 
                    className="btn volume-button"
                    onClick={handleVolumeDecrement}
                    disabled={volume === 0}
                    title="Volume down"
                  >
                    🔉
                  </button>
                  
                  <div className="volume-slider-container">
                    <input
                      type="range"
                      min="0"
                      max="100"
                      value={volume}
                      onChange={(e) => handleVolumeChange(parseInt(e.target.value))}
                      className="volume-slider"
                      title={`Volume: ${volume}%`}
                      disabled={isMuted}
                    />
                    <div className="volume-label">
                      {isMuted ? 'Muted' : `${volume}%`}
                    </div>
                  </div>
                  
                  <button 
                    className="btn volume-button"
                    onClick={handleVolumeIncrement}
                    disabled={volume === 100}
                    title="Volume up"
                  >
                    🔊
                  </button>
                </div>
              </div>
            </div>

            {/* Right Side: Conversation (50%) */}
            <div className="conversation-section">
              <ConversationDisplay
                messages={activeMessages}
              />
            </div>
          </div>
        </div>
      </div>
      {/* Footer - Same component used in settings page */}
      <MinimalFooter />
    </div>
  );
};

export default DashboardPage;