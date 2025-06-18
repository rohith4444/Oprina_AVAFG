import React from 'react';

interface QuotaDisplayProps {
  isVisible: boolean;
}

const QuotaDisplay: React.FC<QuotaDisplayProps> = ({ isVisible }) => {
  if (!isVisible) return null;

  // TODO: Replace with actual API call
  const quotaMinutes = 10; // Placeholder data

  return (
    <span className="quota-display">
      Quota left for streaming Avatar: {quotaMinutes} mins left
    </span>
  );
};

export default QuotaDisplay;