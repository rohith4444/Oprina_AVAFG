import React from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import Button from '../components/Button';
import '../styles/AuthPages.css';

const ThankYou: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="auth-page">
      <Navbar />
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
            onClick={() => navigate('/login')}
            className="mt-6"
          >
            Log In
          </Button>
        </div>
      </div>
      <Footer />
    </div>
  );
};

export default ThankYou;