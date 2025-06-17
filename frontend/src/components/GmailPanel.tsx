/* eslint-disable @typescript-eslint/no-unused-vars */
import React, { useState, useEffect } from 'react';
import { Mail, Search } from 'lucide-react';
import '../styles/GmailPanel.css';

interface Email {
  id: string;
  from: string;
  subject: string;
  snippet: string;
  date: string;
  unread: boolean;
}

const GmailPanel: React.FC = () => {
  const [emails, setEmails] = useState<Email[]>([]);
  const [selectedEmail, setSelectedEmail] = useState<Email | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // TODO: Connect to your Gmail Agent in Phase 5
    // For now, load from localStorage or show placeholder
    const token = localStorage.getItem('gmail_token');
    if (token) {
      fetchEmails(token);
    }
  }, []);

  const fetchEmails = async (token: string) => {
    try {
      // This will be replaced with your Gmail Agent API call
      const response = await fetch('/api/gmail/emails', {
        headers: { Authorization: `Bearer ${token}` }
      });
      const data = await response.json();
      setEmails(data.emails || []);
    } catch (error) {
      console.error('Failed to fetch emails:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="gmail-panel-container">
        <div className="gmail-header">
          <Mail size={20} />
          <h3>Gmail</h3>
        </div>
        <div className="gmail-loading">
          <div className="loading-spinner"></div>
          <p>Loading emails...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="gmail-panel-container">
      <div className="gmail-header">
        <Mail size={20} />
        <h3>Gmail</h3>
        <button className="gmail-refresh">
          <Search size={16} />
        </button>
      </div>

      {selectedEmail ? (
        <div className="email-detail">
          <button 
            className="back-button"
            onClick={() => setSelectedEmail(null)}
          >
            ← Back to inbox
          </button>
          <div className="email-content">
            <h4>{selectedEmail.subject}</h4>
            <p className="email-from">From: {selectedEmail.from}</p>
            <p className="email-date">{selectedEmail.date}</p>
            <div className="email-body">
              {selectedEmail.snippet}
            </div>
          </div>
        </div>
      ) : (
        <div className="emails-list">
          {emails.length === 0 ? (
            <div className="no-emails">
              <Mail size={48} />
              <p>No emails found</p>
              <small>Try saying "Check my emails"</small>
            </div>
          ) : (
            emails.map(email => (
              <div
                key={email.id}
                className={`email-item ${email.unread ? 'unread' : ''}`}
                onClick={() => setSelectedEmail(email)}
              >
                <div className="email-from">{email.from}</div>
                <div className="email-subject">{email.subject}</div>
                <div className="email-snippet">{email.snippet}</div>
                <div className="email-date">{email.date}</div>
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default GmailPanel;