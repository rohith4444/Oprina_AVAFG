// src/pages/DashboardPage.tsx
// Updated dashboard with HybridAvatarManager integration

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import HybridAvatarManager, { HybridAvatarManagerRef } from '../components/HybridAvatarManager';
import ConversationDisplay from '../components/ConversationDisplay';
import type { 
  AvatarModeEvent, 
  QuotaEvent, 
  HeyGenSessionEvent 
} from '../types/heygen';
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
  const [volume, setVolume] = useState(75);
  const [isMuted, setIsMuted] = useState(false);
  const [recognition, setRecognition] = useState<InstanceType<typeof window.SpeechRecognition> | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  
  // New hybrid avatar state
  const [currentAvatarMode, setCurrentAvatarMode] = useState<string>('static');
  const [quotaInfo, setQuotaInfo] = useState<any>(null);
  
  const navigate = useNavigate();
  const avatarManagerRef = useRef<HybridAvatarManagerRef>(null);

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

    // Use hybrid avatar to speak assistant responses
    if (sender === 'assistant' && avatarManagerRef.current) {
      console.log('🗣️ Making hybrid avatar speak:', text);
      avatarManagerRef.current.speak(text).catch(error => {
        console.error('❌ Failed to make avatar speak:', error);
      });
    }
  }, [activeConversationId]);

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
    } else if (lowerCommand.includes('quota') || lowerCommand.includes('time')) {
      return "I'm currently monitoring my interactive time quota. When my HeyGen interactive time runs out, I'll automatically switch to voice-only mode so we can continue our conversation without interruption. You'll see the quota indicator in the top-right corner.";
    } else if (lowerCommand.includes('mode') || lowerCommand.includes('switch')) {
      return "I can operate in different modes: Interactive mode with full visual avatar, TTS mode with voice-only responses, and static mode for low-power usage. The mode indicator shows my current status in the top-left corner.";
    } else {
      return `I understand you said: "${transcript}". I'm your intelligent voice assistant powered by advanced AI technology. I can help you with email management, calendar scheduling, task organization, and much more. Try asking me to check your emails or review your calendar!`;
    }
  };

  const handleStartListening = useCallback(() => {
    if (recognition && !isListening) {
      console.log('🎤 Starting speech recognition...');
      recognition.start();
      setIsListening(true);
    }
  }, [recognition, isListening]);

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

  // ============================================================================
  // HYBRID AVATAR EVENT HANDLERS
  // ============================================================================

  const handleModeChange = useCallback((event: AvatarModeEvent) => {
    console.log('🔄 Avatar mode changed:', event.fromMode, '→', event.toMode);
    setCurrentAvatarMode(event.toMode);
    
    // Update UI based on mode change
    if (event.toMode === 'fallback') {
      console.log('⚠️ Switched to fallback mode:', event.reason);
    } else if (event.toMode === 'interactive') {
      console.log('✅ Switched to interactive mode');
    }
  }, []);

  const handleQuotaEvent = useCallback((event: QuotaEvent) => {
    console.log('📊 Quota event:', event.type, event.remainingMinutes);
    
    if (event.type === 'quota_warning') {
      console.log('⚠️ Quota warning: Low interactive time remaining');
      // Could show a toast notification here
    } else if (event.type === 'quota_exceeded') {
      console.log('❌ Quota exceeded: Switched to voice-only mode');
      // Could show a notification about the mode switch
    }
    
    // Update quota info for display
    setQuotaInfo({
      type: event.type,
      remainingMinutes: event.remainingMinutes,
      timestamp: event.timestamp,
    });
  }, []);

  const handleSessionEvent = useCallback((event: HeyGenSessionEvent) => {
    console.log('🎭 HeyGen session event:', event.type);
    
    if (event.type === 'session_ready') {
      console.log('🎉 HeyGen session is ready for interaction');
    } else if (event.type === 'session_error') {
      console.log('❌ HeyGen session error occurred');
    }
  }, []);

  // ============================================================================
  // CONVERSATION MANAGEMENT
  // ============================================================================

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

  // ============================================================================
  // MANUAL AVATAR CONTROL
  // ============================================================================

  const handleManualSpeak = useCallback((text: string) => {
    if (avatarManagerRef.current && text.trim()) {
      avatarManagerRef.current.speak(text).catch(error => {
        console.error('❌ Manual speak failed:', error);
      });
    }
  }, []);

  const handleResetQuota = useCallback(() => {
    if (avatarManagerRef.current) {
      avatarManagerRef.current.resetQuota();
      console.log('🔄 Quota reset manually');
    }
  }, []);

  // ============================================================================
  // RENDER
  // ============================================================================

  return (
    <div className="dashboard-page">
      {/* Sidebar - unchanged */}
      <Sidebar
        conversations={conversations}
        activeConversationId={activeConversationId}
        onNewChat={handleNewChat}
        onSelectChat={handleSelectChat}
      />
      
      {/* Main Content Area - 50/50 Layout */}
      <div className="main-content">
        <div className="dashboard-unified">
          
          {/* Left Side: Hybrid Avatar + Controls (50%) */}
          <div className="avatar-section">
            
            {/* NEW: Hybrid Avatar Manager */}
            <HybridAvatarManager
              ref={avatarManagerRef}
              selectedAvatarId="Ann_Therapist_public"
              quotaConfig={{
                totalMinutes: 20,
                warningThreshold: 5,
                resetType: 'manual',
              }}
              onModeChange={handleModeChange}
              onQuotaEvent={handleQuotaEvent}
              onSessionEvent={handleSessionEvent}
              className="hybrid-avatar-instance"
            />

            {/* Voice Controls - enhanced with hybrid avatar integration */}
            <div className="compact-voice-controls">
              {/* Microphone Button */}
              <button 
                className={`btn voice-button mic-button ${isListening ? 'active' : ''}`}
                onClick={isListening ? handleStopListening : handleStartListening}
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

              {/* NEW: Manual Controls for Testing */}
              {process.env.NODE_ENV === 'development' && (
                <div className="debug-controls">
                  <button 
                    className="btn debug-button"
                    onClick={() => handleManualSpeak('This is a test of the hybrid avatar system.')}
                    title="Test speech"
                  >
                    🗣️
                  </button>
                  <button 
                    className="btn debug-button"
                    onClick={handleResetQuota}
                    title="Reset quota"
                  >
                    🔄
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Right Side: Conversation (50%) - unchanged */}
          <div className="conversation-section">
            <ConversationDisplay
              messages={activeMessages}
            />
          </div>
        </div>
      </div>

      {/* Development Info Panel */}
      {process.env.NODE_ENV === 'development' && (
        <div className="dev-info-panel">
          <h4>🔧 Development Info</h4>
          <div className="dev-info-grid">
            <div>
              <strong>Avatar Mode:</strong> {currentAvatarMode}
            </div>
            <div>
              <strong>Speech Recognition:</strong> {recognition ? 'Available' : 'Not Available'}
            </div>
            <div>
              <strong>Listening:</strong> {isListening ? 'Yes' : 'No'}
            </div>
            <div>
              <strong>Volume:</strong> {volume}%
            </div>
            {quotaInfo && (
              <div>
                <strong>Last Quota Event:</strong> {quotaInfo.type} ({Math.round(quotaInfo.remainingMinutes)}min)
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DashboardPage;