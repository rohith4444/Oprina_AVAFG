// src/components/StaticAvatar.tsx
import { useState, useEffect, forwardRef, useImperativeHandle } from 'react';
import { getStaticAvatarAPI, AvatarData } from '../utils/staticAvatarAPI';
import '../styles/StaticAvatar.css';

interface StaticAvatarProps {
  isListening: boolean;
  isSpeaking: boolean;
  onAvatarReady?: () => void;
  onAvatarError?: (error: string) => void;
  onAvatarStartTalking?: () => void;
  onAvatarStopTalking?: () => void;
}

// Define the methods that will be exposed via ref (same as HeyGenAvatar)
export interface StaticAvatarRef {
  speak: (text: string) => Promise<void>;
}

const StaticAvatar = forwardRef<StaticAvatarRef, StaticAvatarProps>(({
  isListening,
  isSpeaking,
  onAvatarReady,
  onAvatarError,
  onAvatarStartTalking,
  onAvatarStopTalking
}, ref) => {
  const [avatarData, setAvatarData] = useState<AvatarData | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('connecting');
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    initializeAvatar();
  }, []);

  const initializeAvatar = async () => {
    try {
      setIsLoading(true);
      setError(null);
      setConnectionStatus('connecting');

      console.log('🔍 Initializing static avatar...');

      const api = getStaticAvatarAPI();
      const primaryAvatarId = import.meta.env.VITE_HEYGEN_AVATAR_ID || 'Ann_Therapist_public';
      const fallbackAvatarId = 'Angela-inblackskirt-20220820';

      console.log('🎯 Looking for avatar:', primaryAvatarId);

      const avatar = await api.getAvailableAvatar(primaryAvatarId, fallbackAvatarId);

      if (avatar && avatar.preview_image_url) {
        setAvatarData(avatar);
        
        // Preload the image
        const imageLoaded = await api.preloadAvatarImage(avatar.preview_image_url);
        if (imageLoaded) {
          setImageLoaded(true);
          setConnectionStatus('connected');
          setIsLoading(false);
          
          console.log('✅ Static avatar ready:', avatar.avatar_name);
          
          // Notify parent component
          if (onAvatarReady) {
            onAvatarReady();
          }
        } else {
          throw new Error('Failed to load avatar image');
        }
      } else {
        throw new Error('No avatars available');
      }
    } catch (err: any) {
      const errorMessage = err?.message || 'Failed to initialize static avatar';
      setError(errorMessage);
      setIsLoading(false);
      setConnectionStatus('error');
      
      console.error('❌ Static avatar error:', errorMessage);
      
      if (onAvatarError) {
        onAvatarError(errorMessage);
      }
    }
  };

  // Mock speak method (same interface as HeyGenAvatar)
  const speak = async (text: string) => {
    if (avatarData && text.trim()) {
      console.log('🗣️ Static avatar "speaking":', text);
      
      // Simulate speaking start
      if (onAvatarStartTalking) {
        onAvatarStartTalking();
      }

      // Simulate speaking duration based on text length
      const speakingDuration = Math.max(1000, text.length * 50); // ~50ms per character
      
      setTimeout(() => {
        if (onAvatarStopTalking) {
          onAvatarStopTalking();
        }
      }, speakingDuration);
    }
  };

  // Expose speak method to parent component via ref
  useImperativeHandle(ref, () => ({
    speak
  }));

  const handleImageLoad = () => {
    setImageLoaded(true);
    console.log('✅ Avatar image loaded successfully');
  };

  const handleImageError = () => {
    setError('Failed to load avatar image');
    setConnectionStatus('error');
    console.error('❌ Avatar image failed to load');
  };

  const retryInitialization = () => {
    setError(null);
    setIsLoading(true);
    setImageLoaded(false);
    initializeAvatar();
  };

  return (
    <div className={`static-avatar ${isListening ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''}`}>
      {/* Minimal Connection Status */}
      <div className="avatar-header">
        <div className={`connection-status ${connectionStatus}`}>
          <div className={`status-dot ${connectionStatus}`}></div>
          <span className="status-text">
            {connectionStatus === 'connecting' && 'Connecting...'}
            {connectionStatus === 'connected' && 'Ready'}
            {connectionStatus === 'error' && 'Error'}
          </span>
        </div>
      </div>

      {/* Avatar Container */}
      <div className="avatar-container">
        {/* Loading State */}
        {isLoading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>Loading avatar...</p>
            <small>Fetching from HeyGen...</small>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-overlay">
            <div className="error-content">
              <h3>Avatar Unavailable</h3>
              <p>{error}</p>
              <button onClick={retryInitialization} className="retry-button">
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Avatar Image */}
        {avatarData && (
          <img
            src={avatarData.preview_image_url}
            alt={avatarData.avatar_name || 'Avatar'}
            className={`avatar-image ${imageLoaded ? 'loaded' : ''}`}
            onLoad={handleImageLoad}
            onError={handleImageError}
            style={{ display: error ? 'none' : 'block' }}
          />
        )}

        {/* Listening Animation Rings */}
        {isListening && imageLoaded && !error && (
          <div className="listening-rings">
            <div className="ring ring-1"></div>
            <div className="ring ring-2"></div>
            <div className="ring ring-3"></div>
          </div>
        )}

        {/* Speaking Indicator */}
        {isSpeaking && imageLoaded && !error && (
          <div className="speaking-indicator">
            <div className="sound-waves">
              <div className="wave"></div>
              <div className="wave"></div>
              <div className="wave"></div>
            </div>
            <span>Speaking...</span>
          </div>
        )}
      </div>

      {/* Bottom Status */}
      <div className="avatar-status">
        <div className={`status-indicator ${isListening ? 'listening' : isSpeaking ? 'speaking' : imageLoaded ? 'ready' : 'loading'}`}>
          {isListening 
            ? '🎤 Listening' 
            : isSpeaking 
            ? '🗣️ Speaking' 
            : imageLoaded 
            ? '😊 Ready' 
            : '⏳ Loading'
          }
        </div>
      </div>
    </div>
  );
});

StaticAvatar.displayName = 'StaticAvatar';

export default StaticAvatar;