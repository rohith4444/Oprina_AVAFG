import { useState, useEffect, useRef, forwardRef, useImperativeHandle } from 'react';
import StreamingAvatar, { 
  AvatarQuality, 
  StreamingEvents, 
  TaskType
} from '@heygen/streaming-avatar';
import '../styles/HeyGenAvatar.css';
import { supabase } from '../supabaseClient';

const BACKEND_API_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000';

interface HeyGenAvatarProps {
  isListening: boolean;
  isSpeaking: boolean;
  onAvatarReady?: () => void;
  onAvatarError?: (error: string) => void;
  onAvatarStartTalking?: () => void;
  onAvatarStopTalking?: () => void;
}

interface AvatarSession {
  streamingAvatar: StreamingAvatar;
  sessionId: string;
  isReady: boolean;
}

// Define the methods that will be exposed via ref
export interface HeyGenAvatarRef {
  speak: (text: string) => Promise<void>;
}

const HeyGenAvatar = forwardRef<HeyGenAvatarRef, HeyGenAvatarProps>(({
  isListening,
  isSpeaking,
  onAvatarReady,
  onAvatarError,
  onAvatarStartTalking,
  onAvatarStopTalking
}, ref) => {
  const [avatarSession, setAvatarSession] = useState<AvatarSession | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<string>('disconnected');
  const [isAvatarTalking, setIsAvatarTalking] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    initializeAvatar();

    // Cleanup on unmount
    return () => {
      cleanup();
    };
  }, []);

  // Use isSpeaking prop to avoid unused warning
  useEffect(() => {
    if (isSpeaking !== isAvatarTalking) {
      console.log('Speaking state sync:', { external: isSpeaking, internal: isAvatarTalking });
    }
  }, [isSpeaking, isAvatarTalking]);

  const initializeAvatar = async () => {
  try {
    setIsLoading(true);
    setError(null);
    setConnectionStatus('connecting');

    console.log('⏳ Waiting before creating session...');
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    const response = await fetch(`${BACKEND_API_URL}/api/v1/avatar/token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Backend error: ${response.status}`);
    }

    const data = await response.json();
    const sessionToken = data.token;

    // Add another small delay after getting token
    await new Promise(resolve => setTimeout(resolve, 500));

    // Create StreamingAvatar with session token
    const streamingAvatar = new StreamingAvatar({
      token: sessionToken
    });

    // Set up event handlers BEFORE creating session
    setupAvatarEvents(streamingAvatar);

    // Create avatar session with minimal config
    const sessionInfo = await streamingAvatar.createStartAvatar({
      quality: AvatarQuality.High,
      avatarName: "Ann_Therapist_public"
    });

    console.log('✅ HeyGen session created:', sessionInfo.session_id);

    // 🚨 NEW: Notify backend that session started
    try {
      const { data: { session } } = await supabase.auth.getSession();
      const token = session?.access_token;
      
      if (token) {
        const backendResponse = await fetch(`${BACKEND_API_URL}/api/v1/avatar/sessions/start`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            heygen_session_id: sessionInfo.session_id,
            avatar_name: "Ann_Therapist_public"
          })
        });
        
        if (backendResponse.ok) {
          console.log('✅ Backend session tracking started');
        } else {
          const errorData = await backendResponse.json();
          console.warn('⚠️ Failed to start backend session tracking:', errorData);
        }
      }
    } catch (trackingError) {
      console.error('❌ Error starting backend session tracking:', trackingError);
      // Don't fail the whole avatar initialization for tracking errors
    }

    // Set avatar session state
    setAvatarSession({
      streamingAvatar,
      sessionId: sessionInfo.session_id,
      isReady: true
    });

    setConnectionStatus('connected');
    setIsLoading(false);

    // Notify parent component
    if (onAvatarReady) {
      onAvatarReady();
    }

  } catch (err: any) {
    const errorMessage = err?.message || 'Failed to initialize avatar';
    setError(errorMessage);
    setIsLoading(false);
    setConnectionStatus('error');
    
    if (onAvatarError) {
      onAvatarError(errorMessage);
    }
  }
};

  const setupAvatarEvents = (streamingAvatar: StreamingAvatar) => {
    // Stream ready event
    streamingAvatar.on(StreamingEvents.STREAM_READY, (event) => {
      if (event && event.detail && videoRef.current) {
        const stream = event.detail;
        videoRef.current.srcObject = stream;
        videoRef.current.play().catch(console.error);
      }
    });

    // Avatar start talking event
    streamingAvatar.on(StreamingEvents.AVATAR_START_TALKING, () => {
      setIsAvatarTalking(true);
      if (onAvatarStartTalking) {
        onAvatarStartTalking();
      }
    });

    // Avatar stop talking event
    streamingAvatar.on(StreamingEvents.AVATAR_STOP_TALKING, () => {
      setIsAvatarTalking(false);
      if (onAvatarStopTalking) {
        onAvatarStopTalking();
      }
    });

    // Stream disconnected event
    streamingAvatar.on(StreamingEvents.STREAM_DISCONNECTED, () => {
      setConnectionStatus('disconnected');
      setError('Stream disconnected');
    });
  };

  const cleanup = async () => {
  try {
    // 🚨 NEW: First, notify backend that session is ending
    if (avatarSession?.sessionId) {
      try {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        
        if (token) {
          const endResponse = await fetch(`${BACKEND_API_URL}/api/v1/avatar/sessions/end`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              heygen_session_id: avatarSession.sessionId
            })
          });
          
          if (endResponse.ok) {
            console.log('✅ Backend session tracking ended');
          } else {
            console.warn('⚠️ Failed to end backend session tracking');
          }
        }
      } catch (trackingError) {
        console.error('❌ Error ending backend session tracking:', trackingError);
      }
    }
    
    // Then cleanup HeyGen session
    if (avatarSession?.streamingAvatar) {
      console.log('🧹 Stopping HeyGen avatar session...');
      await avatarSession.streamingAvatar.stopAvatar();

      // Add a small delay to ensure cleanup completes
      await new Promise(resolve => setTimeout(resolve, 1000));
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    
    // Clear state
    setAvatarSession(null);
    setConnectionStatus('disconnected');
    console.log('✅ Avatar cleanup completed');
    
  } catch (err) {
    console.error('Error during cleanup:', err);
  }
};

  // Method to make avatar speak
  const speak = async (text: string) => {
    if (avatarSession?.streamingAvatar && avatarSession.isReady && text.trim()) {
      try {
        await avatarSession.streamingAvatar.speak({
          text: text,
          task_type: TaskType.REPEAT
        });
      } catch (err) {
        console.error('Error making avatar speak:', err);
        setError('Failed to make avatar speak');
      }
    }
  };

  // Expose speak method to parent component via ref
  useImperativeHandle(ref, () => ({
    speak
  }));

  return (
    <div className={`heygen-avatar ${isListening ? 'listening' : ''} ${isAvatarTalking ? 'speaking' : ''}`}>
      {/* Minimal Connection Status - Just a small dot */}
      <div className="avatar-header">
        <div className={`connection-status ${connectionStatus}`}>
          <div className={`status-dot ${connectionStatus}`}></div>
          <span className="status-text">
            {connectionStatus === 'connecting' && 'Connecting...'}
            {connectionStatus === 'connected' && 'Ready'}
            {connectionStatus === 'error' && 'Error'}
            {connectionStatus === 'disconnected' && 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Clean Avatar Video Container */}
      <div className="avatar-container">
        {/* Loading State */}
        {isLoading && (
          <div className="loading-overlay">
            <div className="spinner"></div>
            <p>Connecting...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="error-overlay">
            <div className="error-content">
              <h3>Connection Error</h3>
              <p>Unable to connect to avatar service</p>
              <button onClick={initializeAvatar} className="retry-button">
                Retry
              </button>
            </div>
          </div>
        )}

        {/* Avatar Video Stream */}
        <video
          ref={videoRef}
          className="avatar-video"
          autoPlay
          playsInline
          muted={false}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            borderRadius: '1rem',
            background: 'linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%)'
          }}
        />

        {/* Listening Animation Rings - Only when listening */}
        {isListening && avatarSession?.isReady && (
          <div className="listening-rings">
            <div className="ring ring-1"></div>
            <div className="ring ring-2"></div>
            <div className="ring ring-3"></div>
          </div>
        )}

        {/* Speaking Indicator - Only when speaking */}
        {isAvatarTalking && (
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

      {/* Clean Bottom Status - Minimal */}
      <div className="avatar-status">
        <div className={`status-indicator ${isListening ? 'listening' : isAvatarTalking ? 'speaking' : avatarSession?.isReady ? 'ready' : 'loading'}`}>
          {isListening 
            ? '🎤 Listening' 
            : isAvatarTalking 
            ? '🗣️ Speaking' 
            : avatarSession?.isReady 
            ? '😊 Ready' 
            : '⏳ Loading'
          }
        </div>
      </div>
    </div>
  );
});

export default HeyGenAvatar;