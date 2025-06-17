import React, { useState, useEffect } from 'react';
import { Mail, Calendar, AlertCircle, Loader2 } from 'lucide-react';
import Button from '../../components/Button';
import { 
  getConnectionStatus, 
  connectGmail, 
  connectCalendar, 
  disconnectService, 
  ConnectionStatus 
} from '../../services/oauthApi';

const ConnectedAppsSettings: React.FC = () => {
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus>({
    gmail: { connected: false },
    calendar: { connected: false },
  });
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Load connection status on component mount
  useEffect(() => {
    loadConnectionStatus();
  }, []);

  const loadConnectionStatus = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('🔄 Loading connection status...');
      const status = await getConnectionStatus();
      
      setConnectionStatus(status);
      console.log('✅ Connection status loaded:', status);
      
    } catch (err: any) {
      console.error('❌ Failed to load connection status:', err);
      setError(err.message || 'Failed to load connection status');
    } finally {
      setLoading(false);
    }
  };

  const handleGmailConnect = async () => {
    try {
      setActionLoading('gmail');
      setError(null);
      
      if (connectionStatus.gmail.connected) {
        // Disconnect Gmail
        await disconnectService('gmail');
        await loadConnectionStatus(); // Refresh status
      } else {
        // Connect Gmail (this will redirect to Google OAuth)
        await connectGmail();
        // Note: User will be redirected, so component will unmount
      }
      
    } catch (err: any) {
      console.error('❌ Gmail action failed:', err);
      setError(err.message || 'Failed to connect Gmail');
    } finally {
      setActionLoading(null);
    }
  };

  const handleCalendarConnect = async () => {
    try {
      setActionLoading('calendar');
      setError(null);
      
      if (connectionStatus.calendar.connected) {
        // Disconnect Calendar
        await disconnectService('calendar');
        await loadConnectionStatus(); // Refresh status
      } else {
        // Connect Calendar (this will redirect to Google OAuth)
        await connectCalendar();
        // Note: User will be redirected, so component will unmount
      }
      
    } catch (err: any) {
      console.error('❌ Calendar action failed:', err);
      setError(err.message || 'Failed to connect Calendar');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="settings-section">
        <h2>Connected Applications</h2>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="animate-spin mr-2" size={20} />
          <span>Loading connection status...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-section">
      <h2>Connected Applications</h2>
      
      {error && (
        <div className="error-message mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex items-center">
          <AlertCircle className="text-red-500 mr-2" size={20} />
          <span className="text-red-700">{error}</span>
          <button 
            onClick={() => setError(null)} 
            className="ml-auto text-red-500 hover:text-red-700"
          >
            ×
          </button>
        </div>
      )}
      
      <div className="connected-apps-list">
        {/* Gmail Service */}
        <div className="service-item">
          <div className="service-info">
            <Mail size={24} />
            <div>
              <h3>Gmail</h3>
              <p>Access and manage your emails</p>
              {connectionStatus.gmail.connected && connectionStatus.gmail.email && (
                <p className="text-sm text-gray-600 mt-1">
                  Connected as: {connectionStatus.gmail.email}
                </p>
              )}
            </div>
          </div>
          <Button
            variant={connectionStatus.gmail.connected ? 'outline' : 'primary'}
            onClick={handleGmailConnect}
            disabled={actionLoading === 'gmail'}
          >
            {actionLoading === 'gmail' ? (
              <>
                <Loader2 className="animate-spin mr-2" size={16} />
                {connectionStatus.gmail.connected ? 'Disconnecting...' : 'Connecting...'}
              </>
            ) : (
              connectionStatus.gmail.connected ? 'Disconnect' : 'Connect'
            )}
          </Button>
        </div>

        {/* Calendar Service */}
        <div className="service-item">
          <div className="service-info">
            <Calendar size={24} />
            <div>
              <h3>Google Calendar</h3>
              <p>Manage your schedule and events</p>
              {connectionStatus.calendar.connected && connectionStatus.calendar.email && (
                <p className="text-sm text-gray-600 mt-1">
                  Connected as: {connectionStatus.calendar.email}
                </p>
              )}
            </div>
          </div>
          <Button
            variant={connectionStatus.calendar.connected ? 'outline' : 'primary'}
            onClick={handleCalendarConnect}
            disabled={actionLoading === 'calendar'}
          >
            {actionLoading === 'calendar' ? (
              <>
                <Loader2 className="animate-spin mr-2" size={16} />
                {connectionStatus.calendar.connected ? 'Disconnecting...' : 'Connecting...'}
              </>
            ) : (
              connectionStatus.calendar.connected ? 'Disconnect' : 'Connect'
            )}
          </Button>
        </div>
      </div>
      
      <div className="mt-4">
        <button 
          onClick={loadConnectionStatus}
          className="text-sm text-blue-600 hover:text-blue-800"
          disabled={loading}
        >
          🔄 Refresh Status
        </button>
      </div>
    </div>
  );
};

export default ConnectedAppsSettings;