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
  const [connectionStatus, setConnectionStatus] = useState<string>('connecting');
  const [imageLoaded, setImageLoaded] = useState(false);

  useEffect(() => {
    initializeAvatar();
  }, []);

  const initializeAvatar = async () => {
    setIsLoading(true);
    setConnectionStatus('connecting');

    console.log('🔍 Initializing static HeyGen avatar (metadata only, no credits)...');

    try {
      const api = getStaticAvatarAPI();
      const primaryAvatarId = import.meta.env.VITE_HEYGEN_AVATAR_ID || 'Ann_Therapist_public';
      const fallbackAvatarId = 'Angela-inblackskirt-20220820';

      console.log('🎯 Getting HeyGen avatar metadata:', primaryAvatarId);

      // Get avatar metadata from HeyGen (no credits used - just metadata)
      const avatar = await api.getAvailableAvatar(primaryAvatarId, fallbackAvatarId);

      if (avatar && avatar.preview_image_url) {
        setAvatarData(avatar);
        
        // Try to preload the image
        const imageLoaded = await api.preloadAvatarImage(avatar.preview_image_url);
        if (imageLoaded) {
          setImageLoaded(true);
          setConnectionStatus('connected');
          setIsLoading(false);
          
          console.log('✅ Static HeyGen avatar ready:', avatar.avatar_name);
          
          // Notify parent component
          if (onAvatarReady) {
            onAvatarReady();
          }
          return;
        }
      }

      // If HeyGen API fails, show error but don't auto-fallback
      throw new Error('Unable to load HeyGen avatar metadata');

    } catch (error) {
      console.error('❌ Failed to initialize HeyGen avatar:', error);
      setConnectionStatus('error');
      setIsLoading(false);
      
      if (onAvatarError) {
        onAvatarError('Unable to connect to HeyGen avatar service');
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
    console.log('✅ HeyGen avatar image loaded successfully');
  };

  return (
    <div className={`static-avatar ${isListening ? 'listening' : ''} ${isSpeaking ? 'speaking' : ''}`}>
      {/* Minimal Connection Status */}
      <div className="avatar-header">
        <div className={`connection-status ${connectionStatus}`}>
          <div className={`status-dot ${connectionStatus}`}></div>
          <span className="status-text">
            {connectionStatus === 'connecting' && 'Loading...'}
            {connectionStatus === 'connected' && 'Ready'}
            {connectionStatus === 'error' && 'Connection Error'}
          </span>
        </div>
      </div>

      {/* Avatar Container */}
      <div className="avatar-container">
        {/* Loading State */}
        {isLoading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>Loading HeyGen avatar...</p>
            <small>Getting metadata...</small>
          </div>
        )}

        {/* Error State */}
        {connectionStatus === 'error' && !isLoading && (
          <div className="error-overlay">
            <div className="error-content">
              <h3>Connection Error</h3>
              <p>Unable to load HeyGen avatar</p>
              <button onClick={initializeAvatar} className="retry-button">
                Retry
              </button>
            </div>
          </div>
        )}

        {/* HeyGen Avatar Display */}
        {avatarData && !isLoading && connectionStatus === 'connected' && (
          <div
            className={`avatar-background-image ${imageLoaded ? 'loaded' : ''}`}
            style={{
              backgroundImage: `url(${avatarData.preview_image_url})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center 25%', // Position to show full face
              backgroundRepeat: 'no-repeat',
              width: '100%',
              height: '100%',
              borderRadius: '1rem',
              transform: 'scale(0.95)', // Slight scale to ensure head isn't cut
              transition: 'opacity 0.5s ease, transform 0.3s ease',
              opacity: imageLoaded ? 1 : 0
            }}
          >
            {/* Hidden image to detect loading */}
            <img
              src={avatarData.preview_image_url}
              alt=""
              style={{ display: 'none' }}
              onLoad={handleImageLoad}
              onError={() => {
                console.log('❌ HeyGen avatar image failed to load');
                setConnectionStatus('error');
              }}
            />
          </div>
        )}

        {/* Listening Animation Rings */}
        {isListening && avatarData && connectionStatus === 'connected' && (
          <div className="listening-rings">
            <div className="ring ring-1"></div>
            <div className="ring ring-2"></div>
            <div className="ring ring-3"></div>
          </div>
        )}

        {/* Speaking Indicator */}
        {isSpeaking && avatarData && connectionStatus === 'connected' && (
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

      {/* Status */}
      <div className="avatar-status">
        <div className={`status-indicator ${isListening ? 'listening' : isSpeaking ? 'speaking' : avatarData ? 'ready' : 'loading'}`}>
          <span className="status-text">
            {isListening && 'Listening...'}
            {isSpeaking && 'Speaking...'}
            {!isListening && !isSpeaking && avatarData && 'Ready'}
            {!isListening && !isSpeaking && !avatarData && 'Loading...'}
          </span>
        </div>
        {avatarData && (
          <div className="avatar-info">
            <small>{avatarData.avatar_name}</small>
          </div>
        )}
      </div>
    </div>
  );
});

StaticAvatar.displayName = 'StaticAvatar';

export default StaticAvatar;