// src/components/StaticAvatarDisplay.tsx
// Static avatar display when HeyGen is not active - matches exact mockup design

import React, { useState, useEffect } from 'react';
import type { HeyGenAvatar, QuotaStatus } from '../types/heygen';
import { getAvatarDisplayName, isValidAvatarImageUrl } from '../utils/avatarutils';

interface StaticAvatarDisplayProps {
  avatar: HeyGenAvatar | null;
  isLoading: boolean;
  error: string | null;
  quotaStatus: QuotaStatus;
  className?: string;
}

const StaticAvatarDisplay: React.FC<StaticAvatarDisplayProps> = ({
  avatar,
  isLoading,
  error,
  quotaStatus,
  className = '',
}) => {
  const [imageError, setImageError] = useState(false);
  const [imageLoaded, setImageLoaded] = useState(false);

  // Reset image state when avatar changes
  useEffect(() => {
    setImageError(false);
    setImageLoaded(false);
  }, [avatar?.avatar_id]);

  const handleImageLoad = () => {
    setImageLoaded(true);
    setImageError(false);
  };

  const handleImageError = () => {
    setImageError(true);
    setImageLoaded(false);
  };

  const getStatusIndicator = () => {
    if (isLoading) {
      return {
        text: 'Loading...',
        icon: '⏳',
        bgColor: 'rgba(156, 163, 175, 0.9)',
      };
    }

    if (error) {
      return {
        text: 'Error',
        icon: '❌',
        bgColor: 'rgba(244, 67, 54, 0.9)',
      };
    }

    if (quotaStatus.status === 'exceeded') {
      return {
        text: 'Quota Exceeded',
        icon: '⚠️',
        bgColor: 'rgba(255, 152, 0, 0.9)',
      };
    }

    return {
      text: 'Static Mode',
      icon: '📷',
      bgColor: 'rgba(156, 163, 175, 0.9)',
    };
  };

  const getPlaceholderContent = () => {
    if (isLoading) {
      return (
        <div className="avatar-placeholder loading">
          <div className="loading-spinner"></div>
          <p>Loading avatar...</p>
        </div>
      );
    }

    if (error) {
      return (
        <div className="avatar-placeholder error">
          <div className="error-icon">❌</div>
          <p>Failed to load avatar</p>
          <small>{error}</small>
        </div>
      );
    }

    if (!avatar) {
      return (
        <div className="avatar-placeholder empty">
          <div className="empty-icon">👤</div>
          <p>No avatar selected</p>
        </div>
      );
    }

    if (imageError || !isValidAvatarImageUrl(avatar.preview_image_url)) {
      return (
        <div className="avatar-placeholder fallback">
          <div className="fallback-icon">🤖</div>
          <p>{getAvatarDisplayName(avatar)}</p>
          <small>Preview not available</small>
        </div>
      );
    }

    return null;
  };

  const statusIndicator = getStatusIndicator();
  const placeholderContent = getPlaceholderContent();

  return (
    <div className={`static-avatar-display ${className}`}>
      <div className="avatar-container">
        {/* Status Indicator - matches mockup */}
        <div 
          className="status-indicator"
          style={{ background: statusIndicator.bgColor }}
        >
          <div className="status-dot"></div>
          <span>{statusIndicator.text}</span>
        </div>

        {/* Avatar Content */}
        <div className="avatar-content">
          {placeholderContent ? (
            placeholderContent
          ) : (
            <>
              {/* Loading overlay while image loads */}
              {!imageLoaded && (
                <div className="image-loading-overlay">
                  <div className="loading-spinner"></div>
                </div>
              )}

              {/* Avatar Image */}
              <img
                src={avatar!.preview_image_url}
                alt={getAvatarDisplayName(avatar)}
                className={`avatar-image ${imageLoaded ? 'loaded' : ''}`}
                onLoad={handleImageLoad}
                onError={handleImageError}
                style={{ 
                  opacity: imageLoaded ? 1 : 0,
                  transition: 'opacity 0.3s ease'
                }}
              />

              {/* Avatar Info Overlay */}
              {imageLoaded && (
                <div className="avatar-info">
                  <h3 className="avatar-name">{getAvatarDisplayName(avatar)}</h3>
                  <p className="avatar-gender">{avatar!.gender}</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Quota Status Overlay for exceeded state */}
        {quotaStatus.status === 'exceeded' && (
          <div className="quota-exceeded-overlay">
            <div className="quota-message">
              <h4>Interactive Time Exceeded</h4>
              <p>Switched to voice-only mode</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default StaticAvatarDisplay;