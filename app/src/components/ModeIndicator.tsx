// src/components/ModeIndicator.tsx
// Displays current avatar mode (Interactive/Fallback/Static) - matches exact mockup design

import React from 'react';
import type { AvatarMode } from '../types/heygen';

interface ModeIndicatorProps {
  mode: AvatarMode;
  isConnecting?: boolean;
  className?: string;
}

const ModeIndicator: React.FC<ModeIndicatorProps> = ({
  mode,
  isConnecting = false,
  className = '',
}) => {
  
  const getModeConfig = () => {
    if (isConnecting) {
      return {
        icon: '⏳',
        text: 'Connecting...',
        color: 'connecting',
      };
    }

    switch (mode) {
      case 'interactive':
        return {
          icon: '🎥',
          text: 'Interactive Mode',
          color: 'success',
        };
      case 'fallback':
        return {
          icon: '🔊',
          text: 'TTS Mode',
          color: 'warning',
        };
      case 'static':
        return {
          icon: '📷',
          text: 'Static Mode',
          color: 'neutral',
        };
      case 'connecting':
        return {
          icon: '⏳',
          text: 'Connecting...',
          color: 'connecting',
        };
      default:
        return {
          icon: '❓',
          text: 'Unknown Mode',
          color: 'neutral',
        };
    }
  };

  const config = getModeConfig();
  const baseClasses = `mode-indicator mode-indicator--${config.color}`;
  const finalClasses = `${baseClasses} ${className}`.trim();

  return (
    <div className={finalClasses}>
      <span className="mode-icon">{config.icon}</span>
      <span className="mode-text">{config.text}</span>
    </div>
  );
};

export default ModeIndicator;