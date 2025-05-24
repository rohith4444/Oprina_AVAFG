import React, { useState } from 'react';
import Sidebar from '../components/Sidebar';
import Avatar from '../components/Avatar';
import VoiceControls from '../components/VoiceControls';
import ConversationDisplay from '../components/ConversationDisplay';
import '../styles/DashboardPage.css';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

const DashboardPage: React.FC = () => {
  const [isListening, setIsListening] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isConversationExpanded, setIsConversationExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  
  const handleStartListening = () => {
    setIsListening(true);
    // In a real app, this would start the speech recognition
    
    // Mock adding a user message after a delay
    setTimeout(() => {
      addMessage('user', 'Show me my unread emails from today.');
    }, 1500);
    
    // Mock adding an assistant response after another delay
    setTimeout(() => {
      setIsListening(false);
      setIsSpeaking(true);
      
      setTimeout(() => {
        addMessage('assistant', 'You have 3 unread emails today. The most recent is from Sarah about the project deadline.');
        setIsSpeaking(false);
      }, 1000);
    }, 3000);
  };
  
  const handleStopListening = () => {
    setIsListening(false);
    // In a real app, this would stop the speech recognition
  };
  
  const handleToggleMute = () => {
    setIsMuted(!isMuted);
    // In a real app, this would mute/unmute the audio output
  };
  
  const addMessage = (sender: 'user' | 'assistant', text: string) => {
    const newMessage: Message = {
      id: Date.now().toString(),
      sender,
      text,
      timestamp: new Date(),
    };
    
    setMessages((prevMessages) => [...prevMessages, newMessage]);
  };
  
  return (
    <div className="dashboard-page">
      <div className="dashboard-container">
        <Sidebar />
        
        <main className="main-content">
          <div className="assistant-interface">
            <div className="avatar-container">
              <Avatar isListening={isListening} isSpeaking={isSpeaking} />
              <VoiceControls
                onStartListening={handleStartListening}
                onStopListening={handleStopListening}
                onToggleMute={handleToggleMute}
                isMuted={isMuted}
                isListening={isListening}
              />
            </div>
            
            <ConversationDisplay
              messages={messages}
              isExpanded={isConversationExpanded}
              onToggleExpand={() => setIsConversationExpanded(!isConversationExpanded)}
            />
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardPage;