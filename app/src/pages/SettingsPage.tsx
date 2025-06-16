import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Mail, Calendar, HardDrive, User, Lock, LogOut, Trash2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import Button from '../components/Button';
import MinimalFooter from '../components/MinimalFooter';
import '../styles/SettingsPage.css';

type TabType = 'profile' | 'connected-apps' | 'account';

interface ProfileFormData {
  fullName: string;
  preferredName: string;
  workType: string;
  preferences: string;
}

interface PasswordFormData {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const SettingsPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const [activeTab, setActiveTab] = useState<TabType>('profile');

  const [profileData, setProfileData] = useState<ProfileFormData>({
    fullName: user?.email?.split('@')[0] || '',
    preferredName: '',
    workType: '',
    preferences: '',
  });

  const [passwordData, setPasswordData] = useState<PasswordFormData>({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  const [connectedServices, setConnectedServices] = useState({
    gmail: false,
    drive: false,
    calendar: false,
  });

  const handleProfileSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const displayName = profileData.preferredName || profileData.fullName;
    localStorage.setItem('user_name', displayName);
    navigate('/dashboard');
  };

  const handlePasswordSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  const handleServiceConnect = (service: keyof typeof connectedServices) => {
    setConnectedServices(prev => ({
      ...prev,
      [service]: !prev[service],
    }));
  };

  const handleLogoutAllDevices = () => {
  };

  const handleDeleteAccount = () => {
  };

  return (
    <div className="min-h-screen flex flex-col">
      <div className="settings-page flex-1">
        <div className="settings-container">
        <button onClick={() => navigate('/dashboard')} className="back-button">
          <ArrowLeft size={20} />
          <span>Back to Dashboard</span>
        </button>

        <h1 className="settings-title">Settings</h1>

        <div className="settings-layout">
          <nav className="settings-sidebar">
            <button className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`} onClick={() => setActiveTab('profile')}>
              <User size={20} />
              <span>Profile</span>
            </button>
            <button className={`tab-button ${activeTab === 'connected-apps' ? 'active' : ''}`} onClick={() => setActiveTab('connected-apps')}>
              <HardDrive size={20} />
              <span>Connected Apps</span>
            </button>
            <button className={`tab-button ${activeTab === 'account' ? 'active' : ''}`} onClick={() => setActiveTab('account')}>
              <Lock size={20} />
              <span>Account</span>
            </button>
          </nav>

          <div className="settings-content">
            {activeTab === 'profile' && (
              <div className="settings-section">
                <h2>Profile Settings</h2>
                <form onSubmit={handleProfileSubmit}>
                  <div className="form-group">
                    <label htmlFor="fullName">Full Name</label>
                    <input
                      type="text"
                      id="fullName"
                      value={profileData.fullName}
                      onChange={(e) => setProfileData({ ...profileData, fullName: e.target.value })}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="preferredName">Preferred Name</label>
                    <input
                      type="text"
                      id="preferredName"
                      value={profileData.preferredName}
                      onChange={(e) => setProfileData({ ...profileData, preferredName: e.target.value })}
                    />
                  </div>

                  <div className="form-group">
                    <label htmlFor="workType">What best describes your work?</label>
                    <select
                      id="workType"
                      value={profileData.workType}
                      onChange={(e) => setProfileData({ ...profileData, workType: e.target.value })}
                    >
                      <option value="">Select an option</option>
                      <option value="developer">Software Developer</option>
                      <option value="designer">Designer</option>
                      <option value="manager">Manager</option>
                      <option value="student">Student</option>
                      <option value="other">Other</option>
                    </select>
                  </div>

                  <div className="form-group">
                    <label htmlFor="preferences">
                      What personal preferences should Oprina consider in responses?
                    </label>
                    <textarea
                      id="preferences"
                      value={profileData.preferences}
                      onChange={(e) => setProfileData({ ...profileData, preferences: e.target.value })}
                      rows={4}
                      placeholder="e.g., Prefer detailed explanations, focus on code examples, etc."
                    />
                  </div>

                  <Button type="submit" variant="primary">
                    Save Changes
                  </Button>
                </form>
              </div>
            )}

            {activeTab === 'connected-apps' && (
              <div className="settings-section">
                <h2>Connected Applications</h2>
                <div className="connected-apps-list">
                  <div className="service-item">
                    <div className="service-info">
                      <Mail size={24} />
                      <div>
                        <h3>Gmail</h3>
                        <p>Access and manage your emails</p>
                      </div>
                    </div>
                    <Button
                      variant={connectedServices.gmail ? 'outline' : 'primary'}
                      onClick={() => handleServiceConnect('gmail')}
                    >
                      {connectedServices.gmail ? 'Connected' : 'Connect'}
                    </Button>
                  </div>

                  <div className="service-item">
                    <div className="service-info">
                      <HardDrive size={24} />
                      <div>
                        <h3>Google Drive</h3>
                        <p>Access your files and documents</p>
                      </div>
                    </div>
                    <Button
                      variant={connectedServices.drive ? 'outline' : 'primary'}
                      onClick={() => handleServiceConnect('drive')}
                    >
                      {connectedServices.drive ? 'Connected' : 'Connect'}
                    </Button>
                  </div>

                  <div className="service-item">
                    <div className="service-info">
                      <Calendar size={24} />
                      <div>
                        <h3>Google Calendar</h3>
                        <p>Manage your schedule and events</p>
                      </div>
                    </div>
                    <Button
                      variant={connectedServices.calendar ? 'outline' : 'primary'}
                      onClick={() => handleServiceConnect('calendar')}
                    >
                      {connectedServices.calendar ? 'Connected' : 'Connect'}
                    </Button>
                  </div>
                </div>
              </div>
            )}

            {activeTab === 'account' && (
              <div className="settings-section">
                <h2>Account Settings</h2>

                <div className="account-actions">
                  <div className="action-group">
                    <h3>Session Management</h3>
                    <Button
                      variant="outline"
                      onClick={handleLogoutAllDevices}
                      icon={<LogOut size={18} />}
                    >
                      Log out of all devices
                    </Button>
                  </div>

                  <div className="action-group">
                    <h3>Change Password</h3>
                    <form onSubmit={handlePasswordSubmit} className="password-form">
                      <div className="form-group">
                        <label htmlFor="oldPassword">Old Password</label>
                        <input
                          type="password"
                          id="oldPassword"
                          value={passwordData.oldPassword}
                          onChange={(e) => setPasswordData({ ...passwordData, oldPassword: e.target.value })}
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="newPassword">New Password</label>
                        <input
                          type="password"
                          id="newPassword"
                          value={passwordData.newPassword}
                          onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                        />
                      </div>

                      <div className="form-group">
                        <label htmlFor="confirmPassword">Confirm New Password</label>
                        <input
                          type="password"
                          id="confirmPassword"
                          value={passwordData.confirmPassword}
                          onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                        />
                      </div>

                      <Button type="submit" variant="primary">
                        Update Password
                      </Button>
                    </form>
                  </div>

                  <div className="action-group danger-zone">
                    <h3>Danger Zone</h3>
                    <Button
                      variant="outline"
                      className="delete-account"
                      onClick={handleDeleteAccount}
                      icon={<Trash2 size={18} />}
                    >
                      Delete Account
                    </Button>
                    <p className="danger-note">
                      This action cannot be undone. All your data will be permanently deleted.
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default SettingsPage;
