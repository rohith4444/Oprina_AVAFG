import React, { useState } from 'react';
import { Mail, Settings, LogOut, User } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';
import Button from './Button';
import '../styles/Sidebar.css';

interface Conversation {
  id: string;
  preview: string;
  timestamp: Date;
}

const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isGmailConnected, setIsGmailConnected] = useState(false);
  
  // Mock data for recent conversations
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: '1',
      preview: 'Email summary for today',
      timestamp: new Date(Date.now() - 30 * 60000),
    },
    {
      id: '2',
      preview: 'Draft reply to marketing team',
      timestamp: new Date(Date.now() - 3 * 3600000),
    },
    {
      id: '3',
      preview: 'Find emails from John',
      timestamp: new Date(Date.now() - 2 * 86400000),
    },
  ]);
  
  const handleGmailConnect = () => {
    // This would be replaced with actual Gmail OAuth logic
    setIsGmailConnected(true);
  };
  
  const handleLogout = async () => {
    await logout();
    navigate('/');
  };
  
  const formatTimestamp = (timestamp: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - timestamp.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    
    if (diffDays === 0) {
      return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else {
      return timestamp.toLocaleDateString();
    }
  };
  
  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <Logo size={30} />
        <h2 className="sidebar-title">Oprina</h2>
      </div>
      
      <div className="gmail-connection">
        {isGmailConnected ? (
          <div className="connection-status">
            <Mail size={18} />
            <span>Gmail Connected</span>
          </div>
        ) : (
          <Button 
            variant="primary" 
            fullWidth 
            onClick={handleGmailConnect}
            icon={<Mail size={18} />}
          >
            Connect Gmail
          </Button>
        )}
      </div>
      
      <div className="conversations-section">
        <h3 className="section-title">Recent Conversations</h3>
        {conversations.length > 0 ? (
          <ul className="conversations-list">
            {conversations.map((conversation) => (
              <li key={conversation.id} className="conversation-item">
                <div className="conversation-preview">{conversation.preview}</div>
                <div className="conversation-time">{formatTimestamp(conversation.timestamp)}</div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="no-conversations">
            <p>No recent conversations</p>
          </div>
        )}
      </div>
      
      <div className="sidebar-footer">
        <button className="sidebar-button">
          <Settings size={20} />
          <span>Settings</span>
        </button>
        
        <div className="user-profile">
          <div className="user-avatar">
            <User size={20} />
          </div>
          <div className="user-info">
            <div className="user-name">{user?.email?.split('@')[0] || 'User'}</div>
            <div className="user-email">{user?.email || 'user@example.com'}</div>
          </div>
          <button className="logout-button" onClick={handleLogout}>
            <LogOut size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;