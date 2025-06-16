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
}

const ConversationDisplay: React.FC<ConversationDisplayProps> = ({
  messages,
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
    <div className="conversation-display">
      {/* Header */}
      <div className="conversation-header">
        <h3 className="conversation-title">Conversation</h3>
        <div className="conversation-status">
          <span className="message-count">{messages.length} messages</span>
        </div>
      </div>
      
      {/* Messages Container */}
      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="no-messages">
            <div className="no-messages-content">
              <p>Start speaking to Oprina</p>
              <small>Use the microphone button to begin a conversation</small>
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

      {/* Input Area */}
      <div className="conversation-input">
        <input
          type="text"
          className="text-input"
          placeholder="Type a message or use voice..."
          onKeyPress={(e) => {
            if (e.key === 'Enter') {
              // Could add text input functionality here in the future
              console.log('Text input pressed:', (e.target as HTMLInputElement).value);
            }
          }}
        />
        <button 
          className="send-button"
          onClick={() => {
            // Could add send functionality here in the future
            console.log('Send button clicked');
          }}
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ConversationDisplay;