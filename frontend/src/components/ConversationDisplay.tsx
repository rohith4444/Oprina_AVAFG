import React, { useRef, useEffect } from 'react';
import '../styles/ConversationDisplay.css';

interface Message {
  id: string;
  sender: 'user' | 'assistant';
  text: string;
  timestamp: Date;
}

interface ConversationDisplayProps {
  messages: Message[];
  activeSessionId: string | null;
  isLoading?: boolean;
}

const ConversationDisplay: React.FC<ConversationDisplayProps> = ({
  messages,
  activeSessionId,
  isLoading = false,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const formatTimestamp = (timestamp: Date) => {
    return new Date(timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // No active session state
  if (!activeSessionId) {
    return (
      <div className="conversation-display">
        {/* Header */}
        <div className="conversation-header">
          <h3 className="conversation-title">Conversation</h3>
          <div className="conversation-status">
            <span className="message-count">0 messages</span>
          </div>
        </div>
        
        {/* Empty state - no session */}
        <div className="messages-container">
          <div className="no-messages">
            <div className="no-messages-content">
              <p>Start speaking to Oprina</p>
              <small>Use the microphone button to begin a conversation</small>
              <div className="instruction-hint">
                💡 Your session will be created automatically when you start talking
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="conversation-display">
      {/* Header */}
      <div className="conversation-header">
        <h3 className="conversation-title">Conversation</h3>
        <div className="conversation-status">
          <span className="message-count">
            {isLoading ? 'Loading...' : `${messages.length} messages`}
          </span>
        </div>
      </div>
      
      {/* Messages Container */}
      <div className="messages-container">
        {isLoading ? (
          <div className="loading-messages">
            <div className="loading-content">
              <p>Loading conversation...</p>
            </div>
          </div>
        ) : messages.length === 0 ? (
          <div className="no-messages">
            <div className="no-messages-content">
              <p>Ready to chat!</p>
              <small>Start speaking to begin this conversation</small>
              <div className="instruction-hint">
                🎙️ Click the microphone button to start talking
              </div>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div 
                key={message.id}
                className={`message ${message.sender === 'user' ? 'user-message' : 'assistant-message'}`}
              >
                <div className="message-content">
                  <div className="message-header">
                    <span className="message-sender">
                      {message.sender === 'user' ? 'You' : 'Oprina'}
                    </span>
                    <span className="message-time">{formatTimestamp(message.timestamp)}</span>
                  </div>
                  <p className="message-text">{message.text}</p>
                </div>
              </div>
            ))}
            <div ref={messagesEndRef}></div>
          </>
        )}
      </div>
      
      {/* Voice interaction hint */}
      {activeSessionId && messages.length === 0 && !isLoading && (
        <div className="voice-hint">
          <p>🎤 This conversation is ready for voice interaction</p>
        </div>
      )}
    </div>
  );
};

export default ConversationDisplay;