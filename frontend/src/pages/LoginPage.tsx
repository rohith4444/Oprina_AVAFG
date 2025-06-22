import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useSearchParams, useLocation } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Navbar from '../components/Navbar';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/AuthPages.css';

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const [searchParams] = useSearchParams();

  const { login, loginWithGoogle, user } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  // Get return path from URL params (e.g., ?return=dashboard)
  const returnPath = searchParams.get('return') || 'dashboard';

  // Check for success message from password reset
  useEffect(() => {
    if (location.state?.message) {
      setSuccessMessage(location.state.message);
      // Clear the message from location state
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  // Removed auto-redirect logic - user must manually login
  // Users coming from Thank You page should enter credentials manually

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setError('Please fill in all fields');
      return;
    }
    try {
      setError('');
      setLoading(true);
      await login(email, password);
      // Redirect to return path after successful login
      navigate(`/${returnPath}`);
    } catch (err) {
      setError('Failed to sign in. Please check your credentials.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    try {
      setError('');
      setLoading(true);
      await loginWithGoogle();
      // Supabase handles redirect, so don't navigate manually here
    } catch (err) {
      setError('Failed to sign in with Google.');
      console.error(err);
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <div className="auth-page flex-1">
        <div className="auth-container">
          <div className="auth-card">
            <h1 className="auth-title">Log in to Oprina</h1>
            <p className="auth-subtitle">Enter your details below</p>
            {successMessage && (
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
                <span>✅</span>
                <span>{successMessage}</span>
                <button
                  onClick={() => setSuccessMessage('')}
                  style={{
                    marginLeft: 'auto',
                    background: 'none',
                    border: 'none',
                    color: '#1d4ed8',
                    cursor: 'pointer',
                    fontSize: '16px',
                    padding: '0 4px'
                  }}
                  aria-label="Dismiss"
                >
                  ×
                </button>
              </div>
            )}
            {error && <div className="auth-error">{error}</div>}

            <form className="auth-form" onSubmit={handleSubmit}>
              <div className="form-group">
                <label className="form-label" htmlFor="email">
                  Email <span>*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  className="form-input"
                  placeholder="Enter your email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                  required
                />
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="password">
                  Password <span>*</span>
                </label>
                <div className="password-input-wrapper">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    id="password"
                    className="form-input"
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    disabled={loading}
                    required
                  />
                  <button
                    type="button"
                    className="password-toggle"
                    onClick={() => setShowPassword(!showPassword)}
                    tabIndex={-1}
                  >
                    {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                  </button>
                </div>
              </div>

              <div className="form-group">
                <div className="remember-me">
                  <input
                    type="checkbox"
                    id="remember"
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  />
                  <label htmlFor="remember">Remember me</label>
                  <Link to="/forgot-password" className="auth-link" style={{ marginLeft: 'auto' }}>
                    Forgot password?
                  </Link>
                </div>
              </div>

              <button
                type="submit"
                className="auth-button"
                disabled={loading}
              >
                {loading ? 'Logging in...' : 'Log in'}
              </button>
            </form>

            <div className="auth-divider">
              <span>Or continue with</span>
            </div>

            <button
              type="button"
              className="google-button"
              onClick={handleGoogleSignIn}
              disabled={loading}
            >
              <img
                src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg"
                alt="Google"
                className="google-icon"
              />
              Log in with Google
            </button>

            <div className="auth-footer">
              Don't have an account?{' '}
              <Link to="/signup" className="auth-link">
                Sign up
              </Link>
            </div>
          </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default LoginPage;
