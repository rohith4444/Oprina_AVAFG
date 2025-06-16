/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState } from 'react';
import {
  Mail,
  Settings,
  LogOut,
  User,
  MessageSquarePlus,
  ChevronLeft,
  Send,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';
import Button from './Button';
import '../styles/Sidebar.css';

interface Conversation {
  id: string;
  messages: {
    id: string;
    sender: 'user' | 'assistant';
    text: string;
    timestamp: Date;
  }[];
  timestamp: Date;
}

interface SidebarProps {
  className?: string;
  conversations: Conversation[];
  onNewChat: () => void;
  onSelectChat: (id: string) => void;
  activeConversationId: string | null; // Add this
}

const Sidebar: React.FC<SidebarProps> = ({ className = '', conversations, onNewChat, onSelectChat, activeConversationId }) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isGmailConnected] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleGmailConnect = () => {
    const clientId = '7774023189-icl1rkitmcseeouj66ut0orcad2vb2u2.apps.googleusercontent.com';
    const redirectUri = 'http://localhost:5173/dashboard';
    const scope = 'https://www.googleapis.com/auth/gmail.readonly';
    const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?response_type=token&client_id=${clientId}&redirect_uri=${redirectUri}&scope=${scope}&prompt=consent&access_type=online`;

    window.location.href = authUrl;
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

  const toggleSidebar = () => {
    setIsCollapsed(!isCollapsed);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''} ${className}`}>
      <div className="sidebar-header">
        <div className="logo-section">
          <Logo size={30} />
          {!isCollapsed && <h2 className="sidebar-title">Oprina</h2>}
        </div>
        <button className="collapse-button" onClick={toggleSidebar}>
          <ChevronLeft
            size={16}
            style={{
              transform: isCollapsed ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.3s ease'
            }}
          />
        </button>
      </div>

      <div className="sidebar-content">
        <button className="new-chat-button" onClick={onNewChat}>
          <MessageSquarePlus size={20} />
          {!isCollapsed && <span>New chat</span>}
        </button>

        <div className="conversations-section">
          {!isCollapsed && <h3 className="section-title">Recent Conversations</h3>}
          {conversations.length > 0 ? (
            <ul className="conversations-list">
              {conversations.map((conversation) => {
                const firstUserMessage = conversation.messages.find(m => m.sender === 'user');
                const title = firstUserMessage ? firstUserMessage.text : 'Untitled Chat';
                return (
                  <li
                    key={conversation.id}
                    className={`conversation-item ${
                      conversation.id === activeConversationId ? 'active' : ''
                    }`}
                    onClick={() => onSelectChat(conversation.id)}
                  >
                    <Send size={16} />
                    {!isCollapsed && (
                      <>
                        <div className="conversation-preview">{title}</div>
                        <div className="conversation-time">{formatTimestamp(conversation.timestamp)}</div>
                      </>
                    )}
                  </li>
                );
              })}
            </ul>
          ) : (
            <div className="no-conversations">
              {!isCollapsed && <p>No recent conversations</p>}
            </div>
          )}
        </div>
      </div>

      <div className="sidebar-footer">
        {!isGmailConnected && (
          <Button
            variant="primary"
            fullWidth
            onClick={handleGmailConnect}
            icon={<Mail size={18} />}
            className="gmail-connect-button"
          >
            {!isCollapsed && 'Connect Gmail'}
          </Button>
        )}

        <div className="user-profile" onClick={() => setShowUserMenu(!showUserMenu)}>
          <div className="user-avatar">
            <User size={20} />
          </div>
          {!isCollapsed && (
            <div className="user-info">
              <div className="user-name">{user?.email?.split('@')[0] || 'User'}</div>
              <div className="user-email">{user?.email || 'user@example.com'}</div>
            </div>
          )}

          {showUserMenu && (
            <div className="user-menu">
              <button className="menu-item" onClick={() => navigate('/settings')}>
                <Settings size={16} />
                <span>Settings</span>
              </button>
              <button className="menu-item" onClick={() => navigate('/contact')}>
                <Send size={16} />
                <span>Contact Us</span>
              </button>
              <button className="menu-item" onClick={handleLogout}>
                <LogOut size={16} />
                <span>Log Out</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
