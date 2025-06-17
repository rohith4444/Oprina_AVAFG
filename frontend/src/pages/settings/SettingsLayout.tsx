import React from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import { ArrowLeft, User, Lock, HardDrive } from 'lucide-react';
import MinimalFooter from '../../components/MinimalFooter';
import '../../styles/SettingsPage.css';

const SettingsLayout: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const getActiveTab = () => {
    const path = location.pathname;
    if (path.includes('/profile')) return 'profile';
    if (path.includes('/connected-apps')) return 'connected-apps';
    if (path.includes('/account')) return 'account';
    return 'profile'; // default
  };

  const activeTab = getActiveTab();

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
              <button 
                className={`tab-button ${activeTab === 'profile' ? 'active' : ''}`} 
                onClick={() => navigate('/settings/profile')}
              >
                <User size={20} />
                <span>Profile</span>
              </button>
              <button 
                className={`tab-button ${activeTab === 'connected-apps' ? 'active' : ''}`} 
                onClick={() => navigate('/settings/connected-apps')}
              >
                <HardDrive size={20} />
                <span>Connected Apps</span>
              </button>
              <button 
                className={`tab-button ${activeTab === 'account' ? 'active' : ''}`} 
                onClick={() => navigate('/settings/account')}
              >
                <Lock size={20} />
                <span>Account</span>
              </button>
            </nav>

            <div className="settings-content">
              <Outlet />
            </div>
          </div>
        </div>
      </div>
      <MinimalFooter />
    </div>
  );
};

export default SettingsLayout; 