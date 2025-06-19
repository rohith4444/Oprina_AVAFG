import React, { useState, useEffect } from 'react';
import { supabase } from '../supabaseClient';

interface QuotaDisplayProps {
  isVisible: boolean;
}

interface QuotaData {
  can_create_session: boolean;
  total_seconds_used: number;
  remaining_seconds: number;
  quota_exhausted: boolean;
  quota_percentage: number;
}

const QuotaDisplay: React.FC<QuotaDisplayProps> = ({ isVisible }) => {
  const [quotaData, setQuotaData] = useState<QuotaData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Get backend URL from environment
  const BACKEND_API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

  // Get user token for API calls
  const getUserToken = async () => {
    const { data: { session } } = await supabase.auth.getSession();
    return session?.access_token;
  };

  // Fetch quota data from backend
  const fetchQuotaData = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const token = await getUserToken();
      if (!token) {
        setError('Authentication required');
        return;
      }

      const response = await fetch(`${BACKEND_API_URL}/api/v1/avatar/quota`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch quota: ${response.status}`);
      }

      const data = await response.json();
      setQuotaData(data);
    } catch (err: any) {
      console.error('Error fetching quota:', err);
      setError(err.message || 'Failed to load quota');
    } finally {
      setIsLoading(false);
    }
  };

  // Load quota data when component becomes visible
  useEffect(() => {
    if (isVisible) {
      fetchQuotaData();
    }
  }, [isVisible]);

  // Auto-refresh quota every 30 seconds when visible
  useEffect(() => {
    if (!isVisible) return;

    const interval = setInterval(() => {
      fetchQuotaData();
    }, 30000); // 30 seconds

    return () => clearInterval(interval);
  }, [isVisible]);

  if (!isVisible) return null;

  // Loading state
  if (isLoading) {
    return (
      <span className="quota-display">
        Loading quota...
      </span>
    );
  }

  // Error state
  if (error) {
    return (
      <span className="quota-display" style={{ color: '#ef4444' }}>
        Quota unavailable
      </span>
    );
  }

  // No data state
  if (!quotaData) {
    return (
      <span className="quota-display">
        Quota data unavailable
      </span>
    );
  }

  // Convert seconds to minutes for display
  const remainingMinutes = Math.floor(quotaData.remaining_seconds / 60);
  const remainingSeconds = quotaData.remaining_seconds % 60;

  // Format display text
  let displayText: string;
  let textColor: string;

  if (quotaData.quota_exhausted) {
    displayText = "Quota exhausted - 0 mins left";
    textColor = '#ef4444'; // Red
  } else if (remainingMinutes < 2) {
    displayText = `Quota: ${remainingSeconds}s left`;
    textColor = '#f59e0b'; // Orange/Yellow
  } else {
    displayText = `Quota left for streaming Avatar: ${remainingMinutes} mins left`;
    textColor = '#10b981'; // Green
  }

  return (
    <span className="quota-display" style={{ color: textColor }}>
      {displayText}
    </span>
  );
};

export default QuotaDisplay;