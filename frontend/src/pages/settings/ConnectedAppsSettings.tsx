import React, { useState } from 'react';
import { Mail, Calendar } from 'lucide-react';
import Button from '../../components/Button';

// Official Gmail SVG
const GmailIcon = () => (
  <svg width="24" height="24" viewBox="0 0 48 48" fill="none">
    <rect width="48" height="48" rx="8" fill="#fff"/>
    <path d="M8 14v20a2 2 0 002 2h28a2 2 0 002-2V14l-16 12L8 14z" fill="#EA4335"/>
    <path d="M8 14l16 12 16-12" fill="#34A853"/>
    <path d="M8 14v20a2 2 0 002 2h28a2 2 0 002-2V14" stroke="#4285F4" strokeWidth="2"/>
  </svg>
);

// Official Google Calendar SVG
const CalendarIcon = () => (
  <svg width="24" height="24" viewBox="0 0 48 48" fill="none">
    <rect width="48" height="48" rx="8" fill="#fff"/>
    <rect x="8" y="14" width="32" height="26" rx="2" fill="#4285F4"/>
    <rect x="8" y="8" width="32" height="8" fill="#34A853"/>
    <rect x="8" y="8" width="32" height="32" rx="4" stroke="#4285F4" strokeWidth="2"/>
    <rect x="16" y="22" width="16" height="12" rx="2" fill="#fff"/>
  </svg>
);

const ConnectedAppsSettings: React.FC = () => {
  const [connectedServices, setConnectedServices] = useState({
    gmail: false,
    calendar: false,
  });

  const handleServiceConnect = (service: keyof typeof connectedServices) => {
    setConnectedServices(prev => ({
      ...prev,
      [service]: !prev[service],
    }));
  };

  return (
    <div className="settings-section">
      <h2>Connected Applications</h2>
      <div className="connected-apps-list">
        <div className="service-item">
          <div className="service-info">
            <Mail size={24} />
            <div>
              <h3>Gmail</h3>
              <p>Access and manage your emails</p>
            </div>
          </div>
          <Button
            variant={connectedServices.gmail ? 'outline' : 'primary'}
            onClick={() => handleServiceConnect('gmail')}
          >
            {connectedServices.gmail ? 'Connected' : 'Connect'}
          </Button>
        </div>

        <div className="service-item">
          <div className="service-info">
            <Calendar size={24} />
            <div>
              <h3>Google Calendar</h3>
              <p>Manage your schedule and events</p>
            </div>
          </div>
          <Button
            variant={connectedServices.calendar ? 'outline' : 'primary'}
            onClick={() => handleServiceConnect('calendar')}
          >
            {connectedServices.calendar ? 'Connected' : 'Connect'}
          </Button>
        </div>
      </div>
    </div>
  );
};

export default ConnectedAppsSettings;