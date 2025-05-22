import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { MessageSquare, Settings, LogOut, Mail } from 'lucide-react';
import Logo from '../components/common/Logo';
import Button from '../components/common/Button';
import AvatarContainer from '../components/avatar/AvatarContainer';
import ConversationDisplay from '../components/conversation/ConversationDisplay';
import { Message } from '../types';

const AppPage: React.FC = () => {
  const [isGmailConnected, setIsGmailConnected] = useState(false);
  const [isConversationMinimized, setIsConversationMinimized] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  
  // Simulate conversation messages
  useEffect(() => {
    if (messages.length === 0) {
      // Add a welcome message
      const welcomeMessage: Message = {
        id: '1',
        sender: 'assistant',
        content: 'Hello! I\'m Oprina, your Gmail voice assistant. How can I help you today?',
        timestamp: Date.now(),
      };
      setMessages([welcomeMessage]);
    }
  }, [messages]);
  
  const handleMicToggle = (isActive: boolean) => {
    console.log('Microphone active:', isActive);
    
    if (isActive) {
      // Simulate user speaking after a delay
      setTimeout(() => {
        const userMessage: Message = {
          id: Date.now().toString(),
          sender: 'user',
          content: 'Show me my unread emails',
          timestamp: Date.now(),
        };
        setMessages(prev => [...prev, userMessage]);
        
        // Simulate assistant response after another delay
        setTimeout(() => {
          const assistantMessage: Message = {
            id: (Date.now() + 1).toString(),
            sender: 'assistant',
            content: isGmailConnected 
              ? 'You have 3 unread emails. The most recent one is from John Smith about "Project Update".'
              : 'To view your emails, you need to connect your Gmail account first. Would you like to do that now?',
            timestamp: Date.now() + 1000,
          };
          setMessages(prev => [...prev, assistantMessage]);
        }, 2000);
      }, 3000);
    }
  };
  
  const handleSpeakerToggle = (isActive: boolean) => {
    console.log('Speaker active:', isActive);
  };
  
  const handleConnectGmail = () => {
    setIsGmailConnected(true);
    
    // Add a system message
    const systemMessage: Message = {
      id: Date.now().toString(),
      sender: 'assistant',
      content: 'Gmail connected successfully! You can now ask me to read, summarize, or compose emails.',
      timestamp: Date.now(),
    };
    setMessages(prev => [...prev, systemMessage]);
  };

  return (
    <div className="h-screen flex bg-gray-100">
      {/* Sidebar */}
      <div className="w-64 bg-white shadow-md flex flex-col">
        <div className="p-4 border-b border-gray-200">
          <Link to="/" className="flex items-center space-x-2">
            <Logo />
            <span className="text-xl font-bold bg-gradient-to-r from-[#5B7CFF] via-[#4FD1C5] to-[#4ADE80] text-transparent bg-clip-text">
              Oprina
            </span>
          </Link>
        </div>
        
        <div className="p-4">
          <Button
            fullWidth
            onClick={handleConnectGmail}
            disabled={isGmailConnected}
          >
            <div className="flex items-center">
              <Mail className="mr-2 h-5 w-5" />
              {isGmailConnected ? 'Gmail Connected' : 'Connect Gmail'}
            </div>
          </Button>
        </div>
        
        <div className="flex-1 overflow-y-auto p-4">
          <div className="mb-6">
            <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2">
              Recent Conversations
            </h3>
            <div className="space-y-2">
              {isGmailConnected ? (
                <>
                  <div className="flex items-center p-2 bg-gray-100 rounded-md">
                    <MessageSquare className="h-4 w-4 text-gray-600 mr-2" />
                    <span className="text-sm font-medium">Email Summary (Today)</span>
                  </div>
                  <div className="flex items-center p-2 hover:bg-gray-100 rounded-md cursor-pointer">
                    <MessageSquare className="h-4 w-4 text-gray-600 mr-2" />
                    <span className="text-sm">Draft to Marketing Team</span>
                  </div>
                  <div className="flex items-center p-2 hover:bg-gray-100 rounded-md cursor-pointer">
                    <MessageSquare className="h-4 w-4 text-gray-600 mr-2" />
                    <span className="text-sm">Inbox Cleanup (Yesterday)</span>
                  </div>
                </>
              ) : (
                <div className="text-sm text-gray-500 italic">
                  Connect Gmail to see your conversations
                </div>
              )}
            </div>
          </div>
        </div>
        
        <div className="p-4 border-t border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 rounded-full bg-gray-200 flex items-center justify-center text-gray-600">
                U
              </div>
              <div>
                <div className="font-medium text-sm">User</div>
                <div className="text-xs text-gray-500">user@example.com</div>
              </div>
            </div>
            
            <div className="flex space-x-2">
              <button className="text-gray-600 hover:text-gray-900">
                <Settings className="h-5 w-5" />
              </button>
              <button className="text-gray-600 hover:text-gray-900">
                <LogOut className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="flex-1 flex flex-col">
        <div className="flex-1 p-6 flex">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 w-full">
            {/* Avatar section - takes 2/3 of the width on large screens */}
            <div className="lg:col-span-2 h-[500px]">
              <AvatarContainer 
                onMicToggle={handleMicToggle}
                onSpeakerToggle={handleSpeakerToggle}
              />
            </div>
            
            {/* Conversation section - takes 1/3 of the width on large screens */}
            <div className="h-[500px]">
              <ConversationDisplay 
                messages={messages}
                isMinimized={isConversationMinimized}
                onToggleMinimize={() => setIsConversationMinimized(!isConversationMinimized)}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AppPage;