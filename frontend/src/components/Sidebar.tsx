import React, { useState } from 'react';
import {
  Settings,
  LogOut,
  User,
  MessageSquarePlus,
  ChevronLeft,
  Send,
  Plug,
  Trash2,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import Logo from './Logo';
import Button from './Button';
import '../styles/Sidebar.css';

interface Session {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

interface SidebarProps {
  className?: string;
  sessions: Session[];
  activeSessionId: string | null;
  onNewChat: () => void;
  onSessionSelect: (sessionId: string) => void;
  onSessionDelete: (sessionId: string) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  className = '', 
  sessions, 
  activeSessionId,
  onNewChat, 
  onSessionSelect,
  onSessionDelete 
}) => {
  const { user, userProfile, logout } = useAuth();
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);

  const handleConnectApps = () => {
    navigate('/settings/connected-apps');
  };

  const handleLogout = async () => {
    await logout();
    navigate('/');
  };

  // Get display name with proper priority
  const getDisplayName = () => {
    // Priority: Backend preferred_name > Backend full_name > localStorage fallback > Email prefix
    if (userProfile?.preferred_name?.trim()) {
      return userProfile.preferred_name.trim();
    }
    
    if (userProfile?.full_name?.trim()) {
      return userProfile.full_name.trim();
    }
    
    // Fallback to localStorage for backward compatibility
    const localDisplayName = localStorage.getItem('user_display_name');
    if (localDisplayName?.trim()) {
      return localDisplayName.trim();
    }
    
    // Final fallback to email prefix
    return user?.email?.split('@')[0] || 'User';
  };

  // Get user email with backend priority
  const getUserEmail = () => {
    return userProfile?.email || user?.email || 'user@example.com';
  };

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

    if (diffDays === 0) {
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    } else if (diffDays === 1) {
      return 'Yesterday';
    } else if (diffDays < 7) {
      return `${diffDays} days ago`;
    } else {
      return date.toLocaleDateString();
    }
  };

  const getSessionPreview = (session: Session) => {
    if (session.message_count === 0) {
      return "New conversation";
    }
    return session.title || "Untitled conversation";
  };

  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation(); // Prevent session selection
    onSessionDelete(sessionId);
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
          {sessions.length > 0 ? (
            <ul className="conversations-list">
              {sessions.map((session) => (
                <li
                  key={session.id}
                  className={`conversation-item ${activeSessionId === session.id ? 'active' : ''}`}
                  onClick={() => onSessionSelect(session.id)}
                >
                  <div className="conversation-content">
                    <Send size={16} className="conversation-icon" />
                    {!isCollapsed && (
                      <div className="conversation-details">
                        <div className="conversation-preview">
                          {getSessionPreview(session)}
                        </div>
                        <div className="conversation-time">
                          {formatTimestamp(session.updated_at)}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {!isCollapsed && (
                    <button
                      className="delete-session-button"
                      onClick={(e) => handleDeleteClick(e, session.id)}
                      title="Delete conversation"
                    >
                      <Trash2 size={14} />
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : (
            <div className="no-conversations">
              {!isCollapsed && (
                <div className="no-conversations-content">
                  <p>No conversations yet.</p>
                  <small>Start a new chat to get started!</small>
                </div>
              )}
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
              <div className="user-name">{getDisplayName()}</div>
              <div className="user-email">{getUserEmail()}</div>
            </div>
          )}

          {showUserMenu && !isCollapsed && (
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
  );
};

export default Sidebar;