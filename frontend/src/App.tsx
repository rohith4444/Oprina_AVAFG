import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import HomePage from './pages/HomePage';
import LoginPage from './pages/LoginPage';
import SignupPage from './pages/SignupPage';
import DashboardPage from './pages/DashboardPage';
import ContactPage from './pages/ContactPage';
import SettingsLayout from './pages/settings/SettingsLayout';
import ProfileSettings from './pages/settings/ProfileSettings';
import ConnectedAppsSettings from './pages/settings/ConnectedAppsSettings';
import AccountSettings from './pages/settings/AccountSettings';
import TermsPage from './pages/TermsPage';
import PrivacyPage from './pages/PrivacyPage';
import EmailConfirmationPending from './pages/EmailConfirmationPending';
import ThankYou from './pages/ThankYou';
import ProtectedRoute from './components/ProtectedRoute';
import './App.css';

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />
          <Route path="/terms" element={<TermsPage />} />
          <Route path="/privacy" element={<PrivacyPage />} />
          <Route path="/email-confirmation" element={<EmailConfirmationPending />} />
          <Route path="/thank-you" element={<ThankYou />} />
          <Route 
            path="/dashboard" 
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/contact" 
            element={
              <ProtectedRoute>
                <ContactPage />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/settings" 
            element={
              <ProtectedRoute>
                <SettingsLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/settings/profile" replace />} />
            <Route path="profile" element={<ProfileSettings />} />
            <Route path="connected-apps" element={<ConnectedAppsSettings />} />
            <Route path="account" element={<AccountSettings />} />
          </Route>
        </Routes>
      </Router>
    </AuthProvider>
  );
}

export default App;