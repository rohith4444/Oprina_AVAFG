import React, { useState, useEffect, useCallback } from 'react';
import { supabase } from '../supabaseClient';
import { useNavigate } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Avatar from '../components/Avatar';
import VoiceControls from '../components/VoiceControls';
import ConversationDisplay from '../components/ConversationDisplay';
import '../styles/DashboardPage.css';
import GmailPreview from '../components/GmailPreview';

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
  }, [activeConversationId]);

  useEffect(() => {
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.substring(1));
    const gmailToken = params.get('access_token');
    if (gmailToken) {
      localStorage.setItem('gmail_token', gmailToken);
      localStorage.setItem('gmail_connected', 'true');
      setIsGmailConnected(true);
      window.history.replaceState(null, '', window.location.pathname);
    }

    const restoreSession = async () => {
      const { data: { session }, error } = await supabase.auth.getSession();
      const user = session?.user;
      const gmailConnected = localStorage.getItem('gmail_connected') === 'true';

      if (user) {
        localStorage.setItem('user', JSON.stringify({
          uid: user.id,
          email: user.email,
        }));
      } else if (!gmailConnected) {
        navigate('/login');
      } else {
        setIsGmailConnected(true);
      }
    };

    restoreSession();

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognitionInstance = new SpeechRecognition();
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';

      recognitionInstance.onresult = (event: SpeechRecognitionEvent) => {
  const transcript = event.results[0][0].transcript;
  addMessage('user', transcript);
  setIsSpeaking(true);
  setTimeout(() => {
    addMessage('assistant', 'I understand you said: ' + transcript);
    setIsSpeaking(false);
  }, 1000);
};

recognitionInstance.onerror = (event: SpeechRecognitionErrorEvent) => {
  console.error('Speech recognition error:', event.error);
  setIsListening(false);
};



      setRecognition(recognitionInstance);
    }
  }, [navigate, addMessage]);

  const handleStartListening = useCallback(() => {
    if (recognition && !isListening) {
      recognition.start();
      setIsListening(true);
    }
  }, [recognition, isListening]);

  const handleStopListening = useCallback(() => {
    if (recognition && isListening) {
      recognition.stop();
      setIsListening(false);
    }
  }, [recognition, isListening]);

  const handleToggleMute = useCallback(() => {
    setIsMuted(!isMuted);
  }, [isMuted]);

  const handleNewChat = () => {
    const newId = Date.now().toString();
    const newConversation: Conversation = {
      id: newId,
      messages: [],
      timestamp: new Date(),
    };
    setConversations(prev => [newConversation, ...prev]);
    setActiveConversationId(newId);
  };

  const handleSelectChat = (id: string) => {
    setActiveConversationId(id);
  };

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar
          className={isGmailConnected ? 'sidebar-collapsed' : ''}
          conversations={conversations}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
        />
        <main className="main-content">
          <div className={`main-panel ${isGmailConnected ? 'gmail-connected' : ''}`}>
            <div className="split-layout">
              {isGmailConnected && (
                <div className="gmail-view split-half">
                  <GmailPreview accessToken={localStorage.getItem('gmail_token') || ''} />
                </div>
              )}
              <div className="assistant-view split-half">
                <div className="top-section">
                  <div className="avatar-section">
                    <Avatar isListening={isListening} isSpeaking={isSpeaking} />
                  </div>
                  <div className="controls-section">
                    <VoiceControls
                      onStartListening={handleStartListening}
                      onStopListening={handleStopListening}
                      onToggleMute={handleToggleMute}
                      isMuted={isMuted}
                      isListening={isListening}
                    />
                  </div>
                </div>
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
