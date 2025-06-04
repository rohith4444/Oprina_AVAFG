// src/components/QuotaIndicator.tsx
// Displays HeyGen quota status and remaining time - matches exact mockup design

import React from 'react';
import type { QuotaStatus } from '../types/heygen';

interface QuotaIndicatorProps {
  quotaStatus: QuotaStatus;
  className?: string;
}

const QuotaIndicator: React.FC<QuotaIndicatorProps> = ({
  quotaStatus,
  className = '',
}) => {
  
  const getStatusColor = () => {
    switch (quotaStatus.status) {
      case 'available':
        return 'success';
      case 'warning':
        return 'warning';
      case 'exceeded':
      case 'grace':
        return 'danger';
      default:
        return 'success';
    }
  };

  const getStatusIcon = () => {
    switch (quotaStatus.status) {
      case 'available':
        return '✅';
      case 'warning':
        return '⚠️';
      case 'exceeded':
      case 'grace':
        return '❌';
      default:
        return 'ℹ️';
    }
  };

  const getStatusText = () => {
    switch (quotaStatus.status) {
      case 'available':
        return 'HeyGen Quota';
      case 'warning':
        return 'HeyGen Quota';
      case 'exceeded':
        return 'Quota Exceeded';
      case 'grace':
        return 'Grace Period';
      default:
        return 'HeyGen Quota';
    }
  };

  const getTimeText = () => {
    if (quotaStatus.status === 'exceeded') {
      return 'Quota exceeded';
    }
    
    const minutes = Math.floor(quotaStatus.remainingMinutes);
    const seconds = Math.round((quotaStatus.remainingMinutes - minutes) * 60);
    
    if (minutes < 1) {
      return `${Math.round(quotaStatus.remainingMinutes * 60)}s remaining`;
    }
    
    return `${minutes}:${seconds.toString().padStart(2, '0')} remaining`;
  };

  const statusColor = getStatusColor();
  const baseClasses = `quota-indicator quota-indicator--${statusColor}`;
  const finalClasses = `${baseClasses} ${className}`.trim();

  return (
    <div className={finalClasses}>
      <div className="quota-header">
        <span className="quota-icon">{getStatusIcon()}</span>
        <span className="quota-status">{getStatusText()}</span>
      </div>
      <div className="quota-time">{getTimeText()}</div>
      <div className="quota-bar">
        <div 
          className="quota-progress" 
          style={{ width: `${quotaStatus.percentUsed}%` }}
        />
      </div>
    </div>
  );
};

export default QuotaIndicator;