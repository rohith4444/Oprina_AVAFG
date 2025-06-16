import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';

const GmailAuthHandler: React.FC = () => {
  const navigate = useNavigate();

  useEffect(() => {
    const hash = window.location.hash;
    const params = new URLSearchParams(hash.substring(1));
    const token = params.get('access_token');

    if (token) {
      localStorage.setItem('gmail_token', token);
      localStorage.setItem('gmail_connected', 'true');
    }

    // Clean the URL and redirect to dashboard
    navigate('/dashboard', { replace: true });
  }, [navigate]);

  return <p>Connecting to Gmail...</p>;
};

export default GmailAuthHandler;
