import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams } from 'react-router-dom';
import { supabase } from '../supabaseClient';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/AuthPages.css';

const ResetPasswordPage: React.FC = () => {
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [isValidToken, setIsValidToken] = useState(true);
  
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    // Check if we have the necessary tokens in the URL hash (Supabase format)
    const hashParams = new URLSearchParams(window.location.hash.substring(1));
    const accessToken = hashParams.get('access_token');
    const type = hashParams.get('type');
    
    // Also check query parameters as fallback
    const queryAccessToken = searchParams.get('access_token');
    const queryType = searchParams.get('type');
    
    const validToken = (accessToken && type === 'recovery') || (queryAccessToken && queryType === 'recovery');
    
    if (!validToken) {
      setIsValidToken(false);
      setError('Invalid or expired reset link. Please request a new password reset.');
    } else {
      // Set the session with the tokens from the URL
      const sessionToken = accessToken || queryAccessToken;
      if (sessionToken) {
        const refreshToken = hashParams.get('refresh_token') || searchParams.get('refresh_token');
        const setSessionAsync = async () => {
          try {
            const { data, error } = await supabase.auth.setSession({
              access_token: sessionToken,
              refresh_token: refreshToken || ''
            });
            
            if (error) {
              console.error('Session error:', error);
              setIsValidToken(false);
              setError('Invalid or expired reset link. Please request a new password reset.');
            }
          } catch (err) {
            console.error('Failed to set session:', err);
            setIsValidToken(false);
            setError('Invalid or expired reset link. Please request a new password reset.');
          }
        };
        
        setSessionAsync();
      }
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!password || !confirmPassword) {
      setError('Please fill in all fields');
      return;
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters long');
      return;
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }

    setLoading(true);
    setError('');

    try {
      // Update the user's password
      const { error } = await supabase.auth.updateUser({
        password: password
      });

      if (error) {
        throw error;
      }

      setSuccess(true);
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        navigate('/login', { 
          state: { message: 'Password updated successfully! Please log in with your new password.' }
        });
      }, 3000);

    } catch (err: any) {
      setError(err.message || 'Failed to update password');
    } finally {
      setLoading(false);
    }
  };

  if (!isValidToken) {
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
              <h2 className="auth-title">Invalid Reset Link</h2>
              <p className="auth-subtitle">This password reset link is invalid or has expired</p>
            </div>

            <div className="form-container">
              {error && (
                <div style={{
                  backgroundColor: '#fef2f2',
                  border: '1px solid #f87171',
                  borderRadius: '8px',
                  padding: '12px 16px',
                  marginBottom: '20px',
                  color: '#dc2626',
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px'
                }}>
                  <span>⚠️</span>
                  <span>{error}</span>
                </div>
              )}

              <div style={{
                textAlign: 'center',
                padding: '20px',
                backgroundColor: '#f8fafc',
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>⚠️</div>
                <h3 style={{ margin: '0 0 8px 0', color: '#1f2937' }}>Link Expired</h3>
                <p style={{ margin: '0', color: '#6b7280', fontSize: '14px' }}>
                  Password reset links expire after 1 hour for security. Please request a new reset link.
                </p>
              </div>

              <div className="auth-footer">
                <Link to="/forgot-password" className="auth-link">
                  Request New Reset Link
                </Link>
                <br />
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

  if (success) {
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
              <h2 className="auth-title">Password Updated!</h2>
              <p className="auth-subtitle">Your password has been successfully updated</p>
            </div>

            <div className="form-container">
              <div style={{
                textAlign: 'center',
                padding: '20px',
                backgroundColor: '#f0fdf4',
                borderRadius: '8px',
                marginBottom: '20px'
              }}>
                <div style={{ fontSize: '48px', marginBottom: '16px' }}>✅</div>
                <h3 style={{ margin: '0 0 8px 0', color: '#1f2937' }}>Success!</h3>
                <p style={{ margin: '0', color: '#6b7280', fontSize: '14px' }}>
                  Your password has been updated. Redirecting you to login...
                </p>
              </div>

              <div className="auth-footer">
                <Link to="/login" className="auth-link">
                  Go to Login
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
            <h2 className="auth-title">Reset Your Password</h2>
            <p className="auth-subtitle">Enter your new password below</p>
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
                <label htmlFor="password" className="form-label">
                  New Password
                </label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="form-input"
                    placeholder="Enter your new password"
                    required
                    disabled={loading}
                    minLength={6}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <label htmlFor="confirmPassword" className="form-label">
                  Confirm New Password
                </label>
                <div className="password-input-wrapper">
                  <input
                    type={showConfirmPassword ? 'text' : 'password'}
                    id="confirmPassword"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className="form-input"
                    placeholder="Confirm your new password"
                    required
                    disabled={loading}
                    minLength={6}
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    tabIndex={-1}
                  >
                    {showConfirmPassword ? '🙈' : '👁️'}
                  </button>
                </div>
              </div>

              <div style={{
                fontSize: '12px',
                color: '#6b7280',
                marginBottom: '20px'
              }}>
                Password must be at least 6 characters long
              </div>

              <button 
                type="submit" 
                className="auth-button"
                disabled={loading}
              >
                {loading ? 'Updating Password...' : 'Update Password'}
              </button>
            </form>

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
};

export default ResetPasswordPage; 