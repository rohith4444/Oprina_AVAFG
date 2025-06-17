import React from 'react';
import { Link } from 'react-router-dom';
import { Mail } from 'lucide-react';
import Navbar from '../components/Navbar';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/AuthPages.css';

const EmailConfirmationPending: React.FC = () => {
  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="auth-page flex-1">
        <div className="auth-container">
        <div className="auth-card">
          <div className="confirmation-icon">
            <Mail size={48} className="text-primary-blue" />
          </div>
          <h1 className="auth-title">Check Your Email</h1>
          <p className="auth-subtitle">
            We've sent a confirmation link to your email. Please click the link to activate your account.
          </p>
          <div className="auth-footer">
            Didn't receive the email?{' '}
            <Link to="/signup" className="auth-link">
              Try again
            </Link>
          </div>
        </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default EmailConfirmationPending;