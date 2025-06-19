import React, { useState, useEffect } from 'react';
import {
  Settings,
  LogOut,
  User,
  MessageSquarePlus,
  ChevronLeft,
  ChevronRight,
  Send,
  Plug,
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
  isCollapsed?: boolean;
  onToggleCollapse?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  className = '', 
  conversations, 
  onNewChat, 
  onSelectChat, 
  isCollapsed: externalIsCollapsed,
  onToggleCollapse: externalOnToggleCollapse
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  
  // Track if we're on mobile
  const [isMobile, setIsMobile] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth <= 768;
    }
    return false;
  });
  
  // Initialize collapsed state based on screen size (if not controlled externally)
  const [internalIsCollapsed, setInternalIsCollapsed] = useState(() => {
    if (typeof window !== 'undefined') {
      return window.innerWidth <= 768; // Default to collapsed on mobile
    }
    return false;
  });
  
  // Use external state if provided, otherwise use internal state
  const isCollapsed = externalIsCollapsed !== undefined ? externalIsCollapsed : internalIsCollapsed;
  const setIsCollapsed = externalOnToggleCollapse || (() => setInternalIsCollapsed(!internalIsCollapsed));
  
  const [isGmailConnected, setIsGmailConnected] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  // Handle window resize to auto-collapse on mobile
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth <= 768;
      setIsMobile(mobile);
      if (mobile && !externalOnToggleCollapse) {
        // Only auto-collapse if not externally controlled
        setInternalIsCollapsed(true);
      }
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, [externalOnToggleCollapse]);

  const handleConnectApps = () => {
          navigate('/settings/connected-apps');
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
    if (externalOnToggleCollapse) {
      externalOnToggleCollapse();
    } else {
      setInternalIsCollapsed(!internalIsCollapsed);
    }
  };

  // Close sidebar when clicking outside on mobile
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (isMobile && e.target === e.currentTarget) {
      if (externalOnToggleCollapse) {
        externalOnToggleCollapse(); // This should close it
      } else {
        setInternalIsCollapsed(true);
      }
    }
  };

  return (
    <>
      {/* Mobile backdrop */}
      {!isCollapsed && isMobile && (
        <div 
          className="sidebar-backdrop"
          onClick={handleBackdropClick}
        />
      )}
      
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
                      className="conversation-item"
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
          <Button
            variant="primary"
            fullWidth
            onClick={handleConnectApps}
            icon={<Plug size={18} />}
            className="connect-apps-button"
          >
            {!isCollapsed && 'Connect Apps'}
          </Button>

          <div className="user-profile" onClick={() => setShowUserMenu(!showUserMenu)}>
            <div className="user-avatar">
              <User size={20} />
            </div>
            {!isCollapsed && (
              <div className="user-info">
                <div className="user-name">{user?.displayName || user?.email?.split('@')[0] || 'User'}</div>
                <div className="user-email">{user?.email || 'user@example.com'}</div>
              </div>
            )}

            {showUserMenu && (
              <div className="user-menu">
                <button className="menu-item" onClick={() => navigate('/settings/profile')}>
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
    </>
  );
};

export default Sidebar;