import React, { useEffect, useState } from 'react';
import '../styles/GmailPreview.css';

interface GmailMessage {
  id: string;
  snippet: string;
  subject: string;
  sender: string;
}

const GmailPreview: React.FC<{ accessToken: string }> = ({ accessToken }) => {
  const [emails, setEmails] = useState<GmailMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchEmails = async () => {
      try {
        const messageListRes = await fetch(
          'https://gmail.googleapis.com/gmail/v1/users/me/messages?maxResults=5',
          {
            headers: {
              Authorization: `Bearer ${accessToken}`,
            },
          }
        );

        const messageListData = await messageListRes.json();
        const messages = messageListData.messages || [];

        const detailedMessages = await Promise.all(
          messages.map(async (msg: { id: string }) => {
            const detailRes = await fetch(
              `https://gmail.googleapis.com/gmail/v1/users/me/messages/${msg.id}`,
              {
                headers: {
                  Authorization: `Bearer ${accessToken}`,
                },
              }
            );
            const detail = await detailRes.json();

            const headers = detail.payload.headers;
            const subject = headers.find((h: any) => h.name === 'Subject')?.value || '(No Subject)';
            const sender = headers.find((h: any) => h.name === 'From')?.value || '(Unknown Sender)';

            return {
              id: detail.id,
              snippet: detail.snippet,
              subject,
              sender,
            };
          })
        );

        setEmails(detailedMessages);
      } catch (err) {
        console.error('Error fetching Gmail messages:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchEmails();
  }, [accessToken]);

  if (loading) return <div className="gmail-preview">Loading Gmail...</div>;

  return (
    <div className="gmail-preview">
      <h3 className="gmail-title">Recent Emails</h3>
      <ul className="gmail-list">
        {emails.map((email) => (
          <li key={email.id} className="gmail-item">
            <strong>{email.sender}</strong>
            <div className="gmail-subject">{email.subject}</div>
            <p className="gmail-snippet">{email.snippet}</p>
          </li>
        ))}
      </ul>
    </div>
  );
};

export default GmailPreview;
