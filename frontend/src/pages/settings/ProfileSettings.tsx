import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
import { supabase } from '../../supabaseClient';
import Button from '../../components/Button';

interface ProfileFormData {
  fullName: string;
  preferredName: string;
  workType: string;
  preferences: string;
}

const ProfileSettings: React.FC = () => {
  const navigate = useNavigate();
  const { user, updateUserDisplayName } = useAuth();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [showSuccess, setShowSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [profileData, setProfileData] = useState<ProfileFormData>({
    fullName: '',
    preferredName: '',
    workType: '',
    preferences: '',
  });

  // Backend API URL - Update this to match your backend
 const BACKEND_API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  // Get Supabase token for API calls
  const getAuthToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token;
  };

  // Load profile data from backend API on component mount
  useEffect(() => {
    const loadProfileData = async () => {
      try {
        setIsLoading(true);
        setError(null);

        const token = await getAuthToken();
        if (!token) {
          setError('Authentication required');
          return;
        }

        // Call your backend API to get user profile
        const response = await fetch(`${BACKEND_API_URL}/api/v1/user/me`, {
          method: 'GET',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          }
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}: Failed to load profile`);
        }

        const userData = await response.json();
        
        // Map backend response to form data
        setProfileData({
          fullName: userData.full_name || '',
          preferredName: userData.preferred_name || '',
          workType: userData.work_type || '',
          preferences: userData.ai_preferences || '',
        });

      } catch (error: any) {
        console.error('Error loading profile:', error);
        setError(error.message || 'Failed to load profile data');
        
        // Fallback to user email for full name if API fails
        setProfileData(prev => ({
          ...prev,
          fullName: prev.fullName || user?.email?.split('@')[0] || '',
        }));
      } finally {
        setIsLoading(false);
      }
    };

    if (user) {
      loadProfileData();
    }
  }, [user, BACKEND_API_URL]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setError(null);

    try {
      const token = await getAuthToken();
      if (!token) {
        throw new Error('Authentication required');
      }

      // Prepare data for backend API
      const updateData = {
        full_name: profileData.fullName.trim() || null,
        preferred_name: profileData.preferredName.trim() || null,
        work_type: profileData.workType.trim() || null,
        ai_preferences: profileData.preferences.trim() || null,
      };

      // Call your backend API to update profile
      const response = await fetch(`${BACKEND_API_URL}/api/v1/user/me`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(updateData)
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: Failed to update profile`);
      }

      const result = await response.json();
      console.log('Profile updated successfully:', result);

      // Update display name in AuthContext (for sidebar updates)
      const displayName = profileData.preferredName?.trim() || profileData.fullName?.trim();
      if (displayName) {
        updateUserDisplayName(displayName);
      }

      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);

      // Optional: Keep localStorage backup for offline scenarios
      localStorage.setItem('user_profile_backup', JSON.stringify(profileData));

    } catch (error: any) {
      console.error('Error saving profile:', error);
      setError(error.message || 'Failed to save profile. Please try again.');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="settings-section">
        <h2>Profile Settings</h2>
        <div className="flex items-center justify-center py-8">
          <div className="text-gray-600">Loading profile data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="settings-section">
      <h2>Profile Settings</h2>
      
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
          {error}
        </div>
      )}
      
      {showSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6">
          Profile updated successfully! Your changes have been saved to the database.
        </div>
      )}

      <form onSubmit={handleProfileSubmit} className="settings-form">
        <div className="form-group">
          <label htmlFor="fullName">Full Name</label>
          <input
            type="text"
            id="fullName"
            value={profileData.fullName}
            onChange={(e) => setProfileData({ ...profileData, fullName: e.target.value })}
            placeholder="Enter your full name"
          />
        </div>

        <div className="form-group">
          <label htmlFor="preferredName">Preferred Name</label>
          <input
            type="text"
            id="preferredName"
            value={profileData.preferredName}
            onChange={(e) => setProfileData({ ...profileData, preferredName: e.target.value })}
            placeholder="How would you like to be addressed? (optional)"
          />
          <small className="text-gray-600">
            This will be used in the sidebar and throughout the app
          </small>
        </div>

        <div className="form-group">
          <label htmlFor="workType">What best describes your work?</label>
          <select
            id="workType"
            value={profileData.workType}
            onChange={(e) => setProfileData({ ...profileData, workType: e.target.value })}
          >
            <option value="">Select an option</option>
            <option value="Software Developer">Software Developer</option>
            <option value="Product Manager">Product Manager</option>
            <option value="Designer">Designer</option>
            <option value="Marketing">Marketing</option>
            <option value="Sales">Sales</option>
            <option value="Executive">Executive</option>
            <option value="Student">Student</option>
            <option value="Consultant">Consultant</option>
            <option value="Entrepreneur">Entrepreneur</option>
            <option value="Other">Other</option>
          </select>
        </div>

        <div className="form-group">
          <label htmlFor="preferences">What personal preferences should Oprina consider in responses?</label>
          <textarea
            id="preferences"
            value={profileData.preferences}
            onChange={(e) => setProfileData({ ...profileData, preferences: e.target.value })}
            rows={4}
            placeholder="e.g., Prefer detailed explanations, focus on code examples, keep responses concise, etc."
          />
          <small className="text-gray-600">
            Help Oprina understand how you like to receive information
          </small>
        </div>

        <Button 
          type="submit" 
          variant="primary" 
          disabled={isSubmitting}
        >
          {isSubmitting ? 'Saving Changes...' : 'Save Changes'}
        </Button>
      </form>
    </div>
  );
};

export default ProfileSettings;