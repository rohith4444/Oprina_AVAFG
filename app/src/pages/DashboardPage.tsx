/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from '../components/Sidebar';
import Avatar from '../components/Avatar';
import VoiceControls from '../components/VoiceControls';
import ConversationDisplay from '../components/ConversationDisplay';
import GmailPanel from '../components/GmailPanel'; // Enhanced version
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
  // State management
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isGmailConnected, setIsGmailConnected] = useState(false);
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [activeConversationId, setActiveConversationId] = useState<string | null>(null);

  // Get active messages
  const activeMessages = conversations.find(c => c.id === activeConversationId)?.messages || [];

  // Voice control handlers
  const handleStartListening = useCallback(() => {
    setIsListening(true);
    // TODO: Connect to Google Cloud Speech in Phase 3
  }, []);

  const handleStopListening = useCallback(() => {
    setIsListening(false);
    // TODO: Process speech and send to backend
  }, []);

  const handleToggleMute = useCallback(() => {
    setIsMuted(!isMuted);
  }, [isMuted]);

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
  };

  const handleSelectChat = (id: string) => {
    setActiveConversationId(id);
  };

  // Check Gmail connection on load
  useEffect(() => {
    const gmailConnected = localStorage.getItem('gmail_connected') === 'true';
    setIsGmailConnected(gmailConnected);
  }, []);

  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        {/* Sidebar - Always Present */}
        <Sidebar
          conversations={conversations}
          onNewChat={handleNewChat}
          onSelectChat={handleSelectChat}
          activeConversationId={activeConversationId}
        />

        {/* Main Dashboard Area */}
        <main className={`main-dashboard ${isGmailConnected ? 'with-gmail' : 'solo'}`}>
          <div className="dashboard-content">
            
            {/* Avatar Section - Main Focus */}
            <section className="avatar-section">
              <div className="avatar-container">
                <Avatar 
                  isListening={isListening} 
                  isSpeaking={isSpeaking}
                />
                <div className="avatar-status">
                  {isSpeaking 
                    ? "Speaking..." 
                    : isListening 
                    ? "Listening..." 
                    : "Ready to help"
                  }
                </div>
              </div>
            </section>

            {/* Voice Controls Section */}
            <section className="voice-controls-section">
              <VoiceControls
                onStartListening={handleStartListening}
                onStopListening={handleStopListening}
                onToggleMute={handleToggleMute}
                isMuted={isMuted}
                isListening={isListening}
              />
            </section>

            {/* Conversation Section */}
            <section className="conversation-section">
              <ConversationDisplay
                messages={activeMessages}
                isExpanded={true}
                onToggleExpand={() => {}} // Always expanded in new layout
              />
            </section>

          </div>
        </main>

        {/* Gmail Panel - Slides in when connected */}
        {isGmailConnected && (
          <aside className="gmail-panel">
            <GmailPanel />
          </aside>
        )}

      </div>
    </div>
  );
};

export default DashboardPage;