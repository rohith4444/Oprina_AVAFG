import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../context/AuthContext';
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
  const [showSuccess, setShowSuccess] = useState(false);

  const [profileData, setProfileData] = useState<ProfileFormData>({
    fullName: user?.email?.split('@')[0] || '',
    preferredName: '',
    workType: '',
    preferences: '',
  });

  // Load saved profile data from localStorage on component mount
  useEffect(() => {
    const savedProfile = localStorage.getItem('user_profile');
    if (savedProfile) {
      try {
        const parsed = JSON.parse(savedProfile);
        setProfileData(prev => ({
          ...prev,
          ...parsed,
          // Keep email-based fullName as fallback if no saved fullName
          fullName: parsed.fullName || user?.email?.split('@')[0] || '',
        }));
      } catch (error) {
        console.error('Error parsing saved profile:', error);
      }
    }
  }, [user]);

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);

    try {
      // Save profile data to localStorage
      localStorage.setItem('user_profile', JSON.stringify(profileData));
      
      // Determine the display name (preferred name takes priority)
      const displayName = profileData.preferredName?.trim() || profileData.fullName?.trim();
      
      if (displayName) {
        // Update the user's display name in AuthContext (this will update the sidebar)
        updateUserDisplayName(displayName);
      }

      // Show success message
      setShowSuccess(true);
      setTimeout(() => setShowSuccess(false), 3000);

    } catch (error) {
      console.error('Error saving profile:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="settings-section">
      <h2>Profile Settings</h2>
      
      {showSuccess && (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded mb-6">
          Profile updated successfully! Your changes have been saved.
        </div>
      )}
      
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

        <Button type="submit" variant="primary" disabled={isSubmitting}>
          {isSubmitting ? 'Saving...' : 'Save Changes'}
        </Button>
      </form>
    </div>
  );
};

export default ProfileSettings; 