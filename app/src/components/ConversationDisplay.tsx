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
  isExpanded: boolean;
  onToggleExpand: () => void;
}

const ConversationDisplay: React.FC<ConversationDisplayProps> = ({
  messages,
  isExpanded,
  onToggleExpand,
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages]);

  const formatTimestamp = (timestamp: Date) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className={`conversation-display ${isExpanded ? 'expanded' : ''}`}>
      <div className="conversation-header">
        <h3>Conversation</h3>
        <button 
          className="toggle-button"
          onClick={onToggleExpand}
          aria-label={isExpanded ? 'Minimize' : 'Expand'}
        >
          {isExpanded ? '▼' : '▲'}
        </button>
      </div>
      
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="no-messages">
            <p>Start speaking to Oprina</p>
          </div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id}
              className={`message ${message.sender === 'user' ? 'user-message' : 'assistant-message'}`}
            >
              <div className="message-content">
                <span className="message-sender">
                  {message.sender === 'user' ? 'You' : 'Oprina'}
                </span>
                <p className="message-text">{message.text}</p>
                <span className="message-time">{formatTimestamp(message.timestamp)}</span>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef}></div>
      </div>
      
      <div className="conversation-input">
        <input 
          type="text" 
          placeholder="Type your message..." 
          className="text-input"
        />
        <button className="send-button">Send</button>
      </div>
    </div>
  );
};

export default ConversationDisplay;