import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/AuthPages.css';

const ForgotPasswordPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [emailSent, setEmailSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email) {
      setError('Please enter your email address');
      return;
    }

    setLoading(true);
    setError('');
    setMessage('');

    try {
      const { error } = await supabase.auth.resetPasswordForEmail(email, {
        redirectTo: `${window.location.origin}/reset-password`,
      });

      if (error) {
        throw error;
      }

      setEmailSent(true);
      setMessage(`Password reset instructions have been sent to ${email}`);
    } catch (err: any) {
      setError(err.message || 'Failed to send reset email');
    } finally {
      setLoading(false);
    }
  };

  if (emailSent) {
    return (
      <div className="auth-page">
        <div className="auth-container">
          <div className="auth-card">
            {/* Header */}
            <div className="login-header">
              <div className="logo-section">
                <div className="logo">
                  <svg width="40" height="40" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="24" cy="24" r="20" stroke="#3B82F6" strokeWidth="3" fill="none"/>
                    <circle cx="24" cy="24" r="6" fill="#3B82F6"/>
                    <path d="M24 4 L26 8 L24 12 L22 8 Z" fill="#3B82F6"/>
                    <path d="M44 24 L40 26 L36 24 L40 22 Z" fill="#3B82F6"/>
                  </svg>
                </div>
                <h1 className="logo-text">Oprina</h1>
              </div>
              <h2 className="auth-title">Check Your Email</h2>
              <p className="auth-subtitle">We've sent password reset instructions to your email</p>
            </div>

            {/* Success Message */}
            <div className="form-container">
              {message && (
                <div style={{
                  backgroundColor: '#dbeafe',
                  border: '1px solid #3b82f6',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  marginBottom: '20px',
                  color: '#1d4ed8',
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span>📧</span>
                  <span>{message}</span>
                </div>
              )}

              <div style={{
                textAlign: 'center',
                padding: '20px',
                backgroundColor: '#f8fafc',
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>📧</div>
                <h3 style={{ margin: '0 0 8px 0', color: '#1f2937' }}>Email Sent!</h3>
                <p style={{ margin: '0', color: '#6b7280', fontSize: '14px' }}>
                  Click the link in your email to reset your password. The link will expire in 1 hour.
                </p>
              </div>

              <div style={{
                textAlign: 'center',
                fontSize: '14px',
                color: '#6b7280'
              }}>
                <p>Didn't receive an email? Check your spam folder or 
                  <button 
                    onClick={() => {
                      setEmailSent(false);
                      setMessage('');
                      setEmail('');
                    }}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#3b82f6',
                      textDecoration: 'underline',
                      cursor: 'pointer',
                      marginLeft: '4px'
                    }}
                  >
                    try again
                  </button>
                </p>
              </div>

              <div className="auth-footer">
                <Link to="/login" className="auth-link">
                  ← Back to Login
                </Link>
              </div>
            </div>
          </div>
        </div>
        <MinimalFooter />
      </div>
    );
  }

  return (
    <div className="auth-page">
      <div className="auth-container">
        <div className="auth-card">
          {/* Header */}
          <div className="login-header">
            <div className="logo-section">
              <div className="logo">
                <svg width="40" height="40" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="24" cy="24" r="20" stroke="#3B82F6" strokeWidth="3" fill="none"/>
                  <circle cx="24" cy="24" r="6" fill="#3B82F6"/>
                  <path d="M24 4 L26 8 L24 12 L22 8 Z" fill="#3B82F6"/>
                  <path d="M44 24 L40 26 L36 24 L40 22 Z" fill="#3B82F6"/>
                </svg>
              </div>
              <h1 className="logo-text">Oprina</h1>
            </div>
                          <h2 className="auth-title">Forgot Password?</h2>
              <p className="auth-subtitle">Enter your email address and we'll send you a link to reset your password</p>
          </div>

          {/* Form */}
          <div className="form-container">
            <form onSubmit={handleSubmit} className="auth-form">
              {error && (
                <div className="auth-error">
                  {error}
                </div>
              )}

              <div className="form-group">
                <label htmlFor="email" className="form-label">
                  Email Address
                </label>
                <input
                  type="email"
                  id="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="form-input"
                  placeholder="Enter your email address"
                  required
                  disabled={loading}
                />
              </div>

              <button 
                type="submit" 
                className="auth-button"
                disabled={loading}
              >
                {loading ? 'Sending Reset Link...' : 'Send Reset Link'}
              </button>
            </form>

            <div className="auth-footer">
              <Link to="/login" className="auth-link">
                ← Back to Login
              </Link>
              <br />
              <Link to="/signup" className="auth-link">
                Don't have an account? Sign up
              </Link>
            </div>
          </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default ForgotPasswordPage; 