import React, { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';
import UnauthenticatedNavbar from '../components/UnauthenticatedNavbar';
import MinimalFooter from '../components/MinimalFooter';
import Button from '../components/Button';
import { useAuth } from '../context/AuthContext';
import '../styles/AuthPages.css';

const ThankYou: React.FC = () => {
  const navigate = useNavigate();
  const { logout } = useAuth();

  // Clear any existing user session when this page loads
  useEffect(() => {
    const clearSession = async () => {
      try {
        // Clear any existing authentication state
        await logout();
        console.log('🧹 Session cleared on Thank You page');
      } catch (error) {
        console.log('No existing session to clear');
      }
    };

    clearSession();
  }, [logout]);

  const handleLoginClick = () => {
    // Navigate to login page - user will need to manually enter credentials
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex flex-col">
      <UnauthenticatedNavbar />
      <div className="auth-page flex-1">
        <div className="auth-container">
        <div className="auth-card">
          <div className="confirmation-icon">
            <CheckCircle size={48} className="text-primary-green" />
          </div>
          <h1 className="auth-title">Thank You!</h1>
          <p className="auth-subtitle">
            Your account has been successfully confirmed.
          </p>
          <Button
            variant="primary"
            fullWidth
            onClick={handleLoginClick}
            className="mt-6"
          >
            Log In
          </Button>
        </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default ThankYou;