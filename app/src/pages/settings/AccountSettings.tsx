import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LogOut, Trash2, AlertTriangle } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { supabase } from '../../supabaseClient';
import Button from '../../components/Button';

interface PasswordFormData {
  oldPassword: string;
  newPassword: string;
  confirmPassword: string;
}

const AccountSettings: React.FC = () => {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  
  const [passwordData, setPasswordData] = useState<PasswordFormData>({
    oldPassword: '',
    newPassword: '',
    confirmPassword: '',
  });

  // Loading and error states
  const [isLoggingOut, setIsLoggingOut] = useState(false);
  const [isChangingPassword, setIsChangingPassword] = useState(false);
  const [isDeletingAccount, setIsDeletingAccount] = useState(false);
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [passwordErrors, setPasswordErrors] = useState<{
    oldPassword?: string;
    newPassword?: string;
    confirmPassword?: string;
  }>({});

  const validatePasswords = (): boolean => {
    const errors: typeof passwordErrors = {};
    
    if (!passwordData.oldPassword) {
      errors.oldPassword = 'Current password is required';
    }
    
    if (!passwordData.newPassword) {
      errors.newPassword = 'New password is required';
    } else if (passwordData.newPassword.length < 6) {
      errors.newPassword = 'Password must be at least 6 characters';
    }
    
    if (!passwordData.confirmPassword) {
      errors.confirmPassword = 'Please confirm your new password';
    } else if (passwordData.newPassword !== passwordData.confirmPassword) {
      errors.confirmPassword = 'Passwords do not match';
    }
    
    setPasswordErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validatePasswords()) {
      return;
    }

    setIsChangingPassword(true);
    setError(null);
    setSuccess(null);

    try {
      // First, reauthenticate with the old password
      if (!user?.email) {
        throw new Error('User email not available');
      }

      const { error: reauthError } = await supabase.auth.signInWithPassword({
        email: user.email,
        password: passwordData.oldPassword,
      });

      if (reauthError) {
        setPasswordErrors({ oldPassword: 'Current password is incorrect' });
        return;
      }

      // Update the password
      const { error: updateError } = await supabase.auth.updateUser({
        password: passwordData.newPassword,
      });

      if (updateError) {
        throw updateError;
      }

      // Success - show message and then log out
      setSuccess('Password updated successfully. You will be logged out for security.');
      
      // Clear the form
      setPasswordData({
        oldPassword: '',
        newPassword: '',
        confirmPassword: '',
      });

      // Log out after 2 seconds
      setTimeout(async () => {
        await logout();
        navigate('/login');
      }, 2000);

    } catch (error: any) {
      console.error('Error changing password:', error);
      setError(error.message || 'Failed to change password');
    } finally {
      setIsChangingPassword(false);
    }
  };

  const handleLogoutAllDevices = async () => {
    setIsLoggingOut(true);
    setError(null);

    try {
      // Sign out from all devices using Supabase
      const { error } = await supabase.auth.signOut({ scope: 'global' });
      
      if (error) {
        throw error;
      }

      // Call the logout from AuthContext to clean up local state
      await logout();
      
      // Redirect to login page
      navigate('/login');
    } catch (error: any) {
      console.error('Error logging out from all devices:', error);
      setError(error.message || 'Failed to log out from all devices');
    } finally {
      setIsLoggingOut(false);
    }
  };

  const handleDeleteAccount = () => {
    setShowDeleteModal(true);
  };

  const confirmDeleteAccount = async () => {
    setIsDeletingAccount(true);
    setError(null);

    try {
      // Get current user and session
      const { data: { user: currentUser } } = await supabase.auth.getUser();
      const { data: { session } } = await supabase.auth.getSession();
      
      if (!currentUser || !session) {
        throw new Error('No authenticated user found');
      }

      // Call our edge function to delete the user account
      const { data, error } = await supabase.functions.invoke('delete-user', {
        body: { userId: currentUser.id }
      });

      if (error) {
        throw error;
      }

      if (data?.error) {
        throw new Error(data.error);
      }

      // Clear all localStorage data
      localStorage.clear();
      
      // Clear auth context
      await logout();
      
      // Close modal
      setShowDeleteModal(false);
      
      // Redirect to signup page
      navigate('/signup');
      
    } catch (error: any) {
      console.error('Error deleting account:', error);
      setError(error.message || 'Failed to delete account. Please contact support.');
    } finally {
      setIsDeletingAccount(false);
    }
  };

  const cancelDeleteAccount = () => {
    setShowDeleteModal(false);
  };

  return (
    <div className="settings-section">
      <h2>Account Settings</h2>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6">
          {success}
        </div>
      )}

      <div className="account-actions">
        <div className="action-group">
          <h3>Session Management</h3>
          <Button
            variant="outline"
            onClick={handleLogoutAllDevices}
            disabled={isLoggingOut}
            icon={<LogOut size={18} />}
          >
            {isLoggingOut ? 'Logging out...' : 'Log out of all devices'}
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
                className={passwordErrors.oldPassword ? 'error' : ''}
              />
              {passwordErrors.oldPassword && (
                <p className="text-red-600 text-sm mt-1">{passwordErrors.oldPassword}</p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="newPassword">New Password</label>
              <input
                type="password"
                id="newPassword"
                value={passwordData.newPassword}
                onChange={(e) => setPasswordData({ ...passwordData, newPassword: e.target.value })}
                className={passwordErrors.newPassword ? 'error' : ''}
              />
              {passwordErrors.newPassword && (
                <p className="text-red-600 text-sm mt-1">{passwordErrors.newPassword}</p>
              )}
            </div>

            <div className="form-group">
              <label htmlFor="confirmPassword">Confirm New Password</label>
              <input
                type="password"
                id="confirmPassword"
                value={passwordData.confirmPassword}
                onChange={(e) => setPasswordData({ ...passwordData, confirmPassword: e.target.value })}
                className={passwordErrors.confirmPassword ? 'error' : ''}
              />
              {passwordErrors.confirmPassword && (
                <p className="text-red-600 text-sm mt-1">{passwordErrors.confirmPassword}</p>
              )}
            </div>

            <Button type="submit" variant="primary" disabled={isChangingPassword}>
              {isChangingPassword ? 'Updating Password...' : 'Update Password'}
            </Button>
          </form>
        </div>

        <div className="action-group danger-zone">
          <h3>Danger Zone</h3>
          <Button
            variant="outline"
            className="delete-account"
            onClick={handleDeleteAccount}
            disabled={isDeletingAccount}
            icon={<Trash2 size={18} />}
          >
            {isDeletingAccount ? 'Deleting Account...' : 'Delete Account'}
          </Button>
          <p className="danger-note">
            This action cannot be undone. All your data will be permanently deleted.
          </p>
        </div>
      </div>

      {/* Delete Account Confirmation Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="text-red-500" size={24} />
              <h3 className="text-xl font-semibold text-gray-900">Delete Account</h3>
            </div>
            
            <p className="text-gray-600 mb-6">
              Are you absolutely sure you want to delete your account? This action cannot be undone. 
              All your data, conversations, and settings will be permanently deleted.
            </p>
            
            <div className="flex space-x-3">
              <Button
                variant="outline"
                onClick={cancelDeleteAccount}
                disabled={isDeletingAccount}
                className="flex-1"
              >
                Cancel
              </Button>
              <Button
                variant="primary"
                onClick={confirmDeleteAccount}
                disabled={isDeletingAccount}
                className="flex-1 bg-red-600 hover:bg-red-700"
                icon={isDeletingAccount ? undefined : <Trash2 size={18} />}
              >
                {isDeletingAccount ? 'Deleting...' : 'Delete Account'}
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default AccountSettings; 