import React, { useRef, useEffect } from 'react';
import { Message } from '../../types';
import { ChevronDown, X } from 'lucide-react';

interface ConversationDisplayProps {
  messages: Message[];
  isMinimized: boolean;
  onToggleMinimize: () => void;
}

const ConversationDisplay: React.FC<ConversationDisplayProps> = ({
  messages,
  isMinimized,
  onToggleMinimize
}) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollToBottom();
  }, [messages, isMinimized]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  if (isMinimized) {
    return (
      <div className="bg-white rounded-lg shadow-md p-4 flex justify-between items-center cursor-pointer" onClick={onToggleMinimize}>
        <div className="flex items-center">
          <div className="w-2 h-2 rounded-full bg-green-500 mr-2"></div>
          <span>Conversation with Oprina</span>
        </div>
        <ChevronDown size={20} />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md flex flex-col h-full">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center">
        <h3 className="font-medium">Conversation</h3>
        <button onClick={onToggleMinimize} className="text-gray-500 hover:text-gray-700">
          <X size={20} />
        </button>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <p>Your conversation will appear here.</p>
          </div>
        ) : (
          messages.map((message) => (
            <div 
              key={message.id}
              className={`flex ${message.sender === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div 
                className={`max-w-[80%] rounded-lg px-4 py-2 ${
                  message.sender === 'user' 
                    ? 'bg-black text-white' 
                    : 'bg-gray-100 text-gray-800'
                }`}
              >
                <p>{message.content}</p>
                <div className={`text-xs mt-1 ${
                  message.sender === 'user' ? 'text-gray-300' : 'text-gray-500'
                }`}>
                  {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="border-t border-gray-200 p-4">
        <div className="relative">
          <input
            type="text"
            placeholder="Type a message..."
            className="w-full rounded-full border border-gray-300 pl-4 pr-12 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
          />
          <button 
            className="absolute right-2 top-1/2 transform -translate-y-1/2 bg-black text-white rounded-full p-1.5"
          >
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};

export default ConversationDisplay;