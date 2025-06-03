import React, { useState, useEffect, useCallback, useRef } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import HeyGenAvatar, { HeyGenAvatarRef } from '../components/HeyGenAvatar';
import VoiceControls from '../components/VoiceControls';
import ConversationDisplay from '../components/ConversationDisplay';
import GmailPanel from '../components/GmailPanel';
import '../styles/DashboardPage.css';
import EnvTest from '../components/EnvTest';

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
  const [isMuted, setIsMuted] = useState(false);
  const [isGmailConnected, setIsGmailConnected] = useState(false);
  const [recognition, setRecognition] = useState<InstanceType<typeof window.SpeechRecognition> | null>(null);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);
  
  // Avatar state management
  const [avatarReady, setAvatarReady] = useState(false);
  const [avatarError, setAvatarError] = useState<string | null>(null);
  const avatarRef = useRef<HeyGenAvatarRef>(null);
  
  const navigate = useNavigate();

  const activeMessages = conversations.find(c => c.id === activeConversationId)?.messages || [];

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

    // If it's an assistant message, make avatar speak
    if (sender === 'assistant' && avatarRef.current && avatarReady) {
      console.log('🗣️ Making avatar speak:', text);
      avatarRef.current.speak(text);
    }
  }, [activeConversationId, avatarReady]);

  useEffect(() => {
    // Handle Gmail OAuth callback
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.substring(1));
    const gmailToken = params.get('access_token');
    if (gmailToken) {
      localStorage.setItem('gmail_token', gmailToken);
      localStorage.setItem('gmail_connected', 'true');
      setIsGmailConnected(true);
      window.history.replaceState(null, '', window.location.pathname);
    }

    // Restore user session
    const restoreSession = async () => {
      const { data: { session } } = await supabase.auth.getSession();
      const user = session?.user;
      const gmailConnected = localStorage.getItem('gmail_connected') === 'true';

      if (user) {
        localStorage.setItem('user', JSON.stringify({
          uid: user.id,
          email: user.email,
        }));
      } else if (!gmailConnected) {
        navigate('/login');
        return;
      } else {
        setIsGmailConnected(true);
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

  // Day 1 dummy response generator (enhanced for avatar testing)
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

  const handleToggleMute = useCallback(() => {
    setIsMuted(!isMuted);
    console.log('🔊 Audio mute toggled:', !isMuted);
  }, [isMuted]);

  // Avatar event handlers
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

  // Conversation management
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

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar
          className={isGmailConnected ? 'sidebar-collapsed' : ''}
          conversations={conversations}
          activeConversationId={activeConversationId}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
        />
        
        <main className="main-content">
          <div className={`main-panel ${isGmailConnected ? 'gmail-connected' : ''}`}>
            <div className="split-layout">
              {/* Gmail Panel (if connected) */}
              {isGmailConnected && (
                <div className="gmail-view split-half">
                  <GmailPanel />
                </div>
              )}
              
              {/* Main Assistant Area */}
              <div className="assistant-view split-half">
                <div className="top-section">
                  {/* Avatar Section */}
                  <div className="avatar-section">
                    <HeyGenAvatar
                      ref={avatarRef}
                      isListening={isListening}
                      isSpeaking={isSpeaking}
                      onAvatarReady={handleAvatarReady}
                      onAvatarError={handleAvatarError}
                      onAvatarStartTalking={handleAvatarStartTalking}
                      onAvatarStopTalking={handleAvatarStopTalking}
                    />

                    <EnvTest />

                    {/* Avatar Status Messages */}
                    {avatarError && (
                      <div className="avatar-error-notice">
                        <p>⚠️ Avatar connection issue. Please check your HeyGen API key and avatar ID in the .env file.</p>
                        <small>Error: {avatarError}</small>
                      </div>
                    )}
                    
                    {!avatarReady && !avatarError && (
                      <div className="avatar-loading-notice">
                        <p>🔄 Setting up your avatar...</p>
                        <small>Connecting to HeyGen streaming service...</small>
                      </div>
                    )}
                    
                    {avatarReady && (
                      <div className="avatar-success-notice">
                        <p>✅ Avatar ready! You can now use voice commands or click "Test Speech".</p>
                      </div>
                    )}
                  </div>
                  
                  {/* Voice Controls Section */}
                  <div className="controls-section">
                    <VoiceControls
                      onStartListening={handleStartListening}
                      onStopListening={handleStopListening}
                      onToggleMute={handleToggleMute}
                      isMuted={isMuted}
                      isListening={isListening}
                    />
                    
                    {/* Day 1 Testing Information */}
                    <div className="day1-info">
                      <h4>🧪 Day 1 - Avatar Testing:</h4>
                      <ul>
                        <li><strong>Test Speech:</strong> Click "Test Speech" button on avatar</li>
                        <li><strong>Voice Recognition:</strong> Use microphone button to speak</li>
                        <li><strong>Try Commands:</strong> "check my emails", "show calendar", "hello"</li>
                        <li><strong>Watch Avatar:</strong> Notice perfect lip-sync when speaking</li>
                      </ul>
                      <div className="status-indicators">
                        <span className={`status ${avatarReady ? 'ready' : 'pending'}`}>
                          Avatar: {avatarReady ? '✅ Ready' : '⏳ Loading'}
                        </span>
                        <span className={`status ${recognition ? 'ready' : 'error'}`}>
                          Speech: {recognition ? '✅ Ready' : '❌ Not Available'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* Conversation Display */}
                <ConversationDisplay
                  messages={activeMessages}
                  isExpanded={true}
                  onToggleExpand={() => {}}
                />
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardPage;