import React, { useState } from 'react';
import {
  Settings,
  LogOut,
  User,
  MessageSquarePlus,
  ChevronLeft,
  //Send,
  Plug,
  Trash2,
  Edit3,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../supabaseClient';
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
  onSessionUpdate?: (sessionId: string, newTitle: string) => void;
  onCollapseChange?: (isCollapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  className = '', 
  sessions, 
  activeSessionId,
  onNewChat, 
  onSessionSelect,
  onSessionDelete,
  onSessionUpdate,
  onCollapseChange
}) => {
  const { user, userProfile, logout } = useAuth();
  const navigate = useNavigate();
  const [isCollapsed, setIsCollapsed] = useState(true); // Default to collapsed on login
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingTitle, setEditingTitle] = useState<string>('');

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
  // Always use session.title (now comes from backend with smart generation)
  return session.title || "New Chat";
};

  const handleDeleteClick = (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation(); // Prevent session selection
    onSessionDelete(sessionId);
  };

  const handleEditClick = (e: React.MouseEvent, session: Session) => {
  e.stopPropagation(); // Prevent session selection
  setEditingSessionId(session.id);
  setEditingTitle(session.title);
};

  const handleTitleSave = async (sessionId: string) => {
    if (!editingTitle.trim()) {
      setEditingSessionId(null);
      return;
    }

    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;

      const response = await fetch(`${import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'}/api/v1/sessions/${sessionId}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ title: editingTitle.trim() })
      });

      if (response.ok) {
        // Use the callback to update parent state instead of setSessions
        if (onSessionUpdate) {
          onSessionUpdate(sessionId, editingTitle.trim());
        }
        console.log('✅ Session title updated');
      } else {
        console.error('Failed to update session title');
      }
    } catch (error) {
      console.error('Error updating session title:', error);
    } finally {
      setEditingSessionId(null);
      setEditingTitle('');
    }
  };

  const handleTitleCancel = () => {
  setEditingSessionId(null);
  setEditingTitle('');
};

  const handleTitleKeyDown = (e: React.KeyboardEvent, sessionId: string) => {
  if (e.key === 'Enter') {
    handleTitleSave(sessionId);
  } else if (e.key === 'Escape') {
    handleTitleCancel();
  }
};

  const toggleSidebar = () => {
    const newCollapsedState = !isCollapsed;
    setIsCollapsed(newCollapsedState);
    onCollapseChange?.(newCollapsedState);
  };

  return (
    <div className={`sidebar ${isCollapsed ? 'collapsed' : ''} ${className}`}>
      <div className="sidebar-header">
        <div className="logo-section" onClick={() => navigate('/')} role="button" tabIndex={0}>
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
                  onClick={() => editingSessionId !== session.id && onSessionSelect(session.id)}
                >
                  <div className="conversation-content">
                    {/*<Send size={16} className="conversation-icon" />*/}
                    {!isCollapsed && (
                      <div className="conversation-details">
                        <div className="conversation-preview">
                          {editingSessionId === session.id ? (
                            <input
                              type="text"
                              value={editingTitle}
                              onChange={(e) => setEditingTitle(e.target.value)}
                              onBlur={() => handleTitleSave(session.id)}
                              onKeyDown={(e) => handleTitleKeyDown(e, session.id)}
                              className="session-title-input"
                              autoFocus
                              maxLength={20}
                            />
                          ) : (
                            <span className="session-title-text">
                              {getSessionPreview(session)}
                            </span>
                          )}
                        </div>
                        <div className="conversation-time">
                          {formatTimestamp(session.updated_at)}
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {!isCollapsed && (
                    <div className="session-actions">
                      {editingSessionId !== session.id && (
                        <button
                          className="edit-session-button"
                          onClick={(e) => handleEditClick(e, session)}
                          title="Edit title"
                        >
                          <Edit3 size={12} />
                        </button>
                      )}
                      <button
                        className="delete-session-button"
                        onClick={(e) => handleDeleteClick(e, session.id)}
                        title="Delete conversation"
                      >
                        <Trash2 size={14} />
                      </button>
                    </div>
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
              <button className="menu-item" onClick={() => navigate('/support')}>
                {/*<Send size={16} >*/}
                <span>Contact Support</span>
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